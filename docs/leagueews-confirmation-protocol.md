# One-time confirmation: bounded protocol draft

**Status: specified analysis design; not an executed or release-ready protocol.**
This document is not a new experiment result and does not open patch 16.17.
It defines the finite confirmation needed for the empirical paper. It does not
replace the original RiftHazard hypotheses, old LeagueEWS screens or their
recorded failures. All choices below follow inspected development data.

## Question and claim family

The claim is transfer of particular fixed-recipe effects to one later patch,
not a new learning principle or proof of practical coaching utility. Evaluate
all four comparisons together, preserving the stated direction even if the
observed sign reverses. No primary comparison can be exchanged for a favorable
secondary event, region, seed, budget or horizon.

| ID | Locked comparison | Endpoint and policy | Direction |
|---|---|---|---|
| C1 | Useful-lead original-weight LeagueEWS minus its timer-history/current-state control | Macro 10–30 s recall; mean of the four already selected matched-early mixtures | Positive |
| C2 | Useful-lead original-weight LeagueEWS minus cumulative-target original LeagueEWS | Macro 20–60 s recall; same matched-early four-budget mean | Positive |
| C3 | Useful-lead original-weight joint LeagueEWS minus useful-lead independent event encoders | Macro 20–60 s recall; same matched-early four-budget mean | Negative |
| C4 | Equal-weight useful-lead LeagueEWS minus equal-weight useful-lead TCN | Macro 10–30 s recall; mean of the four already selected capped-KL policies | Positive |

These choices confirm the empirical paper's specific development findings.
They do not assert that a nonzero effect is large enough for a user. No
post-result minimum worthwhile effect or noninferiority margin is introduced.
The different policies and training recipes must remain visible in reporting.
C4 confirms the later risk-policy architecture comparison (+0.225 development
points); it is not an exact replication of the +0.242 matched-mixture estimate.

## Frozen assets and population

Use the original audited 6,000 test matches from patch 16.17, retaining both
regions, all registered event definitions and all original exclusions. Do not
discard matches because of events, confidence, warnings or poor predictions.
Do not add matches after seeing the outcome. Preserve original train and
calibration membership and the sealed payloads until an executable release
record is complete under the project's existing data boundary.

Bind the exact original three-seed checkpoints, normalizer, feature/label code,
policy thresholds, mixture probabilities, cap and cooldown. Models may not be
refitted, ensembled, recalibrated or retuned. C1–C3 reuse the previously frozen
mixture components and probabilities; C4 reuses the previous common-threshold
KL policies. No threshold is selected or adjusted using test outcomes. The
population-risk guarantee of the KL theory is not asserted under patch shift.

The required family inventory is cumulative LeagueEWS, useful-lead original-weight
LeagueEWS, useful-lead timer-history control, useful-lead independent event
encoders, useful-lead equal-weight LeagueEWS and equal-weight TCN. Independent
encoders retain their existing event-specific fits. The runtime benchmark's
explicit float32 setting must not silently replace the predictive studies'
inference configuration: an executable confirmation must reconstruct and bind
the original CUDA prediction configuration and verify development-score parity
before accessing any test payload.

## Analysis

Reuse the registered chronological warning semantics and event denominator,
including events without an observed opportunity. Average the fixed-seed
event metrics and then the three event types according to the existing
analysis implementation; do not pool seeds as independent matches. Report
precision, total/false/late burden and event counts alongside recall.

Use 10,000 paired whole-match bootstrap draws, stratified by region, with seed
20261007 and the identical draws shared by every model, policy and endpoint.
All fitted training seeds remain fixed. For four primary contrasts, report
two-sided 98.75% percentile intervals, using quantiles 0.00625 and 0.99375.
This is a Bonferroni allocation of nominal interval error across the four
comparisons. It is an approximate bootstrap familywise procedure, not an exact
finite-sample guarantee. A directional finding is supported only if its entire
adjusted interval has the prespecified sign. Report all four outcomes.

Retain pointwise 95% intervals for the complete secondary table: every event,
both regions, both lead windows, each budget and every fitted seed. Mark these
as descriptive and unadjusted; they cannot rescue a failed primary comparison.
Report every nominal warning-budget overrun and the maximum regional burden.
An interval crossing zero does not imply equivalence; a negative event result
must not be hidden by a positive macro mean. Correlation between matches sharing
players is a limitation unless independently bound player-group information
supports an additional prespecified sensitivity analysis.

## Executable release conditions

The remaining implementation must produce one manifest containing complete
checkpoint and policy hashes, test membership hash, processed-payload checksums,
source and environment hashes, expected head/match counts and the exact command.
Before test access, it must pass development prediction parity and independent
scalar replay checks, verify that no source can tune on test data, and commit
the full executable analysis and manifest. The design alone is not that gate.

No held-out payload was opened to write this protocol. Original processed-data
directories and split metadata are present locally; payload availability and
integrity must be checked through the controlled release implementation, without
previewing outcomes. Do not claim a missing upload unless that check establishes
an actual access problem.

## One result, including a negative one

Release the test once for the full comparison family. A technical interruption
may resume byte-identical work, preserving partial files and recording the
failure; it may not revise the predictor or selected policies. Publish all
results and update the manuscript regardless of direction. If confirmation
fails, the paper becomes an explicit non-replication or development-only result.
It must not trigger another search on patch 16.17. Further method development
would need a new question and genuinely new confirmation data.
