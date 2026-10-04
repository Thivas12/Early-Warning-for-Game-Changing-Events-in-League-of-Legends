# Conditional non-timing-history control

The completed useful-lead input study finds a short-lead full-minus-current-only
recall gain of +.650 points [.478, .821], with lower aggregate burden, and a
full-minus-timing-only gain of +2.933 points. Those two interventions cannot
identify whether the useful history is non-timing state: one removes all past
values, while the other removes current and past non-timing values. This gap was
recorded before those new predictions in the prior interpretation gate.

Freeze one further intervention, `clock_history`, across the three original
seeds. Start from the exact current-only operator, then restore genuine history
in the seven original timing/count features and their missingness. Keep every
current feature, frame age, valid mask, length and padded value unchanged.
Full minus this control tests past non-timing state conditional on genuine timer
history and current full state. The new control minus current-only tests the
remaining timer-history representation component. Together their paired point
and bootstrap differences decompose the original full-minus-current contrast.
This does not make either input component a causal effect of in-game actions.

The architecture, initialization, normalizer, dropout, batch order, AdamW,
event weights, useful-next-event evaluated heads, cumulative auxiliary heads
and twelve-epoch budget remain fixed. Run exactly three fits, 576 checkpointed
updates each. Verify the original, timely and six completed input controls;
run one CUDA shard and resume the same checkpoint in one locked worker.
Fault tracing is enabled because the previous study had a recovered native
Python crash. Do not change packages or frozen sources to hide it.

All three fits complete before calibration predictions. Commit the evaluator
and paired analysis before any new predictions. Reproduce all previous 198
heads and their five policies exactly, add the 18 new heads, then jointly
freeze all 216 early heads before later evaluation. Independently replay both
common budget-one policies for every later match of each new head; sample
component thresholds for every head. Preserve the original registered
LeagueEWS-minus-GRU comparison and every previous failed gate.

Primary: full timely LeagueEWS minus `clock_history`, macro10–30-second recall,
equally averaged over the four prespecified matched-early budgets. Report both
components, all events, regions, seeds, lead windows, policies and burden
components. Use 2,000 shared paired whole-match region-stratified bootstrap draws
with the original seed. Rows, seeds and budgets are not additional matches.
Intervals remain conditional, pointwise, unadjusted and adaptive exploratory.

The plan fixes descriptive conditional-history support, event point non-harm,
no-extra-burden and regional consistency rules. Neither a diagnostic pass nor
an early budget choice can rescind the full-input model's previous regional
failures. Effective capacity and optimization still differ after input removal;
this is not a test of temporal order, cross-attention novelty or task sharing.
No new practical promotion or fresh generalization claim is authorized by it.

Use only the unchanged League development ZIP. Patch 16.17 stays sealed. Preserve
all old worktrees, freezes and checkpoints. Publish code and aggregate results,
including negative findings; exclude private scores, matches and model binaries.
