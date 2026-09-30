# Public-data objective training: completed development experiments

**Advancement decisions: {'small': False, 'expanded': False}. No breakthrough or generalization claim.**

The experiment tests whether learning through the actual 60-second alarm
cooldown adds value beyond established classification and temporal-score losses.
Both data sizes, losses, seeds, training schedules and advancement gates were
declared before the first objective-training score. All 42 final neural fits,
six shared warm starts and two tree fits completed. No evaluation split was loaded.
A subsequently declared shared-threshold follow-up added six final fits, for
**48 completed final neural fits** in total. All results are retained below.

## Data and independent events

The original 109 training matches contain 29,249 decision rows but just 76
eligible Roshan damage onsets. Seventy-five onsets have eight eligible warning
rows; one has nine. Unequal per-event positive-row multiplicity is too small
to explain the previous failures. Row counts overstate the independent evidence.

Exactly 600 additional training and 150 additional calibration candidates were
selected by outcome-independent hashes, disjoint from all 750 previously
selected matches and ten schema-development matches. All are earlier than the
original evaluation period. Existing strict clock, coverage, identity and
combat-versus-health checks were applied without changing exclusion rules.
New retained matches: 449/750. New hero-state rows: 7,561,480. Exclusions: {'unverified_pause_clock': 260, 'incomplete_or_duplicate_hero_frame': 2, 'entity_hp_loss_without_combat_damage': 27, 'onset_without_entity_hp_confirmation': 7, 'metadata_duration_disagreement': 5}.
Retained additions by league: {'Destiny League': 347, 'Dota 2 Space League': 35, 'Party To Play league': 16, 'SIVVIT League': 16, '互联网联赛': 14, 'DOTA2-Ticu梦幻联赛': 11, 'EPL World Series: Southeast Asia 2024-2025 Season ': 5, 'WBT CYBER CLUB #1': 4, '天蝉杯': 1}.
Source league labels do not establish elite-tournament generalization.

| Development dataset | Train matches | Train onsets | Train decisions | Calibration matches | Calibration onsets | Calibration decisions |
|---|---:|---:|---:|---:|---:|---:|
| small | 109 | 76 | 29,249 | 37 | 29 | 10,834 |
| expanded | 449 | 378 | 123,441 | 146 | 127 | 41,098 |

Expanded data include the original development matches; these two experiments
are not independent replications. Matches and days may share players and leagues.
Both training and calibration cohorts expand, so the two tables alone do not
isolate a training-set-size effect on a fixed calibration population.
No result here evaluates League of Legends or opens its private final test.

## Matched comparisons

All neural arms use the same 197 history features, train-only normalization and
missingness masks, two 64-unit GELU layers, optimizer, batch order and common
10-epoch BCE warm start. Each arm then trains for 30 epochs. The final epoch is
used without validation checkpoint selection. Seeds are 17, 29 and 43.
Thresholds maximize calibration hits under at most one unmatched alarm per
match using the same frozen search. All alarms use a 60-second cooldown and
one-to-one credit for a target 20-60 seconds ahead. False, early, late and
duplicate unmatched alarms all consume the budget.

### Small data: 29 calibration onsets

| Loss | Hits, seed 17 | Hits, seed 29 | Hits, seed 43 | Mean recall | Unmatched/match range |
|---|---:|---:|---:|---:|---:|
| bce | 1 | 3 | 1 | 5.75% | 0.108-0.784 |
| weighted_bce | 1 | 3 | 2 | 6.90% | 0.108-0.838 |
| sol_f1 | 3 | 3 | 3 | 10.34% | 0.784-0.865 |
| wsol_f1 | 4 | 2 | 2 | 9.20% | 0.270-0.649 |
| wsol_tss | 3 | 4 | 3 | 11.49% | 0.757-0.973 |
| independent_utility | 3 | 4 | 1 | 9.20% | 0.108-0.973 |
| cooldown_utility | 6 | 7 | 6 | 21.84% | 0.838-0.919 |
| Fixed HGBT history | 5 | — | — | 17.24% | 0.865 |

The HGBT control has one fixed seed and is not a three-seed mean.

