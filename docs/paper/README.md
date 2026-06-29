# Typed Composition Search — Paper

ACL-style LaTeX paper: "Typed Composition Search: Entity-Based Tool Routing for Large Tool Ecosystems"

## Structure

```
docs/paper/
├── main.tex                  # Master document
├── acl.sty                   # ACL style file
├── acl_natbib.bst            # ACL bibliography style
├── references.bib            # Bibliography
├── sections/
│   ├── abstract.tex          # Abstract
│   ├── introduction.tex      # Sec 1 — Motivation, Figure 1, contributions
│   ├── background.tex        # Sec 2 — Tool routing, existing approaches, why entities
│   ├── method.tex            # Sec 3 — Formal definition, typed transformations, BFS, hypotheses
│   ├── experimental_setup.tex# Sec 4 — Domains, models, queries, strategies, metrics
│   ├── results.tex           # Sec 5 — Main results, hallucinations, decomposition, pruning
│   ├── analysis.tex          # Sec 6 — Errors, regressions, mechanistic explanation
│   ├── related_work.tex      # Sec 7 — PLaG, ControlLLM, GRAFT, positioning
│   ├── limitations.tex       # Sec 8 — Typed graph assumption, linear composition, BFS write ops
│   └── conclusion.tex        # Sec 9
├── figures/
│   └── table_*.tex           # Generated LaTeX tables (7 total)
└── scripts/
    └── generate_tables.py    # Extracts tables from benchmarks/results/*.json
```

## Compiling

### Docker (recommended)

No local install needed — just Docker:

```bash
cd docs/paper
docker run --rm -v "$PWD:/work" -w /work texlive/texlive:latest \
  sh -c "pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex"
```

For a smaller image (~500MB vs ~5GB), use [blang/latex](https://github.com/blang/latex-docker):

```bash
docker run --rm -v "$PWD:/data" blang/latex:ctanbasic \
  sh -c "pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex"
```

### Local LaTeX

```bash
brew install --cask mactex   # macOS
cd docs/paper
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

### Overleaf

Upload the `docs/paper/` directory to [Overleaf](https://www.overleaf.com).

## Regenerating tables

Tables in `figures/` are generated from benchmark result JSONs:

```bash
python3 scripts/generate_tables.py
```

This reads from `benchmarks/results/*.json` and writes 7 `.tex` files into `figures/`.

## Key numbers

| Metric | Value |
|--------|-------|
| Model–domain combinations improved | 19/19 |
| Avg ΔF1 (graph − baseline) | +0.33 |
| Hallucinated tools (graph) | 0 (structural guarantee) |
| R_wrong (fault tolerance) | 0.415 |
| Entity pruning range | 56–87% |
| Tool space reduction | 97–99% |
| Domains | 5 (54–170 tools each) |
| Models | 4 (8B–20B+ params) |
| Total queries | 140 |
