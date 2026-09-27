"""Checkpoint B4 training after each whole staged training shard."""

from __future__ import annotations

import fcntl
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.b4_backend import TorchBackend
from league_ews.b4_normalizer import _validated_manifest, apply_b4_normalizer
from league_ews.b4_plan import freeze_b4_plan
from league_ews.b4_sequence import SEQUENCE_FEATURES, STEPS
from league_ews.baseline_floor import LABELS

UNITS_PER_SEED = 48 * 3


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _new_backend(seed: int, device: str) -> TorchBackend:
    return TorchBackend(seed, device)


def _shard(
    root: Path, entry: dict[str, Any], normalizer: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if entry["partition"] != "train":
        raise ValueError("B4 training cannot load a calibration shard")
    with np.load(root / "shards" / entry["file"], allow_pickle=False) as shard:
        if set(shard.files) != {"inputs", "history_mask", "targets", "match_offsets"}:
            raise ValueError("B4 training shard array inventory differs")
        inputs = shard["inputs"]
        mask = shard["history_mask"]
        targets = shard["targets"]
        offsets = shard["match_offsets"]
        rows = entry["observations"]
        if (
            inputs.shape != (rows, STEPS, len(SEQUENCE_FEATURES))
            or mask.shape != (rows, STEPS)
            or mask.dtype != np.bool_
            or targets.shape != (rows, len(LABELS))
            or offsets.shape != (501,)
            or int(offsets[0]) != 0
            or int(offsets[-1]) != rows
            or not np.all(np.diff(offsets) > 0)
            or not np.isin(targets, (0, 1)).all()
        ):
            raise ValueError("B4 training shard dimensions, offsets or targets differ")
        scaled = apply_b4_normalizer(inputs, mask, normalizer)
        if not np.isfinite(scaled).all():
            raise ValueError("B4 scaled inputs contain nonfinite values")
        return scaled, mask, targets


def train_b4_seed(
    staging_root: str | Path,
    normalizer_path: str | Path,
    plan_path: str | Path,
    freeze_path: str | Path,
    output_root: str | Path,
    *,
    seed: int,
    device: str = "cpu",
    max_new_shards: int = 1,
) -> dict[str, Any]:
    """Resume one fixed seed; calibration arrays and test payloads stay unread."""

    if max_new_shards < 1:
        raise ValueError("B4 shard budget must be positive")
    stage = Path(staging_root)
    frozen = freeze_b4_plan(stage, normalizer_path, plan_path, freeze_path)
    if seed not in frozen["seeds"]:
        raise ValueError("B4 seed is absent from the frozen ten-seed experiment")
    freeze_bytes = Path(freeze_path).read_bytes()
    _, manifest = _validated_manifest(stage)
    normalizer = json.loads(Path(normalizer_path).read_bytes())
    binding = _sha(freeze_bytes)
    folder = Path(output_root) / f"seed-{seed}"
    folder.mkdir(parents=True, exist_ok=True)
    checkpoint = folder / "checkpoint.pt"
    with (folder / "training.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        backend = _new_backend(seed, device)
        if checkpoint.exists():
            saved = backend.load(str(checkpoint))
            completed = saved.get("completed_shards")
            if (
                saved.get("schema_version") != "league-ews-b4-training-checkpoint-v1"
                or saved.get("freeze_sha256") != binding
                or saved.get("seed") != seed
                or saved.get("device") != backend.device
                or saved.get("torch_version") != backend.version
                or type(completed) is not int
                or not 0 <= completed <= UNITS_PER_SEED
            ):
                raise ValueError("B4 checkpoint differs from frozen inputs or step range")
            backend.load_state_dict(saved["backend"])
        else:
            completed = 0
        last_loss = None
        last_rows = None
        for unit in range(completed, min(UNITS_PER_SEED, completed + max_new_shards)):
            epoch, shard_index = divmod(unit, 48)
            entry = manifest["shards"][shard_index]
            x, mask, targets = _shard(stage, entry, normalizer)
            last_loss, last_rows = backend.train_shard(
                x, mask, targets, seed=seed + 10_000 * epoch + shard_index
            )
            state = {
                "schema_version": "league-ews-b4-training-checkpoint-v1",
                "freeze_sha256": binding,
                "seed": seed,
                "device": backend.device,
                "torch_version": backend.version,
                "completed_shards": unit + 1,
                "backend": backend.state_dict(),
            }
            temporary = checkpoint.with_suffix(".pt.partial")
            backend.save(state, str(temporary))
            temporary.replace(checkpoint)
            print(
                f"B4 seed {seed}: epoch {epoch + 1}/3, shard {shard_index + 1}/48; "
                f"completed {unit + 1}/{UNITS_PER_SEED}",
                flush=True,
            )
        progress = min(UNITS_PER_SEED, completed + max_new_shards)
        return {
            "schema_version": "league-ews-b4-training-progress-v1",
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
