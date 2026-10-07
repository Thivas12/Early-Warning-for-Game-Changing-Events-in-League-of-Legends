# What explains useful early warnings in League of Legends? A controlled evaluation of history, task sharing and alert policies

**Development-study manuscript draft, 7 October 2026.** This paper synthesizes
completed experiments; it reports no new training or evaluation. All numerical
comparisons use inspected development calibration. Future-patch confirmation
has not been performed. This is not a submission-ready or breakthrough claim.

## Abstract

Accurate row-level event scores do not establish useful advance warnings. We
revisit LeagueEWS, a temporal hybrid for Baron, Dragon and teamfight prediction,
after auditing information leakage and retrospective alert selection in its
original evaluation. The continuation uses 24,000 training matches and 6,000
development calibration matches, chronological warning replay, three fixed
training seeds and paired whole-match uncertainty. Across controlled studies,
past non-timing state adds 0.533 percentage points of macro recall with
10–30 seconds of lead beyond genuine timer history and current state
(conditional 95% interval 0.374–0.696). Beneficial sharing is not uniform:
with useful-lead targets, joint training loses 0.664 points at 20–60 seconds
relative to independent event encoders (−0.925 to −0.397). After matching loss
weights, the hybrid's short-lead advantage over a TCN is 0.242 points
(0.131–0.354), with unresolved regional consistency. A capped risk-screened
policy eliminates observed nominal-budget violations across 720 regional
evaluation cells but reduces hybrid recall by 1.818 short-lead and 3.114
longer-lead points. These exploratory results distinguish history information,
supervision and policy effects from broad architecture claims. They do not
establish a new learning method, certified risk control or untouched-patch
generalization.

## 1. Research question

The original LeagueEWS project attributed gains in three-event prediction to
temporal buildup and shared learning. Its saved evaluation cannot test that
explanation: scaling preceded splitting, overlapping windows and their jitter
copies were randomly divided, and end-of-match statistics entered the feature
pool. Its displayed alerts also used future scores to select retrospective
peaks. We preserve the original notebooks and results as historical artifacts
and evaluate a causally usable descendant with explicit information boundaries.
The original report and notebook disagree on several saved metrics; none of
those historical scores is treated as newly reproduced evidence.
([Notebook and report audit](notebook-continuation.md).)

Our question is which proposed explanations survive controlled comparisons:
past information beyond current state and timers, aligned warning targets,
shared supervision, hybrid architecture, and warning-policy selection. These
are related but distinct explanations. Better performance after changing one
does not establish the others.

