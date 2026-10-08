# LeagueEWS: a five-minute technical review

**Keerthivasan Kannan · Applied ML / research engineering · October 2026**

LeagueEWS asks whether three League of Legends event types can be warned about
early enough to help a player. The project rebuilt an MSc predictor after finding
leakage, then used controlled experiments to separate information, supervision,
architecture and warning-policy effects. Its most useful engineering lesson is
that evaluation must reproduce the decisions a system can actually make.

## The five-minute route

| Time | What to inspect | What it demonstrates |
|---|---|---|
| 0–1 min | [Two-page brief](../reports/publication-package-2026-10-07/leagueews-project-brief.pdf) | Problem, scale, evidence and limitations in one place |
| 1–2 min | [Original notebook audit](notebook-continuation.md) | Detecting split leakage, unavailable features and retrospective alert selection; keeping the original evidence intact |
| 2–3 min | [Warning evaluator](../scripts/warning_risk.py) | Chronological actions, cooldown, one-to-one event credit and an independent scalar reference |
| 3–4 min | [Checkpointed runner](../scripts/run_compact_notebook.py) and [models](../src/league_ews/notebook_ews.py) | Resumable PyTorch experiments and explicit input, model and runtime boundaries |
| 4–5 min | [Revised paper](leagueews-paper-revised.md), Sections 5 and 8 | Choosing strong comparators, reporting negative transfer and measuring the CPU/GPU tradeoff |

The development cohort has 30,000 matches and 879,998 native observations. The
completed research inventory contains 69 neural fits. These describe scale and
execution; they do not, by themselves, establish scientific quality.

## A public, reproducible demonstration

From the repository root, using Python 3.12 or 3.13:

```bash
python scripts/verify_publication_package.py
```

This standard-library command checks eight exact effects against their frozen
JSON sources, recalculates 24 runtime summaries from 2,400 timing samples, and
checks document hashes and local evidence links. It needs no GPU, credentials
or private match archive. Expected status: `passed-public-artifact-verification`.
It verifies the published artifacts; retraining and replaying private matches
require the separate data and checkpoint access documented in the
[reproduction guide](../reports/publication-package-2026-10-07/reproduce.md).

## Three decisions worth discussing in an interview

**A strong baseline changed the conclusion.** Under the original warning policy,
the hybrid exceeds GRU by 4.623 macro recall percentage points, but its difference
from TCN is only 0.012 points, with a conditional interval spanning zero. That
prevented the weaker comparator from supporting a broad architecture claim.

**Evaluation changed what counted as success.** The replay scores a warning
when it is emitted. A later score peak cannot replace it. Late and false warnings
consume budget, and one event receives credit only once. This connects the metric
to the alert stream rather than to independently classified rows.

**Hardware choice followed measurement.** The saved hybrid takes 1.540 ms on CPU
and 4.377 ms on GPU at batch one, using medians across three fitted-seed medians.
At batch 128 the GPU is faster. A failed CPU/GPU parity check exposed TF32
precision differences; explicit float32 passed the unchanged tolerance. These
are resident-input model timings, not end-to-end serving latency.

The owner should be ready to explain why splitting overlapping windows leaks
information, why a backward recurrent layer inside an entirely past window can
still be usable online, why rows are not independent bootstrap units, and why
zero observed budget violations do not certify future risk after adaptive
selection. The [case study](leagueews-case-study.md) contains source-linked
details and résumé bullets for the owner to verify.

## Accurate project positioning

Describe this as an **AI-assisted empirical ML and research-engineering project**
with reproducible artifacts and an exploratory working paper. It is not yet an
accepted publication or a deployed player assistant. Future-patch confirmation
remains pending. Material AI assistance is disclosed in the
[authorship and AI-use record](ai-usage.md); project ownership is not a substitute
for understanding and verifying the implementation.
