from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from league_ews.alert_policy import (
    MatchRisk,
    _calibration_risks,
    evaluate_alerts,
    run_alert_policy,
    select_threshold,
    summarize_alert_policy,
)
from league_ews.tabular_baseline import FEATURES


def test_unique_strict_future_matching_and_cooldown():
    games = [
        MatchRisk(
            times_ms=(0, 20_000, 70_000, 140_000),
            events_ms=(30_000, 90_000, 140_000),
            risks=(0.8, 0.8, 0.9, 0.7),
        ),
        MatchRisk(times_ms=(0, 60_001), events_ms=(0,), risks=(0.0, 0.7)),
    ]
    metrics = evaluate_alerts(games, 0.5)
    assert metrics["alerts"] == 4
    assert metrics["matched_events"] == 2
    assert metrics["false_alerts"] == 2
    assert metrics["precision"] == 0.5
    assert metrics["event_recall"] == 0.5
    assert metrics["event_f1"] == 0.5
    assert metrics["median_lead_seconds"] == 25
    assert metrics["false_alerts_per_game"] == 1
    with pytest.raises(ValueError, match="threshold"):
        evaluate_alerts(games, 0)
    with pytest.raises(ValueError, match="chronological"):
        evaluate_alerts([MatchRisk((5, 5), (), (0.3, 0.3))], 0.1)


def test_event_threshold_selection_maximizes_f1_without_test_data():
    games = [MatchRisk((0, 100_000), (40_000,), (0.9, 0.1))]
    threshold, metrics = select_threshold(games)
    assert 0.1 < threshold <= 0.9
    assert metrics["event_f1"] == 1
    assert metrics["false_alerts"] == 0


class _Classifier:
    def predict_proba(self, x):
        assert x.shape[1] == len(FEATURES)
        probabilities = np.where(x[:, 0] == 0, 0.2, 0.8)
        return np.column_stack([1 - probabilities, probabilities])


def _processed(match_id):
    participants = [
        {
            "participant_id": i,
            "team_id": 100 if i <= 5 else 200,
            "total_gold": 500,
            "xp": 0,
            "level": 1,
            "lane_minions": 0,
            "jungle_minions": 0,
            "position": None,
        }
        for i in range(1, 11)
    ]
    return {
        "schema_version": "league-ews-processed-match-v1",
        "timeline": {
            "match_id": match_id,
            "platform_id": "EUW1",
            "game_version": "16.16.1",
            "game_creation_ms": 1,
            "observations": [
                {"timestamp_ms": timestamp, "participants": participants, "events": []}
                for timestamp in (0, 60_000)
            ],
        },
        "event_index": {"dragon_ms": [50_000]},
        "labels": [
            {"timestamp_ms": timestamp, "y_dragon_60": int(timestamp == 0)}
            for timestamp in (0, 60_000)
        ],
    }


def test_calibration_scores_read_only_bound_processed_matches(tmp_path):
    root = tmp_path / "processed"
    (root / "matches").mkdir(parents=True)
    payload = json.dumps(_processed("EUW1_1")).encode()
    (root / "matches" / "EUW1_1.json").write_bytes(payload)
    from types import SimpleNamespace

    records = {
        "EUW1_1": SimpleNamespace(sha256=hashlib.sha256(payload).hexdigest(), observations=2)
    }
    matches, targets, scores = _calibration_risks(
        root, [{"match_id": "EUW1_1"}], records, "dragon", _Classifier()
    )
    assert matches == [MatchRisk((0, 60_000), (50_000,), (0.2, 0.8))]
    assert targets.tolist() == [1, 0]
    assert scores.tolist() == pytest.approx([0.2, 0.8])
    records["EUW1_1"].sha256 = "0" * 64
    with pytest.raises(ValueError, match="checksum"):
        _calibration_risks(root, [{"match_id": "EUW1_1"}], records, "dragon", _Classifier())


def test_policy_is_bound_and_resume_does_not_rescore(tmp_path, monkeypatch):
    processed = tmp_path / "processed"
    processed.mkdir()
    manifest = {
        "schema_version": "league-ews-processing-manifest-v1",
        "normalizer": "riot-match-v5-normalized-v1",
        "label_policy": "exact-future-events-v1",
        "contains_player_identifiers": False,
        "matches": [
            {
                "match_id": f"EUW1_{i + 1}",
                "game_version": "16.16.1",
                "observations": 1,
                "baron_events": 0,
                "dragon_events": 0,
                "teamfight_events": 0,
                "sha256": "a" * 64,
            }
            for i in range(36000)
        ],
    }
    manifest_path = processed / "processing-manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    processing_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    frozen = {"partitions": {"calibration": [{"match_id": f"EUW1_{i + 1}"} for i in range(6000)]}}
    monkeypatch.setattr("league_ews.alert_policy.freeze_final_split", lambda *args: frozen)
    split = tmp_path / "split.json"
    split.write_text(json.dumps(frozen))
    split_sha = hashlib.sha256(split.read_bytes()).hexdigest()
    floor = tmp_path / "floor"
    floor.mkdir()
    monkeypatch.setattr("league_ews.alert_policy._bound_floor", lambda *args: "f" * 64)
    b3 = tmp_path / "b3"
    b3.mkdir()
    (b3 / "model.y_dragon_60.joblib").write_bytes(b"model")
    (b3 / "report.y_dragon_60.json").write_text(
        json.dumps(
            {
                "schema_version": "league-ews-final-tabular-calibration-v1",
                "label": "y_dragon_60",
                "feature_names": list(FEATURES),
                "split_sha256": split_sha,
                "processing_manifest_sha256": processing_sha,
                "floor_model_sha256": "f" * 64,
                "model_sha256": hashlib.sha256(b"model").hexdigest(),
                "test_matches_unread": 6000,
                "metrics": {"average_precision": 1.0},
            }
        )
    )
    monkeypatch.setattr("league_ews.alert_policy.joblib.load", lambda *args: object())
    monkeypatch.setattr(
        "league_ews.alert_policy._calibration_risks",
        lambda *args: (
            [MatchRisk((0,), (30_000,), (0.9,))] * 6000,
            np.array([1, 1]),
            np.array([0.9, 0.9]),
        ),
    )
    output = tmp_path / "policy"
    args = (
        tmp_path / "raw",
        processed,
        tmp_path / "frame",
        tmp_path / "g2",
        tmp_path / "audit",
        split,
        floor,
        b3,
        output,
    )
    report = run_alert_policy(*args, "dragon")
    assert report["selected_threshold"] <= 0.9
    assert report["calibration_event_metrics"]["event_recall"] == 1
    assert report["test_matches_unread"] == 6000
    monkeypatch.setattr(
        "league_ews.alert_policy._calibration_risks",
        lambda *args: pytest.fail("Resume should not rescore"),
    )
    assert run_alert_policy(*args, "dragon") == report
    for event in ("baron", "teamfight"):
        (output / f"policy.{event}.json").write_text(
            json.dumps({**report, "event": event, "label": f"y_{event}_60"})
        )
    summary = summarize_alert_policy(output)
    assert set(summary["events"]) == {"baron", "dragon", "teamfight"}
    assert summary["test_matches_unread"] == 6000
    changed = json.loads((output / "policy.teamfight.json").read_text())
    changed["split_sha256"] = "x" * 64
    (output / "policy.teamfight.json").write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="inconsistent"):
        summarize_alert_policy(output)
