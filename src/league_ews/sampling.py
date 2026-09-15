"""Strict, executable validation for the registered research sampling frame."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import date
from itertools import pairwise
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

SAMPLING_FRAME_SCHEMA_VERSION = "league-ews-sampling-frame-v1"
SAMPLING_VALIDATION_SCHEMA_VERSION = "league-ews-sampling-frame-validation-v1"

REGISTERED_FRAME_ID = "rifthazard-2026-09-15"
REGISTERED_FREEZE_DATE = date(2026, 9, 15)
REGISTERED_RANDOM_SEED = 20_260_915
REGISTERED_ROUTE_PLATFORMS = (
    ("europe", "EUW1"),
    ("americas", "NA1"),
)
REGISTERED_PUBLIC_PATCHES = tuple(f"26.{minor}" for minor in range(12, 18))
REGISTERED_GAME_PATCHES = tuple(f"16.{minor}" for minor in range(12, 18))
REGISTERED_PATCH_WINDOWS = (
    (date(2026, 6, 10), date(2026, 6, 24)),
    (date(2026, 6, 24), date(2026, 7, 15)),
    (date(2026, 7, 15), date(2026, 7, 29)),
    (date(2026, 7, 29), date(2026, 8, 12)),
    (date(2026, 8, 12), date(2026, 8, 26)),
    (date(2026, 8, 26), date(2026, 9, 10)),
)
REGISTERED_PILOT_TARGET = 5_000
REGISTERED_FINAL_TARGET = 36_000
REGISTERED_FINAL_MATCHES_PER_CELL = 3_000
REGISTERED_FORBIDDEN_EXCLUSIONS = frozenset(
    {"future-event-label", "model-score", "downstream-performance"}
)
REGISTERED_ENDPOINTS = frozenset(
    {
        "league-v4.challenger",
        "league-v4.grandmaster",
        "league-v4.master",
        "summoner-v4.by-summoner-id",
        "match-v5.ids-by-puuid",
        "match-v5.match",
        "match-v5.timeline",
    }
)
REGISTERED_SOURCE_URLS = (
    "https://developer.riotgames.com/apis",
    "https://developer.riotgames.com/docs/lol#routing-values",
    "https://support.riotgames.com/en-us/league-of-legends/gameplay/"
    "patch-schedule-league-of-legends/",
    "https://static-developer.riotgames.com/docs/lol/queues.json",
    "https://static-developer.riotgames.com/docs/lol/maps.json",
    "https://static-developer.riotgames.com/docs/lol/gameModes.json",
    "https://static-developer.riotgames.com/docs/lol/gameTypes.json",
    "https://ddragon.leagueoflegends.com/api/versions.json",
)
MATCH_ID_PATTERN = re.compile(r"^[A-Z0-9]+_[0-9]+$")

Region = Literal["americas", "asia", "europe", "sea"]
SamplingStage = Literal["pilot", "final"]


class FrameSources(BaseModel):
    """Official inputs consulted when the frame was frozen."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reviewed_on: date
    api_reference: str
    routing_values: str
    patch_schedule: str
    queue_ids: str
    maps: str
    game_modes: str
    game_types: str
    data_dragon_versions: str


class RoutePlatform(BaseModel):
    """One platform route paired with its Match-V5 regional route."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    regional_route: Region
    platform_id: str = Field(pattern=r"^[A-Z0-9]+$")


class PatchWindow(BaseModel):
    """One completed patch and its half-open calendar window."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    public_patch: str = Field(pattern=r"^\d+\.\d+$")
    game_version_patch: str = Field(pattern=r"^\d+\.\d+$")
    released_on: date
    closed_on: date


