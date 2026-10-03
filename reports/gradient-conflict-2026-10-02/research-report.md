# PCGrad changes the tradeoff but does not repair LeagueEWS task sharing

**The focused follow-up fails its frozen practical screen.** PCGrad increases
average 10–30-second recall, but does not recover Baron, loses macro recall in
one seed, adds warning burden, and breaches a regional budget. At 20–60 seconds
it improves Baron while reducing Dragon and teamfight recall in every seed.
This is an informative negative mechanism result, not a breakthrough.

All three fits completed on 2 October 2026; analysis completed on 3 October.
The training plan was committed before fitting and the analysis before scoring.
Existing experiments and checkpoints are preserved. **Patch 16.17 remains sealed.**

## Primary warning results

Mean recall percentages across the three fixed seeds, with 10–30 seconds of
lead. Burden is false-plus-late warnings per match per event, averaged across
events and seeds; it is not a combined three-event attention budget.

| Model | Baron | Dragon | Teamfight | Macro | Burden |
|---|---:|---:|---:|---:|---:|
| PCGrad LeagueEWS | 20.724 | 14.102 | 3.410 | 12.745 | 0.911 |
| Ordinary joint LeagueEWS | 20.878 | 13.176 | 3.082 | 12.379 | 0.865 |
| Independent LeagueEWS | 21.506 | 11.257 | 3.038 | 11.934 | 0.840 |
| TCN | 20.734 | 13.532 | 2.834 | 12.367 | 0.864 |
| GRU | 12.085 | 8.977 | 2.204 | 7.755 | 0.785 |
| Snapshot | 18.636 | 11.743 | 2.590 | 10.990 | 0.845 |

PCGrad minus ordinary joint LeagueEWS, in percentage points. Intervals are
paired whole-match conditional 95% intervals; seed order is 20260930, 20261001,
20261002.

| Event | Mean difference [interval] | Differences by seed |
|---|---:|---|
| Baron, focused diagnostic endpoint | −0.154 [−0.460, +0.168] | −0.401, −0.710, +0.648 |
| Dragon | +0.927 [+0.761, +1.089] | −0.026, +2.454, +0.353 |
| Teamfight | +0.328 [+0.258, +0.402] | −0.197, +0.541, +0.642 |
| Macro | +0.367 [+0.249, +0.490] | −0.208, +0.762, +0.548 |

The mean macro interval is positive, but seed consistency fails. PCGrad macro
recall ranges from 12.565% to 12.968%, sample SD 0.204 points. Its mean gain costs
**0.0459** extra false-plus-late warnings per match per event: 0.0361 false and
0.0097 late. Teamfight gains cost 0.1022 extra warnings per match; Dragon gains
cost 0.0568. These are comparisons under the same selection procedure, not
equal realized burdens or demonstrated alarm-efficiency gains.

PCGrad exceeds TCN in macro recall by **0.379 points [0.218, 0.542]**, positive
in every seed, with 0.0470 additional burden. It exceeds independent encoders
by **0.812 [0.616, 1.021]**, also positive in every seed, with 0.0708 additional
burden. Nevertheless, Baron is worse than independent training by **0.782
points [0.225, 1.321]**, negative in every seed. Those positive macro comparisons
do not rescue the failed Baron-recovery and no-mean-task-harm rules.

## Regions and longer lead times

PCGrad breaches the primary **Europe Dragon** limit in seed 20261001:
**1.014** false-plus-late warnings per match against a maximum of one. It meets
the primary limits elsewhere. Original control failures remain recorded:
Americas Baron for joint LeagueEWS and GRU in seed 20261001, independent and
snapshot in seed 20260930, and TCN in every seed. A failing control does not
excuse a candidate failure.

Mean primary macro differences versus joint are +0.402 points [0.231, 0.578]
in Europe and +0.332 [0.167, 0.506] in the Americas. Dragon and teamfight mean
gains occur in both regions. Baron changes are +0.021 [−0.402, +0.478] in Europe
and −0.327 [−0.751, +0.099] in the Americas; neither interval supports recovery.

