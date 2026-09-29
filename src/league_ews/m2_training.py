"""Bounded, checksum-bound training of the exploratory two-stream model."""

from __future__ import annotations

import fcntl
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.m1_normalizer import TRAIN_SHARDS
from league_ews.m1_training import _training_shard
from league_ews.m1_training_plan import SEEDS
from league_ews.m2_backend import MODES, TorchM2Backend
from league_ews.m2_plan import _checked_inputs

UNITS_PER_SEED = 3 * TRAIN_SHARDS


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _training_input(
    root: Path, entry: dict[str, Any], normalizer: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if entry["partition"] != "train":
        raise ValueError("M2 training cannot access calibration shards")
    path = root / "shards" / entry["file"]
    content = path.read_bytes()
    if _sha(content) != entry["sha256"]:
        raise ValueError("M2 training shard checksum differs from frozen staging")
    with np.load(io.BytesIO(content), allow_pickle=False) as shard:
        raw_nodes = shard["nodes"]
    scaled, edges, mask, ages, hazards = _training_shard(root, entry, normalizer)
    return raw_nodes, scaled, edges, mask, ages, hazards


def _bound_hybrid(
    staging_root: str | Path,
    normalizer_path: str | Path,
    training_plan_path: str | Path,
    hazards_path: str | Path,
    training_freeze_path: str | Path,
    audit_path: str | Path,
    plan_path: str | Path,
    hybrid_freeze_path: str | Path,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Bind every train/calibration use to the same immutable prefit audit."""

    root = Path(staging_root)
    normalizer_file = Path(normalizer_path)
    audit_file = Path(audit_path)
    plan_file = Path(plan_path)
    manifest, normalizer, m1_binding = _checked_inputs(
        root,
        normalizer_file,
        Path(training_plan_path),
        Path(hazards_path),
        Path(training_freeze_path),
        audit_file,
        plan_file,
    )
    frozen_content = Path(hybrid_freeze_path).read_bytes()
    frozen = json.loads(frozen_content)
    if (
        frozen.get("schema_version") != "league-ews-m2-hybrid-freeze-v1"
        or frozen.get("staging_manifest_sha256")
        != _sha((root / "staging-manifest.json").read_bytes())
        or frozen.get("normalizer_sha256") != _sha(normalizer_file.read_bytes())
        or frozen.get("m1_training_freeze_sha256") != m1_binding
        or frozen.get("spatial_audit_sha256") != _sha(audit_file.read_bytes())
        or frozen.get("plan_sha256") != _sha(plan_file.read_bytes())
        or frozen.get("split_sha256") != manifest["split_sha256"]
        or frozen.get("modes") != list(MODES)
        or frozen.get("seeds") != SEEDS
        or frozen.get("train_matches") != 24000
        or frozen.get("calibration_matches_unread") != 6000
        or frozen.get("test_matches_unread") != 6000
        or frozen.get("identifiers_in_summary") is not False
    ):
        raise ValueError("M2 hybrid training differs from its prefit freeze")
    return manifest, normalizer, _sha(frozen_content)


def train_m2_seed(
    staging_root: str | Path,
    normalizer_path: str | Path,
    training_plan_path: str | Path,
    hazards_path: str | Path,
    training_freeze_path: str | Path,
    audit_path: str | Path,
    plan_path: str | Path,
    hybrid_freeze_path: str | Path,
    output_root: str | Path,
    *,
    mode: str,
    seed: int,
    device: str = "cpu",
    max_new_shards: int = 1,
) -> dict[str, Any]:
    if mode not in MODES or seed not in SEEDS or max_new_shards < 1:
        raise ValueError("M2 training mode, seed or bounded shard count is invalid")
    root = Path(staging_root)
    manifest, normalizer, binding = _bound_hybrid(
        root,
        normalizer_path,
        training_plan_path,
        hazards_path,
        training_freeze_path,
        audit_path,
        plan_path,
        hybrid_freeze_path,
    )
    folder = Path(output_root) / mode / f"seed-{seed}"
    folder.mkdir(parents=True, exist_ok=True)
    checkpoint = folder / "checkpoint.pt"
    with (folder / "training.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        backend = TorchM2Backend(seed, device, mode=mode)
        if checkpoint.exists():
            saved = backend.load(str(checkpoint))
            completed = saved.get("completed_shards")
            if (
                saved.get("schema_version") != "league-ews-m2-hybrid-checkpoint-v1"
                or saved.get("freeze_sha256") != binding
                or saved.get("mode") != mode
                or saved.get("seed") != seed
                or saved.get("device") != backend.device
                or saved.get("torch_version") != backend.version
                or type(completed) is not int
                or not 0 <= completed <= UNITS_PER_SEED
            ):
                raise ValueError("M2 checkpoint differs from frozen inputs or runtime")
            backend.load_state_dict(saved["backend"])
        else:
            completed = 0
        last_loss = None
        last_rows = None
        for unit in range(completed, min(UNITS_PER_SEED, completed + max_new_shards)):
            epoch, index = divmod(unit, TRAIN_SHARDS)
            raw, scaled, edges, mask, ages, hazards = _training_input(
                root, manifest["shards"][index], normalizer
            )
            last_loss, last_rows = backend.train_shard(
                raw,
                scaled,
                edges,
                mask,
                ages,
                hazards,
                seed=seed + 10_000 * epoch + index,
            )
            saved = {
                "schema_version": "league-ews-m2-hybrid-checkpoint-v1",
                "freeze_sha256": binding,
                "mode": mode,
                "seed": seed,
                "device": backend.device,
                "torch_version": backend.version,
                "completed_shards": unit + 1,
                "backend": backend.state_dict(),
            }
            temporary = checkpoint.with_suffix(".pt.partial")
            backend.save(saved, str(temporary))
            temporary.replace(checkpoint)
            print(
                f"M2 {mode} seed {seed}: epoch {epoch + 1}/3, shard {index + 1}/{TRAIN_SHARDS}; "
                f"completed {unit + 1}/{UNITS_PER_SEED}",
                flush=True,
            )
        progress = min(UNITS_PER_SEED, completed + max_new_shards)
        return {
            "schema_version": "league-ews-m2-hybrid-progress-v1",
            "mode": mode,
            "seed": seed,
            "device": backend.device,
            "torch_version": backend.version,
            "completed_shards": progress,
            "total_shards": UNITS_PER_SEED,
            "complete": progress == UNITS_PER_SEED,
            "last_shard_loss": last_loss,
            "last_shard_rows": last_rows,
            "freeze_sha256": binding,
            "checkpoint_sha256": _sha(checkpoint.read_bytes()) if checkpoint.exists() else None,
            "calibration_matches_unread": 6000,
            "test_matches_unread": 6000,
            "identifiers_in_summary": False,
        }
