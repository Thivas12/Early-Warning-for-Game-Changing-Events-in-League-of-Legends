"""M1 operating points reuse B3's event rule without selecting a seed."""

from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest

from league_ews import m1_alert_policy
from league_ews.baseline_floor import LABELS
from league_ews.cli import build_parser
from league_ews.m1_training_plan import SEEDS


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _fixture(tmp_path, monkeypatch):
    stage = tmp_path / "stage"
    stage.mkdir()
    staging_bytes = b'{"processing_manifest_sha256":"pending"}'
    processed = tmp_path / "processed"
    processed.mkdir()
    processing_bytes = b"private-processed-manifest\n"
    (processed / "processing-manifest.json").write_bytes(processing_bytes)
    staging_bytes = json.dumps({"processing_manifest_sha256": _sha(processing_bytes)}).encode()
    (stage / "staging-manifest.json").write_bytes(staging_bytes)
    split = tmp_path / "split.json"
    split.write_text(
        json.dumps(
            {
                "processing_manifest_sha256": _sha(processing_bytes),
                "partitions": {"calibration": [{"match_id": "A"}, {"match_id": "B"}]},
            }
        )
    )
    split_sha = _sha(split.read_bytes())
    root = tmp_path / "calibration"
    root.mkdir()
    (root / "ten-seed-summary.json").write_text("summary")
    scores = np.tile(np.tile([0.2, 0.3, 0.4, 0.5], 3), (4, 1)).astype(np.float32)
    truth = np.zeros((4, len(LABELS)), dtype=np.int8)
    score_file = root / f"seed-{SEEDS[0]}" / "calibration-scores.npz"
    score_file.parent.mkdir()
    np.savez_compressed(
        score_file, probabilities=scores, targets=truth, match_offsets=np.array([0, 2, 4])
    )
    monkeypatch.setattr(m1_alert_policy, "CAL_MATCHES", 2)
    monkeypatch.setattr(m1_alert_policy, "PROCESSED_MATCHES", 2)
    monkeypatch.setattr(
        m1_alert_policy,
        "summarize_m1_calibration",
        lambda *args: {
            "staging_manifest_sha256": _sha(staging_bytes),
            "split_sha256": split_sha,
            "seed_results": [
                {
                    "seed": seed,
                    "checkpoint_sha256": f"{seed:064x}",
                    "scores_sha256": _sha(score_file.read_bytes()),
                }
                for seed in SEEDS
            ],
        },
    )
    monkeypatch.setattr(
        m1_alert_policy,
        "ProcessingManifest",
        SimpleNamespace(
            model_validate_json=lambda *args: SimpleNamespace(
                matches=[
                    SimpleNamespace(match_id=match_id, sha256="checksum") for match_id in ("A", "B")
                ]
            )
        ),
    )
    payload = {
        "timeline": {"observations": [{"timestamp_ms": 1000}, {"timestamp_ms": 20000}]},
        "labels": [{"timestamp_ms": time, **dict.fromkeys(LABELS, 0)} for time in (1000, 20000)],
        "event_index": {f"{event}_ms": [15000] for event in ("baron", "dragon", "teamfight")},
    }
    monkeypatch.setattr(m1_alert_policy, "_read_match", lambda *args: payload)
    args = (
        stage,
        tmp_path / "normalizer",
        tmp_path / "plan",
        tmp_path / "hazards",
        tmp_path / "freeze",
        tmp_path / "training",
        root,
        tmp_path / "floor",
        tmp_path / "tabular",
        processed,
        split,
        tmp_path / "policy",
    )
    return args, payload, score_file


def test_policy_uses_same_event_rule_for_all_types_and_is_immutable(tmp_path, monkeypatch):
    args, _, _ = _fixture(tmp_path, monkeypatch)
    result = m1_alert_policy.select_m1_alert_policy(*args, seed=SEEDS[0])
    assert result["selected_seed"] is None
    assert result["test_matches_unread"] == 6000
    assert set(result["events"]) == {"baron", "dragon", "teamfight"}
    assert all(
        item["calibration_event_metrics"]["matches"] == 2 for item in result["events"].values()
    )
    assert m1_alert_policy.select_m1_alert_policy(*args, seed=SEEDS[0]) == result
    output = args[-1] / f"policy.seed-{SEEDS[0]}.json"
    output.write_bytes(output.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="Existing M1 alert policy"):
        m1_alert_policy.select_m1_alert_policy(*args, seed=SEEDS[0])


def test_policy_rejects_changed_labels_and_split(tmp_path, monkeypatch):
    args, payload, _ = _fixture(tmp_path, monkeypatch)
    payload["labels"][0][LABELS[0]] = 1
    with pytest.raises(ValueError, match="labels differ"):
        m1_alert_policy.select_m1_alert_policy(*args, seed=SEEDS[0])
    payload["labels"][0][LABELS[0]] = 0
    args[-2].write_bytes(args[-2].read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="split differs"):
        m1_alert_policy.select_m1_alert_policy(*args, seed=SEEDS[0])


def test_cli_requires_private_inputs_and_no_test_path():
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
        "processed",
        "split",
        "output",
    )
    args = build_parser().parse_args(
        [
            "select-m1-alert-policy",
            *[part for name in names for part in (f"--{name}", name)],
            "--seed",
            str(SEEDS[0]),
        ]
    )
    assert args.seed == SEEDS[0]
    assert not hasattr(args, "test_root")
