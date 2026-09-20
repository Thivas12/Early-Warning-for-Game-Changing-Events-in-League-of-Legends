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
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from league_ews.constants import EVENTS, RIFTHAZARD_HORIZONS_SECONDS
from league_ews.duration_rule import validate_duration_rule
from league_ews.labels import extract_event_index
from league_ews.pilot_collection import RawRecordLike, validate_pilot_collection_binding
from league_ews.sampling import (
    SamplingFrame,
    SamplingStage,
    load_registered_sampling_frame,
    sampling_coverage,
)
from league_ews.timeline import normalise_match_timeline

RAW_MANIFEST_SCHEMA_VERSION = "riot-raw-collection-v2"
RAW_VALIDATION_SCHEMA_VERSION = "riot-raw-validation-v5"
EVENT_SPOT_CHECK_SCHEMA_VERSION: Literal["riot-event-spot-check-v1"] = "riot-event-spot-check-v1"


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


class ProcessedBundleRecord(BaseModel):
    """One de-identified processed match declared by its processing manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    match_id: str = Field(pattern=r"^[A-Z0-9]+_[0-9]+$")
    game_version: str = Field(pattern=r"^\d+\.\d+(?:\.\d+)*$")
    observations: int = Field(gt=0)
    baron_events: int = Field(ge=0)
    dragon_events: int = Field(ge=0)
    teamfight_events: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ProcessingManifest(BaseModel):
    """Strict subset of the processing manifest needed for review binding."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["league-ews-processing-manifest-v1"]
    normalizer: Literal["riot-match-v5-normalized-v1"]
    label_policy: Literal["exact-future-events-v1"]
    matches: tuple[ProcessedBundleRecord, ...] = Field(min_length=1)
    contains_player_identifiers: Literal[False]


class EventSpotCheckSample(BaseModel):
    """One manually reviewed bundle, bound to the raw payload checksums."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    match_id: str = Field(pattern=r"^[A-Z0-9]+_[0-9]+$")
    match_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    timeline_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    processed_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    objective_events_match_source: Literal[True]
    teamfight_episodes_match_source: Literal[True]
    strict_future_labels_match_processed: Literal[True]


class EventSpotCheckRecord(BaseModel):
    """Private human-review evidence for exact event and label construction."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-event-spot-check-v1"]
    reviewed_at: datetime
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    processing_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewer_attestation: Literal[True]
    samples: tuple[EventSpotCheckSample, ...] = Field(min_length=1)


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


def _platform(match_id: str) -> str:
    return match_id.split("_", maxsplit=1)[0]


def _frame_eligibility_matches(
    match_payload: Mapping[str, Any],
    entry: RawBundleRecord,
    frame: SamplingFrame,
) -> bool:
    info = match_payload.get("info")
    metadata = match_payload.get("metadata")
    if not isinstance(info, Mapping) or not isinstance(metadata, Mapping):
        return False
    expected_routes = {route.platform_id: route.regional_route for route in frame.route_platforms}
    platform = _platform(entry.match_id)
    expected_patches = {patch.game_version_patch for patch in frame.patches}
    info_participants = info.get("participants")
    metadata_participants = metadata.get("participants")
    return (
        expected_routes.get(platform) == entry.regional_route
        and info.get("platformId") == platform
        and _patch(entry.game_version) in expected_patches
        and info.get("queueId") == frame.eligibility.queue_id
        and info.get("mapId") == frame.eligibility.map_id
        and info.get("gameMode") == frame.eligibility.game_mode
        and info.get("gameType") == frame.eligibility.game_type
        and isinstance(info_participants, list)
        and len(info_participants) == frame.eligibility.participant_count
        and isinstance(metadata_participants, list)
        and len(metadata_participants) == frame.eligibility.participant_count
    )


def _duration_eligibility_matches(
    match_payload: Mapping[str, Any],
    minimum_seconds: int,
) -> bool:
    info = match_payload.get("info")
    if not isinstance(info, Mapping):
        return False
    value = info.get("gameDuration")
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum_seconds


