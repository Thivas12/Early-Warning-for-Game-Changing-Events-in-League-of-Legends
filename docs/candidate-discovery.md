# Candidate discovery protocol

`configs/rifthazard-discovery-plan.yaml` is the executable supplement that
closes the sampling frame's previously unspecified ladder-crawl stopping rule.
It is bound to sampling-frame SHA-256
`2355ec26182aa6862e8a110ff94f0ab402e9a4e77c0a52a0a5c81f1892033f6b` and
was frozen before any pilot candidate request.

## Deterministic stopping rule

1. Fetch one private canonical snapshot of the Challenger, Grandmaster and
   Master Ranked Solo ladders for EUW1 and NA1.
2. Prefer a ladder PUUID when present; otherwise resolve its encrypted summoner
   ID to a PUUID through Summoner-V4.
3. Hash-order members independently within each platform using seed
   `20260915`, platform, identifier kind and identifier.
4. Advance both platforms together in 32-player waves. For every included
   player, request one queue-420 Match-V5 ID page capped at 100 IDs for each of
   the six frozen half-open UTC discovery windows. Because a PUUID can retain
   matches from a previous platform after an account transfer, retain only
   well-formed IDs whose platform prefix matches the registered platform. A
   filtered ID is not replaced with another request or page.
5. Globally deduplicate match IDs and stop after the first complete equal wave
   in which every route-window cell contains at least twice its pilot quota:
   834 candidates for each 417-match cell and 832 for each 416-match cell.
6. Fail incomplete after 256 players per platform rather than changing the
   rule after observing data.

No match detail, timeline, event label, model score or downstream result is
read to decide when discovery stops. Calendar windows only generate a buffered
candidate pool. The next collection stage must use Match-V5 detail fields to
assign authoritative `gameVersion` cells and apply the registered eligibility
contract. That deterministic stage is specified in
`docs/pilot-selection.md`.

## Private resumable state

All discovery output belongs under ignored `data/private/`. The command writes
the ladder snapshot before requesting any match IDs, then atomically caches one
player resolution and one player-window history response per file. A rerun
validates and reuses those files. Any partial, mismatched or unexpected cache
inventory stops the run.

`candidate-pool.json` contains private match IDs. The separate discovery
manifest exposes only counts and checksums, binds the snapshot, caches and pool
to the exact frame and discovery plan, and explicitly grants no redistribution
authority. The snapshot, resolution cache, histories and candidate pool are all
identifier-bearing raw research inputs governed by the authority record's
retention period; they must not enter Git, public artifacts or unapproved
backups.

## Commands

The first two commands are offline:

```bash
make validate-discovery-plan
make preflight-discovery
```

After the private v2 authority record and runtime key pass, start or resume the
network collection with:

```bash
make discover-candidates
```

Requests are sequential and conservatively spaced by 1.25 seconds across both
platform- and region-routed clients. Riot `429` and server responses retain the
existing bounded retry behavior. If the shell or network stops, rerun the same
command; do not recreate the snapshot or edit cached files.

After discovery completes, validate its binding and begin the separate
detail-only pilot selection stage:

```bash
make validate-candidate-pool
make preflight-pilot-selection
make select-pilot
```
