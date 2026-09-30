# Novelty defense under adversarial comparison

Audit date: 30 September 2026. This document supersedes any interpretation of
the original two-context example as evidence of superiority over temporal-loss
or decision-planning methods. It does not change the frozen private-data runner.

## Verdict and defensible wording

The broad claim does not survive: learning when to warn, temporal utility,
optimal intervention timing, and refractory-process equations all have prior
art. The stronger controls added here also match our method on the example that
previously separated it from pointwise classification.

The technically defensible statement is:

> We formulate repeated warning-policy training on exogenous, sparsely observed
> trajectories using exact expected emitted-alarm credit under a hard cooldown.
> Within an explicitly restricted policy family, we integrate out action coins
> and differentiate the deployed emission mechanism. We establish when additive
> timely credit equals unique event recall and evaluate every comparator on the
> same causal observation and action clocks.

This describes a concrete method and a testable distinction from the reviewed
implementations. It does **not** establish a first-ever algorithm, a new theorem
of general sequential decision theory, improved League performance, or a
publication-level advance. Combining known ingredients is insufficient unless
the resulting distinction produces a useful, demonstrated contribution.

## Closest prior work and the precise boundary

| Work inspected | What is already established | Remaining distinction and its limit |
|---|---|---|
| Damera Venkata and Bhattacharyya, NeurIPS 2022, *When to Intervene* [1] | Optimal intervention timing as an optimal-stopping problem, with hazard-based continuation values; ordinary static thresholds can be suboptimal. | Its stated objective scores the first trigger and trades residual time against missing the event. Our objective counts repeated emitted warnings under cooldown and a bounded useful lead window. This distinction does not imply that general control methods cannot solve our problem. |
| Legnaro, Guastavino and Marchetti, 2026, wSOL; pinned author implementation [2] | Temporally coupled, differentiable weighted confusion scores. Neighboring labels and probabilities affect the loss. | The inspected implementation does not propagate an emitted-alarm availability state, cooldown duration or physical-time exclusion matrix. Our objective explicitly contains those quantities. Nevertheless, all four tested wSOL variants solve our constructed example equally well. |
| Yèche et al., CHIL 2024, Dynamic Survival Analysis [3] | Learned event-time distributions and alarm policies including silencing and imminent-event prioritization. | Survival-likelihood training and subsequent alarm selection differ from differentiating repeated emitted-event credit. A strong survival model with a decision planner remains a necessary comparator. |
| Deger et al., 2010, refractory point processes [4] | Active/refractory population dynamics; their Eq. 7 partitions total mass into currently active and recently firing mass. | Our discrete availability recurrence has the same exclusion structure. The recurrence and its differentiation cannot be presented as newly invented mathematics. |
| Yèche et al., ICML 2023, TLS [5]; Rath and Hughes, AISTATS 2022 [6] | Temporal early-warning objectives and constrained alarm learning. | A useful target window, a false-alarm penalty or a dual variable alone is insufficient novelty. |
| Yang et al., *Predicting Events in MOBA Games* [7] | Event forecasting and attribution in MOBA. | League deployment and larger row counts do not establish methodological novelty. |

The OTI paper explicitly allows system reactivation as separate trials and says
its objective considers only the first trigger (Section 2). It also assumes
event occurrence is observable with certainty at each timestep. Our replay does
not reveal unobserved between-frame event status to the predictor. These are
protocol differences, not proof that OTI cannot be adapted.

For wSOL, we inspected the authors' source and README, plus the indexed primary
abstract. The full paper remained unavailable through the retrieval routes used.
This audit therefore establishes implementation-level loss differences, not an
exhaustive statement about every experiment or extension in the paper. Related
reinforcement-learning, alarm-management and differentiable-control literature
also prevents a global absence-of-prior-art claim from this targeted review.

## What can actually be proved

### Assumptions

Fix one recorded trajectory and ordered eligible action times \(s_1<\cdots<s_n\).
The predictor uses only observations available at each time. Conditional on
this trajectory, proposal coins are independent Bernoulli variables with
probabilities \(p_j\). An alarm emits only when no previously emitted alarm lies
in \((s_j-C,s_j)\). Exactly \(C\) seconds after an alarm is eligible again.

