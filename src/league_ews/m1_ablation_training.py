"""Resume one registered M1 graph removal ablation at a time."""

from __future__ import annotations

import fcntl
import hashlib
from pathlib import Path
from typing import Any

from league_ews.m1_ablation_inputs import ablate_graph_inputs
from league_ews.m1_ablation_plan import freeze_m1_ablations
from league_ews.m1_backend import TorchM1Backend
from league_ews.m1_normalizer import TRAIN_SHARDS
from league_ews.m1_training import (
    UNITS_PER_SEED,
    _bound_inputs,
    _training_shard,
)
from league_ews.m1_training_plan import SEEDS

SUPPORTED_VARIANTS = (
    "no-positions-or-proximity",
    "no-interaction-edges",
    "no-objective-nodes",
    "no-assistance-history",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _new_backend(seed: int, device: str) -> TorchM1Backend:
    return TorchM1Backend(seed, device)


def _new_objective_free_backend(seed: int, device: str) -> TorchM1Backend:
    return TorchM1Backend(seed, device, node_count=10, relation_count=3)


def train_m1_graph_ablation_seed(
    staging_root: str | Path,
    normalizer_path: str | Path,
    training_plan_path: str | Path,
    hazard_path: str | Path,
    training_freeze_path: str | Path,
    ablation_plan_path: str | Path,
    ablation_freeze_path: str | Path,
    calibration_summary_path: str | Path,
    alert_summary_path: str | Path,
    output_root: str | Path,
    *,
    variant: str,
    seed: int,
    device: str = "cpu",
    max_new_shards: int = 1,
) -> dict[str, Any]:
    """Train on the original shard order; never decode calibration or test."""

    if variant not in SUPPORTED_VARIANTS:
        raise ValueError("M1 graph ablation variant needs a supported backend")
    if seed not in SEEDS or max_new_shards < 1:
        raise ValueError("M1 ablation seed or shard budget differs from frozen plan")
    frozen_path = Path(ablation_freeze_path)
    if not frozen_path.is_file():
        raise ValueError("M1 ablation freeze must be created before training")
    frozen = freeze_m1_ablations(
        ablation_plan_path,
        training_plan_path,
        training_freeze_path,
        calibration_summary_path,
        alert_summary_path,
        frozen_path,
    )
    stage = Path(staging_root)
    manifest, normalizer, original_binding = _bound_inputs(
        stage,
        Path(normalizer_path),
        Path(training_plan_path),
        Path(hazard_path),
        Path(training_freeze_path),
    )
    if (
        frozen["training_freeze_sha256"] != _sha(Path(training_freeze_path).read_bytes())
        or frozen["split_sha256"] != manifest["split_sha256"]
    ):
        raise ValueError("M1 ablation freeze differs from staged training matches")
    binding = _sha(frozen_path.read_bytes())
    folder = Path(output_root) / variant / f"seed-{seed}"
    folder.mkdir(parents=True, exist_ok=True)
    checkpoint = folder / "checkpoint.pt"
    with (folder / "training.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        node_count, relation_count = (10, 3) if variant == "no-objective-nodes" else (12, 5)
        backend = (
            _new_objective_free_backend(seed, device)
            if variant == "no-objective-nodes"
            else _new_backend(seed, device)
        )
        if checkpoint.exists():
            saved = backend.load(str(checkpoint))
            completed = saved.get("completed_shards")
            if (
                saved.get("schema_version") != "league-ews-m1-graph-ablation-checkpoint-v1"
                or saved.get("ablation_freeze_sha256") != binding
                or saved.get("training_freeze_sha256") != original_binding
                or saved.get("variant") != variant
                or saved.get("seed") != seed
                or saved.get("device") != backend.device
                or saved.get("torch_version") != backend.version
                or saved.get("node_count", 12) != node_count
                or saved.get("relation_count", 5) != relation_count
                or type(completed) is not int
                or not 0 <= completed <= UNITS_PER_SEED
            ):
                raise ValueError("M1 ablation checkpoint differs from frozen inputs")
            backend.load_state_dict(saved["backend"])
        else:
            completed = 0
        last_loss = None
        last_rows = None
        for unit in range(completed, min(UNITS_PER_SEED, completed + max_new_shards)):
            epoch, index = divmod(unit, TRAIN_SHARDS)
            nodes, edges, mask, ages, hazards = _training_shard(
                stage, manifest["shards"][index], normalizer
            )
            nodes, edges = ablate_graph_inputs(nodes, edges, mask, ages, variant=variant)
            last_loss, last_rows = backend.train_shard(
                nodes, edges, mask, ages, hazards, seed=seed + 10_000 * epoch + index
            )
            state = {
                "schema_version": "league-ews-m1-graph-ablation-checkpoint-v1",
                "ablation_freeze_sha256": binding,
                "training_freeze_sha256": original_binding,
                "variant": variant,
                "seed": seed,
                "device": backend.device,
                "torch_version": backend.version,
                "node_count": node_count,
                "relation_count": relation_count,
                "completed_shards": unit + 1,
                "backend": backend.state_dict(),
            }
            partial = checkpoint.with_suffix(".pt.partial")
            backend.save(state, str(partial))
            partial.replace(checkpoint)
            print(
                f"M1 ablation {variant} seed {seed}: epoch {epoch + 1}/3, "
                f"shard {index + 1}/{TRAIN_SHARDS}; completed {unit + 1}/{UNITS_PER_SEED}",
                flush=True,
            )
        progress = min(UNITS_PER_SEED, completed + max_new_shards)
        return {
            "schema_version": "league-ews-m1-graph-ablation-progress-v1",
            "variant": variant,
            "seed": seed,
            "device": backend.device,
            "torch_version": backend.version,
            "node_count": node_count,
            "relation_count": relation_count,
            "completed_shards": progress,
            "total_shards": UNITS_PER_SEED,
            "complete": progress == UNITS_PER_SEED,
            "last_shard_loss": last_loss,
            "last_shard_rows": last_rows,
            "ablation_freeze_sha256": binding,
            "checkpoint_sha256": _sha(checkpoint.read_bytes()) if checkpoint.exists() else None,
            "calibration_matches_unread": 6000,
            "test_matches_unread": 6000,
            "identifiers_in_summary": False,
        }
