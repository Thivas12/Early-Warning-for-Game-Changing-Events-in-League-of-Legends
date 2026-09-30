# Novelty audit verification — 30 September 2026

The [defense](../docs/policy-novelty-defense.md) and
[machine-readable evidence](policy-novelty-defense-2026-09-30.json) document the
restricted claim and the stronger controls that reject a toy-performance
advantage over wSOL and a Bayes planner.

## Executed checks

- Full repository suite: **430 passed**, one existing warning, **86.10% branch-inclusive
  coverage**, 233.83 seconds. Required coverage gate: 85%.
- Eight new scientific tests: forward/reverse scans versus dense autograd and
  exhaustive policy enumeration; cooldown boundaries; empty traces; a duplicate
  event-credit counterexample; temporal-loss gradient and match-boundary checks;
  invalid configurations; Bayes planning and the analytical score-only bound.
- Ruff lint and format: pass, 207 files formatted. Strict mypy: pass on 84 source
  files. Whitespace and current-tree credential-pattern checks: pass.
- Pinned-author wSOL parity: 16 configurations, maximum absolute loss error
  `5.960464477539063e-08`, gradient error `1.4901161193847656e-08`.
- Exact and enumerated score-function logit gradients agree within
  `2.7755575615628914e-17` in the report fixture. This concerns action-sampling
  variance conditional on a fixed trace, not total training uncertainty.
- All four tested wSOL variants and the Bayes planner reach 100% timely-event
  recall and .2 non-timely alarms per episode on the constructed population,
  matching the original exact-credit candidate. No held-out performance is
  estimated by this diagnostic.

The report records source SHA-256 hashes and pinned author-source provenance.
Author code is not vendored. Frozen scheduled-policy training modules, the
original synthetic-control script and private-data launch configuration have no
changes in this audit. CPU execution is verified; CUDA execution and expanded
private-data comparisons have not run here. No final-test payloads were read.

First-ever novelty, general superiority and real-data improvement are **not
established**. The existing six-model private experiment lacks the newly
required temporal-loss and planning baselines and remains exploratory.
