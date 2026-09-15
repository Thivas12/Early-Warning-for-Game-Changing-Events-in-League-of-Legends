# Legacy MSc v1 audit

**Decision:** preserve the original work as an historical artifact, but reject
its reported model scores as evidence of out-of-sample early-warning ability.

This decision is based on executable checks in `league_ews.audit` and
`league_ews.diagnostics`. It is not a criticism of using notebooks for
exploration; it is a criticism of information flow and evaluation design.

## Artifact identity

| Property | Value |
|---|---:|
| Released table | `final_dataset.csv` |
| SHA-256 | `dd2b2dffc95ca182792ee679b458c362469e99b975f8361124900f050f64ffc0` |
| Rows | 484,255 |
| Columns | 86 |
| Matches | 2,998 |
| Base sequence windows | 74,728 |
| Windows after jitter copies | 224,184 |

The dataset is not committed. The hash identifies the separate Kaggle artifact
used for this audit.

## Critical findings

| Finding | Direct evidence | Consequence | v2 correction |
|---|---|---|---|
| Post-match leakage | 16 final match-summary columns are repeated at every prediction timestamp. | The input includes facts that were not known at prediction time. | Feature allowlist derived only from timeline observations at or before the cutoff. |
| Generator defaults | All 11 health/alive/objective-count fields are constant. Missing health became zero, which made every player appear low-health. | The advertised state representation is partly fictional. | Missing fields stay missing; objective ownership uses `killerTeamId`; unsupported health is excluded. |
| Split contamination | The notebook creates overlapping windows, makes two jitter copies, and only then calls random row splits. | Nearly identical observations occur across train, validation and test. | Split complete matches before transformations. |
| Global preprocessing | `StandardScaler.fit_transform` is called before the random split. | Validation and test distributions influence training preprocessing. | Fit transforms on training matches only. |
| Synthetic cadence | Core participant snapshots change in only 16.7% of the ten-second rows. | A ten-second table does not imply ten-second source observations. | Preserve native Riot frame cadence and exact event timestamps. |
| Ambiguous teamfight proxy | Every kill that begins a ten-second interval containing at least three kills is added as a fight. | One combat episode can create multiple pseudo-events. | Cluster kill events into disjoint episodes and emit one onset time per episode. |
| No patch key | No game-version field is present. | Patch drift cannot be measured or controlled. | Store full `gameVersion`; use future-patch holdouts. |
| Row-centric warning demo | A warning is called a hit when the current row label is positive, and fixed thresholds are chosen manually. | Repeated positive rows and multiple warnings can over-count one event. | Upward crossings, cooldowns, validation-only thresholds and one-to-one event matching. |

## Quantified contamination

The diagnostic recreates the exact sequence length (40), step (5), three-copy
augmentation and two `train_test_split(..., random_state=42)` calls without
allocating the feature tensors.

| Partition | Examples | Same window family elsewhere | Same match elsewhere | Overlapping time window elsewhere |
|---|---:|---:|---:|---:|
| Train | 161,412 | 48.47% | 100.00% | 100.00%* |
| Validation | 40,353 | 96.83% | 100.00% | 100.00% |
| Test | 22,419 | 99.10% | 100.00% | 100.00% |

\* 99.998% before rounding.

## Leakage-safe baseline results

Matches are ordered by the numeric portion of the legacy match ID, then split
70/15/15 into 2,098/450/450 complete matches. Match ID is only a chronology
proxy because the release omits creation time. Thresholds maximize event-level
F1 on validation only. Each alert is an upward threshold crossing with a
60-second cooldown and can match at most one event in the next 30 seconds.

| Features | Event | Test ROC-AUC | Test AP | Alert precision | Alert recall | Alert F1 | False alerts/game |
|---|---|---:|---:|---:|---:|---:|---:|
| Time only | Baron | 0.960 | 0.143 | 0.213 | 0.225 | 0.219 | 0.49 |
| History | Baron | 0.989 | 0.487 | 0.316 | 0.419 | 0.361 | 0.54 |
| Causal tabular | Baron | 0.990 | 0.494 | 0.344 | 0.416 | **0.376** | 0.47 |
| Time only | Dragon | 0.672 | 0.101 | 0.097 | 0.125 | 0.109 | 3.26 |
| History | Dragon | 0.954 | 0.526 | 0.440 | 0.369 | 0.401 | 1.31 |
| Causal tabular | Dragon | 0.959 | 0.562 | 0.515 | 0.348 | **0.415** | 0.91 |
| Time only | Teamfight | 0.674 | 0.171 | 0.086 | 0.089 | 0.087 | 2.39 |
| History | Teamfight | 0.740 | 0.266 | 0.123 | 0.165 | 0.141 | 2.97 |
| Causal tabular | Teamfight | 0.743 | 0.271 | 0.123 | 0.188 | **0.149** | 3.37 |

The headline lesson is operational: a 0.990 row-level ROC-AUC for Baron becomes
0.376 event-level alert F1. Teamfight remains unusable at the tested operating
point. Median lead time for the causal models is 20 seconds.

A diagnostic using only the 16 post-match summary fields produced zero useful
alerts on the test set. This negative result does not make those fields valid;
it shows that final summaries alone do not localize an event in time.

## What this audit does not prove

- It does not estimate future-patch generalization because patch metadata is
  absent.
- It does not validate the reconstructed timer resets against raw event JSON.
- It does not compare neural models fairly; the purpose is to establish a
  leakage-safe floor.
- It does not provide confidence intervals yet. Those are preregistered for the
  rights-cleared v2 dataset using match-cluster bootstrap resampling.

Machine-readable evidence is in `reports/legacy-audit.json`,
`reports/legacy-split-contamination.json`, `reports/legacy-baselines.json` and
`reports/legacy-postmatch-leak.json`.
