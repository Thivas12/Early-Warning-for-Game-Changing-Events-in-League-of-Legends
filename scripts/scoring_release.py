"""Hash-bound committed analysis release, issued only before fitted-model scoring."""

from __future__ import annotations

import argparse
import datetime
import fcntl
import hashlib
import json
import subprocess
from pathlib import Path

from scripts.export_league_development import require


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def committed_sources(repo, commit, paths):
    require(bool(paths) and len(set(paths)) == len(paths), "Analysis sources required")
    full = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"], cwd=repo, text=True
    ).strip()
    values = {}
    for name in paths:
        p = Path(name)
        require(not p.is_absolute() and ".." not in p.parts, "Source must be repository-relative")
        content = subprocess.check_output(["git", "show", f"{full}:{p.as_posix()}"], cwd=repo)
        value = hashlib.sha256(content).hexdigest()
        require(digest(repo / p) == value, "Analysis source differs from committed bytes")
        values[p.as_posix()] = value
    return full, values


def issue(repo, study, plan, commit, paths):
    """Caller holds the study's exclusive lock; never backfill a scored study."""
    require(not (study / "summary.json").exists(), "Study already scored")
    require(not list(study.glob("*/seed-*/report.json")), "Study already scored")
    require(not list(study.glob("*/seed-*/calibration-scores*")), "Scoring already started")
    plan_name = plan.resolve().relative_to(repo.resolve()).as_posix()
    full, sources = committed_sources(repo, commit, [*paths, plan_name])
    value = {
        "schema_version": "league-committed-scoring-release-v1",
        "recorded_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "analysis_commit": full,
        "sources_sha256": sources,
        "plan": plan_name,
        "training_freeze_sha256": digest(study / "freeze.json"),
    }
    path = study / "analysis-release.json"
    # An existing release is never replaced silently.
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
    return value


def verify(repo, study, plan, paths):
    path = study / "analysis-release.json"
    require(path.exists(), "Awaiting committed analysis release; preserve trained checkpoints")
    value = json.loads(path.read_bytes())
    plan_name = plan.resolve().relative_to(repo.resolve()).as_posix()
    full, sources = committed_sources(repo, value["analysis_commit"], [*paths, plan_name])
    require(
        value["schema_version"] == "league-committed-scoring-release-v1"
        and value["analysis_commit"] == full
        and value["sources_sha256"] == sources
        and value["plan"] == plan_name
        and value["training_freeze_sha256"] == digest(study / "freeze.json"),
        "Scoring release binding differs",
    )
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "study", "plan"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--source", action="append")
    sources.add_argument("--clock-history", action="store_true")
    args = parser.parse_args()
    if args.clock_history:
        from scripts.run_clock_history_released import SOURCES

        args.source = list(SOURCES)
    with (args.study / "experiment.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print(
            json.dumps(issue(args.repo, args.study, args.plan, args.commit, args.source), indent=2)
        )
