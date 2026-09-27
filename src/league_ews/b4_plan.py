"""Freeze the B4 neural experiment before fitting or calibration scoring."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from league_ews.b4_normalizer import _validated_manifest
from league_ews.tabular_baseline import FEATURES

SEEDS = list(range(20260915, 20260925))
EXPECTED_PLAN: dict[str, Any] = {
    "schema_version": "league-ews-b4-experiment-plan-v1",
    "freeze_stage": "before-neural-training-and-calibration",
    "model": {
        "family": "masked-gru",
        "input_channels": 55,
        "history_steps": 8,
        "hidden_units": 48,
        "recurrent_layers": 1,
        "output_targets": 12,
    },
    "training": {
        "seeds": SEEDS,
        "epochs": 3,
        "batch_size": 1024,
        "optimizer": "adamw",
        "learning_rate": 0.001,
        "weight_decay": 0.01,
        "loss": "unweighted-binary-cross-entropy-with-logits",
        "checkpoint_unit": "completed-training-shard",
        "training_patch_scope": ["16.12", "16.13", "16.14", "16.15"],
    },
    "calibration": {
        "patch": "16.16",
        "use": "threshold-selection-and-reporting-only",
        "select_training_seed": False,
        "horizon_seconds": 60,
    },
    "test": {
        "patch": "16.17",
        "release": "once-after-all-model-and-alert-policies-frozen",
    },
}


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def freeze_b4_plan(
    staging_root: str | Path,
    normalizer_path: str | Path,
    plan_path: str | Path,
    output: str | Path,
) -> dict[str, Any]:
    """Verify all staged checksums, then bind a fixed plan to train-only scaling."""

    staging_bytes, manifest = _validated_manifest(Path(staging_root))
    normalizer_bytes = Path(normalizer_path).read_bytes()
    normalizer = json.loads(normalizer_bytes)
    counts = np.asarray(normalizer.get("present_counts"), dtype=np.int64)
    mean = np.asarray(normalizer.get("mean"), dtype=np.float64)
    scale = np.asarray(normalizer.get("scale"), dtype=np.float64)
    observations = normalizer.get("training_observations")
    if (
        normalizer.get("schema_version") != "league-ews-b4-normalizer-v1"
        or normalizer.get("staging_manifest_sha256") != _sha(staging_bytes)
        or normalizer.get("split_sha256") != manifest["split_sha256"]
        or normalizer.get("processing_manifest_sha256") != manifest["processing_manifest_sha256"]
        or normalizer.get("features") != list(FEATURES)
        or normalizer.get("train_matches") != 24000
        or normalizer.get("calibration_matches_unread") != 6000
        or normalizer.get("test_matches_unread") != 6000
        or type(observations) is not int
        or observations < 24000
        or counts.shape != (len(FEATURES),)
        or np.any(counts < 0)
        or np.any(counts > observations)
        or mean.shape != (len(FEATURES),)
        or scale.shape != (len(FEATURES),)
        or not np.isfinite(mean).all()
        or not np.isfinite(scale).all()
        or np.any(scale <= 0)
    ):
        raise ValueError("B4 normalizer does not bind to complete frozen training shards")
    plan_bytes = Path(plan_path).read_bytes()
    if yaml.safe_load(plan_bytes) != EXPECTED_PLAN:
        raise ValueError("B4 experiment plan differs from the registered fixed settings")
    frozen: dict[str, Any] = {
        "schema_version": "league-ews-b4-experiment-freeze-v1",
        "staging_manifest_sha256": _sha(staging_bytes),
        "normalizer_sha256": _sha(normalizer_bytes),
        "plan_sha256": _sha(plan_bytes),
        "split_sha256": manifest["split_sha256"],
        "seeds": SEEDS,
        "train_matches": 24000,
        "calibration_matches_unread": 6000,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
    target = Path(output)
    content = (json.dumps(frozen, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if target.exists():
        if target.read_bytes() != content:
            raise ValueError("Existing B4 experiment freeze differs from its bound inputs")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".partial")
        temporary.write_bytes(content)
        temporary.replace(target)
    return frozen
