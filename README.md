# LeagueEWS Research

[![Research CI](https://github.com/Thivas12/Early-Warning-for-Game-Changing-Events-in-League-of-Legends/actions/workflows/ci.yml/badge.svg)](https://github.com/Thivas12/Early-Warning-for-Game-Changing-Events-in-League-of-Legends/actions/workflows/ci.yml)

LeagueEWS Research studies whether strategically important League of Legends
events can be forecast before they occur using only information that was
available at prediction time.

The current research question is:

> Can Baron, Dragon and teamfight events be forecast 10–60 seconds ahead with
> calibrated probabilities that remain useful on unseen matches and game
> patches?

This repository is the **research and reproducibility project**. A future
player-facing product will live in a separate repository and will consume only
a versioned, validated research release.

## Research status

The original MSc notebooks reported promising results, but a post-project audit
found data leakage, broken features and train/test contamination. Those results
are preserved for research transparency under [`legacy/msc-v1`](legacy/msc-v1)
and are **not treated as production or generalisation evidence**.

The `research/v2` programme starts again from a falsifiable protocol:

1. establish causal data contracts;
2. split complete matches before preprocessing or augmentation;
3. beat time, event-history and tabular baselines;
4. evaluate distinct events rather than positive rows;
5. test calibration, alert burden and lead time;
6. hold out future patches and publish negative results.

See [`docs/research-plan.md`](docs/research-plan.md) for the registered plan and
[`reports/rifthazard-calibration-2026-09-26.md`](reports/rifthazard-calibration-2026-09-26.md)
for the first registered calibration results, including the negative B3
event-level alert-utility finding. The future-patch test is still untouched.
See [`docs/legacy-audit.md`](docs/legacy-audit.md) for the evidence that motivated
the reset. Post-freeze corrections are recorded in
[`docs/protocol-amendments.md`](docs/protocol-amendments.md). The executable
two-route, six-patch population and allocation are in
[`docs/sampling-frame.md`](docs/sampling-frame.md). Its deterministic,
pre-detail crawl and stopping supplement is in
[`docs/candidate-discovery.md`](docs/candidate-discovery.md). Checksum-bound
detail eligibility and exact pilot selection are documented in
[`docs/pilot-selection.md`](docs/pilot-selection.md). Selection-bound,
resumable timeline collection is specified in
[`docs/pilot-collection.md`](docs/pilot-collection.md). The outcome-blind,
checksum-bound post-pilot duration inspection is documented in
[`docs/pilot-duration.md`](docs/pilot-duration.md), with the frozen final rule
in [`configs/rifthazard-duration-rule.yaml`](configs/rifthazard-duration-rule.yaml).
The pilot-isolated, outcome-blind expansion to the final candidate pool is in
[`docs/final-discovery.md`](docs/final-discovery.md). Its checksum-bound,
detail-only final eligibility screen and exact 36,000-match allocation are in
[`docs/final-selection.md`](docs/final-selection.md). Its selection-bound,
resumable timeline materialization is specified in
[`docs/final-collection.md`](docs/final-collection.md).

## Quick start

Python 3.12 and [uv](https://docs.astral.sh/uv/) are the supported development
environment.

```bash
uv sync --all-groups
uv run league-ews audit --csv /path/to/final_dataset.csv
uv run league-ews benchmark --csv /path/to/final_dataset.csv --output reports/local
uv run league-ews validate-sampling-frame --frame configs/rifthazard-sampling-frame.yaml
make validate-discovery-plan
make validate-candidate-pool
make validate-pilot-selection
make validate-final-discovery-plan
make validate-final-selection-plan
make preflight-final-collection
make validate-final
uv run pytest
```

Raw and derived datasets are intentionally excluded from Git. Public data must
be accompanied by a source, licence and checksum manifest under
`data/manifests/`.

## Repository map

```text
src/league_ews/       tested research library and command-line interface
tests/                unit, contract and regression tests
configs/              versioned experiment configurations
data/manifests/       provenance and licence metadata, never raw data
reports/              committed reproducible summaries, not ad-hoc outputs
paper/                manuscript and bibliography
docs/                 protocol, audit, cards, ethics and AI-use record
legacy/msc-v1/        immutable historical MSc assets
```

## Reproducibility contract

Every reported result must identify its Git commit, dataset checksum, feature
and label versions, split manifest, configuration, random seed and runtime.
Model selection uses validation data only. Test results are generated once for
the frozen candidate and are never used for tuning.

Raw-validation reports also record genuine within-match snapshot cadence and
the event-level label opportunity at each registered horizon. These diagnostics
do not interpolate observations and are not treated as model performance.
When a sampling frame is supplied, validation additionally requires the exact
route-platform/patch cross-product and stage-specific count in every cell.
Registered-pilot validation also proves that the raw inventory exactly
materializes the checksum-bound frozen selection; route and patch counts alone
cannot substitute for that identity binding.

## Riot and data notice

This project is not endorsed by Riot Games and does not reflect the views or
opinions of Riot Games or anyone officially involved in producing or managing
Riot Games properties. Riot Games and all associated properties are trademarks
or registered trademarks of Riot Games, Inc.

The legacy Kaggle dataset is distributed separately under CC BY-NC 4.0. It may
support non-commercial research, but it is not a commercial product data asset.
Do not commit Riot API keys, PUUIDs or raw player identifiers.

## Licence and citation

Code is licensed under the [MIT License](LICENSE). Dataset, model and paper
licences are declared separately. Citation metadata is provided in
[`CITATION.cff`](CITATION.cff).
