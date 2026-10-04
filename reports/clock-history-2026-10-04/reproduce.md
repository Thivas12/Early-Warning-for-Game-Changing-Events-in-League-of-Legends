# Reproduce the conditional history control

Branch: `research/league-clock-history-20261004`, based on completed input study
`966f89a` (draft PR #81). Training and protocol: `997e299`. Evaluation and paired
analysis: `98346c3`. The [analysis gate](analysis-gate.json) was written at
14:35 UTC with 524 checkpointed updates and zero new predictions. Git approval
returned later: the commit is timestamped 16:37 UTC, after predictions at
15:01 UTC. The unchanged source hashes match the earlier record, but the planned
commit-before-scoring order was not met. See [the timing deviation](protocol-deviation.json);
do not call this a pre-scoring Git registration. Preserve every frozen artifact.

The environment is the existing RTX 4060 Laptop GPU (8 GB), driver 610.74,
Python 3.12.14, PyTorch 2.14.0+cu130, CUDA 13.0 and NumPy 2.5.3. Do not sync the
CPU lockfile into the CUDA environment. No package change is part of this study.
Inspect the worker and progress before executing a training command; never
launch another worker while its lock is held or retrain a completed fit.

```bash
league_root=/home/thivas/work/ai-portfolio/league-ews-audit
league_python="$league_root/.venv/bin/python"
league_archive="$league_root/data/private/league-three-event-export-v1/development.zip"
league_source=/home/thivas/work/ai-portfolio/league-ews-gpu
league_control="$league_source/data/private/compact-notebook-v1"
league_timely="$league_root/data/private/league-timely-neural-v1"
league_inputs="$league_root/data/private/league-timely-inputs-v1"
league_training="$league_root/data/private/league-clock-history-v1"
league_output="$league_root/data/private/league-clock-history-policy-v1"
league_report=reports/clock-history-2026-10-04

# Resume only an inactive, incomplete study after inspecting its checkpoints.
PYTHONFAULTHANDLER=1 bash scripts/run_clock_history.sh "$league_python" \
  "$league_archive" "$league_control" "$league_training" "$league_report/plan.json" \
  "$league_source" "$league_timely" "$league_inputs"

league_args=(
  --archive "$league_archive" --control "$league_control"
  --history "$league_root/data/private/league-history-ablation-v1"
  --independent "$league_root/data/private/league-task-sharing-v1"
  --pcgrad "$league_root/data/private/league-pcgrad-v1"
  --study "$league_timely" --inputs "$league_inputs" --new-study "$league_training"
  --warning "$league_root/data/private/league-warning-efficiency-v1"
  --reference "$league_root/data/private/league-timely-policy-v1"
  --dense "$league_root/data/private/league-dense-policy-v1"
  --previous "$league_root/data/private/league-timely-input-policy-v1"
  --control-plan reports/timely-neural-2026-10-03/plan.json
  --input-plan reports/timely-inputs-2026-10-04/plan.json
  --plan "$league_report/plan.json" --output "$league_output"
)
PYTHONPATH=.:src "$league_python" -u -m scripts.evaluate_clock_history \
  "${league_args[@]}" --early-only
# Record all 216 frozen early heads and zero later heads before proceeding.
PYTHONPATH=.:src "$league_python" -u -m scripts.evaluate_clock_history "${league_args[@]}"
PYTHONPATH=.:src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$league_python" \
  -u -m scripts.analyse_clock_history --study "$league_output" \
  --archive "$league_archive" --plan "$league_report/plan.json" --output "$league_report"
PYTHONPATH=.:src "$league_python" -m scripts.audit_clock_history_results \
  --training "$league_training" --policy "$league_output" --output "$league_report" \
  --analysis-commit 98346c3
PYTHONPATH=.:src "$league_python" -m scripts.render_clock_history --output "$league_report"
```

The successful one-update CUDA canary was resumed in the same output; do not
repeat it. All three fits must finish their 576 updates before scoring. Model,
optimizer, RNG, source, archive, normalizer and runtime bindings are checked on
continuation. Fault tracing is enabled because an earlier study recovered from
a native Python crash whose root cause remains unresolved; no new crash is
implied by that precaution.

The evaluator verifies all 198 old heads, their early counts/selections and
all five later-policy count arrays exactly. It adds 18 heads and jointly freezes
all 216 before later evaluation. Each new head receives an independent replay
of all 3,000 later matches at both common budget-one policies (108,000 checks).
Every head also receives fixed-sample component-threshold checks. Resume skips
verified completed artifacts; source or artifact changes stop execution. Use a
new empty output directory for a fresh replay and preserve the original one.

The paired analysis retains every event, region, fixed seed, policy and budget.
It verifies the component identity on point values and shared whole-match
bootstrap draws. Public files contain aggregates, never per-match arrays or
model binaries. Rendering losslessly formats JSON; record raw and published
hashes. Optional standalone figures use the existing isolated Matplotlib:

```bash
PYTHONPATH=/tmp/league-warning-plot-tools:.:src MPLCONFIGDIR=/tmp/league-warning-mpl \
  "$league_python" -m scripts.render_clock_history --output "$league_report" --plots
```

Before new scoring: 635 tests passed, one skipped, 85.89% coverage, Ruff clean,
and mypy passed 87 source files. Eight focused tests cover the intervention,
exact resume, nonfinite-checkpoint protection, all-fit scoring gate, policy
indexing/reference parity, paired component attribution and early/later gate
with resume/tamper protection. Software fixtures are not League findings.
Patch 16.17 stays sealed throughout.

The post-study scoring-release repair adds seven checks; the expanded suite
passes 642 tests with the same 85.89% coverage. It does not alter the frozen
training or analysis and is not used to retroactively release this study.
For future runs, follow [the enforced release procedure](scoring-release-repair.md)
and use `scripts.run_clock_history_released`; the historical wrapper above is
retained only to reproduce the actual execution, including its disclosed timing
deviation. Do not repeat completed fits.
