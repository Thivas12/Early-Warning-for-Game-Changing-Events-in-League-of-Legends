# RiftHazard: research findings and revised method decision

Date: 29 September 2026. Review of repository tree
`59c1fcf92187e5b9963f155196842f21a6697215` (remote commit `e555152`).

## Executive finding

The project has a useful empirical puzzle: the graph model improves aggregate
ranking substantially while worsening Dragon warnings. The current evidence
does not show that a larger architecture or censoring correction will solve it.
The most justified next method is an event-specific model that receives the
same objective history as the strongest tabular baseline, with controlled tests
of what player geometry and relations add. Its primary evaluation must measure
useful warnings at a fixed false-alert budget.

This review found two concrete conceptual problems in the previous M3 proposal:
completed match termination was being treated as unknown follow-up, and a
binary partial-bin mask was described too strongly as a proper likelihood for
the desired continuous-time probability. The diagnostic remains useful for
measuring boundary coverage; its counts do not establish corrupted negatives.

The evidence below includes existing private-run results transcribed in public
reports, new calculations from those values, and newly executed controlled
examples. **No new model was trained on private League data in this review.**
The numerical counterexamples are explicitly synthetic. They prove properties
of a method or implementation, not an effect size on the League cohort.

## 1. What the completed experiments actually show

The recorded cohort has 24,000 training matches from patches 16.12–16.15,
6,000 calibration matches from 16.16, and 6,000 reserved test matches from
16.17. All performance below is calibration performance. Neural results are
ten-seed means; B3 is the recorded tabular reference.

| Model | Macro average precision, 12 targets | Difference from B3 |
|---|---:|---:|
| Prevalence B0 | 0.06531 | −0.31063 |
| Clock B1 | 0.11133 | −0.26461 |
| Event history B2 | 0.23985 | −0.13609 |
| Tabular B3 | 0.37594 | Reference |
| Temporal GRU B4 | 0.32382 | −0.05212 |
| Graph hazard M1 | 0.49112 | +0.11518 |
| M1 without objective nodes | 0.51086 | +0.13491 |
| M1 without interaction edges | 0.46634 | +0.09040 |
| M1 without assistance history | 0.46346 | +0.08751 |
| M1 without positions and proximity | 0.13914 | −0.23680 |

M1 improves macro AP by **30.64% relative to B3**. However,
`(0.466337 − 0.375942) / (0.491119 − 0.375942) = 78.48%` of that numerical
gap persists without interaction edges. This is descriptive arithmetic across
separately fitted variants. It does not mean edges causally explain exactly
21.52% of performance. It does mean a strong model based on a set of players,
spatial information, and history is essential before crediting interactions.

Removing positions and proximity together costs 0.35198 AP. That intervention
removes multiple channels simultaneously. Removing objective nodes adds
0.01974 AP but changes graph size, relations, and mean-pooling scale. Neither
intervention identifies a clean mechanism by itself.

### Warnings have a different result from aggregate ranking

| Event | B3 F1 | M1 F1 | B3 recall | M1 recall | B3 false alerts/game | M1 false alerts/game |
|---|---:|---:|---:|---:|---:|---:|
| Baron | 0.47758 | 0.49852 | 0.68667 | 0.51085 | 1.28767 | 0.58347 |
| Dragon | 0.71183 | 0.58807 | 0.77891 | 0.63018 | 1.55200 | 1.94413 |
| Combat episode proxy | 0.42568 | 0.44203 | 0.75086 | 0.67829 | 11.85267 | 9.27712 |

For Dragon, M1 loses **12.38 percentage points of F1**, loses **14.87 points
of recall**, and produces **25.27% more false alerts**. Baron and combat proxy
F1 improve modestly, with lower recall. These are calibration-selected
operating points, so they are not unbiased deployment estimates.

The later-half sensitivity analysis is consistent with the Dragon problem:
M1 mean F1 0.58935 and 1.96563 false alerts/game. That analysis was designed
after viewing aggregate calibration outcomes. It is supporting sensitivity
evidence, not an independent confirmation sample.

The registered H5 requirement is unmet at the reported full-calibration
operating points. This does **not** prove that no threshold could satisfy the
budget: the current selector maximizes F1, whereas a budget-constrained
selector answers a different question.

