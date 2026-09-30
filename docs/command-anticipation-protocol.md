# Command-stream anticipation: third public-data experiment

Declared after the two negative precontact experiments, before fitting command
models or acquiring the new evaluation cohort. This is a new exploratory screen,
not a retroactive claim of preregistration or a sequential significance guarantee.

Hypothesis: recorded movement destinations provide information about a coming
Roshan damage onset beyond the positions, motion, and command frequency already
observed. Orders are observable replay messages, not verified psychological
intentions, successful actions, or player-visible information. The canonical
export omits selected unit IDs and stores message `entindex` in the misleadingly
named `issuer_player_id` column. Treat that column only as an anonymous issuing
entity key; do not join it to hero slots or infer teams. Orders can control
couriers, illusions, and other units as well as heroes.

## Source validation

Use the same pinned canonical and metadata revisions as the precontact pilot.
Inspect schema match 7581685965 and training replay 7616388415 only during feature
development. Independently decode the latter's archived replay with pinned Gem
e276f3ea5e77b5b8652a68ef7687b5c494592853. Require equality of every exported raw
order field and tick. Audit the fixed +16384 XY conversion from command vectors
to the cell-coordinate convention of the snapshots using selected-unit positions;
this diagnostic may use subsequent positions but is never a forecasting input.
Retain raw missingness and disclose that the derivative omits selected units.

## Cohorts and fixed task

Reuse the original 110 accepted training matches and 37 accepted calibration
matches. These are development data, and calibration has been consulted before.
Never train on either previously evaluated cohort. Select exactly 250 new matches
with the lowest SHA256(`command-anticipation-v1:match_id`), after excluding all
500 matches in the first two manifests and the first ten schema-development
matches. Require start_time >=1760390736, then sort chronologically. Freeze the
manifest before download. No replacements or optional expansion after results.

Apply the unchanged strict precontact snapshot, clock, identity, and damage/HP
quality checks to fresh records. Additionally require nonempty, finite, ordered
integer command ticks, embedded match identity, command clock agreement within
0.2 seconds, finite XY on move-to-position (1) and attack-move (3) orders, and at
least one live-game command. Do not exclude no-onset matches or use event counts
to select matches. An additional command-QC failure removes a match from every
paired model. Require at least 20 retained fresh matches to score the screen.

Keep first decision at minute 5, 5-second decisions, 20–60-second eligible lead,
10-second quiet-gap onsets, 60-second cooldown, all unmatched alarms counted,
and the original calibration-only threshold search with <=1 unmatched/match.
Keep HistGradientBoostingClassifier parameters unchanged (120 iterations,
15 leaves, minimum leaf 30, L2=1, learning rate .08, no early stopping). Use seed
17 only: the previous three seeds produced identical fitted policies and were
not independent repetitions.

## Frozen models and inputs

Refit clock (5), current (77), history (197), and coordination (225) controls.
Add the following three fixed current-state augmentations:

1. **command_rate**: per trailing 5, 15, and 30 seconds, counts of all orders,
   move-to-position/attack-move, attack-target, cast (5–9), stop/hold (21 and 10),
   queue orders, distinct issuing entities, and maximum orders from one issuer.
2. **command_destination** (primary): command_rate plus the spatial summaries
   below, with the fixed +16384 XY conversion.
3. **rotated_destination** (negative control): the same spatial summaries after
   negating both raw command coordinates before the conversion. Preserve time,
   issuing entity, order counts and model capacity; this is a deliberately
   incorrect map-location control, not a causal permutation test.

For each of the same trailing windows, use only order types 1 and 3. Compare
destinations with Roshan's position available at the current decision. Include
destination-distance minimum, median, maximum; counts and distinct issuers within
500, 1500, 3000 units; then each issuer's most recent eligible destination:
distance minimum, median, maximum and counts within those same radii. Counts are
zero when no spatial orders exist, distance summaries missing. An order in the
left-open/right-closed window (t-window,t] is eligible; never use later messages.
These are histories of destinations, not assertions that an order remains active.

No final statistics, postgame result, hero gold, inferred future paths, subsequent
damage, attack-target entity identity, or target location at the future onset.

Choose one comparator on calibration only among clock/current/history/
coordination/command_rate: most onset hits, then fewer unmatched, fewer alarms,
then model name. Freeze all models, thresholds and comparator before evaluation.
Publish all seven models and unchanged-threshold 5-second delivery-delay scores.

The primary candidate advances only if its new-cohort unmatched rate is <=1,
and its paired recall gain versus BOTH the selected comparator and
rotated_destination has a strictly positive lower 95% percentile interval under
both match and calendar-day bootstrap (2000 draws, fixed seed 7391). These are
screening thresholds, not multiplicity-corrected proof of discovery. Report
league composition and the strongest fresh-test baseline even when it differs
from the calibration-selected comparator. Do not call a passing feature screen
a breakthrough: an independent replication and stronger external baselines
would still be required.

Camera-based fight prediction and trajectory-based strategy interpretation are
prior art: Tot et al., CoG 2021, `paper_101.pdf`; T-Foresight, 2025,
https://www.sciencedirect.com/science/article/pii/S2468502X25000440 (abstract only
accessible in this session). Yang et al., IEEE Transactions on Games,
arXiv:2012.09424, already predict multiple MOBA events with rich state features.
Using a new input stream by itself does not establish methodological novelty.

Pre-fit correction: direct inspection of the pinned protobuf enum showed that
STOP is 21 and HOLD_POSITION is 10; 11 means TRAIN_ABILITY. The initial numeric
parenthesis was corrected before any feature production or fitting. The intended
stop/hold category is unchanged; no fresh outcomes informed this correction.

Pre-fit secondary audit: also score the unchanged frozen alarms against the first
positive damage to Roshan in each life (reset only after a recorded Roshan death),
with the same minute-5 warmup and 20–60-second lead window. This separates first
engagement from quiet-gap re-engagement. It does not change the primary target,
training labels, thresholds, comparator or advancement gate. Report every model
and count all alarms unmatched to this stricter target, without recalibration.
