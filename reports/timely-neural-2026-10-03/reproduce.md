# Reproduce the timely-target neural control

Use the existing League development ZIP and immutable completed controls. Patch
16.17 is absent from this archive and remains prohibited. Preserve the original
GPU source checkout, environment and outputs. The study is on the separate
`research/league-timely-neural-20261003` branch. Training was committed at
`eeaf25b`, and the evaluation and analysis at `d26fe75` before any new calibration
predictions. The analysis and evaluation gate records document the chronology.

The six fits use Python 3.12.14, PyTorch 2.14.0+cu130, CUDA 13.0 and the RTX 4060
Laptop GPU. Evaluation uses NumPy 2.5.3. Do not install into or synchronize the
research environment. Source, runtime, archive, normalizer and control digests
are checked by the runners. Completed output resumes by verification; it does
not retrain. A fresh reproduction requires new output directories.

```bash
league_root=/home/thivas/work/ai-portfolio/league-ews-audit
league_python="$league_root/.venv/bin/python"
league_archive="$league_root/data/private/league-three-event-export-v1/development.zip"
league_control=/home/thivas/work/ai-portfolio/league-ews-gpu/data/private/compact-notebook-v1
league_control_source=/home/thivas/work/ai-portfolio/league-ews-gpu
league_history="$league_root/data/private/league-history-ablation-v1"
league_independent="$league_root/data/private/league-task-sharing-v1"
league_pcgrad="$league_root/data/private/league-pcgrad-v1"
league_warning="$league_root/data/private/league-warning-efficiency-v1"
league_training="$league_root/data/private/league-timely-neural-v1"
league_policy="$league_root/data/private/league-timely-policy-v1"
league_report=reports/timely-neural-2026-10-03

# Inspect workers first. The wrapper holds an exclusive training lock.
bash scripts/run_timely_neural.sh "$league_python" "$league_archive" \
  "$league_control" "$league_training" "$league_report/plan.json" "$league_control_source"

# All six fits must finish before scores are written. Only then select policies.
league_eval_args=(
  --archive "$league_archive" --control "$league_control" --history "$league_history"
  --independent "$league_independent" --pcgrad "$league_pcgrad"
  --study "$league_training" --warning "$league_warning"
  --plan "$league_report/plan.json" --output "$league_policy"
)
PYTHONPATH=.:src "$league_python" -u -m scripts.evaluate_timely_neural \
  "${league_eval_args[@]}" --early-only
# The complete 162-head early-policy freeze must exist before opening this gate.
PYTHONPATH=.:src "$league_python" -u -m scripts.evaluate_timely_neural \
  "${league_eval_args[@]}"

PYTHONPATH=.:src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$league_python" \
  -u -m scripts.analyse_timely_neural --study "$league_policy" \
  --archive "$league_archive" --plan "$league_report/plan.json" --output "$league_report"
PYTHONPATH=.:src "$league_python" -m scripts.render_timely_neural --output "$league_report"
```

The evaluator holds an exclusive output lock and shared locks on every control,
including the completed timely training. On interruption, rerun the identical
command. Do not delete the freeze, change sources or overwrite a checkpoint.
Every old head's two previously evaluated policies must reproduce every saved
match count at every budget exactly. Every new head also receives independent
reference replay on all 3,000 later matches for the original budget-one policy,
plus sampled reference replay for every component threshold.

Only aggregates, frozen policy definitions and artifact hashes are published.
Per-match arrays, scores, checkpoints and the development ZIP remain private.
The report renderer losslessly compacts JSON; raw and published hashes are
recorded separately. CSVs must be explicitly staged because data-like files are
ignored by the repository. Optional plots use Matplotlib 3.11.2 from the existing
isolated `/tmp/league-warning-plot-tools` installation:

```bash
PYTHONPATH=/tmp/league-warning-plot-tools:.:src MPLCONFIGDIR=/tmp/league-warning-mpl \
  "$league_python" -m scripts.render_timely_neural --output "$league_report" --plots
```

The unchanged CPU review environment ran the full suite: 615 passed, one skipped,
85.89% coverage. All 11 new tests passed, covering next-event/boundary semantics,
input isolation, exact model/optimizer/RNG resume, nonfinite-checkpoint protection,
all-fit and all-early gates, reference replay, policy controls, paired differences
and each frozen gate. Mypy passed all 87 source files. Tests are implementation
checks, not empirical League evidence.
