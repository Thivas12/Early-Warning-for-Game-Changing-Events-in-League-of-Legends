from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest
from sklearn.metrics import average_precision_score

from league_ews.baseline_floor import LABELS
from league_ews.calibration_bootstrap import (
    REPLICATES,
    _collect_calibration,
    _sorted_ap_inputs,
    _weighted_ap,
    paired_match_bootstrap,
    run_calibration_bootstrap,
    summarize_calibration_bootstrap,
)
from league_ews.tabular_baseline import FEATURES


def test_weighted_ap_exactly_matches_sklearn_with_tied_scores_and_repeated_matches():
    truth = np.array([1, 0, 0, 1, 1, 0], dtype=np.int8)
    scores = np.array([0.8, 0.8, 0.2, 0.8, 0.4, 0.2])
    groups = np.array([0, 0, 1, 1, 2, 2])
    counts = np.array([2, 0, 3])
    prepared = _sorted_ap_inputs(truth, scores, groups)
    assert _weighted_ap(*prepared, counts) == pytest.approx(
        average_precision_score(truth, scores, sample_weight=counts[groups])
    )
    assert _weighted_ap(*prepared, np.zeros(3, dtype=int)) == 0.0
    with pytest.raises(ValueError, match="equal nonempty"):
        _sorted_ap_inputs(truth[:-1], scores, groups)
    with pytest.raises(ValueError, match="finite"):
        _sorted_ap_inputs(truth, np.array([float("nan")] * 6), groups)


def test_bootstrap_is_paired_deterministic_and_resamples_matches():
    truth = np.array([1, 0, 1, 0, 1, 0], dtype=np.int8)
    b2 = np.array([0.6, 0.6, 0.1, 0.1, 0.5, 0.5])
    b3 = np.array([0.9, 0.2, 0.8, 0.1, 0.7, 0.3])
    groups = np.array([0, 0, 1, 1, 2, 2])
    a = paired_match_bootstrap(truth, b2, b3, groups, matches=3, replicates=30)
    b = paired_match_bootstrap(truth, b2, b3, groups, matches=3, replicates=30)
    assert a == b
    assert a["observed_ap"]["B3"] == pytest.approx(1.0)
    assert a["observed_ap"]["delta"] > 0
    assert a["ci95"]["paired_delta"][0] <= a["ci95"]["paired_delta"][1]
    assert len(a["bootstrap_ap"]["B2"]) == 30
    with pytest.raises(ValueError, match="Invalid match"):
        paired_match_bootstrap(truth, b2, b3, groups, matches=2)
    with pytest.raises(ValueError, match="Invalid match"):
        paired_match_bootstrap(truth[:0], b2[:0], b3[:0], groups[:0], matches=3)


def _payload(match_id: str) -> dict:
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
                {"timestamp_ms": 0, "participants": participants, "events": []},
                {
                    "timestamp_ms": 60_000,
                    "participants": participants,
                    "events": [
                        {
                            "timestamp_ms": 50_000,
                            "event_type": "CHAMPION_KILL",
                            "killer_team_id": 100,
                        }
                    ],
                },
            ],
        },
        "event_index": {},
        "labels": [
            {"timestamp_ms": 0, **{label: 0 for label in LABELS}},
            {"timestamp_ms": 60_000, **{label: 1 for label in LABELS}},
        ],
    }


class _Classifier:
    def predict_proba(self, x):
        assert x.shape[1] == len(FEATURES)
        risk = np.where(x[:, 0] == 0, 0.3, 0.7)
        return np.stack([1 - risk, risk], axis=1)


def test_collect_scores_calibration_only_with_checksum_binding(tmp_path):
    root = tmp_path / "processed"
    (root / "matches").mkdir(parents=True)
    records = {}
    for i in (1, 2):
        match_id = f"EUW1_{i}"
        content = json.dumps(_payload(match_id)).encode()
        (root / "matches" / f"{match_id}.json").write_bytes(content)
        records[match_id] = SimpleNamespace(
            sha256=hashlib.sha256(content).hexdigest(), observations=2
        )
    floor_model = {"prevalence": {"y_dragon_30": 0.5}, "clock_counts": {}, "history_counts": {}}
    entries = [{"match_id": "EUW1_1"}, {"match_id": "EUW1_2"}]
    truth, b2, b3, groups = _collect_calibration(
        root, entries, records, "y_dragon_30", floor_model, _Classifier()
    )
    assert truth.tolist() == [0, 1, 0, 1]
    assert groups.tolist() == [0, 0, 1, 1]
    assert b2.tolist() == [0.5] * 4
    assert b3.tolist() == pytest.approx([0.3, 0.7, 0.3, 0.7])
    records["EUW1_1"].sha256 = "0" * 64
    with pytest.raises(ValueError, match="checksum"):
        _collect_calibration(root, entries, records, "y_dragon_30", floor_model, _Classifier())


