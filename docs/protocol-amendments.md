# Registered protocol amendments

This file records changes made after `docs/research-plan.md` was frozen. An
amendment states when it occurred, what evidence was available and whether it
changes a hypothesis, outcome or decision rule.

## 2026-09-15 — align processed horizons with the registered protocol

**Stage:** after one operational Match-V5 canary; before the research pilot,
model fitting, threshold selection or outcome analysis.

The frozen research plan and `configs/rifthazard-v2.yaml` both specify 10, 20,
30 and 60-second horizons. The processing default accidentally contained only
10, 20 and 30 seconds. Research-v2 processing is corrected to emit all four
registered horizons. The legacy audit remains fixed to the 10, 20 and 30-second
columns that exist in the historical dataset.

This is an implementation-conformance correction. It does not change a
hypothesis, primary outcome, split rule, event definition or pass criterion.
No model result was available or inspected when the correction was made.

## 2026-09-15 — record native-cadence label opportunities

**Stage:** after the operational canary; before the research pilot, model
fitting, threshold selection or outcome analysis.

Raw validation now reports within-match snapshot intervals and, for every
registered event/horizon pair, the fraction of events that have at least one
genuine strictly prior observation within the forecast horizon. This is a
descriptive opportunity diagnostic, not a model-performance measure or data
quality threshold. It does not interpolate, forward-fill or otherwise create
additional observations.

This addition makes the registered native-versus-fixed-cadence ablation and
short-horizon feasibility limits auditable. It does not change a hypothesis,
outcome, event definition, horizon or pass criterion. No model result was
available or inspected when the diagnostic was added.

## 2026-09-15 — operationalize the pilot sampling frame

**Stage:** after the checksum-bound one-match canary review; before pilot
candidate discovery, pilot match-detail collection, duration inspection, model
fitting, threshold selection or outcome analysis.

The registered two-route, six-consecutive-patch design is made executable as
EUW1/europe and NA1/americas over completed Match-V5 game-version patches
16.12-16.17 (Riot public schedule 26.12-26.17), queue 420. The 5,000-match pilot
uses deterministic balanced-largest-remainder allocation across all 12 cells:
417 per route for patches 16.12-16.15 and 416 per route for patches 16.16-16.17.
The full target remains 3,000 per cell and 36,000 total. Seed 20260915 and a
checksum-bound high-ranked ladder candidate construction are fixed before
fetching pilot details.

No duration cutoff is set from the canary. Otherwise eligible short games stay
in the pilot, which is excluded from final claims. A single duration rule must
be frozen after inspecting only the pilot and before final collection. Final
frame validation is blocked until that post-pilot amendment exists.

This operationalizes choices left open by the registered plan without changing
its hypotheses, outcomes, event definitions, horizons or pass criteria. The
only real evidence inspected was the operational canary's source/processed
agreement, native cadence and label-opportunity diagnostics; no pilot or model
result existed.

## 2026-09-15 — freeze the candidate-discovery stopping rule

**Stage:** after freezing and validating the sampling frame; before any pilot
ladder, summoner, match-history or match-detail request.

The sampling frame fixed the ladder source and match-ID ordering but did not
state how many ladder members to query or when the pre-detail crawl must stop.
The checksum-bound discovery supplement closes that operational gap before
observing candidates: members are hash-ordered with the registered seed; EUW1
and NA1 advance in equal 32-player waves; each player contributes one capped
100-ID queue-420 page for every frozen patch window; and discovery stops at the
first complete wave with twice the pilot quota in every calendar cell. The run
fails incomplete at 256 players per platform rather than changing the rule.

This rule can inspect only ladder identifiers and Match-V5 ID-list responses.
It cannot inspect match details, labels, model scores or downstream outcomes.
The calendar-cell buffer is not an eligibility decision: authoritative patch
and population checks remain based on Match-V5 detail in the next stage. This
amendment changes no hypothesis, outcome, event definition, horizon, split or
pilot quota; no pilot candidate or model evidence existed when it was frozen.

## 2026-09-15 — make pilot eligibility selection executable

**Stage:** after candidate discovery completed; before any registered pilot
match-detail or timeline request, duration inspection, model fitting, threshold
selection or outcome analysis.

The already-frozen eligibility and seeded ordering rules are implemented as a
checksum-bound, resumable detail-screen stage. All globally deduplicated
candidates are traversed in the registered SHA-256 order. Match-V5 detail
assigns the authoritative `gameVersion` cell and enforces queue, map, mode,
type, platform, creation-time and participant-count requirements. Selection
stops only when all 12 pilot quotas are exact. A 404 is recorded as unavailable;
other request failures stop rather than silently exclude a candidate.

The only newly observed evidence before this implementation was the
identifier-free discovery summary: two balanced 64-player waves produced a
complete two-times buffer in every cell. No candidate detail, duration,
timeline, label or model outcome was inspected. This implementation does not
change a hypothesis, population rule, seed, quota, event definition, horizon,
split or pass criterion.

## 2026-09-16 — bind timeline collection to the frozen pilot

**Stage:** after deterministic detail screening filled all 12 pilot cells;
before any selected timeline request, duration inspection, event extraction,
model fitting, threshold selection or outcome analysis.