| Seed | Primary hits | Best control hits | Difference in recall | Gate |
|---|---:|---:|---:|---|
| 17 | 6 | 5 | +3.45 pp | FAIL |
| 29 | 7 | 5 | +6.90 pp | FAIL |
| 43 | 6 | 5 | +3.45 pp | FAIL |

### Expanded data: 127 calibration onsets

| Loss | Hits, seed 17 | Hits, seed 29 | Hits, seed 43 | Mean recall | Unmatched/match range |
|---|---:|---:|---:|---:|---:|
| bce | 6 | 6 | 10 | 5.77% | 0.863-0.993 |
| weighted_bce | 5 | 5 | 6 | 4.20% | 0.425-0.966 |
| sol_f1 | 10 | 9 | 10 | 7.61% | 0.788-0.918 |
| wsol_f1 | 8 | 9 | 9 | 6.82% | 0.664-0.952 |
| wsol_tss | 11 | 9 | 8 | 7.35% | 0.897-0.993 |
| independent_utility | 9 | 16 | 6 | 8.14% | 0.815-0.938 |
| cooldown_utility | 11 | 10 | 7 | 7.35% | 0.575-0.884 |
| Fixed HGBT history | 10 | — | — | 7.87% | 0.952 |

The HGBT control has one fixed seed and is not a three-seed mean.

| Seed | Primary hits | Best control hits | Difference in recall | Gate |
|---|---:|---:|---:|---|
| 17 | 11 | 11 | +0.00 pp | FAIL |
| 29 | 10 | 16 | -4.72 pp | FAIL |
| 43 | 7 | 10 | -2.36 pp | FAIL |

The small-data gate requires at least 8/29 hits and at least three more hits
than every control for EACH seed. The expanded gate requires at least 25%
recall and a gain of at least 10 percentage points over every control for EACH
seed. These are predeclared resource gates, not significance tests. Calibration
has been consulted repeatedly; neither a passing seed nor a mean improvement
would constitute held-out evidence. No confidence interval based on only three
seeds should be read as uncertainty over the match population.

## Post-fit diagnostic: training credit versus calibration burden

This descriptive audit was added after the small-cohort results, without changing
models, thresholds or advancement decisions. Every saved checkpoint must exactly
reproduce its originally recorded deterministic calibration policy. The following
ranges span the three cooldown-utility seeds using their RAW sigmoid probabilities
as Bernoulli alarm proposals, without the subsequent threshold calibration.
These stochastic values are not the deployed metrics in the tables above.

| Data | Split | Expected stochastic recall range | Expected unmatched/match range |
|---|---|---:|---:|
| small | train | 94.69%-95.89% | 0.551-1.118 |
| small | calibration | 25.22%-30.84% | 2.251-3.158 |
| expanded | train | 74.66%-80.94% | 0.580-0.775 |
| expanded | calibration | 12.53%-14.67% | 1.632-1.930 |

A learned training multiplier is not a finite-sample budget guarantee, and
optimizing expected training credit does not ensure transfer to later matches.
The audit also records deterministic training metrics at the unchanged
calibration-selected threshold. Training performance is optimistic by construction.

## Interpretation and novelty boundary

Exact refractory emission credit is an established renewal identity. Optimizing
it is a candidate training objective, not a new theorem. Its value and gradients
were independently checked against exhaustive Bernoulli-policy enumeration and
actual one-to-one event matching, including overlapping target windows. Padding
and match boundaries were tested. The full focused suite passed 47 tests before
fitting. Loss definitions and training schedules stayed fixed; thresholds
were selected by the predeclared calibration search.

The stochastic training objective differs from deterministic threshold deployment.
Thus exact expected training credit does not imply optimal deployed decisions.
This experiment does not rule out other encoders, schedules or utility policies.
It tests the declared candidate under a controlled, limited training budget.

