# Registered research plan: RiftHazard

Version 0.1 — frozen before collecting the research-v2 dataset.

## Working title

**RiftHazard: Calibrated, Patch-Robust Forecasting of Strategic Events in
League of Legends with Temporal Interaction Graphs**

The legacy audit can independently become a short reproducibility paper titled
**When 0.99 AUC Is Not an Early-Warning System**. The method paper proceeds only
if the prospective model clears the preregistered gates below.

## Research question

Can a model that treats ten players and map objectives as a changing
interaction graph forecast Baron, Dragon and multi-kill combat episodes 10, 20,
30 and 60 seconds ahead, with calibrated and monotone risk, on matches and
patches not seen during training?

## Falsifiable hypotheses

The causal tabular gradient-boosted model is the primary baseline. All deltas
are evaluated on the same held-out matches.

| ID | Hypothesis | Primary pass criterion |
|---|---|---|
| H1 | Temporal interactions add information beyond clock, history and tabular state. | Mean event AP improves by at least 0.03 absolute and the 95% match-bootstrap CI for the paired delta excludes zero. |
| H2 | Discrete hazards make multi-horizon risk coherent. | Zero monotonicity violations and no worse integrated Brier score than independently trained horizon heads beyond a 0.005 non-inferiority margin. |
| H3 | Patch conditioning reduces temporal drift. | Relative AP loss on the next unseen patch improves by at least 20% versus the same encoder without patch/rule inputs. |
| H4 | Selective abstention protects users under drift. | At matched recall within 0.03, patch-OOD abstention reduces false alerts per game by at least 25%. |
| H5 | The system has plausible coaching utility. | For at least two event types: event recall at least 0.50, precision at least 0.50, median lead at least 20 seconds and no more than one false alert per game. |

Failure of H1–H4 is publishable as a negative benchmark result. Failure of H5
blocks the product transfer even if a model is statistically interesting.

## Outcomes

Primary statistical outcome: macro-average precision across event types and
horizons on the future-patch test set.

Primary operational outcome: event-level F1 after a validation-selected alert
threshold, with one alert matched to at most one event.

Secondary outcomes include ROC-AUC, Brier score, expected calibration error,
calibration slope/intercept, recall, precision, false alerts per game/hour,
median lead time, 10th-percentile lead time, abstention coverage, inference
latency and memory.

Rows are not independent. Confidence intervals and paired comparisons resample
whole matches. Neural experiments use ten fixed seeds; every seed is reported.
The untouched test patch is evaluated once after model and operating policy are
frozen.

## Dataset protocol

### Target sample

- Ranked Solo/Duo matches from two regional routes and at least six consecutive
  patches.
- Target 36,000 valid matches: approximately 3,000 per region-patch cell.
- A 5,000-match pilot may test the pipeline but cannot support final claims.
- Sampling frame and seed construction are recorded before fetching match
  details; duplicate matches are removed before any split.

### Inclusion

- Summoner's Rift, standard ranked queue, ten participants.
- Full Match-V5 detail and timeline payloads available.
- Game version and creation time present.
- Minimum duration fixed before collection after inspecting only the pilot.

### Exclusion

- Remakes, unsupported modes, corrupt/incomplete timelines and duplicated match
  IDs.
- No exclusion based on labels, model score or downstream performance.

### Privacy and rights

Raw payloads remain private and access-controlled. PUUIDs and account mappings
are removed from derived research tables. A public dataset release requires a
separate Riot/publisher review and an explicit licence; otherwise only schemas,
hash manifests and code are released. The non-commercial legacy dataset is not
a product asset.

## Event definitions

- Baron and Dragon: exact `ELITE_MONSTER_KILL` event timestamps and
  `monsterType`.
- Teamfight proxy: a connected episode of at least three `CHAMPION_KILL`
  events, where adjacent kills are no more than ten seconds apart; one onset
  timestamp per episode.
- Sensitivity analyses vary the teamfight minimum kills, gap and participant
  diversity. No definition is selected using test performance.
- Labels use strict future intervals: prediction time < event time ≤ horizon.

## Split protocol

1. Deduplicate complete matches.
2. Order by game creation time and patch.
3. Reserve the newest complete patch as final test.
4. Reserve the preceding patch for calibration/threshold selection.
5. Train on earlier patches with grouped inner validation by match.
6. Detect repeat players across partitions and report a stricter player-component
   holdout sensitivity analysis.
7. Only then generate windows, augmentations, graphs and scalers.

## Model ladder

| Level | Model | Purpose |
|---|---|---|
| B0 | Empirical prevalence | Sanity floor |
| B1 | Match clock / spawn rules | Measures schedule prior |
| B2 | Event history | Measures recurrence/respawn prior |
| B3 | Causal tabular gradient boosting | Strong inexpensive baseline |
| B4 | Temporal convolution/GRU | Tests whether sequence context helps |
| M1 | Temporal graph encoder + discrete competing hazards | Proposed model |
| M2 | M1 + patch/rule representation | Patch-robust candidate |
| M3 | M2 + OOD score/abstention | Selective prediction candidate |

The B4 causal sequence input contract and training boundary are documented in
[`docs/b4-temporal-baseline.md`](b4-temporal-baseline.md). This input contract
does not change the frozen final split or the H1 comparison against B3.

The graph has player and objective nodes; edges encode team membership,
proximity, assistance and objective proximity. Feature availability is
explicit. Health is not inferred from fields absent in the API.

## Mandatory ablations

- remove positions/proximity;
- remove interaction edges but retain node features;
- remove objective nodes;
- remove event history;
- remove patch/rule inputs;
- independent horizon heads versus discrete hazards;
- fixed grid versus native irregular timing;
- no abstention versus OOD abstention;
- teamfight-definition sensitivity;
- time-only and spawn-rule-only controls.

## Gates

| Gate | Evidence required | Status |
|---|---|---|
| G0 Legacy validity | Executable audit and contamination reproduction | Passed: legacy scores rejected |
| G1 Data authority | Fresh Riot key/product registration as applicable; written redistribution decision | Private authority preflight passed; record and credential remain private |
| G2 Data quality | Manifest, schema checks, event spot-checks, patch coverage | Private final validation passed on 36,000 matches with 12-cell human spot-check; report remains private |
| G3 Baselines | B0–B3 with locked splits and confidence intervals | B0–B3 calibration and paired uncertainty complete; B3 versus B2 macro AP gain 0.13609 (95% whole-match interval 0.13061–0.14182). Three B3 alert thresholds frozen; none meets H5 on calibration. Final test pending. See [`reports/rifthazard-calibration-2026-09-26.md`](../reports/rifthazard-calibration-2026-09-26.md). |
| G4 Method | All seeds, ablations, calibration and OOD tests | Pending v2 data |
| G5 Paper | Claims trace to tables; negative results included; independent review | Pending |
| G6 Transfer | H5 utility plus policy, privacy and model-card approval | Pending; product repo not created |

## Stop rules

- Do not use the credential exposed in historical notebooks; it must be
  revoked, not recycled.
- Do not tune on the final patch.
- Do not market row-level AUC as warning utility.
- Do not claim novelty merely from adding attention or a graph network.
- If the graph model misses H1, publish the benchmark/audit and do not invent a
  positive story.
- If H5 fails, do not ship real-time warnings.
