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

For an authorized research-v2 collection, put one safe Match-V5 ID per line in
an ignored local file, export `RIOT_API_KEY`, and run:

```bash
uv run league-ews collect --match-ids /private/match-ids.txt --region europe
```

The collector retries rate limits/server failures, writes match/timeline pairs
atomically, resumes existing pairs and records checksums without copying PUUIDs
into its collection manifest.

Normalize the private pairs and build exact labels with:

```bash
uv run league-ews process --raw data/raw --output data/processed
```

Processed match files contain the supported causal timeline fields and labels,
not Riot IDs or PUUIDs. They remain ignored until redistribution is explicitly
approved.
