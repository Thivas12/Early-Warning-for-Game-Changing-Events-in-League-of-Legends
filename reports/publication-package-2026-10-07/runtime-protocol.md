# Saved-model runtime measurement

This is a systems microbenchmark supporting the paper and engineering case
study, not another predictive-method experiment. No training, warning-policy
selection, calibration outcome evaluation or held-out payload access is allowed.

Measure the existing equal-weight useful-lead LeagueEWS and TCN fits at all
three original seeds on CPU and CUDA, with batches of 1 and 128. Use the first
training shard of the checksum-bound compact development archive. Reconstruct
the audited eight-frame histories and use 128 evenly spaced training rows,
without selecting rows using labels or scores. Reuse the saved training-only
normalizer and require agreement between the two studies' normalizers.

Load only saved model weights from complete 576-unit checkpoints after checking
their report digests and training-freeze binding. Require expected parameter
counts and CPU/CUDA prediction agreement at rtol 1e-4 and atol 1e-5. This is an
implementation consistency check, not an empirical accuracy measurement.

Use float32, deterministic algorithms, two CPU threads and one interop thread.
Time forward inference plus sigmoid on resident inputs, excluding model loading,
feature construction, transfers, output conversion and warning decisions. Use
20 warmup calls and 100 measured calls per cell; CUDA calls synchronize before
and after the timed work. Batch-one calls cycle over training rows. Report all
24 cells with individual durations, median, p95 and batch-throughput derived
from the median. CUDA memory is PyTorch peak allocated memory, not whole-device
memory or model-storage size. Alternate architecture order across seed blocks.

Commit this protocol and the runner before measurement; the runner compares
all listed source files with that commit and refuses an existing output folder.
Use one execution unless it fails for an explicit technical reason; preserve
partial results and disclose any repair. No minimum favorable speedup or latency
gate is imposed. Report hardware and runtime versions, uncontrolled thermal and
background-load limitations, and every measured seed. These figures cannot
support a network-service latency guarantee or a production-readiness claim.