The recorded environment is unaffected by alarms. Proposal probabilities have
no additional dependence on sampled action history; availability is the only
such dependence. Future outcomes may supply supervised training rewards, but
are never prediction inputs. No event-time Markov assumption is required for
the following fixed-trajectory identity.

### Exact emitted-alarm marginals

Let \(B_{ji}=1\{0<s_j-s_i<C\}\). All earlier alarms in this interval are mutually
exclusive, because any two are closer than the cooldown. Thus availability and
emission probability are

\[
 a_j=1-\sum_i B_{ji}m_i,\qquad m_j=p_ja_j.
\]

Linearity of expectation gives exact expected additive utility
\(J=\sum_j r_jm_j\). Emitted alarms are dependent; the proof does not assume
their independence. This is a discrete refractory-process identity, with clear
antecedents in [4], not a priority claim.

### Explicit credit for blocking future opportunities

Differentiating \(m_j=p_j(1-\sum_i B_{ji}m_i)\) gives

\[
 (I+\operatorname{diag}(p)B)\,dm=\operatorname{diag}(a)\,dp.
\]

Define the reverse adjoint by

\[
 g_i=r_i-\sum_{j>i:\,s_j-s_i<C}p_jg_j.
\]

Then

\[
 \frac{\partial J}{\partial p_i}=a_ig_i,\qquad
 \frac{\partial J}{\partial z_i}=a_ig_ip_i(1-p_i),\quad p_i=\sigma(z_i).
\]

The future sum is the opportunity cost omitted by an independent utility loss.
It includes downstream interactions through the adjoint. Two prefix/suffix
scans compute these quantities in linear time after the time-bound lookups,
with linear auxiliary storage. The new NumPy reference demonstrates this; the
frozen GPU training runner still uses a dense triangular solve. No GPU speedup
has been measured or claimed. Reverse-mode differentiation itself is standard.

### When additive credit equals unique event credit

Each action is assigned only to its **next strictly future** event, and is timely
when lead is 20--60 seconds. With \(C=60\) seconds, two emitted alarms cannot
both be timely for the same event: both action times would have to fit inside
an interval only 40 seconds wide. Since each action has at most one assigned
event, \(\sum_j m_j y_j\) equals expected unique timely-event count.

The 60-second condition is sufficient, not necessary. For a closed lead interval
\([L,H]\), \(C>H-L\) suffices; endpoint conventions matter at equality.
Changing matching rules requires a new argument. Our explicit failure example
uses an event at 50 seconds, alarms at 0 and 30 seconds, and cooldown 30 seconds:
both alarms emit and are timely, so additive credit is 2 although unique event
count is 1. The implementation must not be generalized blindly to that case.

### Exact expectation is different from temporal weighting

In the inspected wSOL implementation, soft true positives sum \(y_jp_j\),
while false-positive and false-negative terms receive temporal adjustments.
There is no emitted-alarm recurrence. With two eligible proposals, \(y=(1,1)\),
\(p=(1,1)\), and one shared cooldown, the soft TP sum is 2 and emitted timely
credit is 1. These are different estimands. This is not a defect in wSOL: it was
not written to implement our deployment counter. Different estimands alone do
not prove different optimal decisions or better performance.

### What exact integration buys over sampled policy gradients

On a fixed trace, the exact gradient has no action-sampling variance. An
enumerated REINFORCE estimator with an exact mean-return baseline has the same
mean gradient but positive variance in the checked example. This is a standard
benefit of analytical marginalization, not a new general policy-gradient result.
Data, minibatch, parameter-initialization and optimization uncertainty remain.
Our restricted policy cannot express arbitrary action-history-dependent or
environment-changing interventions; general RL has broader scope.

## Stronger comparisons: the original superiority argument fails

All numbers below are a designed, finite population of 20 outcomes: equal
observable contexts C and D, actions at 0 and 30 seconds, cooldown 60 seconds.
In C an event occurs at 50 seconds with probability .6, otherwise at 80 seconds.
In D it occurs at 40 seconds with probability .6, otherwise no event occurs.
The mean non-timely-alarm budget is .25 per episode.

