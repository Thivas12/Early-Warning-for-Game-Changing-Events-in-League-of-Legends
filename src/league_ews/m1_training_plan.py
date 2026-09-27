"""Freeze the M1 graph-hazard experiment before fitting any model."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from league_ews.graph import FEATURE_NAMES
from league_ews.m1_graph_window import EDGE_TYPES, STEPS
from league_ews.m1_normalizer import CONTINUOUS, TRAIN_SHARDS, _validated_manifest

SEEDS = list(range(20260915, 20260925))
EXPECTED_PLAN: dict[str, Any] = {
    "schema_version": "league-ews-m1-training-plan-v1",
    "freeze_stage": "before-m1-training-or-calibration-scoring",
    "input": {
        "history_steps": STEPS,
        "nodes": 12,
        "node_features": len(FEATURE_NAMES),
        "edge_types": list(EDGE_TYPES),
        "age_units": "minutes",
        "normalizer": "training-only-participant-numeric",
    },
    "model": {
        "family": "relation-aware-temporal-graph-gru",
        "message_layers": 2,
        "message_hidden_units": 64,
        "relation_aggregation": "masked-mean-per-edge-type",
        "temporal_hidden_units": 64,
        "temporal_layers": 1,
        "temporal_readout": "last-real-frame",
        "dropout": 0.1,
        "output": "independent-event-specific-discrete-hazards",
        "event_order": ["baron", "dragon", "teamfight"],
        "hazard_bins": 6,
        "hazard_bin_seconds": 10,
    },
    "training": {
        "seeds": SEEDS,
        "epochs": 3,
        "batch_size": 256,
        "optimizer": "adamw",
        "learning_rate": 0.001,
        "weight_decay": 0.01,
        "loss": "mean-bce-with-logits-over-at-risk-bins",
        "at_risk": "per-event-through-first-event-bin-inclusive",
        "checkpoint_unit": "completed-training-shard",
        "shard_order": "registered-order-with-seeded-within-shard-permutation",
        "training_patches": ["16.12", "16.13", "16.14", "16.15"],
        "model_selection": "report-all-ten-seeds-no-calibration-seed-selection",
    },
    "calibration": {
        "patch": "16.16",
        "use": "thresholds-and-reporting-only",
        "horizon_seconds": [10, 20, 30, 60],
    },
    "test": {"patch": "16.17", "release": "once-after-model-and-policy-freeze"},
    "registered_m1_ablations": [
        "no-positions-or-proximity",
        "no-interaction-edges",
        "no-objective-nodes",
        "no-assistance-history",
        "independent-horizon-heads",
        "fixed-minute-grid",
    ],
}
EXPECTED_HAZARDS: dict[str, Any] = {
    "schema_version": "league-ews-m1-hazard-supplement-v1",
    "experiment_id": "M001",
    "supersedes_model_output": "discrete-competing-hazards",
    "model_output": "independent-event-specific-discrete-hazards",
    "events": ["baron", "dragon", "teamfight"],
    "bin_seconds": 10,
    "bins": 6,
    "horizons_seconds": [10, 20, 30, 60],
    "time_origin": "genuine-observation-timestamp",
    "event_boundary": "strictly-future-through-inclusive-horizon",
    "target": "first-future-event-of-each-type",
    "training_at_risk": "until-first-event-of-that-type-or-horizon-end",
    "cross_event_constraint": "none",
    "calibration_partition": "patch-16.16",
    "test_partition": "patch-16.17-unread-until-model-and-policy-freeze",
}


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def freeze_m1_training_plan(
    staging_root: str | Path,
    normalizer_path: str | Path,
    plan_path: str | Path,
    hazard_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    """Bind every staged checksum and the train-only scaler to the fixed design.

    Calibration shard bytes are hashed by manifest validation; their arrays
    and the sealed test patch are never opened.
    """

    staging_bytes, manifest = _validated_manifest(Path(staging_root))
    normalizer_bytes = Path(normalizer_path).read_bytes()
    normalizer = json.loads(normalizer_bytes)
    if not isinstance(normalizer, dict):
        raise ValueError("M1 normalizer must be a JSON object")
    observations = sum(int(entry["observations"]) for entry in manifest["shards"][:TRAIN_SHARDS])
    counts = np.asarray(normalizer.get("present_counts"), dtype=np.int64)
    mean = np.asarray(normalizer.get("mean"), dtype=np.float64)
    scale = np.asarray(normalizer.get("scale"), dtype=np.float64)
    if (
        normalizer.get("schema_version") != "league-ews-m1-normalizer-v1"
        or normalizer.get("staging_manifest_sha256") != _sha(staging_bytes)
        or any(
            normalizer.get(key) != manifest[key]
            for key in (
                "split_sha256",
                "processing_manifest_sha256",
                "plan_sha256",
                "freeze_sha256",
            )
        )
        or normalizer.get("node_features") != list(FEATURE_NAMES)
        or normalizer.get("normalized_feature_indices") != list(CONTINUOUS)
        or normalizer.get("training_observations") != observations
        or normalizer.get("train_matches") != 24000
        or normalizer.get("calibration_matches_unread") != 6000
        or normalizer.get("test_matches_unread") != 6000
        or normalizer.get("identifiers_in_report") is not False
        or counts.shape != (len(CONTINUOUS),)
        or not np.all(counts[:5] == observations * 10)
        or not np.all(counts[5:] <= observations * 10)
        or np.any(counts[5:] < 0)
        or mean.shape != (len(CONTINUOUS),)
        or scale.shape != (len(CONTINUOUS),)
        or not np.isfinite(mean).all()
        or not np.isfinite(scale).all()
        or np.any(scale <= 0)
    ):
        raise ValueError("M1 normalizer does not bind to the complete frozen train shards")
    plan_bytes = Path(plan_path).read_bytes()
    hazard_bytes = Path(hazard_path).read_bytes()
    if yaml.safe_load(plan_bytes) != EXPECTED_PLAN:
        raise ValueError("M1 training plan differs from registered settings")
    if yaml.safe_load(hazard_bytes) != EXPECTED_HAZARDS:
        raise ValueError("M1 hazard supplement differs from the event target contract")
    frozen: dict[str, Any] = {
        "schema_version": "league-ews-m1-training-freeze-v1",
        "staging_manifest_sha256": _sha(staging_bytes),
        "normalizer_sha256": _sha(normalizer_bytes),
        "training_plan_sha256": _sha(plan_bytes),
        "hazard_supplement_sha256": _sha(hazard_bytes),
        "split_sha256": manifest["split_sha256"],
        "processing_manifest_sha256": manifest["processing_manifest_sha256"],
        "graph_plan_sha256": manifest["plan_sha256"],
        "graph_freeze_sha256": manifest["freeze_sha256"],
        "seeds": SEEDS,
        "train_matches": 24000,
        "training_observations": observations,
        "calibration_matches_unread": 6000,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
    target = Path(output_path)
    content = (json.dumps(frozen, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if target.exists():
        if target.read_bytes() != content:
            raise ValueError("Existing M1 training freeze differs from its bound inputs")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix(target.suffix + ".partial")
        partial.write_bytes(content)
        partial.replace(target)
    return frozen