Temporal MOBA event prediction is established. Yang et al. study four events
in Honor of Kings; Vardakis et al. study imminent player deaths in League.
Their event definitions and evaluation settings do not permit direct score
comparisons with ours. Early-event research also already separates time-step
prediction from event-level alarm prioritization. Our contribution target is
a controlled empirical account of this League system's behavior, rather than
priority for these components. ([Yang et al.](https://arxiv.org/abs/2012.09424);
[Vardakis et al.](https://www.sciencedirect.com/science/article/pii/S1875952126000133);
[Yèche et al.](https://proceedings.mlr.press/v248/yeche24a.html).)

## 2. Data, targets and information availability

The audited development archive contains 24,000 training matches from patches
16.12–16.15 and 6,000 calibration matches from patch 16.16, drawn from the
Europe and Americas routes. It contains 879,998 genuine observed rows: 704,967
training and 175,031 calibration. Whole matches are split before sequence
construction, and normalization is fitted on training observations. The
earlier 3,000 calibration matches select warning policies; the later 3,000
evaluate them, with 1,500 matches per region in each half. Repeated inspection
of both halves makes the research program adaptive development. The separate
6,000-match patch-16.17 test has not been used in these studies.
([Data boundary](league-research-scope.md);
[initial continuation methods](../reports/neural-continuation-2026-10-01/methods.md).)

The three targets are Baron completion, Dragon completion and the registered
teamfight kill episode. Objective labels come from objective-kill records;
they are not objective engagement onsets. Consequently, the paper makes no
claim of forecasting an objective before its first attack. Inputs use audited
current and past information, with explicit ages, masks and missingness.
Eight genuine frames retain approximately seven minutes of history at the
usual observation cadence. No interpolated row is represented as a new
observation. Sparse observation cadence remains an information limitation.
([Label implementation](../src/league_ews/labels.py);
[input adaptation](notebook-continuation.md).)

## 3. Warning endpoint and statistical analysis

At an observed timestamp, a policy emits a warning if the score exceeds its
selected threshold and the event-specific 60-second cooldown permits it.
Warnings are emitted chronologically; future scores cannot replace earlier
actions. A warning receives credit for the earliest unmatched event within
its prediction horizon. Each event is credited once. A timely warning precedes
the event by 10–30 seconds for the primary endpoint or 20–60 seconds for the
secondary endpoint. Warnings with shorter lead are late; warnings without a
credited event in the horizon are false. Both incur warning cost.

For event type e, recall is the total timely credited events divided by the
total events, including events without an observed decision opportunity.
Burden is false-plus-late warnings divided by matches. Macro recall and burden
average event-specific quantities equally. Budgets apply separately to each
event and region; they are not one shared attention budget for all three
events. The two lead-window policies are evaluated separately, not as one
simultaneously deployed system.
([Chronological replay and independent reference](../scripts/warning_risk.py).)

The initial continuation used a common deterministic threshold at budget one.
Later studies predeclared four early-calibration budgets, 0.25, 0.50, 0.75 and
1.00. Their primary operating comparison uses region-specific mixtures of
whole-match threshold policies to match expected early cost. A mixture selects
a policy for a whole match; it does not switch thresholds using future match
outcomes. Reported mixture results are expected policy counts. Fine-grid
common deterministic policies provide separate sensitivity analyses. Equal
early cost does not imply equal later cost. Estimates under these policies
are labeled separately throughout the paper.
([Operating-point study](../reports/warning-efficiency-2026-10-03/protocol.md);
[fine-grid study](../reports/dense-policy-2026-10-04/protocol.md).)

Each model is fitted with three fixed seeds. Paired intervals use 2,000
whole-match bootstrap draws stratified by region, with the same sampled
matches shared across models, events, budgets and seeds. Counts from fixed
fits are averaged within the analysis; rows, seeds and repeated budgets are
not independent match samples. All intervals below are pointwise conditional
95% intervals. They omit refitting, policy selection and the adaptive research
search; secondary intervals are not multiplicity-adjusted. These intervals
must not be read as confirmatory significance after selection.

## 4. Controlled comparisons

The continuation retains LeagueEWS's residual dilated TCN, squeeze-excitation,
stacked bidirectional GRUs, cross-attention and temporal pooling. Bidirectionality
within a window entirely preceding the prediction cutoff is permissible;
later observations are excluded. The adaptation differs from the Keras
notebook in normalization, masks, dropout semantics, input channels, fixed
training schedule and output horizons. It is not a bit-for-bit reproduction.
All planned fits use 12 epochs and three fixed seeds. The final inventory is
69 neural fits, including controls and negative results; it is not 69 independent
replications of a selected claim.
([Architecture and training description](notebook-continuation.md);
[final fit inventory](../reports/matched-optimization-2026-10-06/research-report.md).)

| Question | Controlled change | Important limit |
|---|---|---|
| Does history help beyond current state and timers? | Retrain the same hybrid while retaining true timer history and current features, repeating current values across past non-timing channels | Input removal changes effective optimization; it does not isolate attention or causal game behavior |
| Does the training target match useful warning lead? | Replace cumulative labels for evaluated heads with the useful-lead intervals, retaining auxiliary heads | An established objective-alignment idea, not a new loss principle |
| Does joint supervision help? | Joint hybrid versus separate same-width encoders for each event | Independent system uses roughly three times the encoder storage and training computation |
| Do weights or gradient projection explain changes? | Original/equal event weights crossed with ordinary training/PCGrad | Results depend on the fixed recipe; no globally optimal optimizer claim |
| Does the hybrid beat a strong temporal control? | Equal-weight useful-lead hybrid versus equal-weight TCN and GRU | Hybrid 1,751,647 parameters; TCN 557,087; GRU 912,717; capacity and tuning are not matched |
| What removes observed warning overruns? | Uncapped empirical, capped empirical, capped fixed-sequence and capped KL fixed-sequence selection | Existing risk mathematics; adaptive calibration prevents nominal certification |

## 5. Results

### 5.1 The initial architecture result depends on the comparator

Under the originally registered common policy at budget one, short-lead macro
recall is 12.379% for LeagueEWS, 7.755% for GRU, 12.367% for TCN and 10.990%
for the snapshot model. LeagueEWS exceeds GRU by 4.623 points [4.223, 5.064]
but exceeds TCN by only 0.012 [−0.156, 0.178]. The regional budget gate fails.
GRU itself trails the snapshot control, and the longer-lead hybrid–GRU macro
contrast is adverse. These findings prevent using the large GRU margin as
evidence of broad hybrid superiority.
([Original results](../reports/neural-continuation-2026-10-01/research-report.md).)

### 5.2 Past non-timing state contributes at short lead

With genuine timer history and all current features retained, full past state
adds 0.533 macro short-lead recall points [0.374, 0.696], averaging the four
matched-early budgets. All three macro seed effects and both regional macro
intervals are positive. Burden falls by 0.01168 warnings per match per event
[−0.01928, −0.00384]. Baron contributes +1.333 points [0.892, 1.777], teamfight
+0.218 [0.093, 0.344], while Dragon's +0.047 [−0.122, 0.202] is uncertain.
At longer lead the macro effect is uncertain, and Dragon declines by 0.154
points [0.006, 0.295]. Lower total burden at short lead combines fewer false
warnings with more late warnings; it does not improve every error component.
([Conditional history results](../reports/clock-history-2026-10-04/research-report.md).)

This control supports incremental predictive information in the retained past
state under the tested recipe. It does not show universal event benefit,
identify a particular cross-attention mechanism, or establish usefulness on
a new patch. The study also has an explicit protocol timing deviation:
analysis hashes preceded scoring, but the corresponding Git commit followed
scoring because of an approval delay. The immutable deviation record remains
part of the evidence.
([Timing deviation](../reports/clock-history-2026-10-04/scoring-release-repair.md).)

### 5.3 Target alignment helps both strong architectures

Useful-lead targets improve short-lead macro recall by 0.451 points
[0.324, 0.584] in LeagueEWS and 0.322 [0.199, 0.451] in TCN under matched-early
budget averaging. At longer lead their gains are 3.996 [3.770, 4.248] and
3.756 [3.514, 4.005]. Much of the improvement therefore occurs without the
hybrid's additional machinery. The larger target gains also exchange late
warnings for false warnings. They are not uniform improvements across errors
or policies: under the original coarse budget-one policy the hybrid's short-lead
target effect is −0.101 [−0.291, 0.094].
([Target results](../reports/timely-neural-2026-10-03/research-report.md).)

### 5.4 Shared learning produces event-dependent transfer

With useful-lead targets and original task weights, joint minus independent
macro recall is −0.061 points [−0.219, 0.099] at short lead. Baron loses 0.514
points while Dragon gains 0.328; there is no clear teamfight effect. At longer
lead the joint system loses 0.664 macro points [−0.925, −0.397], with every
seed and both regional macro intervals adverse. Baron loses 2.180 points
[1.414, 2.928]. Aligned targets benefit independent models more at longer
lead: the target-by-sharing interaction is −0.562 [−0.776, −0.343].
([Useful-lead sharing results](../reports/timely-sharing-2026-10-05/research-report.md).)

This rejects uniform beneficial sharing under these recipes. It does not prove
that all shared learning is harmful. Equal task weights subsequently recover
part of Baron's deficit, demonstrating that the earlier effect cannot be
attributed solely to an unavoidable shared-representation bottleneck. PCGrad
does not provide a clear additional primary benefit after equal weighting.
([Weighting factorial](../reports/timely-optimization-2026-10-05/research-report.md).)

### 5.5 Matching weights leaves a small hybrid–TCN margin

Under equal event weights and useful-lead targets, the hybrid exceeds TCN by
0.242 short-lead macro points [0.131, 0.354] across matched-early budgets.
All three seeds and all aggregate event recall intervals are positive.
Europe's macro interval nevertheless includes zero; capacity, compute and
tuning remain unmatched. The longer-lead margin is 0.714 [0.540, 0.892],
with additional Baron warning burden. These estimates support a limited
recipe comparison, not an isolated cross-attention effect or a practically
important margin established independently of the observed data.
([Matched controls](../reports/matched-optimization-2026-10-06/research-report.md).)

### 5.6 Budget compliance comes with recall loss

The final policy comparison reuses five fitted families and applies a cap
of four chronological warnings per event and match. The cap uses only past
emitted warnings; it does not use future labels. A four-warning cap bounds
loss by four, not by the nominal budget of one. Thresholds are selected on
the same fixed fine grid under two regional constraints. Fixed-sequence
selection stops at the first failed test. The KL variant uses an established
bounded-loss test with error allocation 0.05/720.
([Policy protocol](../reports/warning-risk-2026-10-07/protocol.md).)

| Policy | Nominal violations, short lead | Nominal violations, longer lead | Hybrid macro recall, short / longer lead |
|---|---:|---:|---:|
| Uncapped empirical | 68/360 | 46/360 | 10.025% / 15.488% |
| Capped empirical | 60/360 | 45/360 | 9.965% / 15.411% |
| Capped empirical fixed sequence | 60/360 | 45/360 | 9.965% / 15.411% |
| Capped KL fixed sequence | 0/360 | 0/360 | 8.206% / 12.374% |

Each window contains five families × three seeds × three events × two regions
× four budgets. These cells are not independent samples. No KL selection is
silent. Hybrid short-lead burden falls from 0.6037 to 0.4546, and longer-lead
burden from 0.5935 to 0.4477. Its total recall changes are −1.818 points
[−1.908, −1.734] and −3.114 [−3.223, −3.010]. Capped empirical and capped
empirical-sequence policies select exactly the same thresholds in this study;
most of the recall cost comes from the uncertainty allowance. The operating
curves do not demonstrate an improved prediction frontier.
([Risk-policy results](../reports/warning-risk-2026-10-07/research-report.md).)

Under KL selection, the short-lead hybrid–TCN advantage remains +0.225 points
[0.118, 0.340]. Europe's interval spans zero, and teamfight burden increases.
Longer-lead Baron still trails independent encoders by 0.774 points
[0.132, 1.399]. Observed budget compliance therefore does not remove the
representation and task-sharing limitations. Learn then Test requires valid
tests under an appropriate calibration sampling model; this repeatedly
adapted research population does not supply a certified risk guarantee.
([Full regional results](../reports/warning-risk-2026-10-07/research-report.md);
[Learn then Test, Section 1.1](https://arxiv.org/pdf/2110.01052v5).)

## 6. Interpretation and limitations

The controlled findings distinguish three statements that the original broad
explanation combined. Past non-timing information can help at short lead.
Shared supervision can help one event while hurting another. The hybrid's
large margin over a weak GRU recipe does not persist at that scale against
TCN. Target alignment and task weights account for material changes without
establishing a new architectural principle. Conservative policy selection
can remove observed overruns by spending less of the budget and recovering
fewer events.

All studies use the same development population. Precommitting each follow-up
protects its execution order; it does not erase adaptation to previous results.
The fitted seeds are few, intervals condition on trained models and policies,
and player overlap may induce dependence not identifiable from the compact
archive. Chronological patch separation does not imply exchangeability. Sparse
observations, completion labels and the limited regions constrain interpretation.
No result establishes an effect on actual player decisions or match outcomes.

The fixed baselines were not given equal parameter counts, FLOPs or a broad,
matched hyperparameter search. Consequently, the results compare specified
recipes and cannot establish a global ranking of model families. A favorable
conditional interval also does not establish a minimum useful coaching effect.
The nearest 2026 League paper was reviewed at publisher-abstract level because
full-text retrieval returned HTTP 403; a complete submission review must
resolve that comparison without guessing at its methods.

An exploratory empirical paper can report negative and conditional findings
without requiring every practical-promotion gate to pass. It must retain those
failures and avoid substituting a successful secondary result for a failed
primary comparison. The manuscript does so. Confirmatory generalization,
method novelty and publication acceptance remain unestablished.

## 7. Reproducibility and evidence access

Original notebooks, frozen source, protocols, fit inventories, selected policy
records, complete aggregate results and negative outcomes remain available in
the repository. The latest completed study records 740 passing software tests,
one skip, 810,000 full independent replay checks and exact reproduction of
previous baseline results. These checks support implementation consistency;
they are not empirical replications or proof of novelty. Private match payloads,
model binaries and score arrays are not part of the public report.
([Reproduction record](../reports/warning-risk-2026-10-07/reproduce.md).)

The [synthesis source index](../reports/publication-synthesis-2026-10-07/sources.json)
binds the dependencies used for this draft. Detailed event, region, seed,
budget and policy results remain in the linked study reports rather than being
selected anew for this synthesis. No new fit or score was produced to write it.
