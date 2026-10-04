# History helps short-lead warnings; it does not explain the larger target gain

All six input-control fits, 3,456 checkpointed updates and 198 gated policy heads
are complete. The primary full-history advantage survives useful-lead supervision:
**+0.650 percentage points [0.478, 0.821]**, with lower average false-plus-late
burden. Every seed and both regions show a positive primary recall difference.
Full input also outperforms timing-only input. These are useful development
findings, not an established breakthrough: longer-lead history evidence is weak,
regional warning-budget failures remain, and the controls do not yet isolate
past non-timing information.

## What was tested and preserved

The [plan](plan.json) and training code were committed at `039f927`; the evaluator
and paired analysis at `9ccb4a6`, before any new calibration predictions.
Two interventions each received the three original seeds: replace past values
and missingness with current state, or retain only seven observed timing/count
features and their missingness. Both retain genuine frame ages and valid masks.
Architecture remains LeagueEWS with 1,751,647 parameters, the original optimizer,
batches, twelve epochs and useful-next-event targets. No seed, epoch, input
channel or threshold was selected using later results.

All 24,000 training and 6,000 calibration matches come from the unchanged League
ZIP. The early and later halves each have 3,000 distinct matches, balanced by
region. All 198 early heads were jointly frozen before later replay. Five
prespecified policy variants and four early budgets are reported. The primary
is the equally weighted four-budget mean under matched-early regional mixtures;
its budget average is not additional data. The original registered comparison
and old thresholds remain separate and unchanged. Patch 16.17 stays sealed.

Intervals below use 2,000 paired, region-stratified whole-match draws, shared
across models, events, policies, budgets and fixed-seed averages. They are
pointwise, unadjusted and conditional on fitted models and selected policies.
Repeated seeds and rows are not independent matches. Repeated calibration
inspection, refitting and policy-selection uncertainty are not covered.

## Primary input results: 10–30 seconds

Recall differences are percentage points. Burden differences are expected
false-plus-late warnings per match per event. Seed order is 20260930, 20261001,
20261002.

| Full timely LeagueEWS minus current-only | Recall difference [95%] | Seed differences | Burden difference [95%] |
|---|---:|---|---:|
| Baron | +1.532 [1.053, 2.007] | +1.833, +1.723, +1.040 | −.00320 [−.01663, .00966] |
| Dragon | +.185 [.018, .349] | +.083, +.292, +.181 | +.00287 [−.00546, .01088] |
| Teamfight | +.233 [.108, .360] | +.308, +.222, +.169 | −.02915 [−.04831, −.01025] |
| Macro, primary | **+.650 [.478, .821]** | +.741, +.745, +.463 | **−.00983 [−.01764, −.00224]** |

Macro seed SD is .162 points. The burden improvement combines fewer false
warnings (−.01659) with more late warnings (+.00676), rather than reducing both
components. Dragon's burden difference is uncertain. The prespecified history,
event point-estimate non-harm, aggregate burden and regional-consistency rules
pass; non-harm is not a formal event-wise noninferiority test.

Full minus timing-only macro recall is **+2.933 [2.631, 3.252]** points; seeds
+3.077, +2.918, +2.805, SD .137. Event differences are Baron +6.539, Dragon
+1.068 and teamfight +1.193, all positive in every seed with positive paired
intervals. The macro burden difference, −.00931 [−.02140, .00325], remains
uncertain. The beyond-timing recall rule passes.

| Timely input, four-budget mean | Baron recall % / burden | Dragon | Teamfight | Macro |
|---|---:|---:|---:|---:|
| Full | 16.276 / .6380 | 10.723 / .6357 | 2.656 / .6052 | 9.885 / .6263 |
| Current-only | 14.744 / .6412 | 10.538 / .6328 | 2.423 / .6343 | 9.235 / .6361 |
| Timing-only | 9.737 / .6346 | 9.654 / .6373 | 1.463 / .6348 | 6.952 / .6356 |

History helps Europe by +.607 [.342, .866] and Americas by +.692 [.467, .922]
points, with all three seed differences positive in each region. Full versus
timing-only gains are +3.255 and +2.616 respectively. Regional recall consistency
is distinct from compliance with the warning budget.

The history effect also survives the fine common deterministic grid at early
budget one: +.763 [.528, .992], all seeds positive. Its burden interval crosses
zero. Full versus timing-only at that operating point gains +3.780 points but
also +.02181 [.00415, .03945] burden. Early matching does not establish equal
later cost, and a more favorable operating point is not substituted for the primary.

## Negative and limiting results

At 20–60 seconds, the four-budget history difference is only **+.089
[−.125, .303]** points, with seeds +.242, +.099, −.073. Baron is −.096
[−.688, .476], Dragon +.071 [−.082, .232], and teamfight +.294 [.137, .441].
Macro burden is +.00364 [−.00300, .01020]. Regional macro intervals also cross
zero. Timing-only remains weaker by +2.138 [1.806, 2.460] macro points, but this
contrast removes both current and historical non-timing information.

