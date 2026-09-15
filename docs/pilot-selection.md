# Pilot eligibility screening and selection

The registered pilot is frozen from the completed private candidate pool before
any timeline is requested. This stage uses only Match-V5 detail fields needed
by the sampling-frame eligibility contract. It cannot inspect objectives,
teamfights, future-event labels, model scores or downstream performance.

## Deterministic selection rule

1. Validate the exact sampling frame, discovery plan, discovery manifest and
   candidate-pool checksums. Reject incomplete, reordered, duplicated or
   out-of-frame candidate inventories.
2. Merge the 12 provisional discovery-window lists and order every unique
   candidate by the frozen `20260915 NUL match-id` SHA-256 rule.
3. Fetch match details in that one global order. Treat only an authoritative
   HTTP 404 as unavailable; authentication, rate-limit exhaustion, transport
   and server failures stop the run rather than becoming exclusions.
4. Require queue 420, map 11, `CLASSIC`, `MATCHED_GAME`, ten participants in
   both metadata and info, the expected platform, a positive creation time and
   a registered `gameVersion` patch.
5. Assign an eligible match to its authoritative route-platform-patch cell from
   the detail payload's `platformId` and `gameVersion`. The calendar window in
   which an ID was discovered is not the final patch assignment.
6. Select the first 417 eligible matches in each route cell for patches
   16.12-16.15 and the first 416 for patches 16.16-16.17. Stop as soon as all 12
   quotas are exact, producing 5,000 globally unique selected matches.

Because requests follow the global hash order, no unrequested candidate can
outrank a selected match in any authoritative cell when the final quota is
reached. Short games are retained: the pilot has no duration exclusion.

## Private resumable state

Each detail response is atomically wrapped with its frame, discovery-manifest,
candidate-pool and candidate-rank checksums under ignored
`data/private/pilot-selection/details/`. The cache must be an exact contiguous
prefix of the global candidate order. A rerun validates and reuses the prefix;
tampering, gaps, unexpected files or partial writes stop the run.

`selection-manifest.json` is identifier-free and reports only checksums,
counts, rejection reason totals and cell completion. Once all quotas are met,
`selected-pool.json` and one match-ID file per regional route are written once
and thereafter byte-verified. These identifier-bearing files remain private
and grant no redistribution authority. Cached payloads may contain PUUIDs and
are governed by the authority record's raw-retention rule.

## Commands

The first command validates the frozen discovery artifacts without making a
request. The second also checks the private authority record and runtime key:

```bash
make validate-candidate-pool
make preflight-pilot-selection
```

Start or resume detail screening with:

```bash
make select-pilot
```

Requests are sequential and share the same conservative 1.25-second pacer as
candidate discovery. Progress goes to standard error every 100 new requests
and contains counts only. Interrupting and rerunning the same command is safe.

For an intentionally bounded work session, invoke the CLI with
`--max-new-requests N`. An incomplete bounded run writes a safe progress
manifest and exits with code 2; rerun without changing any private artifacts.

This stage deliberately does not fetch timelines. Complete detail/timeline
bundle collection from the frozen route files is the next protocol stage.
