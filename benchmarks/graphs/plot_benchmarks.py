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
import matplotlib.ticker as ticker
import numpy as np

# ── Paths ───────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent
RESULTS_CSV = SCRIPT_DIR.parent / 'results.csv'
FIGS_DIR    = SCRIPT_DIR / 'figs'
FIGS_DIR.mkdir(exist_ok=True)

# ── Publication style ───────────────────────────────────────────────────────────
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
    'grid.linewidth':           0.4,       # Lightened grid
    'grid.color':               '#E5E7EB', # Softer grey grid
    'xtick.bottom':             False,
    'ytick.left':               True,
    'ytick.major.size':         3.0,
    'ytick.major.width':        0.6,
    'figure.dpi':               150,
    'savefig.dpi':              300,
    'savefig.bbox':             'tight',
    'savefig.pad_inches':       0.08,
})

# ── Layout ──────────────────────────────────────────────────────────────────────
VARIANT_ORDER  = ['Fortran', 'CPP', 'Fortran-OMP', 'CPP-OMP', 'CUDA']
FUNCTION_ORDER = ['CDW', 'CDU', 'CDV', 'CVD']

# DESIGN FIX: Slimmer bars, wider gap between groups
BAR_WIDTH  = 0.13   
GROUP_GAP  = 0.25   

# ── Palette — Professional, story-driven colors ─────────────────────────────────
# CPU variants get professional, understated cool tones
C_FORTRAN     = '#1F3A5E'   # Deep Navy
C_CPP         = '#4A7C99'   # Steel Muted Blue
C_FORTRAN_OMP = '#1F3A5E'   # Navy (distinguished by hatch)
C_CPP_OMP     = '#4A7C99'   # Steel (distinguished by hatch)

# CUDA kernel gets a punchy accent color to draw the eye to the "blazing fast" part
C_KERNEL      = '#D7263D'   # Sharp Crimson Red

# Memory remains muted to show weight without dominating visually
C_MEM_MOV     = '#C4C4C4'   # Soft Grey
C_MEM_ALLOC   = '#EAEAEA'   # Very Light Grey

# Hatches for accessibility and OpenMP distinction
H_FORTRAN     = ''
H_CPP         = ''
H_FORTRAN_OMP = '////'      # Denser hatch for visibility
H_CPP_OMP     = '\\\\\\\\'  # Opposite direction for C++
H_KERNEL      = ''
H_MEM         = 'xxxx'
H_ALLOC       = '....'

ECOLOR = '#404040'          # Slightly softer error bar color

LEGEND_PATCHES = [
    mpatches.Patch(facecolor=C_FORTRAN,     hatch=H_FORTRAN,     edgecolor='white', label='Fortran (serial)'),
    mpatches.Patch(facecolor=C_CPP,         hatch=H_CPP,         edgecolor='white', label='C++ (serial)'),
    mpatches.Patch(facecolor=C_FORTRAN_OMP, hatch=H_FORTRAN_OMP, edgecolor='white', label='Fortran (OpenMP)'),
    mpatches.Patch(facecolor=C_CPP_OMP,     hatch=H_CPP_OMP,     edgecolor='white', label='C++ (OpenMP)'),
    mpatches.Patch(facecolor=C_KERNEL,      hatch=H_KERNEL,      edgecolor='white', label='CUDA — kernel'),
    mpatches.Patch(facecolor=C_MEM_MOV,     hatch=H_MEM,         edgecolor='white', label='CUDA — data transfer (H↔D)'),
    mpatches.Patch(facecolor=C_MEM_ALLOC,   hatch=H_ALLOC,       edgecolor='white', label='CUDA — malloc / free'),
]


# ── CSV helpers ─────────────────────────────────────────────────────────────────

def parse_cell(s: str) -> tuple:
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
    groups: dict = defaultdict(list)
    for r in rows:
        key = (r['grid_x'], r['grid_y'], r['grid_z'], r['iters'])
        groups[key].append(r)
    return groups


# ── Plotting ────────────────────────────────────────────────────────────────────

