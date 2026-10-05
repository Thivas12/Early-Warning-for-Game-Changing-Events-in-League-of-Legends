# Reproduce the useful-lead task-sharing control

Branch `research/league-timely-sharing-20261005` starts from completed conditional
history study `cf610ba` (draft PR #82). Training and protocol commit: `7b9bc1b`.
Evaluation and paired analysis commit: `570b10c`. The [analysis gate](analysis-gate.json)
records zero predictions before that commit. The new runner enforces a separate,
hash-bound committed-analysis release before scoring. This corrects the previous
study's disclosed commit-timing deviation without altering its historical results.
All studies remain exploratory on previously inspected development matches.

Use the existing RTX 4060 Laptop GPU (8 GB), driver 610.74, Python 3.12.14,
PyTorch 2.14.0+cu130, CUDA 13.0 and NumPy 2.5.3. No dependency changes are required.
Never synchronize the CPU lockfile into the GPU environment. First inspect running
workers, the output lock and progress; resume only an inactive study. Preserve
all completed checkpoints and every frozen source file.

```bash
league_root=/home/thivas/work/ai-portfolio/league-ews-audit
league_python="$league_root/.venv/bin/python"
league_archive="$league_root/data/private/league-three-event-export-v1/development.zip"
league_source=/home/thivas/work/ai-portfolio/league-ews-gpu
league_control="$league_source/data/private/compact-notebook-v1"
league_timely="$league_root/data/private/league-timely-neural-v1"
league_independent="$league_root/data/private/league-task-sharing-v1"
league_training="$league_root/data/private/league-timely-sharing-v1"
league_output="$league_root/data/private/league-timely-sharing-policy-v1"
league_report=reports/timely-sharing-2026-10-05

# Resume the existing study only after verifying that its worker is inactive.
PYTHONFAULTHANDLER=1 bash scripts/run_timely_sharing.sh "$league_python" \
  "$league_archive" "$league_control" "$league_training" "$league_report/plan.json" \
  "$league_source" "$league_timely" "$league_independent"
```

The successful one-update CUDA canary is part of this study, not an extra fit.
The worker resumes it and completes exactly nine fits, each with 576 shard
updates. Training, optimizer, RNG, normalizer, data, runtime and source bindings
must match. Nonfinite updates do not overwrite the last valid checkpoint.
Fault tracing is enabled; no new failure is implied by this precaution.

After all nine fits, a missing release returns
`awaiting-committed-analysis-release` with zero new scores. Issue the release
only when the worker has exited, the analysis sources are tested and committed,
and all nine checkpoints are complete. The exclusive lock rejects an active
worker. The helper refuses any study that has already begun scoring and never
silently replaces a release. This example also records the pre-scoring gate:

```bash
PYTHONPATH=.:src "$league_python" - <<'PY'
import datetime
import fcntl
import json
from pathlib import Path
from scripts.scoring_release import digest, issue

repo = Path.cwd()
study = Path('/home/thivas/work/ai-portfolio/league-ews-audit/data/private/league-timely-sharing-v1')
plan = repo / 'reports/timely-sharing-2026-10-05/plan.json'
with (study / 'experiment.lock').open('a+b') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    progress = [json.loads(p.read_bytes()) for p in study.glob('*/seed-*/progress.json')]
    assert len(progress) == 9 and all(p['completed_units'] == 576 for p in progress)
    release = issue(repo, study, plan, '570b10c', json.loads(plan.read_bytes())['analysis_sources'])
    gate = {
        'recorded_at_utc': datetime.datetime.now(datetime.UTC).isoformat(),
        'fits_complete': 9, 'training_shard_updates': 5184,
        'new_prediction_reports': 0, 'new_later_policy_evaluations': 0,
        'analysis_release_sha256': digest(study / 'analysis-release.json'),
        'release': release, 'test_payloads_opened': 0,
    }
    with (plan.parent / 'scoring-release-gate.json').open('x') as stream:
        json.dump(gate, stream, indent=2)
        stream.write('\n')
PY

# Resume the same command above after release. Completed fits are not retrained.
```

Do not reissue a release or rerun a completed study merely to reproduce the
record. The scoring worker verifies the release before reading calibration for
prediction. It saves only each event's trained four columns, with original and
fitted target definitions. Its summary contains no warning-policy evaluation.

```bash
league_args=(
  --archive "$league_archive" --control "$league_control"
  --history "$league_root/data/private/league-history-ablation-v1"
  --independent "$league_independent" --pcgrad "$league_root/data/private/league-pcgrad-v1"
  --study "$league_timely" --inputs "$league_root/data/private/league-timely-inputs-v1"
  --warning "$league_root/data/private/league-warning-efficiency-v1"
  --reference "$league_root/data/private/league-timely-policy-v1"
  --dense "$league_root/data/private/league-dense-policy-v1"
  --previous "$league_root/data/private/league-timely-input-policy-v1"
  --new-study "$league_root/data/private/league-clock-history-v1"
  --latest "$league_root/data/private/league-clock-history-policy-v1"
  --independent-study "$league_training"
  --control-plan reports/timely-neural-2026-10-03/plan.json
  --input-plan reports/timely-inputs-2026-10-04/plan.json
  --clock-plan reports/clock-history-2026-10-04/plan.json
  --plan "$league_report/plan.json" --output "$league_output"
)
PYTHONPATH=.:src "$league_python" -u -m scripts.evaluate_timely_sharing \
  "${league_args[@]}" --early-only
# Record all 234 frozen early heads and zero later heads before proceeding.
PYTHONPATH=.:src "$league_python" -u -m scripts.evaluate_timely_sharing "${league_args[@]}"
PYTHONPATH=.:src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$league_python" \
  -u -m scripts.analyse_timely_sharing --study "$league_output" \
  --archive "$league_archive" --plan "$league_report/plan.json" --output "$league_report"
PYTHONPATH=.:src "$league_python" -m scripts.audit_timely_sharing_results \
  --training "$league_training" --policy "$league_output" --output "$league_report" \
  --analysis-commit 570b10c
PYTHONPATH=.:src "$league_python" -m scripts.render_timely_sharing --output "$league_report"
```

The evaluator must reproduce all 216 previous heads across all five policies.
It adds 18 heads, freezing all 234 early selections before later replay.
Independent replay covers both common budget-one policies on all 3,000 later
matches for every new head: 108,000 checks. Fixed-sample component-threshold
checks additionally cover every head. The aggregate audit checks exact prior
estimates and release ordering; its local timestamps are not an external registry.

All contrasts share 2,000 paired whole-match bootstrap draws, stratified by
region. Report individual events, regions, fixed seeds, every policy and budget,
and both warning components. The sharing-by-target identity must hold for both
point estimates and bootstrap draws. No best-head selection is performed.

Rendering losslessly formats aggregate JSON. Retain the raw hashes in
`execution-record.json` and separately record the published hashes. Optional
standalone figures use the existing isolated Matplotlib installation:

```bash
PYTHONPATH=/tmp/league-warning-plot-tools:.:src MPLCONFIGDIR=/tmp/league-warning-mpl \
  "$league_python" -m scripts.render_timely_sharing --output "$league_report" --plots
```

Before release: 653 tests passed, one skipped, 85.89% coverage; Ruff passed and
mypy checked 87 source files. Eleven focused tests cover exact checkpoint resume,
target and event-column alignment, nonfinite preservation, all-fit/release gates,
previous-policy parity, early/later gates with tamper detection and the paired
interaction identity. These software checks are not empirical League evidence.
Publish only aggregate reports and code; exclude private arrays and model binaries.
Patch 16.17 stays sealed.