| Method | Timely-event recall | Non-timely alarms/episode | Interpretation |
|---|---:|---:|---|
| Oracle pointwise timely scores, original finite selection grid | 70.00% | .2400 | Restricted score-only decisions |
| Analytical optimum over the declared score-only family | 70.3125% | .2500 | A stronger bound than the finite-grid result |
| Independent utility, original optimizer and selection grid | 60.7654% | .244961 | Particular training result, not a universal upper bound |
| Exact cooldown credit | 100.00% | .2000 | Original mechanism illustration |
| wSOL prod/TSS | 100.00% | .2000 | Newly added temporal-loss control |
| wSOL prod/F1 | 100.00% | .2000 | Newly added temporal-loss control |
| wSOL max/TSS | 100.00% | .2000 | Newly added temporal-loss control |
| wSOL max/F1 | 100.00% | .2000 | Newly added temporal-loss control |
| Bayes decision planner | 100.00% | .2000 | Known conditional population, no realized future outcomes |

The planner compares the expected reward of acting now, waiting, and staying
silent; it waits in C and acts immediately in D. It knows the declared population
distribution, just as the oracle score control does. It is a decision-theory
sanity check, not a faithful implementation of the OTI paper.

The wSOL controls use the same two-context parameter table, per-match temporal
loss, 400 Adam steps at learning rate .1, float64, zero initialization, and the
same deployed cooldown and policy-selection families/grid. They adapt the
author loss to our timely-window labels. This is **not a reproduction of the
paper's benchmark** or a claim of tuned League performance. The four variants
provide a direct falsification of superiority on this particular toy.

### Why the score-only bound is narrow

Both contexts have first-slot timely probability \(\alpha=.6\), so a policy
using only the current timely score has a shared first-action probability \(r\).
Give it the most favorable second-stage decisions: always alarm in C if
available, never in D. Its timely hits and wrong alarms per episode are

\[
 h(r)=\tfrac12[1+(2\alpha-1)r],\qquad w(r)=(1-\alpha)r.
\]

With \(b=.25\), \(r\le b/(1-\alpha)=.625\). Dividing maximum hits .5625 by
event frequency .8 gives .703125 recall. The bound applies to this score-only
family, not to all classifiers, temporal losses, contextual policies, learned
value functions, survival distributions or planners. The result proves the
insufficiency of one scalar myopic score for this decision problem.

## Verification and provenance

Evidence is saved in
[`reports/policy-novelty-defense-2026-09-30.json`](../reports/policy-novelty-defense-2026-09-30.json).
The author reference is pinned to commit
`d929f0575833972c33826f1a41114fafb16ccb94`, with implementation Git blob
`4380ee110fcbe78722f0e162d4356b8eba4177a1` and configuration blob
`27aff3e70f9faf2ac3117c3ec9d56c721c8d83d6`. Author source was inspected locally;
it is not vendored here. Our independently expressed mathematical loss matched
the author's implementation on 16 configurations, including missing classes
and short sequences:

- Maximum absolute loss difference: `5.960464477539063e-08`.
- Maximum absolute gradient difference: `1.4901161193847656e-08`.
- Scope: uniform threshold, prod/max weighting, TSS/F1 scores. Cosine thresholds
  and other scores are not covered by this check.

The new tests compare the forward/reverse scan against the existing independent
dense solve/autograd and exhaustive policy enumeration, exercise cooldown
boundaries, check temporal-loss gradients and match separation, and verify
planner performance and the analytical score-only bound. The report checks a
no-conflict reduction and demonstrates the short-cooldown counting failure.

To regenerate without downloading author code:

```bash
PYTHONPATH=src:. python scripts/defend_policy_novelty.py
```

The optional `--reference-directory /path/to/pinned-author-checkout` enables
source-hash verification and parity testing. Without it, the report explicitly
marks parity as not run. Sequence boundaries must remain separate; the loss's
temporal weights are by slot index, not physical elapsed time. Irregular or
padded private sequences require a declared adaptation.

