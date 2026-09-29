"""Small, checksum-bound audit of positional missingness and rare targets.

This exploratory diagnostic decodes the existing M1 train/calibration shards
only. It never opens the sealed patch 16.17 or writes another feature corpus.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.m1_graph_window import EDGE_TYPES, STEPS
from league_ews.m1_training import _bound_inputs


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _accumulator() -> dict[str, Any]:
    return {
        "matches": 0,
        "rows": 0,
        "position_count_rows": np.zeros(11, dtype=np.int64),
        "position_count_positive_rows": np.zeros((11, len(LABELS)), dtype=np.int64),
        "objective_spawn_rows": np.zeros((2, 2), dtype=np.int64),
        "objective_spawn_positive_rows": np.zeros((2, 2, len(LABELS)), dtype=np.int64),
        "current_edge_counts": np.zeros(len(EDGE_TYPES), dtype=np.int64),
    }


def _add_shard(target: dict[str, Any], shard: Any, entry: dict[str, Any]) -> None:
    names = {
        "nodes", "edges", "history_mask", "ages_minutes", "targets", "hazard_targets",
        "match_offsets",
    }
    if set(shard.files) != names:
        raise ValueError("M2 audit shard inventory differs from frozen M1 graph staging")
    nodes = shard["nodes"]
    edges = shard["edges"]
    mask = shard["history_mask"]
    labels = shard["targets"]
    hazards = shard["hazard_targets"]
    offsets = shard["match_offsets"]
    rows = entry["observations"]
    if (
        nodes.shape != (rows, STEPS, 12, 11)
        or nodes.dtype != np.float32
        or edges.shape != (rows, STEPS, len(EDGE_TYPES), 12, 12)
        or edges.dtype != np.bool_
        or mask.shape != (rows, STEPS)
        or mask.dtype != np.bool_
        or labels.shape != (rows, len(LABELS))
        or labels.dtype != np.int8
        or hazards.shape != (rows, 3, 6)
        or hazards.dtype != np.float32
        or offsets.shape != (entry["matches"] + 1,)
        or int(offsets[0]) != 0
        or int(offsets[-1]) != rows
        or not np.all(np.diff(offsets) > 0)
        or not np.all(mask[:, -1])
        or not np.isin(labels, (0, 1)).all()
        or not np.isin(hazards, (0, 1)).all()
        or np.any(hazards.sum(axis=-1) > 1)
        or not np.isin(nodes[:, -1, :10, 10], (0, 1)).all()
        or not np.isin(nodes[:, -1, 10:, 10], (0, 1)).all()
        or np.any(nodes[:, -1, :10, 8:10][nodes[:, -1, :10, 10] == 0] != 0)
        or not np.isfinite(nodes).all()
    ):
        raise ValueError("M2 audit shard array dimensions or values are invalid")
    if not np.array_equal(
        np.maximum.accumulate(hazards, axis=-1)[:, :, [0, 1, 2, 5]].reshape(rows, len(LABELS)),
        labels,
    ):
        raise ValueError("M2 audit labels disagree with the exact-future hazard targets")
    counts = nodes[:, -1, :10, 10].sum(axis=1).astype(np.int64)
    target["position_count_rows"] += np.bincount(counts, minlength=11)
    for index in range(len(LABELS)):
        target["position_count_positive_rows"][:, index] += np.bincount(
            counts, weights=labels[:, index], minlength=11
        ).astype(np.int64)
    for objective in range(2):
        ready = nodes[:, -1, 10 + objective, 10].astype(np.int64)
        target["objective_spawn_rows"][objective] += np.bincount(ready, minlength=2)
        for index in range(len(LABELS)):
            target["objective_spawn_positive_rows"][objective, :, index] += np.bincount(
                ready, weights=labels[:, index], minlength=2
            ).astype(np.int64)
    target["current_edge_counts"] += edges[:, -1].sum(axis=(0, 2, 3))
    target["matches"] += entry["matches"]
    target["rows"] += rows


def _summary(partition: dict[str, Any]) -> dict[str, Any]:
    rows = int(partition["rows"])
    by_count = partition["position_count_rows"]
    by_target = partition["position_count_positive_rows"]
    objective_rows = partition["objective_spawn_rows"]
    objective_positive = partition["objective_spawn_positive_rows"]
    return {
        "matches": partition["matches"],
        "rows": rows,
        "position_count_rows": by_count.tolist(),
        "position_count_positive_rows": {
            name: by_target[:, index].tolist() for index, name in enumerate(LABELS)
        },
        "target_prevalence": {
            name: float(by_target[:, index].sum() / rows) for index, name in enumerate(LABELS)
        },
        "objective_spawn": {
            objective: {
                "rows": objective_rows[index].tolist(),
                "positive_rows": {
                    name: objective_positive[index, :, column].tolist()
                    for column, name in enumerate(LABELS)
                },
            }
            for index, objective in enumerate(("baron", "dragon"))
        },
        "mean_directed_edges_per_frame": {
            name: float(partition["current_edge_counts"][index] / rows)
            for index, name in enumerate(EDGE_TYPES)
        },
    }


def audit_m2_preprocessing(
    staging_root: str | Path,
    normalizer_path: str | Path,
    training_plan_path: str | Path,
    hazard_path: str | Path,
    training_freeze_path: str | Path,
    output: str | Path,
) -> dict[str, Any]:
    """Count observed-position strata against exact event labels, with no refit."""

    root = Path(staging_root)
    manifest, _, training_binding = _bound_inputs(
        root,
        Path(normalizer_path),
        Path(training_plan_path),
        Path(hazard_path),
        Path(training_freeze_path),
    )
    totals = {"train": _accumulator(), "calibration": _accumulator()}
    for entry in manifest["shards"]:
        path = root / "shards" / entry["file"]
        if not path.is_file() or _sha(path.read_bytes()) != entry["sha256"]:
            raise ValueError("M2 audit shard checksum differs from frozen staging inventory")
        with np.load(path, allow_pickle=False) as shard:
            _add_shard(totals[entry["partition"]], shard, entry)
    if (
        totals["train"]["matches"] != 24000
        or totals["calibration"]["matches"] != 6000
        or totals["train"]["rows"]
        != sum(entry["observations"] for entry in manifest["shards"][:240])
        or totals["calibration"]["rows"]
        != sum(entry["observations"] for entry in manifest["shards"][240:])
    ):
        raise ValueError("M2 audit match or row inventory differs from frozen split")
    report: dict[str, Any] = {
        "schema_version": "league-ews-m2-preprocessing-audit-v1",
        "staging_manifest_sha256": _sha((root / "staging-manifest.json").read_bytes()),
        "training_freeze_sha256": training_binding,
        "split_sha256": manifest["split_sha256"],
        "test_matches_unread": 6000,
        "identifiers_in_report": False,
        "partitions": {name: _summary(value) for name, value in totals.items()},
        "interpretation": (
            "Descriptive association only; position coverage and objective spawn flags "
            "can reflect game phase and observation processes, not causal effects"
        ),
    }
    target = Path(output)
    content = (json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    if target.exists():
        if target.read_bytes() != content:
            raise ValueError("Existing M2 preprocessing audit differs from checked inputs")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix(target.suffix + ".partial")
        partial.write_bytes(content)
        partial.replace(target)
    return report
