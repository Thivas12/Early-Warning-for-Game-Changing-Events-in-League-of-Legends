# Research program: recurrence, geometry and useful event warnings

**Revised 2026-09-29 after a research and implementation review.** This is a
post-M1 exploratory proposal. The original M1/M2 targets, losses, metrics and
registered comparisons remain frozen. The full evidence, primary literature,
reproducible calculations and controlled counterexamples are in
[`research-assessment-2026-09-29.md`](../reports/research-assessment-2026-09-29.md).

## Corrections to the earlier proposal

1. **Verified completed match termination is not automatically censoring.**
   If the event stream is complete through match end, an event that did not
   occur before termination is a known negative for the actual-match outcome,
   even when the requested horizon extends beyond termination. True source
   truncation while play continues is different. Final-frame/duration
   disagreement alone cannot distinguish these cases.
2. **The boundary mask is a diagnostic, not an established target correction.**
   `confirmed_followup_masks` measures coverage through the earlier of the last
   frame and screened duration. Its excluded negatives can include valid
   completed-match outcomes. Including partial-bin positives while dropping
   partial-bin negatives also introduces a discretization approximation.
   `censored_hazard_bce` is an unweighted masked binary loss; the mask does not
   automatically make it a correct likelihood for the desired continuous-time
   risk. Do not train a replacement merely because the audit finds many
   boundary-crossing rows.
3. **An unseen test is not invalidated by development on calibration data.**
   If patch 16.17 remains genuinely sealed, a documented amendment can freeze
   additional comparisons before one joint test release. Preserve the original
   registered analysis, identify added claims and handle multiplicity. A fresh
   cohort is necessary after adapting to test outcomes and valuable for claims
   across multiple patch transitions; it is not automatically mandatory here.

## Findings that determine the next experiment

- Existing calibration results: M1 macro AP 0.49112 versus B3 0.37594,
  but Dragon event F1 0.58807 versus 0.71183 and false alerts/game 1.94413
  versus 1.55200. Better aggregate ranking has not delivered better Dragon
  warnings at the reported operating points.
- B3 receives objective counts and time since the last Dragon/Baron. M1 graph
  construction omits those explicit recurrence features. A paired synthetic
  probe confirms that changing a past Dragon kill leaves its graph unchanged.
  Whether this omission explains the performance gap requires a matched refit.
- Removing interaction edges leaves 78.48% of the numerical M1-versus-B3 AP
  gap. That is descriptive arithmetic, not a causal attribution. A player-set
  model with comparable geometry and history is an essential control.
- The cooldown suppresses alerts exactly 60 seconds apart. The combat outcome
  is a temporal multi-kill proxy without spatial coherence or total-duration
  constraints. Preserve both frozen conventions; label and examine them
  explicitly in the follow-on protocol.

All performance above is from existing public transcriptions of private-run
calibration summaries. This review did not train new private-data models or
open sealed test payloads.

## Primary question and controlled comparison

**Do temporal player relations improve useful Dragon warnings beyond objective
recurrence and observed geometry under sparse telemetry?** Use Dragon within
60 seconds as the primary follow-on outcome, with Baron and the combat proxy
secondary. Finish the original registered M1 analysis under its original rules.

Give every new contender identical causal global information: game time,
observed objective counts, time since the last objective, source-availability
indicators, and patch-specific availability state only where validated from
past events and recorded rules. Future duration, frame times and retrospectively
qualified episodes are target metadata, never prediction inputs.

| Contender | Question answered |
|---|---|
| Recorded B3 and M1 | Historical reference under the frozen protocol. |
| B3 with comparable participant/pit geometry and objective history | Does a cheap, informed model suffice? |
| Player-set encoder + GRU + global history, without relation messages | What do relations add beyond player states and history? |
| M1 encoder + global history | Does the confirmed omission affect Dragon warnings? |
| Event-specific relational readout + global history | Does objective-focused aggregation improve shared mean pooling? |

Use the same temporal development split, input availability, seed list,
selection budget and policy search. Record model size and compute; equal
_epochs_ alone do not equalize optimization. Architecture selection belongs on
an inner development split; probability and policy calibration use their
declared partitions. Report all assigned seeds.

Compare direct 60-second probability prediction and the existing hazard
formulation on the same actual-match target. Begin with unweighted binary
loss. Investigate an exposure likelihood only if genuine incomplete event
ascertainment is established. If cause-specific survival is used, integrate
match termination as a competing terminal event when computing actual risk.
Weighted/focal objectives need separate probability calibration checks.

## Warning policy and decision rule

Select the threshold to maximize Dragon recall subject to at most one false
alert per match on the tuning partition, then report the realized burden on
disjoint evaluation matches. The budget on tuning data is not a guarantee
under drift. The original F1-selected operating point does not answer this
constrained question. Predeclare a cooldown convention, one-to-one matching,
the primary contrast, seed aggregation, minimum useful effect and multiplicity.

Report all-event and opportunity-conditional recall, precision, false alerts
per match and per hour, their per-match quantiles, lead-time median and p10,
AP and Brier/calibration by event, horizon, route and phase. Resample paired
whole matches for uncertainty; seeds are repeated fits, not independent
samples of a patch. Account for repeated players when the recorded grouping
information permits it. Opportunity denominators must match the warning
window and any minimum lead requirement.

## Role of the existing boundary audit

`make audit-confirmed-followup` binds train/calibration processed matches,
staged targets, the frozen split, selected-pool durations and selection
manifest by checksum. It counts rows crossing the earlier of duration and
last frame and checks target consistency. `make render-confirmed-followup`
renders those counts. Neither reads test match payloads.

The retained v1 field names such as `negative_labels_without_full_followup`
describe the mask's boundary criterion. They **do not establish that the
actual-match outcome is unknown**. Interpret the figure the same way. Event
ascertainment, completed termination and actual truncation must be checked
before deriving a different training population or loss. The archived raw
collection is not needed simply to reanalyse the existing aggregate results.

## Publication scope

MOBA event forecasting, temporal graph models, survival losses and early-alarm
objectives all have prior art; see the full report's nine-paper comparison.
A graph/GRU/hazard/gate combination alone is not a demonstrated novelty claim.
The contribution must be the measured value of relations under controlled
information, realistic observation cadence, alert burden and temporal shift.

Retain the registered combat proxy and validate any new tactical-teamfight
endpoint separately. Reconcile publication tables with original score
artifacts. Treat the present dataset as retrospective observer-style Match-V5
forecasting; establish live API field and visibility parity before claiming
a deployable player application. Keep private source timelines and player
identifiers within the recorded redistribution scope.
