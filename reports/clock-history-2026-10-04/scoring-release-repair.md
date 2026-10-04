# Enforced scoring release for future runs

The frozen runner used in this study remains unchanged. Its absence of a
committed-analysis release check caused the documented timing deviation.
`scripts/run_clock_history_released.py` is a new entry point that uses that
same training implementation with a shard limit equal to the remaining updates.
The old runner returns at that boundary before fitted-model calibration scoring.
When all fits are complete, the new entry point returns
`awaiting-committed-analysis-release` without invoking the scoring path.

`scripts/scoring_release.py` issues a release only while holding the exclusive
study lock and only if no score file, partial score file, prediction report or
study summary exists. It checks that the plan, evaluator, analysis and release
code match an existing Git commit byte for byte. The release binds those hashes
to the study's training freeze. The new entry point validates them again before
allowing the original scoring code to run. Missing, changed or invalid releases
stop scoring and preserve checkpoints. Completed studies are not retrained or
retrospectively given release records.

For a future explicitly planned run, use the new entry point instead of the old
shell wrapper, retaining the same argument names. After training stops, commit
the analysis and release code. Issue the record with the complete frozen analysis source set and both release modules:

```bash
PYTHONPATH=.:src "$league_python" -m scripts.scoring_release \
  --repo "$league_worktree" --study "$league_training" \
  --plan "$league_worktree/$league_report/plan.json" --commit "$league_analysis_commit" \
  --clock-history
```

Then resume through `python -m scripts.run_clock_history_released` with the
same training arguments. Do not launch an additional worker or use this repair
to rerun the completed study. The successor entry point is tested software for
future use, not an empirical fit or a retroactive fix of this study's timing.
A future different experiment must declare its own complete analysis source set.
