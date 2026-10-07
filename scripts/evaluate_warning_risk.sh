#!/usr/bin/env bash
# Development-only policy study: commit, freeze every early head, then replay.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
python_bin=${1:?Provide the existing Python path}
data_root=${2:?Provide the repository with private League development data}
control_root=${3:?Provide the frozen original GPU checkout}
analysis_commit=${4:?Provide the committed warning-risk analysis revision}
report=reports/warning-risk-2026-10-07
output="$data_root/data/private/league-warning-risk-v1"
mkdir -p -- "$output"
exec 9>"$output/worker.lock"
flock -n 9
trap 'worker_exit=$?; printf "%s\n" "$worker_exit" > "$output/worker-exit-code"' EXIT
league_args=(
  --data-root "$data_root" --control-root "$control_root"
  --plan "$report/plan.json" --output "$output" --analysis-commit "$analysis_commit"
)
PYTHONPATH=.:src "$python_bin" -u -m scripts.evaluate_warning_risk "${league_args[@]}" --early-only
PYTHONPATH=.:src "$python_bin" -u -m scripts.evaluate_warning_risk "${league_args[@]}"
PYTHONPATH=.:src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$python_bin" \
  -u -m scripts.analyse_warning_risk --study "$output" \
  --archive "$data_root/data/private/league-three-event-export-v1/development.zip" \
  --plan "$report/plan.json" --output "$report"
PYTHONPATH=.:src "$python_bin" -m scripts.audit_warning_risk \
  --study "$output" --output "$report"
