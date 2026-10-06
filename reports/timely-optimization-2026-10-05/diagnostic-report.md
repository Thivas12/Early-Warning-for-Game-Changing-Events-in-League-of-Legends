# Useful-lead optimization: training-only diagnostics

The local probes support testing loss weighting separately from projection; they
do not establish the cause of the observed warning-performance deficit. No new
model has been fitted by this diagnostic, and no test payload has been opened.

The [protocol](diagnostic-plan.json) and executable were committed as `54ebaa2`
before execution. All 576 probes completed on 6 October 2026: four optimizer
cells on one fixed 256-row batch from each of 48 training shards, for each of
the three original useful-lead joint checkpoints. Every probe restored the same
model, AdamW moments and RNG state. Before/after loss measurements used identical
dropout masks. Original checkpoint hashes remained unchanged. Archive validation
checks development arrays, but these probe statistics use training rows only.

Counts below are batches whose observed unweighted event loss increased after
one virtual AdamW update. Each seed contributes 48 batches. Rows within and
across these batches are not independent experimental units.

| Cell | Baron, by seed | Dragon, by seed | Teamfight, by seed |
|---|---|---|---|
| Original weights, ordinary sum | 4, 2, 12 | 0, 0, 4 | 0, 0, 0 |
| Equal weights, ordinary sum | 0, 0, 3 | 2, 0, 4 | 9, 0, 10 |
| Original weights, PCGrad | 1, 1, 7 | 0, 0, 2 | 0, 0, 0 |
| Equal weights, PCGrad | 0, 0, 2 | 0, 0, 2 | 6, 0, 4 |

Seeds are 20260930, 20261001 and 20261002. Original weights are (1, 2, 2.5);
equal weights are (11/6, 11/6, 11/6), preserving total weight 5.5. PCGrad projects
shared gradients only. Full unrounded measurements, including first-order
changes under the actual AdamW update, gradient norms and pairwise cosines, are
in [diagnostics.json](diagnostics.json).

Raw gradient sums and actual AdamW updates disagree. For example, in seed
20261002 the original raw sum is an ascent direction for Baron in 3/48 batches,
while the actual full-parameter AdamW first-order change is positive in 11/48;
the observed loss rises in 12/48. Stored momentum, preconditioning, weight decay
and curvature prevent a raw-gradient cosine from identifying training harm.
PCGrad itself does not guarantee descent after AdamW.

Equal weighting helps local Baron loss directions but can worsen teamfight
directions. These probes all start with moments learned under original weights
at the final checkpoint. They cannot predict an alternative training trajectory
or held-out warning utility. The [next factorial protocol](plan.json) therefore
fits all three missing cells across all seeds, reports all events and both lead
windows, and retains the primary warning endpoint and all prior failed gates.

The methods are established controls. [PCGrad](https://proceedings.neurips.cc/paper/2020/hash/3fe78a8acf5fda99de95303940a2420c-Abstract.html)
already addresses conflicting task gradients; [GradNorm](https://proceedings.mlr.press/v80/chen18a.html)
addresses task balancing, and [CAGrad](https://proceedings.neurips.cc/paper/2021/hash/9d27fdf2477ffbff837d73ef7ae23db9-Abstract.html)
uses local task improvement to regularize joint optimization. This factorial
study is a diagnostic of the LeagueEWS recipe, not a new optimizer or breakthrough.
