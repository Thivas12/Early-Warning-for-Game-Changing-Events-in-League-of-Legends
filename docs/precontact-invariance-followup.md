# Invariance follow-up: declared after the initial negative result

The initial 26-match evaluation contained 23 onsets. Clock/objective history
caught four; individual history caught zero; the full coordination feature set
caught one. The candidate did not pass its advancement gate. These results stay
in the record. The next experiment is development informed by that failure,
not a retroactively preregistered analysis of the same holdout.

Hypothesis: absolute coordinates and arbitrary within-team player ordering make
the small tree model too sensitive to incidental representation. This explanation
is unproven. Test it by removing those inputs, using established invariance
principles rather than claiming a new architecture.

Keep the original 110 training matches, 37 calibration matches, model capacity,
seeds, lead window, cooldown and calibration algorithm. Add two representations:

1. Invariant current state: clock/objective history, unordered team geometry
   relative to current Roshan position, and team summaries of health, mana, level
   and alive state. No absolute map coordinates or hero/player identities.
2. Invariant motion: the same summaries plus past-ten-second velocity alignment,
   speed and approach-to-objective measures already present in the first feature
   archive. No new future-derived information or label changes.

Make team ordering invariant too: order the two team summaries by mean distance
to the objective, with a deterministic summary-based lexicographic tie-breaker.
Use all player slots when calculating geometry (including dead heroes), with
alive counts and health summaries explicit. This is a restricted feature ablation;
it does not establish that team coordination causes an event.

Before viewing any new outcome, select exactly 200 disjoint matches from the same
late period as the initial evaluation, using the lowest SHA256 of
`precontact-replication-v1:match_id`. Apply unchanged source quality rules. Do not
substitute newly available matches for exclusions. Require at least 20 retained
evaluation matches. None of the original evaluation matches enter training or
calibration. Frozen original models must reproduce their calibration thresholds
and counts exactly on refit.

Choose the comparator using calibration only: highest onset hits among the five
original models (the kill-trained model is re-scored on onset for this choice)
and invariant-current, breaking ties by fewer unmatched alarms, fewer alarms,
then model name. Compare invariant-motion with that fixed comparator on the new
cohort. Publish every model, even if another one looks better on evaluation.

Advancement requires at most one unmatched alert per new match, and a strictly
positive lower 95% paired recall-difference interval using both match and
calendar-day bootstrap, for every seed. This remains a screening gate, not a
sequential-testing guarantee or proof of novelty. Do not replace the first
negative result with a favorable second result or pool them as a preplanned test.
No optional expansion after viewing this second result.

The source metadata labels all selected matches PROFESSIONAL, but 176 of the
first 300 belong to Destiny League. This is not evidence of elite-tournament,
independent-team, player-visible, or League of Legends generalization.

## Reproduction

After completing the first-wave commands in `precontact-pilot-protocol.md`:

```bash
python -m research.acquire_precontact_replication \
  --metadata data/external/betty/matches.parquet \
  --original-manifest reports/precontact-cohort-2026-09-30.json \
  --manifest reports/precontact-replication-cohort-2026-09-30.json \
  --output-dir data/external/betty-replication
python -m research.precontact_data \
  --root data/external/betty-replication \
  --manifest reports/precontact-replication-cohort-2026-09-30.json \
  --output-dir data/processed/precontact \
  --report reports/precontact-replication-quality-2026-09-30.json
python -m research.run_precontact_invariance \
  --original-quality reports/precontact-quality-2026-09-30.json \
  --fresh-quality reports/precontact-replication-quality-2026-09-30.json \
  --original-results reports/precontact-pilot-2026-09-30.json \
  --data-dir data/processed/precontact \
  --output reports/precontact-invariance-2026-09-30.json
python -m research.audit_precontact_completion_credit
python -m research.summarize_precontact
```

The fixed delivery-delay sensitivity conservatively counts queued alarms arriving
after game end as unmatched. It does not claim a measured deployment latency.
The completion-credit audit is a post-hoc descriptive mechanism check added after
both model comparisons, with no new model fitting or threshold selection.
