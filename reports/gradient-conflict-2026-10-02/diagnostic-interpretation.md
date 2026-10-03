# Why test gradient conflict mitigation?

The completed sharing intervention found higher Dragon recall and lower Baron
recall under joint training. This next study tests an established optimization
intervention, PCGrad, to assess whether changing shared task gradients can
improve that tradeoff. It does not introduce a new algorithm or establish that
gradient conflict caused the earlier result.

Before selecting this intervention, a read-only diagnostic used one fixed
256-row batch from each of the 48 training shards, at each of the three final
joint checkpoints. Sampled rows were identical across seeds. Training dropout
was enabled, no optimizer step was taken, and checkpoint hashes were unchanged.
These are 144 batch diagnostics, not 144 independent fitted experiments.

| Seed | Other gradients oppose Baron | Raw joint gradient points uphill for Baron | Median weighted gradient norm: Baron / Dragon / teamfight |
|---|---:|---:|---|
| 20260930 | 43.75% | 2.08% | 0.189 / 0.439 / 0.586 |
| 20261001 | 41.67% | 2.08% | 0.194 / 0.421 / 0.539 |
| 20261002 | 47.92% | 0.00% | 0.226 / 0.426 / 0.640 |

Mean pairwise cosines are close to zero (−0.019 to +0.028 across pairs and
seeds). Thus occasional opposition coexists with constructive interactions;
there is no evidence here of uniformly antagonistic task gradients. The
diagnostic ignores curvature and Adam's preconditioning. It samples final
checkpoints, not the training trajectory, and cannot identify causal harm.

The earlier 3,000 calibration matches provide a separate timing diagnostic.
At 10–30 seconds, joint-minus-independent Dragon recall changes are +3.725,
0.000 and +2.156 percentage points, alongside burden changes of +0.253,
−0.034 and +0.107 false-plus-late warnings per match. Corresponding Baron recall
changes are −0.768, +0.675 and −1.535 points. At 20–60 seconds, Baron changes
are negative in every seed (−1.228, −3.930 and −3.224 points), with lower Baron
average precision in every seed. Primary row-AUC changes are small and mixed.
Discrimination, calibration, threshold-grid choices and warning timing remain
plausible contributors; a row metric alone does not explain event-level utility.

The [machine-readable diagnostic](diagnostics.json) includes every gradient
batch and early-calibration probability metrics by event, horizon, region and
match phase, plus chronological warning replay by region. Row strata are
descriptive and have no IID uncertainty claims. Its label-based lead bins place
exact lower-bound ties in the shorter interval; event replay retains the
registered inclusive timely boundaries. Only early calibration enters these
statistics. No new later-calibration comparison selected the intervention.

A further descriptive reading of those same frozen diagnostics, while PCGrad
was training, shows that early-calibration Dragon recall gains occur in both
regions on average (+2.020 points Europe, +1.903 Americas), with extra burden
of 0.102 and 0.116 respectively. Early Baron primary mean changes are −0.304
and −0.785 points, but seed signs are mixed in each region. At 20–60 seconds,
Baron loses recall in every seed in both regions. Its average precision also
falls in every seed in both the 20–30-minute and later match phases. Dragon
average precision rises consistently after 20 minutes at both horizons;
teamfight's primary average precision falls in every seed before 30 minutes.
These descriptive patterns leave event type, phase and policy timing relevant;
they do not identify a gradient mechanism. This reading did not amend the plan.

The frozen [plan](plan.json) therefore tests a limited hypothesis: can PCGrad
recover Baron timely recall while retaining the other tasks and satisfying the
same regional warning limits? It preserves model width, history, task weights,
updates, optimizer and policy. Existing joint, independent and TCN results
remain strong controls; GRU and snapshot remain in the complete comparison.
Three backward passes increase compute, and PCGrad changes both gradient
direction and magnitude. Even a positive result would not uniquely separate
gradient interference, scaling and representation competition.

All calibration findings remain exploratory because this development patch
has already informed research. The original registered LeagueEWS–GRU primary
comparison is unchanged. Patch 16.17 stays sealed.
