# Shared-threshold utility follow-up

Declared after the small-data 21-fit comparison and its stochastic-policy audit,
while the expanded seven-loss experiment was running. The first six expanded
seed-17 control scores were visible (6, 5, 10, 8, 11, 9 hits of 127); its
cooldown-utility score had not yet been inspected. No shared-threshold fit or
score exists at declaration. This is an additional exploratory development
experiment, not part of the original preregistered comparison.

## Hypothesis and prior-art boundary

Independent Bernoulli alarm proposals during training and one fixed threshold
during deployment induce different joint decision distributions. The small-data
audit also shows a substantial train/calibration gap; this experiment cannot
assume that policy mismatch, rather than overfitting, causes it.

For a match, draw ONE threshold uniformly on [0,1], use it at every decision,
apply the ordinary causal 60-second cooldown, and score the resulting alarms.
Integrate timely hits and unmatched counts over all threshold intervals exactly.
Sort scores descending. For each prefix, compute the deterministic emitted-alarm
counts; the difference between consecutive prefix counts is the coefficient of
that sorted score. This is the established Lovasz extension of the corresponding
set function, not a new integration theorem. See
[Berman et al., CVPR 2018](https://openaccess.thecvf.com/content_cvpr_2018/papers/Berman_The_LovaSz-Softmax_Loss_CVPR_2018_paper.pdf)
for the standard sorted-increment construction and loss-optimization precedent.
Our alarm set function is not asserted to be submodular or the extension convex.
No consistency, optimality, or state-of-the-art claim follows from exact integration.

Because useful event windows are 40 seconds wide and cooldown is 60 seconds,
the existing binary timely labels give exact one-to-one hit counts for emitted
alarms. The policy still sees only current/past inputs. Future labels and later
decisions enter supervised training rewards, never current model features.

## Fixed comparison and checks

Add exactly one loss arm at each of the two frozen development data sizes,
seeds 17/29/43: six additional final fits. Reuse the same saved BCE warm starts,
training-only preprocessing, 197 history inputs, MLP, identical shuffled whole-
match batches, AdamW settings, gradient clipping and 30-epoch schedule. Reset
the utility multiplier to .1 and update by .01 times (mean expected unmatched
count minus one), clipped to [0,100], as in the two previous utility arms.
Use exact shared-threshold hit/unmatched expectations in that objective.

Verify values by independently integrating interval-midpoint policies using the
actual alarm emitter and one-to-one matcher. Check gradients by finite
differences away from ties, tie-valued expectations, padding, cooldown boundaries,
overlapping targets and event-free matches. The compiled count loop may improve
speed but must agree with those independent checks. Stable sort supplies a
deterministic region gradient at ties; no differentiability at ties is claimed.

No new evaluation data, hyperparameter search, early stopping or seed selection.
Use the original fixed calibration search for the final epoch. Compare against
ALL seven existing neural arms and the tree control for the same size and seed.
Small gate: at least 8/29 hits AND at least three more than the strongest control
for EACH seed, within one unmatched/match. Expanded gate: at least 25% recall
AND at least 10 percentage points above the strongest control for EACH seed,
within the same budget. These gates are resource heuristics, not significance.
Publish all six fits, including a negative result. A passing development result
still requires a newly frozen independent evaluation cohort.
