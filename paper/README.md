# Manuscript

The current three-event continuation is the
[LeagueEWS controlled-evaluation working paper](leagueews-2026-10/leagueews-working-paper.pdf).
Its [source and reproduction guide](leagueews-2026-10/README.md) include the
completed studies, source-derived figures and saved-model runtime measurements.
It remains exploratory, with fresh confirmation pending.

## Preserved legacy-audit paper

`main.tex` is a working-paper draft built from the committed legacy audit. It
is intentionally framed as an evaluation/reproducibility result, not as the
unfinished RiftHazard method paper.

Build locally:

```bash
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Generated build files are ignored. Numeric edits must be traced back to the
machine-readable files under `reports/`.
