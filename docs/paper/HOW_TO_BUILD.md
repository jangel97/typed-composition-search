# Building the Paper

## Prerequisites

A LaTeX distribution with `pdflatex` and `bibtex`. On macOS, install [MacTeX](https://tug.org/mactex/).

## Build

```bash
cd docs/paper
pdflatex -interaction=nonstopmode main
bibtex main
pdflatex -interaction=nonstopmode main
pdflatex -interaction=nonstopmode main
```

Output: `main.pdf` (17 pages).

## Clean

```bash
rm -f main.aux main.bbl main.blg main.log main.out main.pdf
```

## Regenerate Tables and Figures

Tables and figures are generated from benchmark result JSONs:

```bash
cd docs/paper
uv run python scripts/generate_tables.py
```

This reads from `benchmarks/results/` and writes `.tex` files to `figures/`.

## Overleaf

To upload to Overleaf, create a zip excluding build artifacts:

```bash
cd docs/paper
zip -r typed_composition_routing.zip . -x "./main.pdf" "*.aux" "*.bbl" "*.blg" "*.log" "*.out" "*.fls" "*.fdb_latexmk" "*.synctex.gz" ".DS_Store" "*__pycache__*" "*.pyc" "*.zip" "*.png"
```

Then use **New Project > Upload Project** in Overleaf.
