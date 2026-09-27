from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from league_ews import b4_plan
from league_ews.cli import build_parser
from league_ews.tabular_baseline import FEATURES

PLAN = Path(__file__).resolve().parents[1] / "configs" / "b4-temporal-plan.yaml"


def _inputs(tmp_path, monkeypatch):
    staging = b"frozen-stage\n"
    manifest = {
        "split_sha256": "a" * 64,
        "processing_manifest_sha256": "b" * 64,
    }
    monkeypatch.setattr(b4_plan, "_validated_manifest", lambda root: (staging, manifest))
    normalizer = {
        "schema_version": "league-ews-b4-normalizer-v1",
        "staging_manifest_sha256": hashlib.sha256(staging).hexdigest(),
        "split_sha256": manifest["split_sha256"],
        "processing_manifest_sha256": manifest["processing_manifest_sha256"],
        "features": list(FEATURES),
        "train_matches": 24000,
        "calibration_matches_unread": 6000,
        "test_matches_unread": 6000,
        "training_observations": 704967,
        "present_counts": [500000] * len(FEATURES),
        "mean": [0.0] * len(FEATURES),
        "scale": [1.0] * len(FEATURES),
    }
    normalizer_path = tmp_path / "normalizer.json"
    normalizer_path.write_text(json.dumps(normalizer))
    return normalizer_path, normalizer, tmp_path / "experiment-freeze.json"


def test_freeze_binds_all_inputs_and_is_immutable(tmp_path, monkeypatch):
    normalizer_path, normalizer, output = _inputs(tmp_path, monkeypatch)
    result = b4_plan.freeze_b4_plan(tmp_path, normalizer_path, PLAN, output)
    assert result["seeds"] == list(range(20260915, 20260925))
    assert result["test_matches_unread"] == 6000
    assert result["normalizer_sha256"] == hashlib.sha256(normalizer_path.read_bytes()).hexdigest()
    assert "EUW1_" not in output.read_text()
    assert b4_plan.freeze_b4_plan(tmp_path, normalizer_path, PLAN, output) == result
    output.write_text("modified")
    with pytest.raises(ValueError, match="Existing"):
        b4_plan.freeze_b4_plan(tmp_path, normalizer_path, PLAN, output)
    output.unlink()
    normalizer["staging_manifest_sha256"] = "0" * 64
    normalizer_path.write_text(json.dumps(normalizer))
    with pytest.raises(ValueError, match="normalizer"):
        b4_plan.freeze_b4_plan(tmp_path, normalizer_path, PLAN, output)


def test_freeze_rejects_changed_plan_and_invalid_statistics(tmp_path, monkeypatch):
    normalizer_path, normalizer, output = _inputs(tmp_path, monkeypatch)
    changed = tmp_path / "changed.yaml"
    changed.write_text(PLAN.read_text().replace("epochs: 3", "epochs: 2"))
    with pytest.raises(ValueError, match="plan differs"):
        b4_plan.freeze_b4_plan(tmp_path, normalizer_path, changed, output)
    normalizer["scale"][0] = 0
    normalizer_path.write_text(json.dumps(normalizer))
    with pytest.raises(ValueError, match="normalizer"):
        b4_plan.freeze_b4_plan(tmp_path, normalizer_path, PLAN, output)


def test_cli_exposes_freeze_command():
    args = build_parser().parse_args(
        [
            "freeze-b4-plan",
            "--staging-root",
            "stage",
            "--normalizer",
            "norm.json",
            "--plan",
            "plan.yaml",
            "--output",
            "freeze.json",
        ]
    )
    assert args.plan.name == "plan.yaml"
