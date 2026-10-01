# First real three-event experiments in this workspace

**Nine models were fitted on the uploaded League data. No breakthrough or
publishable new method is established.** The first screen does not show a macro
benefit from the tested historical features. The follow-up shows a modest
benefit from aligning labels with useful lead time, an established principle.
The GPU neural study is ready to run on the user's PC; it has not run here.

## Verified data

Archive SHA-256:
`3bdee868abe445947a8573167d4b3b561b60f5d2247f1857f6b538ff603e6a23`.
All 60 shards passed checksum, dtype, shape, within-match chronology and exact
event-time/label checks. All 89 exporter-recorded source files matched.
Every original 10/20/30/60-second label was checked against exact event times.

| Partition | Matches | Observed rows | Baron events | Dragon events | Teamfight events |
|---|---:|---:|---:|---:|---:|
| Training, 16.12–16.15 | 24,000 | 704,967 | 25,600 | 90,990 | 161,658 |
| Calibration, 16.16 | 6,000 | 175,031 | 6,498 | 22,737 | 40,021 |

These are 879,998 genuine observed rows, not forward-filled 10-second rows.
The same training population is reused across models; multiplying by nine does
not create nine times as many independent matches. The export contains no test
payloads or test membership. Its recorded provenance is checked, but unavailable
raw Riot payloads have not been independently re-audited in this workspace.

Baron and Dragon targets mean objective kills/completions. Teamfight retains
the registered kill-episode definition. This is not a pre-attack prediction study.

## Fixed controls and evaluation

HistGradientBoostingClassifier, 200 iterations, learning rate 0.06, at most 31
leaves, minimum 100 samples per leaf, L2=1, unweighted binary log loss, fixed seed
20261001. Automatic early stopping is disabled. All 24,000 training matches are
used for each fit; calibration never enters fitting or hyperparameter selection.

Snapshot uses 27 current values and 27 missingness flags. History adds actual
lag-1/3/7 frames and their ages, giving 219 features. Short histories repeat the
oldest available frame with its actual age. Lags never cross match boundaries.
The snapshot already includes cumulative objectives, time since objectives and
recent-kill summaries. This tests additional past frames beyond those summaries,
not the presence versus absence of all historical information.
This preserves the tree size/depth budget but increases the feature search
space; it is not an equal-feature or neural-capacity attribution experiment.

The first six fits predict the original within-30-second label. After that
screen was completed, a separately frozen follow-up fitted three history models
to the next-event **10–30-second** interval, including both boundaries. The
follow-up is adaptive exploratory research and is identified as such.

Every model emits warnings chronologically on the same actual observation times,
with a 60-second cooldown and one-to-one event credit. Thresholds are selected
on the first 1,500 calibration matches per region. The constraint is at most one
false-plus-late warning per match for each event and region. Fixed thresholds
are then evaluated on the later 1,500 matches per region: 3,000 matches total.
The constraints are per event; they are not a combined three-event attention budget.

## Useful warning recall

All values below are percentages of distinct events warned about with 10–30
seconds of lead in the later calibration matches.

| Event | Snapshot, within 30s | History, within 30s | History, useful 10–30s target |
|---|---:|---:|---:|
| Baron | 19.778% | 19.192% | 19.068% |
| Dragon | 11.687% | 12.093% | 13.081% |
| Teamfight | 2.864% | 2.986% | 3.546% |

**Historical features:** macro difference versus snapshot **−0.0197 percentage
points**, conditional paired 95% interval **[−0.2763, +0.2305]**. The macro result
does not support an improvement. Snapshot Baron also exceeds the North America
warning limit: 1.038 false-plus-late warnings per match. The history models meet
the limit in both regions for all three events. The first screen therefore
does not pass an all-model regional-budget advancement gate.

**Useful-interval training:** macro difference versus the within-30 history
control **+0.4753 percentage points**, conditional paired 95% interval
**[+0.1850, +0.7913]**. All three new models and all three history controls meet
the regional warning limits. Baron nevertheless declines by 0.1234 percentage
points; the event-specific interval crosses zero. This is not improvement on
every task.

