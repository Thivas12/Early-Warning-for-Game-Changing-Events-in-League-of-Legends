"""Freeze the registered patch split from audited private manifest metadata."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, cast

from pydantic import ValidationError

from league_ews.raw_validation import ProcessingManifest, RawCollectionManifest
from league_ews.sampling import SamplingFrame, load_registered_sampling_frame, sampling_cells


def _load_json(path: Path) -> tuple[str, dict[str, Any]]:
    content = path.read_bytes()
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object")
    return hashlib.sha256(content).hexdigest(), payload


def _assign(
    raw: RawCollectionManifest, processed: ProcessingManifest, frame: SamplingFrame
) -> dict[str, list[dict[str, object]]]:
    """Assign whole matches using only creation time, route and patch metadata."""

    expected = {
        (cell.regional_route, cell.platform_id, cell.game_version_patch): cell.final_target
        for cell in sampling_cells(frame)
    }
    if len(expected) != 12 or set(expected.values()) != {3000}:
        raise ValueError("Registered final split requires 12 cells of 3,000 matches")
    processed_by_id = {record.match_id: record for record in processed.matches}
    raw_by_id = {record.match_id: record for record in raw.available}
    if (
        len(raw_by_id) != 36000
        or len(raw.available) != 36000
        or len(processed_by_id) != 36000
        or len(processed.matches) != 36000
        or set(raw_by_id) != set(processed_by_id)
    ):
        raise ValueError("Final raw and processed inventories must contain the same 36,000 matches")
    patch_to_split = {
        **dict.fromkeys(frame.split.training_patches, "train"),
        frame.split.calibration_patch: "calibration",
        frame.split.final_test_patch: "test",
    }
    if len(patch_to_split) != len(frame.patches):
        raise ValueError("Frozen split does not partition the registered patches")
    counts: Counter[tuple[str, str, str]] = Counter()
    partitions: dict[str, list[dict[str, object]]] = {
        "train": [],
        "calibration": [],
        "test": [],
    }
    for record in raw.available:
        patch = ".".join(record.game_version.split(".")[:2])
        platform = record.match_id.split("_", 1)[0]
        cell = (record.regional_route, platform, patch)
        if (
            cell not in expected
            or processed_by_id[record.match_id].game_version != record.game_version
        ):
            raise ValueError("Final match lies outside the registered route-patch inventory")
        counts[cell] += 1
        partitions[patch_to_split[patch]].append(
            {
                "match_id": record.match_id,
                "regional_route": record.regional_route,
                "game_version_patch": patch,
                "game_creation_ms": record.game_creation_ms,
            }
        )
    if counts != expected:
        raise ValueError("Final split does not have exactly 3,000 matches per cell")
    for entries in partitions.values():
        entries.sort(key=lambda item: (cast(int, item["game_creation_ms"]), str(item["match_id"])))
    if {name: len(entries) for name, entries in partitions.items()} != {
        "train": 24000,
        "calibration": 6000,
        "test": 6000,
    }:
        raise ValueError("Frozen split has unexpected partition counts")
    return partitions


def freeze_final_split(
    raw_root: str | Path,
    processed_root: str | Path,
    frame_path: str | Path,
    g2_report_path: str | Path,
    processed_audit_path: str | Path,
) -> dict[str, object]:
    """Require G2 and processed audit bindings before freezing private match membership.

    No match payload, label, outcome or feature file is opened by this step.
    """

    frame, frame_sha = load_registered_sampling_frame(frame_path)
    raw_sha, raw_payload = _load_json(Path(raw_root) / "collection-manifest.json")
    processed_sha, processed_payload = _load_json(Path(processed_root) / "processing-manifest.json")
    g2_sha, g2 = _load_json(Path(g2_report_path))
    audit_sha, audit = _load_json(Path(processed_audit_path))
    try:
        raw = RawCollectionManifest.model_validate(raw_payload)
        processed = ProcessingManifest.model_validate(processed_payload)
    except ValidationError as error:
        raise ValueError("Final collection manifest schema rejected") from error
    if not (
        g2.get("schema_version") == "riot-raw-validation-v5"
        and g2.get("passed") is True
        and g2.get("automated_passed") is True
        and g2.get("g2_complete") is True
        and g2.get("manifest_sha256") == raw_sha
        and isinstance(g2.get("manual_event_spot_check"), dict)
        and g2["manual_event_spot_check"].get("status") == "passed"
        and isinstance(g2.get("sampling_frame"), dict)
        and g2["sampling_frame"].get("status") == "passed"
        and isinstance(g2.get("summary"), dict)
        and g2["summary"].get("valid_bundles") == 36000
    ):
        raise ValueError("Final G2 report is incomplete or does not bind to the raw manifest")
    if not (
        audit.get("schema_version") == "league-ews-processed-validation-v1"
        and audit.get("passed") is True
        and audit.get("raw_manifest_sha256") == raw_sha
        and audit.get("processing_manifest_sha256") == processed_sha
        and isinstance(audit.get("summary"), dict)
        and audit["summary"].get("validated_matches") == 36000
        and audit["summary"].get("contains_player_identifiers") is False
    ):
        raise ValueError("Processed audit is incomplete or does not bind to both manifests")
    partitions = _assign(raw, processed, frame)
    return {
        "schema_version": "league-ews-final-split-v1",
        "frame_id": frame.frame_id,
        "frame_sha256": frame_sha,
        "raw_manifest_sha256": raw_sha,
        "processing_manifest_sha256": processed_sha,
        "g2_report_sha256": g2_sha,
        "processed_audit_sha256": audit_sha,
        "order": "game_creation_ms-then-match_id",
        "partitions": partitions,
        "summary": {
            "identifiers_in_summary": False,
            "counts": {name: len(entries) for name, entries in partitions.items()},
            "patches": {
                "train": list(frame.split.training_patches),
                "calibration": [frame.split.calibration_patch],
                "test": [frame.split.final_test_patch],
            },
            "route_patch_cells": 12,
        },
    }
