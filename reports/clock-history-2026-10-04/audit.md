# Identification repair and remaining limits

The [previous audit](../timely-inputs-2026-10-04/audit.md) records the original
notebook leakage, unavailable end-of-match features, fabricated cadence and
hindsight alert selection, plus the continuation's target and threshold-grid
mismatches. Those repairs and every negative result remain in the record.
The source notebooks and final MSc report remain unchanged.

The latest missing comparison was more specific. Full-minus-current-only input
removes both past timer and past other state. Full-minus-timing-only removes
both current and past other state. Positive results from both contrasts cannot
identify a benefit from *past non-timing state*. That limitation was recorded
before the preceding six fits produced their calibration predictions; this
follow-up is still adaptive because its execution follows their results.

This study adds exactly the missing intermediate representation: real timer
history plus every current feature. The same current-only operator first
repeats the current values across valid positions; restoring seven timer/count
columns and their missingness then keeps true timing trajectories. Twenty
other value columns and their twenty missingness columns retain only current
state. Age, mask, valid length, padded positions and the current frame are
unchanged. The three fixed seeds, initialization, parameter count, normalizer,
optimizer, loss, targets, epochs and training examples are held fixed.

For each paired estimate and bootstrap draw:

    full − current = (full − timer-history) + (timer-history − current)

The first term is the primary conditional non-timing-history contrast. The
second is the timer-history component conditional on current full state. This
is a path-specific decomposition under a fixed training recipe, not a full
factorial interaction experiment. Confidence-interval endpoints do not add.
Missingness trajectories are part of the removed information; current features
include historical summaries. Changes in effective capacity and optimization
remain possible explanations for reduced-input performance.

Three implementation checks prevent plausible analytic mistakes: exact zero
conditional differences when full and timer-history counts agree even if the
current-only model is worse; equality of the timer component and total in that
case on identical bootstrap draws; and preservation of all five previous
policies with an all-head early freeze before later evaluation. These fixtures
are software checks, not empirical League data.

The analysis keeps 3,000 later calibration matches (1,500 per region) as the
sampling units, pairing all variants, events, budgets and fixed seeds. It does
not increase sample size by counting rows, repeat seeds or operating points.
Conditional pointwise intervals omit model refitting, policy selection,
adaptive search and realized random-policy assignment variance. The archive
cannot identify shared players across matches, so that dependence is not
modeled. All inspected calibration results remain exploratory.

Full timely LeagueEWS already exceeds the regional hard-one warning budget in
12 of 18 event/region/seed cells under the primary budget-one mixture. This
control cannot erase that failure. Its lower-budget results remain descriptive;
selecting one after inspecting them would not create independent confirmation.
The original registered LeagueEWS-minus-GRU comparison is reproduced unchanged.
Temporal ordering, architectural components, task sharing under useful-lead
labels, and robust regional budget control remain separate hypotheses.

Baron and Dragon are completion labels, not engagement onset. Only actual
League development frames are used. Patch 16.17 remains sealed. No component
result establishes a novel method, a causal effect of game actions, or a
breakthrough in generalization.

## Execution mistake: the analysis release was not enforced

The analysis hash record and successful tests preceded new scoring. Git
approval did not return until after the worker had scored all three fits. The
runner's all-fit gate worked, but it lacked an explicit committed-analysis
release check. Thus the protocol's **commit-before-predictions** requirement
was not met. Source hashes still match the prewritten record; no new prediction
values or policy results had been inspected when this discrepancy was recorded.
The [deviation record](protocol-deviation.json) retains the actual times.

Do not retroactively repair timestamps, discard checkpoints or rerun these
models to disguise the deviation. Keep this analysis unchanged and explicitly
exploratory. Any future runner must stop safely after training until a separate
release verifies the analysis commit and source/plan hashes; approval delays
must not automatically open calibration. The current frozen runner is preserved.
The separate all-early-head policy freeze remains enforced before later replay.
