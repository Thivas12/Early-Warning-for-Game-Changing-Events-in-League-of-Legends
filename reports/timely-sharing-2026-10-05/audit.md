# Remaining identification gap and safeguards

The original MSc hypothesis invokes both temporal buildup and shared learning
for Baron, Dragon and teamfights. The [notebook continuation](../../docs/notebook-continuation.md)
records the leakage and hindsight-warning repairs. The useful-lead target
study fixed a later omission: the cumulative labels rewarded some events too
close to warn usefully. Its gains occur in both LeagueEWS and TCN. Subsequent
history interventions tested that component under the repaired targets.

The independent-event controls still used cumulative targets. Transferring their
Baron harm / Dragon gain pattern directly to the timely models would conflate
target definition with task sharing. This study completes the missing fourth
cell of a two-by-two comparison:

| Supervision | Joint encoder | Independent event encoders |
|---|---|---|
| Cumulative labels | Completed original control | Completed nine-fit sharing control |
| Useful-lead evaluated labels | Completed timely control | Nine new fits in this study |

The new primary is useful-lead joint minus useful-lead independent recall,
using the same preselected policy rules and original fixed seeds. The paired
interaction subtracts the cumulative sharing contrast. Equivalently, it is the
joint target effect minus the independent target effect. The analysis verifies
that identity for every point and shared bootstrap draw. A positive interaction
would mean the joint recipe benefits more from the target repair, not that
sharing is necessarily beneficial in absolute terms. The primary and both
component effects must therefore be reported alongside the interaction.

Independent fits preserve per-event architecture capacity, initial weights,
unused-head forward/dropout calls, optimizer hyperparameters, original event
loss weights, normalizer, histories, masks, batches and twelve-epoch budget.
Only each event's own four columns supervise its encoder; the evaluated30/60
columns use the useful next-event targets and10/20auxiliaries stay cumulative.
Unused heads remain allocated/frozen solely to preserve initialization and RNG.
Their predictions are never treated as trained outputs. Each fit has1,749,591
active parameters (1,751,647 allocated); an independent three-event system uses
5,248,773 active parameters and about three times the encoder training/inference
work of one joint model. Equal per-task capacity does not imply equal resources
or equal optimization difficulty.

The five fixed warning policies and four fixed budgets are retained. Shared
early expected burden is not shared later burden. Report both warning components,
all seed signs, both lead windows, every event and region, and every nominal or
hard-one overrun. Do not construct an ensemble by choosing the best heads on
later calibration, tune loss weights, or change the primary after seeing results.
Existing joint-model regional failures cannot be rescinded by this diagnostic.

The [previous timing deviation](../clock-history-2026-10-04/protocol-deviation.json)
is directly addressed in the new runner: after all nine fits, missing analysis
release returns without loading the fitted-model calibration scoring path.
A release must bind the training freeze, plan and complete declared analysis
source set to an existing Git commit. Changed or absent releases block scoring.
The release is issued under the study lock before any score artifact exists.
All234early policy heads must additionally freeze before later replay.
Checkpoint/model/RNG continuity and nonfinite-parameter preservation are tested.

Inference uses3,000whole matches with1,500per region and2,000shared stratified
bootstrap draws. The same weights pair all events, model variants, seeds,
policies and budgets. Rows, seeds and budgets are not independent samples.
Intervals are conditional, pointwise and unadjusted; they omit refitting,
adaptive-search, policy-selection and realized mixture randomization variance.
Player overlap across matches is not identifiable in the archive. All these
calibration matches have already informed research decisions. There is no fresh
confirmation or new-patch performance claim.

This comparison cannot separately identify gradient conflict, task-loss scaling,
representation competition or causal in-game mechanisms. PCGrad's prior mixed
results remain preserved, and established multitask methods preclude calling
ordinary independent supervision or task balancing novel. Baron/Dragon labels
mean objective completion, not engagement onset. Real observation cadence
remains unchanged; no artificial frames or non-League data are introduced.
Patch16.17 stays sealed, and all original primary results remain in the record.

## Why the previous gradient finding is not a mechanism diagnosis here

The [prior aggregate gradient review](prior-gradient-review.json) preserves the
original three-seed measurements. Other tasks oppose Baron's own raw gradient
component in 43.75%,41.67%,47.92% of the fixed training batches. The full summed
raw gradient points uphill for Baron in only 2.08%,2.08%,0% of those batches.
Opposition of one component is not equivalent to a harmful total update; Adam
preconditioning and future optimization complicate that interpretation further.
Those measurements use final cumulative-label checkpoints and cannot be treated
as measurements of the useful-lead models. No new gradients or fits were run
for this review, and the active training worker was not disturbed.
