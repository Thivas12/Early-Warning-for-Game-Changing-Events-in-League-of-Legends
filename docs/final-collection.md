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

`process-final` processes at most 2,000 new matches per invocation. Rerun it
until it exits with status 0 and writes
`data/processed/registered-final/processing-manifest.json`. An incomplete but
successful chunk exits with status 2 and prints the available count. The
processor checks the existing processed files form the exact sorted prefix,
reads their identities and labels, then resumes after them. It does not
overwrite the completed files. Each invocation repeats raw validation before
processing; no Riot API key or network request is needed.

`validate-final` checks every payload checksum, identity, causal schema,
route-patch allocation and inclusive duration rule. It additionally proves
that the raw inventory exactly materializes the frozen final selected pool;
matching aggregate counts alone cannot pass. `process-final` repeats that gate
before producing identifier-free normalized observations and strict future
labels under `data/processed/registered-final`.

Once processing finishes, run `make validate-final-processed`. The offline
report in `data/private/final-processed-validation.json` binds to the passed
raw validation report and audits all 36,000 processed files: inventory,
checksums, schema and identity, event indexes in normalized timelines,
strict future labels and player identifier fields. A passing automated report
precedes the separate human event spot-check for the 12 route-patch cells;
it does not attest that review on the researcher's behalf.

Run `make prepare-final-event-review` after a passing processed audit. It
creates the ignored `data/private/final-event-review-packet.json` with one
event-rich match from every route-patch cell. Within each cell it chooses the
smallest SHA-256 of the raw manifest checksum and match ID. This quality
control selection does not change the frozen research sample. The packet lists
source objective timestamps, qualifying kill episodes, processed event indexes
and 10/20/30/60-second label witnesses. The referenced raw timeline and
processed file paths let the researcher inspect the source fields directly.

After manually comparing all 12 source matches and labels, create the
checksum-bound attestation. The confirmation flags assert that the researcher
actually checked all listed event types and future labels:

```bash
mapfile -t review_ids < <(uv run python - <<'PY'
import json
from pathlib import Path
packet = json.loads(Path('data/private/final-event-review-packet.json').read_text())
for sample in packet['samples']:
    print(sample['match_id'])
PY
)
review_args=()
for match_id in "${review_ids[@]}"; do
  review_args+=(--match-id "$match_id")
done
uv run league-ews record-event-spot-check \
  --raw data/raw/registered-final \
  --processed data/processed/registered-final \
  "${review_args[@]}" \
  --output data/private/final-event-spot-check.json \
  --confirm-objective-events \
  --confirm-teamfight-episodes \
  --confirm-future-labels
make validate-final-g2
```

The validation report must say `passed: true`, `g2_complete: true`, and
`manual_event_spot_check.status: passed`. Keep the packet and attestation
private; neither belongs in Git.
