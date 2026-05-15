import os
import re
import statistics
import subprocess
import sys

# ── Configuration ──────────────────────────────────────────────────────────────
FUNCTIONS    = ['CDW', 'CDU', 'CDV']
VARIANTS     = ['Fortran', 'Fortran-OMP', 'CUDA']
# GRIDS        = [[64, 64, 64], [128, 128, 128], [256, 256, 128]]
GRIDS        = [[256, 256, 256]]
ITERS        = [100]
WARMUP_ITERS = 10   # in-kernel warm-up iterations passed to the binary
WARMUP_ROUNDS = 2   # full-program rounds whose timing is discarded
ROUNDS        = 5   # full-program rounds whose timing is collected

# ───────────────────────────────────────────────────────────────────────────────

BENCHMARKS_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_SEP = ';'

CSV_HEADER = CSV_SEP.join([
    'function', 'variant', 'rounds',
    'grid_x', 'grid_y', 'grid_z',
    'iters', 'warmup_iters', 'warmup_turns',
    'cuda_malloc_ms', 'cuda_h2d_ms', 'cuda_h2d_gbps',
    'cuda_kernel_run', 'cuda_d2h_ms', 'cuda_d2h_gbps',
    'cuda_free_ms', 'total_ms',
])


# ── Helpers ────────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def fmt(values: list[float]) -> str:
    """Return 'mean+-stddev' with 3 decimal places, or '' for an empty list."""
    if not values:
        return ''
    mean = statistics.mean(values)
    std  = statistics.stdev(values) if len(values) > 1 else 0.0
    return f'{mean:.3f}+-{std:.3f}'


def binary_path(case: str, variant: str,
                nx: int, ny: int, nz: int,
                niter: int, nwarmup: int) -> str:
    build_id = f'{case}_{variant}_NX{nx}_NY{ny}_NZ{nz}_NITER{niter}_NWARMUP{nwarmup}'
    return os.path.join(BENCHMARKS_DIR, 'bin', build_id, 'benchmark')


def build(case: str, variant: str,
          nx: int, ny: int, nz: int,
          niter: int, nwarmup: int) -> str:
    """Ensure the benchmark binary exists; build if needed. Returns binary path."""
    path = binary_path(case, variant, nx, ny, nz, niter, nwarmup)
    if os.path.exists(path):
        return path

    log(f'  building {case}/{variant} {nx}x{ny}x{nz} niter={niter} nwarmup={nwarmup} ...')
    result = subprocess.run(
        ['make',
         f'CASE={case}', f'VARIANT={variant}',
         f'NX={nx}', f'NY={ny}', f'NZ={nz}',
         f'NITER={niter}', f'NWARMUP={nwarmup}'],
        cwd=BENCHMARKS_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f'Build failed:\n{result.stderr.strip()}')
    return path


def run_once(binary: str) -> str:
    """Run the benchmark binary once and return its stdout."""
    result = subprocess.run(
        [binary],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f'Run failed:\n{result.stderr.strip()}')
    return result.stdout


# ── Output parsers ─────────────────────────────────────────────────────────────

def parse_fortran(output: str) -> float:
    """Parse total_ms from a Fortran/Fortran-OMP benchmark run."""
    m = re.search(r'total_ms:\s+([\d.]+)\s+ms', output)
    if not m:
        raise ValueError(f'Could not find total_ms in output:\n{output}')
    return float(m.group(1))


def parse_cuda(output: str) -> dict[str, float]:
    """Parse the CUDA timing summary block. Returns a dict of floats."""
    def get(pattern):
        m = re.search(pattern, output)
        return float(m.group(1)) if m else 0.0

    return {
        'malloc_ms':  get(r'malloc_total_ms:\s+([\d.]+)'),
        'h2d_ms':     get(r'h2d_total_ms:\s+([\d.]+)'),
        'h2d_gbps':   get(r'h2d_total_ms:.*?\(([\d.]+)\s+GBps\)'),
        'kernel_ms':  get(r'kernel_total_ms:\s+([\d.]+)'),
        'd2h_ms':     get(r'd2h_total_ms:\s+([\d.]+)'),
        'd2h_gbps':   get(r'd2h_total_ms:.*?\(([\d.]+)\s+GBps\)'),
        'free_ms':    get(r'free_total_ms:\s+([\d.]+)'),
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def run_combination(case, variant, nx, ny, nz, niter) -> str:
    """Build, warm up, measure, and return a CSV row string."""
    binary = build(case, variant, nx, ny, nz, niter, WARMUP_ITERS)

    log(f'  warmup ({WARMUP_ROUNDS} rounds) ...')
    for _ in range(WARMUP_ROUNDS):
        run_once(binary)

    log(f'  measuring ({ROUNDS} rounds) ...')
    outputs = [run_once(binary) for _ in range(ROUNDS)]

    prefix = CSV_SEP.join(str(x) for x in [
        case, variant, ROUNDS, nx, ny, nz, niter, WARMUP_ITERS, WARMUP_ROUNDS,
    ])

    if variant == 'CUDA':
        data = [parse_cuda(o) for o in outputs]
        def col(key):
            return fmt([d[key] for d in data])
        total = fmt([
            d['malloc_ms'] + d['h2d_ms'] + d['kernel_ms'] + d['d2h_ms'] + d['free_ms']
            for d in data
        ])
        suffix = CSV_SEP.join([
            col('malloc_ms'), col('h2d_ms'), col('h2d_gbps'),
            col('kernel_ms'), col('d2h_ms'), col('d2h_gbps'),
            col('free_ms'), total,
        ])
    else:
        totals = [parse_fortran(o) for o in outputs]
        suffix = CSV_SEP.join(['', '', '', '', '', '', '', fmt(totals)])

    return prefix + CSV_SEP + suffix


def main():
    print(CSV_HEADER, flush=True)

    for case in FUNCTIONS:
        for variant in VARIANTS:
            for (nx, ny, nz) in GRIDS:
                for niter in ITERS:
                    label = f'{case}/{variant} {nx}x{ny}x{nz} niter={niter}'
                    log(f'[{label}]')
                    try:
                        row = run_combination(case, variant, nx, ny, nz, niter)
                        print(row, flush=True)
                    except Exception as exc:
                        log(f'  ERROR: {exc}')


if __name__ == '__main__':
    main()