Sources: `rifthazard-calibration-2026-09-26.md` and
`m1-graph-ablation-calibration-2026-09-28.json` in this directory. The latter's
SHA-256 is recorded in the companion findings JSON. The sources themselves
state that the values are transcriptions of private summaries. Publication
tables require reconciliation with those original summaries. Aggregates alone
cannot yield fresh paired confidence intervals, calibration curves, or model
ensembles.

## 2. New implementation findings

### 2.1 M1 and B3 do not receive equivalent objective history

`tabular_baseline.py` gives B3 game clock, objective counts, and time since the
last Dragon and Baron. `graph.py` gives M1 fixed pit locations and an initial
spawn-elapsed flag. Its only event-derived edge is champion-kill assistance;
`ELITE_MONSTER_KILL` does not update graph features or edges. `m1_backend.py`
adds relative frame ages, but no explicit objective recurrence state.

I executed a paired synthetic input at game time 600 seconds. Adding a known
Dragon kill at 540 seconds, while holding participant states fixed, left all
M1 graph node features and relations identical. B3's `dragons_blue` changed
from 0 to 1 and `minutes_since_dragon` from missing to 1.0.

**Established:** the explicit recurrence signal is absent from the M1 graph
construction. **Hypothesis:** this helps explain why B3 gives better Dragon
warnings. That performance explanation requires a matched refit; indirect
correlations in gold, positions, or past states may still carry information.
M2's current 24 spatial features also contain initial spawn flags, not exact
last-objective timers, so its existing fusion experiment does not directly
resolve this omission.

### 2.2 The cooldown has an exact-minute boundary

`alert_policy.evaluate_alerts` skips an alert when
`time - last_alert <= 60000`. Consecutive frames exactly 60 seconds apart
therefore cannot both alert. With continuously high scores on exact minute
frames, the earliest next alert is often two minutes later.

In a synthetic three-event example with perfect 30-second advance scores,
the current convention catches 2/3 events. Allowing an alert at *at least*
60 seconds catches 3/3 with zero false alerts in that example. This establishes
sensitivity to the boundary convention, not a measured performance gain. The
existing rule is reproducible and documented as suppression through 60 seconds;
do not silently change it in the frozen analysis. Predeclare both conventions
for a sensitivity replay and select one for the follow-on experiment.

### 2.3 The combat label is a temporal multi-kill proxy

`labels._combat_episode_starts` chains adjacent kills no more than ten seconds
apart. It does not check spatial coherence, participant overlap, team balance,
or total episode duration. I executed an example with eleven kills, alternating
between distant positions, over 90 seconds. It produces one qualifying episode.

The code follows the recorded proxy definition. The issue is construct
validity: this outcome cannot automatically be described as a single tactical
teamfight. Retain the original outcome for the registered comparison. Treat
spatially coherent fights as a separate, explicitly defined endpoint, with
human agreement measured on a stratified sample before using it as a paper's
central claim. Episode onset may be labeled retrospectively, but retrospective
qualification must never become an input at that onset.

### 2.4 Observation cadence sets the short-horizon opportunity

| Event | Events with frame within 10s / within 60s | Ratio | 20s ratio | 30s ratio |
|---|---:|---:|---:|---:|
| Baron | 1,080 / 6,494 | 16.63% | 33.09% | 50.23% |
| Dragon | 3,772 / 22,713 | 16.61% | 33.03% | 49.86% |
| Combat proxy | 6,508 / 39,998 | 16.27% | 33.75% | 50.20% |

These ratios use the recorded **60-second-eligible events** as denominator,
not necessarily every event. At native frame times, a 10-second event-warning
policy can only match events with a genuine frame in its 10-second window.
This limits attainable all-event recall independently of network capacity.
It does not prevent emitting a longer-horizon warning at an earlier frame.
Opportunity must be reported for the chosen warning window and minimum lead.

## 3. Correction to the previous M3 censoring argument

### 3.1 Define the probability being predicted

For event type `e`, the useful completed-match target is:

`Y_e(t,h) = 1` if an event of type `e` occurs after `t`, by `t+h`, before the
match terminates; otherwise `Y_e(t,h) = 0`.

