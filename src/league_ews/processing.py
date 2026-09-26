"""Raw-to-normalized research-v2 processing with de-identified outputs."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from league_ews.labels import extract_event_index, future_event_labels
from league_ews.timeline import normalise_match_timeline


@dataclass(frozen=True)
class ProcessedMatch:
    match_id: str
    game_version: str
    observations: int
    baron_events: int
    dragon_events: int
    teamfight_events: int
    sha256: str


def _read_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected a JSON object in {path.name}")
    return payload


def _serialized(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    partial.write_bytes(content)
    partial.replace(path)


def _existing_record(path: Path, expected_match_id: str) -> ProcessedMatch:
    content = path.read_bytes()
    payload = json.loads(content)
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != "league-ews-processed-match-v1"
    ):
        raise ValueError(f"Invalid existing processed match: {path.name}")
    timeline = payload.get("timeline")
    events = payload.get("event_index")
    labels = payload.get("labels")
    if (
        not isinstance(timeline, dict)
        or not isinstance(events, dict)
        or not isinstance(labels, list)
    ):
        raise ValueError(f"Invalid existing processed match: {path.name}")
    observations = timeline.get("observations")
    game_version = timeline.get("game_version")
    if (
        timeline.get("match_id") != expected_match_id
        or not isinstance(game_version, str)
        or not isinstance(observations, list)
        or len(observations) != len(labels)
    ):
        raise ValueError(f"Existing processed match identity or labels differ: {path.name}")
    counts: dict[str, int] = {}
    for event_type in ("baron", "dragon", "teamfight"):
        values = events.get(f"{event_type}_ms")
        if not isinstance(values, list) or not all(isinstance(value, int) for value in values):
            raise ValueError(f"Invalid existing event index: {path.name}")
        counts[event_type] = len(values)
    return ProcessedMatch(
        match_id=expected_match_id,
        game_version=game_version,
        observations=len(observations),
        baron_events=counts["baron"],
        dragon_events=counts["dragon"],
        teamfight_events=counts["teamfight"],
        sha256=hashlib.sha256(content).hexdigest(),
    )


def process_raw_collection(
    raw_root: str | Path,
    *,
    output_root: str | Path,
    max_new_matches: int | None = None,
) -> dict[str, object]:
    """Resume a contiguous processed prefix and create exact future labels."""

    if max_new_matches is not None and max_new_matches < 1:
        raise ValueError("max_new_matches must be positive")

    raw = Path(raw_root)
    output = Path(output_root)
    match_paths = sorted((raw / "matches").glob("*.json"))
    if not match_paths:
        raise ValueError("Raw collection contains no match payloads")

    processed_dir = output / "matches"
    existing_paths = sorted(processed_dir.glob("*.json"))
    if existing_paths != [processed_dir / path.name for path in match_paths[: len(existing_paths)]]:
        raise ValueError("Existing processed files are not a contiguous prefix of raw matches")
    partials = list(processed_dir.glob("*.partial"))
    if partials:
        raise ValueError("Unfinished processed files require inspection before resuming")
    if len(existing_paths) < len(match_paths) and (output / "processing-manifest.json").exists():
        raise ValueError("A final processing manifest exists for an incomplete collection")
    records = [_existing_record(path, path.stem) for path in existing_paths]
    remaining = match_paths[len(existing_paths) :]
    work = remaining if max_new_matches is None else remaining[:max_new_matches]
    for match_path in work:
        timeline_path = raw / "timelines" / match_path.name
        if not timeline_path.is_file():
            raise FileNotFoundError(f"Missing timeline pair for {match_path.stem}")
        normalized = normalise_match_timeline(
            _read_object(match_path),
            _read_object(timeline_path),
        )
        events = extract_event_index(normalized)
        labels = future_event_labels(
            tuple(observation.timestamp_ms for observation in normalized.observations),
            events,
        )
        rows = [
            {
                str(column): value.item() if hasattr(value, "item") else value
                for column, value in row.items()
            }
            for row in labels.to_dict(orient="records")
        ]
        payload: dict[str, Any] = {
            "schema_version": "league-ews-processed-match-v1",
            "timeline": normalized.model_dump(mode="json"),
            "event_index": asdict(events),
            "labels": rows,
        }
        content = _serialized(payload)
        destination = output / "matches" / match_path.name
        _atomic_write(destination, content)
        records.append(
            ProcessedMatch(
                match_id=normalized.match_id,
                game_version=normalized.game_version,
                observations=len(normalized.observations),
                baron_events=len(events.baron_ms),
                dragon_events=len(events.dragon_ms),
                teamfight_events=len(events.teamfight_ms),
                sha256=hashlib.sha256(content).hexdigest(),
            )
        )

    manifest: dict[str, object] = {
        "schema_version": "league-ews-processing-manifest-v1",
        "normalizer": "riot-match-v5-normalized-v1",
        "label_policy": "exact-future-events-v1",
        "matches": [asdict(record) for record in records],
        "contains_player_identifiers": False,
    }
    complete = len(records) == len(match_paths)
    if complete:
        _atomic_write(output / "processing-manifest.json", _serialized(manifest))
    manifest["complete"] = complete
    manifest["new_matches"] = len(work)
    manifest["expected_matches"] = len(match_paths)
    return manifest
