"""Private, reproducible source-to-processed event review packet."""

from __future__ import annotations

import hashlib
import json
from bisect import bisect_right
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from league_ews.constants import RIFTHAZARD_HORIZONS_SECONDS
from league_ews.raw_validation import ProcessingManifest, RawCollectionManifest

_EVENTS = ("baron", "dragon", "teamfight")


def _object(path: Path) -> tuple[bytes, dict[str, Any]]:
    content = path.read_bytes()
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object")
    return content, payload


def _source_events(
    timeline: Mapping[str, Any],
) -> tuple[dict[str, list[int]], list[dict[str, Any]]]:
    info = timeline.get("info")
    if not isinstance(info, dict) or not isinstance(info.get("frames"), list):
        raise ValueError("Invalid source timeline frames")
    objectives: dict[str, set[int]] = {"baron": set(), "dragon": set()}
    kills: list[int] = []
    for frame in info["frames"]:
        if not isinstance(frame, dict) or not isinstance(frame.get("events"), list):
            raise ValueError("Invalid source timeline events")
        for event in frame["events"]:
            if not isinstance(event, dict):
                raise ValueError("Invalid source timeline event")
            if event.get("type") not in {"ELITE_MONSTER_KILL", "CHAMPION_KILL"}:
                continue
            if type(event.get("timestamp")) is not int:
                raise ValueError("Invalid source event timestamp")
            timestamp = event["timestamp"]
            if event.get("type") == "ELITE_MONSTER_KILL":
                if event.get("monsterType") == "BARON_NASHOR":
                    objectives["baron"].add(timestamp)
                elif event.get("monsterType") == "DRAGON":
                    objectives["dragon"].add(timestamp)
            elif event.get("type") == "CHAMPION_KILL":
                kills.append(timestamp)
    episodes: list[list[int]] = []
    for timestamp in sorted(kills):
        if episodes and timestamp - episodes[-1][-1] <= 10_000:
            episodes[-1].append(timestamp)
        else:
            episodes.append([timestamp])
    qualified = [episode for episode in episodes if len(episode) >= 3]
    return (
        {
            "baron_ms": sorted(objectives["baron"]),
            "dragon_ms": sorted(objectives["dragon"]),
            "teamfight_ms": [episode[0] for episode in qualified],
        },
        [{"onset_ms": episode[0], "kill_ms": episode} for episode in qualified],
    )


def _witnesses(
    processed: Mapping[str, Any], source_index: Mapping[str, list[int]]
) -> list[dict[str, object]]:
    rows = processed.get("labels")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Processed labels are missing")
    witnesses: list[dict[str, object]] = []
    for event in _EVENTS:
        times = source_index[f"{event}_ms"]
        for horizon in RIFTHAZARD_HORIZONS_SECONDS:
            label = f"y_{event}_{horizon}"
            selected = next((row for row in rows if row.get(label) == 1), rows[0])
            timestamp = selected["timestamp_ms"]
            index = bisect_right(times, timestamp)
            next_event = times[index] if index < len(times) else None
            delay = next_event - timestamp if next_event is not None else None
            expected = int(delay is not None and delay <= horizon * 1000)
            if type(selected[label]) is not int or selected[label] != expected:
                raise ValueError("Review witness does not match strict future-event rule")
            witnesses.append(
                {
                    "label": label,
                    "observation_ms": timestamp,
                    "next_source_event_ms": next_event,
                    "delay_ms": delay,
                    "expected": expected,
                    "processed": selected[label],
                }
            )
    return witnesses


def create_final_event_review_packet(
    raw_root: str | Path,
    processed_root: str | Path,
    processed_audit: str | Path,
    *,
    required_cells: int = 12,
) -> dict[str, object]:
    """Select event-rich QC samples without modifying research selection."""

    raw = Path(raw_root)
    processed = Path(processed_root)
    try:
        raw_content, raw_payload = _object(raw / "collection-manifest.json")
        processed_content, processed_payload = _object(processed / "processing-manifest.json")
        audit_content, audit = _object(Path(processed_audit))
        raw_manifest = RawCollectionManifest.model_validate(raw_payload)
        processing_manifest = ProcessingManifest.model_validate(processed_payload)
    except (OSError, json.JSONDecodeError, ValueError, ValidationError) as error:
        raise ValueError("Valid raw/processed manifests and audit report are required") from error
    raw_sha = hashlib.sha256(raw_content).hexdigest()
    processed_sha = hashlib.sha256(processed_content).hexdigest()
    if (
        audit.get("schema_version") != "league-ews-processed-validation-v1"
        or audit.get("passed") is not True
        or audit.get("raw_manifest_sha256") != raw_sha
        or audit.get("processing_manifest_sha256") != processed_sha
    ):
        raise ValueError("Passed processed audit does not bind the current manifests")
    by_id = {record.match_id: record for record in processing_manifest.matches}
    if len(by_id) != len(processing_manifest.matches):
        raise ValueError("Processed manifest has duplicate matches")
    cells: dict[tuple[str, str], list[Any]] = defaultdict(list)
    for record in raw_manifest.available:
        processed_record = by_id.get(record.match_id)
        if processed_record is None or processed_record.game_version != record.game_version:
            raise ValueError("Processed inventory does not match raw inventory")
        if all(getattr(processed_record, f"{event}_events") > 0 for event in _EVENTS):
            cells[(record.regional_route, ".".join(record.game_version.split(".")[:2]))].append(
                record
            )
    if len(cells) != required_cells:
        raise ValueError("At least one event-rich sample is required in every registered cell")

    samples: list[dict[str, object]] = []
    for (route, patch), candidates in sorted(cells.items()):
        selected = min(
            candidates,
            key=lambda record: hashlib.sha256(f"{raw_sha}:{record.match_id}".encode()).hexdigest(),
        )
        match_id = selected.match_id
        raw_path = raw / "timelines" / f"{match_id}.json"
        processed_path = processed / "matches" / f"{match_id}.json"
        raw_bytes, source = _object(raw_path)
        processed_bytes, normalized = _object(processed_path)
        if (
            hashlib.sha256(raw_bytes).hexdigest() != selected.timeline_sha256
            or hashlib.sha256(processed_bytes).hexdigest() != by_id[match_id].sha256
        ):
            raise ValueError("Selected review sample checksum differs from its manifest")
        source_index, episodes = _source_events(source)
        if normalized.get("event_index") != source_index:
            raise ValueError("Selected source and processed event indexes disagree")
        samples.append(
            {
                "regional_route": route,
                "game_version_patch": patch,
                "match_id": match_id,
                "raw_timeline_path": str(raw_path),
                "processed_path": str(processed_path),
                "source_event_index": source_index,
                "source_teamfight_episodes": episodes,
                "processed_event_index": normalized["event_index"],
                "label_witnesses": _witnesses(normalized, source_index),
            }
        )
    return {
        "schema_version": "league-ews-final-event-review-packet-v1",
        "raw_manifest_sha256": raw_sha,
        "processing_manifest_sha256": processed_sha,
        "processed_audit_sha256": hashlib.sha256(audit_content).hexdigest(),
        "selection_rule": "event-rich-in-each-cell;minimum-sha256(raw-manifest-sha:match-id)",
        "human_review_status": "pending",
        "samples": samples,
    }
