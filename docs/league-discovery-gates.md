# LeagueEWS: the evidence needed for a strong paper

**Latest completed follow-up, 4 October 2026:** the [conditional history study](../reports/clock-history-2026-10-04/research-report.md) completed three further fits and all 216 policy heads. Past non-timing state adds +.533 recall points [.374, .696] beyond genuine timer history and current state at 10–30 seconds, with all seed and regional macro effects positive and lower aggregate burden. Longer-lead Dragon declines; regional budget gates remain failed. The analysis hash record preceded scoring, but Git approval delayed its commit until afterward; [the deviation and enforced future release procedure](../reports/clock-history-2026-10-04/scoring-release-repair.md) are explicit. Preserve all 42 completed neural fits. No worker needs restarting, no breakthrough is claimed, and patch 16.17 stays sealed.

**Latest evidence, 4 October 2026:** the [useful-lead input controls](../reports/timely-inputs-2026-10-04/research-report.md) support a primary history gain of +.650 points [.478, .821], with lower aggregate burden and positive effects in every seed and both regions. Full input also exceeds timing-only input, but those two comparisons do not identify the contribution of past non-timing state conditional on current state and timer history. Longer-lead history evidence is weak, and previously failed regional budgets remain failed. This is an exploratory mechanism result, not a novel architecture or breakthrough. All six new fits and 198 gated policy heads completed; patch 16.17 remains sealed.

**Update, 3 October 2026:** the development archive is available and validated.
[Nine real three-event tree fits](../reports/league-three-event-results-2026-10-01.md)
are complete, as are the twelve neural fits and three matched history-ablation
fits, followed by nine independent event fits and three PCGrad fits. The
[neural report](../reports/neural-continuation-2026-10-01/research-report.md)
records failed development gates and a limited history benefit. The
[task sharing report](../reports/task-sharing-2026-10-02/research-report.md)
finds a +0.445-point macro recall effect of joint training, while Baron loses
0.627 points and both variants fail a regional budget. Uniform task benefit is
unsupported. The [PCGrad follow-up](../reports/gradient-conflict-2026-10-02/research-report.md)
raises mean primary macro recall by 0.367 points with more burden, but fails
Baron recovery, seed consistency and a regional budget. Longer-lead Baron gains
accompany Dragon and teamfight losses. No breakthrough is established.
The [warning-efficiency diagnostic](../reports/warning-efficiency-2026-10-03/research-report.md)
now evaluates all seven variants across four fixed budgets without new fitting.
With expected early cost matched, PCGrad-minus-joint primary macro recall is
+0.027 points [−0.036, +0.098]; its longer-lead difference is negative in every
seed. The frozen screen fails. A primary history benefit survives, while the
joint-versus-independent macro advantage does not clearly survive this policy
comparison. The access limitation recorded below is historical and resolved.

Status, 30 September 2026: **no breakthrough established**. The next empirical
question comes from the original report's claim that temporal buildup and
shared learning explain improvements across Baron, Dragon and teamfights.
The [source review](notebook-continuation.md) recovers that claim and its actual
notebook implementation. Its contaminated scores cannot establish the claim.

## What the evidence currently says

| Evidence | Consequence for the next experiment |
|---|---|
| Engineered coordination adds 0.168 percentage points of timely Dragon recall over observed history; the conditional interval crosses zero | There is no demonstrated new coordination mechanism to promote as a discovery |
| Changing the Dragon training target to the useful warning interval changes the recall/late-warning tradeoff; the North America primary budget gate fails | Objective alignment matters, but this is neither general superiority nor a new learning principle |
| Original LeagueEWS compares a large temporal hybrid against RF and a last-frame MLP | The comparison does not isolate history, capacity, cross-attention, or cross-event transfer |
| Private training and calibration data exist in the user's WSL run, but only aggregate summaries are available here | Those summaries cannot train models, produce matched per-match comparisons, or measure transfer |

See the two immutable real-run reports linked in
[the League scope record](league-research-scope.md). None of the historical
other-game experiments contributes evidence to this paper.

## Closest literature: claims already occupied

This is a targeted novelty check, not a claim of an exhaustive systematic review.
Publisher/author abstracts were checked on 30 September 2026. Conclusions below
are restricted to what those sources support; unavailable full texts have not
been treated as read.

