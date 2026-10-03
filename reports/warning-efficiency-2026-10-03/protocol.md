# League warning-efficiency diagnostic

The PCGrad study increased primary macro recall by 0.367 percentage points over
ordinary joint LeagueEWS while adding 0.0459 false-plus-late warnings per match
per event. That comparison does not establish a more efficient warning system.
The next diagnostic asks whether its gain survives matched **early-calibration**
warning cost, and whether it persists across four fixed budgets. This is an
adaptive exploratory analysis of completed League models. Patch 16.17 stays sealed.

The machine-readable plan is `plan.json`. Select policies for every family,
seed, event and horizon on early calibration before evaluating any new policy
on later calibration. Reproduce the original deterministic budget-1 thresholds
and every original later match count exactly. Compare the original deterministic
policy rule with region-specific convex mixtures of at most two whole-match
threshold policies. The latter match expected early cost exactly at 0.25, 0.50,
0.75 and 1.00 false-plus-late warnings per match. Apply this flexibility to every
model, and report subsequent cost drift. Expected counts integrate the threshold
randomization analytically; threshold choice occurs once per match.

This adds no fitted model and makes no new method claim. Exact early matching
is neither later equality nor a future risk guarantee. Equality can force a
policy to spend an unhelpful warning budget. These are diagnostic operating
points, not a proposed deployment policy. The original registered LeagueEWS–GRU
comparison is preserved, including its failed regional budget gate. A favourable
new contrast cannot revise that outcome or establish novelty.

Use all three seeds, both regions, all three events and both lead windows.
Bootstrap paired whole matches, with the same draws for all budgets, policies,
models and seeds; never treat rows, budget points or repeated fits as independent
matches. Report false and late warnings separately as well as their sum. The new
primary diagnostic averages PCGrad–joint primary macro recall over the four
matched-early budgets. Its five frozen gates and uncertainty limitations are in
the plan. No post-result worthwhile-effect margin is invented.

Run from this worktree with the existing research Python and private study paths:

```bash
bash scripts/run_warning_efficiency.sh PYTHON ARCHIVE CONTROL HISTORY INDEPENDENT PCGRAD OUTPUT \
  reports/warning-efficiency-2026-10-03/plan.json --early-only
# Commit the paired analysis implementation before removing --early-only.
# Rerun the same command without --early-only for gated later evaluation.
```

The runner takes an exclusive output lock and shared locks on completed controls.
It verifies all 27 fit/checkpoint/score bindings, snapshots its source hashes,
and checkpoints every selected and evaluated head. Resumption accepts only
identical source, plan, inputs and artifact bindings. Controls are read-only.
Only aggregate evidence, code and provenance are suitable for publication;
private match counts, predictions and model binaries remain under `data/private`.

Implementation validation before execution: 17 focused tests pass, including
independent sequential replay, float-boundary/cooldown/event-credit cases,
mixture optimization against a separate linear-program solver, full-selection
gating, resume/tamper rejection and whole-match mixture evaluation. These are
implementation fixtures, not empirical research results.
