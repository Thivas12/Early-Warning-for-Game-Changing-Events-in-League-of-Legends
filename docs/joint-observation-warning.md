# Joint observation and warning control: implemented research candidate

30 September 2026. This is an isolated experimental branch, not an extension of
the frozen private-data training protocol. It does not establish a breakthrough.

## Scientific target

Learn which observations to acquire and when to emit repeated useful warnings,
while accounting for acquisition cost and the future warnings suppressed by an
alarm cooldown. The central computational target is exact training from complete
exogenous recorded panels without sampling acquisition/alarm paths or fitting a
generative transition model.

That last condition is narrower than general active sensing: every reading the
policy might buy must exist in the training panel, and neither buying a reading
nor issuing an alarm may change the environment. Missing readings cannot be
manufactured or treated as available. Sparse League timelines could support
experiments that withhold existing frames; they cannot establish the benefit of
buying observations between frames that were never collected.

## Model and information contract

The prototype is a finite controller with two shared trainable parameter tables.
Its retained state is the latest acquired sensor value, its age, the event-clock
phase, and remaining alarm cooldown. The acquisition table chooses whether to
read the current sensor. Only after that decision can the warning table use the
new value. A reading can be acquired during alarm cooldown for future decisions.

The tables are shared across trajectories, never indexed by trajectory identity,
future outcome or hidden state. They do not retain arbitrary observation history;
that restriction makes exact merging possible and can reduce attainable value.
The independently computed Bayesian reference retains the full posterior and
knows the generating laws, so its population value is an upper reference rather
than an equally informed learned baseline.

## Exact joint-state recursion

Condition on one complete recorded panel. Before step t, let d_t(i,c) be the
probability that the latest purchased reading has index i and the cooldown has
c steps remaining. A sentinel index denotes no reading. Let q_t(i,c) be the
acquisition probability computed using that retained information.

The post-acquisition mass is

\[
 v_t(i,c)=d_t(i,c)(1-q_t(i,c)),\qquad
 v_t(t,c)=\sum_i d_t(i,c)q_t(i,c).
\]

The newly acquired index t is distinct from all old indices. If p_t(i) is the
warning probability after acquisition, emitted mass is

\[
 e_t(i)=v_t(i,0)p_t(i).
\]

Emitted mass moves to cooldown C-1 at the next tick. Unemitted available mass
stays available, and blocked mass decrements its cooldown. Read counts sum the
acquired mass, while timely and wrong counts weight emitted mass by the actual
future event label. In the study, candidate event opportunities are three ticks
apart, warning lead is 1--3 ticks, and cooldown is three ticks; no event can
receive two timely emitted alarms.

**Proof of exactness:** start with unit mass at the initial sentinel/available
state. Acquisition partitions each state into disjoint read/no-read paths. Paths
with identical retained information and cooldown have identical future policy
probabilities and can be merged. Warning partitions available mass into emitted
and silent paths. Induction therefore reproduces the complete action tree.
Differentiating this finite sum yields its exact policy gradient. Averaging over
independent exogenous panels estimates the corresponding population objective;
action integration does not eliminate uncertainty from the panels themselves.

Runtime is O(B T² C) for B panels, T ticks and C cooldown states, with O(B T C)
rolling state storage. Autograd retains additional intermediate tensors. The
training demonstration uses nine ticks and is not evidence of long-match GPU
scaling. Finite-state dynamic programming and analytical marginalization are
established techniques; this derivation is not claimed as a newly invented
general control theorem.

### Why two separate marginal recurrences are insufficient

Observation history and cooldown become correlated. For example, read with
probability one half and warn exactly when the read occurs. At the next tick,
fresh information always coincides with a blocked alarm. Replacing the joint
law by independent marginals creates a spurious probability one quarter of
having both fresh information and an available alarm. A policy that warns only
in that state then receives fictitious credit. The implementation retains the
joint law throughout.

## Prior work that limits the novelty claim