def plot_scenario(key: tuple, rows: list[dict], out_stem: str) -> None:
    gx, gy, gz, niter = key

    lookup = {(r['function'], r['variant']): r for r in rows}
    present_funcs = {r['function'] for r in rows}
    funcs = [f for f in FUNCTION_ORDER if f in present_funcs]
    funcs += sorted(present_funcs - set(funcs))

    n_funcs    = len(funcs)
    n_variants = len(VARIANT_ORDER)

    group_width  = n_variants * BAR_WIDTH + GROUP_GAP
    group_ctrs   = np.arange(n_funcs) * group_width
    offsets = (np.arange(n_variants) - (n_variants - 1) / 2) * BAR_WIDTH

    fig_w = 4.0 + n_funcs * 2.2  
    fig, ax = plt.subplots(figsize=(fig_w, 4.2))

    for vi, variant in enumerate(VARIANT_ORDER):
        for fi, func in enumerate(funcs):
            row = lookup.get((func, variant))
            if row is None:
                continue

            x = group_ctrs[fi] + offsets[vi]
            ebar_kw = dict(elinewidth=0.8, ecolor=ECOLOR, capsize=2.5,
                           capthick=0.8, zorder=6)

            if variant == 'CUDA':
                kernel_ms = row['cuda_kernel_run'] or 0.0
                mem_ms    = (row['cuda_h2d_ms'] or 0.0) + (row['cuda_d2h_ms'] or 0.0)
                alloc_ms  = (row['cuda_malloc_ms'] or 0.0) + (row['cuda_free_ms'] or 0.0)
                total_std = row['total_ms_std'] or 0.0

                ax.bar(x, kernel_ms, BAR_WIDTH,
                       color=C_KERNEL, hatch=H_KERNEL, edgecolor='white', linewidth=0.6, zorder=3)
                ax.bar(x, mem_ms, BAR_WIDTH, bottom=kernel_ms,
                       color=C_MEM_MOV, hatch=H_MEM, edgecolor='white', linewidth=0.6, zorder=3)
                ax.bar(x, alloc_ms, BAR_WIDTH, bottom=kernel_ms + mem_ms,
                       color=C_MEM_ALLOC, hatch=H_ALLOC, edgecolor='white', linewidth=0.6, zorder=3,
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
                       color=c, hatch=h, edgecolor='white', linewidth=0.6, zorder=3,
                       yerr=total_std, error_kw=ebar_kw)

    # ── Axes decoration ────────────────────────────────────────────────────────
    ax.set_xticks(group_ctrs)
    ax.set_xticklabels(funcs, fontsize=11)
    ax.set_ylabel('Execution time (ms)', labelpad=6)
    ax.set_xlabel('Kernel', labelpad=6)
    
    # Pad limits so bars don't hug the edges of the plot
    ax.set_xlim(group_ctrs[0] - group_width * 0.55,
                group_ctrs[-1] + group_width * 0.55)
    ax.set_ylim(bottom=0)
    
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    ax.set_title(
        f'Grid {gx}\u202f×\u202f{gy}\u202f×\u202f{gz},  {niter} iterations per call',
        pad=10,
    )

    # ── Legend ─────────────────────────────────────────────────────────────────
    present_variants = {r['variant'] for r in rows}

    def _variant_in_label(label):
        if 'Fortran' in label and 'OpenMP' not in label: return 'Fortran' in present_variants
        if 'Fortran (OpenMP)' in label:                  return 'Fortran-OMP' in present_variants
        if 'C++ (serial)' in label:                      return 'CPP' in present_variants
        if 'C++ (OpenMP)' in label:                      return 'CPP-OMP' in present_variants
        return 'CUDA' in present_variants

    visible_patches = [p for p in LEGEND_PATCHES if _variant_in_label(p.get_label())]
    
    ax.legend(handles=visible_patches, loc='upper left', bbox_to_anchor=(1.02, 1),
              title='Implementation', ncol=1, handlelength=1.6, handleheight=1.1,
              borderaxespad=0.)

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