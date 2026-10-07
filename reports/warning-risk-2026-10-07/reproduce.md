# Reproduce the completed warning-risk study

**Complete:** 90 early/later heads, four policies, paired analysis and audit
finished with worker exit zero. This study adds no neural fit; preserve all
69 existing fits and all previous study files. Do not restart completed work.

This branch starts from the matched architecture report, `ae56ce4` (draft
PR #86). Commit `3b382337c4b4a8fb4a699d31e22a4506828998d2` freezes the
protocol, plan, selector, replay, analysis, audit, wrapper and tests before
new early-policy selection. All 43 source bindings are checked against that
commit. The analysis release cannot be backfilled after any early or later
artifact exists. Every early policy is frozen before later replay begins.

Use the existing CUDA Python environment without synchronizing the CPU lock.
The new work runs on CPU with completed scores; it does not retrain or rescore
models. All previous checkpoint, prediction and policy bindings are verified
through the original provenance chain before selecting new policies.

The exact completed command is:

```bash
bash scripts/evaluate_warning_risk.sh \
  /home/thivas/work/ai-portfolio/league-ews-audit/.venv/bin/python \
  /home/thivas/work/ai-portfolio/league-ews-audit \
  /home/thivas/work/ai-portfolio/league-ews-gpu \
  3b382337c4b4a8fb4a699d31e22a4506828998d2
```

The wrapper acquires one worker lock, selects all early policies, verifies
the complete early gate, replays later matches, calculates the paired
analysis and audits provenance. It writes a worker exit code. It resumes
already completed artifacts after checking their hashes. Never remove a
freeze, change a committed source or overwrite a release to bypass a gate.

The five families × three seeds × three events × two windows form 90 heads.
The exact original fine-grid common policy is reproduced from scores in both
halves, including each later match's six counts. The cap and risk policies
share the 1,002-entry grid, 60-second cooldown, four fixed budgets and
whole-match bootstrap draws. A separate scalar oracle checks every later
match for each of three new budget-one policies (810,000 checks), plus all
selected thresholds on a fixed match sample (25,699 checks).

The analysis preserves all four count metrics and their paired conditional
intervals, seed values, every nominal-budget failure and per-head cap activity.
The unchanged baseline reproduces 150 model and 150 shared-contrast groups
exactly. Descriptive event precision can be reconstructed from aggregate
timely-hit and warning counts. No private player or match-level data are
published in this report directory.

Render the complete tables and two standalone PNG/SVG figures with:

```bash
PYTHONPATH=/tmp/league-warning-plot-tools:.:src \
MPLCONFIGDIR=/tmp/league-warning-mpl \
  /home/thivas/work/ai-portfolio/league-ews-audit/.venv/bin/python \
  -m scripts.render_warning_risk \
  --output reports/warning-risk-2026-10-07 --plots
```

The plotting environment uses Matplotlib 3.11.2 and NumPy 2.5.3. Aggregate JSON
is losslessly compacted for publication; raw hashes remain in the execution
record and published bytes are bound separately. CSV line endings are LF.
Both four-panel figures were visually inspected. The renderer is a subsequent
presentation file and changes none of the frozen inference sources.

Validation before selection: 740 tests passed, one skipped, 85.86% source
coverage, including 36 new focused checks; Ruff, mypy on 87 files, shell syntax
and the secret check passed. The new checks cover independent replay, causal
caps, non-monotonic cost, bounded-loss tail inequalities, the first-failure
rule, regional constraints, silent fallback, paired intervals and immutable
analysis release. Synthetic fixtures are software checks, not League results.

The observed practical pass applies to this adaptively reused development
sample. It neither certifies the research search nor changes any prior gate.
The [report](research-report.md) records recall losses and failed regional and
no-extra-burden rules. Patch-16.17 payloads stay sealed.