Correcting the target does **not** clearly increase the macro history effect:
the paired interaction is −.067 [−.177, .051] points at 10–30 seconds and
+.010 [−.156, .180] at 20–60. Primary Baron history benefit actually declines
by .334 points [−.586, −.050], with all seeds negative. The large longer-lead
target gain is already present in current-only input: +3.985 [3.751, 4.231]
points, versus +3.996 for full input. It cannot be attributed to learning more
useful historical buildup from the corrected target.

At primary mixture budget one, the full, current-only and timing-only models
exceed one later warning per match in **12, 11 and 10 of 18** region/event/seed
cells. Their maxima are 1.0631, 1.0762 and 1.0476. The fine common grid still has
5, 3 and 3 primary failures. None of these three models has a primary hard-one
overrun at the three lower prespecified budgets, but selecting those after
seeing results cannot retrospectively pass the prior promotion gate. All nominal
and hard-one failures are retained in [the violation table](budget-violations.csv).

## Original four families and registered comparison

The original common deterministic budget-one primary results reproduce exactly.
These operating points differ from the four-budget means above.

| Original model | Baron recall % / burden | Dragon | Teamfight | Macro |
|---|---:|---:|---:|---:|
| LeagueEWS | 20.878 / .9479 | 13.176 / .8887 | 3.082 / .7578 | 12.379 / .8648 |
| GRU | 12.085 / .8510 | 8.977 / .8220 | 2.204 / .6806 | 7.755 / .7845 |
| TCN | 20.734 / .9658 | 13.532 / .8991 | 2.834 / .7260 | 12.367 / .8636 |
| Snapshot | 18.636 / .9471 | 11.743 / .8264 | 2.590 / .7601 | 10.990 / .8446 |

Registered LeagueEWS-minus-GRU remains **+4.623 [4.223, 5.064]** points;
seed differences are +4.932, +3.379, +5.559. This supports the recall difference,
but the full registered regional screen still fails. LeagueEWS-minus-TCN is
+.012 [−.156, .178], with two negative seeds; minus snapshot is +1.389
[1.135, 1.637], all seeds positive. Under corrected targets and matched-early
policies, LeagueEWS exceeds TCN by only +.176 [.061, .290] primary points.
Unequal parameter counts and these controls do not isolate cross-attention or
a novel architecture. Earlier task-sharing results used cumulative labels;
this study does not establish transfer under useful-lead supervision.

## Mechanism, audit and next focused question

The evidence supports useful past input under this fixed training recipe at
short lead, and useful information beyond a timing-only representation. It does
not prove that the history gain specifically comes from past non-timing state.
The two ablations remove different combinations of current and past information;
this identification gap was [recorded before new scoring](interpretation-gate.json).
A focused next control should keep all current state and genuine timing history,
replacing only past non-timing values and missingness. Full minus that control
would isolate the remaining past-state question under the same recipe. Capacity,
optimization, task sharing and fresh generalization limits would still remain.

The [audit](audit.md) records the earlier leakage and objective/policy omissions,
this study's limits, and the regional exposure check. Established temporal event
prediction and localized-risk methods preclude a novelty claim from these small
metric changes; see the [targeted literature check](literature-check.md).

## Execution and reproducibility

The original compact study's `summary.json` exists. This study adds six fits to
33 completed neural fits, for 39 total. Training used the RTX 4060 Laptop GPU
and the unchanged CUDA environment; measured fit time totals about 70.7 minutes,
excluding preflight, checkpoint overhead and recovery downtime. One native
Python SIGSEGV interrupted the final seed at update 32. All six checkpoints
loaded with finite tensors; the five completed hashes remained unchanged.
One-shard recovery advanced to update 33, and the resumed worker completed with
exit zero. The [recovery record](recovery-record.json) preserves the failure;
its native root cause was not established or claimed repaired.

All 162 previous coarse/mixture heads and 72 previous dense heads reproduce
exact counts and selections. New controls passed 216,000 full-match independent
replay checks, with 76,601 additional component checks. All 16,800 prior model
metric/interval records and 12,960 shared contrast records reproduce exactly.
The CPU suite passed 627 tests, one skipped, at 85.89% coverage; Ruff and mypy
(87 source files) passed. The initial draft passed all seven CI checks.

[Reproduction commands](reproduce.md), [execution record](execution-record.json),
[complete tables](tables.md), [paired analysis](analysis.json),
[aggregate counts](aggregate-counts.csv), [seed results](by-seed.csv), and the
[figure](input-effects.svg) preserve positive and negative evidence. Private
scores, match records and model binaries are excluded. No test payload was opened.
