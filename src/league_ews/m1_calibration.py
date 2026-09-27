"""Score frozen M1 seeds on calibration after all ten training runs complete."""

from __future__ import annotations

import hashlib
import importlib
import io
import json
from pathlib import Path
from typing import Any, cast

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.graph import FEATURE_NAMES
from league_ews.m1_backend import TorchM1Backend, at_risk_mask, right_pad_graphs
from league_ews.m1_graph_staging import MATCHES_PER_SHARD
from league_ews.m1_graph_window import EDGE_TYPES, STEPS
from league_ews.m1_normalizer import TRAIN_SHARDS, apply_m1_normalizer
from league_ews.m1_training import UNITS_PER_SEED, _bound_inputs
from league_ews.m1_training_plan import SEEDS
from league_ews.metrics import probabilistic_metrics

CAL_SHARDS = 60
CAL_MATCHES = 6000


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _completed_checkpoints(
    root: Path, freeze_sha: str
) -> tuple[dict[str, str], dict[int, dict[str, Any]]]:
    """Refuse calibration access until every registered seed is complete."""

    torch = importlib.import_module("torch")
    hashes: dict[str, str] = {}
    states: dict[int, dict[str, Any]] = {}
    for seed in SEEDS:
        content = (root / f"seed-{seed}" / "checkpoint.pt").read_bytes()
        state = torch.load(io.BytesIO(content), map_location="cpu", weights_only=True)
        if (
            not isinstance(state, dict)
            or state.get("schema_version") != "league-ews-m1-training-checkpoint-v1"
            or state.get("freeze_sha256") != freeze_sha
            or state.get("seed") != seed
            or state.get("completed_shards") != UNITS_PER_SEED
            or state.get("device") not in ("cpu", "cuda")
            or state.get("torch_version") != str(torch.__version__)
            or not isinstance(state.get("backend"), dict)
        ):
            raise ValueError("Every M1 seed must complete the same frozen training plan")
        hashes[str(seed)] = _sha(content)
        states[seed] = state
    if len({(state["device"], state["torch_version"]) for state in states.values()}) != 1:
        raise ValueError("M1 seeds must use the same device and PyTorch runtime")
    return hashes, states


