#!/usr/bin/env bash
# One monitored CUDA worker; all fits finish before the explicit scoring release.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
python_bin=${1:?Provide the existing CUDA Python path}
archive=${2:?Provide the development ZIP path}
control=${3:?Provide the useful-lead control study}
output=${4:?Provide the separate optimizer study output}
plan=${5:?Provide the frozen study plan}
optimization=${6:?Provide the completed loss-weighting study}
mkdir -p -- "$output"
exec 9>"$output/worker.lock"
if ! flock -n 9; then
  echo 'The matched architecture worker is already running.'
  exit 0
fi
trap 'worker_exit=$?; printf "%s\n" "$worker_exit" > "$output/worker-exit-code"' EXIT
PYTHONPATH=.:src "$python_bin" -u -m scripts.run_matched_optimization \
  --archive "$archive" --control "$control" --output "$output" \
  --plan "$plan" --optimization "$optimization" --device cuda --max-new-shards 0
