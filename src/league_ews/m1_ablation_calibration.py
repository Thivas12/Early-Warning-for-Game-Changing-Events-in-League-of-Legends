"""Score one registered M1 ablation after all ten variant seeds complete."""

from __future__ import annotations

import hashlib
import importlib
import io
import json
from pathlib import Path
from typing import Any, cast

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.m1_ablation_inputs import ablate_graph_inputs
from league_ews.m1_ablation_plan import freeze_m1_ablations
from league_ews.m1_ablation_training import SUPPORTED_VARIANTS
from league_ews.m1_backend import TorchM1Backend
from league_ews.m1_calibration import CAL_MATCHES, CAL_SHARDS, _calibration_shard
from league_ews.m1_fixed_grid import fixed_minute_grid
from league_ews.m1_normalizer import TRAIN_SHARDS
from league_ews.m1_training import UNITS_PER_SEED, _bound_inputs
from league_ews.m1_training_plan import SEEDS
from league_ews.metrics import probabilistic_metrics


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _completed_variant_checkpoints(
    root: Path, variant: str, ablation_sha: str, training_sha: str
) -> tuple[dict[str, str], dict[int, dict[str, Any]]]:
    """Validate every registered seed before a calibration shard is opened."""

    torch = importlib.import_module("torch")
    node_count, relation_count = (10, 3) if variant == "no-objective-nodes" else (12, 5)
    hashes: dict[str, str] = {}
    states: dict[int, dict[str, Any]] = {}
    for seed in SEEDS:
        path = root / variant / f"seed-{seed}" / "checkpoint.pt"
        if not path.is_file():
            raise ValueError("All ten graph ablation seeds must finish before calibration")
        content = path.read_bytes()
        state = torch.load(io.BytesIO(content), map_location="cpu", weights_only=True)
        if (
            not isinstance(state, dict)
            or state.get("schema_version") != "league-ews-m1-graph-ablation-checkpoint-v1"
            or state.get("ablation_freeze_sha256") != ablation_sha
            or state.get("training_freeze_sha256") != training_sha
            or state.get("variant") != variant
            or state.get("seed") != seed
            or state.get("device") not in ("cpu", "cuda")
            or state.get("torch_version") != str(torch.__version__)
            or state.get("node_count", 12) != node_count
            or state.get("relation_count", 5) != relation_count
            or state.get("output_mode", "hazards")
            != ("independent-heads" if variant == "independent-horizon-heads" else "hazards")
            or state.get("completed_shards") != UNITS_PER_SEED
            or not isinstance(state.get("backend"), dict)
        ):
            raise ValueError("Graph ablation checkpoints differ from the frozen training plan")
        hashes[str(seed)] = _sha(content)
        states[seed] = state
    if len({(state["device"], state["torch_version"]) for state in states.values()}) != 1:
        raise ValueError("Graph ablation seeds must use the same device and PyTorch runtime")
    return hashes, states