[Temporal label smoothing](https://proceedings.mlr.press/v202/yeche23a.html) and
[dynamic survival prediction](https://proceedings.mlr.press/v248/yeche24a.html)
already address useful event timing. The [wSOL paper](https://arxiv.org/pdf/2606.23145)
compares temporal confusion-score losses using a common TCN and explicitly
reports dataset-dependent gains. Here the same loss equations are applied to
an MLP, with valid confusion counts pooled across matches while temporal shifts
remain inside each match. This adaptation avoids ignoring event-free matches.
It agrees with the author-checked reference on individual unpadded sequences;
it is not a reproduction of that paper's architecture or benchmark results.
The fixed three-lag wSOL control does not represent all possible temporal weights.

[Horizon-aware disruption work](https://arxiv.org/html/2609.24443v1) likewise
compares established horizon objectives under a common causal encoder. Merely
changing the domain to games cannot establish methodological novelty.

## Subsequent shared-threshold experiment

After inspecting the first study's training/calibration gap and policy mismatch,
a separate protocol replaced independent Bernoulli proposals with ONE uniform
threshold shared across each match. Every threshold uses the exact deployed
causal cooldown policy. Counts are integrated exactly over score intervals.
The implementation uses the established sorted-increment Lovasz extension of
an alarm-count set function, without claiming submodularity or convexity.
This is an application of existing mathematics, not a new extension theorem.
The protocol and verified implementation were published in commit
adc1f070b83bb41f007ac11d091864e8784940f3 before these six fits started.

Ten additional tests independently integrated actual emitted alarm policies
and checked numerical gradients, ties, padding, boundaries and overlapping
events. The combined focused suite passed 57 tests. Each follow-up reused the
same saved warm start, preprocessing, optimizer, batch order, 30-epoch schedule
and final calibration search. All seven original arms are controls here.

| Data | Seed | Hits | Recall | Unmatched/match | Best control hits | Gate |
|---|---:|---:|---:|---:|---:|---|
| small | 17 | 5/29 | 17.24% | 0.838 | 6 | FAIL |
| small | 29 | 4/29 | 13.79% | 0.568 | 7 | FAIL |
| small | 43 | 5/29 | 17.24% | 0.811 | 6 | FAIL |
| expanded | 17 | 10/127 | 7.87% | 0.877 | 11 | FAIL |
| expanded | 29 | 13/127 | 10.24% | 0.753 | 16 | FAIL |
| expanded | 43 | 10/127 | 7.87% | 0.973 | 10 | FAIL |

The thresholds are still selected on calibration. Integrating over all training
thresholds is not the same as optimizing the eventual selected threshold.
Matching the policy mechanism cannot by itself solve distribution shift or
overfitting. These data do not identify which remaining limitation dominates.
The follow-up uses the same development matches and is not independent validation.
Its declared gates are unchanged in form, with the original cooldown arm now
also included among the controls. Full records and weight hashes are in the
adjacent shared-threshold JSON files; saved policies were checked again by the
post-fit audit. None of these experiments supports a breakthrough claim.

Reproduce the follow-up with research/shared-threshold-requirements.txt after
preserving its published result/freeze files in a separate checkout:

```bash
python -m research.run_shared_threshold
python -m research.run_shared_threshold --expanded
python -m research.audit_objective_fit --shared
python -m research.audit_objective_fit --shared --expanded
```

## Reproduction

Reconstruct the original command-study development arrays first. Install the
pinned dependencies in research/command-requirements.txt and the CPU Torch build
in research/objective-training-requirements.txt. Use PYTHONPATH=.:src.
Preserve published objective-training JSON files under other names in a separate
reproduction checkout: the runner refuses to overwrite changed frozen inputs
or resume without the bound local checkpoints. Binary weights and raw data are
not committed. Code, protocols, source hashes and all result records are committed.

```bash
python -m research.acquire_objective_expansion --plan-only
python -m research.acquire_objective_expansion
python -m research.precontact_data \
  --root data/external/betty-objective-expansion \
  --manifest reports/objective-expansion-cohort-2026-09-30.json \
  --output-dir data/processed/objective-expansion \
  --report reports/objective-expansion-quality-2026-09-30.json
python -m research.public_objective_training
python -m research.public_objective_training --expanded
python -m research.audit_objective_fit
python -m research.audit_objective_fit --expanded
python -m research.run_shared_threshold
python -m research.run_shared_threshold --expanded
python -m research.audit_objective_fit --shared
python -m research.audit_objective_fit --shared --expanded
python -m research.summarize_objective_training
```

The adjacent objective-training-{small,expanded} JSON files contain all 42
loss histories, thresholds, calibration counts, seed gates and checkpoint hashes.
The quality report records every included or excluded candidate and source hash.
