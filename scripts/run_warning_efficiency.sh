#!/usr/bin/env bash
set -euo pipefail
if (( $# < 8 )); then
  echo 'usage: run_warning_efficiency.sh PYTHON ARCHIVE CONTROL HISTORY INDEPENDENT PCGRAD OUTPUT PLAN [--early-only]' >&2
  exit 2
fi
python_bin=$1
archive=$2
control=$3
history=$4
independent=$5
pcgrad=$6
output=$7
plan=$8
shift 8
export PYTHONPATH=.:src
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
exec "$python_bin" -u -m scripts.run_warning_efficiency \
  --archive "$archive" --control "$control" --history "$history" \
  --independent "$independent" --pcgrad "$pcgrad" --output "$output" --plan "$plan" "$@"
