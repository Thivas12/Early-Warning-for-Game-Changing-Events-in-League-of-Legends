# Reproduce the League continuation analysis

The code is on the local branch `research/league-neural-followup-20261001`.
Implementation commit `8631209` contains the tested training and analysis code;
commit `0365c07` records the original results and follow-up plan before any
follow-up calibration was scored. The original study's checkout and checkpoints
remain under `league-ews-gpu`, at source commit
`0f849a4ce83f374fdcfa001bc49297abee224d67`.

Use the existing environment. Do not reinstall PyTorch or change the frozen
source/runtime while resuming a study. The original and follow-up freezes bind
source hashes, data, model settings and runtime. The development archive is
SHA-256 `3bdee868abe445947a8573167d4b3b561b60f5d2247f1857f6b538ff603e6a23`.
It contains training and calibration only. These commands do not require
patch 16.17 or new collection.

## Paths

```bash
cd /home/thivas/work/ai-portfolio/league-ews-audit/tmp/league-ews-analysis-20261001
export LEAGUE_PYTHON=/home/thivas/work/ai-portfolio/league-ews-audit/.venv/bin/python
export LEAGUE_ARCHIVE=/home/thivas/work/ai-portfolio/league-ews-audit/data/private/league-three-event-export-v1/development.zip
export LEAGUE_CONTROL=/home/thivas/work/ai-portfolio/league-ews-gpu/data/private/compact-notebook-v1
export LEAGUE_FOLLOWUP=/home/thivas/work/ai-portfolio/league-ews-audit/data/private/league-history-ablation-v1
```

## Recompute the completed analyses

The first command checks all original checkpoint and prediction hashes and
refuses incomplete studies. It reproduces the registered primary point estimates
before computing additional paired intervals. Write regenerated outputs to a new
directory to preserve the archived analysis used to select the follow-up.

```bash
PYTHONPATH=.:src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 "$LEAGUE_PYTHON" \
  -m scripts.analyse_neural_screen --study "$LEAGUE_CONTROL" \
  --archive "$LEAGUE_ARCHIVE" --output reports/local/neural-reanalysis

PYTHONPATH=.:src "$LEAGUE_PYTHON" -m scripts.render_neural_tables \
  --input reports/local/neural-reanalysis/neural-analysis.json \
  --output reports/local/neural-reanalysis/tables.md

PYTHONPATH=.:src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 "$LEAGUE_PYTHON" \
  -m scripts.analyse_history_ablation --control "$LEAGUE_CONTROL" \
  --followup "$LEAGUE_FOLLOWUP" --archive "$LEAGUE_ARCHIVE" \
  --output reports/local/neural-reanalysis/history-analysis.json

PYTHONPATH=.:src "$LEAGUE_PYTHON" -m scripts.render_history_tables \
  --original reports/local/neural-reanalysis/neural-analysis.json \
  --followup reports/local/neural-reanalysis/history-analysis.json \
  --output reports/local/neural-reanalysis/history-tables.md
```

The follow-up analysis requires all three fits and reports to be complete.
The seed mean is the mean performance of fixed fits, not an ensemble.
The 2,000 bootstrap draws share sampled matches across events and seeds and
preserve regional strata. See [methods](methods.md).

## Resume an interrupted follow-up

Inspect processes and the log first. The wrapper holds a worker lock, and the
Python runner holds an experiment lock and a read-only shared lock on the
completed control. A duplicate worker is rejected. The resume loads model,
optimizer and RNG state from the last completed shard; it does not reset a fit.

```bash
bash scripts/run_history_ablation.sh "$LEAGUE_PYTHON" "$LEAGUE_ARCHIVE" \
  "$LEAGUE_CONTROL" "$LEAGUE_FOLLOWUP" \
  reports/neural-continuation-2026-10-01/history-ablation-plan.json \
  >> "$LEAGUE_FOLLOWUP/worker.log" 2>&1
```

Keep this command in a persistent terminal or a monitored execution session.
In this execution environment, a detached `nohup` launch did not leave a live
worker. Its canary checkpoint was intact, and monitored execution resumed it.
The wrapper records its exit code. Existing reports are checked against their
checkpoint and prediction hashes before the summary is regenerated.

## Implementation checks

```bash
PYTHONPATH=.:src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 "$LEAGUE_PYTHON" \
  -m pytest -q --no-cov tests/test_neural_analysis.py \
  tests/test_history_ablation.py tests/test_compact_research.py \
  tests/test_notebook_continuation.py
```

The 32 focused tests passed before the follow-up. They check the resampling unit,
paired seed handling, history intervention, causal input isolation, exact resume,
scoring alignment, and the calibration gate. Their small synthetic fixtures are
software checks, not League research results.
