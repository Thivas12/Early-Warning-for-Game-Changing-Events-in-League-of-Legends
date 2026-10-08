# Runtime protocol amendment: explicit float32 math

All sampling, seeds, devices, batches, timing, reporting and parity tolerances
remain as specified in [version 1](runtime-protocol.md). This amendment changes
only the numerical precision configuration: disable TF32 for both CUDA matrix
multiplication and cuDNN, and request highest float32 matmul precision before
constructing a model. The unchanged v1 runner supplies all measurement logic;
the committed v2 wrapper verifies its own bytes before calling that runner.
Both are bound to the new pre-measurement commit.

The first run stopped after its first two CPU cells when the unchanged
rtol=1e-4, atol=1e-5 CPU/CUDA check failed. Preserve that partial run under
`league-publication-runtime-v1`. A training-only diagnosis on the first saved
hybrid fit found cuDNN TF32 enabled: maximum absolute probability difference
0.00021395087242126465, with 36/1,536 elements outside tolerance. Disabling TF32
reduced the maximum to 0.00000038743019104003906 and produced zero failures.
The tolerance is not relaxed. The original fit and prediction artifacts are
unchanged. This does not retrospectively imply that the CUDA-only predictive
studies used these amended inference settings.

Run the amended measurement once in the separate `league-publication-runtime-v2`
directory. Report explicit precision configuration and all seeds. Runtime is
hardware- and precision-specific; these timings cannot be called the original
training or production-serving latency. If another consistency check fails,
report that failure rather than publishing an incomplete speed comparison.