If the complete match ends 20 seconds after prediction with no event, the
30- and 60-second actual-match outcomes can both be known negatives. A source
record ending while the game continues is a different situation. Duration
and final-frame disagreement alone cannot determine event ascertainment.

The previous M3 mask marks those two horizons unknown in an executed complete
match fixture (prediction 180s; termination 200s). Its count of negative rows
past a frame/duration boundary therefore mixes legitimate terminal negatives
with potentially incomplete ascertainment. **The current evidence does not
establish that M1's terminal all-zero targets are wrong.** Direct finite-horizon
prediction from completely observed matches can already learn the desired
actual-match probability without a separate survival model.

If a cause-specific hazard model is chosen, match termination is a competing
terminal event for each event type. Converting an event-only hazard to risk
while censoring termination targets a different quantity. Competing-risk
theory makes this rate/risk distinction explicit [6]. For constant event
rate 0.01/s and terminal rate 0.02/s, the actual 60-second event incidence is
27.82%; ignoring the terminal competitor gives 45.12%. These rates are a
constructed illustration, not fitted League rates.

### 3.2 Binary partial-bin masks introduce a discretization assumption

The mask includes an observed positive from a partly observed bin but omits a
negative from that same partial bin. This is a recognized style of discrete-time
approximation [7], not an exact likelihood for continuous event timestamps.
Calling it automatically a proper score for the desired continuous-time risk
was too strong.

I ran 200,000 synthetic exponential event times with true 10-second risk 10%.
Independent censoring was equally split between 5 and 10 seconds. Fitting an
intercept to the included binary outcomes gives:

| Quantity | 10-second event probability |
|---|---:|
| True generating risk | 10.000% |
| Analytic optimum of binary inclusion rule | 14.393% |
| Synthetic observed binary optimum | 14.377% |
| Constant-rate likelihood using exact exposed time | 9.993% |

This is a counterexample to assuming the mask is an exact continuous-time
correction. It does not estimate the bias in the League dataset. If genuine
truncation is material, use exact elapsed exposure in a piecewise exponential
likelihood, or quantify discretization sensitivity before selecting bins.

## 4. What prior research already covers

Targeted primary-source review, checked 29 September 2026. This is a focused
review of the closest task and method families, not an exhaustive systematic
review or proof of firstness. Publisher text/abstract availability varies.

| Primary work | Verified relevance | Implication for this project |
|---|---|---|
| Yang et al., *Predicting Events in MOBA Games* [1] | Honor of Kings event prediction using dense, per-second game features, sequence models and attribution. | MOBA event forecasting and Transformer attribution already exist. Different targets/cadence prevent a numerical leaderboard comparison. |
| Vardakis et al., *Prediction of MOBA game events based on In-Game Data* (2026) [2] | League professional-match death prediction; Temporal Fusion Transformer; 10s history, 5s horizon, reported F1 about 0.599. Publisher abstract/highlights inspected. | Direct League event forecasting already exists. Compare task definitions and available inputs; its F1 is not a baseline score for Dragon on solo queue. |
| Caldeira et al. (2025) [3] | Cooperative interaction graph measures in League. | Graph structure in League is established prior art, not a sufficient novelty claim. |
| Chitayat et al. (AIIDE 2023) [4] | Game design parameters for patch-agnostic Dota analytics. | Rule-aware representations and patch robustness have precedents. Test actual cross-patch stability. |
| Oskarsson et al., TGNN4I (AISTATS 2023) [5] | Irregular, partially observed graph forecasting with continuous latent dynamics. | Observation-aware temporal graphs are an established comparator. A new gate alone is modest novelty. |
| Andersen et al. (2012) [6] | Cause-specific rates and cumulative incidence under competing events. | Define termination and the target probability before adding a survival loss. |
| Kvamme and Borgan, PC-Hazard (2021) [7] | Discrete versus continuous survival; explicit discretization and piecewise constant rates. | Exact event time and exposure can be used with a small model; a complex neural point process is not required merely to handle partial bins. |
| Yèche et al., TLS (ICML 2023) [8] | Temporal training objectives for early warning, evaluated at low false-alarm rates. | Include a temporal-label objective as a controlled comparator only if warning utility remains weak; check calibration on original binary targets. |
| Yu et al., DyGFormer/DyGLib (NeurIPS 2023) [9] | Dynamic graph benchmarks with common implementations and evaluation. | Reproducible input and protocol parity matters. Its link-prediction scores are not a direct comparator for graph-level event warning. |

