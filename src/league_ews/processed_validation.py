"""Offline audit of every processed match against the frozen raw inventory."""

from __future__ import annotations

import hashlib
import json
from bisect import bisect_right
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from league_ews.constants import RIFTHAZARD_HORIZONS_SECONDS
from league_ews.labels import EventIndex, extract_event_index
from league_ews.raw_validation import ProcessingManifest, RawCollectionManifest
from league_ews.timeline import NormalizedTimeline

_EVENTS = ("baron", "dragon", "teamfight")
_IDENTIFIER_KEYS = (
    b'"puuid"',
    b'"summonername"',
    b'"summonerid"',
    b'"accountid"',
    b'"riotidgamename"',
    b'"riotidtagline"',
    b'"gamename"',
    b'"tagline"',
)


def _read_object(path: Path) -> tuple[bytes, Mapping[str, Any]]:
    content = path.read_bytes()
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object")
    return content, payload


def _labels_match(
    observations: tuple[Any, ...],
    event_index: EventIndex,
    labels: object,
) -> bool:
    if not isinstance(labels, list) or len(labels) != len(observations):
        return False
    expected_keys = {"timestamp_ms"} | {
        f"y_{event}_{horizon}" for event in _EVENTS for horizon in RIFTHAZARD_HORIZONS_SECONDS
    }
    for observation, row in zip(observations, labels, strict=True):
        if not isinstance(row, dict) or set(row) != expected_keys:
            return False
        timestamp = observation.timestamp_ms
        if type(row["timestamp_ms"]) is not int or row["timestamp_ms"] != timestamp:
            return False
        for event in _EVENTS:
            times = event_index.for_event(event)
            index = bisect_right(times, timestamp)
            delay = times[index] - timestamp if index < len(times) else None
            for horizon in RIFTHAZARD_HORIZONS_SECONDS:
                actual = row[f"y_{event}_{horizon}"]
                expected = int(delay is not None and delay <= horizon * 1000)
                if type(actual) is not int or actual != expected:
                    return False
    return True


def _bundle_checks(content: bytes, payload: Mapping[str, Any], record: Any) -> dict[str, bool]:
    checks = {
        "checksums": hashlib.sha256(content).hexdigest() == record.sha256,
        "payload-schema": False,
        "event-index": False,
        "future-labels": False,
        "player-identifiers": not any(key in content.lower() for key in _IDENTIFIER_KEYS),
    }
    if set(payload) != {"schema_version", "timeline", "event_index", "labels"}:
        return checks
    if payload["schema_version"] != "league-ews-processed-match-v1":
        return checks
    try:
        timeline = NormalizedTimeline.model_validate(payload["timeline"])
    except (ValidationError, ValueError, TypeError):
        return checks
    checks["payload-schema"] = (
        timeline.schema_version == "riot-match-v5-normalized-v1"
        and timeline.match_id == record.match_id
        and timeline.game_version == record.game_version
        and len(timeline.observations) == record.observations
    )
    if not checks["payload-schema"]:
        return checks
    events = extract_event_index(timeline)
    checks["event-index"] = payload["event_index"] == {
        "baron_ms": list(events.baron_ms),
        "dragon_ms": list(events.dragon_ms),
        "teamfight_ms": list(events.teamfight_ms),
    } and (
        len(events.baron_ms),
        len(events.dragon_ms),
        len(events.teamfight_ms),
    ) == (record.baron_events, record.dragon_events, record.teamfight_events)
    checks["future-labels"] = _labels_match(timeline.observations, events, payload["labels"])
    return checks


def validate_processed_collection(
    raw_root: str | Path,
    processed_root: str | Path,
    raw_validation_report: str | Path,
) -> dict[str, object]:
    """Verify identities, bytes, events and strict future labels for all bundles."""

    raw = Path(raw_root)
    processed = Path(processed_root)
    try:
        raw_content, raw_payload = _read_object(raw / "collection-manifest.json")
        raw_manifest = RawCollectionManifest.model_validate(raw_payload)
        processed_content, processed_payload = _read_object(processed / "processing-manifest.json")
        processing_manifest = ProcessingManifest.model_validate(processed_payload)
        _, validation = _read_object(Path(raw_validation_report))
    except (OSError, json.JSONDecodeError, ValueError, ValidationError):
        return {
            "schema_version": "league-ews-processed-validation-v1",
            "passed": False,
            "failed_checks": ["input-manifests"],
            "summary": {"validated_matches": 0, "expected_matches": 0},
        }

    raw_by_id = {record.match_id: record for record in raw_manifest.available}
    processed_by_id = {record.match_id: record for record in processing_manifest.matches}
    raw_binding = (
        validation.get("schema_version") == "riot-raw-validation-v5"
        and validation.get("passed") is True
        and validation.get("automated_passed") is True
        and validation.get("manifest_sha256") == hashlib.sha256(raw_content).hexdigest()
        and isinstance(validation.get("summary"), dict)
        and validation["summary"].get("valid_bundles") == len(raw_manifest.available)
    )
    inventory = (
        len(raw_by_id) == len(raw_manifest.available)
        and len(processed_by_id) == len(processing_manifest.matches)
        and set(raw_by_id) == set(processed_by_id)
        and all(
            raw_by_id[match_id].game_version == record.game_version
            for match_id, record in processed_by_id.items()
            if match_id in raw_by_id
        )
        and {path.stem for path in (processed / "matches").glob("*.json")} == set(processed_by_id)
    )
    failed = set()
    if not raw_binding:
        failed.add("raw-validation-binding")
    if not inventory:
        failed.add("processed-inventory")
    validated = 0
    for record in processing_manifest.matches:
        try:
            content, payload = _read_object(processed / "matches" / f"{record.match_id}.json")
            checks = _bundle_checks(content, payload, record)
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            failed.add("processed-payload")
            continue
        failed.update(name for name, passed in checks.items() if not passed)
        if all(checks.values()):
            validated += 1
    return {
        "schema_version": "league-ews-processed-validation-v1",
        "passed": not failed,
        "raw_manifest_sha256": hashlib.sha256(raw_content).hexdigest(),
        "processing_manifest_sha256": hashlib.sha256(processed_content).hexdigest(),
        "failed_checks": sorted(failed),
        "summary": {
            "expected_matches": len(raw_manifest.available),
            "validated_matches": validated,
            "processed_files": len(list((processed / "matches").glob("*.json"))),
            "contains_player_identifiers": "player-identifiers" in failed,
        },
    }
