# Lazy Memory Management — Proof of Concept

Self-contained demo of the `mprotect`/`SIGSEGV` mechanism described in the
[parent README](../README.md).  No CUDA required — the "GPU computation" is
replaced by a trivial doubling of the input array to keep the focus on the
memory-protection machinery.

---

## Files

| File | Purpose |
|------|---------|
| `managed_mem.cpp` | `arm_memory_locks()`: sets `mprotect` permissions and registers the `SIGSEGV` handler |
| `main.f90` | Fortran program that allocates two arrays, calls `arm_memory_locks`, then performs one of four access patterns |
| `Makefile` | Cross-language build; `ARGS=N` selects the test case |

---

## Build and run

```bash
make          # builds ./pure_fortran_app
make ARGS=3   # run test case 3 (read from output buffer)
```

---

## Test cases

| Case | Fortran action | Trap? | What happens |
|------|----------------|-------|--------------|
| `1` | Read `in_arr(1)` | No | `in_arr` is `PROT_READ`; reads go through freely. Returns `15`. |
| `2` | Write `in_arr(1) = 999` | Yes | Write to `PROT_READ` raises `SIGSEGV`. Handler runs the doubling (simulating H→D re-upload), restores access, then the write succeeds. |
| `3` | Read `out_arr(1)` | Yes | `out_arr` is `PROT_NONE`. Handler runs the doubling (simulating D→H) and restores access. Returns `30` (= 15 × 2). |
| `4` | Write `out_arr(1) = 888` | Yes | Same trap as case 3. Handler doubles `out_arr(2)` onward; `out_arr(1)` is then overwritten to `888` by Fortran. |

---

## Expected output for case 3

```
[C++ HOOK] Trap triggered at memory address: 0x...
[C++ HOOK] Executing lazy doubling NOW!
--- TEST 3: Reading Output ---
Action: Reading out_arr(1)
Result:  30
Result: out_arr(2) =  60
Expected: Hook fired. Result is 30.
```

The Fortran code that triggers the handler is a plain, unmodified array read:

```fortran
print *, out_arr(1)   ! raises SIGSEGV → handler fires → computation → resume
```

---

## Notes

**Page alignment** — `mprotect` operates at page granularity (4 096 bytes).
Fortran `allocate` does not guarantee page-aligned addresses, so `managed_mem.cpp`
rounds the pointer down to the nearest page boundary before calling `mprotect`.

**`SA_SIGINFO`** — the handler uses this flag to receive `siginfo_t`, which
carries the exact faulting address (`si_addr`), allowing the handler to identify
which buffer was touched.

**Double-fault trap** — if the program crashes with `Segmentation Fault (core dumped)`
immediately after printing a trap message, there is likely an I/O call inside the
handler that accesses still-protected heap memory.  Call `mprotect` to unlock all
affected pages *before* any logging inside the handler.

