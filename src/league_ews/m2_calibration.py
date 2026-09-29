"""Score all completed exploratory hybrid seeds on the calibration partition."""

from __future__ import annotations

import hashlib
import importlib
import io
import json
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.m1_calibration import _calibration_shard
from league_ews.m1_normalizer import TRAIN_SHARDS
from league_ews.m1_training_plan import SEEDS
from league_ews.m2_backend import MODES, TorchM2Backend
from league_ews.m2_training import UNITS_PER_SEED, _bound_hybrid
from league_ews.metrics import probabilistic_metrics


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _completed_checkpoints(
    root: Path, binding: str, mode: str
) -> tuple[dict[str, str], dict[int, dict[str, Any]]]:
    """A mode may not read calibration until all ten of its seeds complete."""

    if mode not in MODES:
        raise ValueError("Unknown M2 hybrid mode")
    torch = importlib.import_module("torch")
    hashes: dict[str, str] = {}
    states: dict[int, dict[str, Any]] = {}
    for seed in SEEDS:
        content = (root / mode / f"seed-{seed}" / "checkpoint.pt").read_bytes()
        state = torch.load(io.BytesIO(content), map_location="cpu", weights_only=True)
        if (
            not isinstance(state, dict)
            or state.get("schema_version") != "league-ews-m2-hybrid-checkpoint-v1"
            or state.get("freeze_sha256") != binding
            or state.get("mode") != mode
            or state.get("seed") != seed
            or state.get("completed_shards") != UNITS_PER_SEED
            or state.get("device") not in ("cpu", "cuda")
            or state.get("torch_version") != str(torch.__version__)
            or not isinstance(state.get("backend"), dict)
        ):
            raise ValueError("All ten M2 seeds must complete the same frozen mode before scoring")
        hashes[str(seed)] = _sha(content)
        states[seed] = state
    if len({(state["device"], state["torch_version"]) for state in states.values()}) != 1:
        raise ValueError("M2 seeds must use the same device and PyTorch runtime")
    return hashes, states


def _raw_calibration_nodes(root: Path, entry: dict[str, Any]) -> np.ndarray:
    if entry["partition"] != "calibration":
        raise ValueError("M2 calibration cannot open a training or test shard")
    content = (root / "shards" / entry["file"]).read_bytes()
    if _sha(content) != entry["sha256"]:
        raise ValueError("M2 calibration shard checksum differs from frozen staging")
    with np.load(io.BytesIO(content), allow_pickle=False) as shard:
        return shard["nodes"]


def score_m2_calibration_seed(
    staging_root: str | Path,
    normalizer_path: str | Path,
    training_plan_path: str | Path,
    hazards_path: str | Path,
    training_freeze_path: str | Path,
    audit_path: str | Path,
    plan_path: str | Path,
    hybrid_freeze_path: str | Path,
    training_root: str | Path,
    output_root: str | Path,
    *,
    mode: str,
    seed: int,
) -> dict[str, Any]:
    if seed not in SEEDS or mode not in MODES:
        raise ValueError("M2 calibration mode or seed is absent from the frozen experiment")
    stage = Path(staging_root)
    manifest, normalizer, binding = _bound_hybrid(
        stage,
        normalizer_path,
        training_plan_path,
        hazards_path,
        training_freeze_path,
        audit_path,
        plan_path,
        hybrid_freeze_path,
    )
    checkpoint_hashes, states = _completed_checkpoints(Path(training_root), binding, mode)
    folder = Path(output_root) / mode / f"seed-{seed}"
    report_path = folder / "calibration-report.json"
    scores_path = folder / "calibration-scores.npz"
    bound = {
        "seed": seed,
        "mode": mode,
        "freeze_sha256": binding,
        "staging_manifest_sha256": _sha((stage / "staging-manifest.json").read_bytes()),
        "normalizer_sha256": _sha(Path(normalizer_path).read_bytes()),
        "checkpoint_sha256": checkpoint_hashes[str(seed)],
        "all_seed_checkpoint_sha256": checkpoint_hashes,
    }
    if report_path.exists():
        existing = json.loads(report_path.read_bytes())
        if (
            any(existing.get(key) != value for key, value in bound.items())
            or existing.get("schema_version") != "league-ews-m2-hybrid-calibration-v1"
            or existing.get("test_matches_unread") != 6000
            or not scores_path.is_file()
            or _sha(scores_path.read_bytes()) != existing.get("scores_sha256")
        ):
            raise ValueError("Existing M2 calibration differs from frozen inputs")
        return existing

    state = states[seed]
    backend = TorchM2Backend(seed, state["device"], mode=mode)
    backend.load_state_dict(state["backend"])
    entries = manifest["shards"][TRAIN_SHARDS:]
    if len(entries) != 60:
        raise ValueError("M2 calibration shard inventory is incomplete")
    scores_list: list[np.ndarray] = []
    truth_list: list[np.ndarray] = []
    offsets = [0]
    for index, entry in enumerate(entries, start=1):
        raw = _raw_calibration_nodes(stage, entry)
        normalized, edges, mask, ages, truth, local_offsets = _calibration_shard(
            stage, entry, normalizer
        )
        scores_list.append(backend.predict_shard(raw, normalized, edges, mask, ages))
        truth_list.append(truth)
        offsets.extend((local_offsets[1:] + offsets[-1]).tolist())
        print(f"M2 {mode} seed {seed}: scored calibration shard {index}/60", flush=True)
    scores = np.concatenate(scores_list)
    truth = np.concatenate(truth_list)
    match_offsets = np.asarray(offsets, dtype=np.int64)
    if (
        match_offsets.shape != (6001,)
        or scores.shape != truth.shape
        or scores.shape[1] != len(LABELS)
        or match_offsets[-1] != len(scores)
        or not np.isfinite(scores).all()
        or np.any((scores < 0) | (scores > 1))
        or np.any(np.diff(scores.reshape(len(scores), 3, 4), axis=-1) < 0)
    ):
        raise ValueError("M2 calibration scores differ from the frozen partition")
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
                raise ValueError("Existing M2 calibration scores differ from frozen inputs")
        temporary.unlink()
    else:
        temporary.replace(scores_path)
    report: dict[str, Any] = {
        "schema_version": "league-ews-m2-hybrid-calibration-v1",
        **bound,
        "device": backend.device,
        "torch_version": backend.version,
        "calibration_matches": 6000,
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
    temporary_report = report_path.with_suffix(".json.partial")
    temporary_report.write_bytes(report_data)
    temporary_report.replace(report_path)
    return report