def _sampling_frame_context(
    sampling_frame: str | Path | None,
    sampling_stage: SamplingStage | None,
) -> tuple[SamplingFrame | None, dict[str, object]]:
    if (sampling_frame is None) != (sampling_stage is None):
        raise ValueError("sampling_frame and sampling_stage must be supplied together")
    if sampling_frame is None:
        return None, {
            "status": "not-supplied",
            "stage": None,
            "frame_id": None,
            "frame_sha256": None,
        }
    try:
        frame, frame_sha256 = load_registered_sampling_frame(sampling_frame)
    except ValueError:
        return None, {
            "status": "invalid",
            "stage": sampling_stage,
            "frame_id": None,
            "frame_sha256": None,
        }
    return frame, {
        "status": "pending-collection-check",
        "stage": sampling_stage,
        "frame_id": frame.frame_id,
        "frame_sha256": frame_sha256,
        "duration_cutoff_status": frame.duration.final_rule_status,
    }


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


def create_event_spot_check_record(
    raw_root: str | Path,
    processed_root: str | Path,
    match_ids: tuple[str, ...],
    *,
    objective_events_match_source: bool,
    teamfight_episodes_match_source: bool,
    strict_future_labels_match_processed: bool,
    reviewed_at: datetime | None = None,
) -> dict[str, object]:
    """Create a private checksum-bound record after a human event review."""

    if not all(
        (
            objective_events_match_source,
            teamfight_episodes_match_source,
            strict_future_labels_match_processed,
        )
    ):
        raise ValueError("All event spot-check comparisons must be explicitly confirmed")
    if not match_ids or len(match_ids) != len(set(match_ids)):
        raise ValueError("Spot-check match IDs must be present and unique")

    timestamp = reviewed_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("reviewed_at must be timezone-aware")

    root = Path(raw_root)
    try:
        manifest_content, raw_manifest = _json_object(root / "collection-manifest.json")
        manifest = RawCollectionManifest.model_validate(raw_manifest)
    except (OSError, json.JSONDecodeError, ValueError, ValidationError) as error:
        raise ValueError("A valid raw collection manifest is required") from error

    available_by_id = {entry.match_id: entry for entry in manifest.available}
    if any(match_id not in available_by_id for match_id in match_ids):
        raise ValueError("Every spot-check match must exist in the collection manifest")

    processed = Path(processed_root)
    try:
        processing_manifest_content, raw_processing_manifest = _json_object(
            processed / "processing-manifest.json"
        )
        processing_manifest = ProcessingManifest.model_validate(raw_processing_manifest)
    except (OSError, json.JSONDecodeError, ValueError, ValidationError) as error:
        raise ValueError("A valid processing manifest is required") from error
    processed_by_id = {entry.match_id: entry for entry in processing_manifest.matches}
    if (
        len(processed_by_id) != len(processing_manifest.matches)
        or set(processed_by_id) != set(available_by_id)
        or any(
            processed_by_id[match_id].game_version != available_by_id[match_id].game_version
            for match_id in available_by_id
        )
    ):
        raise ValueError("Processed output must exactly cover the raw manifest inventory")

    samples: list[dict[str, object]] = []
    for match_id in match_ids:
        entry = available_by_id[match_id]
        try:
            match_content = (root / "matches" / f"{match_id}.json").read_bytes()
            timeline_content = (root / "timelines" / f"{match_id}.json").read_bytes()
        except OSError as error:
            raise ValueError("Every spot-check match must have a complete raw pair") from error
        if (
            hashlib.sha256(match_content).hexdigest() != entry.match_sha256
            or hashlib.sha256(timeline_content).hexdigest() != entry.timeline_sha256
        ):
            raise ValueError("Every spot-check raw pair must match its manifest checksums")
        processed_entry = processed_by_id[match_id]
        try:
            processed_content = (processed / "matches" / f"{match_id}.json").read_bytes()
        except OSError as error:
            raise ValueError("Every spot-check match must have processed output") from error
        if hashlib.sha256(processed_content).hexdigest() != processed_entry.sha256:
            raise ValueError("Every spot-check processed file must match its manifest checksum")
        samples.append(
            {
                "match_id": match_id,
                "match_sha256": entry.match_sha256,
                "timeline_sha256": entry.timeline_sha256,
                "processed_sha256": processed_entry.sha256,
                "objective_events_match_source": True,
                "teamfight_episodes_match_source": True,
                "strict_future_labels_match_processed": True,
            }
        )

    record = EventSpotCheckRecord(
        schema_version=EVENT_SPOT_CHECK_SCHEMA_VERSION,
        reviewed_at=timestamp,
        manifest_sha256=hashlib.sha256(manifest_content).hexdigest(),
        processing_manifest_sha256=hashlib.sha256(processing_manifest_content).hexdigest(),
        reviewer_attestation=True,
        samples=tuple(EventSpotCheckSample.model_validate(sample) for sample in samples),
    )
    return record.model_dump(mode="json")