| Primary work | Overlap that must be credited | What this prototype actually changes |
|---|---|---|
| Meuleau et al., UAI 1999, [finite policy search](https://arxiv.org/pdf/1301.6720) and [finite-state controller learning](https://arxiv.org/abs/1301.6721) | Finite policy graphs, exact and sampled policy gradients, complexity reductions through restrictions. | A latest-observation/cooldown state construction evaluated directly on complete exogenous panels. This is a specialization, not invention of finite-state policy gradients. |
| Qin, van der Schaar and Lee, NeurIPS 2023, [Risk-Averse Active Sensing](https://proceedings.neurips.cc/paper_files/paper/2023/file/1498a03a04f9bcd3a7d44058fc5dc639-Paper-Conference.pdf) | Learning acquisition timing and feature selection for timely prediction under cost pressure; tail-risk treatment. | Repeated emitted-warning credit is integrated with acquisition paths. We have not reproduced their full system and cannot claim to outperform it. |
| von Kleist et al., JMLR 2025, [AFA evaluation for time-varying features](https://jmlr.org/papers/v26/23-1635.html) | Causal assumptions for evaluating acquisition policies from retrospective data, including no direct effect and semi-offline evaluation. | The current complete-panel/no-environment-effect assumption avoids missing counterfactual readings by restriction. It is not a new identification result. |
| Rezvan et al., September 2026, [AFA with incomplete training data](https://arxiv.org/abs/2609.32325) | Missing training features can damage multi-step acquisition value; restoration and filtering have limitations. | We disallow unrecorded acquisitions. This prototype does not solve incomplete-panel acquisition. |

The first three sources' relevant formulations were inspected; the latest AFA
paper's abstract and HTML were retrieved. This is a targeted review, not proof
of global originality. The broad claim "jointly learn what to observe and when
to warn" is not a defensible first-ever claim based on this search.

## Executed study

The [complete JSON](../reports/joint-observation-warning-2026-09-30.json) records
27 fits: nine methods, three initialization seeds, 200 optimizer steps each,
2,048 independent training trajectories, and 8,192 independent evaluation
trajectories in each of four designed worlds. Evaluation action counts are exact
expectations for every trained method. No private League data was used.

Methods include joint exact training, score-function training of the same
controller using eight action draws per minibatch, no observation, every-tick
observation, and all phases of periodic two-/three-tick observation. Every fixed
observation policy has its warning head trained through the same exact alarm
mechanism. An exactly silent policy supplies a zero-cost, zero-utility control.
The Bayesian reference solves the known-world finite-horizon belief recursion
without quantizing beliefs to a grid. Floating-point arithmetic remains.

The primary objective is timely warnings minus wrong warnings minus .05 times
the number of observations. These are common Lagrangian prices, **not equal
hard-budget operating points**. Recall must not be compared without showing the
different wrong-alarm and observation counts. The complete cost/constraint
frontier has not been estimated.

All methods receive the same training-only smoothed probability initialization.
Training time is measured; update counts do not imply equal computation.
Evaluation cases cover matched conditions, weaker sensors, a higher event rate,
and sensors carrying no information. No adaptation is performed on these cases.
Paired bootstrap intervals resample trajectories after averaging fitted seeds;
they are conditional on the fitted models and omit training-set uncertainty.

The world and cost were chosen for a nontrivial information-purchasing problem,
not sampled from a registered application distribution. Periodic phase controls
were expanded after the initial diagnostic to avoid an unfairly timed comparator.
This is exploratory simulation research, not confirmatory evidence.

## What would justify continuing this candidate

A broad priority claim already overlaps established work. Advancing a more
specific computational contribution requires a meaningful advantage over strong
same-information controllers at matched compute and costs, and a benefit at
realistic sequence lengths. Current short simulations cannot establish either
general superiority or a League contribution. Sensor degradation is an explicit
failure case, not an omitted inconvenient result.

Before any real-data use: define which recorded feature groups can actually be
withheld; recompute features solely from purchased history; forbid buying absent
frames; compare against phase-tuned schedules and adaptive sensing methods;
evaluate the false-warning/acquisition frontier on untouched trajectories. A
model that silently uses rolling features computed from withheld frames is
invalid. A model trained on hindsight observer data does not establish live
player-view performance.

This branch is a reproducible candidate investigation. It is not promoted to
the main research claim and does not justify describing the project as
groundbreaking.

## Reproduce

```bash
PYTHONPATH=src:. python research/run_joint_observation_warning.py
PYTHONPATH=src:. python -m pytest tests/test_joint_observation_warning.py -q --no-cov
```

The isolated prototype changes no frozen training modules and launches no
private-data job. See the accompanying results note for the final numerical
comparison and verification.