No searched source establishes that combining a graph, a GRU, a hazard head,
missingness flags and a gate is a new general method. The defensible opening is
**what relational information adds to objective recurrence and geometry under
sparse observation, and whether that benefit survives an alert budget and
temporal shift**. That claim needs a positive controlled result or a carefully
reported negative answer.

## 5. Concrete method decision

### Primary experiment: add explicit recurrence before changing the loss

Use Dragon within 60 seconds as the primary follow-on task because it has a
strong existing B3 comparator and a clear M1 failure. Baron is secondary;
the combat proxy remains a distinct endpoint. Finish the original registered
M1 analysis separately under its frozen targets, controls and selection rule.

For every new contender, provide identical causal global information: current
game time; observed objective counts; time since last objective; and any
patch-specific availability state that can be validated from recorded rules
and past events. Missing state has its own indicator. No future match end,
future frame time, future label, or completed episode qualification enters X.

The relational candidate uses participant geometry and history, then an
event-specific readout combining player context with the global recurrence
features. A residual form is easy to inspect:

`logit h[e,b] = f[e,b](clock, objective history, rule state) + g[e,b](players, relations, observed ages)`.

Here `b` indexes a future time bin. Compare to direct 60-second probability
heads on the same complete-match target. If a termination-aware survival
formulation is used, predict and integrate the terminal hazard as well;
separate per-event versus terminal models need not claim a jointly coherent
four-way event process. Strategic event types are not mutually exclusive over
the minute. The residual equation is a proposed design, not an originality or
performance claim.

| Contender | Purpose |
|---|---|
| Recorded B3 and M1 | Preserve the historical comparison. |
| B3 with objective history plus participant/pit geometry | Strong cheap model with comparable information. |
| Participant set encoder + GRU + the same global history, no relation messages | Isolate the value of relations from spatial input access. |
| M1 encoder + the same global history | Test the confirmed missing-signal hypothesis directly. |
| Event-specific relational readout + global history | Test whether objective-focused aggregation improves on shared mean pooling. |

Use the same train/development match splits, feature availability, seed list,
selection budget and operating-policy search. Record parameter counts and
training/inference costs. Equal epochs alone do not equalize optimization
between boosting and neural methods. Select architecture and training length
on an inner temporal development split; use calibration only for the frozen
probability/policy procedure. Report all assigned seeds without choosing one.

Run loss comparisons only after input parity: unweighted proper binary loss,
the existing hazard formulation, and a justified exact-exposure method if
there is real incomplete ascertainment. Focal or weighted loss changes the
probability interpretation and requires recalibration. Avoid a Cartesian
product of encoders, loss weights and gates without a specific hypothesis.

### Policy and statistical decision

For the new protocol, choose thresholds to maximize Dragon recall subject to
at most one false alert per match on the threshold-tuning partition. Report
the realized budget on a disjoint evaluation partition; a calibration budget
is not a guarantee under drift. Show the full recall-versus-false-alert curve,
and predeclare what happens when no threshold meets the recall/precision gate.
Use the same cooldown convention and one-to-one matching for every contender.

Report all-event recall, opportunity-conditional recall, precision, false
alerts/game and/hour, per-match false-alert p50/p90/p95, median and p10 lead,
AP and Brier/calibration by event/horizon, route and match phase. A new model
must improve warning performance at matched burden; an AP-only gain does not
answer the follow-on question. Paired uncertainty resamples whole matches,
with route strata; repeated-player dependence needs the recorded player-group
sensitivity when mappings are available. Ten seeds are repeated fits, not ten
independent clinical-style trials or ten independent samples of a patch.

Prespecify the primary contrast, seed aggregation, multiple-comparison treatment,
and minimum useful effect. Estimate precision/power from match-level
development predictions rather than inventing a sample-size justification from
the rounded aggregate table.

### Reuse the sealed test responsibly

