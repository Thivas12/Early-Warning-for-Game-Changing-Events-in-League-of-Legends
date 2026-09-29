# Coordination signal screen: the first experiment

Status: implementation ready; private-data results pending. This is an
exploratory experiment designed after reviewing patch 16.16 calibration
results. It does not establish novelty, state of the art, or test performance.

## Scientific purpose

Test whether recent identity-linked player movement improves useful Dragon
warnings after providing objective history, current geometry and recent state
history. This is the first gate for the proposed research on anticipating team
coordination under sparse observations and patch changes.

A positive result motivates a learned probabilistic coordination representation.
A negative result rejects these engineered summaries at the tested capacities;
it does not establish that no learnable coordination signal exists. No result
from this screen identifies players' intentions or a causal effect of movement.

## Four matched comparisons

All models use the same gradient-boosted tree family, training matches, feature
construction, capacity search and warning policy. Historical B3 scores are not
substituted for a matched refit.

| Variant | Inputs | Purpose |
|---|---|---|
| `b3` | The existing 27 B3 features, including clock, resources, objective history and basic spatial spread | Refit reference |
| `snapshot` | B3 plus current position coverage, team centroids, within/across-team distances and pit proximity | Value of richer current geometry |
| `history` | Snapshot plus two preceding observed snapshot vectors and their actual ages | Value of recent state history |
| `coordination` | History plus identity-linked displacement, directional coherence, simultaneous approach to pits and cross-team closing | Incremental value of these coordination summaries |

The primary contrast is `coordination - history`. `history - snapshot` and
`snapshot - b3` are secondary. A gain over B3 alone cannot establish a gain
from coordination.

Features use participant identities only to connect the same player across
observed frames; no account identity becomes an input. Reordering players in
an observation leaves features unchanged. Displacements are endpoint changes,
not instantaneous velocities or reconstructed movement paths. No interpolation
creates new frames. Past frames older than 180 seconds are marked missing.
Approximate pit anchors match the existing M1 constants; they enforce no game
rules. Missing values use zero plus training-fitted missing indicators, with
empty columns retained. The imputer is refitted on the appropriate training
partition during both selection and the final fit.

## Model selection and evaluation

1. Fit candidate capacities on patches 16.12–16.14.
2. Select 7, 15 or 31 leaves using average precision on whole matches from
   patch 16.15; break ties toward fewer leaves. All candidates use 100 boosting
   iterations, learning rate 0.08, minimum leaf size 100 and L2 penalty 1.
3. Refit the chosen capacity on patches 16.12–16.15. Automatic early stopping
   and its random row validation split are disabled. This deterministic tree
   screen uses one fixed seed; repeating identical fits is not new evidence.
4. Tune the warning threshold on the earlier 1,500 calibration matches in each
   route. Evaluate on the later 1,500 per route. These halves remain exploratory
   because aggregate calibration results were previously viewed.
5. Leave all 6,000 patch 16.17 payloads unopened. The implementation has no
   option to train, stage, or score that partition.

Train the original actual-match `Dragon within 60 seconds` target, validated
against exact future onset timestamps. Completed-match negative targets remain
negative. The abandoned boundary-censoring proposal is not applied.

### Warning policy

The frozen grid is the existing 101 logarithmically spaced thresholds from
0.00001 through 1, plus an explicit no-alert policy. Choose the most timely
hits subject to at most one false alert per match on tuning data. Tie-break by
fewer false alerts, fewer late alerts, then higher threshold. Do not retune
using later-half outcomes.

- A warning matches one unique subsequent Dragon onset within 60 seconds.
- A matched lead of **20–60 seconds** is timely; a shorter lead is late.
- An unmatched alert is false. Late alerts are reported separately and do
  not count as false under this definition.
- The new experiment allows alerts exactly 60 seconds apart. This is an
  explicit new convention; the frozen M1 evaluator is unchanged.
- Timely recall uses **all Dragon onsets** as denominator. Also report recall
  conditional on a genuine frame in the eligible 20–60-second window.
- Report realized evaluation false-alert burden. Meeting the tuning budget
  does not guarantee meeting it under temporal shift.

Report AP, Brier score, ordinary and timely recall/precision, late/false alerts
per match, false-alert quantiles and lead-time median/p10. Route-stratified
paired whole-match bootstrap intervals use 2,000 draws. They are conditional
on these fitted models and selected policies. They do not quantify uncertainty
from model selection, repeated players, or a population of future patches.
Three exploratory contrasts do not become confirmatory claims through their
unadjusted intervals.

## How this controls effort

This screen uses CPU training and no new collection. Feature staging commits
one checksum-bound shard per 100 matches. Restarting skips completed shards
and completed model results. A failed partial shard or model is rebuilt;
completed artifacts with changed hashes are rejected. Disk-backed matrices
avoid assembling all features in Python object lists. Tree fitting and
imputation still allocate working memory beyond the feature-file size.

The runtime freeze records protocol, source hashes, dependency versions,
processed audit, processing manifest and split checksums before any fitting.
It is a reproducibility record for an exploratory screen, not retrospective
preregistration. Original model, label and metric artifacts are untouched.

## Running in the existing research checkout

Prerequisites are the existing processed matches, `final-split.json` and
`final-processed-validation.json`. The archived raw collection and graph
shards are not required. No new package dependency is introduced.

- `make freeze-coordination-screen` binds the local inputs and reports feature
  storage size without opening match payloads.
- `make coordination-screen` stages remaining data and fits one remaining
  variant. Repeat to resume. `MAX_NEW_SHARDS=10` limits new staging work;
  `MAX_NEW_MODELS=0` completes all remaining models.
- `make start-coordination-screen` starts all remaining work detached from the
  terminal, with one-run locking. `make coordination-screen-status` shows the
  log, exit status and completed model count. Closing the terminal is safe.
- `make coordination-screen-smoke` runs public synthetic positive and negative
  controls. These are software checks, not evidence about real League games.

Default outputs are private under `data/private/coordination-screen-v1`.
`summary.json` contains identifier-free metrics and paired comparisons;
per-model artifacts include the full tuning curve, selected capacity,
probabilities and match offsets. Source data and fitted model files stay
private. The public synthetic report explicitly sets
`new_private_model_results: false`.

## Decision after the real run

Read the primary paired contrast together with realized alert burden, Brier
score and opportunity. A point gain with a broad interval is inconclusive.
A gain that exceeds the alert budget does not meet the operational objective.
If history helps but coordination adds little, investigate a learned player-set
history control before increasing graph complexity. If coordination adds
material value, the next method experiment models uncertainty over future
coordination and tests controlled observation removal and untouched patch
transitions. The 10-percentage-point recall ambition is a proposed later
success target, not an achieved result or this screen's significance threshold.
