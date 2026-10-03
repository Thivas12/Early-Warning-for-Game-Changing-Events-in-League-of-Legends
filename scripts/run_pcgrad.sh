#!/usr/bin/env bash
# Run in a monitored foreground session; resume only with the same frozen files.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
python_bin=${1:?Provide the existing CUDA Python path}
archive=${2:?Provide the development ZIP path}
control=${3:?Provide the completed original study directory}
output=${4:?Provide a separate ablation output directory}
control_source=${6:?Provide the frozen control source checkout}
independent=${7:?Provide the completed independent control directory}
plan=${5:?Provide the frozen follow-up plan}
mkdir -p -- "$output"
exec 9>"$output/worker.lock"
if ! flock -n 9; then
  echo 'The PCGrad worker is already running.'
  exit 0
fi
trap 'worker_exit=$?; printf "%s\n" "$worker_exit" > "$output/worker-exit-code"' EXIT
PYTHONPATH=.:src "$python_bin" -u -m scripts.run_pcgrad \
  --archive "$archive" --control "$control" --output "$output" \
  --control-source "$control_source" --independent "$independent" --plan "$plan" --device cuda --max-new-shards 0
