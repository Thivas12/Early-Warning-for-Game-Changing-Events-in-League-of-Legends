# Public replay objective-training screen

Declared after the command and history-command experiments failed. This screen
asks whether training through the cooldown mechanism improves event-level warning
credit on real replay data. It does not propose the refractory recurrence as new
mathematics and does not reuse any evaluated cohort for model selection.

## Diagnostic and prior-art boundary

The retained training set contains 109 matches, 29,249 decision rows, 599 positive
rows and only 76 eligible onsets. Seventy-five onsets have eight eligible warning
rows and one has nine. Only ten decision rows belong to two event windows.
Unequal event multiplicity is therefore not a substantial explanation of the
previous negative results. Large row counts must not obscure the small number
of distinct training events.

Temporal label objectives and survival alarm policies already exist: Yèche et al.,
[ICML 2023](https://proceedings.mlr.press/v202/yeche23a.html) and
[CHIL 2024](https://proceedings.mlr.press/v248/yeche24a.html). Legnaro et al.'s
[2026 wSOL paper](https://arxiv.org/pdf/2606.23145) is now available in full and
explicitly studies differentiable temporal confusion scores. Its gains depend on
the dataset and on whether useful timing information is already in the labels.
It uses a common TCN across losses. Our matched MLP comparison is an application
of its loss equations, not a reproduction of its benchmark results.

Recent [horizon-aware disruption work](https://arxiv.org/html/2609.24443v1) and
[GPU failure warnings](https://arxiv.org/abs/2609.34473) further prevent claiming
that horizon alignment or threshold/persistence/cooldown policies are new.
The existing repository's exact-credit and author-checked wSOL implementations
remain the reference. The proposed test concerns empirical incremental value.

## Fixed development data and representations

Only the hash-verified 109 training and 37 calibration matches in
`command-anticipation-quality-2026-09-30.json`. Never load an evaluation split.
Use the same 197 history features; no command inputs or new feature selection.
Standardize using training means and population standard deviations only;
impute missing standardized values to zero and append missingness flags.
Clip standardized finite values to [-20,20]. Keep the original 20–60-second
labels, 5-second decisions, 60-second cooldown and one-unmatched-per-match
calibration budget. All match boundaries and padded rows remain explicit.

## Matched training

MLP: 394 inputs, two hidden layers of width 64 with GELU, one scalar logit.
Initialize the output bias to the training positive prevalence logit. CPU,
deterministic Torch, four threads, seeds 17/29/43. AdamW, learning rate .001,
weight decay .01, batch eight whole matches grouped by length, gradient norm
clipped at 5. No validation-driven early stopping or checkpoint selection.

For each seed, train one common 10-epoch BCE warm start. Clone its weights into
all seven loss arms, reset optimizers, and train 30 additional epochs using
identical shuffled match batches per arm. Evaluate the final epoch only:

1. BCE, averaged within each match then across matches.
2. Weighted BCE, positive weight sqrt(training-negative/training-positive), with
   the same averaging. This is an established imbalance control.
3. Unweighted soft F1 (SOL) from batch-pooled valid confusion counts.
4. wSOL F1 using max temporal weights (.5,.25,.125) at 5/10/15-second lags.
5. wSOL TSS with the same temporal weights.
6. Independent proposal utility: expected timely proposal count minus a learned
   nonnegative multiplier times (unmatched proposals minus one per match).
7. **Cooldown utility, primary**: replace proposal probabilities with exact
   emitted-alarm marginals under the hard 60-second cooldown in the same utility.

For both utility arms initialize the multiplier at .1. After each batch, update
it by .01 times (batch mean expected unmatched count minus one), projected onto
[0,100]. Multipliers see training outcomes only. Confusion scores pool counts
across a batch while temporal shifts remain within each match; padded rows do
not contribute. Pooling avoids a constant F1 loss on an individual event-free
match. This batching adaptation is explicit and must pass single-match agreement
with the independently author-checked reference and padding/boundary tests.

With a 40-second useful window and 60-second cooldown, at most one emitted alarm
can fall in any one event's window. Thus, for these fixed labels, additive timely
emission credit equals the one-to-one hit count. Verify this independently by
enumerating a small overlapping-event example, not by comparing two expressions
of the same recurrence. Scores at prediction time still use only observed history.

## Calibration, stopping and advancement

Calibrate each final score with the existing fixed quantile threshold search and
deterministic emission policy. All seven arms have identical threshold budgets.
Include the already frozen HGBT history baseline (5/29 calibration hits) as an
external architecture control. Training stochastic utility and deployment's
deterministic threshold are different; expose both, never call the threshold
policy an exact optimizer of the training objective.

Proceed to a separately selected fresh cohort only if, for EACH seed, cooldown
utility catches at least eight of the 29 calibration onsets and at least three
more than the best non-primary neural arm or frozen HGBT baseline, with at most
one unmatched alarm per match. This is an explicit resource-allocation heuristic,
not significance on repeatedly consulted calibration data. Publish all 21 fits,
including failures and degenerate policies. Do not change losses, epochs, seeds,
or this gate after viewing scores. A passing development screen still does not
establish novelty or generalization.
