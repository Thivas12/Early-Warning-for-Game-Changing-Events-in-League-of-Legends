#!/usr/bin/env bash
# Run in the foreground under nohup when a persistent worker is wanted.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
python_bin=${1:?Provide the existing CUDA Python path}
archive=${2:?Provide the development ZIP path}
control=${3:?Provide the completed original study directory}
output=${4:?Provide a separate ablation output directory}
plan=${5:?Provide the frozen follow-up plan}
mkdir -p -- "$output"
exec 9>"$output/worker.lock"
if ! flock -n 9; then
  echo 'The history ablation worker is already running.'
  exit 0
fi
trap 'worker_exit=$?; printf "%s\n" "$worker_exit" > "$output/worker-exit-code"' EXIT
PYTHONPATH=.:src "$python_bin" -u -m scripts.run_history_ablation \
  --archive "$archive" --control "$control" --output "$output" \
  --plan "$plan" --device cuda --max-new-shards 0
