# Research direction: forecasting objective engagement before first contact

Status: an exploratory measurement study and a falsifiable research program.
Neither a new state-of-the-art predictor nor a defended priority claim exists
yet. The implementation is isolated in `research/`; the League forecasting
pipeline, its prior results, and the sealed patch-16.17 test are unchanged.

The [completed real-replay audit](../reports/objective-onset-corpus-2026-09-30.md)
contains seven verified matches, 21 kills, 41 primary damage episodes, full
sensitivity results, and a compact artifact that reproduces the report offline.

## The question that would justify the work

**Can coordinated team behavior forecast the beginning of an objective attack
20–60 seconds ahead, including attacks that do not produce an objective kill,
under the information actually available to the intended observer?**

The prospective scientific contribution would be a reproducible answer to that
question, together with an independently validated dataset and a method that
beats strong controls across patches. A promising result would distinguish
early tactical information from knowledge that combat has already started.
Calling a graph, Transformer, multi-state survival model, or exact policy
gradient novel would not answer the question.

First contact is a measurable event. It is **not** the time a team formed an
intention, the time a decision became irreversible, or the last time a useful
response was possible. Those stronger constructs need separate measurements.

## Why this direction survived the research screen

| Direction examined | Closest established work or limitation | Decision |
|---|---|---|
| Timing a warning under a cooldown | Optimal intervention timing, refractory point processes, and temporal warning losses already cover much of this territory. The repository's stronger controls erased the original synthetic advantage. | Retain as a control, not the novelty claim. |
| Jointly choosing observations and warnings | Active sensing and finite-state POMDP controllers have direct precedents. Our previous 27-fit study did not establish robust superiority. | Do not promote the candidate. |
| Inferring player intent from movement/cameras | Tot et al. already predict Dota team fights from player and camera positions. Our League frames do not record cameras or intentions. | A claim of first intent prediction is untenable. |
| Warnings before an actionable response deadline | Optimal intervention and response-aware prediction are established. Passive League frames do not identify the response's causal benefit. | Requires response measurements and a prospective study. |
| Player-visible versus omniscient forecasting | Potentially valuable, but the current League schema lacks authoritative visibility. Geometric vision estimates cannot silently become ground truth. | A required future data contract, not a result in this audit. |
| Forecasting objective engagement onset, retaining non-terminal episodes | Completion timestamps and contact timestamps are distinct targets. Replay logs permit direct examination; current League Match-V5 frames do not. | Selected for an empirical measurement study before model development. |

This selection is a judgment about tractability and scientific value. A search
that failed to retrieve a paper does not prove the absence of prior work.

## Literature boundary

