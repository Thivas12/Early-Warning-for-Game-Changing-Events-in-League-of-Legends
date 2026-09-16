# Selection-bound pilot collection

The registered pilot collector turns the frozen 5,000-match selected pool into
private Match-V5 detail/timeline bundles without reopening selection. It is a
materialization stage, not a new sampling decision.

## Frozen inputs and request boundary

Before constructing a Riot client, the collector validates:

1. the registered sampling frame and candidate-discovery plan;
2. the complete discovery manifest and candidate-pool checksums;
3. the exact deterministic prefix of detail-screen records and its aggregate
   checksum;
4. every eligibility decision, cell assignment and 416/417 quota;
5. `selected-pool.json` and both regional selected-ID file checksums; and
6. the private authority record, endpoint/route scope and runtime credential.

The cached detail payload for every selected match is byte-bound to its screen
record and selected-pool entry. The collector therefore makes exactly one new
kind of request: Match-V5 timeline. It does not refetch details, replace failed
matches, inspect outcomes to select alternatives or change any cell quota. A
timeline 404, exhausted retry, authentication error, malformed response or
identity mismatch stops the run.

## Resumable state machine

Raw files live only in ignored `data/raw/registered-pilot/`. On every rerun the
collector reconstructs and checksum-validates state from the files themselves:

- complete detail/timeline pairs must be a contiguous prefix of the frozen
  selected order;
- those pairs are reused without a Riot request;
- one final timeline without its cached detail is treated as an interrupted
  atomic write and is completed locally;
- a match-only pair, multiple interrupted bundles, a gap, an unselected bundle,
  a changed payload or an unexpected partial file fails closed.

The timeline is written before the already-cached detail. This makes the only
possible interrupted bundle recoverable without repeating a successful API
request. Manifest and binding writes are atomic.

## Commands

Run the two offline gates first, then start or resume collection:

```bash
make validate-pilot-selection
make preflight-pilot-collection
make collect-selected-pilot
```

Requests are sequential and share one conservative 1.25-second pacer across
Europe and Americas. Count-only progress is written to standard error every
100 new timeline requests. An intentionally bounded session may use:

```bash
uv run league-ews collect-selected-pilot \
  --authority-record data/private/riot-authority.yaml \
  --sampling-frame configs/rifthazard-sampling-frame.yaml \
  --discovery-plan configs/rifthazard-discovery-plan.yaml \
  --discovery-root data/private/pilot-discovery \
  --selection-root data/private/pilot-selection \
  --output data/raw/registered-pilot \
  --max-new-requests 500
```

An incomplete bounded run exits with code 2 after writing a consistent partial
manifest. Running the same command again resumes safely. Do not edit or move
individual private artifacts between runs.

## Provenance and validation

`collection-manifest.json` uses the cumulative `riot-raw-collection-v2`
contract and remains private because it inventories match IDs.
`selection-binding.json` is identifier-free and binds that manifest to the
frame, discovery plan, discovery manifest, candidate pool and selected pool.
It reports only checksums and counts, including available bundles, new timeline
requests and locally recovered interrupted bundles.

After all 5,000 bundles are present, run:

```bash
make validate-pilot
```

Validation requires complete file pairs, payload identities, hashes,
normalizable causal schemas, exact 12-cell coverage and exact identity with the
frozen selected pool. It makes no network request. The earlier operational
canary belongs under `data/raw/canary` and cannot satisfy or contaminate this
registered path.

Raw details and timelines may contain PUUIDs. They must remain private, are not
authorized for redistribution by these manifests and remain subject to the
retention period in `data/private/riot-authority.yaml`.
