# Pre-contact forecasting pilot: protocol frozen before model fitting

This is an exploratory Dota study, not League validation or an established novel method.
The purpose is to test whether measurable pre-contact movement predicts objective damage
onset at a useful alert budget, before investing in a new architecture.

## Cohort

Pin Betty canonical v1 to `29aca0551be317948d0a181e9630c9a583fadc32`.
Select 300 matches by the lowest SHA256 of `precontact-v1:match_id` from the
9,385-row public metadata table. Exclude the first ten matches used for schema
development. Freeze chronological 60/20/20 train/calibration/evaluation membership
before quality exclusions or reading prediction results. Preserve unsuccessful downloads
and exclusions. These matches are a convenience sample; repeated players and teams remain.

## Data validation and limits

The older export's `game_time` is raw elapsed tick time. The canonical combat
table also has that problem. Canonical snapshot clocks subtract completed pauses,
but can advance during a pause and jump backward afterward. **For this pilot,
exclude every match whose snapshot clock is not a constant 30-Hz mapping**,
rather than silently reconstructing unverified pause boundaries. Match labels and
snapshots join on replay ticks. Enforce full ten-hero snapshots, consistent hero
identities, combat game-start/end states, and terminal Roshan damage/death consistency.
Require first target damage to agree with an observed Roshan HP reduction within
two snapshot seconds. Conversely, every HP reduction must have nearby positive
combat damage; absent combat records alone cannot certify no event. Keep
non-terminal contact episodes and no-event matches. The reverse HP check was
added during training-partition adapter development, before fitting any model.

The canonical `team_side` is inconsistent with combat team identifiers in the
schema-development match. Do not use it. Derive fixed hero teams from pre-horn
combat records only, require five per team, and reject contradictory or incomplete
mappings. Do not use exported resource gold/net worth, whose hero attribution is
not independently verified. Restrict hero inputs to entity-local position, health,
mana, level, alive state. Roshan position/HP and combat events are observer data.
No player-visible, live-deployment, intent, or causal-intervention claim is allowed.

## Forecasting and comparators

Primary target: first positive Roshan damage after an observed death or a damage
gap strictly greater than 10 seconds, including episodes without a kill.
The first decision is at game minute five (30-second feature history is then available).
Eligible targets occur at least 20 seconds after the first decision. Predictions
use only observations at or before their decision tick. Decision interval 5 seconds;
alert cooldown 60 seconds. Credit requires a 20–60 second lead with one-to-one
matching. Every unmatched alert counts, including duplicates and late alerts.
Primary delivery is immediate on the observer clock. Also apply a fixed five-second
delivery delay to the already-selected alarms without recalibration; this is a
sensitivity test, not a measured end-to-end deployment latency.

Fit fixed-capacity histogram gradient boosting baselines: clock/contact history
with current objective health and alive status;
individual current hero state; individual state with 10/30-second histories;
the same histories plus explicit within-team geometry and motion. Also train the
last feature set on kill-completion labels, and score its unchanged alarms against
both targets. Include a reactive first-damage detector and a silent policy.
Use the same model capacity and seeds 17, 29, 43; do not select a lucky seed.

Thresholds are selected on calibration only, maximizing onset recall with at most
one unmatched alert per match, ties favor fewer alerts. Use a fixed 101-point
score-quantile grid augmented with 101 fixed upper-tail levels
`1 - logspace(-4, 0, 101)`, plus silence. The upper-tail refinement was fixed
before model fitting because events are sparse. Completion-trained policy calibrates to
completion targets, to expose target mismatch. Evaluation is untouched until
all choices and predictions are frozen. Bootstrap paired matches for uncertainty;
also summarize calendar-day blocks because matches may share teams.

## Advancement criteria

Advance coordination as a candidate only if its evaluation alert budget is met
and the lower 95% interval for paired recall improvement over individual-history
is positive, consistently across seeds. A positive pilot warrants replication
on fresh matches, team/tournament holdouts, stronger temporal models, visibility
constraints and annotation checks. It is not a breakthrough declaration.
If cohort validation fails, repair measurement against authoritative replay facts
before training. Do not lower the quality gates to obtain a favorable result.

## Reproduction

Use Python 3.12 and `research/precontact-requirements.txt`. Run from the repository root.
The source metadata is `matches.parquet` from `wolframko/betty-dota2` revision
`b20e01577af2f4f5dffcdc4f1d5bad5c3807abca`, SHA256
`4f5c2152ba188ced430e5680775d57107bf77e2a51d2b099f816bf34faffe4bb`.
It is used only for match selection, dates, duration verification and split membership;
final player statistics and match outcome are never model inputs.

```bash
python -m research.acquire_precontact \
  --metadata data/external/betty/matches.parquet \
  --output-dir data/external/betty-canonical \
  --manifest reports/precontact-cohort-2026-09-30.json
python -m research.precontact_data \
  --root data/external/betty-canonical \
  --manifest reports/precontact-cohort-2026-09-30.json \
  --output-dir data/processed/precontact \
  --report reports/precontact-quality-2026-09-30.json
python -m research.run_precontact_pilot \
  --quality-report reports/precontact-quality-2026-09-30.json \
  --data-dir data/processed/precontact \
  --output reports/precontact-pilot-2026-09-30.json
```

`verify_precontact_replay.py` additionally requires the pinned Gem source checkout
and its parser dependencies (`python-snappy`, `zstandard`, `protobuf`) on `PYTHONPATH`.
The independent-parser report records the exact source replay and hashes. It tests
agreement on one training match, not the reliability of every field or match.

## Prior work and source boundaries

- [Yang et al., Predicting Events in MOBA Games](https://arxiv.org/abs/2012.09424):
  event prediction and temporal models already exist.
- [Tot et al., team-fight prediction from cameras](https://ieee-cog.org/2021/assets/papers/paper_101.pdf):
  team behavior and camera-derived intent proxies are established directions.
- [RiskProp](https://arxiv.org/abs/2603.27165): collision-anchored anticipation
  and backward risk supervision prevent claiming that completion-supervised
  anticipation itself is new.
- [Betty metadata and older derived tables](https://huggingface.co/datasets/wolframko/betty-dota2),
  [canonical export](https://huggingface.co/datasets/wolframko/betty-dota2-canonical-v1),
  [raw archive](https://huggingface.co/datasets/wolframko/betty-dota2-raw-v2).
  The source card's 2025 description does not match the full metadata date range,
  which begins in 2024. Canonical export has no dataset card at the pinned revision.

The implemented tree model and hand-built geometry are baselines, not an invented
algorithm. Any defensible contribution must come from a replicated finding about
anticipation, evaluation or information constraints, with closer comparisons than
this initial screen can supply. Raw public datasets are not committed to this repository.
