"""Outcome-blind duration diagnostics for the checksum-bound registered pilot."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from league_ews.duration_rule import (
    CANDIDATE_MINIMUM_SECONDS,
    DURATION_ANALYSIS_SCHEMA_VERSION,
)
from league_ews.pilot_collection import PilotCollectionBinding
from league_ews.raw_validation import RawCollectionManifest
from league_ews.sampling import load_registered_sampling_frame, sampling_cells

PERCENTILES = (1, 5, 10, 25, 50, 75, 90, 95, 99)


@dataclass(frozen=True)
class DurationObservation:
    """Identifier-free fields permitted in the post-pilot duration decision."""

    regional_route: str
    platform_id: str
    game_version_patch: str
    duration_seconds: int
    early_surrender: bool
    surrender: bool
    early_surrender_flag_complete: bool
    surrender_flag_complete: bool


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _object(content: bytes, *, name: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(f"{name} contains invalid JSON") from error
    if not isinstance(payload, Mapping):
        raise ValueError(f"{name} must contain a JSON object")
    return payload


def _patch(game_version: str) -> str:
    parts = game_version.split(".")
    if len(parts) < 2:
        raise ValueError("Pilot manifest contains an invalid game version")
    return ".".join(parts[:2])


def _duration_seconds(info: Mapping[str, Any]) -> int:
    value = info.get("gameDuration")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
        or int(value) != value
    ):
        raise ValueError("Pilot match detail contains an invalid gameDuration")
    return int(value)


def _participant_flag(
    participants: object,
    field: str,
) -> tuple[bool, bool]:
    if not isinstance(participants, list) or len(participants) != 10:
        raise ValueError("Pilot match detail must contain exactly ten participants")
    values: list[bool] = []
    complete = True
    for participant in participants:
        if not isinstance(participant, Mapping):
            raise ValueError("Pilot match detail contains a malformed participant")
        value = participant.get(field)
        if not isinstance(value, bool):
            complete = False
            continue
        values.append(value)
    return any(values), complete


def _nearest_rank(values: Sequence[int], percentile: int) -> int:
    ordered = sorted(values)
    index = max(0, math.ceil(percentile / 100 * len(ordered)) - 1)
    return ordered[index]


def _duration_summary(observations: Sequence[DurationObservation]) -> dict[str, object]:
    durations = [observation.duration_seconds for observation in observations]
    if not durations:
        raise ValueError("Duration analysis requires at least one pilot match")
    return {
        "matches": len(observations),
        "minimum_seconds": min(durations),
        "mean_seconds": round(sum(durations) / len(durations), 3),
        "percentiles_seconds": {
            f"p{percentile:02d}": _nearest_rank(durations, percentile) for percentile in PERCENTILES
        },
        "maximum_seconds": max(durations),
        "early_surrender_matches": sum(observation.early_surrender for observation in observations),
        "surrender_matches": sum(observation.surrender for observation in observations),
        "early_surrender_flag_complete_matches": sum(
            observation.early_surrender_flag_complete for observation in observations
        ),
        "surrender_flag_complete_matches": sum(
            observation.surrender_flag_complete for observation in observations
        ),
    }


def _threshold_summary(
    observations: Sequence[DurationObservation],
) -> list[dict[str, int | float]]:
    total = len(observations)
    summaries: list[dict[str, int | float]] = []
    for minimum in CANDIDATE_MINIMUM_SECONDS:
        excluded = [
            observation for observation in observations if observation.duration_seconds < minimum
        ]
        excluded_early = sum(observation.early_surrender for observation in excluded)
        summaries.append(
            {
                "minimum_seconds": minimum,
                "excluded_matches": len(excluded),
                "excluded_fraction": round(len(excluded) / total, 8),
                "excluded_early_surrender_matches": excluded_early,
                "excluded_other_matches": len(excluded) - excluded_early,
                "retained_matches": total - len(excluded),
            }
        )
    return summaries


def _processed_match_ids(content: bytes) -> tuple[str, ...]:
    manifest = _object(content, name="processing manifest")
    if (
        manifest.get("schema_version") != "league-ews-processing-manifest-v1"
        or manifest.get("contains_player_identifiers") is not False
    ):
        raise ValueError("Processing manifest does not satisfy the pilot contract")
    records = manifest.get("matches")
    if not isinstance(records, list):
        raise ValueError("Processing manifest has no match inventory")
    identifiers: list[str] = []
    for record in records:
        if not isinstance(record, Mapping) or not isinstance(record.get("match_id"), str):
            raise ValueError("Processing manifest contains an invalid match inventory")
        identifiers.append(record["match_id"])
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Processing manifest contains duplicate matches")
    return tuple(identifiers)


def analyze_pilot_duration(
    raw_root: str | Path,
    processed_root: str | Path,
    sampling_frame: str | Path,
) -> dict[str, object]:
    """Describe the pilot duration/remake distribution without event or model inputs."""

    raw = Path(raw_root)
    processed = Path(processed_root)
    frame, frame_sha256 = load_registered_sampling_frame(sampling_frame)

    raw_manifest_content = (raw / "collection-manifest.json").read_bytes()
    raw_manifest_sha256 = _sha256(raw_manifest_content)
    raw_manifest = RawCollectionManifest.model_validate_json(raw_manifest_content)

    binding_content = (raw / "selection-binding.json").read_bytes()
    binding = PilotCollectionBinding.model_validate_json(binding_content)
    if (
        not binding.complete
        or binding.frame_id != frame.frame_id
        or binding.frame_sha256 != frame_sha256
        or binding.collection_manifest_sha256 != raw_manifest_sha256
    ):
        raise ValueError("Pilot collection binding does not match the registered inputs")

    processed_manifest_content = (processed / "processing-manifest.json").read_bytes()
    processed_ids = _processed_match_ids(processed_manifest_content)
    raw_ids = tuple(record.match_id for record in raw_manifest.available)
    if (
        len(set(raw_ids)) != len(raw_ids)
        or set(raw_ids) != set(processed_ids)
        or len(raw_ids) != binding.expected_selected_match_ids
    ):
        raise ValueError("Raw and processed pilot inventories do not match the frozen selection")

    registered_cells = {
        (cell.regional_route, cell.platform_id, cell.game_version_patch)
        for cell in sampling_cells(frame)
    }
    observations: list[DurationObservation] = []
    for record in raw_manifest.available:
        match_content = (raw / "matches" / f"{record.match_id}.json").read_bytes()
        if _sha256(match_content) != record.match_sha256:
            raise ValueError("A pilot match detail checksum does not match its manifest")
        match_payload = _object(match_content, name="pilot match detail")
        info = match_payload.get("info")
        metadata = match_payload.get("metadata")
        if not isinstance(info, Mapping) or not isinstance(metadata, Mapping):
            raise ValueError("Pilot match detail is missing metadata or info")
        if metadata.get("matchId") != record.match_id:
            raise ValueError("Pilot match identity does not match its manifest")

        platform_id = record.match_id.split("_", maxsplit=1)[0]
        cell = (record.regional_route, platform_id, _patch(record.game_version))
        if cell not in registered_cells:
            raise ValueError("Pilot match belongs to an unregistered route-patch cell")
        participants = info.get("participants")
        early_surrender, early_complete = _participant_flag(
            participants,
            "gameEndedInEarlySurrender",
        )
        surrender, surrender_complete = _participant_flag(
            participants,
            "gameEndedInSurrender",
        )
        observations.append(
            DurationObservation(
                regional_route=cell[0],
                platform_id=cell[1],
                game_version_patch=cell[2],
                duration_seconds=_duration_seconds(info),
                early_surrender=early_surrender,
                surrender=surrender,
                early_surrender_flag_complete=early_complete,
                surrender_flag_complete=surrender_complete,
            )
        )

    by_cell: defaultdict[tuple[str, str, str], list[DurationObservation]] = defaultdict(list)
    for observation in observations:
        by_cell[
            (
                observation.regional_route,
                observation.platform_id,
                observation.game_version_patch,
            )
        ].append(observation)

    cells: list[dict[str, object]] = []
    for registered in sampling_cells(frame):
        key = (
            registered.regional_route,
            registered.platform_id,
            registered.game_version_patch,
        )
        cell_observations = by_cell.get(key, [])
        if not cell_observations:
            continue
        cells.append(
            {
                "regional_route": key[0],
                "platform_id": key[1],
                "game_version_patch": key[2],
                "duration": _duration_summary(cell_observations),
                "candidate_minimums": _threshold_summary(cell_observations),
            }
        )

    return {
        "schema_version": DURATION_ANALYSIS_SCHEMA_VERSION,
        "frame_id": frame.frame_id,
        "bindings": {
            "frame_sha256": frame_sha256,
            "collection_manifest_sha256": raw_manifest_sha256,
            "selection_binding_sha256": _sha256(binding_content),
            "selected_pool_sha256": binding.selected_pool_sha256,
            "processing_manifest_sha256": _sha256(processed_manifest_content),
        },
        "input_policy": {
            "fields_used": [
                "info.gameDuration",
                "info.participants.gameEndedInEarlySurrender",
                "info.participants.gameEndedInSurrender",
            ],
            "event_labels_used": False,
            "model_outputs_used": False,
            "winner_used": False,
        },
        "duration": _duration_summary(observations),
        "candidate_minimums": _threshold_summary(observations),
        "represented_cells": len(cells),
        "cells": cells,
        "identifiers_in_summary": False,
        "redistribution": "not-authorized",
    }