def _private_contract(tmp_path, monkeypatch):
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
                "observations": 2,
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
    monkeypatch.setattr("league_ews.calibration_bootstrap.freeze_final_split", lambda *args: frozen)
    split = tmp_path / "split.json"
    split.write_text(json.dumps(frozen))
    split_sha = hashlib.sha256(split.read_bytes()).hexdigest()
    floor = tmp_path / "floor"
    floor.mkdir()
    (floor / "model.json").write_text(
        json.dumps({"schema_version": "league-ews-baseline-floor-v1", "split_sha256": split_sha})
    )
    floor_sha = hashlib.sha256((floor / "model.json").read_bytes()).hexdigest()
    (floor / "calibration-report.json").write_text(
        json.dumps(
            {
                "schema_version": "league-ews-baseline-floor-calibration-v1",
                "model_sha256": floor_sha,
                "split_sha256": split_sha,
                "train_matches": 24000,
                "calibration_matches": 6000,
                "test_matches_unread": 6000,
                "metrics": {"B2": {"y_dragon_30": {"average_precision": 0.5}}},
            }
        )
    )
    b3 = tmp_path / "b3"
    b3.mkdir()
    (b3 / "model.y_dragon_30.joblib").write_bytes(b"test-model")
    b3_report = {
        "schema_version": "league-ews-final-tabular-calibration-v1",
        "label": "y_dragon_30",
        "feature_names": list(FEATURES),
        "split_sha256": split_sha,
        "processing_manifest_sha256": processing_sha,
        "floor_model_sha256": floor_sha,
        "test_matches_unread": 6000,
        "model_sha256": hashlib.sha256(b"test-model").hexdigest(),
        "metrics": {"average_precision": 1.0},
    }
    (b3 / "report.y_dragon_30.json").write_text(json.dumps(b3_report))
    return processed, split, floor, b3


def test_run_checkpoint_provenance_and_summary(tmp_path, monkeypatch):
    processed, split, floor, b3 = _private_contract(tmp_path, monkeypatch)
    monkeypatch.setattr("league_ews.calibration_bootstrap.joblib.load", lambda _path: object())
    monkeypatch.setattr(
        "league_ews.calibration_bootstrap._collect_calibration",
        lambda *args: (
            np.array([0, 1]),
            np.array([0.5, 0.5]),
            np.array([0.1, 0.9]),
            np.array([0, 1]),
        ),
    )
    output = tmp_path / "bootstrap"
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
    report = run_calibration_bootstrap(*args, "y_dragon_30")
    assert report["observed_ap"]["B3"] == pytest.approx(1.0)
    assert report["observed_ap"]["B2"] == pytest.approx(0.5)
    assert report["replicates"] == REPLICATES
    assert report["test_matches_unread"] == 6000
    assert "EUW1_1" not in json.dumps(report)
    assert run_calibration_bootstrap(*args, "y_dragon_30") == report
    with pytest.raises(ValueError, match="Unsupported"):
        run_calibration_bootstrap(*args, "y_win_10")
    # Each target stores the same seeded match draws, so macro deltas are paired.
    sample = json.loads((output / "bootstrap.y_dragon_30.json").read_text())
    for label in LABELS:
        target = dict(sample, label=label)
        (output / f"bootstrap.{label}.json").write_text(json.dumps(target))
    summary = summarize_calibration_bootstrap(output)
    assert summary["targets"] == 12
    assert summary["observed_macro_ap"]["delta"] == pytest.approx(0.5)
    assert summary["test_matches_unread"] == 6000
    target = json.loads((output / "bootstrap.y_baron_10.json").read_text())
    target["seed"] += 1
    (output / "bootstrap.y_baron_10.json").write_text(json.dumps(target))
    with pytest.raises(ValueError, match="inconsistent"):
        summarize_calibration_bootstrap(output)
