#!/usr/bin/env python3
"""
graphs/plot_benchmarks.py

Reads ../results.csv and writes one figure per unique (grid, iters) combination.
Output: graphs/figs/grid_{gx}x{gy}x{gz}_niter{niter}.{png,pdf}

Message the figure conveys:
  "Memory transfer dominates CUDA cost; the kernel itself is blazing fast."
"""

import csv
import re
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

# ── Paths ───────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent
RESULTS_CSV = SCRIPT_DIR.parent / 'results.csv'
FIGS_DIR    = SCRIPT_DIR / 'figs'
FIGS_DIR.mkdir(exist_ok=True)

# ── Publication style (apply before any figure is created) ──────────────────────
plt.rcParams.update({
    'font.family':              'sans-serif',
    'font.size':                9,
    'axes.labelsize':           10,
    'axes.titlesize':           10,
    'axes.titleweight':         'normal',
    'axes.labelweight':         'normal',
    'xtick.labelsize':          11,
    'ytick.labelsize':          9,
    'legend.fontsize':          8.5,
    'legend.title_fontsize':    9,
    'legend.framealpha':        0.95,
    'legend.edgecolor':         '#cccccc',
    'legend.borderpad':         0.6,
    'axes.linewidth':           0.7,
    'axes.spines.top':          False,
    'axes.spines.right':        False,
    'axes.grid':                True,
    'axes.axisbelow':           True,
    'grid.linewidth':           0.5,
    'grid.color':               '#e0e0e0',
    'xtick.bottom':             False,
    'ytick.left':               True,
    'ytick.major.size':         3.5,
    'ytick.major.width':        0.7,
    'figure.dpi':               150,
    'savefig.dpi':              300,
    'savefig.bbox':             'tight',
    'savefig.pad_inches':       0.08,
})

# ── Layout ──────────────────────────────────────────────────────────────────────
VARIANT_ORDER  = ['Fortran', 'Fortran-OMP', 'CUDA', 'CPP', 'CPP-OMP']
FUNCTION_ORDER = ['CDW', 'CDU', 'CDV', 'CVD']   # fallback order; actual order from CSV

BAR_WIDTH  = 0.16   # width of a single bar (narrower to fit 5 per group)
GROUP_GAP  = 0.12   # extra space between function groups

# ── Palette — Wong (2011) colorblind-safe ────────────────────────────────────────
#   blue          amber         green         vermillion    gray
C_FORTRAN     = '#0072B2'
C_FORTRAN_OMP = '#E69F00'
C_KERNEL      = '#009E73'   # fast — green
C_MEM_MOV     = '#D55E00'   # bottleneck — vermillion
C_MEM_ALLOC   = '#CCCCCC'   # minor overhead — gray
C_CPP         = '#56B4E9'   # sky blue
C_CPP_OMP     = '#CC79A7'   # reddish purple

# Hatches for B&W / accessibility
H_FORTRAN     = ''
H_FORTRAN_OMP = '///'
H_KERNEL      = ''
H_MEM         = 'xxx'
H_ALLOC       = '...'
H_CPP         = '\\\\\\'
H_CPP_OMP     = 'ooo'

ECOLOR = '#333333'

LEGEND_PATCHES = [
    mpatches.Patch(facecolor=C_FORTRAN,     hatch=H_FORTRAN,     edgecolor='white', label='Fortran (serial)'),
    mpatches.Patch(facecolor=C_FORTRAN_OMP, hatch=H_FORTRAN_OMP, edgecolor='white', label='Fortran (OpenMP)'),
    mpatches.Patch(facecolor=C_KERNEL,      hatch=H_KERNEL,      edgecolor='white', label='CUDA — kernel'),
    mpatches.Patch(facecolor=C_MEM_MOV,     hatch=H_MEM,         edgecolor='white', label='CUDA — data transfer (H↔D)'),
    mpatches.Patch(facecolor=C_MEM_ALLOC,   hatch=H_ALLOC,       edgecolor='white', label='CUDA — malloc / free'),
    mpatches.Patch(facecolor=C_CPP,         hatch=H_CPP,         edgecolor='white', label='C++ (serial)'),
    mpatches.Patch(facecolor=C_CPP_OMP,     hatch=H_CPP_OMP,     edgecolor='white', label='C++ (OpenMP)'),
]


