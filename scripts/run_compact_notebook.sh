#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
archive=${1:?Provide the development.zip path}
output=${2:-data/private/compact-notebook-v1}
python_bin=${3:-.venv/bin/python}
device=${4:-cuda}
mkdir -p -- "$output"
exec 9>"$output/worker.lock"
if ! flock -n 9; then
  echo 'A compact LeagueEWS worker is already running.'
  exit 0
fi
status_file="$output/worker-exit-code"
rm -f -- "$status_file"
trap 'worker_exit=$?; printf "%s\n" "$worker_exit" > "$status_file"' EXIT
PYTHONPATH=.:src "$python_bin" -u -m scripts.run_compact_notebook \
  --archive "$archive" --output "$output" --device "$device" --max-new-shards 0
