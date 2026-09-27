"""Score every frozen B4 seed on calibration shards after all training completes."""

from __future__ import annotations

import hashlib
import importlib
import io
import json
from pathlib import Path
from typing import Any, cast

import numpy as np

from league_ews.b4_backend import TorchBackend
from league_ews.b4_normalizer import _validated_manifest, apply_b4_normalizer
from league_ews.b4_plan import freeze_b4_plan
from league_ews.b4_sequence import SEQUENCE_FEATURES, STEPS
from league_ews.b4_training import UNITS_PER_SEED
from league_ews.baseline_floor import LABELS
from league_ews.metrics import probabilistic_metrics


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _load_calibration_shard(
    root: Path, entry: dict[str, Any], normalizer: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if entry["partition"] != "calibration":
        raise ValueError("B4 calibration may open only calibration shards")
    with np.load(root / "shards" / entry["file"], allow_pickle=False) as shard:
        if set(shard.files) != {"inputs", "history_mask", "targets", "match_offsets"}:
            raise ValueError("B4 calibration shard inventory differs")
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
            raise ValueError("B4 calibration shard dimensions, offsets or targets differ")
        scaled = apply_b4_normalizer(inputs, mask, normalizer)
        if not np.isfinite(scaled).all():
            raise ValueError("B4 scaled calibration inputs contain nonfinite values")
        return scaled, mask, targets, offsets


def _completed_checkpoints(
    root: Path, seeds: list[int], freeze_sha: str
) -> tuple[dict[str, str], dict[int, dict[str, Any]]]:
    torch = importlib.import_module("torch")
    hashes: dict[str, str] = {}
    states: dict[int, dict[str, Any]] = {}
    for seed in seeds:
        content = (root / f"seed-{seed}" / "checkpoint.pt").read_bytes()
        state = torch.load(io.BytesIO(content), map_location="cpu", weights_only=True)
        if (
            not isinstance(state, dict)
            or state.get("schema_version") != "league-ews-b4-training-checkpoint-v1"
            or state.get("freeze_sha256") != freeze_sha
            or state.get("seed") != seed
            or state.get("completed_shards") != UNITS_PER_SEED
            or state.get("device") not in ("cpu", "cuda")
            or state.get("torch_version") != str(torch.__version__)
            or not isinstance(state.get("backend"), dict)
        ):
            raise ValueError("Every B4 seed must complete the same frozen training plan")
        hashes[str(seed)] = _sha(content)
        states[seed] = state
    if len({(state["device"], state["torch_version"]) for state in states.values()}) != 1:
        raise ValueError("B4 seeds must use the same device and PyTorch runtime")
    return hashes, states


def score_b4_calibration_seed(
    staging_root: str | Path,
    normalizer_path: str | Path,
    plan_path: str | Path,
    freeze_path: str | Path,
    training_root: str | Path,
    output_root: str | Path,
    *,
    seed: int,
) -> dict[str, Any]:
    """Report one seed without selecting a winner or opening test-patch payloads."""

    stage = Path(staging_root)
    frozen = freeze_b4_plan(stage, normalizer_path, plan_path, freeze_path)
    seeds = frozen["seeds"]
    if seed not in seeds:
        raise ValueError("B4 calibration seed is absent from the frozen experiment")
    freeze_sha = _sha(Path(freeze_path).read_bytes())
    manifest_bytes, manifest = _validated_manifest(stage)
    normalizer = json.loads(Path(normalizer_path).read_bytes())
    checkpoint_hashes, states = _completed_checkpoints(Path(training_root), seeds, freeze_sha)
    folder = Path(output_root) / f"seed-{seed}"
    report_path = folder / "calibration-report.json"
    scores_path = folder / "calibration-scores.npz"
    binding = {
        "seed": seed,
        "freeze_sha256": freeze_sha,
        "staging_manifest_sha256": _sha(manifest_bytes),
        "normalizer_sha256": _sha(Path(normalizer_path).read_bytes()),
        "checkpoint_sha256": checkpoint_hashes[str(seed)],
        "all_seed_checkpoint_sha256": checkpoint_hashes,
    }
    if report_path.exists():
        existing_report = cast(dict[str, Any], json.loads(report_path.read_bytes()))
        if (
            any(existing_report.get(key) != value for key, value in binding.items())
            or existing_report.get("schema_version") != "league-ews-b4-calibration-v1"
            or existing_report.get("test_matches_unread") != 6000
            or not scores_path.is_file()
            or _sha(scores_path.read_bytes()) != existing_report.get("scores_sha256")
        ):
            raise ValueError("Existing B4 calibration differs from frozen inputs")
        return existing_report

    state = states[seed]
    backend = TorchBackend(seed, state["device"])
    backend.load_state_dict(state["backend"])
    all_scores: list[np.ndarray] = []
    all_targets: list[np.ndarray] = []
    all_offsets = [0]
    for index, entry in enumerate(manifest["shards"][48:], start=1):
        inputs, mask, targets, offsets = _load_calibration_shard(stage, entry, normalizer)
        all_scores.append(backend.predict_shard(inputs, mask))
        all_targets.append(targets)
        all_offsets.extend((offsets[1:] + all_offsets[-1]).tolist())
        print(f"B4 seed {seed}: scored calibration shard {index}/12", flush=True)
    scores = np.concatenate(all_scores)
    truth = np.concatenate(all_targets)
    offsets_array = np.asarray(all_offsets, dtype=np.int64)
    if (
        len(all_scores) != 12
        or offsets_array.shape != (6001,)
        or scores.shape != truth.shape
        or scores.shape[1] != len(LABELS)
        or offsets_array[-1] != len(scores)
    ):
        raise ValueError("B4 calibration partition is incomplete")
    metrics = {
        label: probabilistic_metrics(truth[:, column], scores[:, column])
        for column, label in enumerate(LABELS)
    }
    folder.mkdir(parents=True, exist_ok=True)
    temporary = scores_path.with_suffix(".npz.partial")
    with temporary.open("wb") as handle:
        np.savez_compressed(
            handle, probabilities=scores, targets=truth, match_offsets=offsets_array
        )
    if scores_path.exists():
        with np.load(scores_path, allow_pickle=False) as existing:
            if (
                set(existing.files) != {"probabilities", "targets", "match_offsets"}
                or not np.array_equal(existing["probabilities"], scores)
                or not np.array_equal(existing["targets"], truth)
                or not np.array_equal(existing["match_offsets"], offsets_array)
            ):
                temporary.unlink()
                raise ValueError("Existing B4 calibration scores differ from frozen inputs")
        temporary.unlink()
    else:
        temporary.replace(scores_path)
    report: dict[str, Any] = {
        "schema_version": "league-ews-b4-calibration-v1",
        **binding,
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
    report_temporary = report_path.with_suffix(".json.partial")
    report_temporary.write_bytes(report_data)
    report_temporary.replace(report_path)
    return report