# ── CSV helpers ─────────────────────────────────────────────────────────────────

def parse_cell(s: str) -> tuple:
    """Parse 'mean+-std' or plain number.  Returns (mean, std)."""
    s = s.strip()
    if not s:
        return None, 0.0
    m = re.match(r'([\d.]+)\+-([\d.]+)', s)
    if m:
        return float(m.group(1)), float(m.group(2))
    try:
        return float(s), 0.0
    except ValueError:
        return None, 0.0


def load_csv(path: Path) -> list[dict]:
    rows = []
    with open(path) as fh:
        reader = csv.DictReader(fh, delimiter=';')
        for raw in reader:
            r: dict = {
                'function': raw['function'],
                'variant':  raw['variant'],
                'grid_x':   int(raw['grid_x']),
                'grid_y':   int(raw['grid_y']),
                'grid_z':   int(raw['grid_z']),
                'iters':    int(raw['iters']),
            }
            for col in ('cuda_malloc_ms', 'cuda_h2d_ms', 'cuda_kernel_run',
                        'cuda_d2h_ms', 'cuda_free_ms', 'total_ms'):
                mean, std = parse_cell(raw.get(col, ''))
                r[col]            = mean
                r[col + '_std']   = std
            rows.append(r)
    return rows


def group_by_scenario(rows: list[dict]) -> dict:
    """Group rows by (grid_x, grid_y, grid_z, iters)."""
    groups: dict = defaultdict(list)
    for r in rows:
        key = (r['grid_x'], r['grid_y'], r['grid_z'], r['iters'])
        groups[key].append(r)
    return groups


# ── Plotting ────────────────────────────────────────────────────────────────────

