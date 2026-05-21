# Benchmark Suite

Compares Fortran stencil kernels across five implementation variants (Fortran,
Fortran-OMP, CUDA, C++, C++-OMP) on three cases (CDU, CDW, CDV).  All builds go
through a single top-level `Makefile`.

---

## Quick Start

```bash
# Build and run a single benchmark (plain Fortran, default grid 64×64×64)
make CASE=CDV VARIANT=Fortran
./bin/CDV_Fortran_NX64_NY64_NZ64_NITER100_NWARMUP5/benchmark

# (Re-)generate all CUDA / C++ / C++-OMP sources from the Fortran originals
source ../venv/bin/activate
python generate_all_sources.py

# Run all cases/variants/grids automatically → results.csv
python run_bechmarks.py > results.csv

# Generate figures from results.csv
python graphs/plot_benchmarks.py
# → graphs/figs/grid_<NX>x<NY>x<NZ>_niter<N>.{png,pdf}
```

---

## Prerequisites

| Tool              | Minimum version | Notes                                                     |
| ----------------- | --------------- | --------------------------------------------------------- |
| GNU Make          | 3.81            | Standard on most Linux systems                            |
| gfortran          | 10+             | Or any Fortran 2003–compatible compiler; set `FC=`        |
| CUDA Toolkit      | 11+             | Only for `VARIANT=CUDA`; set `CUDA_HOME=` if non-standard |
| Python            | 3.9+            | Runner + graph scripts                                    |
| matplotlib, numpy | any recent      | `pip install matplotlib numpy`                            |

---

## Source Generation

The `CPP`, `CPP-OMP`, and `CUDA` variants use auto-generated sources.
`generate_all_sources.py` runs the `fort_to_cuda` compiler for every case and
writes results into the correct variant directories.  Re-run it when the Fortran
originals or the compiler change.

```bash
source ../venv/bin/activate
python generate_all_sources.py          # all cases
python generate_all_sources.py CDU CDV  # specific cases
```

Generated files are committed to the repository, so benchmarks can be built
without the compiler toolchain unless you change the sources.

---

## Building and Running a Benchmark

```bash
make CASE=<case> [VARIANT=<variant>] [NX=N NY=N NZ=N] [NITER=N] [CUDA_ARCH=sm_XX]
```

| Variable  | Default    | Values                                          |
| --------- | ---------- | ----------------------------------------------- |
| `CASE`    | `CDV`      | `CDU` \| `CDW` \| `CDV`                        |
| `VARIANT` | `Fortran`  | `Fortran` \| `Fortran-OMP` \| `CUDA` \| `CPP` \| `CPP-OMP` |
| `NX/NY/NZ`| `64`       | Grid dimensions                                 |
| `NITER`   | `100`      | Timed iterations                                |
| `CUDA_ARCH` | _(auto)_ | e.g. `sm_89` — required if auto-detection fails |

The binary lands in `bin/<CASE>_<VARIANT>_NX<n>_NY<n>_NZ<n>_NITER<n>_NWARMUP<n>/benchmark`.

```bash
make clean CASE=CDV VARIANT=Fortran   # remove one build
make clean-all                         # wipe all builds
```

---

## Automated Benchmark Runner

`run_bechmarks.py` sweeps all configured combinations, writes a semicolon-
separated CSV to stdout, and prints progress to stderr.

```bash
source ../venv/bin/activate
python run_bechmarks.py > results.csv
```

Edit the configuration at the top of the script to change what is benchmarked:

```python
FUNCTIONS     = ['CDW', 'CDU', 'CDV']
VARIANTS      = ['Fortran', 'Fortran-OMP', 'CUDA', 'CPP', 'CPP-OMP']
GRIDS         = [[512, 512, 512]]
ITERS         = [100]
WARMUP_ITERS  = 10    # warm-up iterations baked into the binary
WARMUP_ROUNDS = 2     # full-program rounds discarded before timing
ROUNDS        = 5     # full-program rounds whose results are recorded
```

---

## Correctness Tests

`run_tests.py` builds each variant on a 16×16×16 grid, runs once with a
deterministic initialisation, and compares every variant against the serial
Fortran reference.

```bash
python run_tests.py        # all cases
python run_tests.py CDU    # single case
```

Typical tolerances: `Fortran-OMP` / `CPP` are bit-exact; `CPP-OMP` ≤ 1e-12;
`CUDA` ≤ 1e-10.

---

## Generating Figures

```bash
source ../venv/bin/activate
python graphs/plot_benchmarks.py [--results FILE] [--omit-title] [--omit-error-bars]
```

Outputs `graphs/figs/grid_<NX>x<NY>x<NZ>_niter<N>.{png,pdf}`.  The y-axis is
normalised to **seconds per Gcell·iter** for cross-grid comparability.

---

## Troubleshooting

**"No rule to make target"** — `CASE` must match the subdirectory name exactly
(case-sensitive: `CDU`, `CDW`, `CDV`).

**`nvcc: command not found`** — set `CUDA_HOME` or add `nvcc` to `PATH`:
```bash
make CASE=CDV VARIANT=CUDA CUDA_HOME=/path/to/cuda
```

**CUDA binary crashes** — verify `CUDA_ARCH` matches your GPU:
```bash
nvidia-smi --query-gpu=compute_cap --format=csv,noheader
# then: make CASE=CDV VARIANT=CUDA CUDA_ARCH=sm_<result_without_dot>
```

**`ModuleNotFoundError: No module named 'matplotlib'`** — `pip install matplotlib numpy`.