The macro intervals use 2,000 paired whole-match bootstrap draws stratified by
region, with the same sampled matches across all three events. They are
conditional on fitted models and selected thresholds. They do not capture
refitting uncertainty, future patch variation, or adaptive search. Secondary
event intervals are unadjusted and are preserved in the JSON reports.

## Warning burden and observation limits

| Event | History within-30: false + late / match | Useful-target: false + late / match | Useful-target North America | Useful-target Europe |
|---|---:|---:|---:|---:|
| Baron | 0.8677 | 0.8637 | 0.9107 | 0.8167 |
| Dragon | 0.8383 | 0.8447 | 0.8513 | 0.8380 |
| Teamfight | 0.8160 | 0.9307 | 0.9587 | 0.9027 |

The teamfight recall gain spends an additional **0.1147 false-plus-late warnings
per match**. These are comparisons under the same maximum budget, not exactly
matched realized burdens, and do not establish uniform alarm-efficiency gains.

Only 1,091/3,241 Baron, 3,736/11,329 Dragon and 6,648/19,795 teamfight events have
an actual observation in their useful lead window. These are schedule opportunity
bounds of about one-third, before accounting for cooldown or prediction error.
They are not Bayes-optimal limits and not limits for a system allowed to schedule
decisions between observations. More clock ticks alone are not new observations.

## Consequences for the paper

1. Do not defend the original temporal/transfer explanation using these tree
   results. Sparse lag features have not shown a macro gain; that neither proves
   nor disproves the original neural encoder's temporal hypothesis.
2. Include useful-target training as a serious control. Its gain is modest here
   and has a warning-burden tradeoff. Do not call objective alignment a novel method.
3. Run the unchanged LeagueEWS/GRU/TCN/snapshot comparison on the PC GPU. The
   [compact CUDA instructions](../docs/compact-gpu-continuation.md) use this same
   archive and preserve checkpoints after every training shard.
4. A neural improvement still requires the history-information and shared-versus-
   independent-task ablations, followed by a frozen confirmatory evaluation.
   This already-inspected calibration patch cannot supply that confirmation.

## Reproducibility and limitations

- [Archive validation](league-upload-validation-2026-10-01.json).
- [Complete first-screen results](league-three-event-tree-summary-2026-10-01.json)
  and [its freeze](league-three-event-tree-freeze-2026-10-01.json).
- [Complete timing-control results](league-three-event-timing-summary-2026-10-01.json)
  and [its freeze](league-three-event-timing-freeze-2026-10-01.json).
- [Model, prediction and source provenance](league-three-event-artifacts-2026-10-01.json).

The provenance record pins the exact executed source commit; later timing-script
edits only change formatting, adjacent-pair iteration syntax and console text.
Use the pinned commit with the commands below to reproduce the recorded source
freeze. Use new output folders when changing source or runtime.

```bash
PYTHONPATH=.:src OMP_NUM_THREADS=6 OPENBLAS_NUM_THREADS=1 python -m scripts.run_three_event_trees --archive /path/to/development.zip
PYTHONPATH=.:src OMP_NUM_THREADS=6 OPENBLAS_NUM_THREADS=1 python -m scripts.run_three_event_timing --archive /path/to/development.zip
```

Training ran on CPU with scikit-learn 1.8.0 and NumPy 2.3.5. These tree methods
use CPU; this does not imply that the user's GPU is unavailable. No real neural
fit or CUDA run was performed here. Twenty-three focused software tests passed:
nine new compact-input/runner tests and fourteen existing continuation tests.
The synthetic test fixtures are implementation checks only. Focused Ruff checks,
shell syntax, Makefile command expansion and `git diff --check` passed.

This is one tree seed and one already-reviewed calibration patch. A narrow
conditional interval, nine trained models, or a large row count cannot establish
a breakthrough, causal task transfer, or international publication quality.