def plot_scenario(key: tuple, rows: list[dict], out_stem: str) -> None:
    gx, gy, gz, niter = key

    # Build lookup: (function, variant) → row
    lookup = {(r['function'], r['variant']): r for r in rows}

    # Use only functions present in this scenario, in preferred order
    present_funcs = {r['function'] for r in rows}
    funcs = [f for f in FUNCTION_ORDER if f in present_funcs]
    funcs += sorted(present_funcs - set(funcs))

    n_funcs    = len(funcs)
    n_variants = len(VARIANT_ORDER)

    group_width  = n_variants * BAR_WIDTH + GROUP_GAP
    group_ctrs   = np.arange(n_funcs) * group_width
    offsets = (np.arange(n_variants) - (n_variants - 1) / 2) * BAR_WIDTH

    fig_w = 3.0 + n_funcs * 2.4   # ~7.2" for 3 functions — double-column friendly
    fig, ax = plt.subplots(figsize=(fig_w, 4.2))

    for vi, variant in enumerate(VARIANT_ORDER):
        for fi, func in enumerate(funcs):
            row = lookup.get((func, variant))
            if row is None:
                continue

            x = group_ctrs[fi] + offsets[vi]
            ebar_kw = dict(elinewidth=0.9, ecolor=ECOLOR, capsize=3,
                           capthick=0.9, zorder=6)

            if variant == 'CUDA':
                kernel_ms = row['cuda_kernel_run'] or 0.0
                mem_ms    = (row['cuda_h2d_ms'] or 0.0) + (row['cuda_d2h_ms'] or 0.0)
                alloc_ms  = (row['cuda_malloc_ms'] or 0.0) + (row['cuda_free_ms'] or 0.0)
                total_std = row['total_ms_std'] or 0.0

                ax.bar(x, kernel_ms, BAR_WIDTH,
                       color=C_KERNEL, hatch=H_KERNEL, edgecolor='white', linewidth=0.5, zorder=3)
                ax.bar(x, mem_ms, BAR_WIDTH, bottom=kernel_ms,
                       color=C_MEM_MOV, hatch=H_MEM, edgecolor='white', linewidth=0.5, zorder=3)
                ax.bar(x, alloc_ms, BAR_WIDTH, bottom=kernel_ms + mem_ms,
                       color=C_MEM_ALLOC, hatch=H_ALLOC, edgecolor='white', linewidth=0.5, zorder=3,
                       yerr=total_std, error_kw=ebar_kw)

            else:
                total_ms  = row['total_ms'] or 0.0
                total_std = row['total_ms_std'] or 0.0
                palette = {
                    'Fortran':     (C_FORTRAN,     H_FORTRAN),
                    'Fortran-OMP': (C_FORTRAN_OMP, H_FORTRAN_OMP),
                    'CPP':         (C_CPP,         H_CPP),
                    'CPP-OMP':     (C_CPP_OMP,     H_CPP_OMP),
                }
                c, h = palette.get(variant, (C_FORTRAN, H_FORTRAN))
                ax.bar(x, total_ms, BAR_WIDTH,
                       color=c, hatch=h, edgecolor='white', linewidth=0.5, zorder=3,
                       yerr=total_std, error_kw=ebar_kw)

    # ── Axes decoration ────────────────────────────────────────────────────────
    ax.set_xticks(group_ctrs)
    ax.set_xticklabels(funcs, fontsize=11)
    ax.set_ylabel('Execution time (ms)', labelpad=6)
    ax.set_xlabel('Kernel', labelpad=6)
    ax.set_xlim(group_ctrs[0] - group_width * 0.55,
                group_ctrs[-1] + group_width * 0.55)
    ax.set_ylim(bottom=0)

    ax.set_title(
        f'Grid {gx}\u202f×\u202f{gy}\u202f×\u202f{gz},  {niter} iterations per call',
        pad=10,
    )

    ax.spines['left'].set_linewidth(0.7)
    ax.spines['bottom'].set_linewidth(0.7)

    # ── Legend ─────────────────────────────────────────────────────────────────
    present_variants = {r['variant'] for r in rows}

    def _variant_in_label(label):
        if 'serial' in label and 'C++' not in label:   return 'Fortran' in present_variants
        if 'OpenMP' in label and 'C++' not in label:   return 'Fortran-OMP' in present_variants
        if 'C++ (serial)' in label:                    return 'CPP' in present_variants
        if 'C++ (OpenMP)' in label:                    return 'CPP-OMP' in present_variants
        return 'CUDA' in present_variants   # all three CUDA entries

    visible_patches = [p for p in LEGEND_PATCHES if _variant_in_label(p.get_label())]
    ax.legend(handles=visible_patches, loc='upper right',
              title='Implementation', ncol=1, handlelength=1.6, handleheight=1.1,
              borderaxespad=0.7)

    fig.tight_layout()

    for ext in ('png', 'pdf'):
        dest = FIGS_DIR / f'{out_stem}.{ext}'
        fig.savefig(dest)
        print(f'  saved → {dest}')

    plt.close(fig)


# ── Entry point ─────────────────────────────────────────────────────────────────

def main() -> None:
    if not RESULTS_CSV.exists():
        raise FileNotFoundError(f'Results file not found: {RESULTS_CSV}')

    rows   = load_csv(RESULTS_CSV)
    groups = group_by_scenario(rows)

    print(f'Found {len(rows)} rows across {len(groups)} scenario(s).')

    for key in sorted(groups):
        gx, gy, gz, niter = key
        stem = f'grid_{gx}x{gy}x{gz}_niter{niter}'
        print(f'Plotting {stem} ...')
        plot_scenario(key, groups[key], stem)

    print('Done.')


if __name__ == '__main__':
    main()
