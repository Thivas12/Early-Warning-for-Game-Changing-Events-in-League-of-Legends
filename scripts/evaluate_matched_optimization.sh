#!/usr/bin/env bash
# Reproducible development-only evaluation; stop on any failed gate.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
python_bin=${1:?Provide the existing Python path}
data_root=${2:?Provide the audit repository with private development data}
control_root=${3:?Provide the frozen original GPU checkout}
report=reports/matched-optimization-2026-10-06
analysis_commit=${4:?Provide the committed matched analysis revision}
training="$data_root/data/private/league-matched-optimization-v1"
output="$data_root/data/private/league-matched-optimization-policy-v1"
archive="$data_root/data/private/league-three-event-export-v1/development.zip"
mkdir -p -- "$output"
exec 9>"$output/worker.lock"
flock -n 9
trap 'worker_exit=$?; printf "%s\n" "$worker_exit" > "$output/worker-exit-code"' EXIT
league_args=(
  --archive "$archive" --control "$control_root/data/private/compact-notebook-v1"
  --history "$data_root/data/private/league-history-ablation-v1"
  --independent "$data_root/data/private/league-task-sharing-v1"
  --pcgrad "$data_root/data/private/league-pcgrad-v1"
  --study "$data_root/data/private/league-timely-neural-v1"
  --inputs "$data_root/data/private/league-timely-inputs-v1"
  --warning "$data_root/data/private/league-warning-efficiency-v1"
  --reference "$data_root/data/private/league-timely-policy-v1"
  --dense "$data_root/data/private/league-dense-policy-v1"
  --previous "$data_root/data/private/league-timely-input-policy-v1"
  --new-study "$data_root/data/private/league-clock-history-v1"
  --latest "$data_root/data/private/league-clock-history-policy-v1"
  --independent-study "$data_root/data/private/league-timely-sharing-v1"
  --sharing-policy "$data_root/data/private/league-timely-sharing-policy-v1"
  --optimization-study "$data_root/data/private/league-timely-optimization-v1"
  --optimization-policy "$data_root/data/private/league-timely-optimization-policy-v1"
  --matched-study "$training"
  --control-plan reports/timely-neural-2026-10-03/plan.json
  --input-plan reports/timely-inputs-2026-10-04/plan.json
  --clock-plan reports/clock-history-2026-10-04/plan.json
  --sharing-plan reports/timely-sharing-2026-10-05/plan.json
  --optimization-plan reports/timely-optimization-2026-10-05/plan.json
  --plan "$report/plan.json" --output "$output"
)
PYTHONPATH=.:src "$python_bin" -u -m scripts.evaluate_matched_optimization \
  "${league_args[@]}" --early-only
PYTHONPATH=.:src "$python_bin" - "$training" "$output" "$report" <<'PY'
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from scripts.scoring_release import digest

training, output, report = map(Path, sys.argv[1:])
frozen = json.loads((output / 'policy-freeze.json').read_bytes())
assert len(frozen['policies_sha256']) == 342
assert all(digest(output / 'early' / f'{k}.json') == v
           for k, v in frozen['policies_sha256'].items())
release = json.loads((report / 'scoring-release-gate.json').read_bytes())
checkpoints = {}
for name, expected in release['checkpoint_sha256'].items():
    variant, seed = name.split('/')
    actual = digest(training / variant / f'seed-{seed}' / 'checkpoint.pt')
    assert actual == expected
    checkpoints[name] = actual
path = report / 'evaluation-gate.json'
binding = digest(output / 'policy-freeze.json')
if path.exists():
    previous = json.loads(path.read_bytes())
    assert previous['policy_freeze_sha256'] == binding
    assert previous['checkpoint_sha256_after_scoring'] == checkpoints
else:
    assert not list((output / 'later').glob('*.npz'))
    gate = {
        'recorded_at_utc': datetime.now(UTC).isoformat(),
        'all_early_heads': 342, 'new_later_heads': 0,
        'policy_freeze_sha256': binding, 'test_payloads_opened': 0,
        'checkpoint_sha256_after_scoring': checkpoints,
    }
    with path.open('x') as stream:
        json.dump(gate, stream, indent=2)
        stream.write('\n')
print(json.dumps({'early_heads': 342, 'policy_freeze_sha256': binding}))
PY
PYTHONPATH=.:src "$python_bin" -u -m scripts.evaluate_matched_optimization "${league_args[@]}"
PYTHONPATH=.:src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$python_bin" \
  -u -m scripts.analyse_matched_optimization --study "$output" \
  --archive "$archive" --plan "$report/plan.json" --output "$report"
PYTHONPATH=.:src "$python_bin" -m scripts.audit_matched_optimization_results \
  --training "$training" --policy "$output" --output "$report" --analysis-commit "$analysis_commit"
