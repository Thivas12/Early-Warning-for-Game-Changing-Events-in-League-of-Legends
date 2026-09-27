"""Bounded checkpointed training for one frozen M1 graph-hazard seed."""

from __future__ import annotations

import fcntl
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from league_ews.baseline_floor import LABELS
from league_ews.graph import FEATURE_NAMES
from league_ews.m1_backend import TorchM1Backend, at_risk_mask, right_pad_graphs
from league_ews.m1_graph_staging import MATCHES_PER_SHARD
from league_ews.m1_graph_window import EDGE_TYPES, STEPS
from league_ews.m1_normalizer import TRAIN_SHARDS, apply_m1_normalizer
from league_ews.m1_training_plan import EXPECTED_HAZARDS, EXPECTED_PLAN, SEEDS

UNITS_PER_SEED = TRAIN_SHARDS * 3


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _new_backend(seed: int, device: str) -> TorchM1Backend:
    return TorchM1Backend(seed, device)


def _bound_inputs(
    stage: Path, normalizer_path: Path, plan_path: Path, hazard_path: Path, freeze_path: Path
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Check immutable hashes without decoding calibration shards."""

    manifest_bytes = (stage / "staging-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    normalizer_bytes = normalizer_path.read_bytes()
    normalizer = json.loads(normalizer_bytes)
    plan_bytes = plan_path.read_bytes()
    hazard_bytes = hazard_path.read_bytes()
    freeze_bytes = freeze_path.read_bytes()
    frozen = json.loads(freeze_bytes)
    if (
        not isinstance(manifest, dict)
        or not isinstance(normalizer, dict)
        or not isinstance(frozen, dict)
        or manifest.get("schema_version") != "league-ews-m1-graph-staging-v1"
        or manifest.get("complete") is not True
        or manifest.get("matches_per_shard") != MATCHES_PER_SHARD
        or manifest.get("steps") != STEPS
        or manifest.get("edge_types") != list(EDGE_TYPES)
        or manifest.get("targets") != list(LABELS)
        or manifest.get("test_matches_unread") != 6000
        or normalizer.get("schema_version") != "league-ews-m1-normalizer-v1"
        or normalizer.get("staging_manifest_sha256") != _sha(manifest_bytes)
        or frozen.get("schema_version") != "league-ews-m1-training-freeze-v1"
        or frozen.get("staging_manifest_sha256") != _sha(manifest_bytes)
        or frozen.get("normalizer_sha256") != _sha(normalizer_bytes)
        or frozen.get("training_plan_sha256") != _sha(plan_bytes)
        or frozen.get("hazard_supplement_sha256") != _sha(hazard_bytes)
        or frozen.get("split_sha256") != manifest.get("split_sha256")
        or frozen.get("processing_manifest_sha256") != manifest.get("processing_manifest_sha256")
        or frozen.get("graph_plan_sha256") != manifest.get("plan_sha256")
        or frozen.get("graph_freeze_sha256") != manifest.get("freeze_sha256")
        or frozen.get("seeds") != SEEDS
        or frozen.get("train_matches") != 24000
        or frozen.get("calibration_matches_unread") != 6000
        or frozen.get("test_matches_unread") != 6000
        or frozen.get("identifiers_in_summary") is not False
        or yaml.safe_load(plan_bytes) != EXPECTED_PLAN
        or yaml.safe_load(hazard_bytes) != EXPECTED_HAZARDS
    ):
        raise ValueError("M1 training inputs differ from the frozen experiment")
    shards = manifest.get("shards")
    if not isinstance(shards, list) or len(shards) != 300:
        raise ValueError("M1 training requires the complete 300-shard inventory")
    for index, entry in enumerate(shards):
        partition = "train" if index < TRAIN_SHARDS else "calibration"
        start = (index if index < TRAIN_SHARDS else index - TRAIN_SHARDS) * MATCHES_PER_SHARD
        if not isinstance(entry, dict) or any(
            entry.get(key) != value
            for key, value in {
                "partition": partition,
                "start": start,
                "matches": MATCHES_PER_SHARD,
                "file": f"{partition}.{start:05d}.npz",
            }.items()
        ):
            raise ValueError("M1 training shard inventory differs from frozen split")
    if frozen.get("training_observations") != sum(
        entry["observations"] for entry in shards[:TRAIN_SHARDS]
    ):
        raise ValueError("M1 training observation inventory differs from freeze")
    return manifest, normalizer, _sha(freeze_bytes)


def _training_shard(
    root: Path, entry: dict[str, Any], normalizer: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if entry["partition"] != "train":
        raise ValueError("M1 training cannot load a calibration shard")
    path = root / "shards" / entry["file"]
    if not path.is_file() or _sha(path.read_bytes()) != entry["sha256"]:
        raise ValueError("M1 training shard checksum differs from frozen manifest")
    with np.load(path, allow_pickle=False) as shard:
        if set(shard.files) != {
            "nodes",
            "edges",
            "history_mask",
            "ages_minutes",
            "targets",
            "hazard_targets",
            "match_offsets",
        }:
            raise ValueError("M1 training shard arrays differ from input contract")
        nodes = shard["nodes"]
        edges = shard["edges"]
        mask = shard["history_mask"]
        ages = shard["ages_minutes"]
        targets = shard["targets"]
        hazards = shard["hazard_targets"]
        offsets = shard["match_offsets"]
        rows = entry["observations"]
        if (
            nodes.shape != (rows, STEPS, 12, len(FEATURE_NAMES))
            or edges.shape != (rows, STEPS, len(EDGE_TYPES), 12, 12)
            or mask.shape != (rows, STEPS)
            or ages.shape != (rows, STEPS)
            or targets.shape != (rows, len(LABELS))
            or targets.dtype != np.int8
            or hazards.shape != (rows, 3, 6)
            or hazards.dtype != np.float32
            or offsets.shape != (MATCHES_PER_SHARD + 1,)
            or offsets.dtype != np.int64
            or int(offsets[0]) != 0
            or int(offsets[-1]) != rows
            or not np.all(np.diff(offsets) > 0)
            or not np.isin(targets, (0, 1)).all()
        ):
            raise ValueError("M1 training shard dimensions, offsets or labels differ")
        at_risk_mask(hazards)
        derived = np.maximum.accumulate(hazards, axis=-1)[:, :, [0, 1, 2, 5]]
        if not np.array_equal(derived.reshape(rows, len(LABELS)), targets):
            raise ValueError("M1 hazard targets disagree with registered future labels")
        right_pad_graphs(nodes, edges, mask, ages)
        scaled = apply_m1_normalizer(nodes, mask, normalizer)
        return scaled, edges, mask, ages, hazards


def train_m1_seed(
    staging_root: str | Path,
    normalizer_path: str | Path,
    plan_path: str | Path,
    hazard_path: str | Path,
    freeze_path: str | Path,
    output_root: str | Path,
    *,
    seed: int,
    device: str = "cpu",
    max_new_shards: int = 1,
) -> dict[str, Any]:
    """Resume one seed after each training shard; calibration and test stay unread."""

    if max_new_shards < 1:
        raise ValueError("M1 shard budget must be positive")
    stage = Path(staging_root)
    manifest, normalizer, binding = _bound_inputs(
        stage, Path(normalizer_path), Path(plan_path), Path(hazard_path), Path(freeze_path)
    )
    if seed not in SEEDS:
        raise ValueError("M1 seed is absent from the frozen ten-seed experiment")
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
                saved.get("schema_version") != "league-ews-m1-training-checkpoint-v1"
                or saved.get("freeze_sha256") != binding
                or saved.get("seed") != seed
                or saved.get("device") != backend.device
                or saved.get("torch_version") != backend.version
                or type(completed) is not int
                or not 0 <= completed <= UNITS_PER_SEED
            ):
                raise ValueError("M1 checkpoint differs from frozen inputs or runtime")
            backend.load_state_dict(saved["backend"])
        else:
            completed = 0
        last_loss = None
        last_rows = None
        for unit in range(completed, min(UNITS_PER_SEED, completed + max_new_shards)):
            epoch, index = divmod(unit, TRAIN_SHARDS)
            entry = manifest["shards"][index]
            nodes, edges, mask, ages, hazards = _training_shard(stage, entry, normalizer)
            last_loss, last_rows = backend.train_shard(
                nodes, edges, mask, ages, hazards, seed=seed + 10_000 * epoch + index
            )
            state = {
                "schema_version": "league-ews-m1-training-checkpoint-v1",
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
                f"M1 seed {seed}: epoch {epoch + 1}/3, shard {index + 1}/{TRAIN_SHARDS}; "
                f"completed {unit + 1}/{UNITS_PER_SEED}",
                flush=True,
            )
        progress = min(UNITS_PER_SEED, completed + max_new_shards)
        return {
            "schema_version": "league-ews-m1-training-progress-v1",
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
