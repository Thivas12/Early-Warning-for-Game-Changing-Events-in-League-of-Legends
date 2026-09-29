#!/usr/bin/env bash
# Complete the two remaining registered calibration controls in frozen order.
# Each seed checkpoints after every shard. Rerunning this file resumes it.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

for variant in independent-horizon-heads fixed-minute-grid; do
  for seed in {20260915..20260924}; do
    printf '\nTraining %s / %s\n' "$variant" "$seed"
    make train-m1-graph-ablation-seed \
      VARIANT="$variant" SEED="$seed" DEVICE=cuda MAX_NEW_SHARDS=720
  done

  for seed in {20260915..20260924}; do
    printf '\nScoring %s / %s on calibration\n' "$variant" "$seed"
    make score-m1-graph-ablation-seed VARIANT="$variant" SEED="$seed"
  done

  printf '\nSummarizing %s\n' "$variant"
  make summarize-m1-graph-ablation VARIANT="$variant"
done

printf '\nAuditing all six registered calibration controls\n'
make audit-m1-calibration \
  AUDIT_OUTPUT=reports/local/m1-calibration-diagnostic-complete.json
