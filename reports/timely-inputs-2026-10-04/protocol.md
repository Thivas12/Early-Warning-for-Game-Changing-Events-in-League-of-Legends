# Useful-lead input controls: historical state and timing

The completed target and threshold-resolution controls improve warning recall,
but do not identify the original report's temporal-buildup explanation. Earlier
history and sharing ablations used cumulative supervision. This study tests the
missing history intervention under corrected supervision, and whether the full
model adds information beyond observed clock/objective timing trajectories.

The [plan](plan.json) fixes six new LeagueEWS fits: three original seeds for
each of two input interventions. `current_only` uses exactly the previous
trained ablation: repeat current values and missingness at valid history
positions while retaining ages, lengths and masks. `clock_only` retains seven
columns and their missingness throughout the observed history: game clock,
both teams' Dragon and Baron counts, and time since Dragon/Baron. All other
values and their missingness are zeroed. Frame age and valid masks remain.
No target or future event enters either feature path.

Nominal architecture, initialization, normalizer, dropout, shuffles, batch size,
optimizer, update count and event weights match the completed full-input timely
LeagueEWS. Targets are the same useful-next-event 10–30/20–60-second heads and
cumulative 10/20-second auxiliaries. Each fit trains all twelve fixed epochs;
there is no calibration selection, retuning or altered observation schedule.
Original and timely control hashes and runtime must match before fitting.

Run one CUDA shard as a canary, then resume exactly from its model, optimizer
and RNG state in one locked worker. Preserve a valid checkpoint if a nonfinite
update occurs. All six fits must complete before calibration prediction scoring.
Commit the evaluator and paired analysis before any new calibration predictions;
freeze all 198 early heads before any new later-policy result. The eleven
variants include all original families and earlier mechanism controls.

Report original common/regional deterministic rules, matched-early whole-match
mixtures, and the frozen finer common/regional grids, at all four prior budgets.
The primary is full timely LeagueEWS minus timely current-only LeagueEWS:
10–30-second macro recall averaged equally across the four matched-early budgets.
The timing-only contrast and the interaction of history with target definition
are prespecified, with every event, region, seed, lead window and burden component.
Preserve the original registered LeagueEWS–GRU comparison and every failed gate.

Use 2,000 paired whole-match region-stratified bootstrap draws, shared across
models, events, policies, budgets and fixed-seed averages. Rows, repeated seeds
and budgets are not additional matches. These conditional pointwise intervals
exclude refitting, policy-selection and adaptive-search uncertainty. The same
calibration data have informed earlier decisions; this remains exploratory.

The descriptive history, beyond-timing, event-harm, burden and regional-consistency
rules are fixed in the plan. There is no new automatic promotion screen: the
full-input control already fails regional hard-one budgets. Neither lowering an
early budget after results nor hiding a negative event can rescind that failure.
Save all negative results and every regional warning-budget overrun.

These controls test predictive input information under a fixed training recipe.
Current summaries still carry history; masks/ages retain observation timing;
clock-only includes objective trajectories. Removing inputs changes effective
capacity despite fixed parameter count. This does not isolate temporal order,
cross-attention, task sharing or causal effects of game actions. A positive
comparison is not architectural novelty or fresh generalization evidence.

Use only the existing League development ZIP. Patch 16.17 remains sealed. Save
code, aggregate evidence and reproduction instructions; keep all matches, scores
and checkpoints private. No previous experiment file is modified.
