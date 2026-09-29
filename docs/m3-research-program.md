# Research program: observation opportunity and recurrent event warnings

**Status:** post-M1 exploratory design, 2026-09-29. This document is an
experiment proposal, not a result or a modification of the frozen M1/M2
training. The original patch 16.17 test remains sealed for its registered
analysis. M3 needs a new untouched, later-patch cohort and a separate freeze.

## The paper question

Can a model built from *actual, partially observed* League Match-V5 frames
warn of a Dragon onset in the next 60 seconds at a fixed, low false-alert
burden, when it is evaluated on a later patch? The contribution would be an
audited observation/opportunity protocol, a censor-aware recurrent-event
forecaster, and a paired warning-utility evaluation. A graph alone, a high
observation-level AP, or an ablation gain cannot establish that claim.

Prior MOBA work already predicts events from much denser Honor of Kings data.
We should compare explicitly against it, while explaining that Riot's
approximately minute-spaced Match-V5 frames make this a different observation
regime. Irregular/partially observed temporal graphs, dynamic survival, and
early-event alarm methods are also established prior art. We can claim only a
specific measured advance under this protocol, not invention of those ideas.

## What is measurable now

`make audit-confirmed-followup` scans the 24,000 training and 6,000
calibration processed matches and the existing checksum-bound M1 target
shards, plus durations in the frozen final selected pool. It checks the
selection manifest and pool checksum, frozen split, processed file hashes,
exact future event times, hazard targets and row offsets. It never reads
patch 16.17 match payloads. The small
identifier-free JSON counts how many negative 10/20/30/60-second labels lack
*confirmed* follow-up through their horizon, by partition and route/patch.
It also counts at-risk 10-second bins before and after masking and measures
disagreement between final-frame time and `info.gameDuration`. The exposure
cutoff is the **earlier** of the final frame and the screened match duration.
It can conservatively mask some negatives when the last frame precedes the
real end. The duration is recorded at integer-second resolution, so a source
event in a partial bin remains positive even if its millisecond timestamp is
just beyond the rounded duration. Treat large disagreements as a provenance
investigation before any training. The archived 29 GB raw folder need not be
restored; selected-pool durations were frozen during outcome-blind screening.
`make render-confirmed-followup` turns the aggregate JSON into a compact SVG
of horizon-specific uncertainty and loss exposure. It requires the optional
`research` plotting dependencies and does not open source timelines.

`confirmed_followup_masks` implements the proposed training/evaluation
contract: for a negative bin, the entire bin must lie before the last
recorded frame **and** screened duration; an actually observed positive remains known even if the
rest of its bin is incomplete. Per-event risk ends at its first onset. The
future frame boundary is target/loss metadata and **cannot** enter a model
feature. The `censored_hazard_bce` primitive implements an unweighted proper
Bernoulli log score on those exposed bins. Neither function changes M1/M2.
The audit must run before fitting M3 and can falsify this mechanism: if the
discarded fraction is negligible or the B3-vs-M1 difference persists on
fully followed predictions, censoring is not a plausible explanation.

## Model and controls to freeze after the audit

1. **Baselines:** B0 event prevalence; B2 event/clock history; B3 tabular;
   unchanged M1; M2 graph-only, spatial-only, equal fusion and learned gate;
   a tabular **objective-clock and measured-position** baseline with explicit
   source availability and comparable data/compute. Reproduce thresholds with
   disjoint tuning and evaluation matches. Report every negative result.
2. **One-factored observations:** keep graph size/pooling fixed while masking
   coordinates, position-observed bit, proximity relations and objective
   anchor content one at a time. Stratify by coverage and phase. The original
   no-positions-or-proximity and no-objective-nodes ablations are confounded
   controls, not mechanistic proof.
3. **M3 candidate:** an event-specific recurrent hazard with an explicitly
   measured frame-age/missingness stream and a learned *bounded* fusion with
   participant graph context. The hazard gives monotone risks at 10/20/30/60
   seconds for each event; types can coincide. Train from exact onset delays
   using the confirmed exposure mask. A no-censoring version and a simpler
   clock/position model receive identical train matches, seed schedule,
   capacity budget and threshold search. A small time-decay or GRU-D-style
   state is an architectural comparator, not automatic novelty. The first
   candidate uses unweighted log loss so risk remains interpretable; bounded
   focal and clipped positive-weight losses are *separate* imbalance
   controls, with calibration and alert costs checked at original prevalence.
4. **Alarm policy:** choose a threshold and 60-second cooldown on earlier
   calibration matches, evaluate on later calibration matches, and freeze it
   before any new cohort. Count one-to-one event matches, all onsets and
   onsets with a prior real frame inside 60 seconds. Report false alerts per
   match with p50/p90/p95, precision, recall, event F1, and lead p10/median.
   A budget such as at most **one false Dragon alert per match** is a proposed
   primary operating point; set the exact budget in the new preregistration
   using application costs and training/calibration data, then keep it fixed.
5. **Primary comparison:** Dragon onset recall at the frozen false-alert
   limit on the new patch, M3 against the stronger of B3 and the frozen M1
   policy. Secondary: Baron, Teamfight, every horizon AP and Brier score,
   calibration by route/phase/coverage, and utility across alert budgets.
   A higher macro AP cannot replace a failed primary warning comparison.
   Use a match-level paired bootstrap, stratified by route/patch, for an
   interval on the recall difference and false-alert difference. Seeds are
   repeated fits, not independent matches. Predeclare how seed results are
   aggregated and how secondary multiplicity is controlled.

The M3 model implementation, freeze, calibration and fresh cohort are **not
completed** by the diagnostic in this branch. Estimate storage before staging
anything new; reuse the existing 340 MB graph shards and keep exposure masks
as a small sidecar if the audit supports the experiment. The user's archived
raw collection is not needed for this train/calibration diagnostic.

## Publication checks

- Prove each prediction input existed at its genuine frame timestamp. Do not
  back-fill event outcomes, interpolate 10-second snapshots, or turn a
  retrospectively qualified combat episode into an input feature.
- Verify normalization source-field presence, 180-second eligibility, sealed
  temporal split, checksum bindings, patient/match-style cluster boundaries,
  sample exclusions, censoring and missing-data denominators.
- Make model and threshold selection on different matches. Reserve a fresh
  patch for one final comparison, publish the preregistered M1 test outcome
  separately, and keep exploratory post hoc analyses visibly labeled.
- Publish code, definitions, synthetic fixtures, provenance and aggregate
  results. Riot raw timelines, match identifiers, and any source with player
  identifiers stay private under the recorded redistribution scope.

## Closest primary sources

- Yang et al., [Predicting Events in MOBA Games](https://arxiv.org/abs/2012.09424),
  event prediction from high-frequency Honor of Kings data.
- Yèche et al., [Temporal Label Smoothing for Early Event Prediction](https://proceedings.mlr.press/v202/yeche23a.html),
  early-warning utility at low false alarms.
- Oskarsson et al., [Temporal Graph Neural Networks for Irregular Data](https://proceedings.mlr.press/v206/oskarsson23a.html),
  irregular and partially observed graph sequences.
- Qi et al., [Toward Conditional Distribution Calibration in Survival Prediction](https://proceedings.neurips.cc/paper_files/paper/2024/hash/9c8df8de46c1a1b39b30b9f74be69c02-Abstract-Conference.html),
  conditional probability calibration under censoring.
