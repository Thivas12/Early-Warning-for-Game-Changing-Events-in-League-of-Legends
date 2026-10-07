"""Audit completed warning-risk provenance and the early-before-later boundary."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from league_ews.coordination_experiment import sha, write_json
from scripts.analyse_warning_risk import load
from scripts.export_league_development import require
from scripts.scoring_release import committed_sources


def run(study, output):
    repo = Path(__file__).resolve().parents[1]
    plan_path = output / "plan.json"
    plan = json.loads(plan_path.read_bytes())
    _, summary, _ = load(study, plan_path)
    release = json.loads((study / "analysis-release.json").read_bytes())
    full, sources = committed_sources(
        repo,
        release["analysis_commit"],
        [*plan["sources"], plan_path.resolve().relative_to(repo).as_posix()],
    )
    require(sources == release["source_sha256"], "Committed policy sources differ")
    commit_time = subprocess.check_output(
        ["git", "show", "-s", "--format=%cI", full], cwd=repo, text=True
    ).strip()
    gate = json.loads((study / "early-gate.json").read_bytes())
    early_files = list((study / "early").glob("*.json"))
    later_files = list((study / "later").glob("*.npz"))
    require(len(early_files) == len(later_files) == 90, "Incomplete policy inventory")
    first_early = min(f.stat().st_mtime for f in early_files)
    last_early = max(f.stat().st_mtime for f in early_files)
    first_later = min(f.stat().st_mtime for f in later_files)
    require(
        datetime.fromisoformat(commit_time).timestamp()
        <= datetime.fromisoformat(release["recorded_at_utc"]).timestamp()
        <= first_early
        and last_early <= datetime.fromisoformat(gate["recorded_at_utc"]).timestamp() <= first_later
        and gate["early_heads"] == 90
        and gate["later_heads"] == 0,
        "Commit/release/early/later ordering differs",
    )
    analysis = json.loads((output / "analysis.json").read_bytes())
    require(
        analysis["full_reference_checks"] == 810000
        and analysis["new_neural_fits"] == analysis["test_payloads_opened"] == 0
        and analysis["study_summary_sha256"] == sha(study / "summary.json")
        and analysis["prior_exact_reproduction"]
        == {
            "model_event_metric_groups": 150,
            "contrast_event_metric_groups": 150,
        },
        "Completed analysis audit differs",
    )
    quality = json.loads((output / "quality-gate.json").read_bytes())
    require(
        quality["status"] == "passed" and quality["plan_sha256"] == sha(plan_path),
        "Quality gate differs",
    )
    require(
        all(sha(repo / p) == h for p, h in quality["source_sha256"].items()),
        "Quality sources differ",
    )
    for name in ("analysis-release.json", "early-gate.json"):
        write_json(output / name, json.loads((study / name).read_bytes()))
    record = {
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "analysis_commit": full,
        "analysis_commit_time_utc": commit_time,
        "first_early_policy_utc": datetime.fromtimestamp(first_early, UTC).isoformat(),
        "first_later_counts_utc": datetime.fromtimestamp(first_later, UTC).isoformat(),
        "protocol_order_met": True,
        "timing_evidence": "Local commit, release and artifact times; not external preregistration",
        "new_neural_fits": 0,
        "total_completed_neural_fits": 69,
        "test_payloads_opened": 0,
        "early_heads": 90,
        "later_heads": 90,
        "previous_counts_reproduced_heads": sum(
            v["previous_counts_reproduced"] for v in summary["heads"].values()
        ),
        "full_reference_checks": analysis["full_reference_checks"],
        "component_reference_checks": analysis["component_reference_checks"],
        "prior_exact_reproduction": analysis["prior_exact_reproduction"],
        "freeze_sha256": sha(study / "freeze.json"),
        "policy_freeze_sha256": sha(study / "policy-freeze.json"),
        "summary_sha256": sha(study / "summary.json"),
        "analysis_release_sha256": sha(study / "analysis-release.json"),
        "early_gate_sha256": sha(study / "early-gate.json"),
        "raw_analysis_sha256": sha(output / "analysis.json"),
        "raw_policies_sha256": sha(output / "early-policies.json"),
        "quality_gate_sha256": sha(output / "quality-gate.json"),
        "quality_gate": quality,
    }
    write_json(output / "execution-record.json", record)
    print(json.dumps({k: v for k, v in record.items() if k != "quality_gate"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.study, args.output)
