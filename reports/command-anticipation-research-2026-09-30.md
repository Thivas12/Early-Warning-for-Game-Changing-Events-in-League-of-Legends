# Command-stream anticipation: completed third public-data screen

**Advancement gate: FAIL. No breakthrough or state-of-the-art claim.**

This experiment tests whether recorded movement destinations improve prediction of
Roshan damage onsets beyond observed positions and command frequency. It was
declared after two unsuccessful feature studies. The earlier results remain intact.

## Data actually used

Exactly 250 new matches were selected before download, disjoint from all 500
previously selected matches and ten schema-development matches. 145 fresh
matches passed the unchanged base checks and new command checks. Development
retained 109 training and
37 calibration matches.

Across this experiment's retained development and evaluation data: 4,891,140
hero-state rows, 18,914,838 live-game command rows,
and 80,473 decision rows. These are repeated
observations within matches, not independent samples. The original development
matches are reused and must not be counted again as new data.

Fresh evaluation: 131 quiet-gap onsets and
40,390 decisions. Quality exclusions: {'missing_movement_destination': 1, 'unverified_pause_clock': 91, 'entity_hp_loss_without_combat_damage': 11, 'onset_without_entity_hp_confirmation': 3}.

The largest retained evaluation league is Destiny League: 97/145 matches. Source PROFESSIONAL labels
do not establish elite-tournament or independent-team generalization. The full
league breakdown is recorded in the machine-readable result and source metadata.

## Frozen comparison

The lead window is 20-60 seconds, cooldown 60 seconds, and each unmatched
alarm counts toward the one-per-match budget. All thresholds are selected on
calibration only. One fixed seed is used; previous seed repetitions produced
identical policies. Both selection and model weights were frozen before scoring.
Calibration selected **history** as the comparator.
Exact prior-policy reproduction is not expected: command quality exclusions changed the development cohort. Every paired model was refit on the same retained data.

| Model | Inputs | Calibration hits | Fresh onset hits | Recall | Unmatched/match | Hits with 5s delivery delay |
|---|---:|---:|---:|---:|---:|---:|
| clock | 5 | 1/29 | 4/131 | 3.05% | 0.193 | 5 |
| current | 77 | 3/29 | 6/131 | 4.58% | 0.366 | 5 |
| history | 197 | 5/29 | 14/131 | 10.69% | 0.552 | 12 |
| coordination | 225 | 4/29 | 4/131 | 3.05% | 0.234 | 5 |
| command_rate | 101 | 4/29 | 4/131 | 3.05% | 0.303 | 3 |
| command_destination | 146 | 4/29 | 11/131 | 8.40% | 0.634 | 9 |
| rotated_destination | 146 | 3/29 | 0/131 | 0.00% | 0.179 | 1 |

Primary candidate: **command_destination**. Paired recall differences:

- Versus history: -2.29 percentage points; match-bootstrap 95% [-8.97, +4.20], calendar-day [-9.52, +4.43] (47 days). Pass: False.
- Versus rotated_destination: +8.40 percentage points; match-bootstrap 95% [+4.28, +13.10], calendar-day [+3.81, +13.43] (47 days). Pass: True.

The strongest fresh-test baseline by hits was history with 14 hits.
That descriptive observation does not replace the calibration-selected comparator.
The intervals are exploratory percentile bootstraps, not a multiple-experiment
error guarantee. Day clusters do not establish independence between teams.

## First engagement versus re-engagement

This secondary check was declared before fitting. It counts only the first
positive damage in each Roshan life, resetting after a Roshan death. All alarms
and thresholds stay fixed; there is no recalibration to this stricter target.

| Model | First-contact hits | Recall | Unmatched/match |
|---|---:|---:|---:|
| clock | 0/96 | 0.00% | 0.221 |
| current | 4/96 | 4.17% | 0.379 |
| history | 6/96 | 6.25% | 0.607 |
| coordination | 2/96 | 2.08% | 0.248 |
| command_rate | 2/96 | 2.08% | 0.317 |
| command_destination | 6/96 | 6.25% | 0.669 |
| rotated_destination | 0/96 | 0.00% | 0.179 |

## Raw-source validation and interpretation

