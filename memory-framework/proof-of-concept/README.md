# Managed Memory PoC: Lazy GPU-Host Migration

This project demonstrates a **hardware-intercepted memory management system** in C++ and Fortran. It uses OS-level page protection to implement a "Just-in-Time" data migration and evaluation pattern.

---

## 1. Motivation: The GPU-Host Bottleneck

In heterogeneous computing (CPU + GPU), data transfer over the PCIe bus is often the primary performance bottleneck.

### The Problem

Traditional programs often copy large buffers from the GPU to the Host "just in case" the CPU needs them. If the CPU only touches 1% of that data (or none at all), 99% of the transfer time was wasted.

### The Solution: Lazy Migration

By "locking" host-side memory at the OS level, we can:

1. Keep data on the GPU by default.
2. Allow the Fortran program to "think" it has the data.
3. **Intercept** the exact moment the CPU attempts to read or write a specific memory address.
4. Only then, migrate the data from the GPU to the Host and resume execution.

This ensures that computation stays on the GPU as long as possible, and data moves **only if needed**.

---

## 2. Proof of Concept: The "Lazy Doubler"

The PoC simulates this behavior using two buffers: `in_arr` and `out_arr`.

* **Input Buffer:** Set to `PROT_READ`. The CPU can read it without penalty. If the CPU tries to **write**, the hook fires to preserve/process the original data before it is lost.
* **Output Buffer:** Set to `PROT_NONE`. Any access (Read or Write) triggers the hook.

### Observed Behavior

| Action | Hardware Permission | Result |
| --- | --- | --- |
| **Read Input** | `PROT_READ` | CPU succeeds immediately. No overhead. |
| **Write Input** | `PROT_READ` | **Page Fault.** C++ handler fires, performs logic, unlocks page, resumes. |
| **Read Output** | `PROT_NONE` | **Page Fault.** C++ handler fires, populates data, unlocks page, resumes. |
| **Write Output** | `PROT_NONE` | **Page Fault.** C++ handler fires, unlocks page, resumes. |

---

## 3. Implementation Details

### Page-Level Granularity

The Operating System manages memory in **Pages** (typically **4096 bytes**). We cannot lock a single integer; we must lock the entire page the integer resides on.

> **Technical Note:** If Fortran allocates memory that isn't "page-aligned" (starting at an address divisible by 4096), the C++ backend manually rounds the pointer down to the nearest page boundary before applying `mprotect`. This ensures compatibility with standard Fortran `allocate` statements.

### The Signal Handler (`SIGSEGV`)

When a protected page is touched, the CPU generates a hardware interrupt. The Linux kernel translates this into a `SIGSEGV` signal.

Our C++ handler uses the `SA_SIGINFO` flag to receive a `siginfo_t` structure, which contains the **exact memory address** (`si_addr`) that caused the fault. This allows us to determine exactly which buffer needs to be synchronized.

### The "Double-Fault" Trap

When writing handlers, **all memory protection must be removed before calling I/O functions** (like `std::cout` or `print`).

* **Reason:** High-level functions often use the heap.
* **Risk:** If `std::cout` tries to access a memory page that we have locked, it will trigger a second Page Fault while inside the first handler, leading to an immediate `Segmentation Fault (core dumped)`.

---

## 4. Developer Tutorial: How to Reproduce

### File Structure

* `managed_mem.cpp`: The C++ "Guardian" (Signal handler and `mprotect` logic).
* `main.f90`: The Fortran "User" (Allocates memory and performs math).
* `Makefile`: Handles cross-language compilation and linking.

### Build and Test

1. **Compile and Link:**
```bash
make

```


2. **Run Test Suite:**
The executable accepts an argument `(1-4)` to isolate specific hardware behaviors.

```bash
./pure_fortran_app 1  # Test Read Input (Allowed)
./pure_fortran_app 2  # Test Write Input (Intercepted)
./pure_fortran_app 3  # Test Read Output (Intercepted)
./pure_fortran_app 4  # Test Write Output (Intercepted)
```

### Summary of Key APIs
*   `sysconf(_SC_PAGESIZE)`: Finds the hardware page size.
*   `mprotect(ptr, size, prot)`: Sets OS permissions (`PROT_NONE`, `PROT_READ`, `PROT_WRITE`).
*   `sigaction(...)`: Registers the hardware fault interceptor.
*   `c_f_pointer`: (Fortran) Maps a raw C address to a native Fortran array.

---

**Note to future self:** If you see a `core dump` immediately after a "Trap Triggered" message, you likely added a print statement *before* the `mprotect` call that unlocks the memory. **Unlock first, then log.**
