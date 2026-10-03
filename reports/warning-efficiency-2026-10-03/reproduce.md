# Reproduce the warning-efficiency study

Use the frozen development ZIP and completed private controls. Their SHA-256
bindings are in `plan.json` and the study freeze. No test data are needed or
permitted. Do not regenerate the training controls or modify their source trees.
The runner refuses mismatched artifacts and acquires shared control locks.

The execution used Python 3.12.14, NumPy 2.5.3 and the existing research
environment. All computations in this follow-up use CPU and stored scores;
no new fit or GPU allocation is required. Keep the CUDA environment unchanged.
Run from the `research/league-warning-efficiency-20261003` worktree.

```bash
league_root=/home/thivas/work/ai-portfolio/league-ews-audit
league_python="$league_root/.venv/bin/python"
league_archive="$league_root/data/private/league-three-event-export-v1/development.zip"
league_control=/home/thivas/work/ai-portfolio/league-ews-gpu/data/private/compact-notebook-v1
league_history="$league_root/data/private/league-history-ablation-v1"
league_independent="$league_root/data/private/league-task-sharing-v1"
league_pcgrad="$league_root/data/private/league-pcgrad-v1"
league_output="$league_root/data/private/league-warning-efficiency-v1"
league_report=reports/warning-efficiency-2026-10-03

bash scripts/run_warning_efficiency.sh "$league_python" "$league_archive" \
  "$league_control" "$league_history" "$league_independent" "$league_pcgrad" \
  "$league_output" "$league_report/plan.json" --early-only

# The published analysis was committed at 3ec6fc1 before this gate was opened.
# A completed output resumes by verification and does not refit or reselect.
bash scripts/run_warning_efficiency.sh "$league_python" "$league_archive" \
  "$league_control" "$league_history" "$league_independent" "$league_pcgrad" \
  "$league_output" "$league_report/plan.json"

PYTHONPATH=.:src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$league_python" \
  -m scripts.analyse_warning_efficiency --study "$league_output" \
  --archive "$league_archive" --plan "$league_report/plan.json" --output "$league_report"
PYTHONPATH=.:src "$league_python" -m scripts.render_warning_efficiency \
  --output "$league_report"
```

For a fresh replay, use a new empty output directory. Reuse the same runner,
plan, Python/NumPy versions and controls. All 126 early heads must be frozen
before any new later-policy evaluation. On interruption, rerun the identical
command; do not delete existing freezes or checkpoints. Every later NPZ is
bound to both the experiment freeze and the complete early-policy freeze.

Optional figures require Matplotlib 3.11.2. Execution installed it with its
dependencies into `/tmp/league-warning-plot-tools`, using `uv pip --target`,
without changing the training environment. Then:

```bash
PYTHONPATH=/tmp/league-warning-plot-tools:.:src MPLCONFIGDIR=/tmp/league-warning-mpl \
  "$league_python" -m scripts.render_warning_efficiency --output "$league_report" --plots
```

Plot data come only from the aggregate analysis. Source SVG and rendered PNG are
provided. The renderer also losslessly compacts aggregate JSON arrays and short
records for review; the execution record retains raw and published analysis
digests. The SVG date is omitted and its hash salt fixed. Private per-match
counts remain in `league_output/later`; only aggregated sums, policies, intervals,
seed summaries and artifact digests are published. CSVs under `reports` must be
explicitly added because the repository ignores data-like files by default.

Implementation checks:

```bash
PYTHONPATH=.:src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest -q
ruff check .
mypy src/league_ews
```

The existing CPU review environment ran the full suite: 604 passed, one skipped,
85.89% coverage. The 19 new focused cases include independent reference replay,
threshold ties and float boundaries, comparison with SciPy's linear-program
solver, selection gating, identity-preserving resume, tamper rejection and
paired bootstrap checks. Artificial fixtures do not contribute empirical claims.
