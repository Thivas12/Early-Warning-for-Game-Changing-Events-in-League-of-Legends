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
the fail-closed placeholder values truthfully, export `RIOT_API_KEY`, and run:

```bash
make preflight
```

The example intentionally fails until ethics status and collection authority
are resolved. The preflight makes no network request, never reads the key into
its report and returns exit code 2 when any gate fails.

Validate the committed population, patch series, split and deterministic cell
allocations independently of credentials or private data:

```bash
make validate-sampling-frame
```

This confirms the pre-pilot contract only. It does not make an API request and
does not claim that the current private authority record includes the americas
route or the additional candidate-discovery endpoints.

Only after the preflight passes, put one safe Match-V5 ID per line in an
ignored local file and run:

```bash
uv run league-ews collect \
  --authority-record data/private/riot-authority.yaml \
  --match-ids /private/match-ids.txt \
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
the exact sampling-frame checksum and requires all 12 route-patch cells to meet
their deterministic 416/417-match quotas. Merely observing two routes and six
patches cannot pass the frame-bound check.
An automated pass does not complete G2: event timestamps still require a
documented human spot-check against source payloads. After manually comparing
the selected source objective events, teamfight episodes and processed strict
future labels, record that review in an ignored, checksum-bound file. Repeat
`--match-id` so the review includes at least one match from each of the 12
route-patch cells:

```bash
uv run league-ews record-event-spot-check \
  --raw data/raw/pilot \
  --processed data/processed/pilot \
  --match-id REPLACE_WITH_REVIEWED_MATCH_ID \
  --output data/private/pilot-event-spot-check.json \
  --confirm-objective-events \
  --confirm-teamfight-episodes \
  --confirm-future-labels
```

Then supply the private record to validation:

```bash
uv run league-ews validate-raw \
  --raw data/raw/pilot \
  --processed data/processed/pilot \
  --event-spot-check data/private/pilot-event-spot-check.json \
  --sampling-frame configs/rifthazard-sampling-frame.yaml \
  --sampling-stage pilot \
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
uv run league-ews process \
  --raw data/raw/pilot \
  --output data/processed/pilot \
  --sampling-frame configs/rifthazard-sampling-frame.yaml \
  --sampling-stage pilot \
  --min-routes 2 \
  --min-patches 6
```

`process` repeats the same frame-bound automated gate before writing derived
files. Canary deviations remain separate from this registered pilot path.

Processed match files contain the supported causal timeline fields and labels,
not Riot IDs or PUUIDs. They remain ignored until redistribution is explicitly
approved.
