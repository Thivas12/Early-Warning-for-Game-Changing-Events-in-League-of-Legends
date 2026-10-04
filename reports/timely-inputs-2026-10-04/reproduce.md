# Reproduce the useful-lead input controls

Use branch `research/league-timely-inputs-20261004`. Training and protocol were
committed at `039f927`. The evaluator and paired analysis were committed at
`9ccb4a6`, before any new calibration predictions; see `analysis-gate.json`.
Preserve the original GPU checkout, every completed study and their checkpoints.
Do not launch another training worker while this study holds its worker lock.

Execution uses the existing RTX 4060 Laptop GPU and Python 3.12.14 environment:
PyTorch 2.14.0+cu130, CUDA 13.0 and NumPy 2.5.3. Do not synchronize dependencies
against the repository's CPU development lockfile in this CUDA environment.

```bash
league_root=/home/thivas/work/ai-portfolio/league-ews-audit
league_python="$league_root/.venv/bin/python"
league_archive="$league_root/data/private/league-three-event-export-v1/development.zip"
league_source=/home/thivas/work/ai-portfolio/league-ews-gpu
league_control="$league_source/data/private/compact-notebook-v1"
league_timely="$league_root/data/private/league-timely-neural-v1"
league_inputs="$league_root/data/private/league-timely-inputs-v1"
league_output="$league_root/data/private/league-timely-input-policy-v1"
league_report=reports/timely-inputs-2026-10-04
league_control_plan=reports/timely-neural-2026-10-03/plan.json

# Inspect processes and progress before resuming. This wrapper rejects duplicates.
bash scripts/run_timely_inputs.sh "$league_python" "$league_archive" \
  "$league_control" "$league_inputs" "$league_report/plan.json" \
  "$league_source" "$league_timely"

league_args=(
  --archive "$league_archive" --control "$league_control"
  --history "$league_root/data/private/league-history-ablation-v1"
  --independent "$league_root/data/private/league-task-sharing-v1"
  --pcgrad "$league_root/data/private/league-pcgrad-v1"
  --study "$league_timely" --inputs "$league_inputs"
  --warning "$league_root/data/private/league-warning-efficiency-v1"
  --reference "$league_root/data/private/league-timely-policy-v1"
  --dense "$league_root/data/private/league-dense-policy-v1"
  --control-plan "$league_control_plan"
  --plan "$league_report/plan.json" --output "$league_output"
)
PYTHONPATH=.:src "$league_python" -u -m scripts.evaluate_timely_inputs \
  "${league_args[@]}" --early-only
# Record the joint policy freeze and zero later heads before the next command.
PYTHONPATH=.:src "$league_python" -u -m scripts.evaluate_timely_inputs "${league_args[@]}"
PYTHONPATH=.:src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$league_python" \
  -u -m scripts.analyse_timely_inputs --study "$league_output" \
  --archive "$league_archive" --plan "$league_report/plan.json" --output "$league_report"
PYTHONPATH=.:src "$league_python" -m scripts.audit_timely_input_results \
  --training "$league_inputs" --policy "$league_output" --output "$league_report"
PYTHONPATH=.:src "$league_python" -m scripts.render_timely_inputs --output "$league_report"
```

The one-shard CUDA canary precedes the wrapper on a new study; it was already
completed for this output. Never repeat a completed fit as a canary. Exact
continuation verifies model, optimizer, RNG, source, data, runtime and device.
The original worker later exited with native SIGSEGV during the final seed,
after 32 checkpointed updates. `recovery-record.json` records verification of
all six checkpoints, preservation of the crash log and partial-fit checkpoint,
and a successful one-shard continuation to update 33. The five completed model
hashes were unchanged. Recovery enabled `PYTHONFAULTHANDLER=1` for diagnostics
without changing training files, packages or settings. The native crash's root
cause was not established; a successful continuation is not proof of its repair.
All six fits finish before calibration scoring. The evaluator verifies all
198 score heads and freezes all early policies before evaluating any new later
head. An interrupted evaluation computes only missing heads after verifying
all preserved bindings. A fresh replay uses a new empty output directory.

Original coarse and matched-cost controls must reproduce every prior match
count and early selection. The four previous dense-grid variants must also
reproduce their entire early grid and later counts. For each of the 36 new
heads, the original and dense common budget-one policies receive independent
replay on every later match. Selected component thresholds receive additional
fixed-sample checks across all heads. The paired bootstrap uses the same 2,000
region-stratified whole-match draws for every variant and seed; seeds remain
fixed fitted models, and repeated budgets remain fixed operating points.

Optional plots use the existing isolated Matplotlib installation without changing
the training environment:

```bash
PYTHONPATH=/tmp/league-warning-plot-tools:.:src MPLCONFIGDIR=/tmp/league-warning-mpl \
  "$league_python" -m scripts.render_timely_inputs --output "$league_report" --plots
```

Rendering losslessly formats aggregate JSON. Preserve raw and published hashes
in the execution record. Public CSV files contain only aggregate counts, fixed
seed estimates and budget failures. Explicitly stage these ignored data-like
files; never stage private scores, matches or checkpoints. Patch 16.17 is not
required and remains sealed.

Before calibration scoring, the CPU review environment passed 627 tests, one
skipped, with 85.89% coverage. Ruff passed and mypy passed 87 source files.
Eight new checks cover both input interventions, checkpoint continuation,
nonfinite-update preservation, gated scoring, coarse/dense/mixture indexing,
paired target-history interaction and policy gate/resume/tamper behavior.
These implementation fixtures are not empirical League evidence.
