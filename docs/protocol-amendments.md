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
