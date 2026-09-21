# RiftHazard sampling frame

`configs/rifthazard-sampling-frame.yaml` is the executable sampling contract
frozen on 2026-09-15, after the one-match canary and before any pilot match
details were requested. It operationalizes the dataset section of the
registered research plan; it does not itself contact Riot or authorize new API
scope.

## Study population

- Platforms/routes: EUW1/europe and NA1/americas.
- Queue: 420 (5v5 Ranked Solo), map 11 (current Summoner's Rift), mode
  `CLASSIC`, type `MATCHED_GAME`, exactly ten participants.
- Required source data: complete Match-V5 detail and timeline payloads with
  game version and creation time.
- Sampling unit: one complete, globally deduplicated match.

The routing pairs and game constants come from Riot's
[API reference](https://developer.riotgames.com/apis),
[routing documentation](https://developer.riotgames.com/docs/lol#routing-values),
[queue list](https://static-developer.riotgames.com/docs/lol/queues.json),
[map list](https://static-developer.riotgames.com/docs/lol/maps.json),
[mode list](https://static-developer.riotgames.com/docs/lol/gameModes.json), and
[type list](https://static-developer.riotgames.com/docs/lol/gameTypes.json).

## Completed patch frame and allocation

Riot's public 2026 schedule labels these releases 26.x, while Match-V5
`gameVersion` and Data Dragon use the corresponding 16.x version prefix. The
calendar windows seed match-history discovery; the authoritative cell is the
detail payload's `gameVersion`, not an inferred deployment time.

| Public patch | Match-V5 patch | Discovery window | EUW1 pilot | NA1 pilot | Final per platform |
|---|---|---|---:|---:|---:|
| 26.12 | 16.12 | 2026-06-10 to 2026-06-24 | 417 | 417 | 3,000 |
| 26.13 | 16.13 | 2026-06-24 to 2026-07-15 | 417 | 417 | 3,000 |
| 26.14 | 16.14 | 2026-07-15 to 2026-07-29 | 417 | 417 | 3,000 |
| 26.15 | 16.15 | 2026-07-29 to 2026-08-12 | 417 | 417 | 3,000 |
| 26.16 | 16.16 | 2026-08-12 to 2026-08-26 | 416 | 416 | 3,000 |
| 26.17 | 16.17 | 2026-08-26 to 2026-09-10 | 416 | 416 | 3,000 |
| **Total** | **6 patches** | **12 cells** | **2,500** | **2,500** | **36,000 overall** |

The 5,000 pilot uses balanced largest remainder in patch-then-platform order.
This assigns the eight remainder matches symmetrically across both routes in
the first four patches. The pilot is restricted to infrastructure checks and
fixing the duration rule; its match IDs cannot be reused for final claims.

The patch split is already frozen: 16.12-16.15 train, 16.16 calibrates and
selects thresholds, and 16.17 remains the untouched future-patch test set.

## Candidate construction

The registered candidate source is a private, checksum-bound snapshot of the
Challenger, Grandmaster and Master `RANKED_SOLO_5x5` ladders on each platform.
Ladder summoner IDs are resolved to PUUIDs with Summoner-V4 when needed, and
Match-history IDs are globally deduplicated before detail fetch or splitting.
The checksum-bound operational supplement in
`configs/rifthazard-discovery-plan.yaml` hash-orders ladder members, advances
both platforms in equal 32-player waves and fixes the pre-detail stopping rule
at a two-times candidate buffer in every calendar cell. See
`docs/candidate-discovery.md`. The subsequent global detail-screen order,
authoritative cell assignment and exact quota freeze are executable as
documented in `docs/pilot-selection.md`.
Within every eligible cell, selection order is the ascending SHA-256 order
defined by `seeded-sha256-within-cell-v1`: hash the UTF-8 bytes of decimal seed
`20260915`, one NUL byte, and the uppercase match ID, then sort by digest with
match ID as the collision tie-break. Labels, model scores and downstream
performance are forbidden selection inputs.

This is a high-ranked connected-player seed design, not a probability sample
of all League matches. Because the ladder snapshot is taken after the selected
historical patch windows, cohort membership is also conditioned on later
ladder survival and performance. Future-patch results therefore estimate
transfer within this retrospective high-ranked connected cohort, not
prospective population-wide generalization. Its rank, repeat-player and
regional biases remain explicit limitations and require the stratified and
player-component analyses in the data card and registered plan.

## Duration and collection boundary

No duration threshold existed for the pilot. All otherwise eligible short
games remained so their duration/remake distribution could be inspected. The
post-pilot supplement in `configs/rifthazard-duration-rule.yaml` now freezes an
inclusive 180-second final minimum and binds it to the private pilot-analysis
checksum. The original frame remains immutable. Final validation requires the
supplement and private analysis, and rejects every match with
`gameDuration < 180`.

The final candidate expansion is separately frozen in
`configs/rifthazard-final-discovery-plan.yaml`. It removes the exact 5,000
pilot IDs before applying its pre-detail stopping rule, requires 6,000
candidates per route-patch cell and leaves the registered final allocation at
3,000 matches per cell. It completed at nine balanced waves with 110,838
globally deduplicated remaining candidates. The subsequent selection contract
in `configs/rifthazard-final-selection-plan.yaml` binds that exact manifest and
pool before any final detail request. It screens one seeded global candidate
prefix, assigns cells from detail `platformId` and `gameVersion`, enforces the
inclusive duration minimum and stops only at all 12 exact quotas. See
`docs/final-discovery.md` and `docs/final-selection.md`.

Authority schema v2 can scope the three League-V4 ladder endpoints,
Summoner-V4 by summoner ID, Match-V5 IDs-by-PUUID, Match-V5 detail/timeline and
both regional routes. `preflight-discovery` binds that private record to the
exact frame and discovery-plan checksums before constructing any API client.

## Offline checks

Validate only the frame contract with:

```bash
make validate-sampling-frame
```

Bind a completed pilot raw validation to the exact frame with:

```bash
uv run league-ews validate-raw \
  --raw data/raw/registered-pilot \
  --sampling-frame configs/rifthazard-sampling-frame.yaml \
  --sampling-stage pilot \
  --discovery-plan configs/rifthazard-discovery-plan.yaml \
  --discovery-root data/private/pilot-discovery \
  --selection-root data/private/pilot-selection \
  --min-routes 2 \
  --min-patches 6
```

This requires all 12 cells, their exact pilot quotas and exact identity with
the checksum-bound selected pool. A count of two routes and six patches is no
longer sufficient. It still does not complete G2 without checksum-bound
processed output and human event review for every observed route-patch cell.
