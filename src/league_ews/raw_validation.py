"""Offline integrity and coverage validation for private raw Riot bundles."""

from __future__ import annotations

import hashlib
import json
from bisect import bisect_left
from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from statistics import median
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from league_ews.constants import EVENTS, RIFTHAZARD_HORIZONS_SECONDS
from league_ews.labels import extract_event_index
from league_ews.timeline import normalise_match_timeline

RAW_MANIFEST_SCHEMA_VERSION = "riot-raw-collection-v2"
RAW_VALIDATION_SCHEMA_VERSION = "riot-raw-validation-v2"


class RawBundleRecord(BaseModel):
    """One checksum-bound match/timeline pair in the collection manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    match_id: str = Field(pattern=r"^[A-Z0-9]+_[0-9]+$")
    regional_route: Literal["americas", "asia", "europe", "sea"]
    game_version: str = Field(pattern=r"^\d+\.\d+(?:\.\d+)*$")
    game_creation_ms: int = Field(gt=0)
    match_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    timeline_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class RawCollectionManifest(BaseModel):
    """Strict schema for resumable raw collection provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-raw-collection-v2"]
    collected_at: datetime
    requested: int = Field(ge=0)
    collected: tuple[RawBundleRecord, ...]
    skipped_existing: tuple[str, ...]
    available: tuple[RawBundleRecord, ...]
    contains_raw_player_identifiers: Literal[True]
    redistribution: Literal["not-authorized-by-this-manifest"]


@dataclass(frozen=True)
class RawValidationCheck:
    check_id: str
    passed: bool
    message: str


def _check(check_id: str, passed: bool, success: str, failure: str) -> RawValidationCheck:
    return RawValidationCheck(
        check_id=check_id,
        passed=passed,
        message=success if passed else failure,
    )


def _json_object(path: Path) -> tuple[bytes, Mapping[str, Any]]:
    content = path.read_bytes()
    payload = json.loads(content)
    if not isinstance(payload, Mapping):
        raise ValueError("JSON payload is not an object")
    return content, payload


def _payload_match_id(payload: Mapping[str, Any]) -> str:
    metadata = payload.get("metadata")
    if not isinstance(metadata, Mapping):
        return ""
    return str(metadata.get("matchId", ""))


def _patch(game_version: str) -> str:
    parts = game_version.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else game_version


def _cadence_summary(intervals_ms: list[int]) -> dict[str, int | float | None]:
    if not intervals_ms:
        return {
            "interval_count": 0,
            "minimum": None,
            "median": None,
            "maximum": None,
        }
    return {
        "interval_count": len(intervals_ms),
        "minimum": min(intervals_ms),
        "median": median(intervals_ms),
        "maximum": max(intervals_ms),
    }


def _event_labelability_summary(
    event_counts: Counter[str],
    labelable_counts: Counter[tuple[str, int]],
) -> dict[str, object]:
    summary: dict[str, object] = {}
    for event in EVENTS:
        total = event_counts[event]
        summary[event] = {
            "total_events": total,
            "by_horizon_seconds": {
                str(horizon): {
                    "labelable_events": labelable_counts[event, horizon],
                    "fraction": labelable_counts[event, horizon] / total if total else None,
                }
                for horizon in RIFTHAZARD_HORIZONS_SECONDS
            },
        }
    return summary


def _record_labelability(
    observation_times_ms: tuple[int, ...],
    event_times_ms: tuple[int, ...],
    *,
    event: str,
    counts: Counter[tuple[str, int]],
) -> None:
    for event_time_ms in event_times_ms:
        prior_index = bisect_left(observation_times_ms, event_time_ms) - 1
        if prior_index < 0:
            continue
        lead_time_ms = event_time_ms - observation_times_ms[prior_index]
        for horizon in RIFTHAZARD_HORIZONS_SECONDS:
            if lead_time_ms <= horizon * 1000:
                counts[event, horizon] += 1


