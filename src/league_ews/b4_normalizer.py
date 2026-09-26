"""Fit and apply B4 feature scaling using only frozen training shards."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.b4_sequence import SEQUENCE_FEATURES, STEPS
from league_ews.baseline_floor import LABELS
from league_ews.tabular_baseline import FEATURES

VALUES = len(FEATURES)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _validated_manifest(root: Path) -> tuple[bytes, dict[str, Any]]:
    content = (root / "staging-manifest.json").read_bytes()
    manifest = json.loads(content)
    expected = {
        "schema_version": "league-ews-b4-staging-v1",
        "sequence_steps": STEPS,
        "sequence_features": list(SEQUENCE_FEATURES),
        "targets": list(LABELS),
        "matches_per_shard": 500,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
        "complete": True,
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("B4 staging is incomplete or its sequence contract changed")
    if any(
        not isinstance(manifest.get(key), str) or len(manifest[key]) != 64
        for key in ("split_sha256", "processing_manifest_sha256")
    ):
        raise ValueError("B4 staging input bindings are invalid")
    shards = manifest.get("shards")
    if not isinstance(shards, list) or len(shards) != 60:
        raise ValueError("B4 staging must contain 48 training and 12 calibration shards")
    for index, entry in enumerate(shards):
        partition = "train" if index < 48 else "calibration"
        start = (index if index < 48 else index - 48) * 500
        if (
            not isinstance(entry, dict)
            or any(
                entry.get(key) != value
                for key, value in {
                    "partition": partition,
                    "start": start,
                    "matches": 500,
                    "file": f"{partition}.{start:05d}.npz",
                }.items()
            )
            or not isinstance(entry.get("observations"), int)
            or entry["observations"] < 500
        ):
            raise ValueError("B4 staging shard inventory differs from the frozen split")
        path = root / "shards" / entry["file"]
        if not path.is_file() or _sha(path.read_bytes()) != entry.get("sha256"):
            raise ValueError("B4 staging shard checksum differs from the manifest")
    return content, manifest


def fit_b4_normalizer(staging_root: str | Path, output: str | Path) -> dict[str, Any]:
    """Fit per-feature moments on one current observation per training row.

    Calibration shard bytes are checksum checked but their arrays are never opened.
    Repeated historical frames therefore do not receive extra statistical weight.
    """

    root = Path(staging_root)
    manifest_bytes, manifest = _validated_manifest(root)
    counts = np.zeros(VALUES, dtype=np.int64)
    means = np.zeros(VALUES, dtype=np.float64)
    m2 = np.zeros(VALUES, dtype=np.float64)
    observations = 0
    for entry in manifest["shards"][:48]:
        with np.load(root / "shards" / entry["file"], allow_pickle=False) as shard:
            if set(shard.files) != {"inputs", "history_mask", "targets", "match_offsets"}:
                raise ValueError("B4 training shard arrays are incomplete")
            inputs = shard["inputs"]
            mask = shard["history_mask"]
            offsets = shard["match_offsets"]
            targets = shard["targets"]
            rows = int(entry["observations"])
            if (
                inputs.shape != (rows, STEPS, len(SEQUENCE_FEATURES))
                or mask.shape != (rows, STEPS)
                or targets.shape != (rows, len(LABELS))
                or offsets.shape != (501,)
                or int(offsets[0]) != 0
                or int(offsets[-1]) != rows
                or not np.all(np.diff(offsets) > 0)
                or not np.all(mask[:, -1])
            ):
                raise ValueError("B4 training shard dimensions or current frame are invalid")
            current = inputs[:, -1, :VALUES].astype(np.float64)
            missing = inputs[:, -1, VALUES : 2 * VALUES]
            if (
                not np.isfinite(current).all()
                or not np.isin(missing, (0, 1)).all()
                or np.any(current[missing == 1] != 0)
            ):
                raise ValueError("B4 training values or missingness channels are invalid")
            observations += rows
            for column in range(VALUES):
                present = current[missing[:, column] == 0, column]
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
        "schema_version": "league-ews-b4-normalizer-v1",
        "staging_manifest_sha256": _sha(manifest_bytes),
        "split_sha256": manifest["split_sha256"],
        "processing_manifest_sha256": manifest["processing_manifest_sha256"],
        "features": list(FEATURES),
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
            raise ValueError("Existing B4 normalizer differs from frozen training statistics")
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


def apply_b4_normalizer(
    inputs: np.ndarray, history_mask: np.ndarray, normalizer: dict[str, Any]
) -> np.ndarray:
    """Scale observed numeric values, retaining missing values and zero padding."""

    if (
        normalizer.get("schema_version") != "league-ews-b4-normalizer-v1"
        or normalizer.get("features") != list(FEATURES)
        or inputs.ndim != 3
        or inputs.shape[1:] != (STEPS, len(SEQUENCE_FEATURES))
        or history_mask.shape != inputs.shape[:2]
    ):
        raise ValueError("B4 normalizer and sequence contracts differ")
    mean = np.asarray(normalizer["mean"], dtype=np.float64)
    scale = np.asarray(normalizer["scale"], dtype=np.float64)
    if (
        mean.shape != (VALUES,)
        or scale.shape != (VALUES,)
        or not np.isfinite(mean).all()
        or not np.isfinite(scale).all()
        or np.any(scale <= 0)
    ):
        raise ValueError("B4 normalizer statistics are invalid")
    result = inputs.copy()
    missing = result[:, :, VALUES : 2 * VALUES]
    present = history_mask.astype(bool)[:, :, None] & (missing == 0)
    values = result[:, :, :VALUES]
    transformed = (values.astype(np.float64) - mean) / scale
    values[present] = transformed[present].astype(values.dtype)
    return result
