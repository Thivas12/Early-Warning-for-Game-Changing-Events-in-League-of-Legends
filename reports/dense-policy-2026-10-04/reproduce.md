# Reproduce the threshold-resolution control

Run from `research/league-dense-policy-20261004`. The plan, evaluator and paired
analysis were committed at `4c89cc6`, before any new early policy was selected.
No neural training or GPU allocation is needed. Preserve all completed fits and
the CUDA environment. Execution used Python 3.12.14 and NumPy 2.5.3.

```bash
league_root=/home/thivas/work/ai-portfolio/league-ews-audit
league_python="$league_root/.venv/bin/python"
league_archive="$league_root/data/private/league-three-event-export-v1/development.zip"
league_control=/home/thivas/work/ai-portfolio/league-ews-gpu/data/private/compact-notebook-v1
league_reference="$league_root/data/private/league-timely-policy-v1"
league_output="$league_root/data/private/league-dense-policy-v1"
league_report=reports/dense-policy-2026-10-04
league_control_plan=reports/timely-neural-2026-10-03/plan.json
league_args=(
  --archive "$league_archive" --control "$league_control"
  --history "$league_root/data/private/league-history-ablation-v1"
  --independent "$league_root/data/private/league-task-sharing-v1"
  --pcgrad "$league_root/data/private/league-pcgrad-v1"
  --study "$league_root/data/private/league-timely-neural-v1"
  --warning "$league_root/data/private/league-warning-efficiency-v1"
  --reference "$league_reference" --control-plan "$league_control_plan"
  --plan "$league_report/plan.json" --output "$league_output"
)
PYTHONPATH=.:src "$league_python" -u -m scripts.evaluate_dense_policy \
  "${league_args[@]}" --early-only
# All 72 early heads must be jointly frozen before this second command.
PYTHONPATH=.:src "$league_python" -u -m scripts.evaluate_dense_policy "${league_args[@]}"
PYTHONPATH=.:src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$league_python" \
  -u -m scripts.analyse_dense_policy --study "$league_output" \
  --reference "$league_reference" --control-plan "$league_control_plan" \
  --archive "$league_archive" --plan "$league_report/plan.json" --output "$league_report"
PYTHONPATH=.:src "$league_python" -m scripts.render_dense_policy --output "$league_report"
```

The runner verifies all completed controls, reference policies, archive and
source identities, and holds exclusive output/shared input locks. A completed
run resumes by verifying saved counts; an interrupted run selects/evaluates only
missing heads. Never delete its freeze or overwrite a control. A fresh replay
uses a new empty output directory. The dense grid nests the original candidates
exactly and reproduces their early counts before selection. Each new budget-one
policy is independently replayed on every later match; all other component
thresholds receive a fixed sample check.

Optional figures use the existing isolated Matplotlib 3.11.2 installation,
without changing the research environment:

```bash
PYTHONPATH=/tmp/league-warning-plot-tools:.:src MPLCONFIGDIR=/tmp/league-warning-mpl \
  "$league_python" -m scripts.render_dense_policy --output "$league_report" --plots
```

The renderer losslessly formats aggregate JSON and removes generated SVG trailing
whitespace. The execution record preserves raw and published digests. Public
CSV files contain aggregate counts and fixed-seed results; they must be explicitly
staged because data-like files are ignored. Per-match arrays and model binaries
remain private. Patch 16.17 is neither read nor needed.

The CPU review environment passes 619 tests (one skipped), 85.89% coverage,
including four new nested-grid, regional replay, paired-interaction and gated
resume/tamper checks. Ruff is clean; mypy passes all 87 source files. Those
fixtures validate implementation only and do not contribute empirical evidence.
