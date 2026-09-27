"""M1 training can begin only from a complete frozen graph and scaler."""

import hashlib
import json
from pathlib import Path

import pytest

from league_ews import m1_training_plan
from league_ews.cli import build_parser
from league_ews.graph import FEATURE_NAMES
from league_ews.m1_normalizer import CONTINUOUS

CONFIGS = Path(__file__).resolve().parents[1] / "configs"
PLAN = CONFIGS / "rifthazard-m1-training-plan.yaml"
HAZARDS = CONFIGS / "rifthazard-m1-hazards.yaml"


def _inputs(tmp_path, monkeypatch):
    staged_bytes = b"frozen-graph-shards\n"
    manifest = {
        "split_sha256": "a" * 64,
        "processing_manifest_sha256": "b" * 64,
        "plan_sha256": "c" * 64,
        "freeze_sha256": "d" * 64,
        "shards": [{"observations": 704967}],
    }
    monkeypatch.setattr(m1_training_plan, "TRAIN_SHARDS", 1)
    monkeypatch.setattr(
        m1_training_plan, "_validated_manifest", lambda root: (staged_bytes, manifest)
    )
    normalizer = {
        "schema_version": "league-ews-m1-normalizer-v1",
        "staging_manifest_sha256": hashlib.sha256(staged_bytes).hexdigest(),
        **{
            key: manifest[key]
            for key in (
                "split_sha256",
                "processing_manifest_sha256",
                "plan_sha256",
                "freeze_sha256",
            )
        },
        "node_features": list(FEATURE_NAMES),
        "normalized_feature_indices": list(CONTINUOUS),
        "training_observations": 704967,
        "train_matches": 24000,
        "calibration_matches_unread": 6000,
        "test_matches_unread": 6000,
        "identifiers_in_report": False,
        "present_counts": [7049670] * 5 + [7000000] * 2,
        "mean": [0.1] * len(CONTINUOUS),
        "scale": [1.0] * len(CONTINUOUS),
    }
    normalizer_path = tmp_path / "normalizer.json"
    normalizer_path.write_text(json.dumps(normalizer))
    return normalizer_path, normalizer, tmp_path / "training-freeze.json"


def test_freeze_binds_plan_hazards_train_scaling_and_is_immutable(tmp_path, monkeypatch):
    normalizer_path, _, output = _inputs(tmp_path, monkeypatch)
    result = m1_training_plan.freeze_m1_training_plan(
        tmp_path, normalizer_path, PLAN, HAZARDS, output
    )
    assert result["seeds"] == list(range(20260915, 20260925))
    assert result["training_observations"] == 704967
    assert result["test_matches_unread"] == 6000
    assert result["normalizer_sha256"] == hashlib.sha256(normalizer_path.read_bytes()).hexdigest()
    assert result["hazard_supplement_sha256"] == hashlib.sha256(HAZARDS.read_bytes()).hexdigest()
    assert "EUW1_" not in output.read_text()
    assert (
        m1_training_plan.freeze_m1_training_plan(tmp_path, normalizer_path, PLAN, HAZARDS, output)
        == result
    )
    output.write_text("modified")
    with pytest.raises(ValueError, match="Existing"):
        m1_training_plan.freeze_m1_training_plan(tmp_path, normalizer_path, PLAN, HAZARDS, output)


def test_changed_plan_hazard_and_normalizer_fail_closed(tmp_path, monkeypatch):
    normalizer_path, normalizer, output = _inputs(tmp_path, monkeypatch)
    changed_plan = tmp_path / "changed-plan.yaml"
    changed_plan.write_text(PLAN.read_text().replace("epochs: 3", "epochs: 2"))
    with pytest.raises(ValueError, match="training plan"):
        m1_training_plan.freeze_m1_training_plan(
            tmp_path, normalizer_path, changed_plan, HAZARDS, output
        )
    changed_hazards = tmp_path / "changed-hazards.yaml"
    changed_hazards.write_text(HAZARDS.read_text().replace("bins: 6", "bins: 5"))
    with pytest.raises(ValueError, match="hazard supplement"):
        m1_training_plan.freeze_m1_training_plan(
            tmp_path, normalizer_path, PLAN, changed_hazards, output
        )
    normalizer["present_counts"][0] -= 1
    normalizer_path.write_text(json.dumps(normalizer))
    with pytest.raises(ValueError, match="normalizer"):
        m1_training_plan.freeze_m1_training_plan(tmp_path, normalizer_path, PLAN, HAZARDS, output)


def test_changed_staging_binding_and_invalid_scale_fail_closed(tmp_path, monkeypatch):
    normalizer_path, normalizer, output = _inputs(tmp_path, monkeypatch)
    normalizer["staging_manifest_sha256"] = "0" * 64
    normalizer_path.write_text(json.dumps(normalizer))
    with pytest.raises(ValueError, match="normalizer"):
        m1_training_plan.freeze_m1_training_plan(tmp_path, normalizer_path, PLAN, HAZARDS, output)
    normalizer["staging_manifest_sha256"] = hashlib.sha256(b"frozen-graph-shards\n").hexdigest()
    normalizer["scale"][0] = 0
    normalizer_path.write_text(json.dumps(normalizer))
    with pytest.raises(ValueError, match="normalizer"):
        m1_training_plan.freeze_m1_training_plan(tmp_path, normalizer_path, PLAN, HAZARDS, output)


def test_cli_exposes_training_freeze():
    args = build_parser().parse_args(
        [
            "freeze-m1-training",
            "--staging-root",
            "stage",
            "--normalizer",
            "norm.json",
            "--plan",
            "plan.yaml",
            "--hazards",
            "hazard.yaml",
            "--output",
            "freeze.json",
        ]
    )
    assert args.hazards.name == "hazard.yaml"
