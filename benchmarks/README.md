# Benchmark Suite

A self-contained benchmark suite for comparing Fortran stencil kernels across five
implementation variants: plain Fortran, OpenMP-parallelised Fortran, CUDA (via
Fortran ↔ C interop), plain C++, and OpenMP-parallelised C++.  All build logic lives in a single top-level `Makefile`;
per-case and per-variant details are factored into small, reusable include files.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Prerequisites](#2-prerequisites)
3. [Running a Single Benchmark](#3-running-a-single-benchmark)
4. [Automated Benchmark Runner](#4-automated-benchmark-runner)
5. [Correctness Tests](#5-correctness-tests)
6. [Generating Figures](#6-generating-figures)
7. [Directory Structure](#7-directory-structure)
8. [Architecture](#8-architecture)  
   8.1 [Build System](#81-build-system)  
   8.2 [Source Layout per Case](#82-source-layout-per-case)  
   8.3 [Benchmark Driver](#83-benchmark-driver)  
   8.4 [Benchmark Runner](#84-benchmark-runner)  
   8.5 [Correctness Test Runner](#85-correctness-test-runner)  
   8.6 [Graph Generation](#86-graph-generation)
9. [Adding a New Case](#9-adding-a-new-case)
10. [Adding a New Variant](#10-adding-a-new-variant)
11. [CSV Output Format](#11-csv-output-format)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Quick Start

```bash
# Build and run a single benchmark (plain Fortran, default grid 64×64×64)
make CASE=CVD VARIANT=Fortran
./bin/CVD_Fortran_NX64_NY64_NZ64_NITER100_NWARMUP5/benchmark

# Run all cases/variants/grids automatically → results.csv
python run_bechmarks.py > results.csv

# Generate publication-quality figures from results.csv
source ../venv/bin/activate
python graphs/plot_benchmarks.py
# → graphs/figs/grid_<NX>x<NY>x<NZ>_niter<N>.{png,pdf}
```

---

## 2. Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| GNU Make | 3.81 | Standard on most Linux systems |
| gfortran | 10+ | Or any Fortran 2003–compatible compiler; set `FC=` |
| CUDA Toolkit | 11+ | Only for `VARIANT=CUDA`; set `CUDA_HOME=` if non-standard |
| Python | 3.9+ | Runner + graph scripts |
| matplotlib, numpy | any recent | `pip install matplotlib numpy` |

The Fortran compiler must support:
- Preprocessing (`-cpp` flag or equivalent)
- The `iso_c_binding` intrinsic module (for CUDA interop)
- OpenMP 3.1+ (for `Fortran-OMP` variant)

For CUDA builds, `nvcc` must be on `PATH` or pointed to via `CUDA_HOME`.

---

## 3. Running a Single Benchmark

All builds are driven by the top-level `Makefile`.  The binary is placed under
`bin/<BUILD_ID>/benchmark` where `BUILD_ID` encodes every parameter that affects
the binary, making it safe to have multiple builds coexist.

### Required parameter

| Variable | Meaning | Example values |
|----------|---------|----------------|
| `CASE` | Benchmark case (subdirectory name) | `CDU`, `CDW`, `CVD` |

### Optional parameters

| Variable | Default | Meaning |
|----------|---------|---------|
| `VARIANT` | `Fortran` | `Fortran` \| `Fortran-OMP` \| `CUDA` \| `CPP` \| `CPP-OMP` |
| `NX` | 64 | Grid interior points in X |
| `NY` | 64 | Grid interior points in Y |
| `NZ` | 64 | Grid interior points in Z |
| `NITER` | 100 | Timed iterations per run |
| `NWARMUP` | 5 | Warm-up iterations (not timed) |
| `FC` | `gfortran` | Fortran compiler |
| `FFLAGS` | `-O3 -march=native -flto` | Base Fortran compiler flags |
| `EXTRA_FFLAGS` | _(empty)_ | Appended to `FFLAGS` — useful for one-off flags |
| `CXX` | `g++` | C++ compiler (CPP / CPP-OMP variants) |
| `CXXFLAGS` | `-O3 -march=native` | Base C++ compiler flags |
| `EXTRA_CXXFLAGS` | _(empty)_ | Appended to `CXXFLAGS` |
| `CUDA_HOME` | `/usr/local/cuda` | CUDA installation root |
| `NVCC` | `$CUDA_HOME/bin/nvcc` | CUDA compiler |
| `NVCCFLAGS` | `-O3` | NVCC base flags |
| `CUDA_ARCH` | _(auto)_ | e.g. `sm_80` — passed as `-arch=$(CUDA_ARCH)` if set |

### Examples

```bash
# Default Fortran build of CVD
make CASE=CVD

# CVD with CUDA on a specific architecture and a large grid
make CASE=CVD VARIANT=CUDA NX=256 NY=256 NZ=256 NITER=50 CUDA_ARCH=sm_80

# CDU with OpenMP and a custom compiler
make CASE=CDU VARIANT=Fortran-OMP FC=/usr/bin/gfortran-13 NX=128 NY=128 NZ=128

# Rebuild cleanly (remove only this combination's artefacts)
make clean CASE=CVD VARIANT=Fortran NX=256

# Wipe everything in bin/
make clean-all
```

Each variant also has its own three-line `Makefile` inside
`CASE/VARIANT/Makefile` that delegates to the top-level — useful for building
from inside the variant directory:

```bash
cd CVD/CUDA && make NX=128 NY=128 NZ=128
```

### Reading the output

**Fortran / Fortran-OMP** benchmark output:

```
--- CVD benchmark ---
grid:         256 x 256 x 256
iters:        100
warmup_iters: 5
total_ms:     1234.567 ms
ms_per_iter:  12.346 ms
```

**CUDA** benchmark output (includes per-phase breakdown):

```
--- CVD benchmark ---
grid:         256 x 256 x 256
iters:        100
warmup_iters: 5
malloc_total_ms:  11.2
h2d_total_ms:     38.4  (23.1 GBps)
kernel_total_ms:   2.6
d2h_total_ms:     11.9  (19.8 GBps)
free_total_ms:    10.7
```

---

## 4. Automated Benchmark Runner

`run_bechmarks.py` sweeps all configured combinations, builds missing binaries on
demand, discards warm-up rounds, and writes a semicolon-separated CSV to stdout.
Progress/errors go to stderr, so redirecting stdout captures a clean CSV.

### Configuration (top of the script)

```python
FUNCTIONS     = ['CDW', 'CDU', 'CVD']   # cases to run
VARIANTS      = ['Fortran', 'Fortran-OMP', 'CUDA']
GRIDS         = [[64, 64, 64], [128, 128, 128], [256, 256, 256]]
ITERS         = [100]
WARMUP_ITERS  = 10    # in-kernel warm-up iterations (compiled into the binary)
WARMUP_ROUNDS = 2     # full-program rounds discarded before timing
ROUNDS        = 5     # full-program rounds whose results are recorded
```

> **Note:** `WARMUP_ITERS` is baked into the binary at compile time (preprocessor
> define `VAR_NWARMUP`).  If you change it, the script will rebuild the binary
> automatically because the build ID changes.

### Running

```bash
# Activate the Python venv first if using one
source ../venv/bin/activate

python run_bechmarks.py > results.csv
```

If a particular combination fails (missing compiler, unsupported GPU, etc.) the
error is printed to stderr and the script continues with the next combination.

### Incremental builds

The runner automatically detects when a source file is newer than the binary
and triggers a rebuild.  It monitors all files under `CASE/VARIANT/`, `CASE/`,
`common/`, and the top-level `Makefile`.

To force a full rebuild regardless of timestamps, run `make clean-all` or
delete the relevant subdirectory under `bin/`.

### Running on a cluster / GPU node

The runner is a plain Python process — run it on whichever node has the required
hardware.  For GPU benchmarks (`VARIANT=CUDA`) the node must have an accessible
GPU; the CUDA binary will be compiled on the same node via `nvcc`.

---

## 5. Correctness Tests

`run_tests.py` builds each variant on a small fixed grid (default 16×16×16),
runs the kernel once with a deterministic initial condition, and compares every
variant's output array against the serial Fortran reference.

### Running

```bash
# Test all three cases
python run_tests.py

# Test a single case
python run_tests.py CDU

# Via Make (tests the specified CASE only)
make test CASE=CDU
```

### How it works

1. `CASE/test_main.f90` initialises all input arrays with deterministic `sin/cos`
   values (no `random_number`), calls the kernel exactly once, then writes the
   interior of the output array to stdout — one `g0.17` value per line.
2. The top-level `Makefile` accepts `MAIN_SRC=test_main.f90` to swap in this
   driver while linking the exact same compiled kernel object.  No code is
   duplicated between the benchmark and the test.
3. `run_tests.py` collects the output lists and, for each non-reference variant,
   reports the maximum element-wise absolute difference against the Fortran
   serial result.

### Tolerances

| Variant | Typical `max_abs_diff` |
|---------|------------------------|
| Fortran-OMP | 0 (usually bit-exact) |
| CPP | 0 (same algorithm and FP order) |
| CPP-OMP | ≤ 1e-12 (minor FP reordering from parallelism) |
| CUDA | ≤ 1e-10 (GPU FP order differs) |

Default tolerance is `1e-10` absolute.  Variants that fail to build (e.g. CUDA
on a node without `nvcc`) are reported as `[SKIP]` rather than `[FAIL]`.

### Example output

```
=== CDU ===
  [REF ] Fortran         4096 values
  [PASS] Fortran-OMP     max_abs_diff=0.000e+00  (tol=1e-10)
  [PASS] CPP             max_abs_diff=0.000e+00  (tol=1e-10)
  [PASS] CPP-OMP         max_abs_diff=0.000e+00  (tol=1e-10)
  [PASS] CUDA            max_abs_diff=0.000e+00  (tol=1e-10)

All tests PASSED.
```

---

## 6. Generating Figures

`graphs/plot_benchmarks.py` reads `results.csv` and produces one figure per
unique `(grid, iters)` combination.

```bash
source ../venv/bin/activate
python graphs/plot_benchmarks.py
```

Figures are saved to `graphs/figs/` as both `.png` (300 dpi) and `.pdf`.  File
names follow the pattern `grid_<NX>x<NY>x<NZ>_niter<N>.{png,pdf}`.

### Figure design

Each figure shows grouped bars — one group per kernel, up to five bars per group:

| Bar | What it shows |
|-----|--------------|
| Blue (Fortran) | Total wall-clock time, serial Fortran |
| Amber (Fortran-OMP) | Total wall-clock time, OpenMP Fortran |
| CUDA (stacked) | Broken down: kernel (green) + data transfer H↔D (vermillion) + malloc/free (gray) |
| Sky blue (CPP) | Total wall-clock time, serial C++ |
| Reddish-purple (CPP-OMP) | Total wall-clock time, OpenMP C++ |

Error bars show ±1 standard deviation across `ROUNDS` runs.

The palette follows the Wong (2011) colorblind-safe scheme; hatch patterns make
bars distinguishable in greyscale print.

### Customising plots

All visual parameters are defined at the top of the script under clearly labelled
sections (`Palette`, `Layout`, `Publication style`).  The `FUNCTION_ORDER` list
controls the left-to-right order of the groups.

---

## 7. Directory Structure

```
benchmarks/
├── Makefile                  ← single unified build entry point
├── run_bechmarks.py          ← automated runner → CSV
├── run_tests.py              ← correctness test runner
├── results.csv               ← latest benchmark results
│
├── common/                   ← shared build infrastructure
│   ├── defaults.mk           ← default values for all Make variables
│   ├── variants.mk           ← per-variant compiler/linker flags
│   ├── standalone.mk         ← template included by variant Makefiles
│   └── common_functions.cuh  ← shared CUDA header (timing, indexing)
│
├── CDU/                      ← case: zonal momentum advection (U component)
│   ├── case.mk               ← declares CASE_SRC and CASE_CUDA_EXTRA
│   ├── main.f90              ← benchmark driver
│   ├── test_main.f90         ← correctness test driver
│   ├── Fortran/
│   │   ├── Makefile          ← 3-line delegating Makefile
│   │   └── cdu.f90
│   ├── Fortran-OMP/
│   │   ├── Makefile
│   │   └── cdu.f90
│   ├── CUDA/
│   │   ├── Makefile
│   │   ├── cdu.f90           ← Fortran ↔ C wrapper
│   │   └── generated_code.cu ← CUDA kernel (auto-generated)
│   ├── CPP/
│   │   ├── Makefile
│   │   ├── cdu.f90           ← Fortran ↔ C wrapper (iso_c_binding)
│   │   └── generated_cpp_impl.cpp ← C++ kernel
│   └── CPP-OMP/
│       ├── Makefile
│       ├── cdu.f90           ← identical to CPP wrapper
│       └── generated_cpp_impl.cpp ← C++ kernel with OpenMP pragmas
│
├── CDW/                      ← case: vertical momentum advection (W component)
│   └── ...                   ← same layout as CDU/
│
├── CDV/                      ← case: meridional momentum advection (V component)
│   └── ...                   ← same layout as CDU/
│
├── graphs/
│   ├── plot_benchmarks.py    ← figure generator
│   └── figs/                 ← generated PNG / PDF figures
│
└── bin/                      ← build artefacts (gitignored)
    └── <BUILD_ID>/
        └── benchmark
```

---

## 8. Architecture

### 8.1 Build System

The build system is split into three layers to keep per-case files minimal while
giving full control from the command line.

```
benchmarks/Makefile          ← all build logic (compile rules, link, paths)
    includes ↓
common/defaults.mk           ← default variable values
CASE/case.mk                 ← what sources this case provides
common/variants.mk           ← extra flags per variant (OMP, CUDA libs)
```

**`common/defaults.mk`** sets safe defaults for every Make variable.  It detects
whether `FC` is Make's built-in `f77` default and replaces it with `gfortran`.

**`CASE/case.mk`** is a small file that answers three questions for the build
system:

```make
CASE_SRC        = cvd.f90            # the variant's main Fortran source
CASE_CUDA_EXTRA = generated_code.cu  # extra .cu files (CUDA only)
CASE_CPP_EXTRA  = generated_cpp_impl.cpp  # extra .cpp files (CPP / CPP-OMP)
```

**`common/variants.mk`** appends variant-specific flags:

| Variant | Extra `FFLAGS` | Extra `CXXFLAGS` | Extra `LDFLAGS` |
|---------|---------------|-----------------|----------------|
| `Fortran` | _(none)_ | — | _(none)_ |
| `Fortran-OMP` | `-fopenmp` | — | `-fopenmp` |
| `CUDA` | _(none)_ | — | `-L$CUDA_HOME/lib64 -lcudart -lstdc++` |
| `CPP` | _(none)_ | _(none)_ | `-lstdc++` |
| `CPP-OMP` | `-fopenmp` | `-fopenmp` | `-lstdc++ -fopenmp` |

**`common/standalone.mk`** is included by every `CASE/VARIANT/Makefile`.  It
locates the top-level `Makefile` relative to itself and forwards `all` and `clean`
targets, automatically passing `CASE` and `VARIANT`.

**Build ID** — the output directory is named:

```
bin/CASE_VARIANT_NX{nx}_NY{ny}_NZ{nz}_NITER{n}_NWARMUP{w}/
```

This means different parameter combinations never collide and the runner can detect
whether a binary already exists without re-parsing Make output.

**CUDA include path** — `common_functions.cuh` is shared across all CUDA cases.
The nvcc compile rule passes `-I$(CURDIR)/common` so every case can use it without
copying the header.

### 8.2 Source Layout per Case

Each case directory contains:

| File | Purpose |
|------|--------|
| `case.mk` | Tells the build system which source files to use |
| `main.f90` | Benchmark driver (allocates arrays, runs warmup + timed loop) |
| `test_main.f90` | Correctness test driver (deterministic init, one-shot, output dump) |
| `Fortran/` | Serial Fortran implementation |
| `Fortran-OMP/` | OpenMP-parallelised Fortran implementation |
| `CUDA/` | CUDA implementation: a Fortran wrapper + generated `.cu` kernel || `CPP/` | C++ implementation: a Fortran wrapper (`iso_c_binding`) + generated `.cpp` kernel |
| `CPP-OMP/` | Same as CPP with `#pragma omp parallel for` on all outer loop nests |
The Fortran source in each variant must export a module named `MomentumAdvection`
that provides at minimum:

```fortran
module MomentumAdvection
  integer, parameter :: knd = kind(1.0d0)   ! double-precision kind
  public :: <KernelSubroutine>, knd, start_hot, finish_hot
  ...
end module
```

`start_hot` / `finish_hot` are no-op hooks in pure Fortran variants; they can be
used in CUDA variants to trigger JIT compilation or other warm-up work before
the timed section.

### 8.3 Benchmark Driver

`CASE/main.f90` is compiled and linked by the top-level `Makefile`.  Grid
dimensions and iteration counts are injected at compile time via preprocessor
defines (`-DVAR_NX`, `-DVAR_NY`, etc.), so the binary has no runtime flags.

The driver follows this pattern:

1. Allocate all required arrays on the heap
2. Initialise arrays with representative values
3. Call `start_hot()` (CUDA: triggers JIT + first allocation)
4. Run `VAR_NWARMUP` un-timed warm-up iterations
5. Record `t_start` with `system_clock`
6. Run `VAR_NITER` timed iterations
7. Record `t_end`, compute and print timing

### 8.4 Benchmark Runner

`run_bechmarks.py` orchestrates the full sweep:

```
for each (case, variant, grid, niter):
    build binary if not present
    run WARMUP_ROUNDS times  (discard output)
    run ROUNDS times         (collect output)
    parse output → list of float timings
    format as mean±stddev
    emit CSV row to stdout
```

Parsing is variant-aware:

- **Fortran / Fortran-OMP / CPP / CPP-OMP**: regex on `total_ms: <value> ms`
- **CUDA**: regex on each phase line (`malloc_total_ms`, `h2d_total_ms`, etc.)

All errors for a single combination are caught and reported to stderr; the loop
continues to the next combination.

### 8.5 Correctness Test Runner

`run_tests.py` drives `make` with `MAIN_SRC=test_main.f90` for each
`(case, variant)` combination, using a fixed 16×16×16 grid and `NITER=1
NWARMUP=0` for near-instant builds and runs.  Build failures are caught
per-variant and reported as `[SKIP]` without aborting the suite.

Comparison is purely element-wise using Python built-ins (no numpy dependency).

### 8.6 Graph Generation

`graphs/plot_benchmarks.py` uses **matplotlib** to produce publication-quality
figures.  One figure per `(grid, iters)` combination is generated.

Key design choices:

- **Wong (2011) colorblind-safe palette** for all bars
- **Hatch patterns** ensure legibility in greyscale / print
- **CUDA bars are stacked** (kernel + transfer + alloc) to show where time goes
- **Error bars** (±1σ) on every bar
- **300 dpi PNG + vector PDF** output
- **`rcParams`-based styling** — all typography and layout is set once at the top
  of the script, making global style changes trivial

---

## 9. Adding a New Case

1. **Create the case directory** and add the required files:

   ```
   benchmarks/NEWCASE/
   ├── case.mk
   ├── main.f90
   ├── Fortran/
   │   ├── Makefile
   │   └── newcase.f90
   ├── Fortran-OMP/
   │   ├── Makefile
   │   └── newcase.f90
   └── CUDA/
       ├── Makefile
       ├── newcase.f90     ← Fortran wrapper using iso_c_binding
       └── generated_code.cu
   ```

2. **Write `case.mk`** (3 lines):

   ```make
   CASE_SRC        = newcase.f90
   CASE_CUDA_EXTRA = generated_code.cu
   include ../../common/standalone.mk   # only needed in variant Makefiles
   ```

   For `case.mk` at the case root, just set the two variables:

   ```make
   CASE_SRC        = newcase.f90
   CASE_CUDA_EXTRA = generated_code.cu
   ```

3. **Write each `VARIANT/Makefile`** (3 lines):

   ```make
   CASE    = NEWCASE
   VARIANT = Fortran
   include ../../common/standalone.mk
   ```

4. **Implement the kernel module** — the Fortran source must export a module
   named `MomentumAdvection` with at least `knd`, `start_hot`, `finish_hot`, and
   the kernel subroutine.

5. **Write `main.f90`** — copy from an existing case and adjust the array
   declarations, allocation sizes, and kernel call.

6. **Write `test_main.f90`** — copy from an existing case, updating the output
   array name and the `call` statement.  The file must print the interior of
   the result array to stdout (see §5).

7. **Register in the runners** — add the new case name to `FUNCTIONS` in
   `run_bechmarks.py` and to `CASES` in `run_tests.py`.

8. **Build and test**:

   ```bash
   make CASE=NEWCASE VARIANT=Fortran
   ./bin/NEWCASE_Fortran_.../benchmark
   make test CASE=NEWCASE
   ```

---

## 10. Adding a New Variant

1. **Create `CASE/NEWVARIANT/`** for every case that should support it.

2. **Write each `Makefile`** (3 lines, as above).

3. **Add variant flags** in `common/variants.mk`:

   ```make
   ifeq ($(VARIANT),NEWVARIANT)
     VARIANT_FFLAGS  += ...
     VARIANT_LDFLAGS += ...
   endif
   ```

4. **Implement the kernel source** — must export the `MomentumAdvection` module.

5. **Update the runner** — add the variant name to `VARIANTS` in
   `run_bechmarks.py`.

6. **Update the graph script** — add a colour/hatch entry and a legend patch in
   `plot_benchmarks.py` if the variant needs its own visual representation.

---

## 11. CSV Output Format

The runner writes semicolon-delimited rows.  Every numeric measurement is
formatted as `mean+-stddev` (3 decimal places).  Empty fields (`;;`) indicate the
column does not apply to that variant.

```
function;variant;rounds;grid_x;grid_y;grid_z;iters;warmup_iters;warmup_turns;
cuda_malloc_ms;cuda_h2d_ms;cuda_h2d_gbps;cuda_kernel_run;
cuda_d2h_ms;cuda_d2h_gbps;cuda_free_ms;total_ms
```

| Column | Fortran/OMP | CUDA |
|--------|-------------|------|
| `function` | case name | case name |
| `variant` | `Fortran` or `Fortran-OMP` | `CUDA` |
| `rounds` | number of timed runs | same |
| `grid_x/y/z` | interior grid dimensions | same |
| `iters` | timed iterations per run | same |
| `warmup_iters` | in-kernel warmup count | same |
| `warmup_turns` | discarded full-program runs | same |
| `cuda_*` | _(empty)_ | per-phase timing / bandwidth |
| `total_ms` | wall-clock total | malloc+h2d+kernel+d2h+free |

---

## 12. Troubleshooting

**Build fails with "No rule to make target"**  
Check that `CASE` is spelled exactly as its subdirectory name (case-sensitive) and
that `CASE/case.mk` exists.

**`nvcc: command not found`**  
Set `CUDA_HOME` to point to your CUDA installation:
```bash
make CASE=CVD VARIANT=CUDA CUDA_HOME=/path/to/cuda
```

**OpenMP not available**  
Pass the correct flag for your compiler, e.g.:
```bash
make CASE=CDU VARIANT=Fortran-OMP EXTRA_FFLAGS=-fopenmp
```
(Most gfortran builds include OpenMP by default with `-fopenmp`.)

**CUDA binary crashes immediately**  
Verify that the `CUDA_ARCH` matches the installed GPU:
```bash
nvidia-smi --query-gpu=compute_cap --format=csv,noheader
make CASE=CVD VARIANT=CUDA CUDA_ARCH=sm_$(compute_cap_without_dot)
```

**Benchmark results show very high variance**  
Other processes are likely competing for resources.  Isolate the run (e.g. via a
job scheduler), increase `WARMUP_ROUNDS`, and/or increase `ROUNDS` to average out
noise.

**`ModuleNotFoundError: No module named 'matplotlib'`**  
Install dependencies into the active Python environment:
```bash
pip install matplotlib numpy
```

**`make test` reports `[FAIL]` with unexpectedly large differences**  
The kernel likely uses single-precision literals or accumulates in `float`.
Verify every arithmetic expression uses `double` (C++) or `real(knd)` (Fortran)
consistently across all variants.

**`make test` skips all non-Fortran variants**  
The compilers (`gfortran`, `g++`, `nvcc`) are not on `PATH`.  This is expected
on login nodes — run the tests on the same node used for benchmarking.
