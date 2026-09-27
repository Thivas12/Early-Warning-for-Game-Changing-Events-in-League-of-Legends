"""Ten-seed alert summaries are bound to immutable calibration inputs."""

from __future__ import annotations

import hashlib
import json

import pytest

from league_ews import m1_policy_summary
from league_ews.alert_policy import THRESHOLDS
from league_ews.cli import build_parser
from league_ews.constants import EVENTS
from league_ews.m1_training_plan import SEEDS


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _experiment(tmp_path, monkeypatch):
    stage = tmp_path / "staging"
    stage.mkdir()
    staging_bytes = b'{"processing_manifest_sha256":"processed"}'
    (stage / "staging-manifest.json").write_bytes(staging_bytes)
    calibration = tmp_path / "calibration"
    calibration.mkdir()
    (calibration / "ten-seed-summary.json").write_text("calibration")
    b3_root = tmp_path / "b3"
    b3_root.mkdir()
    for event in EVENTS:
        (b3_root / f"policy.{event}.json").write_text(event)
    seed_results = [
        {
            "seed": seed,
            "checkpoint_sha256": f"{seed:064x}",
            "scores_sha256": f"{seed + 1:064x}",
        }
        for seed in SEEDS
    ]
    monkeypatch.setattr(
        m1_policy_summary,
        "summarize_m1_calibration",
        lambda *args: {
            "split_sha256": "split",
            "staging_manifest_sha256": _sha(staging_bytes),
            "seed_results": seed_results,
        },
    )
    monkeypatch.setattr(
        m1_policy_summary,
        "summarize_alert_policy",
        lambda *args: {
            "split_sha256": "split",
            "test_matches_unread": 6000,
            "events": {
                event: {
                    "events": 2,
                    "precision": 0.4,
                    "event_recall": 0.4,
                    "event_f1": 0.4,
                    "false_alerts_per_game": 0.001,
                }
                for event in EVENTS
            },
        },
    )
    root = tmp_path / "policies"
    root.mkdir()
    metrics = {
        "matches": 6000,
        "events": 2,
        "alerts": 2,
        "matched_events": 1,
        "false_alerts": 1,
        "precision": 0.5,
        "event_recall": 0.5,
        "event_f1": 0.5,
        "false_alerts_per_game": 1 / 6000,
        "median_lead_seconds": 15.0,
        "p10_lead_seconds": 10.0,
    }
    for seed_result in seed_results:
        seed = seed_result["seed"]
        report = {
            "schema_version": "league-ews-m1-alert-policy-v1",
            "seed": seed,
            "split_sha256": "split",
            "processing_manifest_sha256": "processed",
            "ten_seed_summary_sha256": _sha((calibration / "ten-seed-summary.json").read_bytes()),
            "checkpoint_sha256": seed_result["checkpoint_sha256"],
            "scores_sha256": seed_result["scores_sha256"],
            "threshold_grid": list(THRESHOLDS),
            "horizon_seconds": 60,
            "cooldown_seconds": 60,
            "criterion": "max-event-f1-then-min-false-alerts-then-max-threshold",
            "calibration_matches": 6000,
            "events": {
                event: {"threshold": THRESHOLDS[30], "calibration_event_metrics": metrics}
                for event in EVENTS
            },
            "selected_seed": None,
            "test_matches_unread": 6000,
            "identifiers_in_report": False,
        }
        (root / f"policy.seed-{seed}.json").write_text(json.dumps(report))
    args = (
        stage,
        tmp_path / "normalizer",
        tmp_path / "plan",
        tmp_path / "hazards",
        tmp_path / "freeze",
        tmp_path / "training",
        calibration,
        tmp_path / "floor",
        tmp_path / "tabular",
        root,
        b3_root,
    )
    return args


def test_summary_reports_all_seeds_and_descriptive_b3(tmp_path, monkeypatch):
    args = _experiment(tmp_path, monkeypatch)
    summary = m1_policy_summary.summarize_m1_alert_policies(*args)
    assert summary["seed_count"] == 10
    assert summary["selected_seed"] is None
    assert summary["test_matches_unread"] == 6000
    assert [record["seed"] for record in summary["seed_reports"]] == SEEDS
    for event in EVENTS:
        assert summary["events"][event]["m1"]["event_f1"]["mean"] == 0.5
        assert summary["events"][event]["b3"]["event_f1"] == 0.4
        assert len(summary["events"][event]["thresholds"]) == 10
    assert m1_policy_summary.summarize_m1_alert_policies(*args) == summary


def test_summary_rejects_tampered_counts_and_missing_policy(tmp_path, monkeypatch):
    args = _experiment(tmp_path, monkeypatch)
    path = args[-2] / f"policy.seed-{SEEDS[-1]}.json"
    report = json.loads(path.read_text())
    report["events"]["baron"]["calibration_event_metrics"]["false_alerts"] = 2
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="event inventory"):
        m1_policy_summary.summarize_m1_alert_policies(*args)
    assert not (args[-2] / "ten-seed-alert-summary.json").exists()
    path.unlink()
    with pytest.raises(FileNotFoundError):
        m1_policy_summary.summarize_m1_alert_policies(*args)


def test_summary_rejects_cross_seed_event_inventory(tmp_path, monkeypatch):
    args = _experiment(tmp_path, monkeypatch)
    path = args[-2] / f"policy.seed-{SEEDS[-1]}.json"
    report = json.loads(path.read_text())
    metrics = report["events"]["teamfight"]["calibration_event_metrics"]
    metrics["events"] = 3
    metrics["event_recall"] = 1 / 3
    metrics["event_f1"] = 2 / 5
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="disagree on event inventory"):
        m1_policy_summary.summarize_m1_alert_policies(*args)


def test_cli_summary_has_no_test_path():
    names = (
        "staging-root",
        "normalizer",
        "plan",
        "hazards",
        "freeze",
        "training-root",
        "calibration-root",
        "floor-root",
        "tabular-root",
        "policy-root",
        "b3-policy-root",
    )
    args = build_parser().parse_args(
        ["summarize-m1-alert-policies", *[part for name in names for part in (f"--{name}", name)]]
    )
    assert args.policy_root.name == "policy-root"
    assert not hasattr(args, "test_root")
