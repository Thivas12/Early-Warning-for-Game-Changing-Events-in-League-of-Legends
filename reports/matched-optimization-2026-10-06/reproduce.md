# Reproduce the matched architecture study

**Complete:** nine new fits, 342 policy heads, analysis and all audits finished.
The sequential scoring/evaluation worker exited zero. Preserve all checkpoints;
do not restart a completed training run. The [report](research-report.md)
records the limited primary gain and failed burden/regional rules.

The branch starts at completed optimizer commit `bd1831b` (draft PR #84).
Training protocol `f45933a` preceded the CUDA canary and nine fits. Analysis
commit `f5e2be605bfd46a16dc0799c9e26236840a54c0a` preceded the explicit scoring
release. The one-shard canary was resumed as part of the first equal-TCN fit;
it is not an additional fit. The inventory is now 69 completed neural fits.

Use the existing CUDA Python environment. The training freeze binds the
original source, development archive, normalizer, Python, PyTorch, NumPy and
GPU runtime. Do not synchronize a CPU dependency lock into that environment.
The plan's parameter counts differ by architecture and are verified per fit.
Exact backend parity and checkpoint-resume checks passed before fitting.

The nine variants/seeds complete all 576 shard updates each before any scoring.
`scripts.scoring_release.verify` requires the committed analysis, plan and
training freeze to match the non-overwritable release. Never backfill a release
after scoring. The training and scoring gates record every checkpoint hash
and zero-score observation. All scores retain twelve heads, including the
cumulative auxiliary heads; six evaluated event/horizon heads per fit enter
the useful-lead policy study.

From this worktree, the completed evaluation can be reproduced with:

```bash
bash scripts/evaluate_matched_optimization.sh \
  /home/thivas/work/ai-portfolio/league-ews-audit/.venv/bin/python \
  /home/thivas/work/ai-portfolio/league-ews-audit \
  /home/thivas/work/ai-portfolio/league-ews-gpu \
  f5e2be605bfd46a16dc0799c9e26236840a54c0a
```

The locked sequential wrapper resolves and verifies every preceding private
study, selects all 342 early heads, writes the early-before-later gate, replays
later matches, calculates paired analysis and audits the result. It checks
that scoring left all checkpoints unchanged. All 288 prior heads reproduce
under all five policies. New full reference replay covers 54 heads × 3,000
later matches × two common budget-one policies, or 324,000 checks. Component
replay adds 130,448 checks. Every prior model and contrast estimate reproduces.

All model, event, region, seed, policy and budget comparisons use shared paired
whole-match bootstrap draws. The two new architecture-by-weighting interactions
are formed inside each draw; all previous interactions remain present. The
primary is equal-weight LeagueEWS minus equal-weight TCN at 10–30 seconds.
GRU and longer-lead results cannot replace it. No parameter matching, baseline
hyperparameter optimization or fresh confirmation is claimed.

Generate aggregate tables and standalone PNG/SVG figures with:

```bash
PYTHONPATH=/tmp/league-warning-plot-tools:.:src \
MPLCONFIGDIR=/tmp/league-warning-mpl \
  /home/thivas/work/ai-portfolio/league-ews-audit/.venv/bin/python \
  -m scripts.render_matched_optimization \
  --output reports/matched-optimization-2026-10-06 --plots
```

The plotting environment uses Matplotlib 3.11.2 and NumPy 2.5.3 without
changing the CUDA environment. Rendering losslessly compacts aggregate JSON;
the execution record retains raw JSON hashes and the publication manifest
records published bytes. CSV line endings are normalized to LF before hashing.
Both six-panel figures were visually inspected.

The quality gate records 704 passed tests, one skipped and 85.86% coverage,
including 28 new focused tests; Ruff, mypy on 87 source files, the shell syntax
checks and secret check passed. All original studies remain frozen. Repeatedly
inspected calibration is exploratory, and patch-16.17 payloads remain sealed.
