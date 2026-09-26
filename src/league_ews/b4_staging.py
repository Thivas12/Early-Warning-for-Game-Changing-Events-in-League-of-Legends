"""Bounded, private sequence shards for train and calibration B4 inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import numpy as np

from league_ews.b4_sequence import SEQUENCE_FEATURES, STEPS, build_causal_sequences
from league_ews.baseline_floor import LABELS, _read_match
from league_ews.final_split import freeze_final_split
from league_ews.raw_validation import ProcessingManifest

MATCHES_PER_SHARD = 500


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _bound_inputs(
    raw_root: Path,
    processed_root: Path,
    frame_path: Path,
    g2_report: Path,
    processed_audit: Path,
    split_path: Path,
) -> tuple[dict[str, object], dict[str, list[dict[str, object]]], dict[str, Any]]:
    split_bytes = split_path.read_bytes()
    frozen = freeze_final_split(raw_root, processed_root, frame_path, g2_report, processed_audit)
    if json.loads(split_bytes) != frozen:
        raise ValueError("Private B4 split differs from audited registered partitions")
    processing_bytes = (processed_root / "processing-manifest.json").read_bytes()
    processing = ProcessingManifest.model_validate_json(processing_bytes)
    by_id = {record.match_id: record for record in processing.matches}
    partitions = cast(dict[str, list[dict[str, object]]], frozen["partitions"])
    if (
        len(by_id) != 36000
        or len(processing.matches) != 36000
        or set(partitions) != {"train", "calibration", "test"}
        or {key: len(value) for key, value in partitions.items()}
        != {"train": 24000, "calibration": 6000, "test": 6000}
        or {str(entry["match_id"]) for values in partitions.values() for entry in values}
        != set(by_id)
    ):
        raise ValueError("B4 frozen partition inventory is incomplete")
    bindings: dict[str, object] = {
        "schema_version": "league-ews-b4-staging-v1",
        "split_sha256": _sha(split_bytes),
        "processing_manifest_sha256": _sha(processing_bytes),
        "sequence_steps": STEPS,
        "sequence_features": list(SEQUENCE_FEATURES),
        "targets": list(LABELS),
        "matches_per_shard": MATCHES_PER_SHARD,
        "test_matches_unread": 6000,
        "identifiers_in_summary": False,
    }
    return bindings, partitions, by_id


def _expected(partitions: dict[str, list[dict[str, object]]]) -> list[tuple[str, int, int]]:
    return [
        (partition, start, min(start + MATCHES_PER_SHARD, len(partitions[partition])))
        for partition in ("train", "calibration")
        for start in range(0, len(partitions[partition]), MATCHES_PER_SHARD)
    ]


def _filename(partition: str, start: int) -> str:
    return f"{partition}.{start:05d}.npz"


def _materialize(
    processed_root: Path, entries: list[dict[str, object]], by_id: dict[str, Any]
) -> dict[str, np.ndarray]:
    inputs: list[np.ndarray] = []
    masks: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    offsets = [0]
    for entry in entries:
        match_id = str(entry["match_id"])
        record = by_id[match_id]
        payload = _read_match(processed_root, match_id, record.sha256)
        sequence = build_causal_sequences(payload, match_id)
        if len(sequence.times_ms) != record.observations:
            raise ValueError("B4 staged observations differ from audited manifest")
        inputs.append(sequence.inputs)
        masks.append(sequence.history_mask)
        targets.append(sequence.targets)
        offsets.append(offsets[-1] + record.observations)
    if not inputs:
        raise ValueError("B4 shard cannot be empty")
    return {
        "inputs": np.concatenate(inputs),
        "history_mask": np.concatenate(masks),
        "targets": np.concatenate(targets),
        "match_offsets": np.asarray(offsets, dtype=np.int64),
    }


def _same_arrays(path: Path, values: dict[str, np.ndarray]) -> bool:
    try:
        with np.load(path, allow_pickle=False) as existing:
            return set(existing.files) == set(values) and all(
                np.array_equal(existing[key], value) for key, value in values.items()
            )
    except (OSError, ValueError, KeyError):
        return False


def stage_b4_sequences(
    raw_root: str | Path,
    processed_root: str | Path,
    frame_path: str | Path,
    g2_report: str | Path,
    processed_audit: str | Path,
    split_path: str | Path,
    output_root: str | Path,
    *,
    max_new_shards: int = 4,
) -> dict[str, object]:
    """Stage a bounded prefix of shards; no test match payload is opened."""

    if max_new_shards < 1:
        raise ValueError("max_new_shards must be positive")
    processed = Path(processed_root)
    bindings, partitions, by_id = _bound_inputs(
        Path(raw_root),
        processed,
        Path(frame_path),
        Path(g2_report),
        Path(processed_audit),
        Path(split_path),
    )
    planned = _expected(partitions)
    root = Path(output_root)
    manifest_path = root / "staging-manifest.json"
    stored = json.loads(manifest_path.read_bytes()) if manifest_path.exists() else None
    if stored is None:
        if root.exists():
            allowed = {"shards", "staging-manifest.json.partial"}
            if {path.name for path in root.iterdir()} - allowed:
                raise ValueError("Unregistered B4 staging files require inspection")
        progress: dict[str, Any] = {**bindings, "shards": [], "complete": False}
    else:
        progress = stored
        if any(progress.get(key) != value for key, value in bindings.items()):
            raise ValueError("Existing B4 staging differs from frozen inputs")
    shards = progress.get("shards")
    if not isinstance(shards, list) or len(shards) > len(planned):
        raise ValueError("B4 staging inventory is invalid")
    for index, record in enumerate(shards):
        partition, start, end = planned[index]
        filename = _filename(partition, start)
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
            raise ValueError("Existing B4 shard or checksum differs from manifest")
    if progress.get("complete") != (len(shards) == len(planned)):
        raise ValueError("B4 staging completion differs from shard inventory")
    unexpected = {path.name for path in (root / "shards").glob("*.npz")} - {
        _filename(partition, start) for partition, start, _ in planned[: len(shards) + 1]
    }
    if unexpected:
        raise ValueError("Unexpected B4 shard files require inspection")
    for partition, start, end in planned[len(shards) : len(shards) + max_new_shards]:
        name = _filename(partition, start)
        path = root / "shards" / name
        arrays = _materialize(processed, partitions[partition][start:end], by_id)
        if path.exists():
            if not _same_arrays(path, arrays):
                raise ValueError("Unregistered B4 shard differs from audited source")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
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
                "file": name,
                "sha256": _sha(path.read_bytes()),
            }
        )
        progress["complete"] = len(shards) == len(planned)
        root.mkdir(parents=True, exist_ok=True)
        temporary = manifest_path.with_suffix(".json.partial")
        temporary.write_text(json.dumps(progress, sort_keys=True, separators=(",", ":")) + "\n")
        temporary.replace(manifest_path)
        print(f"Staged {len(shards)}/{len(planned)} B4 shards", flush=True)
    return {
        "schema_version": bindings["schema_version"],
        "complete": progress["complete"],
        "staged_shards": len(shards),
        "total_shards": len(planned),
        "staged_matches": sum(int(item["matches"]) for item in shards),
        "train_matches": sum(
            int(item["matches"]) for item in shards if item["partition"] == "train"
        ),
        "calibration_matches": sum(
            int(item["matches"]) for item in shards if item["partition"] == "calibration"
        ),
        "test_matches_unread": 6000,
        "split_sha256": bindings["split_sha256"],
        "identifiers_in_summary": False,
    }
