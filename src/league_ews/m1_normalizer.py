"""Fit M1 participant scaling on frozen training graph shards only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.graph import FEATURE_NAMES
from league_ews.m1_graph_staging import MATCHES_PER_SHARD
from league_ews.m1_graph_window import EDGE_TYPES, STEPS

CONTINUOUS = tuple(range(3, 10))
POSITION = (8, 9)
TRAIN_SHARDS = 24000 // MATCHES_PER_SHARD
TOTAL_SHARDS = 30000 // MATCHES_PER_SHARD


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _validated_manifest(root: Path) -> tuple[bytes, dict[str, Any]]:
    content = (root / "staging-manifest.json").read_bytes()
    manifest = json.loads(content)
    contract = {
        "schema_version": "league-ews-m1-graph-staging-v1",
        "steps": STEPS,
        "edge_types": list(EDGE_TYPES),
        "targets": list(LABELS),
        "matches_per_shard": MATCHES_PER_SHARD,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
        "complete": True,
    }
    if not isinstance(manifest, dict) or any(
        manifest.get(key) != value for key, value in contract.items()
    ):
        raise ValueError("M1 graph staging is incomplete or its input contract changed")
    if any(
        not isinstance(manifest.get(key), str) or len(manifest[key]) != 64
        for key in ("split_sha256", "processing_manifest_sha256", "plan_sha256", "freeze_sha256")
    ):
        raise ValueError("M1 graph staging input bindings are invalid")
    shards = manifest.get("shards")
    if not isinstance(shards, list) or len(shards) != TOTAL_SHARDS:
        raise ValueError("M1 graph staging requires 240 train and 60 calibration shards")
    for index, entry in enumerate(shards):
        partition = "train" if index < TRAIN_SHARDS else "calibration"
        start = (index if index < TRAIN_SHARDS else index - TRAIN_SHARDS) * MATCHES_PER_SHARD
        filename = f"{partition}.{start:05d}.npz"
        if not isinstance(entry, dict) or any(
            entry.get(key) != value
            for key, value in {
                "partition": partition,
                "start": start,
                "matches": MATCHES_PER_SHARD,
                "file": filename,
            }.items()
        ):
            raise ValueError("M1 graph shard inventory differs from frozen split")
        rows = entry.get("observations")
        if type(rows) is not int or rows < MATCHES_PER_SHARD:
            raise ValueError("M1 graph shard observation inventory is invalid")
        path = root / "shards" / filename
        if not path.is_file() or _sha(path.read_bytes()) != entry.get("sha256"):
            raise ValueError("M1 graph shard checksum differs from manifest")
    expected = {str(entry["file"]) for entry in shards}
    if {path.name for path in (root / "shards").iterdir()} != expected:
        raise ValueError("M1 graph shard directory differs from frozen inventory")
    return content, manifest


def _training_values(root: Path, entry: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """Read current participant channels once, excluding missing coordinates."""

    with np.load(root / "shards" / entry["file"], allow_pickle=False) as shard:
        if set(shard.files) != {
            "nodes",
            "edges",
            "history_mask",
            "ages_minutes",
            "targets",
            "hazard_targets",
            "match_offsets",
        }:
            raise ValueError("M1 training shard array inventory differs")
        nodes = shard["nodes"]
        mask = shard["history_mask"]
        offsets = shard["match_offsets"]
        rows = entry["observations"]
        if (
            nodes.shape != (rows, STEPS, 12, len(FEATURE_NAMES))
            or nodes.dtype != np.float32
            or mask.shape != (rows, STEPS)
            or mask.dtype != np.bool_
            or offsets.shape != (MATCHES_PER_SHARD + 1,)
            or offsets.dtype != np.int64
            or int(offsets[0]) != 0
            or int(offsets[-1]) != rows
            or not np.all(np.diff(offsets) > 0)
            or not np.all(mask[:, -1])
            or not np.isfinite(nodes).all()
        ):
            raise ValueError("M1 training shard dimensions or current frame differ")
        current = nodes[:, -1, :10]
        if (
            not np.all(current[:, :, 0] == 1)
            or not np.all(current[:, :, 1] == 0)
            or not np.isin(current[:, :, 10], (0, 1)).all()
            or np.any(current[:, :, 8:10][current[:, :, 10] == 0] != 0)
        ):
            raise ValueError("M1 participant or position-missingness channels differ")
        return current[:, :, CONTINUOUS].astype(np.float64), current[:, :, 10] == 1


def fit_m1_normalizer(staging_root: str | Path, output: str | Path) -> dict[str, Any]:
    """Fit only current train frames; calibration shard bytes are hashed, never decoded."""

    root = Path(staging_root)
    manifest_bytes, manifest = _validated_manifest(root)
    counts = np.zeros(len(CONTINUOUS), dtype=np.int64)
    means = np.zeros(len(CONTINUOUS), dtype=np.float64)
    m2 = np.zeros(len(CONTINUOUS), dtype=np.float64)
    observations = 0
    for entry in manifest["shards"][:TRAIN_SHARDS]:
        values, position_present = _training_values(root, entry)
        observations += int(entry["observations"])
        for column, feature in enumerate(CONTINUOUS):
            present = (
                values[:, :, column][position_present]
                if feature in POSITION
                else values[:, :, column].ravel()
            )
            n = len(present)
            if not n:
                continue
            batch_mean = float(present.mean())
            batch_m2 = float(np.sum((present - batch_mean) ** 2))
            total = int(counts[column]) + n
            delta = batch_mean - means[column]
            m2[column] += batch_m2 + delta * delta * int(counts[column]) * n / total
            means[column] += delta * n / total
            counts[column] = total
    scale = np.sqrt(np.divide(m2, counts, out=np.zeros_like(m2), where=counts > 0))
    zero_variance = (counts == 0) | (scale == 0)
    means[zero_variance] = 0
    scale[zero_variance] = 1
    report: dict[str, Any] = {
        "schema_version": "league-ews-m1-normalizer-v1",
        "staging_manifest_sha256": _sha(manifest_bytes),
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
        "mean": means.tolist(),
        "scale": scale.tolist(),
        "present_counts": counts.tolist(),
        "training_observations": observations,
        "train_matches": 24000,
        "calibration_matches_unread": 6000,
        "test_matches_unread": 6000,
        "identifiers_in_report": False,
    }
    target = Path(output)
    serialized = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if target.exists():
        if target.read_bytes() != serialized:
            raise ValueError("Existing M1 normalizer differs from frozen training statistics")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix(target.suffix + ".partial")
        partial.write_bytes(serialized)
        partial.replace(target)
    return {
        "schema_version": report["schema_version"],
        "staging_manifest_sha256": report["staging_manifest_sha256"],
        "training_observations": observations,
        "train_matches": 24000,
        "calibration_matches_unread": 6000,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
        "output": str(target),
    }


def apply_m1_normalizer(
    nodes: np.ndarray, history_mask: np.ndarray, normalizer: dict[str, Any]
) -> np.ndarray:
    """Scale present participant values; preserve padding, objectives and missing positions."""

    if (
        normalizer.get("schema_version") != "league-ews-m1-normalizer-v1"
        or normalizer.get("node_features") != list(FEATURE_NAMES)
        or normalizer.get("normalized_feature_indices") != list(CONTINUOUS)
        or nodes.ndim != 4
        or nodes.shape[1:] != (STEPS, 12, len(FEATURE_NAMES))
        or nodes.dtype != np.float32
        or history_mask.shape != nodes.shape[:2]
        or history_mask.dtype != np.bool_
    ):
        raise ValueError("M1 normalizer and graph contracts differ")
    mean = np.asarray(normalizer["mean"], dtype=np.float64)
    scale = np.asarray(normalizer["scale"], dtype=np.float64)
    if (
        mean.shape != (len(CONTINUOUS),)
        or scale.shape != (len(CONTINUOUS),)
        or not np.isfinite(mean).all()
        or not np.isfinite(scale).all()
        or np.any(scale <= 0)
        or not np.isfinite(nodes).all()
    ):
        raise ValueError("M1 normalizer statistics or graph inputs are invalid")
    result = nodes.copy()
    active = np.broadcast_to(history_mask[:, :, None], (*history_mask.shape, 10))
    for column, feature in enumerate(CONTINUOUS):
        present = active
        if feature in POSITION:
            present = active & (nodes[:, :, :10, 10] == 1)
        values = result[:, :, :10, feature]
        transformed = (values.astype(np.float64) - mean[column]) / scale[column]
        values[present] = transformed[present].astype(np.float32)
    return result
