# Selection-bound final collection

The final collector materializes the frozen 36,000-match sample without
reopening selection. It revalidates the checksum-bound final selection, reuses
the exact Match-V5 detail payload already accepted during screening and makes
only Match-V5 timeline requests.

## Safety and resumability

Before any request, `preflight-final-collection` verifies the private authority
record, both regional routes, timeline endpoint scope, runtime credential and
the complete frozen-selection provenance chain. The collector never substitutes
a failed match or changes a cell allocation.

Output lives under ignored `data/raw/registered-final/`. Complete pairs must
form a contiguous prefix of the frozen selected order. Each rerun verifies and
skips that prefix. One timeline-only next bundle is recoverable locally from
the frozen detail cache; gaps, match-only bundles, unexpected identifiers,
changed payloads and checksum drift fail closed. Manifest and checkpoint writes
are atomic.

## Commands

Run the offline selection validation and the collection gate first:

```bash
make validate-final-selection
make preflight-final-collection
```

Start or resume the complete collection with:

```bash
make collect-selected-final
```

For operationally safer sessions, use the CLI directly with the same arguments
as the Make target and append `--max-new-requests 1000`. An incomplete bounded
run writes a consistent checkpoint and exits with code 2 by design. Repeating
the command resumes from that checkpoint. A complete run exits with code 0.

Requests are sequential and conservatively paced. Do not run memory-intensive
model servers in the same constrained WSL instance during collection.

## Provenance and privacy

`collection-manifest.json` inventories the cumulative raw pairs.
`selection-binding.json` binds them to the sampling frame, duration rule, pilot
exclusion, final discovery, final selection plan and exact selected-pool
checksum. The public-style binding summary contains counts and checksums only;
the raw files and identifier-bearing inventory remain private and are not
authorized for redistribution.

## Offline validation and processing

After all 36,000 pairs are present, run:

```bash
make validate-final
make process-final
```

`validate-final` checks every payload checksum, identity, causal schema,
route-patch allocation and inclusive duration rule. It additionally proves
that the raw inventory exactly materializes the frozen final selected pool;
matching aggregate counts alone cannot pass. `process-final` repeats that gate
before producing identifier-free normalized observations and strict future
labels under `data/processed/registered-final`.
