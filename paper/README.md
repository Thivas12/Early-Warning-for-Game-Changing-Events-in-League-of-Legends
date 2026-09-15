# Manuscript

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
