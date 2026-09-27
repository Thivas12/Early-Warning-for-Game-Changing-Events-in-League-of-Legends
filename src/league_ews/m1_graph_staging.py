"""Bounded, checksum-bound private M1 graph shards for train and calibration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import numpy as np

from league_ews.b4_staging import _bound_inputs, _same_arrays
from league_ews.baseline_floor import LABELS, _read_match
from league_ews.m1_graph_plan import load_graph_plan
from league_ews.m1_graph_window import EDGE_TYPES, STEPS, build_causal_graph_windows

MATCHES_PER_SHARD = 100


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _materialize(
    processed_root: Path,
    entries: list[dict[str, object]],
    by_id: dict[str, Any],
    plan_path: Path,
) -> dict[str, np.ndarray]:
    _, rules, radius = load_graph_plan(plan_path)
    values: dict[str, list[np.ndarray]] = {
        name: []
        for name in ("nodes", "edges", "history_mask", "ages_minutes", "targets", "hazard_targets")
    }
    offsets = [0]
    for entry in entries:
        match_id = str(entry["match_id"])
        record = by_id[match_id]
        payload = _read_match(processed_root, match_id, record.sha256)
        windows = build_causal_graph_windows(
            payload, match_id, objective_rules=rules, proximity_radius=radius
        )
        if len(windows.times_ms) != record.observations:
            raise ValueError("M1 observations differ from audited processing inventory")
        for name in values:
            values[name].append(getattr(windows, name))
        offsets.append(offsets[-1] + record.observations)
    if not entries:
        raise ValueError("M1 shard cannot be empty")
    return {
        **{name: np.concatenate(arrays) for name, arrays in values.items()},
        "match_offsets": np.asarray(offsets, dtype=np.int64),
    }


def stage_m1_graphs(
    raw_root: str | Path,
    processed_root: str | Path,
    frame_path: str | Path,
    g2_report: str | Path,
    processed_audit: str | Path,
    split_path: str | Path,
    plan_path: str | Path,
    freeze_path: str | Path,
    output_root: str | Path,
    *,
    max_new_shards: int = 1,
) -> dict[str, object]:
    """Stage only the registered train/calibration partitions in bounded shards."""

    if max_new_shards < 1:
        raise ValueError("max_new_shards must be positive")
    plan = Path(plan_path)
    plan_sha, _, _ = load_graph_plan(plan)
    processed = Path(processed_root)
    prior_bindings, partitions, by_id = _bound_inputs(
        Path(raw_root),
        processed,
        Path(frame_path),
        Path(g2_report),
        Path(processed_audit),
        Path(split_path),
    )
    frozen_bytes = Path(freeze_path).read_bytes()
    frozen = json.loads(frozen_bytes)
    if not isinstance(frozen, dict) or any(
        frozen.get(key) != value
        for key, value in {
            "schema_version": "league-ews-m1-graph-freeze-v1",
            "plan_sha256": plan_sha,
            "split_sha256": prior_bindings["split_sha256"],
            "processing_manifest_sha256": prior_bindings["processing_manifest_sha256"],
            "train_matches": 24000,
            "calibration_matches": 6000,
            "test_matches_unread": 6000,
            "identifiers_in_summary": False,
        }.items()
    ):
        raise ValueError("M1 graph freeze differs from audited inputs")
    planned = [
        (partition, start, min(start + MATCHES_PER_SHARD, len(partitions[partition])))
        for partition in ("train", "calibration")
        for start in range(0, len(partitions[partition]), MATCHES_PER_SHARD)
    ]
    bindings: dict[str, object] = {
        "schema_version": "league-ews-m1-graph-staging-v1",
        "split_sha256": prior_bindings["split_sha256"],
        "processing_manifest_sha256": prior_bindings["processing_manifest_sha256"],
        "plan_sha256": plan_sha,
        "freeze_sha256": _sha(frozen_bytes),
        "steps": STEPS,
        "edge_types": list(EDGE_TYPES),
        "targets": list(LABELS),
        "matches_per_shard": MATCHES_PER_SHARD,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
    root = Path(output_root)
    manifest_path = root / "staging-manifest.json"
    stored = json.loads(manifest_path.read_bytes()) if manifest_path.exists() else None
    if stored is None:
        if root.exists() and {path.name for path in root.iterdir()} - {"shards"}:
            raise ValueError("Unregistered M1 staging files require inspection")
        progress: dict[str, Any] = {**bindings, "shards": [], "complete": False}
    else:
        progress = stored
        if any(progress.get(key) != value for key, value in bindings.items()):
            raise ValueError("Existing M1 staging differs from frozen inputs")
    shards = progress.get("shards")
    if not isinstance(shards, list) or len(shards) > len(planned):
        raise ValueError("M1 staging inventory is invalid")
    for index, record in enumerate(shards):
        partition, start, end = planned[index]
        filename = f"{partition}.{start:05d}.npz"
        path = root / "shards" / filename
        if (
            not isinstance(record, dict)
            or record.get("partition") != partition
            or record.get("start") != start
            or record.get("matches") != end - start
            or record.get("file") != filename
            or not path.is_file()
            or _sha(path.read_bytes()) != record.get("sha256")
        ):
            raise ValueError("Existing M1 shard or checksum differs from manifest")
    if progress.get("complete") != (len(shards) == len(planned)):
        raise ValueError("M1 staging completion differs from shard inventory")
    allowed = {f"{partition}.{start:05d}.npz" for partition, start, _ in planned[: len(shards) + 1]}
    shard_dir = root / "shards"
    if shard_dir.exists() and {path.name for path in shard_dir.iterdir()} - allowed:
        raise ValueError("Unexpected M1 shard files require inspection")
    for partition, start, end in planned[len(shards) : len(shards) + max_new_shards]:
        filename = f"{partition}.{start:05d}.npz"
        path = shard_dir / filename
        arrays = _materialize(processed, partitions[partition][start:end], by_id, plan)
        if path.exists():
            if not _same_arrays(path, arrays):
                raise ValueError("Unregistered M1 shard differs from audited source")
        else:
            shard_dir.mkdir(parents=True, exist_ok=True)
            partial = path.with_suffix(".npz.partial")
            with partial.open("wb") as handle:
                np.savez_compressed(handle, **arrays)  # type: ignore[arg-type]
            partial.replace(path)
        shards.append(
            {
                "partition": partition,
                "start": start,
                "matches": end - start,
                "observations": int(arrays["targets"].shape[0]),
                "file": filename,
                "sha256": _sha(path.read_bytes()),
            }
        )
        progress["complete"] = len(shards) == len(planned)
        root.mkdir(parents=True, exist_ok=True)
        temporary = manifest_path.with_suffix(".json.partial")
        temporary.write_text(json.dumps(progress, sort_keys=True, separators=(",", ":")) + "\n")
        temporary.replace(manifest_path)
        print(f"Staged {len(shards)}/{len(planned)} M1 graph shards", flush=True)
    return {
        "schema_version": bindings["schema_version"],
        "complete": progress["complete"],
        "staged_shards": len(shards),
        "total_shards": len(planned),
        "staged_matches": sum(int(cast(dict[str, Any], item)["matches"]) for item in shards),
        "test_matches_unread": 6000,
        "split_sha256": bindings["split_sha256"],
        "identifiers_in_summary": False,
    }