## Reviewer objections and decisions

| Objection | Answer supported now | What remains necessary |
|---|---|---|
| "This is optimal stopping under another name." | Timing decisions are established. Our repeated-count deployment objective differs from OTI's first-trigger objective. | Compare against a trained survival/continuation-value planner on the same observations and budget; no claim that planning is incapable of matching us. |
| "wSOL already solves your example." | Correct. All four tested variants tie exact credit. | Add wSOL to a separately frozen private-data comparison before making comparative claims. The original six-model run is incomplete for novelty assessment. |
| "Your mathematics is an old refractory model." | Correct for the marginal recurrence and standard differentiation. | Show a consequential algorithmic or empirical benefit of exact deployment credit; do not claim a new recurrence. |
| "You gave your model more action times." | The scheduled controls share the action grid; the observation-only ablation measures its effect. | Compare at identical clocks and vary observation cadence without adding future information. |
| "The gain is more tuning or a weak baseline." | The toy has matched selection for learned scores, but is constructed and tiny. | Strong action-age boosted trees, TLS/survival controls, wSOL and a planner; comparable selection budgets, multiple seeds and paired match-level inference. |
| "Exact gradients are already known." | Correct. Here their value is exact policy-specific credit without action draws. | Measure training variance, memory and runtime at equal compute; the present fixed-trace algebra is insufficient for a systems claim. |
| "This is a deployment-impact or causal claim." | It is an offline forecasting evaluation on exogenous traces. | A prospective study would be required to claim changed player behavior or match outcomes. |

The existing frozen v1 run can continue as exploratory evidence. It must not be
retrospectively described as containing these newly added private-data baselines.
Before opening the sealed final test, freeze the expanded comparison, event
matching, regional budget gate, model selection rules and minimum useful gain.
Repeatedly inspected calibration cannot provide independent confirmation.

A credible positive result would show a reproducible gain over the strongest
matched temporal-loss and planning controls under every regional alarm-budget
requirement, followed by confirmation on untouched data and preferably another
domain or event type. A tie, budget violation, disappearance after matching
action clocks, or failure under modest cadence changes should narrow or reject
the effectiveness claim. Even a positive result supports superiority only over
the tested methods and settings, never "better than any existing research."

## Primary sources

1. Damera Venkata and Bhattacharyya (2022), [When to Intervene: Learning Optimal Intervention Policies for Critical Events](https://proceedings.neurips.cc/paper_files/paper/2022/file/c26a8494fe31695db965ae8b7244b7c1-Paper-Conference.pdf), NeurIPS. Full paper inspected, especially Section 2 and Eqs. 1--9.
2. Legnaro, Guastavino and Marchetti (2026), [Weighted Score-Oriented Losses for Temporally Localized Event Prediction](https://arxiv.org/abs/2606.23145); [pinned author implementation](https://github.com/edoardolegnaro/ScoreOrientedLosses/blob/d929f0575833972c33826f1a41114fafb16ccb94/wsol/torch/wsol.py). Abstract and author source inspected; full paper unavailable.
3. Yèche et al. (2024), [Dynamic Survival Analysis for Early Event Prediction](https://arxiv.org/html/2403.12818v1), CHIL. Full HTML inspected, especially alarm policies in Section 3.3.
4. Deger et al. (2010), [Non-equilibrium dynamics of stochastic point processes with refractoriness](https://arxiv.org/pdf/1002.3798), Physical Review E 82, 021129. Full paper inspected, especially active-pool Eqs. 4 and 7.
5. Yèche et al. (2023), [Temporal Label Smoothing for Early Event Prediction](https://proceedings.mlr.press/v202/yeche23a.html), ICML.
6. Rath and Hughes (2022), [Optimizing Early Warning Classifiers to Control False Alarms via a Minimum Precision Constraint](https://proceedings.mlr.press/v151/rath22a.html), AISTATS.
7. Yang et al. (2020), [Predicting Events in MOBA Games: Prediction, Attribution, and Evaluation](https://arxiv.org/abs/2012.09424).
