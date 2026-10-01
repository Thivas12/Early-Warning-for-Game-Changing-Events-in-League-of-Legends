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

**1 October 2026:** The uploaded development archive passed validation, and nine
three-event tree controls were fitted on 24,000 League matches. Added lagged
frames did not improve macro timely recall; training for the useful lead window
gave a modest exploratory gain, with a warning-burden tradeoff. See the
[complete results](reports/league-three-event-results-2026-10-01.md) and
[PC GPU instructions](docs/compact-gpu-continuation.md) for the unchanged
LeagueEWS/GRU/TCN/snapshot neural study. No breakthrough is established; the
patch-16.17 test remains sealed.

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

See [`docs/research-plan.md`](docs/research-plan.md) for the registered plan,
[`docs/research-eda.md`](docs/research-eda.md) for the offline audited data atlas,
[`docs/rare-event-research.md`](docs/rare-event-research.md) for the rare-event
diagnostic and follow-on experiment plan, and
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

## Original LeagueEWS and its continuation

The research starts from the user's MSc **LeagueEWS**: residual TCN with
squeeze-excitation, stacked BiGRUs, cross-attention and shared heads for Baron,
Dragon and teamfights. The [source review and continuation](docs/notebook-continuation.md)
trace the original notebooks, saved metrics and final report, including the
corrections needed to evaluate that architecture fairly.

The implemented continuation retains this model family and compares it with
snapshot, GRU and TCN controls on the existing audited League sequence cache.
It restores all three events and separately reports the original 30-second task.
Twelve fits are planned; **none has been run on real data in this workspace**.
The WSL runner needs the existing cache, without exporting or recollecting it.

## League research status

**This project is exclusively about League of Legends.** The
[scope correction](docs/league-research-scope.md) records the evidence boundary
and the next data-access step. The separate Dota experiments are inactive and
excluded from League results and novelty claims.

The audited League development cohort contains **24,000 training matches /
704,967 genuine observed rows** and **6,000 calibration matches / 175,031 rows**.
Training covers patches 16.12–16.15 and calibration covers 16.16. The 6,000
patch-16.17 test payloads remain sealed according to the saved run records.
Dragon and Baron targets identify objective kills/completions, not first attacks.

| Completed League experiment | Finding | Research conclusion |
|---|---|---|
| [Coordination screen](reports/coordination-screen-real-2026-09-29.md) | Coordination versus history: +0.168 percentage points of timely Dragon recall; paired 95% interval −0.044 to +0.389 | No clear incremental coordination benefit |
| [Timing-objective screen](reports/timely-objective-real-2026-09-30.md) | Training for the useful warning interval improved recall under a false-plus-late budget, but failed the primary regional budget gate | Objective alignment, without established methodological novelty |

These are **exploratory calibration results from the user's WSL runs**. Their
aggregate summaries are available here; the private models have not been refitted
in this workspace. The later calibration half has already been examined and is
not a fresh test. Neither result establishes a breakthrough or state of the art.

The [cooldown-aware warning candidate](docs/cooldown-aware-warning-research.md)
and [adversarial novelty checks](docs/policy-novelty-defense.md) are implemented,
but **no verified real League result exists for this candidate yet**. Synthetic
examples establish implementation behavior only. Its private-data runner is
`make start-scheduled-policy`, with explicit CUDA preflight.

The [notebook continuation](docs/notebook-continuation.md#run-with-the-users-existing-wsl-data)
runs against the audited three-event cache in WSL. The earlier
[export script](scripts/export_league_development.py) remains an optional transfer
route for the separate Dragon coordination cache; it is not a prerequisite for
continuing the original three-event model.

## Archived work outside League

The [Dota archive index](docs/archived-dota-work.md) preserves the historical
reports and their unchanged frozen artifacts, including the 48 neural fits.
Those fits and the additional 7.56 million hero-state rows are Dota work;
they are not League experiments or an expansion of the Riot cohort.

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
