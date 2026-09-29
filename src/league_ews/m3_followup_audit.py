"""Checksum-bound audit of terminal follow-up on train/calibration only."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.baseline_floor import LABELS, _read_match
from league_ews.final_selection import FinalSelectedPool
from league_ews.hazards import EVENT_TYPES
from league_ews.m1_backend import at_risk_mask
from league_ews.m1_normalizer import _validated_manifest
from league_ews.m3_followup import confirmed_followup_masks
from league_ews.raw_validation import ProcessingManifest

HORIZONS = (10, 20, 30, 60)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _counts() -> dict[str, Any]:
    return {
        "matches": 0,
        "rows": 0,
        "original_loss_bins": 0,
        "confirmed_loss_bins": 0,
        "negative_labels_without_full_followup": [0] * 12,
        "positive_labels": [0] * 12,
        "fully_followed_negative_labels": [0] * 12,
        "last_frame_after_duration": 0,
        "last_frame_before_duration": 0,
        "last_frame_at_duration": 0,
        "maximum_absolute_gap_ms": 0,
    }


def _accumulate(
    counts: dict[str, Any],
    times: np.ndarray,
    hazards: np.ndarray,
    labels: np.ndarray,
    game_duration_ms: int | None = None,
) -> None:
    """Count exposure without printing source timelines or identifiers."""

    exposure, known = confirmed_followup_masks(times, hazards, game_duration_ms=game_duration_ms)
    expected = np.maximum.accumulate(hazards, axis=-1)[:, :, [0, 1, 2, 5]].reshape(-1, 12)
    if not np.array_equal(expected, labels):
        raise ValueError("Staged labels disagree with exact future events")
    known_rows = known.reshape(-1, 12)
    at_risk = at_risk_mask(hazards)
    counts["matches"] += 1
    counts["rows"] += len(times)
    counts["original_loss_bins"] += int(at_risk.sum())
    counts["confirmed_loss_bins"] += int(exposure.sum())
    if game_duration_ms is not None:
        gap = int(times[-1]) - game_duration_ms
        counts["last_frame_after_duration"] += gap > 0
        counts["last_frame_before_duration"] += gap < 0
        counts["last_frame_at_duration"] += gap == 0
        counts["maximum_absolute_gap_ms"] = max(counts["maximum_absolute_gap_ms"], abs(gap))
    for index in range(12):
        positive = labels[:, index] == 1
        counts["positive_labels"][index] += int(positive.sum())
        counts["negative_labels_without_full_followup"][index] += int(
            ((~positive) & (~known_rows[:, index])).sum()
        )
        counts["fully_followed_negative_labels"][index] += int(
            ((~positive) & known_rows[:, index]).sum()
        )


def _source_times_and_hazards(
    payload: Mapping[str, Any], match_id: str
) -> tuple[np.ndarray, np.ndarray]:
    if payload.get("schema_version") != "league-ews-processed-match-v1":
        raise ValueError("Unsupported processed match")
    timeline = payload.get("timeline")
    index = payload.get("event_index")
    if not isinstance(timeline, dict) or not isinstance(index, dict):
        raise ValueError("Processed timeline or source events missing")
    frames = timeline.get("observations")
    if timeline.get("match_id") != match_id or not isinstance(frames, list) or not frames:
        raise ValueError("Processed match identity or frames differ")
    times = np.asarray([frame["timestamp_ms"] for frame in frames], dtype=np.int64)
    if times[0] < 0 or np.any(np.diff(times) <= 0):
        raise ValueError("Source observation times are invalid")
    hazards = np.zeros((len(times), 3, 6), np.float32)
    for event_index, event in enumerate(EVENT_TYPES):
        values = index.get(f"{event}_ms")
        if not isinstance(values, list) or any(type(item) is not int for item in values):
            raise ValueError("Source event timestamps are invalid")
        events = np.asarray(values, dtype=np.int64)
        if (len(events) and (events[0] < 0 or events[-1] > times[-1])) or np.any(
            np.diff(events) <= 0
        ):
            raise ValueError("Source event lies outside confirmed follow-up")
        positions = np.searchsorted(events, times, side="right")
        present = positions < len(events)
        if present.any():
            row = np.flatnonzero(present)
            delays = events[positions[present]] - times[present]
            in_window = delays <= 60_000
            bins = (delays[in_window] - 1) // 10_000
            hazards[row[in_window], event_index, bins] = 1
    return times, hazards


def audit_confirmed_followup(
    processed_root: str | Path,
    split_path: str | Path,
    staging_root: str | Path,
    selection_root: str | Path,
    output: str | Path,
) -> dict[str, Any]:
    """Read only frozen train/calibration matches and existing graph target arrays."""

    processed = Path(processed_root)
    stage = Path(staging_root)
    split_bytes = Path(split_path).read_bytes()
    split = json.loads(split_bytes)
    processing_bytes = (processed / "processing-manifest.json").read_bytes()
    inventory = ProcessingManifest.model_validate_json(processing_bytes)
    manifest_bytes, staging = _validated_manifest(stage)
    selection = Path(selection_root)
    pool_bytes = (selection / "selected-pool.json").read_bytes()
    pool = FinalSelectedPool.model_validate_json(pool_bytes)
    selection_manifest_bytes = (selection / "selection-manifest.json").read_bytes()
    selection_manifest = json.loads(selection_manifest_bytes)
    if (
        split.get("schema_version") != "league-ews-final-split-v1"
        or split.get("processing_manifest_sha256") != _sha(processing_bytes)
        or split.get("summary", {}).get("counts")
        != {"train": 24000, "calibration": 6000, "test": 6000}
        or len(inventory.matches) != 36000
        or staging["split_sha256"] != _sha(split_bytes)
        or staging["processing_manifest_sha256"] != _sha(processing_bytes)
        or selection_manifest.get("schema_version") != "riot-final-selection-manifest-v1"
        or selection_manifest.get("complete") is not True
        or selection_manifest.get("selected_match_ids") != 36000
        or selection_manifest.get("selected_pool_sha256") != _sha(pool_bytes)
        or pool.frame_sha256 != split.get("frame_sha256")
        or pool.selected_match_ids != 36000
        or len(pool.cells) != 12
    ):
        raise ValueError("Follow-up audit differs from frozen split or processed inventory")
    partitions = split.get("partitions")
    if not isinstance(partitions, dict) or {k: len(v) for k, v in partitions.items()} != {
        "train": 24000,
        "calibration": 6000,
        "test": 6000,
    }:
        raise ValueError("Follow-up audit requires all three frozen partitions")
    by_id = {record.match_id: record for record in inventory.matches}
    if len(by_id) != 36000:
        raise ValueError("Processed match inventory contains duplicates")
    durations: dict[str, tuple[int, str, str]] = {}
    for cell in pool.cells:
        if cell.selected_count != 3000 or len(cell.selected) != 3000:
            raise ValueError("Selection cell has an incomplete duration inventory")
        for record in cell.selected:
            if record.match_id in durations:
                raise ValueError("Selection duration inventory contains duplicate matches")
            durations[record.match_id] = (
                record.game_duration_seconds * 1000,
                cell.regional_route,
                cell.game_version_patch,
            )
    if len(durations) != 36000:
        raise ValueError("Frozen selection durations are incomplete")
    profiles: dict[str, dict[str, Any]] = {"train": _counts(), "calibration": _counts()}
    cells: dict[str, dict[str, Any]] = {}
    for entry in staging["shards"]:
        partition = entry["partition"]
        members = partitions[partition][entry["start"] : entry["start"] + entry["matches"]]
        with np.load(stage / "shards" / entry["file"], allow_pickle=False) as shard:
            if set(shard.files) != {
                "nodes",
                "edges",
                "history_mask",
                "ages_minutes",
                "targets",
                "hazard_targets",
                "match_offsets",
            }:
                raise ValueError("Staged graph array inventory differs")
            offsets = shard["match_offsets"]
            hazards = shard["hazard_targets"]
            labels = shard["targets"]
            if (
                offsets.shape != (len(members) + 1,)
                or offsets.dtype != np.int64
                or offsets[0] != 0
                or offsets[-1] != entry["observations"]
                or np.any(np.diff(offsets) <= 0)
                or hazards.shape != (entry["observations"], 3, 6)
                or labels.shape != (entry["observations"], 12)
            ):
                raise ValueError("Staged follow-up row offsets differ")
            for i, member in enumerate(members):
                match_id = member["match_id"]
                if match_id not in by_id or match_id not in durations:
                    raise ValueError("Staged match is absent from processed inventory")
                duration_ms, route, patch = durations[match_id]
                if (route, patch) != (member["regional_route"], member["game_version_patch"]):
                    raise ValueError("Selection duration cell differs from split")
                payload = _read_match(processed, match_id, by_id[match_id].sha256)
                times, expected = _source_times_and_hazards(payload, match_id)
                start, stop = int(offsets[i]), int(offsets[i + 1])
                if len(times) != stop - start or not np.array_equal(expected, hazards[start:stop]):
                    raise ValueError("Staged hazards disagree with checksum-bound source events")
                key = f"{partition}/{member['regional_route']}/{member['game_version_patch']}"
                if key not in cells:
                    cells[key] = _counts()
                _accumulate(profiles[partition], times, expected, labels[start:stop], duration_ms)
                _accumulate(cells[key], times, expected, labels[start:stop], duration_ms)
    if profiles["train"]["matches"] != 24000 or profiles["calibration"]["matches"] != 6000:
        raise ValueError("Audited match count differs from frozen partitions")
    report = {
        "schema_version": "league-ews-confirmed-followup-audit-v1",
        "processing_manifest_sha256": _sha(processing_bytes),
        "split_sha256": _sha(split_bytes),
        "staging_manifest_sha256": _sha(manifest_bytes),
        "selected_pool_sha256": _sha(pool_bytes),
        "selection_manifest_sha256": _sha(selection_manifest_bytes),
        "followup_boundary": "minimum-of-screened-game-duration-and-last-source-frame",
        "horizons_seconds": list(HORIZONS),
        "label_order": list(LABELS),
        "partitions": profiles,
        "cells": cells,
        "test_matches_unread": 6000,
        "identifiers_in_report": False,
    }
    target = Path(output)
    content = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if target.exists() and target.read_bytes() != content:
        raise ValueError("Existing follow-up audit differs from bound source data")
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        temporary = target.with_suffix(target.suffix + ".partial")
        temporary.write_bytes(content)
        temporary.replace(target)
    return report
