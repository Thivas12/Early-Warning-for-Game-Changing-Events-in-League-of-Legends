# LeagueEWS · Useful early warnings in League of Legends

**Keerthivasan Kannan · Applied machine learning and research engineering**

Can a model warn about Baron, Dragon and teamfight events early enough to be
useful, while controlling false and late alerts? LeagueEWS investigates that
question with prediction-time-available inputs, reproducible GPU experiments
and chronological warning replay.

**30,000 development matches · 879,998 native observations · 69 neural fits**

[Read the paper](paper/leagueews-2026-10/leagueews-reviewed-paper.pdf) ·
[Two-page project brief](reports/publication-package-2026-10-07/leagueews-project-brief.pdf) ·
[Five-minute technical review](docs/recruiter-walkthrough.md) ·
[Engineering case study](docs/leagueews-case-study.md)

**Status — October 2026:** completed exploratory development study and working
paper. Incremental experiment sweeps have stopped. The future-patch test remains
sealed; the [submission closeout](docs/submission-readiness.md) records the
remaining work. This is not an accepted publication or a deployed player product.

## The research result

![Controlled comparisons with conditional intervals](reports/publication-package-2026-10-07/evidence-overview.png)

The investigation separates explanations that are easy to conflate:

| Controlled question | Result | Interpretation |
|---|---|---|
| Does past state add information beyond timers and current state? | +0.533 macro recall percentage points at 10–30 seconds of lead | Evidence of incremental history information under the tested recipe |
| Does joint training help all events? | −0.664 points at 20–60 seconds versus independent encoders | Sharing is task-dependent; independent models also use more resources |
| Does the hybrid outperform a strong temporal baseline? | +0.242 points versus TCN with matched targets and task weights | Small margin, about 3.14× the parameters, unresolved regional consistency |
| Can conservative selection remove observed warning overruns? | 0/720 regional-cell violations, with 1.818 and 3.114 points of recall loss | Compliance has a cost; this is not a certified future risk guarantee |

These are separate comparisons, not additive effects or one common-policy
leaderboard. All use inspected development calibration. Intervals condition on
fixed fits and selected policies; they do not account for the adaptive research
search. Read the [manuscript](docs/leagueews-paper-revised.md) for absolute recall,
event-level limitations, intervals, negative results and exact policy definitions.

## Engineering behind the evidence

- **Leakage audit:** identified overlapping-window contamination, unavailable
  end-of-match features and retrospective alert peaks in the original MSc
  evaluation. [Audit and preserved originals](docs/notebook-continuation.md).
- **Reliable experiments:** whole-match splits, training-only normalization,
  checkpointed PyTorch execution, and source/data/model hashes.
  [Training runner](scripts/run_compact_notebook.py) ·
  [model implementation](src/league_ews/notebook_ews.py).
- **Decision-level evaluation:** chronological warnings, 60-second cooldown,
  one-to-one event credit, and an independent scalar replay reference. The latest
  predictive study records 810,000 full independent replay checks.
  [Evaluator](scripts/warning_risk.py) ·
  [verification record](reports/warning-risk-2026-10-07/research-report.md).
- **Measured systems tradeoffs:** six saved models, 24 CPU/GPU benchmark cells,
  and 2,400 timing samples. Batch-one hybrid inference is 1.540 ms on CPU versus
  4.377 ms on GPU on the measured laptop; GPU batching changes the comparison.
  A TF32 parity failure and its correction are preserved.
  [Benchmark scope and precision amendment](reports/publication-package-2026-10-07/runtime-protocol-v2.md).

The benchmark measures resident-input model execution, not end-to-end serving.
Software checks establish consistency; they are not independent scientific
replications. Material AI assistance is documented in the [AI-use record](docs/ai-usage.md).

## Verify the public evidence

From the repository root, with Python 3.12 or 3.13:

```bash
python scripts/verify_publication_package.py
```

No GPU, credentials or private data are needed for this standard-library check.
It verifies eight source-linked effects, recomputes all 24 runtime summaries,
and checks published documents and evidence links. It does not retrain models
or replay the private dataset. See the
[full reproduction guide](reports/publication-package-2026-10-07/reproduce.md)
and [editorial revision record](reports/publication-review-2026-10-08/README.md).

For library development:

```bash
uv sync --all-groups
uv run pytest
```

## Repository guide

| Area | Start here |
|---|---|
| Research paper and exact evidence | [Revised manuscript](docs/leagueews-paper-revised.md), [effect records](reports/publication-package-2026-10-07/evidence.json), [absolute baselines](reports/publication-review-2026-10-08/absolute-baselines.json) |
| Research library and tests | [Source](src/league_ews/), [tests](tests/) |
| Protocols and completed studies | [Research history](RESEARCH_HISTORY.md), [experiment stop decision](docs/publication-decision-2026-10-07.md) |
| Data and labels | [League scope](docs/league-research-scope.md), [labels](src/league_ews/labels.py), [provenance manifests](data/manifests/) |
| Confirmation boundary | [Four-claim design](docs/leagueews-confirmation-protocol.md), [submission closeout](docs/submission-readiness.md) |
| Original MSc work | [Preserved notebooks and report](legacy/msc-v1/) |

Baron and Dragon labels identify objective completions, not engagement onsets.
Historical work outside League is archived and excluded from this project's
empirical claims. Raw data, API keys and player identifiers are not committed.

Code: [MIT License](LICENSE). Dataset, model and paper licences are separate.
[Citation metadata](CITATION.cff). The legacy Kaggle data are separately licensed
CC BY-NC 4.0. This project is not endorsed by Riot Games and does not reflect the
views or opinions of Riot Games or anyone officially involved in producing or
managing Riot Games properties. Riot Games and associated properties are
trademarks or registered trademarks of Riot Games, Inc.
