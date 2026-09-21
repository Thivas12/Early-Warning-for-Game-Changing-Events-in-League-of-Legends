# Final candidate discovery

The 5,000-match registered pilot is excluded from every final claim. Its
24,976-ID discovery pool also cannot supply the registered final allocation of
3,000 matches in each of 12 route-patch cells. Final discovery therefore uses a
separate, post-pilot plan frozen after the minimum-duration decision and before
any final Match-V5 detail screening.

The executable plan is
`configs/rifthazard-final-discovery-plan.yaml`. It is bound to:

- the immutable `rifthazard-2026-09-15` sampling frame;
- the checksum-bound `gameDuration >= 180` rule and private analysis;
- the exact frozen 5,000-match pilot selected pool; and
- the original pilot discovery provenance needed to validate those IDs.

## Outcome-blind capacity rule

Final discovery takes one new private Challenger, Grandmaster and Master ladder
snapshot for EUW1 and NA1. Members are placed in the same seeded order used by
the sampling frame and processed in equal 32-player waves. For every member,
the command requests one bounded queue-420 Match-V5 ID page for each of the six
registered half-open patch windows.

Match-V5 history is region-routed, while a PUUID can remain associated with
accounts across platforms after a transfer. Each bounded response is therefore
validated and reduced to well-formed match IDs carrying the cell's registered
platform prefix before it is cached or counted. Off-platform IDs are discarded
without replacement or additional pagination, so the frozen one-page request
budget and outcome-blind stopping rule are unchanged.

Before a cell count is evaluated, every frozen pilot match ID is removed. The
command stops at the first complete balanced wave for which every cell has at
least 6,000 remaining IDs, twice its final target. It may process at most 512
players per platform. This stopping rule reads no match details, timelines,
events, labels, winners, model features, predictions or performance results.

The two-times pool is a screening reserve, not a change to the final sample
size. Later detail screening must still enforce the registered population,
the inclusive 180-second rule and exactly 3,000 selected matches per cell.

## Commands and private outputs

Validate the public plan and all local private bindings before any request:

```bash
make validate-final-discovery-plan
make preflight-final-discovery
```

Build or resume the pool, then validate every checksum and exclusion:

```bash
make discover-final-candidates
make validate-final-candidate-pool
```

Identifier-bearing artifacts remain ignored under
`data/private/final-discovery`. Writes are atomic. Re-running the same command
reuses the frozen ladder snapshot, player resolutions and complete history
pages. Unexpected partial files, cache additions, checksum drift, changed
pilot artifacts, a changed duration report or an undersized cell stop the
workflow.

Terminal and validation summaries contain counts and hashes only. Candidate
IDs, PUUIDs and ladder identities are never emitted in those summaries or
committed to Git.
