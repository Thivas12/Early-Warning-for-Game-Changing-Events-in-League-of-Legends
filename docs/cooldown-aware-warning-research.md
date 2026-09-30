# Learning When to Warn from Sparse Observations

**Research candidate, 30 September 2026.** Proposed contribution: exact expected
credit assignment for cooldown-constrained warning policies, evaluated with
causal actions between sparse observations. No claim of priority, state of the
art, publication readiness, or real-data improvement is established here.

**Adversarial audit:** the [novelty defense](policy-novelty-defense.md) now checks
the wSOL author implementation and stronger decision controls. All four tested
wSOL variants and a Bayes planner match exact credit on the original toy. The
example does not establish superiority over these methods. Optimal intervention
timing and refractory-process mathematics have explicit prior art.

## The criticism the project needs

The existing work is a useful, unusually careful evaluation pipeline. It has not
established a new scientific method. A million correlated rows do not constitute
a million independent examples, and GPU use would not change that.

The engineered coordination features gained only **0.168 percentage points** over
history, with a paired interval including zero. They do not support a claim that
we discovered a new coordination signal. The subsequent **33.22-point** gain
under a false-plus-late budget primarily demonstrates objective mismatch in the
old comparator. It is not a new state of the art. Under the earlier false-only
budget, the new history target *lost* about **3.49 points** of timely recall.
The strict-budget candidate also failed its regional requirement in NA.

Calibration patch 16.16 has now informed repeated development decisions. Calling
its next result independent validation or preregistered confirmation would be
misleading. The 6,000 patch-16.17 payloads remain sealed, but even success on that
single patch would not prove generality across games, patches, or applications.

## A precise question

Can a model learn to **save an alarm opportunity for a more useful future time**,
instead of maximizing the probability of a timely event at each individual time?

A false early alarm is doubly costly: it consumes attention and starts a cooldown
that can suppress a later useful warning. Pointwise classification does not
assign this second cost during training. We test whether differentiating through
the *actual expected emitted alarms* makes a useful difference.

We also separate the observation clock from the action clock. Player state still
arrives roughly once a minute. A warning can be issued on a ten-second clock
using the last received state and its age. This does not reconstruct movement,
create player observations, or multiply the independent sample size. Every
between-observation control receives the same opportunities.

## What already exists, and what we are proposing

