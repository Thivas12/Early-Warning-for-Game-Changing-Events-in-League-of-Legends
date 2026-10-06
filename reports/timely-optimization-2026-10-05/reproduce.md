# Reproduce the useful-lead optimizer factorial

This branch starts at the completed sharing report, commit `285635c` (draft
PR #83). Diagnostic code and protocol were committed as `54ebaa2`; all 576
training-only probes completed before training protocol `881262a`. The nine
new fits then completed 5,184 shard updates and stopped with zero scores.
Analysis commit `2dbe0dd` precedes the explicit hash-bound scoring release.

Use the existing CUDA environment. The training freeze pins the same Python,
PyTorch, GPU, NumPy, data, normalizer and original source as the useful-lead
joint/TCN control. Do not replace this environment with the CPU dependency lock.
All prior source and study files remain unchanged. The old CUDA-unavailable
test now explicitly mocks unavailable CUDA so it also works on this GPU host;
that fixture correction changes no research source.

Training is complete: preserve the nine checkpoints. The one-shard canary is
part of the first equal-weight fit, not an additional fit. Original-weight
ordinary-sum controls are the three previously completed useful-lead joint
fits. The new cells are equal weights plus ordinary sum, original weights plus
PCGrad, and equal weights plus PCGrad, each with the original three seeds.

The runner resumes completed checkpoints without updating them. It cannot
score before every fit completes and `scripts.scoring_release.verify` matches
the committed analysis, protocol and training freeze. Never backfill a release
after scoring or overwrite a previous release. The [training gate](training-gate.json)
and [scoring gate](scoring-release-gate.json) preserve checkpoint hashes and
zero-score observations. The [quality gate](quality-gate.json) records 676 passed
tests, one skipped, 85.86% coverage, Ruff, mypy on 87 source files and the
credential check. These are software checks, not evidence of a research gain.

From this worktree, after scoring is complete:

```bash
bash scripts/evaluate_timely_optimization.sh \
  /home/thivas/work/ai-portfolio/league-ews-audit/.venv/bin/python \
  /home/thivas/work/ai-portfolio/league-ews-audit \
  /home/thivas/work/ai-portfolio/league-ews-gpu
```

This sequential runner selects every early policy first, records all 288 frozen
heads and zero new later heads, checks that scoring changed no checkpoint, then
replays later matches and computes paired contrasts. It adds 54 heads and
reproduces all 234 prior heads across all five policies. The nine new fits cover
three events and two evaluated horizons for each model. Full independent
reference replay covers two common budget-one policies on all 3,000 later
matches for every new head: 324,000 checks, in addition to component checks.

All models, events, fixed seeds, policies and budgets share the same 2,000
whole-match bootstrap draws, stratified by region. The optimizer interaction
is formed inside every paired draw. Prior model estimates and every prior
contrast, including the history and target-sharing interactions, must reproduce
exactly. The aggregate audit refuses missing prior results.

Only the primary equal-weight ordinary-sum contrast can pass the primary
weighting rule. Longer-lead Baron recovery is a separate prespecified mechanism
endpoint. Neither it nor a favorable secondary optimizer cell can replace a
failed primary result. Report all event harms and nominal/hard-one burden
violations. The shared encoder has the same 1,751,647 parameters in every
optimizer cell; PCGrad's extra computation must be reported.

The analysis remains adaptive exploratory development on repeatedly inspected
calibration matches. Conditional bootstrap intervals omit training, policy
selection and research-search uncertainty. No optimizer novelty, practical
promotion or breakthrough follows from a software gate. Patch 16.17 stays sealed.
