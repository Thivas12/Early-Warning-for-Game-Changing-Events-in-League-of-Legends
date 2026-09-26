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
