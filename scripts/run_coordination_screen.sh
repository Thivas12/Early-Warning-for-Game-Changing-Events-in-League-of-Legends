#!/usr/bin/env bash
# Detached execution is initiated by Make; this worker owns its lifetime lock.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
mkdir -p data/private/coordination-screen-v1
exec 9>data/private/coordination-screen-v1/worker.lock
if ! flock -n 9; then
  echo 'A coordination screen worker is already running.'
  exit 0
fi
status_file=data/private/coordination-screen-v1/worker-exit-code
rm -f -- "$status_file"
trap 'worker_exit=$?; printf "%s\n" "$worker_exit" > "$status_file"' EXIT
uv run --no-sync python -m league_ews.coordination_experiment --max-new-models 0 --threads 4
