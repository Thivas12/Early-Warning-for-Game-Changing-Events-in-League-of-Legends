# Final match selection

Final candidate discovery completed before any final Match-V5 detail request.
Nine balanced player waves produced 110,838 globally deduplicated,
pilot-excluded candidate IDs. Every registered route-patch cell exceeded its
6,000-ID reserve. The identifier-free discovery manifest and private candidate
pool are bound by SHA-256 in
`configs/rifthazard-final-selection-plan.yaml`.

That public plan was frozen on 2026-09-21 before detail screening. It preserves
the registered target of exactly 36,000 final matches: 3,000 in each of the six
patches for both EUW1/europe and NA1/americas.

## Deterministic screening rule

All 110,838 candidate IDs are placed in one global order using the sampling
frame's frozen seed: SHA-256 of the decimal seed, one NUL byte and the match ID,
with the match ID as the collision tie-break. Screening advances only through
a contiguous prefix of that order.

For each candidate, Match-V5 detail is the sole eligibility source. A match is
eligible only when it has:

- the candidate's registered platform;
- queue 420, map 11, `CLASSIC`, `MATCHED_GAME` and ten participants;
- an authoritative `gameVersion` in patches 16.12-16.17;
- a positive creation time; and
- `info.gameDuration >= 180` seconds.

The detail payload's platform and `gameVersion` determine the authoritative
cell. A candidate discovered in one calendar window can therefore be assigned
to another registered patch cell. A 404 or any failed eligibility check is
recorded and skipped. The first 3,000 eligible matches encountered for each
authoritative cell are selected, and screening stops only when all 12 quotas
are exact.

Timelines, events, labels, winners, features, predictions and downstream model
performance are forbidden selection inputs. Although a detail payload may
contain winner and player fields, the selector does not use them. Full detail
responses remain private only so later collection can reuse the selected
payloads without another detail request.

## Resumption and integrity

Each detail response or 404 marker is written atomically under
`data/private/final-selection/details`. Every record binds the frame, final
discovery manifest, candidate pool and seeded candidate rank. A rerun validates
the entire cached prefix before issuing another request. Gaps, additions,
partial files, identity drift or changed provenance stop the command.

The command may be deliberately chunked with `--max-new-requests`. An API or
credential error leaves the last complete record as a safe checkpoint; rerun
the same command after resolving the error. Once all quotas are full, the
selector freezes `selected-pool.json` and one selected-ID file per regional
route. Public terminal and validation reports contain only counts and hashes.

## Commands

Validate the public freeze and every private input before opening a client:

```bash
make validate-final-selection-plan
make preflight-final-selection
```

Start or resume the detail-only screen, then validate the frozen result:

```bash
make select-final
make validate-final-selection
```

For a bounded run, invoke the same CLI command used by the Make target and add,
for example, `--max-new-requests 1000`. A bounded incomplete run intentionally
returns exit code 2; its completed detail records remain valid checkpoints.

At the default 1.25-second request interval, screening tens of thousands of
candidates is expected to take many hours. The exact request count is not
known in advance because authoritative patch reassignment, unavailable
details and the duration rule are applied only as the frozen global prefix is
screened.

No identifier-bearing selection artifact is committed or authorized for
redistribution.
