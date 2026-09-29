"""Identifier-free source-field audit of the frozen train/calibration timelines."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

FIELDS = ("totalGold", "xp", "level", "minionsKilled", "jungleMinionsKilled", "position")
PATCHES = ("16.12", "16.13", "16.14", "16.15", "16.16")
ROUTES = ("europe", "americas")
TRAIN_MATCHES = 24000
CALIBRATION_MATCHES = 6000
TEST_MATCHES = 6000


def _read(path: Path) -> tuple[dict[str, Any], str]:
    content = path.read_bytes()
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("Source-field audit requires JSON objects")
    return payload, hashlib.sha256(content).hexdigest()


def _usable_number(value: object, *, level: bool = False) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        number = float(value)
    except OverflowError:
        return False
    return math.isfinite(number) and (number >= 1 if level else number >= 0)


def _count_timeline_fields(
    timeline: object,
    route: str,
    patch: str,
    counts: Counter[tuple[str, str, str, str]],
    states: Counter[tuple[str, str]],
) -> int:
    info = timeline.get("info") if isinstance(timeline, dict) else None
    frames = info.get("frames") if isinstance(info, dict) else None
    if not isinstance(frames, list) or not frames:
        raise ValueError("Source-field audit timeline frames differ")
    for frame in frames:
        participant_frames = frame.get("participantFrames") if isinstance(frame, dict) else None
        if not isinstance(participant_frames, dict):
            raise ValueError("Source-field audit participant frames differ")
        for participant_id in range(1, 11):
            state = participant_frames.get(str(participant_id))
            if not isinstance(state, dict):
                raise ValueError("Source-field audit participant inventory differs")
            states[route, patch] += 1
            for field in FIELDS:
                if field not in state or state[field] is None:
                    counts[route, patch, field, "absent"] += 1
                elif field == "position":
                    value = state[field]
                    if not (
                        isinstance(value, dict)
                        and _usable_number(value.get("x"))
                        and _usable_number(value.get("y"))
                    ):
                        counts[route, patch, field, "invalid"] += 1
                elif not _usable_number(state[field], level=field == "level"):
                    counts[route, patch, field, "invalid"] += 1
    return len(frames)


def _audit_members(
    members: list[dict[str, Any]],
    partition: str,
    by_id: dict[str, dict[str, Any]],
    raw: Path,
    visited: set[str],
    counts: Counter[tuple[str, str, str, str]],
    states: Counter[tuple[str, str]],
) -> int:
    frames_count = 0
    for member in members:
        match_id = member.get("match_id")
        route = member.get("regional_route")
        patch = member.get("game_version_patch")
        record = by_id.get(match_id) if isinstance(match_id, str) else None
        if (
            not isinstance(match_id, str)
            or re.fullmatch(r"[A-Z0-9]+_[0-9]+", match_id) is None
            or match_id in visited
            or route not in ROUTES
            or patch not in PATCHES
            or (partition == "calibration") != (patch == "16.16")
            or not isinstance(record, dict)
            or record.get("regional_route") != route
            or not isinstance(record.get("game_version"), str)
            or not record["game_version"].startswith(patch + ".")
        ):
            raise ValueError("Source-field audit split differs from collection inventory")
        visited.add(match_id)
        content = (raw / "timelines" / f"{match_id}.json").read_bytes()
        if hashlib.sha256(content).hexdigest() != record.get("timeline_sha256"):
            raise ValueError("Source-field audit timeline checksum differs")
        frames_count += _count_timeline_fields(json.loads(content), route, patch, counts, states)
    return frames_count


def audit_raw_field_coverage(
    raw_root: str | Path, g2_path: str | Path, split_path: str | Path
) -> dict[str, Any]:
    """Count unavailable source fields without reading the sealed test timelines."""

    raw = Path(raw_root)
    g2, g2_sha = _read(Path(g2_path))
    split, split_sha = _read(Path(split_path))
    manifest, manifest_sha = _read(raw / "collection-manifest.json")
    partitions = split.get("partitions")
    if not (
        g2.get("schema_version") == "riot-raw-validation-v5"
        and g2.get("passed") is True
        and g2.get("g2_complete") is True
        and g2.get("manifest_sha256") == manifest_sha
        and split.get("schema_version") == "league-ews-final-split-v1"
        and split.get("g2_report_sha256") == g2_sha
        and split.get("raw_manifest_sha256") == manifest_sha
        and split.get("summary", {}).get("counts")
        == {"train": TRAIN_MATCHES, "calibration": CALIBRATION_MATCHES, "test": TEST_MATCHES}
        and manifest.get("schema_version") == "riot-raw-collection-v2"
        and isinstance(partitions, dict)
        and set(partitions) == {"train", "calibration", "test"}
    ):
        raise ValueError("Source-field audit requires the passed, bound final collection and split")
    entries = manifest.get("available")
    if not isinstance(entries, list) or len(entries) != (
        TRAIN_MATCHES + CALIBRATION_MATCHES + TEST_MATCHES
    ):
        raise ValueError("Source-field audit requires the complete 36,000-bundle inventory")
    by_id: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("match_id"), str):
            raise ValueError("Source-field audit inventory contains invalid records")
        by_id[entry["match_id"]] = entry
    if len(by_id) != TRAIN_MATCHES + CALIBRATION_MATCHES + TEST_MATCHES:
        raise ValueError("Source-field audit inventory contains duplicates")
    counts: Counter[tuple[str, str, str, str]] = Counter()
    states: Counter[tuple[str, str]] = Counter()
    frames_count = 0
    visited: set[str] = set()
    for partition in ("train", "calibration"):
        members = partitions[partition]
        if not isinstance(members, list) or len(members) != (
            TRAIN_MATCHES if partition == "train" else CALIBRATION_MATCHES
        ):
            raise ValueError("Source-field audit split inventory differs")
        if not all(isinstance(member, dict) for member in members):
            raise ValueError("Source-field audit split member differs")
        frames_count += _audit_members(members, partition, by_id, raw, visited, counts, states)
    rows = [
        {
            "route": route,
            "patch": patch,
            "participant_states": states[route, patch],
            "fields": {
                field: {
                    "absent": counts[route, patch, field, "absent"],
                    "invalid": counts[route, patch, field, "invalid"],
                }
                for field in FIELDS
            },
        }
        for patch in PATCHES
        for route in ROUTES
    ]
    return {
        "schema_version": "league-ews-source-field-coverage-v1",
        "matches": len(visited),
        "frames": frames_count,
        "participant_states": sum(states.values()),
        "cells": rows,
        "g2_sha256": g2_sha,
        "split_sha256": split_sha,
        "raw_manifest_sha256": manifest_sha,
        "test_timelines_unread": True,
        "contains_player_identifiers": False,
    }


def write_raw_field_coverage(
    raw_root: str | Path, g2_path: str | Path, split_path: str | Path, output: str | Path
) -> dict[str, Any]:
    report = audit_raw_field_coverage(raw_root, g2_path, split_path)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".partial")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return report
