# Data card

## Legacy v5 derived table

Purpose: historical MSc exploration and non-commercial audit only.

- 484,255 ten-second rows from 2,998 matches; 86 columns.
- Separate distribution reportedly licensed CC BY-NC 4.0.
- No patch/version field, raw payloads or collection manifest in the release.
- Known future leakage, constant generator-default features, forward-filled
  source frames, ambiguous teamfight episodes and contaminated legacy splits.
- Not suitable for commercial use, player-level decisions, fairness claims or
  future-patch conclusions.

The exact audited file hash and findings are in `data/manifests/legacy-v5.yaml`
and `reports/legacy-audit.json`.

## Research v2 dataset (registered pilot collected; final not yet collected)

Unit of sampling: complete ranked match. Unit of prediction: a genuine timeline
observation within a match. Unit of evaluation: a distinct future event.

Raw inputs:

- Match-V5 detail payload;
- Match-V5 timeline payload;
- versioned static game/rule metadata;
- collection and sampling manifest.

Derived releases exclude Riot IDs, PUUIDs and reversible player mappings. Each
row carries pseudonymous match ID, game version, creation time, region, native
timestamp, feature-schema version and label-policy version.

Expected representation gaps include unavailable real-time health, fog-of-war
visibility and player intent. These are not imputed as observed facts. Position
frames are lower frequency than events and are not advertised as ten-second
telemetry. For the sampled 2026 patches, participant level is valid from 1 to
20 because Riot's top-lane role quest can raise the historical level-18 cap;
levels above 20 remain invalid.

The frozen frame is EUW1/europe plus NA1/americas, queue 420, over completed
Match-V5 patches 16.12-16.17. The operational 5,000-match pilot is balanced
across all 12 route-patch cells and is excluded from final claims. The final
target remains 3,000 matches per cell. Exact allocations, patch windows and
selection controls are documented in `docs/sampling-frame.md`. The pilot-only
duration inspection subsequently froze `gameDuration >= 180` seconds for final
eligibility; the pilot remains excluded from final claims. A separate final
candidate crawl removes all frozen pilot IDs before measuring its two-times
per-cell screening reserve.

## Bias and representativeness

The proposed high-ranked seed strategy may over-represent elite play, long
sessions, specific regions and players connected in the match graph. Results
must be stratified by region, patch, rank band where lawfully available, match
duration and event prevalence. Generalization to casual, professional, other
queues or other regions is not assumed. Because the frozen ladder snapshot is
later than the sampled historical patch windows, membership also reflects
retrospective ladder survival and performance; future-patch evaluation applies
to that connected cohort rather than the overall Ranked Solo population. Each
selected player contributes at most the single 100-ID Match-V5 page returned
for a patch window, so very high activity beyond that cap is not represented
exhaustively and API result ordering may shape which of those matches enter the
candidate pool.

## Access and retention

Raw payloads are private research inputs and excluded from Git. Retention,
redistribution and deletion follow Riot's current terms and the approved
research/product registration. Public artifacts contain code, schemas,
aggregate results and cryptographic manifests unless redistribution is
explicitly authorized.
