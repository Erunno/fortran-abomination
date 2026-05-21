# Fortran-to-CUDA/C++ Compiler

A source-to-source compiler that reads a Fortran stencil kernel module and generates:

- A **CUDA implementation** (`.cu`) — each do-loop nest becomes a `__global__` kernel; memory management and Fortran interop are emitted automatically.
- A **plain C++ implementation** (`.cpp`) — a flat, single-function C++ kernel callable directly from Fortran, without any GPU code.
- A **Fortran interface module** (`.f90`) — thin `iso_c_binding` wrapper that exposes the generated C function under the original Fortran subroutine name, keeping the call site unchanged.
- The **shared header** (`common_functions.cuh`) — column-major indexing utility (`F_IDX`) and CUDA timing infrastructure used by both output targets.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [CLI Reference](#2-cli-reference)
3. [Input File Format](#3-input-file-format)  
   3.1 [File-level markers](#31-file-level-markers)  
   3.2 [Kernel subroutines](#32-kernel-subroutines)  
   3.3 [Entry kernel](#33-entry-kernel)  
   3.4 [Supported constructs](#34-supported-constructs)  
   3.5 [Restrictions](#35-restrictions)
4. [Output Files](#4-output-files)

---

## 1. Quick Start

```bash
# Install the single dependency
pip install fparser

# Generate all outputs for the CDU kernel into out/
python -m compiler \
    --input  fortran-stencils/elmm_cdu.f90 \
    --kernel CDU \
    --output-dir out/
```

Expected output:

```
Generated files in /path/to/out/
  cuda:              generated_code.cu
  c++:               generated_cpp_impl.cpp
  fortran interface: generated_interface.f90
  common header:     common_functions.cuh
```

---

## 2. CLI Reference

```
python -m compiler --input FILE --kernel NAME [options]
```

### Required

| Flag            | Short | Description                                  |
| --------------- | ----- | -------------------------------------------- |
| `--input FILE`  | `-i`  | Input Fortran source file.                   |
| `--kernel NAME` | `-k`  | Entry kernel function name (case-sensitive). |

### Optional

| Flag                    | Short | Default                   | Description                                                      |
| ----------------------- | ----- | ------------------------- | ---------------------------------------------------------------- |
| `--output-dir DIR`      | `-o`  | `.` (cwd)                 | Directory for all generated files. Created if it does not exist. |
| `--cuda-output FILE`    |       | `generated_code.cu`       | CUDA output filename.                                            |
| `--cpp-output FILE`     |       | `generated_cpp_impl.cpp`  | Plain C++ output filename.                                       |
| `--fortran-output FILE` |       | `generated_interface.f90` | Fortran interface output filename.                               |
| `--common-header FILE`  |       | `common_functions.cuh`    | Common header output filename.                                   |
| `--no-common-header`    |       | off                       | Skip copying the common header.                                  |
| `--verbose`             | `-v`  | off                       | Print detailed parsing and kernel-graph information.             |

### Error handling

If `--kernel` is not found in the file, the compiler exits with a message listing all available kernel names:

```
error: kernel 'FOO' not found in elmm_cdu.f90
       available kernels: set, multiply, CDUdiv, CDUadv, CDU
```

---

## 3. Input File Format

### 3.1 File-level markers

The compiler uses comment markers to discover which files contain kernels and which
subroutines inside them are kernels.

The **first line** of the file must be exactly:

```fortran
! kernels
```

This tells the file scanner to parse the file rather than skip it.

```fortran
! kernels                        ← required first line
module MomentumAdvection
  implicit none
  private
  public CDU
contains
  ...
end module MomentumAdvection
```

### 3.2 Kernel subroutines

Each subroutine that should be compiled must be preceded by the comment:

```fortran
  ! kernel
  subroutine MyKernel(...)
    ...
  end subroutine MyKernel
```

Subroutines without this comment are ignored by the compiler.

### 3.3 Entry kernel

The entry kernel (passed via `--kernel`) is the top-level subroutine that the
Fortran driver calls. It may itself call other `! kernel`-annotated subroutines.
The compiler traverses the full call graph from this entry point, inlines all
reachable sub-kernels, and merges their do-loop nests into the generated C++/CUDA
output.

A typical entry kernel composes several passes:

```fortran
  ! kernel
  subroutine CDU(U2, U, V, W, dxmin, dymin, dzmin, Unx, Uny, Unz)
    real(knd), contiguous, intent(out) :: U2(:,:,:)
    real(knd), contiguous, intent(in)  :: U(:,:,:), V(:,:,:), W(:,:,:)
    real(knd), intent(in) :: dxmin, dymin, dzmin
    real(knd) :: zero, half
    integer, intent(in) :: Unx, Uny, Unz

    zero = 0.0_knd
    half = 0.5_knd

    call set(U2, zero, Unx, Uny, Unz)        ! sub-kernel 1
    call CDUdiv(U2, U, V, W, ...)             ! sub-kernel 2
    call CDUadv(U2, U, V, W, ...)             ! sub-kernel 3
    call multiply(U2, half, Unx, Uny, Unz)   ! sub-kernel 4
  end subroutine CDU
```

### 3.4 Supported constructs

| Construct                                          | Notes                                                                |
| -------------------------------------------------- | -------------------------------------------------------------------- |
| 3-D arrays passed as `(:,:,:)` assumed-shape       | Row/column order is preserved via the `F_IDX` indexing macro         |
| `real(knd)` scalars                                | Mapped to `double`                                                   |
| `integer` scalars                                  | Mapped to `int`                                                      |
| `intent(in)` / `intent(out)` / `intent(inout)`     | Drives `const`/`__restrict__` decoration in C++                      |
| Scalar local variables                             | Lifted to declarations at the top of the C++ function                |
| `do k = lo, hi` loops (up to 3 levels deep)        | Mapped to C++ `for` loops; loop bounds may reference size parameters |
| Arithmetic expressions (all Fortran operators)     | Translated element-by-element to C++                                 |
| Scalar assignments before loops (pre-computations) | Emitted as C++ assignments outside the loop body                     |
| `call SubKernel(...)` within an entry kernel       | Inlined: the sub-kernel's body is merged into the generated output   |

### 3.5 Restrictions

The following are not yet supported:

- Input from multiple source files (one file per invocation for now).
- Non-3-D arrays.
- `if` / `select case` control flow inside kernels.
- Reductions (e.g., accumulating a scalar sum inside a loop).
- Fortran intrinsics other than arithmetic operators.
- `intent(inout)` arrays used with read-before-write patterns across loop groups
  (the compiler will generate code but the CUDA variant may produce incorrect results).

---

## 4. Output Files

### `generated_code.cu`

Full CUDA implementation. Each group of kernels that shares the same outer do-loop
context is fused into one `__global__` device kernel. The generated host-side
`cpp_<KERNEL_NAME>` function:

1. Allocates device buffers (`cudaMalloc`)
2. Copies inputs host → device (`cudaMemcpy`)
3. Launches each fused kernel with a 1-D thread block layout
4. Copies the result device → host
5. Frees device buffers

Timing instrumentation (controlled by `#define MEASURE_CUDA_EXECUTION_TIME`) is
injected around each phase and reported by `cpp_finish_hot()`.

### `generated_cpp_impl.cpp`

Plain CPU C++ implementation. All sub-kernels are inlined into a single
`cpp_<KERNEL_NAME>` function with `extern "C"` linkage, which can be compiled by
any C++17-compatible compiler and linked directly with `gfortran`.  
Arrays are accessed through the same `F_IDX` column-major indexing macro as the
CUDA version, so correctness can be verified by comparing the two outputs.

### `generated_interface.f90`

A Fortran module named `MomentumAdvection` that:

- Declares the `iso_c_binding` interface for `cpp_<KERNEL_NAME>`.
- Exposes a wrapper subroutine with the same signature as the original Fortran
  kernel, keeping every call site in the driver unchanged.
- Exports `knd`, `start_hot`, and `finish_hot` so the benchmark driver compiles
  without modification regardless of which variant is linked.

### `common_functions.cuh`

Shared C++ header copied from the compiler's internal template. Provides:

- `F_IDX(i, j, k, dim1, dim2, dim3)` — variadic, compile-time column-major index
  function, works in both host and device code.
- `generated_kernels::timing` — CUDA-event-based timing helpers used by the CUDA
  variant (`measure_alloc`, `measure_h2d`, `measure_kernel_executions`, etc.).