Developing a new model using training/calibration data does not, by itself,
invalidate a test that has genuinely never been inspected. The earlier blanket
requirement for a completely new cohort was stronger than necessary. If the
16.17 test remains sealed, a documented amendment can freeze additional
comparisons before one joint release, with original and added claims clearly
identified and multiplicity handled. The original registered claim retains
its original analysis. A later untouched cohort becomes necessary if the test
has been used for adaptation, and is valuable for claims across multiple patch
transitions. One held-out patch does not establish broad patch robustness.

## 6. Paper scope and decision

Proposed research question: **Do temporal player relations improve useful
strategic-event warnings beyond recurrence clocks and observed geometry when
telemetry is sparse?** A suitable working title is *Strategic Event Warnings
from Sparse League of Legends Telemetry: Recurrence, Geometry and Relations*.
This title does not assume the result.

The current evidence can support a calibration-stage benchmark and method
diagnosis. A stronger paper needs the matched-information comparisons, a final
unseen evaluation, validated endpoint meaning, and result tables tied to
original score artifacts. No acceptance or breakthrough result can be
guaranteed from the existing aggregates.

Scope the current task as retrospective forecasting from observer-style
Match-V5 data. Chronological availability within a recorded timeline does not
establish access to the same fields in a live player application. Riot
documents a separate Live Client Data API [10]; field and visibility parity
must be demonstrated before product claims. That distinction affects what
the paper can claim, even when its offline evaluation is correct.

**Decision now:** prioritize the missing objective-history/input-parity
experiment and budget-aligned policy. Treat terminal coverage as provenance
analysis until complete termination and actual truncation are distinguished.
The current code and aggregate results do not justify calling censoring the
main failure mode or spending on a broad new architecture sweep.

## Reproduction and evidence files

- `scripts/research_findings_20260929.py`: executable secondary calculations,
  input-equivalence probe, terminal-label probe, 200,000-row synthetic
  discretization experiment, cooldown example and combat-label example.
- `reports/research-findings-2026-09-29.json`: generated results; each synthetic
  section is marked and real-data input provenance is recorded.
- Existing source reports are named in Section 1. This review did not open
  private match files or compute a new private-data model score.

## Primary references and search record

1. Yang et al., [Predicting Events in MOBA Games: Prediction, Attribution, and Evaluation](https://arxiv.org/abs/2012.09424).
2. Vardakis et al., [Prediction of MOBA game events based on In-Game Data](https://doi.org/10.1016/j.entcom.2026.101091), Entertainment Computing 57 (2026).
3. Caldeira et al., [Collective Intelligence Outperforms Individual Talent](https://arxiv.org/abs/2506.02706).
4. Chitayat et al., [Beyond the Meta](https://arxiv.org/abs/2305.18477), AIIDE 2023.
5. Oskarsson et al., [Temporal Graph Neural Networks for Irregular Data](https://proceedings.mlr.press/v206/oskarsson23a.html), AISTATS 2023.
6. Andersen et al., [Competing risks in epidemiology: possibilities and pitfalls](https://doi.org/10.1093/ije/dyr213), International Journal of Epidemiology 41 (2012).
7. Kvamme and Borgan, [Continuous and discrete-time survival prediction with neural networks](https://doi.org/10.1007/s10985-021-09532-6), Lifetime Data Analysis 27 (2021).
8. Yèche et al., [Temporal Label Smoothing for Early Event Prediction](https://proceedings.mlr.press/v202/yeche23a.html), ICML 2023.
9. Yu et al., [Towards Better Dynamic Graph Learning](https://proceedings.neurips.cc/paper_files/paper/2023/hash/d611019afba70d547bd595e8a4158f55-Abstract.html), NeurIPS 2023.
10. Riot Games, [League developer documentation, Live Client Data API](https://developer.riotgames.com/docs/lol).

Queries included League/MOBA event forecasting with Dragon/teamfight,
the exact title of the 2026 League paper, temporal label smoothing and false
alarms, irregular graph forecasting, dynamic graph benchmark parity,
competing terminal risks, and discrete/continuous survival discretization.
Primary publisher, conference, author-preprint and official documentation pages
were used. No comprehensive Scopus/Web of Science citation crawl was performed.
