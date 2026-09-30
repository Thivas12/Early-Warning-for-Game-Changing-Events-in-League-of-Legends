# Pre-contact objective forecasting: two completed experimental waves

**Status: exploratory research. No breakthrough or new algorithm is established.**

Audited 500 disjoint public Dota matches. Retained 288 after source checks, with 4,820,790 hero-state rows and 79,247 five-second decision rows. Hero rows are repeated observations, not independent samples.

## Design and order of work

The first wave selected 300 matches by a fixed hash, then split them chronologically 180/60/60 before validation. Quality checks retained 110 training, 37 calibration, and 26 evaluation matches. Model capacity and alert rules were fixed before fitting. All five comparisons used the same feature archive and capacity.

After reading that negative result, the follow-up removed absolute map coordinates and player/team ordering. Its current-state and motion variants were declared before new evaluation scores. Exactly 200 disjoint later-period matches were selected. Training and calibration remained unchanged; 115 new matches passed validation. The original holdout was never added to training or calibration.

The target is observable damage onset after a death or a gap strictly longer than ten seconds. It includes non-terminal attempts. It is not strategic intent or irreversible commitment. Decisions begin at minute five, require 20-60 seconds of lead, use a 60-second cooldown, and receive one-to-one credit. Every unmatched alert counts. The empirical alert budget is at most one unmatched alert per match. The thresholds are chosen using calibration only. Observation scope is an omniscient replay observer.

## First wave: negative result

| Policy | Onset hits | Onset recall | Unmatched alerts / match | Kill recall |
|---|---:|---:|---:|---:|
| clock | 4/23 | 17.4% | 0.462 | 26.3% |
| current | 0/23 | 0.0% | 0.423 | 0.0% |
| history | 0/23 | 0.0% | 0.385 | 5.3% |
| coordination | 1/23 | 4.3% | 0.308 | 0.0% |
| completion_trained | 0/23 | 0.0% | 0.192 | 5.3% |
| reactive first-damage detector | 0/23 | 0.0% | 0.885 | 78.9% |

Coordination minus individual history: +4.35 percentage points; match-bootstrap 95% interval [+0.00, +15.00] percentage points; calendar-day interval [+0.00, +15.79] percentage points. Advancement gate: **False**.

The clock baseline outperformed the proposed full coordination representation. The one additional hit over individual history does not demonstrate a gain. The reactive detector's high completion recall and zero onset recall use the same alarm stream but different target denominators; subtracting those recalls is not a causal decomposition of model skill.

## Fresh-cohort follow-up

| Policy | Onset hits | Onset recall | Unmatched alerts / match | Kill recall |
|---|---:|---:|---:|---:|
| clock | 7/110 | 6.4% | 0.861 | 4.8% |
| current | 11/110 | 10.0% | 0.591 | 8.1% |
| history | 6/110 | 5.5% | 0.513 | 6.5% |
| coordination | 7/110 | 6.4% | 0.617 | 1.6% |
| completion_trained | 1/110 | 0.9% | 0.209 | 3.2% |
| invariant_current | 10/110 | 9.1% | 0.670 | 6.5% |
| invariant_motion | 7/110 | 6.4% | 0.626 | 6.5% |
| reactive first-damage detector | 4/110 | 3.6% | 0.870 | 69.4% |

The comparator selected on calibration was **current**. Invariant motion minus that comparator: -3.64 percentage points; match-bootstrap 95% interval [-10.89, +3.48] percentage points; calendar-day interval [-10.10, +1.92] percentage points. Advancement gate: **False**.

Three fixed seeds (17, 29, 43) were run. Full-feature histogram boosting is deterministic here; identical repeats are not independent replications. The scientific replication is the disjoint match cohort. Complete per-seed and per-match results, including the fixed five-second delivery-delay sensitivity, are in the JSON reports. Original model refits must reproduce their first-wave calibration thresholds and counts exactly.

