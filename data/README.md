# Data boundary

No dataset is stored in Git.

- `raw/`, `interim/`, `processed/` and `external/` are ignored.
- `manifests/` contains small provenance, licence and checksum records.
- A manifest identifies bytes; it does not grant redistribution rights.
- Raw Riot payloads may contain persistent player identifiers and must remain
  private.

To reproduce the legacy audit, obtain the separately distributed
`final_dataset.csv`, verify its SHA-256 against the manifest, place it anywhere
outside Git (the Makefile assumes `audit-data/`), then run `make audit diagnose
benchmark`.

Before any research-v2 request, copy
`configs/riot-authority.example.yaml` to the ignored path
`data/private/riot-authority.yaml`. Review the current Riot policies, replace
the fail-closed placeholder values truthfully and export `RIOT_API_KEY`.
Authority schema v2 explicitly covers EUW1/europe, NA1/americas and the seven
endpoints registered for candidate discovery and complete bundle collection.

Validate the frame and its checksum-bound stopping supplement without a key or
network request:

```bash
make validate-sampling-frame
make validate-discovery-plan
```

Then validate the private authority, both routes, all endpoints and runtime key:

```bash
make preflight-discovery
```

The committed example intentionally fails until ethics status and collection
authority are resolved. The preflight makes no network request, never returns
the key and exits with code 2 when any gate fails.

After preflight passes, create or resume the private ladder snapshot and
pre-detail Match-V5 ID pool:

```bash
make discover-candidates
```

The discovery command processes EUW1 and NA1 in equal deterministic player
waves and stops only when all 12 calendar cells have the frozen two-times
candidate buffer. It caches every identifier-bearing response atomically under
`data/private/pilot-discovery`, so the same command safely resumes after an
interruption. Its terminal manifest contains only counts and checksums. It does
not fetch match details or timelines; exact eligibility and authoritative
`gameVersion` assignment belong to the next collection stage.

After discovery completes, verify its exact checksums and authority gate, then
start or resume deterministic detail-only eligibility screening:

```bash
make validate-candidate-pool
make preflight-pilot-selection
make select-pilot
```

This reads candidates in the frozen global hash order and stops when the exact
5,000-match, 12-cell pilot allocation is full. It atomically caches private
detail responses under `data/private/pilot-selection` and prints only counts
and checksums. On success it freezes `selected-pool.json` plus separate Europe
and Americas match-ID files for the later bundle collector. It does not fetch
timelines. See `docs/pilot-selection.md` for the eligibility, reassignment,
resume and HTTP-404 rules.

Before timeline collection, revalidate the complete screening cache and repeat
the authority gate. Then start or resume the exact selected pilot:

```bash
make validate-pilot-selection
make preflight-pilot-collection
make collect-selected-pilot
```

The registered collector reuses the 5,000 frozen Match-V5 detail payloads and
requests only their timelines. It writes private pairs under
`data/raw/registered-pilot`, never under the canary path. Existing pairs must be
an exact contiguous prefix of the selected pool. A rerun checksum-validates and
skips that prefix. One timeline-only next bundle is recoverable after an
interruption; gaps, match-only bundles, unselected bundles, unexpected partials,
identity changes and selection drift stop the run. Progress and the terminal
`selection-binding.json` contain counts and checksums only. See
`docs/pilot-collection.md`.

For a deliberately pre-specified Match-V5 canary, put one safe ID per line in
an ignored local file and run:

```bash
uv run league-ews collect \
  --authority-record data/private/riot-authority.yaml \
  --match-ids /private/match-ids.txt \
  --output data/raw/canary \
  --region europe
```

`collect` repeats the preflight as a mandatory gate and exits before constructing
the API client if it fails. The collector retries rate limits/server failures,
writes each payload atomically, manifests only complete match/timeline pairs,
resumes existing pairs and records checksums without copying PUUIDs into its
collection manifest. Manifest schema v2 retains and revalidates the complete
available inventory across resumed runs, even when a later run requests only a
subset.

Validate the private raw inventory before processing:

```bash
make validate-raw
```

This network-free command checks manifest consistency, complete pairs,
checksums, payload identity, supported causal normalization, and the registered
minimum of two regional routes and six patches. It writes the report to the
ignored `data/private/raw-validation.json`, binds that report to the exact
manifest SHA-256, and returns exit code 2 on failure.
For a deliberately smaller pipeline smoke test, call `validate-raw` directly
with lower `--min-routes` and `--min-patches` values and record that deviation.

For the registered pilot, use `make validate-pilot`. This binds validation to
the exact sampling frame, discovery artifacts and frozen selected-pool
checksums, and requires all 12 route-patch cells to meet their deterministic
416/417-match quotas. Merely observing two routes and six patches—or even the
right cell counts with different match identities—cannot pass.
An automated pass does not complete G2: event timestamps still require a
documented human spot-check against source payloads. After manually comparing
the selected source objective events, teamfight episodes and processed strict
future labels, record that review in an ignored, checksum-bound file. Repeat
`--match-id` so the review includes at least one match from each of the 12
route-patch cells:

```bash
uv run league-ews record-event-spot-check \
  --raw data/raw/registered-pilot \
  --processed data/processed/registered-pilot \
  --match-id REPLACE_WITH_REVIEWED_MATCH_ID \
  --output data/private/pilot-event-spot-check.json \
  --confirm-objective-events \
  --confirm-teamfight-episodes \
  --confirm-future-labels
```

Then supply the private record to validation:

```bash
uv run league-ews validate-raw \
  --raw data/raw/registered-pilot \
  --processed data/processed/registered-pilot \
  --event-spot-check data/private/pilot-event-spot-check.json \
  --sampling-frame configs/rifthazard-sampling-frame.yaml \
  --sampling-stage pilot \
  --discovery-plan configs/rifthazard-discovery-plan.yaml \
  --discovery-root data/private/pilot-discovery \
  --selection-root data/private/pilot-selection \
  --output data/private/pilot-validation.json \
  --min-routes 2 \
  --min-patches 6
```

The record is bound to the exact raw and processing manifests plus every
reviewed raw/processed file checksum. It must contain at least one reviewed
match from every observed route-patch cell. The identifier-minimized
validation summary reports only counts and check outcomes, not the reviewed
match IDs. A canary deviation can pass its own manual review but does not
complete the registered two-route, six-patch G2 gate. If a spot-check record is
supplied but is stale, incomplete or invalid, validation returns exit code 2
even when every automated raw-integrity check passes.

The pre-pilot frame intentionally blocks `--sampling-stage final`: the minimum
duration rule is still unset. Freeze that rule in a post-pilot amendment before
collecting or validating the final 36,000-match sample.

Normalize the private pairs and build exact labels with:

```bash
make process-pilot
```

`process-pilot` repeats the same frame- and selection-bound automated gate
before writing derived files. Canary deviations remain separate from this
registered pilot path.

After all 5,000 processed files reconcile with the manifest, create the
identifier-free, checksum-bound duration/remake report:

```bash
make analyze-pilot-duration
```

This repeats registered-pilot validation and writes the ignored
`data/private/pilot-duration-analysis.json`. Only Match-V5 `gameDuration` and
the two surrender flags enter the diagnostic; timeline events, labels, winners
and model outputs do not. Candidate minimums are reported descriptively and do
not become a rule until one is frozen in a post-pilot supplement. See
`docs/pilot-duration.md`.

Processed match files retain match IDs for provenance but contain only the
supported causal timeline fields and labels, with no player identifier fields
such as PUUIDs. They remain ignored until redistribution is explicitly approved.
