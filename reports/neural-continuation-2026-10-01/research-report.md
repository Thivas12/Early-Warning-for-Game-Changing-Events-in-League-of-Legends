# League neural study and history followup

**The twelve-fit study and the three-fit follow-up completed successfully on the
RTX 4060 Laptop GPU.** Past observed state improves the hybrid's average useful
warning recall in a controlled retraining comparison, mainly for Baron. The
evidence does not establish a hybrid advantage over TCN, benefit for every event,
or task transfer. Regional warning-budget failures prevent either study from
passing its full development screen. No novelty or breakthrough is established.

## The registered architecture comparison

Mean timely event recall with 10–30 seconds of lead, across three fixed seeds:

| Family | Baron | Dragon | Teamfight | Macro |
|---|---:|---:|---:|---:|
| LeagueEWS | 20.878% | 13.176% | 3.082% | 12.379% |
| GRU | 12.085% | 8.977% | 2.204% | 7.755% |
| TCN | 20.734% | 13.532% | 2.834% | 12.367% |
| Snapshot | 18.636% | 11.743% | 2.590% | 10.990% |

The primary LeagueEWS-minus-GRU difference is **+4.623 percentage points
[+4.223, +5.064]**. Its three seed differences are +4.932, +3.379 and +5.559.
However, Americas Baron burden in seed 20261001 exceeds the limit of one
false-plus-late warning per match for both models: 1.0113 and 1.0120. The
registered gate therefore fails. LeagueEWS also spends 0.080 more false-plus-late
warnings per match per event on average than GRU.

LeagueEWS minus TCN is **+0.012 points [−0.156, +0.178]**, with mixed seed signs.
The hybrid's added components have not earned a recall advantage over TCN here.
GRU itself trails snapshot by 3.234 points. At the secondary 20–60-second endpoint,
LeagueEWS trails GRU by **0.843 points [0.307, 1.358]**, driven by Dragon. These
negative findings rule out a broad superiority claim.

## The focused followup

LeagueEWS exceeded snapshot by 1.389 points, but that comparison changes both
inputs and model capacity. After reviewing the complete study, I froze and ran
the protocol's history ablation: three new LeagueEWS fits with the same 1,751,647
parameters, initialization seeds, batches, loss weights and 12-epoch budget.
Past values and missingness were replaced with the current frame; ages, valid
lengths, padding and targets were retained. All fits finished before scoring.

| Event | Full history recall | Current-only recall | Difference in percentage points and paired 95% interval |
|---|---:|---:|---:|
| Baron | 20.878% | 18.441% | +2.438 [+1.818, +3.074] |
| Dragon | 13.176% | 13.346% | −0.171 [−0.392, +0.047] |
| Teamfight | 3.082% | 2.795% | +0.286 [+0.115, +0.453] |
| Macro | 12.379% | 11.527% | **+0.851 [+0.625, +1.074]** |

The macro differences are +1.064, +0.443 and +1.046 points across seeds.
Average false-plus-late burden decreases from 0.880 to 0.865 with full history,
although Baron burden increases. History improves Baron recall in both routes;
the teamfight gain is clearer in Europe than in the Americas.

Both variants have an Americas Baron budget failure, in different seeds. Dragon
does not show a positive mean effect. The frozen rule requiring consistent macro
gain, no event-level mean harm and all regional budgets therefore fails. At
20–60 seconds the macro difference is +0.219 points [−0.093, +0.504], with mixed
seed signs. The useful history effect is specific to the task and lead window.

## What explains the gain

**Additional history:** the matched-architecture ablation supports an incremental
macro benefit from past observed state at 10–30 seconds under this training
recipe. It does not remove historical information already encoded in current
summaries or retained timing, and it does not show that every event benefits.

**Architecture:** the original comparison gives no clear hybrid advantage over
TCN. Capacity, component effects and optimization are not individually isolated.
**Task sharing:** all studied encoders share supervision across events; no
matched independent-event encoders were trained. Positive task transfer remains
a hypothesis.

## Scope and reproducibility

All models reuse 24,000 League training matches. Evaluation uses 3,000 later
calibration matches after thresholds are selected on the earlier 3,000. The
2,000 paired whole-match bootstrap draws preserve regions and share sampled
matches across events and seeds. Intervals condition on fitted models and
policies; seeds are not independent match populations. The follow-up is adaptive,
secondary intervals are unadjusted, and patch 16.16 was already examined.
Baron and Dragon targets are completions, not engagement onset. **Patch 16.17
remained sealed.**

The original worker was preserved through exit code 0. The follow-up also exited
0; a failed detached launch was recovered from its intact canary checkpoint.
Thirty-two focused software checks passed. Frozen source, data and runtime
bindings, checkpoints and predictions are retained.

- [Original findings, seed variation and warning burden](original-findings.md)
- [All family, event, region and seed tables](tables.md)
- [Follow-up tables and regional failures](history-tables.md)
- [Original analysis JSON](neural-analysis.json) and [follow-up analysis JSON](history-analysis.json)
- [Frozen follow-up plan](history-ablation-plan.json)
- [Methods and original notebook review](methods.md)
- [Reproduction and resume commands](reproduce.md)
- [Execution record and artifact locations](execution-record.json)