| Primary source | Relevant established work | What we therefore cannot claim |
|---|---|---|
| Vardakis et al., *Prediction of MOBA game events based on In-Game Data*, Entertainment Computing 57 (2026), 101091; [publisher](https://www.sciencedirect.com/science/article/pii/S1875952126000133), DOI 10.1016/j.entcom.2026.101091 | Temporal Fusion Transformer forecasts imminent deaths in professional League matches; abstract reports roughly 0.6 F1 for a five-second horizon with fewer than 200 matches | First temporal neural League event predictor. Its five-second death score is not directly comparable to our three event definitions and 10–60-second horizons. Full article retrieval returned 403; no split-quality judgment was made |
| Yang et al., *Predicting Events in MOBA Games: Prediction, Attribution, and Evaluation*, IEEE Transactions on Games (2022); [author manuscript](https://arxiv.org/abs/2012.09424) | Four event types and feature attribution in Honor of Kings | First multi-event MOBA prediction or first interpretable MOBA event model. This is related work, not a dataset substitution |
| Nguyen et al., *Clinical Risk Prediction with Temporal Probabilistic Asymmetric Multi-Task Learning*, AAAI (2021); [proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/17097) | Time-dependent asymmetric transfer and protection against negative transfer across clinical tasks | First temporal task-sharing or first mechanism for protecting individual tasks; a gating layer alone would not distinguish us |
| Damera Venkata and Bhattacharyya, *When to Intervene*, NeurIPS (2022); [proceedings](https://proceedings.neurips.cc/paper_files/paper/2022/hash/c26a8494fe31695db965ae8b7244b7c1-Abstract-Conference.html) | Optimal timing through a hazard-process stopping formulation | First learned intervention timing or first warning policy beyond thresholded classification |
| Yèche et al., *Dynamic Survival Analysis for Early Event Prediction*, CHIL (2024); [proceedings](https://proceedings.mlr.press/v248/yeche24a.html) | Risk localization and alarm prioritization improve event-level evaluation | First time-localized risk or first event-level alarm optimization |

The previous [policy novelty defense](policy-novelty-defense.md) also rules out
calling the refractory recurrence a new theorem. Repackaging these ingredients
with a new acronym is not a contribution.

## The next falsifiable question

**After fixing information availability, does the original LeagueEWS encoder
learn transferable precursors that improve useful advance warning for all three
events across patches and regions?**

The immediate experiment is a mechanism screen. A positive screen identifies
something to investigate; it does not automatically establish a new method.

1. Complete the already implemented four-family, three-seed continuation:
   LeagueEWS, GRU, TCN and snapshot. Preserve its original freeze and all seeds.
   Do not replace its losses or outputs after seeing calibration results.
2. If LeagueEWS has a useful gain over matched-data sequence controls, add a
   separately frozen mechanism study. Retrain the same LeagueEWS architecture
   with every valid historical value/missingness vector replaced by the current
   one, retaining valid lengths and original age channels. This preserves the
   parameter count and tensor dimensions while removing past state information.
   It is a trained ablation, not an out-of-distribution inference corruption.
   It does not isolate every aspect of temporal computation.
3. Train three separate same-width LeagueEWS encoders, one per event, using
   that event's four horizons and original loss weight. Compare each to the
   corresponding joint-model head on identical match data and seeds. Each
   event gets the same encoder capacity; the independent system uses roughly
   three times the total encoder storage and training compute. Report both
   per-event and total costs. The causal claim concerns shared supervision,
   not an equal-total-compute comparison.
4. Inspect where transfer helps or hurts using training and early calibration
   only before choosing a new mechanism. Relevant strata include event type,
   lead interval, region and match phase. Report task-specific harm even when
   the macro average improves. A proposed sharing mechanism must then beat
   the independent encoders, ordinary shared training and an appropriate
   established transfer method; the model family must follow the observed
   failure, not precede it as an invented novelty label.

Steps 1 and 2 are complete; neither passed its full regional-budget screen.
Step 3 is now complete: sharing raises Dragon recall, lowers Baron recall in
every seed, and gives no clear primary teamfight recall gain. The mean effect
varies by region and lead interval and costs additional warning burden. The
frozen no-task-harm and practical promotion rules fail. This identifies a
task-dependent effect of the joint recipe, without isolating gradient conflict,
loss scaling, representation competition or threshold timing as its cause.
Step 4 now includes training-only gradient and early-calibration diagnostics,
followed by a separately frozen test of established PCGrad. Its three fits and
gated evaluation completed; the frozen practical screen fails. It changes the
event/lead-time tradeoff without establishing gradient conflict as the cause
of Baron harm. Mean primary gains against TCN and independent encoders carry
additional warning burden. A next comparison should address warning efficiency
across prespecified early-calibration operating budgets for all strong controls;
selecting favorable heads, seeds or horizons from these results is not confirmation.
That warning-efficiency comparison is now complete. Exact early-cost mixtures
do not establish a primary PCGrad advantage; later budget drift remains. The
robust primary history effect motivates identifying which past information
matters, using a separately frozen trained ablation before any new claims.
No further method or test release is selected here. All completed training
freezes remain unchanged. No new transfer mechanism or broad hybrid advantage
has been established.

### Endpoints and rejection rules

Keep the registered match-disjoint patches: 24,000 training matches on
16.12–16.15, 6,000 calibration matches on 16.16. The 6,000 patch-16.17 payloads
stay sealed. Earlier calibration has already influenced this research; this
is exploratory development even if the next comparison was written in advance.

Primary continuation endpoint: macro event recall with 10–30 seconds of lead,
60-second cooldown, and at most one false-plus-late warning per match **for each
event and each region**. Report the 20–60-second endpoint separately. The
per-event limits are not a single combined attention budget; a joint-budget
claim requires a separately specified policy and matched controls.

Reject a claimed mechanism if the gain disappears against the relevant control,
comes from extra observation/decision times, violates a regional budget, or
improves the macro average by concealing material event-specific degradation.
Use paired whole-match uncertainty, preserve region strata, show all seeds,
and distinguish conditional-on-fit intervals from training variability.
Overlapping windows are not independent experimental units.

Before confirmatory testing, freeze the selected method, strong controls,
minimum worthwhile effect, task-specific noninferiority margins, budget policy,
and multiplicity handling. Those effect margins must be justified for the
offline research/coaching use case, not chosen to pass observed results. A
documented amendment may precede one joint release of the untouched test; this
document does not authorize opening it.

An outstanding paper would require a replicable discovery about transferable
precursors or a distinct validated method, strong matched comparisons, and
held-out generalization. Neither adding layers nor reaching one million rows
satisfies those conditions.

## Make the necessary data available

The public legacy Kaggle endpoint currently returns HTTP 403 with
`Permission 'datasets.get' was denied`. No dataset was downloaded and no
authentication bypass was attempted. The private WSL cache is not mounted here.

The new `scripts/export_league_three_events.py` resolves the earlier
Dragon-only export limitation. It reads the existing audited train/calibration
processed matches, checks their original hashes, and exports:

- 27 current-frame values and their missingness flags, genuine observation
  times, all 12 binary targets, and exact three-event times;
- whole-match offsets, development-only match/region/patch membership, and
  source/checksum manifests;
- each frame once, with bit-for-bit eight-frame reconstruction checked for
  every match before it is included.

It does not collect matches, fit models, require CUDA, open test payloads, or
export player identifiers. It regenerates the audited B4 features from existing
processed matches, so a staged B4 cache is not a prerequisite. Match IDs and
development route/patch metadata are included. It exports no fitted normalizer;
the receiving trainer must fit normalization on training current frames only.
Actual ZIP size is reported when the real export finishes; no size is promised
from the synthetic verification fixtures.

Run in the existing WSL checkout without switching away from a running study:

```bash
cd /home/thivas/work/ai-portfolio/league-ews-audit
git fetch origin research/league-three-event-evidence
git worktree add --detach ../league-ews-export origin/research/league-three-event-evidence
cd ../league-ews-export
PYTHONPATH=.:src ../league-ews-audit/.venv/bin/python \
  -m scripts.export_league_three_events --repo . --data-repo ../league-ews-audit
```

The separate checkout supplies code; `--data-repo` reads existing private data
from the original checkout. It does not copy data or switch the running study's
branch. Create the worktree once; rerun the Python command if an export was
interrupted. When already on this branch with the private data in the same
checkout, the equivalent short command is:

```bash
make export-league-three-events
```

Upload `data/private/league-three-event-export-v1/development.zip`. Existing ZIPs
are never overwritten; an interruption removes its partial ZIP. The exporter
cannot run in this workspace until the private source exists. Software checks
are not evidence for the research hypotheses above.

Verification in this workspace: 25 tests passed (11 new export-contract checks
and 14 existing notebook-continuation checks), plus focused Ruff checks,
`git diff --check`, and a Makefile dry run. Export checks use synthetic fixtures
to exercise exact reconstruction, all three target families, future isolation,
numeric-only storage, event-time/label agreement, excluded test payloads,
checksums, source symlinks, no-overwrite publication, cleanup on failure and
separate code/data checkouts without copying source data.
The real export command stops at the missing private source freeze here.