def _spot_check_placeholder(
    status: Literal["pending", "blocked"],
    *,
    required_cells: int,
) -> dict[str, object]:
    message = (
        "No private event spot-check record was supplied"
        if status == "pending"
        else "A valid collection manifest is required before reviewing spot-check evidence"
    )
    return {
        "status": status,
        "schema_version": EVENT_SPOT_CHECK_SCHEMA_VERSION,
        "reviewed_at": None,
        "sampled_bundles": 0,
        "covered_route_patch_cells": 0,
        "required_route_patch_cells": required_cells,
        "message": message,
        "checks": [],
    }


def _processed_sample_checksums_valid(
    samples: tuple[EventSpotCheckSample, ...],
    *,
    processed_root: Path | None,
    processed_by_id: Mapping[str, ProcessedBundleRecord],
) -> bool:
    if processed_root is None or any(sample.match_id not in processed_by_id for sample in samples):
        return False
    for sample in samples:
        if sample.processed_sha256 != processed_by_id[sample.match_id].sha256:
            return False
        try:
            content = (processed_root / "matches" / f"{sample.match_id}.json").read_bytes()
        except OSError:
            return False
        if hashlib.sha256(content).hexdigest() != sample.processed_sha256:
            return False
    return True


def _event_spot_check_summary(
    record_path: Path | None,
    *,
    processed_root: Path | None,
    checked_at: datetime,
    manifest_sha256: str,
    valid_by_id: Mapping[str, RawBundleRecord],
) -> dict[str, object]:
    required_cells = {
        (entry.regional_route, _patch(entry.game_version)) for entry in valid_by_id.values()
    }
    if record_path is None:
        return _spot_check_placeholder("pending", required_cells=len(required_cells))

    try:
        _, raw_record = _json_object(record_path)
        record = EventSpotCheckRecord.model_validate(raw_record)
    except (OSError, json.JSONDecodeError, ValueError, ValidationError):
        check = RawValidationCheck(
            check_id="record-schema",
            passed=False,
            message="Private event spot-check record is missing, unreadable, or invalid",
        )
        return {
            "status": "failed",
            "schema_version": EVENT_SPOT_CHECK_SCHEMA_VERSION,
            "reviewed_at": None,
            "sampled_bundles": 0,
            "covered_route_patch_cells": 0,
            "required_route_patch_cells": len(required_cells),
            "message": "Manual event spot-check evidence failed validation",
            "checks": [asdict(check)],
        }

    try:
        if processed_root is None:
            raise ValueError("processed root was not supplied")
        processing_manifest_content, raw_processing_manifest = _json_object(
            processed_root / "processing-manifest.json"
        )
        processing_manifest = ProcessingManifest.model_validate(raw_processing_manifest)
        processed_by_id = {entry.match_id: entry for entry in processing_manifest.matches}
        processing_manifest_valid = True
        processing_inventory_valid = (
            len(processed_by_id) == len(processing_manifest.matches)
            and set(processed_by_id) == set(valid_by_id)
            and all(
                processed_by_id[match_id].game_version == valid_by_id[match_id].game_version
                for match_id in valid_by_id
            )
        )
    except (OSError, json.JSONDecodeError, ValueError, ValidationError):
        processing_manifest_content = b""
        processed_by_id = {}
        processing_manifest_valid = False
        processing_inventory_valid = False

    sample_ids = [sample.match_id for sample in record.samples]
    record_date_valid = record.reviewed_at.tzinfo is not None and record.reviewed_at <= checked_at
    manifest_binding_valid = record.manifest_sha256 == manifest_sha256
    inventory_valid = len(sample_ids) == len(set(sample_ids)) and all(
        match_id in valid_by_id for match_id in sample_ids
    )
    checksums_valid = inventory_valid and all(
        sample.match_sha256 == valid_by_id[sample.match_id].match_sha256
        and sample.timeline_sha256 == valid_by_id[sample.match_id].timeline_sha256
        for sample in record.samples
    )
    processing_manifest_binding_valid = (
        processing_manifest_valid
        and record.processing_manifest_sha256
        == hashlib.sha256(processing_manifest_content).hexdigest()
    )
    processed_inventory_valid = processing_manifest_valid and all(
        sample.match_id in processed_by_id for sample in record.samples
    )
    processed_checksums_valid = processed_inventory_valid and _processed_sample_checksums_valid(
        record.samples,
        processed_root=processed_root,
        processed_by_id=processed_by_id,
    )
    covered_cells = {
        (
            valid_by_id[match_id].regional_route,
            _patch(valid_by_id[match_id].game_version),
        )
        for match_id in sample_ids
        if match_id in valid_by_id
    }
    cell_coverage_valid = bool(required_cells) and covered_cells == required_cells
    checks = [
        RawValidationCheck(
            check_id="record-schema",
            passed=True,
            message=f"Event spot-check record conforms to {EVENT_SPOT_CHECK_SCHEMA_VERSION}",
        ),
        _check(
            "review-date",
            record_date_valid,
            "Event spot-check review time is valid",
            "Event spot-check review time must be timezone-aware and not in the future",
        ),
        _check(
            "manifest-binding",
            manifest_binding_valid,
            "Event spot-check evidence is bound to the current collection manifest",
            "Event spot-check evidence was created for a different collection manifest",
        ),
        _check(
            "sample-inventory",
            inventory_valid,
            "Every reviewed sample is a unique valid bundle",
            "Reviewed samples must be unique valid bundles in the current manifest",
        ),
        _check(
            "sample-checksums",
            checksums_valid,
            "Every reviewed sample matches its recorded raw checksums",
            "One or more reviewed samples do not match their recorded raw checksums",
        ),
        _check(
            "processing-inventory",
            processing_inventory_valid,
            "Processed output exactly covers the valid raw inventory",
            "Processed output does not exactly cover the valid raw inventory",
        ),
        _check(
            "processing-manifest-binding",
            processing_manifest_binding_valid,
            "Event spot-check evidence is bound to the current processing manifest",
            "Event spot-check evidence was created for different or unavailable processed data",
        ),
        _check(
            "processed-sample-inventory",
            processed_inventory_valid,
            "Every reviewed sample has unique processed output",
            "One or more reviewed samples are absent or duplicated in processed output",
        ),
        _check(
            "processed-sample-checksums",
            processed_checksums_valid,
            "Every reviewed processed sample matches its recorded checksum",
            "One or more reviewed processed samples fail checksum validation",
        ),
        _check(
            "route-patch-coverage",
            cell_coverage_valid,
            f"Human review covers all {len(required_cells)} observed route-patch cells",
            "Human review does not cover every observed route-patch cell",
        ),
    ]
    passed = all(check.passed for check in checks)
    return {
        "status": "passed" if passed else "failed",
        "schema_version": record.schema_version,
        "reviewed_at": record.reviewed_at.astimezone(UTC).isoformat(),
        "sampled_bundles": len(record.samples),
        "covered_route_patch_cells": len(covered_cells),
        "required_route_patch_cells": len(required_cells),
        "message": (
            "Manual event spot-check evidence passed"
            if passed
            else "Manual event spot-check evidence failed validation"
        ),
        "checks": [asdict(check) for check in checks],
    }