At **20–60 seconds**, PCGrad minus joint changes are:

| Event | Recall difference [interval], points | Burden difference per match |
|---|---:|---:|
| Baron | +1.738 [+1.296, +2.194] | +0.0708 |
| Dragon | −0.827 [−0.993, −0.673] | −0.0353 |
| Teamfight | −0.783 [−0.886, −0.685] | −0.1560 |
| Macro | +0.043 [−0.121, +0.207] | −0.0402 |

Each event's sign agrees across all three seeds at this endpoint. The mean
Baron gain and Dragon/teamfight losses also occur in both regions. There is
no clear macro advantage. PCGrad fails the secondary Americas Baron budget
in seed 20261001 at **1.0027**. The effect depends on the warning interval;
it is not uniform protection against negative transfer.

## What this establishes

The original notebook attributed gains to temporal buildup and shared learning.
The matched history ablation found a **0.851-point** macro benefit from
additional past states, mainly for Baron, with failed development gates.
Joint supervision added **0.445 points** on average while hurting Baron.
These are separate interventions, not an additive explanation of the GRU gap.
Ordinary LeagueEWS still has no clear macro advantage over TCN. The registered original
LeagueEWS–GRU primary remains **+4.623 points [4.223, 5.064]**, with its regional
budget gate failed. The new diagnostic does not replace that comparison.

Training-only gradients and early-calibration diagnostics motivated this
[separately frozen PCGrad test](plan.json). The intervention keeps architecture,
inputs, weights, batches, optimizer and policy fixed, changing shared-gradient
aggregation. It establishes that this optimization intervention changes the
event/lead-time tradeoff at the fixed training budget. It does **not** establish
gradient conflict as the cause of Baron harm: PCGrad changes gradient magnitude
as well as direction, and calibration and warning timing still matter. Its
failure does not reject all conflict-mitigation methods. PCGrad is an
[established method](literature.md), not a new algorithm introduced here.

The next unresolved question is whether the mean gains survive a comparison of
warning efficiency across prespecified early-calibration operating budgets.
A future study must apply the same policy comparison to every strong control
and retain all events and seeds. Selecting the best head, seed or lead interval
from these results would compound adaptive selection. No additional method or
confirmatory evaluation has been selected by this report.

## Reproduction and uncertainty

The run completed **1,728 training-shard updates**, equivalent to **100,116
minibatch optimizer steps**, and exited 0. Recorded shard processing took
4,157.7 seconds, including input reconstruction and training, excluding
checkpoint writes and scoring. PCGrad uses the same 1,751,647 active parameters
as joint LeagueEWS, with three task backward passes per batch. Examples, update
budget and capacity match; wall-clock compute does not. Independent encoders
use three encoders per seed.

All 18 new policies passed independent chronological replay across the 6,000
calibration matches. Threshold selection uses the earlier 3,000; evaluation
uses the later **3,000 distinct matches**. All score files postdate the last
training checkpoint, and frozen source hashes still match. The 2,000 paired
bootstrap draws preserve regions and share matches across models, events and
seeds. Intervals condition on fixed fits and selected policies; rows and repeated
seeds are not independent matches. This repeatedly inspected development patch
and unadjusted intervals cannot confirm a discovery or future-patch generalization.
Baron and Dragon labels identify completions, not engagement onset.

- [Complete tables](tables.md), [all seed results](by-seed.csv), [paired analysis](analysis.json)
- [Selection diagnostics](diagnostic-interpretation.md), [frozen plan](plan.json), [freeze](freeze.json)
- [Reproduction](reproduce.md), [execution evidence](execution.json), [test log](test-results.log)

Validation: 585 tests passed, one optional skip, 85.89% coverage; lint, formatting
and type checks passed. These software checks are not empirical League findings.
Private match arrays, predictions and model binaries are excluded from the PR.
