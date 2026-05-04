# fortran-tool-v2

Translate/analyze Fortran sources with Python tooling built around `fparser`.

## Project layout

- `compiler/`: Python package with parsing and compiler-side logic.
- `fortran-stencils/`: sample/input Fortran sources.

## Setup

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

   `python -m pip install -r requirements.txt`

## Run

Run from the repository root:

`python -m compiler`

Important: do not run `compiler/main.py` directly. Running as a module keeps package imports stable when files move into subdirectories.

## VS Code

This repo includes a launch configuration at `.vscode/launch.json`:

- **Run compiler package**: runs `python -m compiler` from the workspace root.

In the Run and Debug panel, select **Run compiler package** and start debugging.

## Import strategy for future refactors

- Keep `compiler/` as a package (it has `__init__.py`).
- Use relative imports inside the package (example: `from .fparser_tree_abstraction import FparserTree`).
- For subpackages, add `__init__.py` and keep using relative imports.
- Keep execution from repo root with `python -m compiler`.