| Prior work | What it already covers | Consequence for our claim |
|---|---|---|
| [Yang et al., Predicting Events in MOBA Games](https://arxiv.org/abs/2012.09424) | Event prediction, attribution and evaluation in MOBA | Neither the application nor event forecasting is novel by itself. |
| [Yèche et al., ICML 2023, Temporal Label Smoothing](https://proceedings.mlr.press/v202/yeche23a.html) | Temporal structure and training objectives for early prediction | Relabeling the useful warning window is not enough. |
| [Yèche et al., CHIL 2024, Dynamic Survival Analysis](https://proceedings.mlr.press/v248/yeche24a.html) | Event-time distributions, silencing and risk-localized alarm policies | A survival head plus a clever threshold is already established territory. |
| [Rath and Hughes, AISTATS 2022](https://proceedings.mlr.press/v151/rath22a.html) | Constrained early-warning training to control false alarms | Constrained training and Lagrange multipliers are not new contributions. |
| [Legnaro, Guastavino and Marchetti, 2026](https://arxiv.org/abs/2606.23145) | Temporally localized weighted score-oriented losses | The author implementation has now been inspected and independently matched in loss and gradient. It does not compute our emitted-alarm recurrence, but all four tested variants solve the toy equally well. Full paper text remains unavailable. |
| [Damera Venkata and Bhattacharyya, NeurIPS 2022](https://proceedings.neurips.cc/paper_files/paper/2022/file/c26a8494fe31695db965ae8b7244b7c1-Paper-Conference.pdf) | Optimal intervention timing, stopping and continuation values | Learning when to warn and limitations of static thresholds are established. Their first-trigger objective differs from our repeated alarm count. |
| [Deger et al., 2010](https://arxiv.org/pdf/1002.3798) | Active/refractory mass equations for stochastic point processes | The availability recurrence has direct mathematical antecedents. We do not claim it as new. |
| [Koshizuka and Yaguchi, September 2026](https://arxiv.org/abs/2609.24443) | Horizon-aligned objectives and fixed-policy evaluation with shared encoders | The previous target-alignment experiment is particularly weak as a novelty claim. |

**The proposed distinction:** optimize exact expected emitted-event credit under
a hard cooldown, rather than treating proposed alarms as independent utility
contributions or only imposing silencing after prediction. Couple this with a
strict causal replay of between-observation decisions.

This is a **candidate method contribution**, not a verified first-ever invention.
The recurrence below is a standard renewal/exclusion identity. Neither the MLP,
the triangular solver, nor primal-dual optimization is claimed as new mathematics.
The novelty case must survive a broader review of sequential decision losses,
refractory point processes and decision-focused learning, as well as the empirical
comparisons. Failure to find an identical paper in this targeted search is not
proof of novelty.

## Model and exact training objective

At action time \(s_j\), the model sees only the last observed history
\(H_{i(j)}\), its age \(s_j-t_{i(j)}\), and a clock. No later frame, future arrival
time, event label, or undisclosed event-survival signal enters the prediction.

The policy proposes an alarm with probability
\(p_j=\sigma(f_\theta(H_{i(j)},s_j-t_{i(j)}))\). It emits the alarm only if no
alarm was emitted in the preceding \(C=60\) seconds. Proposal probabilities do
not otherwise depend on the sampled action history. The recorded game trajectory
is treated as exogenous: we do not claim alarms change player behavior.

Let \(m_j=P(A_j=1\mid\text{recorded trajectory})\). Then

\[
 m_j=p_j\left(1-\sum_{i<j:\,0<s_j-s_i<C}m_i\right).
\]

**Why this is exact:** all earlier emitted alarms inside a single cooldown window
are mutually exclusive. Their sum is therefore the probability that the current
action is blocked. Conditional proposal coins are independent of earlier coins.
No independence assumption is made between emitted alarms.

Writing \(B_{ji}=1\{0<s_j-s_i<C\}\),

\[
 (I+\operatorname{diag}(p)B)m=p.
\]

The implementation uses a differentiable batched lower-triangular solve for
training, and a linear-time sliding cumulative recurrence for evaluation.
Training uses padded whole matches with length bucketing; it never truncates a
match to make the computation easier. Storage for the solve is quadratic in the
number of decision ticks in a batch. Batch size is configurable for GPU memory.

Let \(y_j=1\) when the **next strictly future** Dragon lies 20–60 seconds after
\(s_j\); otherwise \(y_j=0\). Because cooldown is at least the matching horizon,
two emitted alarms cannot claim the same event. Thus

\[
 E[\text{timely events}]=\sum_j m_jy_j,\qquad
 E[\text{non-timely alarms}]=\sum_j m_j(1-y_j).
\]

This equivalence is not guaranteed without an appropriate cooldown condition or
under a different matching rule. The implementation is specific to this protocol.
A late next event is never skipped to credit a later timely event.

After two shared BCE warm-up epochs, minimize over six more epochs

\[
 \frac1M\sum_{g=1}^{M}
 \left[-\sum_j m_{gj}y_{gj}
 +\lambda_{r(g)}\left(\sum_j m_{gj}(1-y_{gj})-1\right)\right],
\]

with nonnegative region-specific dual updates. This is ordinary primal-dual
training, not a finite-sample guarantee about future patches. Losses use entire
matches; the effective independent unit remains the match.

At policy selection, all models get the same randomized and deterministic policy
families, 49 fixed logit offsets, and a disabled option. Family and offset are
chosen on the earlier calibration half. Randomized metrics are exact expected
counts, **not realized counts from one stochastic deployment**. Deterministic
policies are the special case of probabilities zero or one. Results report the
selected family explicitly. We do not discard deterministic controls simply
because the proposed loss is stochastic.

## An explicit counterexample to pointwise optimality

Consider two equally frequent observable contexts, each with decisions at 0 and
30 seconds and a 60-second cooldown.

- Context C: an event is at 50 seconds with probability .6, otherwise at 80.
  Timely probabilities at the two decisions are (.6, 1).
- Context D: an event is at 40 seconds with probability .6, otherwise absent.
  Timely probabilities are (.6, 0); an alarm at 30 is late when the event occurs.

A Bayes-optimal pointwise classifier gives the same .6 score to the first
decision in both contexts. A common threshold cannot tell it to wait in C while
acting immediately in D. The policy objective can: first alarms in C block an
always-timely second decision, whereas first alarms in D are necessary.

The committed experiment optimizes a two-context action table, and evaluates
both families under a .25 non-timely-alarm budget per episode:

| Synthetic method | Timely event recall | Non-timely alarms/episode |
|---|---:|---:|
| Oracle pointwise probabilities, selected alarm policy | 70.00% | .2400 |
| Independent utility training, cooldown applied at evaluation | 60.77% | .2450 |
| Exact cooldown credit | 100.00% | .2000 |

These are **enumerated population illustrations on a designed 20-outcome toy**,
not held-out estimates, training seeds, or evidence of a League improvement.
The independent-utility number also depends on the specified optimizer and
finite offset grid; it is not a universal bound. The exact-credit result
illustrates why the research question is coherent.

The [subsequent stronger controls](policy-novelty-defense.md) give **100% recall
and .2 wrong alarms per episode for all four tested wSOL variants and a Bayes
planner**, matching exact credit. The exact upper bound for the declared
score-only family is 70.3125%; 70% above is its finite-grid result. This example
separates policies using only a myopic scalar score from richer temporal/contextual
decisions; it does not separate our method from existing temporal losses or
decision theory. The frozen six-model private-data screen does not yet include
these additional comparators.

When decisions are at least 60 seconds apart, the exact loss reduces to the
independent loss. A no-information control also gives a shared bound: if each
admissible decision has conditional timely probability \(q\), then
\(E[\mathrm{hits}]\le bq/(1-q)\) under expected wrong-alarm budget \(b\).
Timing machinery cannot create information when no predictive information exists.

## Runnable real-data experiment

The source is the completed, hash-verified coordination cache. Original processed
files, frozen feature definitions and previous experiment outputs remain intact.
Only train and calibration shards are reconstructed into the new output directory.
The source binding reads test **membership metadata**, never test payloads.

- **Training:** 24,000 matches, 704,967 real observations, patches 16.12–16.15.
- **Calibration:** 6,000 matches, 175,031 observations, patch 16.16; earlier
  1,500 per route for policy selection and later 1,500 per route for evaluation.
- **Features:** the same 158 observed history features, train-fitted scaling,
  explicit missing indicators, and observation age. No champion/player graph
  architecture is claimed.
- **Encoder:** two 128-unit GELU layers. Standard AdamW, eight fixed epochs.
  No model or epoch is selected on the later evaluation half.
- **Action grid:** absolute 10-second ticks with observation age below 60 seconds.
  Long gaps cause abstention; observations are not interpolated.
- **Seeds:** 20260930, 20260931, 20260932. These are integer seeds, not dates.
- **Budget:** <=.9 mean false-plus-late alarms in *each tuning region*, with a
  predeclared margin; evaluation requirement <=1 in each region. No guarantee
  is implied by this margin.

| Model | Training | Action opportunities | Purpose |
|---|---|---|---|
| history-bce | Timely-window BCE | 10-second ticks | Matched architecture and inputs |
| history-pmf | 25-category event-time likelihood | Same ticks | Distribution-based alternative |
| history-utility | Same warm-up, independent expected utility | Same ticks | Remove cooldown credit from the loss |
| history-refractory | Same warm-up, exact expected utility | Same ticks | Proposed candidate |
| clock-bce | BCE on observed clock/Dragon counts/time since Dragon | Same ticks | Detect timer-only explanations |
| history-refractory-frame | Exact expected utility | Real observation times only | Separate scheduling from extra information |

The PMF uses 24 five-second residual-time bins through 120 seconds plus a tail.
A stale forecast supplies mass in [age+20, age+60], using piecewise-uniform bin
mass. It is never renormalized on an unobserved claim that the event has not
happened. This is a likelihood baseline, **not a full reproduction of CHIL DSA,
survTLS, or wSOL**. Their additional regularizers and tuning are not represented.

All methods stop at the recorded final observation boundary. Online deployment
would require an observable match-end signal; no claim that the final frame can
be anticipated is made. This recording-window convention is shared by controls.

The runner preserves model weights, raw logits, policy curves, per-match expected
counts, selected policies, device/library metadata and checksums. Completed model
runs resume; an interrupted *incomplete* model is refit. This is not epoch-level
checkpoint recovery. GPU preflight runs before launching the background worker.

Primary contrast: exact-credit history versus matched BCE history. The exploratory
gate requires >=2 percentage points, a positive conditional paired interval,
positive gains in all three fitted seeds, improvement over the PMF, independent
utility and clock controls, and every required model/seed meeting both regional
budgets. Full curves and all failures remain in the results.

Intervals resample whole matches within regions after averaging paired fitted-seed
counts. They are conditional on those fits and selected policies; they do not
measure refitting, hyperparameter-selection, patch-population or live-action
uncertainty. Per-seed gains are separately exposed. No multiplicity-adjusted
confirmatory claim follows from this exploratory gate.

## What must happen before a publication-strength claim

1. Run the private-data screen. **No new League result exists in this branch.**
2. Add tuned strong boosted-tree controls on the *same action-age inputs*, and
   faithful TLS/survTLS/wSOL comparisons with equal tuning budgets. The prior
   frame-based tree score alone is not a sufficiently matched comparator.
3. Test observation dropping and 60/120/180-second cadences. Rebuild each retained
   history causally; dropping rows while retaining hidden lag features would
   leak the omitted observations. Test both fixed-rate and irregular arrivals.
4. Test label shuffles at the whole-match level within region/patch and realistic
   confounder controls, in addition to the committed analytical/synthetic checks.
5. Freeze a confirmatory protocol only after the method and baselines stabilize.
   Use patch 16.17 once, then acquire future untouched patches and at least one
   external early-warning dataset to establish generality.
6. Measure inference cost, action variance, uncertainty under refitting and
   robustness of false-plus-late burden. Exogenous replay cannot prove an alarm
   changes game outcomes; that requires a separate intervention study.

**Kill the method claim** if gains disappear against matched utility/distribution
or strong tree baselines, occur only through extra action opportunities, depend
on one seed/region, or violate the burden constraint. A negative result should
remain a negative result; renaming the architecture will not rescue it.

## Run from WSL

Explainable scope: six models × three seeds = 18 fits. New GPU training uses
existing real observations; it does not fetch more matches or read the test set.

```bash
cd /home/thivas/work/ai-portfolio/league-ews-audit
git fetch origin feat/cooldown-aware-warning-policy
git switch feat/cooldown-aware-warning-policy
make start-scheduled-policy
make scheduled-policy-status
```

The default requires CUDA and fails visibly if this environment has only a CPU
PyTorch build. `make scheduled-policy-preflight` prints the installed build/device.
Do not blindly run `uv sync`: the repository's existing torch source is CPU.
Select an appropriate official PyTorch CUDA build in a separate environment if
needed. `DEVICE=cpu` is an explicit CPU alternative, not an automatic GPU claim.
For a smaller GPU use `BATCH_MATCHES=8` **from the first launch**; changing it after
freezing requires a separate output directory. GPU memory/time have not been
measured on the user's hardware.

Results: `data/private/scheduled-policy-v1/summary.json`. For foreground bounded
progress, `make scheduled-policy MAX_NEW_MODELS=1` completes one pending fit.
Resume with the same command/configuration. Never run two workers on the same
output; locking enforces this.