class EligibilityPolicy(BaseModel):
    """Match-detail fields required for the registered study population."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    queue_id: Literal[420]
    map_id: Literal[11]
    game_mode: Literal["CLASSIC"]
    game_type: Literal["MATCHED_GAME"]
    participant_count: Literal[10]
    match_detail_required: Literal[True]
    timeline_required: Literal[True]
    game_version_required: Literal[True]
    game_creation_required: Literal[True]


class CandidateProtocol(BaseModel):
    """Pre-detail candidate discovery and deterministic ordering contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    method: Literal["ranked-ladder-puuid-match-history-v1"]
    ladder_queue: Literal["RANKED_SOLO_5x5"]
    ladder_tiers: tuple[Literal["CHALLENGER", "GRANDMASTER", "MASTER"], ...] = Field(
        min_length=3,
        max_length=3,
    )
    ladder_snapshot: Literal["private-checksum-before-match-id-discovery"]
    candidate_order: Literal["seeded-sha256-within-cell-v1"]
    candidate_hash_material: Literal["decimal-seed-nul-match-id-utf8-v1"]
    deduplicate_match_ids: Literal["globally-before-detail-fetch-and-split"]
    required_endpoints: tuple[
        Literal[
            "league-v4.challenger",
            "league-v4.grandmaster",
            "league-v4.master",
            "summoner-v4.by-summoner-id",
            "match-v5.ids-by-puuid",
            "match-v5.match",
            "match-v5.timeline",
        ],
        ...,
    ] = Field(min_length=7, max_length=7)


class DurationPolicy(BaseModel):
    """Pilot-only inspection rule for setting the eventual remake cutoff."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pilot_minimum_seconds: None
    pilot_rule: Literal["observe-without-duration-exclusion"]
    final_minimum_seconds: None
    final_rule_status: Literal["pending-pilot-freeze"]
    freeze_rule: Literal["set-once-after-pilot-before-final-collection"]


class StageTarget(BaseModel):
    """Target count and cell-allocation rule for one collection stage."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    target_matches: int = Field(gt=0)
    allocation: Literal["balanced-largest-remainder-v1", "equal-per-cell-v1"]
    matches_per_cell: int | None = Field(default=None, gt=0)


class SelectionPolicy(BaseModel):
    """Frozen seed, allocation, and exclusion controls."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sampling_unit: Literal["complete-match"]
    random_seed: int = Field(gt=0)
    cell_order: Literal["patch-then-platform-v1"]
    pilot_use: Literal["infrastructure-and-duration-rule-only"]
    pilot_match_ids_excluded_from_final: Literal[True]
    forbidden_exclusions: tuple[
        Literal["future-event-label", "model-score", "downstream-performance"], ...
    ] = Field(min_length=3, max_length=3)
    pilot: StageTarget
    final: StageTarget


class SplitPolicy(BaseModel):
    """Patch-level split fixed before candidate details are fetched."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    training_patches: tuple[str, ...] = Field(min_length=1)
    calibration_patch: str
    final_test_patch: str


