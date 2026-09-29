#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
mkdir -p data/private/timely-objective-v1
exec 9>data/private/timely-objective-v1/worker.lock
if ! flock -n 9; then
  echo 'A timely objective worker is already running.'
  exit 0
fi
status_file=data/private/timely-objective-v1/worker-exit-code
rm -f -- "$status_file"
trap 'worker_exit=$?; printf "%s\n" "$worker_exit" > "$status_file"' EXIT
uv run --no-sync python -m league_ews.timely_experiment --max-new-models 0 --threads 4
