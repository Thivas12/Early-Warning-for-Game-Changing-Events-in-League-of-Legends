# League shared and independent event learning

**Joint training raises Dragon recall but lowers Baron recall under the frozen
LeagueEWS recipe.**
All nine independent event fits and their gated evaluations completed successfully.
The modest average recall gain from sharing hides Baron degradation in every
seed, and both approaches have a regional warning-budget failure. This is evidence
of a task-dependent tradeoff, not a breakthrough or a new learning method.

## Timely warnings across all models

Mean recall with 10–30 seconds of lead, across three fixed seeds. Burden is
false-plus-late warnings per match per event, averaged over events and seeds.
The independent row combines three separately trained event encoders per seed.

| Model | Baron recall | Dragon recall | Teamfight recall | Macro recall | Mean burden |
|---|---:|---:|---:|---:|---:|
| Joint LeagueEWS | 20.878% | 13.176% | 3.082% | 12.379% | 0.865 |
| Independent LeagueEWS | 21.506% | 11.257% | 3.038% | 11.934% | 0.840 |
| GRU | 12.085% | 8.977% | 2.204% | 7.755% | 0.785 |
| TCN | 20.734% | 13.532% | 2.834% | 12.367% | 0.864 |
| Snapshot | 18.636% | 11.743% | 2.590% | 10.990% | 0.845 |

The focused contrast is joint minus independent LeagueEWS. Differences are
percentage points; intervals are conditional paired 95% intervals.

| Event | Recall difference and interval | Seed differences in original order |
|---|---:|---|
| Baron | **−0.627 [−1.155, −0.071]** | −0.123, −0.278, −1.481 |
| Dragon | **+1.918 [+1.677, +2.162]** | +3.637, +0.026, +2.092 |
| Teamfight | +0.044 [−0.066, +0.148] | −0.354, +0.323, +0.162 |
| Macro | **+0.445 [+0.251, +0.644]** | +1.053, +0.024, +0.258 |

Seeds are 20260930, 20261001 and 20261002. The positive macro effect meets the
frozen descriptive rule, but its magnitude varies substantially. Independent
macro recall ranges from 11.720% to 12.182% across seeds, with sample SD 0.233
points; joint recall ranges from 12.156% to 12.773%, with SD 0.343 points. These
fit differences are not covered by the conditional match-sampling interval.

## Burden and regional failures

Sharing adds **0.025** false-plus-late warnings per match per event on average:
0.018 more false and 0.007 more late warnings. Dragon's recall gain accompanies
0.104 additional warnings per match: 0.075 false and 0.029 late. The comparison
uses the same early-calibration selection rule, not equal realized warning burden.

Both variants fail the primary Americas Baron budget in one seed: joint seed
20261001 produces **1.0113** false-plus-late warnings per match, and independent
seed 20260930 produces **1.0080**, against a limit of one. Neither has a Europe
primary budget failure. Averaging seeds does not remove these failures.

The Baron recall penalty is clearer in Europe: **−1.201 points [−2.010, −0.385]**,
versus −0.061 [−0.797, +0.705] in the Americas. Dragon gains occur in both regions.
Macro gain is +0.247 [−0.040, +0.537] in Europe and +0.640 [+0.368, +0.915] in the
Americas. The frozen no-task-harm and practical promotion rules fail.

At 20–60 seconds, joint minus independent macro recall is **−0.270 points
[−0.559, +0.008]**, with mixed seed signs. Baron falls by **2.139 points
[1.371, 2.956]**, negative in every seed. Dragon improves by 0.877 points and
teamfight by 0.451 points, although the teamfight sign varies by seed. Both
variants meet every regional budget at this secondary endpoint.

## What the mechanisms support

The earlier matched history intervention supports an incremental 0.851-point
macro benefit from past observed state, mainly for Baron. The original
architecture comparison finds no clear hybrid advantage over TCN. This new
intervention establishes an event-dependent effect of the joint training and
calibration recipe. It does not identify gradient conflict, representation
competition, loss scaling or threshold timing as the cause. These interventions
are separate comparisons, not an additive decomposition of the GRU gap.

The original registered LeagueEWS versus GRU contrast remains **+4.623 points
[+4.223, +5.064]**, and its regional-budget gate remains failed. LeagueEWS versus
TCN remains +0.012 [−0.156, +0.178]. The new comparison does not replace the
registered primary or establish broad architectural superiority.

The consequential unresolved question is why added supervision helps Dragon
while reducing Baron warning recall. A future mechanism study should use training
and early-calibration diagnostics to distinguish optimization from warning-timing
effects, then freeze appropriate joint, independent and established multitask
controls. A mixture chosen from the best later-calibration heads would need a
separate study. Existing transfer methods already address task-specific harm;
see the [targeted literature check](literature.md).

## Scope and reproducibility

Each independent fit matches the joint encoder's width, history, initial seed,
dropout randomness, batches, optimizer and original event loss weight. Only its
event's four horizons supervise it. Three independent encoders use 5,248,773 active
parameters versus 1,751,647 joint parameters; this matches capacity per event,
not total resources. Nine fits completed 5,184 shard updates. All score files
postdate the final training checkpoint, and the worker exited 0.

The study reuses 24,000 League training matches and 6,000 calibration matches.
Thresholds use the earlier 3,000; reported evaluation uses the later **3,000
distinct matches**. All 18 new policies passed independent chronological replay.
The 2,000 paired whole-match bootstrap draws preserve regions and share sampled
matches across events and seeds. They condition on fitted models and thresholds;
rows and repeated seeds are not independent match populations. Calibration was
already inspected, and intervals are exploratory and unadjusted. Baron and Dragon
targets are completions, not engagement onset. **Patch 16.17 remains sealed.**

- [Complete regional and seed tables](tables.md) and [seed CSV](by-seed.csv)
- [Analysis, paired uncertainty and replay checks](analysis.json)
- [Frozen plan](plan.json), [source freeze](freeze.json) and [reproduction](reproduce.md)
- [Execution and verification record](execution.json)
- [Original study and history ablation](../neural-continuation-2026-10-01/research-report.md)