## Same-encounter completion check

A post-hoc descriptive check restricts both labels to the same completed encounters. On the fresh cohort the reactive detector caught 43 of 62 kills, but anticipated only 3 of those same encounters' damage onsets. Of its credited kill warnings, 41 arrived at or after the corresponding encounter had already started. This rules out different target populations as the sole explanation of the score gap. Incidental warnings of subsequent re-engagements retain their legitimate credit. This is a descriptive mechanism check, not a separately registered discovery test.

| Quiet gap | Same completed encounters | Kill hits | Onset hits | Credited kill warnings at/after onset |
|---|---:|---:|---:|---:|
| 5 s | 62 | 43 | 7 | 38 |
| 10 s | 62 | 43 | 3 | 41 |
| 20 s | 62 | 43 | 3 | 41 |
| 30 s | 62 | 43 | 1 | 43 |

## Data quality and provenance

The older public export's `game_time`, and the canonical combat table's `game_time_sec`, track elapsed replay ticks. They cannot be directly compared with pause-adjusted snapshot times. Some canonical snapshot clocks also advance during pauses and then jump backward. This pilot excludes unresolved pauses; it never silently repairs them.

The schema-development match also has team labels contradicted by pregame combat identities. The adapter derives team membership exclusively from pre-horn records and requires five heroes per team. Gold and net-worth fields are omitted because their hero attribution was not independently verified. Every labeled onset must agree with entity HP loss, and every observed HP loss must have nearby combat damage.

| Exclusion reason | Matches |
|---|---:|
| unverified_pause_clock | 193 |
| entity_hp_loss_without_combat_damage | 12 |
| onset_without_entity_hp_confirmation | 4 |
| incomplete_or_duplicate_hero_frame | 2 |
| metadata_duration_disagreement | 1 |

A separate Gem parse of archived training match 7616388415 matched all 150 target damage/death records exactly. Maximum clock discrepancy across 1438 samples was 0.033301 seconds. One independent parse is a useful check, not certification of every field or match.

## Interpretation and limits

The tree models and engineered geometry are established methods. This work does not establish algorithmic novelty, state of the art, or a breakthrough. The measurement result is that objective-completion recall can substantially reward a detector triggered by damage already underway. Whether this supports a novel benchmark contribution still needs a closer comparison with existing event anticipation evaluations.

The metadata calls the source PROFESSIONAL, but 176 of the first 300 selected matches belong to Destiny League. Repeated teams and players may create dependence beyond calendar-day blocks. Excluding pauses and parse inconsistencies changes the sampled population. The match count and event count are modest, calibration is adaptive, and these are exploratory intervals rather than multiplicity-corrected discovery guarantees. Neither observer inputs nor Dota results establish usable player-visible warnings or League of Legends performance. The private League test remains untouched.

No more samples are added after inspecting the second wave. A further method revision requires a new declared experiment and fresh evaluation. Useful next work is authoritative pause reconstruction and broader league/team coverage, followed by matched temporal-model and visibility-restricted comparisons; it is not relabeling these baseline features as a new algorithm.

## Artifacts and reproduction

- [First protocol](../docs/precontact-pilot-protocol.md) and [follow-up declaration](../docs/precontact-invariance-followup.md).
- [First results](precontact-pilot-2026-09-30.json) and [fresh results](precontact-invariance-2026-09-30.json).
- [First quality ledger](precontact-quality-2026-09-30.json) and [fresh quality ledger](precontact-replication-quality-2026-09-30.json).
- [Independent parser check](precontact-independent-parser-2026-09-30.json).
- [Same-encounter completion check](precontact-completion-credit-2026-09-30.json).
- Acquisition manifests pin the public dataset revision, selected match IDs, split membership, and source file hashes.
- The scientific timing, prefix-access, team-attribution, alert-budget, and invariance tests pass. Raw replays and feature caches are not committed.
