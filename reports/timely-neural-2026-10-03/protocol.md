# Frozen timely-target neural control

Purpose: test the missing objective-alignment control in LeagueEWS and the
stronger sequence baseline TCN. The [audit](audit.md) explains the prior omission
and the concrete target/evaluator mismatch. This is six new fits, two families
by the original three seeds, on the existing development data and GPU. No model
is selected from calibration and no previous checkpoint is modified.

The [machine-readable plan](plan.json) fixes the intervention and comparisons.
Only the two evaluated output targets per event change: the next strictly
future event must lie in the closed 10–30 or 20–60-second lead interval. The
10/20-second cumulative auxiliary heads, all model parameters, initialization,
optimizer, event weights, input rows, normalization, masks, shuffles and twelve
epochs remain those of the original respective family. This changes shared
supervision; it does not isolate loss scaling from representation learning.
Mixed output semantics mean cross-horizon probability monotonicity is no longer
an appropriate test. Row metrics must use each head's fitted target definition.

Every training shard saves model, optimizer and RNG state atomically. Nonfinite
loss or parameters refuse to replace the previous valid checkpoint. All six
fits must finish before calibration predictions are saved. Policy evaluation
is a separate step: commit its implementation and select/freeze all early
policies before inspecting any new later-policy result.

Evaluate all seven previous variants plus timely LeagueEWS and timely TCN,
three seeds, three events, two lead windows, both regions and four fixed budgets.
Include the original common deterministic policy, a new regional deterministic
control and the previous exact-early-cost regional mixture. The new control
makes region selection inspectable separately from mixture interpolation.
Mixtures are whole-match policies and evaluation integrates their randomization
analytically. Early equality does not guarantee later equality.

The new primary diagnostic is timely LeagueEWS minus original LeagueEWS:
10–30-second macro recall, averaged equally across four matched-early budgets.
Also compare timely TCN to its original, both timely families to each other, and
the difference between those two target effects. All other frozen contrasts are
reported. Preserve the original registered LeagueEWS–GRU result and failed gate.
Report the objective effect, event harm, burden, strong control and regional
gates separately. Passing an exploratory gate is not a breakthrough.

Use 2,000 whole-match bootstrap draws, stratified by region, shared across every
model, event, seed, policy and budget. Average fixed-seed metrics; do not inflate
sample size by rows or repeated fits. Intervals condition on trained models and
selected policies and are pointwise unadjusted. All negative results and regional
failures remain in the report. No test release or new collection is included.

Before fitting: verify the original source/checkpoint/score hashes, recompute
and compare the training normalizer, check the same runtime, and run a one-shard
CUDA canary. Resume the canary in one locked worker; never start a second worker
for the same output. Keep the execution code fixed thereafter.