def _calibration_shard(
    root: Path, entry: dict[str, Any], normalizer: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if entry["partition"] != "calibration":
        raise ValueError("M1 calibration may open only calibration shards")
    path = root / "shards" / entry["file"]
    if not path.is_file() or _sha(path.read_bytes()) != entry["sha256"]:
        raise ValueError("M1 calibration shard checksum differs from frozen manifest")
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
            raise ValueError("M1 calibration shard arrays differ from input contract")
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
            raise ValueError("M1 calibration shard dimensions, offsets or labels differ")
        at_risk_mask(hazards)
        expected = np.maximum.accumulate(hazards, axis=-1)[:, :, [0, 1, 2, 5]]
        if not np.array_equal(expected.reshape(rows, len(LABELS)), targets):
            raise ValueError("M1 calibration hazards disagree with registered future labels")
        right_pad_graphs(nodes, edges, mask, ages)
        return apply_m1_normalizer(nodes, mask, normalizer), edges, mask, ages, targets, offsets


def score_m1_calibration_seed(
    staging_root: str | Path,
    normalizer_path: str | Path,
    plan_path: str | Path,
    hazard_path: str | Path,
    freeze_path: str | Path,
    training_root: str | Path,
    output_root: str | Path,
    *,
    seed: int,
) -> dict[str, Any]:
    """Report one seed without selecting the best seed or opening the test patch."""

    stage = Path(staging_root)
    manifest, normalizer, freeze_sha = _bound_inputs(
        stage, Path(normalizer_path), Path(plan_path), Path(hazard_path), Path(freeze_path)
    )
    if seed not in SEEDS:
        raise ValueError("M1 calibration seed is absent from the frozen experiment")
    checkpoint_hashes, states = _completed_checkpoints(Path(training_root), freeze_sha)
    folder = Path(output_root) / f"seed-{seed}"
    report_path = folder / "calibration-report.json"
    scores_path = folder / "calibration-scores.npz"
    binding = {
        "seed": seed,
        "freeze_sha256": freeze_sha,
        "staging_manifest_sha256": _sha((stage / "staging-manifest.json").read_bytes()),
        "normalizer_sha256": _sha(Path(normalizer_path).read_bytes()),
        "checkpoint_sha256": checkpoint_hashes[str(seed)],
        "all_seed_checkpoint_sha256": checkpoint_hashes,
    }
    if report_path.exists():
        existing = cast(dict[str, Any], json.loads(report_path.read_bytes()))
        if (
            any(existing.get(key) != value for key, value in binding.items())
            or existing.get("schema_version") != "league-ews-m1-calibration-v1"
            or existing.get("test_matches_unread") != 6000
            or not scores_path.is_file()
            or _sha(scores_path.read_bytes()) != existing.get("scores_sha256")
        ):
            raise ValueError("Existing M1 calibration differs from frozen inputs")
        return existing

    state = states[seed]
    backend = TorchM1Backend(seed, state["device"])
    backend.load_state_dict(state["backend"])
    all_scores: list[np.ndarray] = []
    all_targets: list[np.ndarray] = []
    offsets = [0]
    entries = manifest["shards"][TRAIN_SHARDS:]
    if len(entries) != CAL_SHARDS:
        raise ValueError("M1 calibration partition has an incomplete shard inventory")
    for index, entry in enumerate(entries, start=1):
        nodes, edges, mask, ages, truth, local_offsets = _calibration_shard(
            stage, entry, normalizer
        )
        all_scores.append(backend.predict_shard(nodes, edges, mask, ages))
        all_targets.append(truth)
        offsets.extend((local_offsets[1:] + offsets[-1]).tolist())
        print(f"M1 seed {seed}: scored calibration shard {index}/{CAL_SHARDS}", flush=True)
    scores = np.concatenate(all_scores)
    truth = np.concatenate(all_targets)
    match_offsets = np.asarray(offsets, dtype=np.int64)
    if (
        match_offsets.shape != (CAL_MATCHES + 1,)
        or scores.shape != truth.shape
        or scores.shape[1] != len(LABELS)
        or match_offsets[-1] != len(scores)
        or not np.isfinite(scores).all()
        or np.any((scores < 0) | (scores > 1))
    ):
        raise ValueError("M1 calibration scores differ from the frozen partition")
    metrics = {
        label: probabilistic_metrics(truth[:, column], scores[:, column])
        for column, label in enumerate(LABELS)
    }
    folder.mkdir(parents=True, exist_ok=True)
    temporary = scores_path.with_suffix(".npz.partial")
    with temporary.open("wb") as handle:
        np.savez_compressed(
            handle, probabilities=scores, targets=truth, match_offsets=match_offsets
        )
    if scores_path.exists():
        with np.load(scores_path, allow_pickle=False) as stored:
            if (
                set(stored.files) != {"probabilities", "targets", "match_offsets"}
                or not np.array_equal(stored["probabilities"], scores)
                or not np.array_equal(stored["targets"], truth)
                or not np.array_equal(stored["match_offsets"], match_offsets)
            ):
                temporary.unlink()
                raise ValueError("Existing M1 calibration scores differ from frozen inputs")
        temporary.unlink()
    else:
        temporary.replace(scores_path)
    report: dict[str, Any] = {
        "schema_version": "league-ews-m1-calibration-v1",
        **binding,
        "device": backend.device,
        "torch_version": backend.version,
        "calibration_matches": CAL_MATCHES,
        "calibration_observations": len(scores),
        "targets": list(LABELS),
        "metrics": metrics,
        "macro_average_precision": float(
            np.mean([float(metric["average_precision"] or 0.0) for metric in metrics.values()])
        ),
        "scores_sha256": _sha(scores_path.read_bytes()),
        "test_matches_unread": 6000,
        "identifiers_in_report": False,
    }
    report_data = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode()
    report_temporary = report_path.with_suffix(".json.partial")
    report_temporary.write_bytes(report_data)
    report_temporary.replace(report_path)
    return report