The selected pilot is now materialized by a checksum-bound, resumable collector
rather than by passing editable route files to the generic collector. Before a
request, it revalidates the full deterministic screening prefix, screening
digest, selected pool, regional ID files and discovery provenance. It reuses
the already-frozen Match-V5 details and requests only one timeline for each of
the 5,000 selected matches. Existing raw pairs must be an exact selected-prefix
inventory; a single timeline-only next bundle can be recovered after a crash,
while gaps, substitutions, extra bundle files or changed checksums stop the run.

The raw collection manifest remains private because it contains match IDs. A
separate identifier-free binding records the selected-pool and raw-manifest
checksums. Registered-pilot validation requires exact selected identities and
metadata in addition to the previously frozen route-patch quotas.

The only newly available evidence was the outcome-blind selection summary:
24,976 candidates yielded 7,687 screened details, 7,677 eligible details, ten
out-of-frame game-version exclusions and the exact 5,000-match allocation. No
timeline, event, label, duration distribution or model result was inspected.
This operational safeguard changes no population rule, selection order, quota,
hypothesis, outcome, horizon, split or pass criterion.


## 2026-09-20 — support the 2026 top-lane level cap

**Stage:** after completing the checksum-bound 5,000-match pilot and its first
raw validation; before pilot processing, the duration-rule decision, feature
analysis, model fitting, threshold selection or test-set access.

The first full-pilot validation accepted 3,514 bundles and rejected 1,486 for
one reason only: the normalized participant schema still imposed the historic
level-18 cap. The failures were present in every route-patch cell. Riot's
[2026 Season One gameplay preview](https://www.leagueoflegends.com/en-gb/news/dev/dev-2026-season-one-gameplay-preview/)
states that the top-lane role quest increases the level cap, and the official
[Patch 26.1 notes](https://www.leagueoflegends.com/en-gb/news/game-updates/patch-26-1-notes/)
explicitly identify level 20 as the new cap.

The normalized participant contract is therefore widened from levels 1-18 to
1-20, while values above 20 remain invalid. Graph input scaling now divides
level by 20 so the registered maximum remains 1.0. Regression tests require
level 20 to normalize and scale correctly and level 21 to fail validation.

This is an implementation-conformance correction to match the rules in force
throughout the already-frozen 2026 patch frame. It changes no raw bytes,
selected identities, population, quota, outcome, label, horizon, split or
pass criterion. Aggregate event diagnostics for the previously accepted
subset had been produced, but no processed pilot feature analysis or model
result was available or used to choose this correction.

## 2026-09-20 — constrain the post-pilot duration inspection

**Stage:** after the complete 5,000-match pilot passed automated raw validation
and processing; before inspecting its duration/remake distribution, fixing the
minimum-duration rule, collecting the final sample, fitting a model or
selecting a threshold.

The one permitted pilot data decision is implemented as a checksum-bound,
identifier-free report. It first revalidates the exact registered selection
and processed inventory, then reads only Match-V5 `gameDuration`,
`gameEndedInEarlySurrender` and `gameEndedInSurrender`. It reports duration
percentiles and retention under a fixed descriptive grid of candidate minimums
overall and by route-patch cell. It does not read event labels, winners,
features, predictions or downstream performance, and it does not choose a
cutoff automatically.

The original frame remains unchanged because pilot discovery, selection and
collection are already bound to its checksum. The single cutoff was therefore
required to be recorded in a separate post-pilot supplement bound to both that
frame and this private analysis report before final collection starts.
Aggregate event counts and label-opportunity diagnostics were already
available from validation, but they are forbidden duration-decision inputs.
This inspection mechanism changes no hypothesis, outcome, event definition,
horizon, split, quota or pass criterion.

## 2026-09-20 — freeze the final minimum-duration rule

**Stage:** after generating the checksum-bound, identifier-free duration report
from the complete registered pilot; before final candidate screening, final
timeline collection, model fitting, threshold selection or test-set access.

The private report contained 5,000 matches across all 12 registered cells and
has SHA-256
`3cab09e4f305bb67b089e28a35276cee1fe67add9584baef6552d78b7a12c9c5`.
At the predeclared 180-second candidate, all 90 early-surrender-flagged matches
were excluded and no other matches were excluded, retaining 4,910 (98.2%).
Every higher positive candidate discarded additional non-early-surrender
matches without excluding another early-surrender case. The final eligibility
rule is therefore frozen as the inclusive condition
`info.gameDuration >= 180` seconds.

The public supplement `configs/rifthazard-duration-rule.yaml` records the rule,
aggregate evidence and private report checksum without publishing match or
player identifiers. The original sampling frame remains unchanged so its
discovery, selection and collection bindings stay valid. Final validation now
requires both documents and checks the duration of every final match.

Only `gameDuration` and Riot's two surrender flags informed this decision.
Event prevalence, future labels, winners, features, predictions and model
performance were not used. The pilot and all pilot match IDs remain excluded
from final claims. The rule becomes immutable when final collection starts and
changes no hypothesis, outcome, event definition, horizon, split, cell quota or
pass criterion.