All 74,276 commands in training replay 7616388415 exactly match
independently decoded raw protobuf fields and ticks. The canonical column
issuer_player_id is actually the raw message entindex; it is used only as an
anonymous issuing-entity key. Selected units are missing from the derivative,
so these commands cannot safely be joined to hero slots or called hero intentions.

Among 51,129 single-selected-hero movement checks, applying +16384
to XY gives median subsequent-position distance 371.4
units and 1,236 matches within 50 units. Without the
conversion, median distance is 23161.7 and none are within
50 units. Subsequent positions are used only for this coordinate diagnostic,
never as forecast inputs. This validates one replay, not every source field.

Only prior commands and the currently observed objective position enter features.
The rotated-destination control retains timing, issuer, command rates and model
capacity while corrupting map location. It is a diagnostic, not a causal test.
Commands may involve heroes, couriers, illusions or other selected units; an
order need not execute. Visibility and real-time delivery were not established.

## Novelty assessment

This is a controlled feature experiment with an established tree learner. It
does not establish a new learning algorithm. Intent-related proxies already
appear in [Tot et al.'s camera-based fight prediction](https://ieee-cog.org/2021/assets/papers/paper_101.pdf).
[Yang et al.](https://arxiv.org/abs/2012.09424) already study multi-event prediction
with rich MOBA state features and attribution. [T-Foresight](https://www.sciencedirect.com/science/article/pii/S2468502X25000440)
studies trajectory-based strategy interpretation; only its abstract was accessible
here. These sources preclude claiming that forecasting player plans in MOBAs is
new merely because this experiment uses a different input stream.

Even a passing screen would need independent replication, stronger external
baselines, sensor-availability validation, and broader tournament coverage.
No result here evaluates League of Legends or opens its private final test.

## Reproduction and evidence

Complete the original precontact protocol to reconstruct training/calibration
arrays. Use the pinned dependencies in research/command-requirements.txt.
The canonical dataset is pinned to 29aca0551be317948d0a181e9630c9a583fadc32.
Raw verification also needs Gem e276f3ea5e77b5b8652a68ef7687b5c494592853 on PYTHONPATH
and the archived training replay from the preceding raw-verification step.

```bash
python -m research.acquire_command_anticipation --plan-only
python -m research.acquire_command_anticipation
python -m research.verify_command_stream
python -m research.command_features
# In a fresh reproduction checkout, preserve the published freeze first:
mv reports/command-anticipation-freeze-2026-09-30.json reports/command-anticipation-freeze-published.json
python -m research.run_command_anticipation fit
python -m research.run_command_anticipation score
python -m research.audit_command_first_contact
python -m research.summarize_command_anticipation
```

Fit intentionally refuses to overwrite frozen artifacts. To reproduce, use a
separate checkout/output workspace and preserve the published evidence files.
The cohort, acquisition hashes, exclusions, per-match alarms, frozen thresholds,
paired intervals and raw validation are in adjacent command-*.json files.
The downloaded replays, Parquet data and model binary are not committed.

## Subsequent development-only experiment

After seeing the negative fresh result, a separate protocol asked whether
commands add value when combined with the full history model. It used only
109 training and 37 calibration matches. Three additional models were fit;
the hash-verified history baseline was reused. The 145-match evaluation was
not scored with these models.

| Development model | Features | Calibration hits | Unmatched/match |
|---|---:|---:|---:|
| history | 197 | 5/29 | 0.865 |
| history_rate | 221 | 4/29 | 0.676 |
| history_destination | 266 | 5/29 | 0.784 |
| history_rotated | 266 | 5/29 | 0.973 |

The pre-fit resource gate required at least three additional calibration hits
over each comparator within the same budget. Advance to a new evaluation: **False**. Calibration is development evidence,
not independent validation or a discovery claim. No new evaluation cohort was
acquired for this unsuccessful variant.

Reproduce this separate stage after preserving its published JSON under a
different filename: `python -m research.run_command_history_screen`. Then rerun
the summary generator. Its protocol is in
[command-history-development-screen.md](../docs/command-history-development-screen.md).

Research decision: neither the current-state nor full-history command
augmentation currently supports an incremental-gain claim. Correct command
locations do carry signal relative to the deliberately incorrect-location
control, but this evidence does not justify a novelty or breakthrough claim.
Further work needs a stronger hypothesis and a new frozen test cohort; repeated
tuning on these evaluation results would not produce independent evidence.