def _failed_manifest_report(
    checked_at: datetime,
    *,
    min_routes: int,
    min_patches: int,
    spot_check_requested: bool,
    pilot_selection_requested: bool,
    sampling_frame_summary: Mapping[str, object],
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
        "automated_passed": False,
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
        "manual_event_spot_check": _spot_check_placeholder(
            "blocked" if spot_check_requested else "pending",
            required_cells=0,
        ),
        "pilot_selection": {
            "status": "blocked" if pilot_selection_requested else "not-supplied",
            "summary": None,
        },
        "sampling_frame": dict(sampling_frame_summary),
    }


def validate_raw_collection(
    raw_root: str | Path,
    *,
    min_routes: int = 2,
    min_patches: int = 6,
    event_spot_check: str | Path | None = None,
    processed_root: str | Path | None = None,
    sampling_frame: str | Path | None = None,
    sampling_stage: SamplingStage | None = None,
    discovery_plan: str | Path | None = None,
    discovery_root: str | Path | None = None,
    selection_root: str | Path | None = None,
    duration_rule: str | Path | None = None,
    duration_analysis: str | Path | None = None,
    checked_at: datetime | None = None,
) -> dict[str, object]:
    """Validate raw inventory, provenance and normalized shape without network access."""

    if min_routes < 1 or min_patches < 1:
        raise ValueError("Coverage minima must be positive")
    pilot_selection_inputs = (discovery_plan, discovery_root, selection_root)
    pilot_selection_requested = all(value is not None for value in pilot_selection_inputs)
    if any(value is not None for value in pilot_selection_inputs) and not pilot_selection_requested:
        raise ValueError(
            "Pilot binding requires discovery_plan, discovery_root and selection_root together"
        )
    if pilot_selection_requested and (sampling_frame is None or sampling_stage != "pilot"):
        raise ValueError("Pilot binding requires a sampling frame and sampling_stage='pilot'")
    duration_inputs = (duration_rule, duration_analysis)
    duration_rule_requested = all(value is not None for value in duration_inputs)
    if any(value is not None for value in duration_inputs) and not duration_rule_requested:
        raise ValueError(
            "Final duration binding requires duration_rule and duration_analysis together"
        )
    if duration_rule_requested and (sampling_frame is None or sampling_stage != "final"):
        raise ValueError("Duration binding requires a sampling frame and sampling_stage='final'")
    timestamp = checked_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("checked_at must be timezone-aware")
    frame, frame_summary = _sampling_frame_context(sampling_frame, sampling_stage)
    duration_validation: dict[str, object] | None = None
    duration_minimum_seconds: int | None = None
    if duration_rule_requested:
        assert duration_rule is not None
        assert duration_analysis is not None
        assert sampling_frame is not None
        duration_validation = validate_duration_rule(
            duration_rule,
            sampling_frame,
            duration_analysis,
        )
        duration_summary = duration_validation.get("summary")
        if duration_validation["passed"] and isinstance(duration_summary, Mapping):
            minimum = duration_summary.get("final_minimum_seconds")
            if isinstance(minimum, int) and not isinstance(minimum, bool):
                duration_minimum_seconds = minimum

    root = Path(raw_root)
    try:
        manifest_content, raw_manifest = _json_object(root / "collection-manifest.json")
        manifest = RawCollectionManifest.model_validate(raw_manifest)
    except (OSError, json.JSONDecodeError, ValueError, ValidationError):
        return _failed_manifest_report(
            timestamp,
            min_routes=min_routes,
            min_patches=min_patches,
            spot_check_requested=event_spot_check is not None,
            pilot_selection_requested=pilot_selection_requested,
            sampling_frame_summary=frame_summary,
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
    frame_cell_counts = Counter[tuple[str, str, str]]()
    frame_eligibility_valid = True
    duration_eligibility_valid = duration_minimum_seconds is not None
    valid_by_id: dict[str, RawBundleRecord] = {}
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
            valid_by_id[entry.match_id] = entry
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
            game_patch = _patch(normalized.game_version)
            patch_counts[game_patch] += 1
            if frame is not None:
                frame_cell_counts[entry.regional_route, _platform(entry.match_id), game_patch] += 1
                frame_eligibility_valid = frame_eligibility_valid and _frame_eligibility_matches(
                    match_payload,
                    entry,
                    frame,
                )
            if sampling_stage == "final" and duration_minimum_seconds is not None:
                duration_eligibility_valid = (
                    duration_eligibility_valid
                    and _duration_eligibility_matches(
                        match_payload,
                        duration_minimum_seconds,
                    )
                )

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
    if pilot_selection_requested:
        assert sampling_frame is not None
        assert discovery_plan is not None
        assert discovery_root is not None
        assert selection_root is not None
        pilot_binding = validate_pilot_collection_binding(
            root,
            sampling_frame,
            discovery_plan,
            discovery_root,
            selection_root,
            manifest_content=manifest_content,
            available_by_id=cast(Mapping[str, RawRecordLike], available_by_id),
        )
        checks.append(
            RawValidationCheck(
                check_id="pilot-selection-binding",
                passed=bool(pilot_binding["passed"]),
                message=str(pilot_binding["message"]),
            )
        )
        pilot_selection_summary: dict[str, object] = {
            "status": "passed" if pilot_binding["passed"] else "failed",
            "summary": pilot_binding["summary"],
        }
    else:
        pilot_selection_summary = {
            "status": "not-supplied",
            "summary": None,
        }
    if sampling_frame is not None:
        frame_valid = frame is not None
        checks.append(
            _check(
                "sampling-frame",
                frame_valid,
                "The supplied sampling frame is valid and checksum-bound in this report",
                "The supplied sampling frame failed registered contract validation",
            )
        )
        coverage: dict[str, object]
        if frame is None or sampling_stage is None:
            coverage = {
                "stage": sampling_stage,
                "passed": False,
                "expected_cells": 0,
                "represented_cells": 0,
                "unexpected_cells": 0,
                "target_matches": 0,
                "observed_in_frame_matches": 0,
                "exact_cell_targets_met": False,
            }
        else:
            coverage = sampling_coverage(frame, frame_cell_counts, stage=sampling_stage)
        checks.extend(
            [
                _check(
                    "frame-eligibility",
                    frame_valid and frame_eligibility_valid,
                    "Every valid bundle matches the frozen route, patch and queue eligibility",
                    "One or more valid bundles fall outside the frozen eligibility contract",
                ),
                _check(
                    "frame-cell-coverage",
                    coverage["passed"] is True,
                    "Every route-patch cell exactly meets its registered stage target",
                    "The exact registered route-patch cell targets are not all met",
                ),
            ]
        )
        if sampling_stage == "final":
            duration_rule_passed = bool(
                duration_validation is not None and duration_validation["passed"]
            )
            checks.append(
                RawValidationCheck(
                    check_id="final-duration-freeze",
                    passed=duration_rule_passed,
                    message=(
                        "The checksum-bound post-pilot duration rule is valid"
                        if duration_rule_passed
                        else "Final collection requires the valid checksum-bound 180-second rule"
                    ),
                )
            )
            checks.append(
                _check(
                    "final-duration-eligibility",
                    duration_rule_passed and duration_eligibility_valid,
                    "Every final match satisfies gameDuration >= 180 seconds",
                    "One or more final matches fail the frozen minimum-duration rule",
                )
            )
            frame_summary["duration_rule"] = {
                "status": "passed" if duration_rule_passed else "missing-or-invalid",
                "rule_id": (
                    duration_validation.get("rule_id") if duration_validation is not None else None
                ),
                "rule_sha256": (
                    duration_validation.get("rule_sha256")
                    if duration_validation is not None
                    else None
                ),
                "final_minimum_seconds": duration_minimum_seconds,
            }
        frame_summary.update(coverage)
        if frame_valid and sampling_stage == "final":
            frame_summary["status"] = (
                "passed"
                if coverage["passed"] is True
                and duration_validation is not None
                and duration_validation["passed"]
                and duration_eligibility_valid
                else "incomplete-or-duration-blocked"
            )
        elif frame_valid:
            frame_summary["status"] = "passed" if coverage["passed"] is True else "incomplete"
    automated_passed = all(check.passed for check in checks)
    spot_check = _event_spot_check_summary(
        Path(event_spot_check) if event_spot_check is not None else None,
        processed_root=Path(processed_root) if processed_root is not None else None,
        checked_at=timestamp,
        manifest_sha256=hashlib.sha256(manifest_content).hexdigest(),
        valid_by_id=valid_by_id,
    )
    passed = automated_passed and (event_spot_check is None or spot_check["status"] == "passed")
    g2_complete = (
        passed
        and sampling_stage == "final"
        and event_spot_check is not None
        and spot_check["status"] == "passed"
    )
    return {
        "schema_version": RAW_VALIDATION_SCHEMA_VERSION,
        "checked_at": timestamp.astimezone(UTC).isoformat(),
        "manifest_sha256": hashlib.sha256(manifest_content).hexdigest(),
        "coverage_requirements": {
            "min_regional_routes": min_routes,
            "min_patches": min_patches,
        },
        "passed": passed,
        "automated_passed": automated_passed,
        "g2_complete": g2_complete,
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
        "manual_event_spot_check": spot_check,
        "pilot_selection": pilot_selection_summary,
        "sampling_frame": frame_summary,
    }