1. **Yang et al., Predicting Events in MOBA Games**
   ([paper](https://arxiv.org/pdf/2012.09424), full text inspected): rich HoK
   telemetry, multiple event tasks, sequence models, and attribution already
   exist. The Tyrant objective task is a direct domain precedent. This work
   prevents claiming that objective-event prediction or interpretable sequence
   models are new.
2. **Tot et al., What Are You Looking At?**
   ([CoG 2021 paper](https://ieee-cog.org/2021/assets/papers/paper_101.pdf),
   full text inspected): camera and character positions support team-fight
   prediction. Its label construction includes ongoing fight intervals; its
   discussion also recognizes problems with fight boundaries. This is an
   important antecedent to a boundary audit, not evidence that nobody has
   considered event onset.
3. **Vardakis et al., Prediction of MOBA game events based on In-Game Data**
   ([publisher](https://www.sciencedirect.com/science/article/pii/S1875952126000133),
   2026): the indexed publisher abstract describes imminent League player
   elimination prediction with a Temporal Fusion Transformer. Full text was
   inaccessible in this session. No claim of surpassing this paper is allowed.
4. **Yèche et al., Temporal Label Smoothing**
   ([ICML 2023](https://proceedings.mlr.press/v202/yeche23a.html)) and
   **Dynamic Survival Analysis for Early Event Prediction**
   ([CHIL 2024](https://proceedings.mlr.press/v248/yeche24a.html)) establish
   temporal objectives and event-level warning evaluation. They are stronger
   methodological controls than an arbitrary binary classifier alone.
5. **RiskProp: Collision-Anchored Self-Supervised Risk Propagation for Early
   Accident Anticipation**, CVPR 2026
   ([author manuscript](https://arxiv.org/html/2603.27165v1), introduction and
   method formulation inspected): next-frame predictions supply detached soft
   supervision, with a monotonicity constraint and collision-frame anchoring.
   It already learns risk without manual anomaly-onset labels. Renaming that
   idea as tactical risk propagation would not establish novelty. Its
   collision-risk target differs from observed contact onsets in both terminal
   and non-terminal episodes; that distinction still needs an empirical case.

The earlier detailed comparison of active sensing and exact policy gradients
is preserved in `joint-observation-warning.md` and `policy-novelty-defense.md`.
This direction does not supersede their negative results.

Search date: 2026-09-30. Query families covered MOBA event/intent prediction,
actionability and response time, aborted objective attempts, early-event onset
labels, and public high-frequency MOBA telemetry. Searches used two engines;
several narrow queries returned irrelevant material. This is a targeted review,
not an exhaustive systematic review or a claim to have searched closed indexes.

## The measurement problem

Let S be the first positive damage to the objective in an episode, T its
destruction time if it is destroyed, and D = T − S. A detector that merely
announces the first damage after delay δ emits at A = S + δ.

Its completion lead is T − A = D − δ. Its onset lead is S − A = −δ.
Consequently, a pure detector receives completion credit whenever

    L_min <= D - delta <= L_max,

while it cannot anticipate its own onset at any strictly positive lead.
This is an elementary identity, not a new theorem. Completion forecasting can
still be useful for a broadcaster or for predicting the result of an ongoing
attempt. The error is describing that success as evidence of pre-contact
anticipation without measuring pre-contact anticipation.

For a completion-positive interval [T − H, T − L], its continuous-time fraction
on or after first contact is

    max(0, min(D, H) - L) / (H - L).

This geometric overlap is not the fraction of a trained model's performance
caused by contact information. Establishing that requires the model's alarms,
features, and a controlled comparison.

## What the executable audit measures

`research/objective_onset.py` independently segments positive objective damage
and scores one-to-one alarm/event matches. The reactive baseline reads only
past damage, uses a 60-second cooldown, and cannot use future kills or offline
episode closure. It has no learned weights or threshold search.

Episodes split after a damage-free gap greater than 10 seconds, or at an
objective death. Sensitivity gaps are 5, 20, and 30 seconds. Episodes with a
long quiet follow-up and no death are called **non-terminal damage episodes**.
They might represent a reset, a probe, a disrupted attack, or a strategic
withdrawal. The code does not pretend to identify which. Episodes at the end
of an incomplete follow-up are right-censored.

Both target systems score the identical alarm stream:

- Completion: every observed objective kill is an event.
- Contact onset: every damage-episode onset is an event, including episodes
  without an objective kill.

The audit crosses four gap definitions, three fixed delivery delays (0, 1,
and 5 seconds), and two lead windows (5–60 and 20–60 seconds). These are
sensitivity analyses, not independent experiments or additional matches.
Five seconds relates to short-horizon MOBA warning work; 20 seconds preserves
the stricter minimum in the existing League project.

The initial public export contains replay ticks without a pause clock. Its
results are explicitly nominal tick-time results. A separate raw-replay corpus
uses Gem's observed pause clock, verifies the raw replay SHA256, rejects parse
errors and missing game endpoints, and checks objective counts/times against
the saved OpenDota parse. The two parsers are a consistency check on the same
game, not two independent observations.

## Data obtained and what remains missing

Source: [Gem replay parser](https://github.com/whanyu1212/gem-dota), pinned commit
`e276f3ea5e77b5b8652a68ef7687b5c494592853`.

The first sample is its complete public `examples/ti14_sample.json`, match
8461735141, SHA256
`cc0011910cd1996ceed947d9833b7f05a08a6ec7796cd8bf641f11a7cd7a23b5`.
The expansion attempts every one of the nine entries in the pinned parser
fixture manifest, including entries marked deprecated. The list was selected
for upstream parser testing, not representativeness. Download or parsing
failures stay in an acquisition ledger. No result-based exclusion is allowed.

These are Dota replays used to test measurement feasibility. They are not
League matches, a training set, a held-out population test, or evidence about
League model performance. The current 36,000-match League collection contains
valuable completion labels but does not identify objective damage onset from
the normalized minute-spaced participant states and kill events. Its aggregate
reports cannot supply the missing onset labels. Inventing between-frame paths
would not fix this.

The next League collection needs actual objective damage/health-reset logs or
replay/video annotations with timing uncertainty. It must retain complete games
and all attempts, not sample clips solely around successful kills. A separate
visibility stream is necessary for player-facing claims. Observer-only
post-match analysis remains possible without pretending to know player vision.

## Advancement experiment: freeze before acquiring confirmation data

The following is a proposed protocol. It has not been externally registered,
and the data and model results do not yet exist.

1. **Validate the target.** On at least 100 independently selected engagement
   episodes, compare extracted damage onsets and quiet-gap closures with replay
   inspection. Include non-terminal and contested episodes. Record onset
   uncertainty and disagreement. Keep the label audit separate from selecting
   model parameters. Damage episodes remain operational labels even if experts
   disagree about strategic intent.
2. **Collect a usable cohort.** Begin with at least 500 complete matches and
   1,000 observed objective episodes across multiple patches. These are planning
   floors, not a power guarantee. Estimate the paired match-level variance from
   a development subset, then freeze the confirmation sample size and split.
   Keep series and repeated-player/team dependence in the split/inference plan.
3. **Run strong controls.** Include clock/spawn rules, past event history,
   individual-state tabular history, a capacity-matched interaction model, a
   temporal sequence model, TLS/dynamic-survival objectives, and the immediate
   damage detector. Match training data, observation access, action times,
   cooldown, and tuning budget. Multi-state survival is an established baseline,
   not the proposed novelty by itself. If completion-only risk distillation is
   developed, include a faithful RiskProp-style control and state the mismatch
   between monotone escalation and interrupted/recurrent engagements.
4. **Separate information questions.** Report observer-information results
   first. With authoritative visibility, evaluate each team's available view
   independently. Downsample genuinely dense observations to 1/10/30/60-second
   cadences; do not upsample sparse frames. Never feed future outcomes or
   episode-success labels to a predictor.
5. **Use useful-warning criteria.** Primary endpoint: pre-contact event recall
   at 20–60 seconds with at most one unmatched alert per match, per prespecified
   domain. Tune on development matches and freeze once. Match-bootstrap paired
   differences; report match-level burden distributions and uncertainty. Final
   validation uses unseen patches and includes non-terminal onsets.
6. **Demand a substantial result.** A candidate advance should beat the
   strongest eligible control by at least five absolute recall points, with a
   paired 95% interval excluding zero, while meeting the alert budget. This is
   a chosen practical gate, not a definition of a breakthrough. Report the
   entire registered comparison family and adjust confirmatory inference for
   any multiple primary comparisons.

Reject or narrow the proposed contribution if the gain depends on ongoing
contact, omniscient information unavailable to the intended user, weak controls,
unreliable onset labels, future outcome selection, or disappears on a future
patch. If the models cannot anticipate onsets, publish that information limit
as an empirical finding, without turning a negative result into a fictional
methodological breakthrough.

## Reproduction

Use Python 3.12. No GPU is needed for the audit.

```bash
git clone --depth 1 https://github.com/whanyu1212/gem-dota.git /tmp/gem-reference
git -C /tmp/gem-reference fetch origin e276f3ea5e77b5b8652a68ef7687b5c494592853
git -C /tmp/gem-reference checkout e276f3ea5e77b5b8652a68ef7687b5c494592853

# Run inside this research repository, in an environment with these packages.
# Execution used python-snappy 0.7.3, zstandard 0.25.0, protobuf 7.36.2.
PYTHONPATH=.:/tmp/gem-reference/src python -m research.prepare_objective_corpus \
  --manifest /tmp/gem-reference/tests/fixtures/opendota/manifest.json \
  --cache-dir data/external/objective-onset/replays \
  --output-dir data/external/objective-onset/contacts --workers 2

# Supply only match JSONs, not acquisition.json, to the audit command.
PYTHONPATH=. python -m research.run_objective_onset_audit \
  data/external/objective-onset/contacts/[0-9]*.json \
  --source-revision e276f3ea5e77b5b8652a68ef7687b5c494592853 \
  --output reports/local/objective-onset-corpus.json

PYTHONPATH=src:. python -m pytest tests/test_objective_onset.py --no-cov -q
```

The upstream repository licenses its code under MIT. The audit does not claim
ownership of Valve's game assets or broad redistribution rights over replays.
Raw replays stay outside version control; the report contains derived numeric
facts, source hashes, and reproduction instructions.