class SamplingFrame(BaseModel):
    """Versioned sampling contract for the RiftHazard study."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["league-ews-sampling-frame-v1"]
    frame_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]+$")
    frozen_on: date
    status: Literal["frozen-before-pilot-details"]
    sources: FrameSources
    route_platforms: tuple[RoutePlatform, ...] = Field(min_length=2, max_length=2)
    patches: tuple[PatchWindow, ...] = Field(min_length=6, max_length=6)
    eligibility: EligibilityPolicy
    candidates: CandidateProtocol
    duration: DurationPolicy
    selection: SelectionPolicy
    split: SplitPolicy


@dataclass(frozen=True)
class SamplingCheck:
    check_id: str
    passed: bool
    message: str


@dataclass(frozen=True)
class SamplingCell:
    regional_route: str
    platform_id: str
    game_version_patch: str
    pilot_target: int
    final_target: int


def _check(check_id: str, passed: bool, success: str, failure: str) -> SamplingCheck:
    return SamplingCheck(
        check_id=check_id,
        passed=passed,
        message=success if passed else failure,
    )


def _safe_validation_error(error: ValidationError) -> str:
    issues = []
    for item in error.errors(include_input=False, include_context=False):
        location = ".".join(str(part) for part in item["loc"]) or "frame"
        issues.append(f"{location}: {item['type']}")
    return "; ".join(issues)


def _load_frame_bytes(path: Path) -> tuple[bytes, SamplingFrame]:
    content = path.read_bytes()
    payload = yaml.safe_load(content)
    if not isinstance(payload, Mapping):
        raise ValueError("sampling frame must contain a mapping")
    return content, SamplingFrame.model_validate(payload)


def load_sampling_frame(path: str | Path) -> SamplingFrame:
    """Load a strictly validated sampling frame or raise a sanitized error."""

    try:
        _, frame = _load_frame_bytes(Path(path))
    except ValidationError as error:
        raise ValueError(
            f"sampling frame schema rejected: {_safe_validation_error(error)}"
        ) from error
    except yaml.YAMLError as error:
        raise ValueError("sampling frame contains invalid YAML") from error
    except OSError as error:
        raise ValueError("sampling frame is missing or unreadable") from error
    except ValueError:
        raise
    return frame


def load_registered_sampling_frame(path: str | Path) -> tuple[SamplingFrame, str]:
    """Load and checksum one frame only if every registered check passes."""

    frame_path = Path(path)
    try:
        content, frame = _load_frame_bytes(frame_path)
    except ValidationError as error:
        raise ValueError(
            f"sampling frame schema rejected: {_safe_validation_error(error)}"
        ) from error
    except yaml.YAMLError as error:
        raise ValueError("sampling frame contains invalid YAML") from error
    except OSError as error:
        raise ValueError("sampling frame is missing or unreadable") from error
    if not all(check.passed for check in _frame_checks(frame)):
        raise ValueError("sampling frame fails the registered contract")
    return frame, hashlib.sha256(content).hexdigest()


def _registered_cells(frame: SamplingFrame) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (route.regional_route, route.platform_id, patch.game_version_patch)
        for patch in frame.patches
        for route in frame.route_platforms
    )


def _balanced_targets(total: int, cell_count: int) -> tuple[int, ...]:
    base, remainder = divmod(total, cell_count)
    return tuple(base + (index < remainder) for index in range(cell_count))


def sampling_cells(frame: SamplingFrame) -> tuple[SamplingCell, ...]:
    """Return deterministic pilot/final targets in registered cell order."""

    coordinates = _registered_cells(frame)
    pilot_targets = _balanced_targets(frame.selection.pilot.target_matches, len(coordinates))
    final_per_cell = frame.selection.final.matches_per_cell or 0
    return tuple(
        SamplingCell(
            regional_route=regional_route,
            platform_id=platform_id,
            game_version_patch=patch,
            pilot_target=pilot_target,
            final_target=final_per_cell,
        )
        for (regional_route, platform_id, patch), pilot_target in zip(
            coordinates,
            pilot_targets,
            strict=True,
        )
    )


def candidate_rank_sha256(frame: SamplingFrame, match_id: str) -> str:
    """Return the frozen outcome-blind rank for one candidate match ID."""

    identifier = match_id.strip()
    if not MATCH_ID_PATTERN.fullmatch(identifier):
        raise ValueError(f"Unsafe or malformed match ID: {identifier!r}")
    material = f"{frame.selection.random_seed}\0{identifier}".encode()
    return hashlib.sha256(material).hexdigest()


def order_candidate_match_ids(
    frame: SamplingFrame,
    match_ids: tuple[str, ...],
) -> tuple[str, ...]:
    """Deduplicate and order candidates using only the frozen seed and ID."""

    identifiers = tuple(
        dict.fromkeys(match_id.strip() for match_id in match_ids if match_id.strip())
    )
    for match_id in identifiers:
        candidate_rank_sha256(frame, match_id)
    return tuple(
        sorted(identifiers, key=lambda match_id: (candidate_rank_sha256(frame, match_id), match_id))
    )


def _patch_series_valid(frame: SamplingFrame) -> bool:
    patches = frame.patches
    public = tuple(patch.public_patch for patch in patches)
    internal = tuple(patch.game_version_patch for patch in patches)
    windows = tuple((patch.released_on, patch.closed_on) for patch in patches)
    windows_chain = all(
        earlier.closed_on == later.released_on for earlier, later in pairwise(patches)
    )
    valid_windows = all(patch.released_on < patch.closed_on <= frame.frozen_on for patch in patches)
    matching_minors = all(
        public_patch.split(".")[1] == game_patch.split(".")[1]
        for public_patch, game_patch in zip(public, internal, strict=True)
    )
    return (
        public == REGISTERED_PUBLIC_PATCHES
        and internal == REGISTERED_GAME_PATCHES
        and windows == REGISTERED_PATCH_WINDOWS
        and windows_chain
        and valid_windows
        and matching_minors
    )


def _official_sources_valid(frame: SamplingFrame) -> bool:
    sources = frame.sources
    urls = (
        sources.api_reference,
        sources.routing_values,
        sources.patch_schedule,
        sources.queue_ids,
        sources.maps,
        sources.game_modes,
        sources.game_types,
        sources.data_dragon_versions,
    )
    return sources.reviewed_on <= frame.frozen_on and urls == REGISTERED_SOURCE_URLS


def _frame_checks(frame: SamplingFrame) -> list[SamplingCheck]:
    route_pairs = tuple(
        (route.regional_route, route.platform_id) for route in frame.route_platforms
    )
    cells = sampling_cells(frame)
    pilot_counts = tuple(cell.pilot_target for cell in cells)
    patch_names = tuple(patch.game_version_patch for patch in frame.patches)
    split_patches = (
        *frame.split.training_patches,
        frame.split.calibration_patch,
        frame.split.final_test_patch,
    )
    final_target_valid = (
        frame.selection.final.target_matches == REGISTERED_FINAL_TARGET
        and frame.selection.final.matches_per_cell == REGISTERED_FINAL_MATCHES_PER_CELL
        and sum(cell.final_target for cell in cells) == REGISTERED_FINAL_TARGET
        and frame.selection.final.allocation == "equal-per-cell-v1"
    )
    return [
        SamplingCheck(
            check_id="frame-schema",
            passed=True,
            message=f"Sampling frame conforms to {SAMPLING_FRAME_SCHEMA_VERSION}",
        ),
        _check(
            "freeze-stage",
            frame.frame_id == REGISTERED_FRAME_ID
            and frame.frozen_on == REGISTERED_FREEZE_DATE
            and frame.sources.reviewed_on == frame.frozen_on,
            "Frame and source review were frozen before pilot match details",
            "Frame freeze or source-review date differs from the registered pre-pilot freeze",
        ),
        _check(
            "official-sources",
            _official_sources_valid(frame),
            "Routing, patch, queue, map, mode and type inputs cite official Riot sources",
            "Sampling inputs must cite reviewed official Riot sources",
        ),
        _check(
            "route-platforms",
            route_pairs == REGISTERED_ROUTE_PLATFORMS and len(set(route_pairs)) == len(route_pairs),
            "EUW1/europe and NA1/americas are the two frozen route-platform pairs",
            "Route-platform pairs differ from the two registered pairs or are duplicated",
        ),
        _check(
            "patch-series",
            _patch_series_valid(frame),
            "Six consecutive completed patches 16.12 through 16.17 are frozen",
            "Patch identifiers or completed half-open windows differ from the registered series",
        ),
        _check(
            "eligibility",
            True,
            "Eligibility is queue 420, map 11, CLASSIC, MATCHED_GAME and ten participants",
            "Eligibility differs from the registered Ranked Solo/Duo population",
        ),
        _check(
            "candidate-protocol",
            set(frame.candidates.ladder_tiers) == {"CHALLENGER", "GRANDMASTER", "MASTER"}
            and len(set(frame.candidates.ladder_tiers)) == 3
            and set(frame.candidates.required_endpoints) == REGISTERED_ENDPOINTS
            and len(set(frame.candidates.required_endpoints)) == len(REGISTERED_ENDPOINTS),
            "Candidate discovery, private snapshot and endpoint scope are fully specified",
            "Candidate discovery tiers or endpoint scope are incomplete or duplicated",
        ),
        _check(
            "selection-controls",
            set(frame.selection.forbidden_exclusions) == REGISTERED_FORBIDDEN_EXCLUSIONS
            and len(set(frame.selection.forbidden_exclusions))
            == len(REGISTERED_FORBIDDEN_EXCLUSIONS)
            and frame.selection.random_seed == REGISTERED_RANDOM_SEED
            and frame.selection.pilot_match_ids_excluded_from_final,
            "Selection is seeded, deduplicated, pilot-isolated and outcome-blind",
            "Selection controls do not match the registered anti-selection-bias rules",
        ),
        _check(
            "pilot-allocation",
            frame.selection.pilot.target_matches == REGISTERED_PILOT_TARGET
            and frame.selection.pilot.matches_per_cell is None
            and frame.selection.pilot.allocation == "balanced-largest-remainder-v1"
            and sum(pilot_counts) == REGISTERED_PILOT_TARGET
            and max(pilot_counts) - min(pilot_counts) <= 1,
            "The 5,000-match pilot is deterministically balanced across all 12 cells",
            "Pilot size or largest-remainder allocation differs from the registered target",
        ),
        _check(
            "final-allocation",
            final_target_valid,
            "The final target is exactly 3,000 matches in each cell (36,000 total)",
            "Final target or equal per-cell allocation differs from the registered target",
        ),
        _check(
            "duration-freeze",
            frame.duration.pilot_minimum_seconds is None
            and frame.duration.final_minimum_seconds is None,
            "No duration cutoff is set before the pilot; one final cutoff must be frozen later",
            "A duration cutoff was set before the registered pilot inspection",
        ),
        _check(
            "future-patch-split",
            split_patches == patch_names
            and len(set(split_patches)) == len(split_patches)
            and frame.split.training_patches == patch_names[:-2]
            and frame.split.calibration_patch == patch_names[-2]
            and frame.split.final_test_patch == patch_names[-1],
            "Patches 16.12-16.15 train, 16.16 calibrates and 16.17 is untouched test",
            "Patch partitions differ from the registered future-patch split",
        ),
    ]


def validate_sampling_frame(path: str | Path) -> dict[str, object]:
    """Validate the frozen frame without making an API request."""

    frame_path = Path(path)
    try:
        content, frame = _load_frame_bytes(frame_path)
    except (OSError, ValueError, yaml.YAMLError, ValidationError) as error:
        if isinstance(error, ValidationError):
            reason = _safe_validation_error(error)
        elif isinstance(error, yaml.YAMLError):
            reason = "invalid YAML"
        elif isinstance(error, OSError):
            reason = "missing or unreadable file"
        else:
            reason = str(error)
        check = SamplingCheck(
            check_id="frame-schema",
            passed=False,
            message=f"Sampling frame rejected: {reason}",
        )
        return {
            "schema_version": SAMPLING_VALIDATION_SCHEMA_VERSION,
            "frame_id": None,
            "frame_sha256": None,
            "passed": False,
            "checks": [asdict(check)],
            "summary": None,
        }

    checks = _frame_checks(frame)
    cells = sampling_cells(frame)
    return {
        "schema_version": SAMPLING_VALIDATION_SCHEMA_VERSION,
        "frame_id": frame.frame_id,
        "frame_sha256": hashlib.sha256(content).hexdigest(),
        "passed": all(check.passed for check in checks),
        "checks": [asdict(check) for check in checks],
        "summary": {
            "regional_routes": [route.regional_route for route in frame.route_platforms],
            "platform_ids": [route.platform_id for route in frame.route_platforms],
            "game_version_patches": [patch.game_version_patch for patch in frame.patches],
            "route_patch_cells": len(cells),
            "pilot_target_matches": sum(cell.pilot_target for cell in cells),
            "final_target_matches": sum(cell.final_target for cell in cells),
            "duration_cutoff_status": frame.duration.final_rule_status,
            "required_endpoints": sorted(frame.candidates.required_endpoints),
            "cells": [asdict(cell) for cell in cells],
        },
    }


def sampling_coverage(
    frame: SamplingFrame,
    observed: Mapping[tuple[str, str, str], int],
    *,
    stage: SamplingStage,
) -> dict[str, object]:
    """Compare observed valid bundle counts with exact registered cell targets."""

    if stage not in {"pilot", "final"}:
        raise ValueError(f"Unsupported sampling stage: {stage}")
    if any(count < 0 for count in observed.values()):
        raise ValueError("Observed sampling-cell counts cannot be negative")

    cells = sampling_cells(frame)
    target_by_cell = {
        (cell.regional_route, cell.platform_id, cell.game_version_patch): (
            cell.pilot_target if stage == "pilot" else cell.final_target
        )
        for cell in cells
    }
    observed_counts = Counter(observed)
    expected_keys = set(target_by_cell)
    observed_keys = {key for key, count in observed_counts.items() if count > 0}
    unexpected = observed_keys - expected_keys
    exact_counts = not unexpected and all(
        observed_counts[key] == target for key, target in target_by_cell.items()
    )
    represented = sum(observed_counts[key] > 0 for key in expected_keys)
    target_total = sum(target_by_cell.values())
    observed_in_frame = sum(observed_counts[key] for key in expected_keys)
    return {
        "stage": stage,
        "passed": exact_counts,
        "expected_cells": len(expected_keys),
        "represented_cells": represented,
        "unexpected_cells": len(unexpected),
        "target_matches": target_total,
        "observed_in_frame_matches": observed_in_frame,
        "exact_cell_targets_met": exact_counts,
    }