def _failed_manifest_report(
    checked_at: datetime,
    *,
    min_routes: int,
    min_patches: int,
) -> dict[str, object]:
    check = RawValidationCheck(
        check_id="manifest-schema",
        passed=False,
        message="Collection manifest is missing, unreadable, or invalid",
    )
    return {
        "schema_version": RAW_VALIDATION_SCHEMA_VERSION,
        "checked_at": checked_at.astimezone(UTC).isoformat(),
        "manifest_sha256": None,
        "coverage_requirements": {
            "min_regional_routes": min_routes,
            "min_patches": min_patches,
        },
        "passed": False,
        "g2_complete": False,
        "checks": [asdict(check)],
        "summary": {
            "manifest_bundles": 0,
            "valid_bundles": 0,
            "observations": 0,
            "events": {event: 0 for event in EVENTS},
            "observation_cadence_ms": _cadence_summary([]),
            "event_labelability": _event_labelability_summary(Counter(), Counter()),
            "regional_routes": {},
            "patches": {},
        },
        "manual_event_spot_check": "pending",
    }


def validate_raw_collection(
    raw_root: str | Path,
    *,
    min_routes: int = 2,
    min_patches: int = 6,
    checked_at: datetime | None = None,
) -> dict[str, object]:
    """Validate raw inventory, provenance and normalized shape without network access."""

    if min_routes < 1 or min_patches < 1:
        raise ValueError("Coverage minima must be positive")
    timestamp = checked_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("checked_at must be timezone-aware")

    root = Path(raw_root)
    try:
        manifest_content, raw_manifest = _json_object(root / "collection-manifest.json")
        manifest = RawCollectionManifest.model_validate(raw_manifest)
    except (OSError, json.JSONDecodeError, ValueError, ValidationError):
        return _failed_manifest_report(
            timestamp,
            min_routes=min_routes,
            min_patches=min_patches,
        )

    checks = [
        RawValidationCheck(
            check_id="manifest-schema",
            passed=True,
            message=f"Manifest conforms to {RAW_MANIFEST_SCHEMA_VERSION}",
        )
    ]
    available_ids = [entry.match_id for entry in manifest.available]
    collected_ids = [entry.match_id for entry in manifest.collected]
    skipped_ids = list(manifest.skipped_existing)
    available_by_id = {entry.match_id: entry for entry in manifest.available}
    run_inventory_valid = (
        manifest.collected_at.tzinfo is not None
        and manifest.collected_at <= timestamp
        and len(available_ids) == len(set(available_ids))
        and len(collected_ids) == len(set(collected_ids))
        and len(skipped_ids) == len(set(skipped_ids))
        and not set(collected_ids).intersection(skipped_ids)
        and len(collected_ids) + len(skipped_ids) == manifest.requested
        and set(collected_ids).union(skipped_ids).issubset(available_by_id)
        and all(available_by_id.get(entry.match_id) == entry for entry in manifest.collected)
    )
    checks.append(
        _check(
            "manifest-inventory",
            run_inventory_valid,
            "Current-run and cumulative manifest inventories are consistent",
            "Current-run or cumulative manifest inventory is inconsistent",
        )
    )

    match_files = {path.stem: path for path in (root / "matches").glob("*.json")}
    timeline_files = {path.stem: path for path in (root / "timelines").glob("*.json")}
    partial_count = sum(1 for _ in root.rglob("*.partial"))
    pair_inventory_valid = (
        set(match_files) == set(timeline_files) == set(available_ids) and partial_count == 0
    )
    checks.append(
        _check(
            "pair-inventory",
            pair_inventory_valid,
            f"All {len(available_by_id)} manifest bundles have complete file pairs",
            "Manifest/file inventory differs, or incomplete partial files remain",
        )
    )

    checksums_valid = True
    identities_valid = True
    schemas_valid = True
    metadata_valid = True
    normalized_bundles = 0
    valid_bundles = 0
    observations = 0
    event_counts = Counter[str]()
    labelable_counts = Counter[tuple[str, int]]()
    cadence_intervals_ms: list[int] = []
    route_counts = Counter[str]()
    patch_counts = Counter[str]()
    for entry in available_by_id.values():
        match_path = match_files.get(entry.match_id)
        timeline_path = timeline_files.get(entry.match_id)
        if match_path is None or timeline_path is None:
            checksums_valid = identities_valid = schemas_valid = metadata_valid = False
            continue
        try:
            match_content, match_payload = _json_object(match_path)
            timeline_content, timeline_payload = _json_object(timeline_path)
        except (OSError, json.JSONDecodeError, ValueError):
            checksums_valid = identities_valid = schemas_valid = metadata_valid = False
            continue

        pair_checksums_valid = (
            hashlib.sha256(match_content).hexdigest() == entry.match_sha256
            and hashlib.sha256(timeline_content).hexdigest() == entry.timeline_sha256
        )
        checksums_valid = checksums_valid and pair_checksums_valid
        pair_identity_valid = (
            _payload_match_id(match_payload) == entry.match_id
            and _payload_match_id(timeline_payload) == entry.match_id
        )
        identities_valid = identities_valid and pair_identity_valid
        try:
            normalized = normalise_match_timeline(match_payload, timeline_payload)
            events = extract_event_index(normalized)
        except (TypeError, ValueError, ValidationError):
            schemas_valid = False
            continue

        pair_metadata_valid = (
            normalized.match_id == entry.match_id
            and normalized.game_version == entry.game_version
            and normalized.game_creation_ms == entry.game_creation_ms
        )
        metadata_valid = metadata_valid and pair_metadata_valid
        normalized_bundles += 1
        if pair_checksums_valid and pair_identity_valid and pair_metadata_valid:
            valid_bundles += 1
            observations += len(normalized.observations)
            observation_times_ms = tuple(
                observation.timestamp_ms for observation in normalized.observations
            )
            cadence_intervals_ms.extend(
                later - earlier for earlier, later in pairwise(observation_times_ms)
            )
            for event in EVENTS:
                event_times_ms = events.for_event(event)
                event_counts[event] += len(event_times_ms)
                _record_labelability(
                    observation_times_ms,
                    event_times_ms,
                    event=event,
                    counts=labelable_counts,
                )
            route_counts[entry.regional_route] += 1
            patch_counts[_patch(normalized.game_version)] += 1

    checks.extend(
        [
            _check(
                "checksums",
                checksums_valid,
                "All bundle hashes match the cumulative manifest",
                "One or more bundle hashes differ from the cumulative manifest",
            ),
            _check(
                "payload-identity",
                identities_valid,
                "Payload and manifest identities agree",
                "One or more payload identities disagree with the manifest",
            ),
            _check(
                "normalized-schema",
                schemas_valid and normalized_bundles == len(available_by_id),
                "Every bundle normalizes under the supported causal schema",
                "One or more bundles fail supported causal schema normalization",
            ),
            _check(
                "manifest-metadata",
                metadata_valid,
                "Manifest version and creation metadata agree with payloads",
                "Manifest version or creation metadata disagree with payloads",
            ),
            _check(
                "route-coverage",
                len(route_counts) >= min_routes,
                f"Observed {len(route_counts)} regional routes (minimum {min_routes})",
                f"Regional-route coverage is below the minimum of {min_routes}",
            ),
            _check(
                "patch-coverage",
                len(patch_counts) >= min_patches,
                f"Observed {len(patch_counts)} patches (minimum {min_patches})",
                f"Patch coverage is below the minimum of {min_patches}",
            ),
        ]
    )
    passed = all(check.passed for check in checks)
    return {
        "schema_version": RAW_VALIDATION_SCHEMA_VERSION,
        "checked_at": timestamp.astimezone(UTC).isoformat(),
        "manifest_sha256": hashlib.sha256(manifest_content).hexdigest(),
        "coverage_requirements": {
            "min_regional_routes": min_routes,
            "min_patches": min_patches,
        },
        "passed": passed,
        "g2_complete": False,
        "checks": [asdict(check) for check in checks],
        "summary": {
            "manifest_bundles": len(available_by_id),
            "valid_bundles": valid_bundles,
            "observations": observations,
            "events": {event: event_counts[event] for event in EVENTS},
            "observation_cadence_ms": _cadence_summary(cadence_intervals_ms),
            "event_labelability": _event_labelability_summary(
                event_counts,
                labelable_counts,
            ),
            "regional_routes": dict(sorted(route_counts.items())),
            "patches": dict(sorted(patch_counts.items())),
        },
        "manual_event_spot_check": "pending",
    }