def score_m1_graph_ablation_seed(
    staging_root: str | Path,
    normalizer_path: str | Path,
    training_plan_path: str | Path,
    hazard_path: str | Path,
    training_freeze_path: str | Path,
    ablation_plan_path: str | Path,
    ablation_freeze_path: str | Path,
    calibration_summary_path: str | Path,
    alert_summary_path: str | Path,
    training_root: str | Path,
    output_root: str | Path,
    *,
    variant: str,
    seed: int,
) -> dict[str, Any]:
    """Score a frozen graph variant without choosing a seed or reading test."""

    if variant not in SUPPORTED_VARIANTS or seed not in SEEDS:
        raise ValueError("Graph ablation calibration variant or seed is not registered")
    ablation_path = Path(ablation_freeze_path)
    if not ablation_path.is_file():
        raise ValueError("M1 ablation freeze must be created before calibration")
    frozen = freeze_m1_ablations(
        ablation_plan_path,
        training_plan_path,
        training_freeze_path,
        calibration_summary_path,
        alert_summary_path,
        ablation_path,
    )
    stage = Path(staging_root)
    manifest, normalizer, training_sha = _bound_inputs(
        stage,
        Path(normalizer_path),
        Path(training_plan_path),
        Path(hazard_path),
        Path(training_freeze_path),
    )
    if (
        frozen["training_freeze_sha256"] != training_sha
        or frozen["split_sha256"] != manifest["split_sha256"]
    ):
        raise ValueError("Graph ablation calibration differs from staged training split")
    ablation_sha = _sha(ablation_path.read_bytes())
    hashes, states = _completed_variant_checkpoints(
        Path(training_root), variant, ablation_sha, training_sha
    )
    folder = Path(output_root) / variant / f"seed-{seed}"
    report_path = folder / "calibration-report.json"
    scores_path = folder / "calibration-scores.npz"
    binding = {
        "variant": variant,
        "seed": seed,
        "ablation_freeze_sha256": ablation_sha,
        "training_freeze_sha256": training_sha,
        "staging_manifest_sha256": _sha((stage / "staging-manifest.json").read_bytes()),
        "normalizer_sha256": _sha(Path(normalizer_path).read_bytes()),
        "checkpoint_sha256": hashes[str(seed)],
        "all_seed_checkpoint_sha256": hashes,
    }
    if report_path.exists():
        existing = cast(dict[str, Any], json.loads(report_path.read_bytes()))
        if (
            any(existing.get(key) != value for key, value in binding.items())
            or existing.get("schema_version") != "league-ews-m1-graph-ablation-calibration-v1"
            or existing.get("test_matches_unread") != 6000
            or not scores_path.is_file()
            or _sha(scores_path.read_bytes()) != existing.get("scores_sha256")
        ):
            raise ValueError("Existing graph ablation calibration differs from frozen inputs")
        return existing

    state = states[seed]
    node_count, relation_count = (10, 3) if variant == "no-objective-nodes" else (12, 5)
    backend = TorchM1Backend(
        seed,
        state["device"],
        node_count=node_count,
        relation_count=relation_count,
        **({"output_mode": "independent-heads"} if variant == "independent-horizon-heads" else {}),
    )
    backend.load_state_dict(state["backend"])
    entries = manifest["shards"][TRAIN_SHARDS:]
    if len(entries) != CAL_SHARDS:
        raise ValueError("M1 graph ablation calibration shard inventory is incomplete")
    all_scores: list[np.ndarray] = []
    all_targets: list[np.ndarray] = []
    offsets = [0]
    for index, entry in enumerate(entries, start=1):
        nodes, edges, mask, ages, truth, local_offsets = _calibration_shard(
            stage, entry, normalizer
        )
        if variant == "fixed-minute-grid":
            nodes, edges, mask, ages = fixed_minute_grid(nodes, edges, mask, ages, local_offsets)
        elif variant != "independent-horizon-heads":
            nodes, edges = ablate_graph_inputs(nodes, edges, mask, ages, variant=variant)
        all_scores.append(backend.predict_shard(nodes, edges, mask, ages))
        all_targets.append(truth)
        offsets.extend((local_offsets[1:] + offsets[-1]).tolist())
        print(
            f"M1 ablation {variant} seed {seed}: calibration shard {index}/{CAL_SHARDS}", flush=True
        )
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
        or (
            variant != "independent-horizon-heads"
            and np.any(np.diff(scores.reshape(len(scores), 3, 4), axis=-1) < -1e-7)
        )
    ):
        raise ValueError("Graph ablation calibration predictions differ from frozen horizons")
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
                raise ValueError("Existing graph ablation scores differ from frozen inputs")
        temporary.unlink()
    else:
        temporary.replace(scores_path)
    report: dict[str, Any] = {
        "schema_version": "league-ews-m1-graph-ablation-calibration-v1",
        **binding,
        "node_count": node_count,
        "relation_count": relation_count,
        **({"output_mode": "independent-heads"} if variant == "independent-horizon-heads" else {}),
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
    report_temporary = report_path.with_suffix(".json.partial")
    report_temporary.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    report_temporary.replace(report_path)
    return report
