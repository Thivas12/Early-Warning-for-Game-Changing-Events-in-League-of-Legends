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
An automated pass does not complete G2: event timestamps still require a
documented human spot-check against source payloads.

Normalize the private pairs and build exact labels with:

```bash
uv run league-ews process --raw data/raw --output data/processed
```

`process` repeats the same automated gate before writing derived files. A pilot
that has a preregistered coverage deviation must pass the matching explicit
`--min-routes` and `--min-patches` values to both commands.

Processed match files contain the supported causal timeline fields and labels,
not Riot IDs or PUUIDs. They remain ignored until redistribution is explicitly
approved.
