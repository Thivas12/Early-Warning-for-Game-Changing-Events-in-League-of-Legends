# B4 temporal baseline: causal input contract

This is the next baseline after the registered B3 calibration and event-level
alert evaluation. The final test patch 16.17 stays unread while the model and
operating policy are built and frozen on earlier patches.

`src/league_ews/b4_sequence.py` constructs one sequence per genuine timeline
observation. Each sequence contains the current frame and at most seven earlier
frames **from the same match**. It never interpolates missing minutes, reaches
into a different match, or reads a frame later than the prediction timestamp.
Short histories are left-padded and carry an explicit history mask. Every real
frame has its actual age in minutes relative to the prediction time. The 27
causal B3 feature values occupy separate channels from 27 missingness bits;
missing numeric values are set to zero in the value channel. The 12 strict
future labels are returned in a separate array, not among the model inputs.

The window function deliberately returns unscaled values. A later trainer must
fit feature scaling and any model selection on patches 16.12–16.15 only, using
a grouped inner training split where needed. It may score and set thresholds
on patch 16.16. Ten fixed seeds are required by the registered neural
experiment protocol, with all seeds reported. The 16.17 patch remains reserved
for a single evaluation after the model and policy are locked. B4 remains a
secondary sequence control; the registered H1 comparison is M1 against B3.

This chunk establishes and tests the causal window contract. It does not fit
a neural model or create a private artifact, and needs no Riot credential.

## Bounded private staging

After the final processed audit and frozen split, `make stage-b4-sequences
MAX_NEW_SHARDS=1` stages one 500-match canary shard. If it completes, `make
stage-b4-sequences-all` finishes the 24,000 training and 6,000 calibration
matches in four-shard process chunks. A normal partial invocation returns
success with `complete: false`; rerunning resumes at the next shard. Each
shard is an atomic compressed NumPy file with sequence inputs, masks, labels
and match row offsets, without match or player identifiers. The ignored
`data/private/b4-sequences/staging-manifest.json` binds every shard checksum to
the audited processed manifest, frozen split and feature contract. An orphan
shard after a process interruption is rechecked against freshly reconstructed
source arrays before it can be recorded. Changed inputs or unexpected files
fail closed. No test-patch payload is opened and no Riot key is required.

The resulting sequence values are not normalized and are not yet a B4 model.
The trainer must derive scaling from staged training shards only, fit all
registered seeds, and score calibration shards while preserving the final
test holdout.

## Training-only normalization

After staging completes, `make fit-b4-normalizer` checks the frozen 60-shard
inventory and every shard checksum. It then reads only the 48 training shard
arrays. Each training observation contributes its current frame once, ignoring
missing values; repeated historical frames do not change the feature moments.
Zero-variance or entirely missing features use an identity transform. The
ignored private `normalizer.json` binds the feature order and fitted statistics
to the staging manifest and frozen split. Applying it scales present numeric
values at real timesteps, preserving missingness bits, age and padding. The
calibration and final test arrays remain unread. This step does not train B4.

## Frozen neural training settings

`make freeze-b4-plan` validates the complete staging inventory, the training
normalizer and `configs/b4-temporal-plan.yaml`, then writes an ignored private
freeze record bound to their exact checksums. This happens before any B4 model
is fitted or calibration predictions are scored. The fixed control is a
mask-aware, 48-unit GRU with twelve outputs, three epochs, AdamW, and ten
specified seeds. Every seed will train on the 24,000 earlier-patch matches;
calibration on patch 16.16 is reserved for threshold selection and reporting,
and cannot be used to select a training seed. The test patch remains sealed.
The trainer will checkpoint after whole shards to bound memory and allow
recovery from WSL interruptions. This freeze step needs no neural runtime.

## Resumable B4 training

After the freeze succeeds, `uv sync --frozen --all-groups --extra b4` installs
the locked CPU-only PyTorch wheel for a stability canary. `make train-b4-seed
SEED=20260915 DEVICE=cpu MAX_NEW_SHARDS=1` runs one 500-match training shard.
The trainer also accepts `DEVICE=cuda` when an NVIDIA driver and CUDA-enabled
PyTorch wheel are available in WSL. The Make target uses `uv run --no-sync` so
it preserves a separately installed CUDA wheel; a seed checkpoint records its
device and torch version and cannot resume under a different runtime. The trainer
loads exactly one training shard at a time, scales with the frozen normalizer,
right-pads real observations for the packed GRU, shuffles rows deterministically
within that shard, and checkpoints the model, AdamW optimizer and RNG state
atomically after each whole shard. Each seed has 48 shards per epoch and three
epochs (144 resumable units). Repeating the same command advances the next
unit. A complete seed has `complete: true`. A process interruption during a
shard replays only that shard from the preceding checkpoint. Only one process
should train a seed at a time; the command also holds a private per-seed lock.

The current chunk trains one specified seed and does not score calibration or
test data. All ten frozen seeds must complete and be reported before comparing
or choosing an alert policy. CPU training remains an option for diagnosis.
Check GPU visibility in WSL and choose the matching official PyTorch CUDA wheel
before starting a GPU seed.

## Calibration scoring after ten complete seeds

After all ten seeds reach 144/144 with the same frozen inputs and PyTorch
runtime, `make score-b4-calibration SEED=20260915` scores one seed on the twelve
staged calibration shards. Repeat for each frozen seed. This command refuses
to score if even one seed is incomplete. It reads only patch 16.16 arrays,
applies the training-only normalizer, and writes an ignored private
`data/private/b4-calibration/seed-*/calibration-scores.npz` with twelve
probabilities per observation, binary targets and match offsets. The companion
report records AP, ROC AUC, Brier score and prevalence for every target, plus
macro AP; it binds every checkpoint checksum, the freeze, the staging manifest,
the normalizer and the score file. The score file contains no match or player
identifiers. It can be reused for a later event-level alert policy, which must
be frozen before reading test-patch data. All ten seed results are retained;
the calibration scores must not be used to choose a preferred seed.

Once every seed has a calibration report, `make summarize-b4-calibration`
verifies the score-file checksums, all ten frozen checkpoints, target truth and
match order across seeds, and recomputes each target's metrics from its saved
probabilities. The ignored private `ten-seed-summary.json` reports all ten
macro AP values and their mean, sample standard deviation and range, with the
same statistics per target. No seed is selected, no final test file is read,
and a changed or missing artifact prevents the summary from being written.
