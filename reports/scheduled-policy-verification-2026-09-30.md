# Cooldown-policy implementation verification

Date: 30 September 2026. Scope: code and synthetic controls. This report contains
no new private League training or test-set result.

- Whole repository: **422 tests passed**, one existing scalar-conversion warning,
  227.76 seconds. Coverage **85.97%**, exceeding the required 85% gate.
- Eight new scientific/integration tests passed. They cover exhaustive
  enumeration versus exact marginals, analytic gradients, the harmful early
  alarm gradient, strict causal input selection, irregular observation gaps,
  exact event boundaries, equal action opportunities, padding invariance,
  evaluation-label independence, all six neural variants, source integrity,
  complete run/resume and checksum rejection.
- Ruff lint and formatting pass across 202 Python files; strict mypy passes on
  83 source files. Shell syntax, Git whitespace and repository credential checks
  pass. The CLI help path is callable.
- `scripts/scheduled_policy_controls.py` reproduces the committed toy result.
  The JSON includes source checksums, versions, numerical precision and optimizer
  settings. No randomness is used in the finite-population illustration.
- The previously intermittent B4 exact-recovery test passed in this full run.
  Its frozen implementation was not changed; this is not a claim that its
  earlier intermittent behavior has been diagnosed or repaired.
- CPU execution was tested. CUDA execution and memory use have **not** been
  measured on the user's GPU. The launcher checks CUDA availability before
  starting a background experiment and records the chosen device and build.
- Private raw matches and test payloads were not available in this workspace.
  Integration tests use synthetic source shards with an unreadable test sentinel.
  The private-data experiment remains to be run in WSL.

The preserved user-run timely summary has SHA-256
`4c158769baec118a41262b4eeba54a9892294c773e79e777bcdc59e70adc1586`,
identical to the uploaded file. Those results are interpreted separately in
`timely-objective-real-2026-09-30.md`.

A passing software suite verifies implementation behavior, not scientific novelty,
generalization, competitive performance, or the live utility of alerts.
