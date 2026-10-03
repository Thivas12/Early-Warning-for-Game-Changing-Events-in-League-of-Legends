# Reproduce the PCGrad mechanism study

Training implementation and plan were committed before fitting at `da18592`.
The new worktree is `research/league-gradient-conflict-20261002`. Original GPU,
history-ablation and independent-event worktrees and outputs are preserved.

- Plan SHA-256: `6e8ded516313f68b1ff30053e9d91868ce1cd85a3fea3649c662fd923a2be907`.
- Runtime freeze SHA-256: `3d1234e010b2db987d9818b0e767f861b89ca49c30073fede974171f22aed458`.
- Development archive SHA-256: `3bdee868abe445947a8573167d4b3b561b60f5d2247f1857f6b538ff603e6a23`.
- Original control checkout: `0f849a4ce83f374fdcfa001bc49297abee224d67`.
- Independent-event implementation: `5c66ffe`; completed report branch at `d79db15`.

Use the existing CUDA environment, rather than syncing the repository's CPU
PyTorch lock into it. Actual environment: Python 3.12.14, PyTorch 2.14.0+cu130,
CUDA 13.0, NVIDIA RTX 4060 Laptop 8 GB, driver 610.74. The runner verifies runtime,
archive, original checkpoints/predictions, source hashes, and training-only
normalizer against controls. All three new fits must finish before scoring.

Commands below use illustrative absolute paths. `CUDA_PYTHON` is the existing
environment; `STUDY` must be a separate private directory. Check host processes
and GPU usage first. A single monitored worker owns the output locks. A resumed
run must use identical frozen sources, plan and runtime; it resumes model,
optimizer and CPU/CUDA RNG from the last atomic checkpoint. Do not edit frozen
training files or launch a duplicate worker.

```bash
export CUDA_PYTHON=/path/to/existing/cuda-env/bin/python
export ARCHIVE=/path/to/development.zip
export CONTROL=/path/to/compact-notebook-v1
export CONTROL_SOURCE=/path/to/frozen/league-ews-gpu
export INDEPENDENT=/path/to/league-task-sharing-v1
export STUDY=/path/to/private/league-pcgrad-v1
export REPORT=reports/gradient-conflict-2026-10-02

# Diagnostic reconstruction: do this in a fresh reproduction directory.
# Do not overwrite the committed diagnostic that binds an existing study.
PYTHONPATH=.:src "$CUDA_PYTHON" -m scripts.diagnose_task_gradients \
  --archive "$ARCHIVE" --control "$CONTROL" --independent "$INDEPENDENT" \
  --output /tmp/league-gradient-diagnostics-reproduction.json --device cuda

# One-shard canary, then resume it with the monitored worker.
PYTHONPATH=.:src "$CUDA_PYTHON" -m scripts.run_pcgrad \
  --archive "$ARCHIVE" --control "$CONTROL" --control-source "$CONTROL_SOURCE" \
  --independent "$INDEPENDENT" --output "$STUDY" --plan "$REPORT/plan.json" \
  --device cuda --max-new-shards 1
bash scripts/run_pcgrad.sh "$CUDA_PYTHON" "$ARCHIVE" "$CONTROL" "$STUDY" \
  "$REPORT/plan.json" "$CONTROL_SOURCE" "$INDEPENDENT"

# After the worker exits successfully and summary.json exists:
PYTHONPATH=.:src OPENBLAS_NUM_THREADS=1 "$CUDA_PYTHON" -m scripts.analyse_pcgrad \
  --archive "$ARCHIVE" --control "$CONTROL" --independent "$INDEPENDENT" \
  --study "$STUDY" --output "$REPORT"
PYTHONPATH=.:src "$CUDA_PYTHON" -m scripts.render_pcgrad \
  --input "$REPORT/analysis.json" --output "$REPORT/tables.md"
```

Diagnostic timestamps and file hashes can differ across reconstruction runs;
the selected rows and numerical calculations are deterministic on the pinned
runtime. Cross-device bit identity is not promised. Compare diagnostic content,
not a newly generated timestamp, with the committed selection evidence.

The analysis independently replays new policies, checks match/target alignment
and unchanged source hashes, and preserves the original registered comparison.
It uses 2,000 region-stratified paired whole-match draws, sharing draws across
all models, events and seeds. Its intervals condition on the fitted models and
early-selected policies, and do not cover refitting, adaptive selection or patch
shift. Private predictions, match arrays, checkpoints and model binaries must
not be committed. Only aggregate evidence and reproducible code are public.

Patch 16.17 is prohibited. This study needs no account username, new collection
or external match acquisition.
