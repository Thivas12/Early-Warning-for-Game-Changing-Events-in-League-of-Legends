"""Future runs: finish checkpointed training, then require a committed scoring release.

Preserves the frozen v1 implementation. Do not use this to retrain completed fits.
"""

from __future__ import annotations

import argparse
import fcntl
import json
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace

from scripts import run_clock_history as original
from scripts.export_league_development import require
from scripts.scoring_release import verify

SOURCES = (
    "scripts/evaluate_clock_history.py",
    "scripts/analyse_clock_history.py",
    "scripts/evaluate_timely_inputs.py",
    "scripts/analyse_timely_inputs.py",
    "scripts/evaluate_timely_neural.py",
    "scripts/evaluate_dense_policy.py",
    "scripts/timely_neural_targets.py",
    "scripts/warning_efficiency.py",
    "scripts/run_warning_efficiency.py",
    "scripts/analyse_neural_screen.py",
    "scripts/audit_neural_results.py",
    "scripts/league_compact_data.py",
    "scripts/export_league_development.py",
    "src/league_ews/coordination_experiment.py",
    "src/league_ews/m1_alert_diagnostics.py",
    "src/league_ews/alert_policy.py",
    "src/league_ews/constants.py",
    "src/league_ews/notebook_experiment.py",
    "scripts/run_clock_history_released.py",
    "scripts/scoring_release.py",
)


def run(args):
    # No completed experiment gets a retrospective release or another fit.
    summary_path = args.output / "summary.json"
    if summary_path.exists():
        return {"status": "already-scored-use-original-results", "summary": str(summary_path)}
    if args.preflight:
        return original.run(args)
    completed = 0
    for family in original.FAMILIES:
        for seed in original.SEEDS:
            p = args.output / family / f"seed-{seed}" / "progress.json"
            if p.exists():
                progress = json.loads(p.read_bytes())
                units = progress["completed_units"]
                require(isinstance(units, int) and 0 <= units <= 576, "Invalid checkpoint progress")
                completed += units
    remaining = 576 * len(original.FAMILIES) * len(original.SEEDS) - completed
    if remaining:
        # The v1 runner returns at this exact update limit, before calibration scoring.
        budget = min(remaining, args.max_new_shards) if args.max_new_shards else remaining
        training = SimpleNamespace(**{**vars(args), "max_new_shards": budget})
        result = original.run(training)
        require(result["status"] == "paused-resume-same-command", "Unexpected training gate")
        return {**result, "next": "resume through this release-aware entry point"}
    if not (args.output / "analysis-release.json").exists():
        return {"status": "awaiting-committed-analysis-release", "new_scores": 0}
    verify(Path(__file__).resolve().parents[1], args.output, args.plan, SOURCES)
    return original.run(SimpleNamespace(**{**vars(args), "max_new_shards": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in (
        "archive",
        "control",
        "control-source",
        "timely",
        "input-controls",
        "output",
        "plan",
    ):
        parser.add_argument(f"--{flag}", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--max-new-shards", type=int, default=0)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    require(args.max_new_shards >= 0, "Invalid shard budget")
    args.output.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        for path, mode, kind in (
            (args.output, "a+b", fcntl.LOCK_EX),
            (args.control, "rb", fcntl.LOCK_SH),
            (args.timely, "rb", fcntl.LOCK_SH),
            (args.input_controls, "rb", fcntl.LOCK_SH),
        ):
            lock = stack.enter_context((path / "experiment.lock").open(mode))
            fcntl.flock(lock, kind | fcntl.LOCK_NB)
        print(json.dumps(run(args), indent=2))
