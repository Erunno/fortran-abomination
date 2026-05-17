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
5. [Architecture](#5-architecture)  
   5.1 [Pipeline overview](#51-pipeline-overview)  
   5.2 [Parsing layer](#52-parsing-layer)  
   5.3 [Abstraction layer](#53-abstraction-layer)  
   5.4 [Analysis layer](#54-analysis-layer)  
   5.5 [Generation layer](#55-generation-layer)  
   5.6 [Templates](#56-templates)

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

| Flag | Short | Description |
|------|-------|-------------|
| `--input FILE` | `-i` | Input Fortran source file. |
| `--kernel NAME` | `-k` | Entry kernel function name (case-sensitive). |

### Optional

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--output-dir DIR` | `-o` | `.` (cwd) | Directory for all generated files. Created if it does not exist. |
| `--cuda-output FILE` | | `generated_code.cu` | CUDA output filename. |
| `--cpp-output FILE` | | `generated_cpp_impl.cpp` | Plain C++ output filename. |
| `--fortran-output FILE` | | `generated_interface.f90` | Fortran interface output filename. |
| `--common-header FILE` | | `common_functions.cuh` | Common header output filename. |
| `--no-common-header` | | off | Skip copying the common header. |
| `--verbose` | `-v` | off | Print detailed parsing and kernel-graph information. |

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

| Construct | Notes |
|-----------|-------|
| 3-D arrays passed as `(:,:,:)` assumed-shape | Row/column order is preserved via the `F_IDX` indexing macro |
| `real(knd)` scalars | Mapped to `double` |
| `integer` scalars | Mapped to `int` |
| `intent(in)` / `intent(out)` / `intent(inout)` | Drives `const`/`__restrict__` decoration in C++ |
| Scalar local variables | Lifted to declarations at the top of the C++ function |
| `do k = lo, hi` loops (up to 3 levels deep) | Mapped to C++ `for` loops; loop bounds may reference size parameters |
| Arithmetic expressions (all Fortran operators) | Translated element-by-element to C++ |
| Scalar assignments before loops (pre-computations) | Emitted as C++ assignments outside the loop body |
| `call SubKernel(...)` within an entry kernel | Inlined: the sub-kernel's body is merged into the generated output |

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

---

## 5. Architecture

### 5.1 Pipeline overview

```
Input Fortran file
    │
    ▼ fparser  (third-party library)
Raw fparser AST
    │
    ▼ FparserTree  (fparser_tree_abstraction.py)
Typed AST wrapper with parent-walking and node search
    │
    ▼ KernelFinder / SourceFilesCollection  (kernels_finder.py)
Map { function_name → KernelFunctionDefinition }
    │
    ▼ KernelFunctionDefinition.extract_kernels_graph()  (kernel_abstraction.py)
List[Kernel]  — one Kernel per do-loop nest in the call graph
    │
    ├──▶ UsedVarsFinder / UsedSizesFinder  (expression_walking/)
    │    (variable and dimension discovery, used by generators)
    │
    ▼ DependenceResolver.group_kernels()  (cuda_generation/kernel_depence.py)
List[KernelGroup]  — kernels sharing outer loop contexts are fused
    │
    ▼ FullCodeGenerator  (cuda_generation/generator.py)
    ├── CudaKernelGenerator     →  generated_code.cu
    ├── PureCppGenerator        →  generated_cpp_impl.cpp
    ├── FortranInterfaceGenerator → generated_interface.f90
    └── template copy           →  common_functions.cuh
```

### 5.2 Parsing layer

**`fparser_tree_abstraction.py`** — `FparserTree`

Thin wrapper around the fparser2 AST node. Provides:
- `get_all_nodes_of_type(type_name)` — recursive node search by class name.
- `get_first_parent_of_type(type_name)` — walks upward through the parent chain.
- `reduce_nodes(fn, initial)` — generic fold over the entire subtree.
- `is_type(type_name)` — class-name comparison (case-insensitive).

All other compiler components operate on `FparserTree` objects rather than raw
fparser nodes, which decouples the codebase from fparser internals.

**`kernels_finder.py`** — `SourceFilesCollection_FromFilesystem`, `KernelFinder`

`SourceFilesCollection_FromFilesystem` accumulates file paths (via `load_file` or
`load_dir`). Its `iterate_paths(first_line_predicate)` method supports pre-filtering
files by their first line, which `KernelFinder` uses to skip files that do not begin
with `! kernels`.

`KernelFinder.load_all_kernels()` parses every collected file with fparser,
walks the AST for `subroutine` nodes preceded by a `! kernel` comment, and
returns a `dict[str, KernelFunctionDefinition]` keyed by subroutine name.

### 5.3 Abstraction layer

**`kernel_abstraction.py`** — `KernelFunctionDefinition`, `Kernel`

`KernelFunctionDefinition` wraps the top-level parsed subroutine and owns the full
local variable context (`LocalContext`).  Its `extract_kernels_graph()` method
performs a depth-first traversal of `call` statements, recursively expanding each
called sub-kernel. The result is a flat `list[Kernel]` in call order.

`Kernel` represents a single atomic computation unit: a do-loop nest together with
its body code lines and its enclosing `Context`.  It supports:
- `get_all_do_loop_contexts_from_outer_to_inner()` — ordered list of loop ranges.
- `enum_lines_with_context()` — yields (code_line_ast, context) pairs for the
  code generator.
- `merge_with(other)` — joins two kernels that share a loop nest (used internally
  by the kernel-graph builder).

**`context.py`** — `Variable`, `Context`, `DoLoopContext`, `LocalContext`

`Variable` stores a variable's name, type, and attribute list (`intent(in)`, etc.).
`Context` is the base class for any variable-scoping environment.
`DoLoopContext` extends `Context` with loop-range information (`from`, `to`, `step`).
`LocalContext` is the function-level scope and holds the complete variable table used
by generators when looking up types and intents.

**`typing.py`** — `ArrayType`, `TerminalType`

Type descriptors that carry enough information for the C++ type generator:
array rank, element type, and Fortran kind parameter.

### 5.4 Analysis layer

**`expression_walking/visitor_base.py`** — `AstVisitor`

A decorator-based AST visitor. Subclasses register handlers with
`@AstVisitor.accept("NodeTypeName")` and fall back to the default
"visit all children" behaviour for unregistered node types.

**`expression_walking/used_var.py`** — `UsedVarsFinder`, `UsedSizesFinder`

`UsedVarsFinder` collects every `Variable` that appears in a kernel's body
(including do-loop bounds). The code generators use this to determine which
variables must appear in the generated function's parameter list.

`UsedSizesFinder` specialises this to find the dimension-size parameters of array
arguments (the `dim1`, `dim2`, `dim3` integers passed alongside each array pointer
in the C++ interface).

**`cuda_generation/kernel_depence.py`** — `DependenceResolver`, `KernelGroup`

`DependenceResolver.group_kernels()` groups the flat kernel list by shared outer
do-loop contexts. Kernels whose outermost loops iterate over the same range are
candidates for fusion into a single CUDA `__global__` kernel, which avoids
redundant global-memory round-trips. Kernels with no iteration context (e.g.
scalar pre-computations) are placed in their own group.

**`code_dependence.py`** — `CodeDependenceExtractor`

Extracts read/write dependencies from assignment statements. Currently used for
analysis diagnostics; not yet wired into the scheduling or fusion decisions.

### 5.5 Generation layer

**`cuda_generation/generator.py`** — `FullCodeGenerator`

Orchestrates all sub-generators. Instantiated with the flat kernel list and the
entry `KernelFunctionDefinition`. Exposes three public methods:

| Method | Output |
|--------|--------|
| `generate_cuda_code()` | `generated_code.cu` |
| `generate_pure_cpp_code()` | `generated_cpp_impl.cpp` |
| `generate_fortran_interface_code()` | `generated_interface.f90` |

Each method loads its template, calls the appropriate sub-generators to produce
code fragments, substitutes the placeholders, and returns the final string.

**`cuda_generation/code_parts/cpp_code_line_gen.py`** — `CppExprCodeGenerator`

Translates a single Fortran assignment or expression AST node into a C++ string.
Handles:
- Binary arithmetic operators (`+`, `-`, `*`, `/`)
- Unary negation
- Array indexing (converted to `F_IDX(...)` calls)
- Scalar variable references
- Numeric literals (integer and real, including `_knd` kind suffixes)

**`cuda_generation/code_parts/cpp_types_gen.py`** — `CppTyper`

Maps `Variable` objects to their C++ type string. Arrays become `double* __restrict__`
plus accompanying `size_t dimN` parameters; scalars become `double` or `int`.

**`cuda_generation/code_parts/cuda_kernel.py`** — `CudaKernelGenerator`, `KernelGroupGenerator`

`KernelGroupGenerator` takes a `KernelGroup` and generates the body of a single
`__global__` kernel function. The loop nest is replaced by a 1-D thread-index
decomposition with column-major coordinate recovery.

`CudaKernelGenerator` iterates over all kernel groups and assembles the full set of
`__global__` device functions.

**`cuda_generation/code_parts/cuda_mem.py`** — `CudaMemCodeGenerator`

Generates the host-side memory management code: `cudaMalloc` declarations,
`cudaMemcpy H→D` for inputs, kernel launches, `cudaMemcpy D→H` for outputs, and
`cudaFree` calls. Each phase is wrapped in a timing helper from `common_functions.cuh`.

**`cuda_generation/code_parts/pure_cpp_gen.py`** — `PureCppGenerator`

Generates the flat CPU C++ implementation by treating all kernels as a single group
(no CUDA thread decomposition). Delegates body generation to `KernelGroupGenerator`
with the fusion disabled, producing straightforward nested `for` loops.

**`cuda_generation/code_parts/fortran_interface.py`** — `FortranInterfaceGenerator`

Generates the Fortran module that bridges the C++ function. Produces:
- The `interface` block declaring `cpp_<KERNEL_NAME>` with `bind(C)`.
- A wrapper subroutine with the original Fortran argument list that converts
  assumed-shape array arguments to `c_loc` pointers and explicit dimension integers
  before delegating to the C++ function.

**`cuda_generation/code_parts/host_params.py`** — `ParamsGenerator`

Generates the parameter list for the host-side C++ wrapper (`cpp_<KERNEL_NAME>`).
Each array argument is expanded to a `double*` pointer plus three `size_t` dimension
parameters; scalars are passed by value.

**`cuda_generation/code_parts/do_loops.py`** — `DoLoopGenerator`

Translates `DoLoopContext` objects into C++ `for` loop headers, handling arbitrary
loop bounds that reference size parameters.

**`cuda_generation/code_parts/variable_namer.py`** — `VariableNamer`

Converts Fortran variable names to their C++ counterparts (currently lowercase,
with any Fortran-specific suffixes stripped).

**`cuda_generation/code_parts/kernel_func_namer.py`** — `KernelFuncNamer`

Generates deterministic names for the `__global__` device functions
(`kernel_group_1_device`, `kernel_group_2_device`, …).

### 5.6 Templates

All output files are assembled by filling placeholders of the form
`$PLACEHOLDER_NAME$` in the template files under `cuda_generation/templates/`.

**`template.py`** — `Template`

Minimal template engine: loads a file, exposes `replace_placeholder(name, content, tabs)`
which substitutes `$NAME$` with `content`, optionally indenting every line by `tabs`
tab stops.

| Template file | Placeholders |
|---------------|-------------|
| `kernels_interface_template.cu` | `KERNEL_NAME`, `HOST_PARAMETERS`, `DEVICE_BUFF_DECLS`, `CUDA_ALLOC`, `CUDA_H2D`, `KERNEL_DEFINITIONS`, `KERNEL_CALLS`, `CUDA_D2H`, `CUDA_FREE` |
| `cpp_impl.cpp` | `KERNEL_NAME`, `HOST_PARAMETERS`, `LOCAL_VAR_DECLS`, `KERNEL_BODY` |
| `fortran_interface.f90` | `MODULE_NAME`, `KERNEL_NAME`, `FORTRAN_INTERFACE_DUMMY`, `FORTRAN_INTERFACE_DECLS`, `ORIGINAL_FORTRAN_FUNC_DUMMY`, `FORTRAN_KERNEL_ARGS_DECLS`, `FORTRAN_CPP_KERNEL_ARGS_CALL` |
| `common_functions.cuh` | *(copied verbatim — no placeholders)* |
