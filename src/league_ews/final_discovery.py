"""Checksum-bound candidate discovery for the pilot-isolated final sample."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal, cast

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from league_ews.authority import DISCOVERY_ENDPOINTS, collection_preflight
from league_ews.discovery import (
    DiscoveryOutputPolicy,
    HistoryPage,
    LadderDiscoveryPolicy,
    LadderSnapshot,
    MatchHistoryPolicy,
    PlatformDiscoveryFetcher,
    RegionalDiscoveryFetcher,
    SamplingFrameBinding,
    SnapshotMember,
    _aggregate_digest,
    _atomic_write,
    _canonical_json,
    _history_path,
    _load_or_create_snapshot,
    _load_or_fetch_history,
    _ordered_members,
    _player_key_sha256,
    _resolution_path,
    _resolve_player,
    _safe_validation_error,
    _sha256,
)
from league_ews.duration_rule import validate_duration_rule
from league_ews.pilot_collection import FrozenPilotSelection, load_frozen_pilot_selection
from league_ews.sampling import (
    MATCH_ID_PATTERN,
    SamplingFrame,
    load_registered_sampling_frame,
    order_candidate_match_ids,
    sampling_cells,
)

FINAL_DISCOVERY_PLAN_SCHEMA_VERSION = "league-ews-final-discovery-plan-v1"
FINAL_DISCOVERY_PLAN_VALIDATION_SCHEMA_VERSION = "league-ews-final-discovery-plan-validation-v1"
FINAL_DISCOVERY_PREFLIGHT_SCHEMA_VERSION = "riot-final-candidate-discovery-preflight-v1"
FINAL_CANDIDATE_POOL_SCHEMA_VERSION = "riot-final-candidate-pool-v1"
FINAL_DISCOVERY_MANIFEST_SCHEMA_VERSION = "riot-final-candidate-discovery-manifest-v1"
FINAL_CANDIDATE_POOL_VALIDATION_SCHEMA_VERSION = "riot-final-candidate-pool-validation-v1"

REGISTERED_PLAN_ID = "rifthazard-final-discovery-2026-09-20"
REGISTERED_FROZEN_ON = date(2026, 9, 20)
REGISTERED_FRAME_ID = "rifthazard-2026-09-15"
REGISTERED_FRAME_SHA256 = "2355ec26182aa6862e8a110ff94f0ab402e9a4e77c0a52a0a5c81f1892033f6b"
REGISTERED_DURATION_RULE_ID = "rifthazard-duration-2026-09-20"
REGISTERED_DURATION_RULE_SHA256 = "b957947597e9fa64dec89bcd2b762ca9c37f4d3941ff26be02e59c09cf8856fe"
REGISTERED_DURATION_ANALYSIS_SHA256 = (
    "3cab09e4f305bb67b089e28a35276cee1fe67add9584baef6552d78b7a12c9c5"
)
REGISTERED_FINAL_MINIMUM_SECONDS = 180
REGISTERED_PILOT_PLAN_ID = "rifthazard-pilot-discovery-2026-09-15"
REGISTERED_PILOT_PLAN_SHA256 = "f2d1fb7460b5bb9466e3ee9adc9aa66cfea252845a1d3f7bf41cf20440a52c85"
REGISTERED_PILOT_DISCOVERY_MANIFEST_SHA256 = (
    "bf82edbdb062ec3a65452023d021af09a3eac7ca652f36037c7e911c84377cc8"
)
REGISTERED_PILOT_CANDIDATE_POOL_SHA256 = (
    "c3a2688cc72ffc77596271dbf9d61e7abf91e24521c5276c0511af0a5a6be111"
)
REGISTERED_PILOT_SELECTED_POOL_SHA256 = (
    "05f566c3c36d5402a9f2ef26bd3c63dae33737bd550dae0c735dbe5f87a656eb"
)
REGISTERED_PILOT_MATCHES = 5_000
REGISTERED_WAVE_SIZE = 32
REGISTERED_MAX_PLAYERS = 512
REGISTERED_HISTORY_COUNT = 100
REGISTERED_CANDIDATE_MULTIPLIER = 2
SHA256_PATTERN = r"^[0-9a-f]{64}$"


class DurationRuleBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: Literal["rifthazard-duration-2026-09-20"]
    rule_sha256: str = Field(pattern=SHA256_PATTERN)
    analysis_sha256: str = Field(pattern=SHA256_PATTERN)
    final_minimum_seconds: int = Field(gt=0)


class PilotSelectionBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    discovery_plan_id: Literal["rifthazard-pilot-discovery-2026-09-15"]
    discovery_plan_sha256: str = Field(pattern=SHA256_PATTERN)
    discovery_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    selected_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    selected_match_ids: int = Field(gt=0)


class FinalStoppingPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    stage: Literal["final"]
    candidate_multiplier_per_cell: int = Field(gt=1)
    rule: Literal["first-complete-balanced-wave-v1"]
    exclude_pilot_match_ids_before_stop: Literal[True]
    inspect_match_details_before_stop: Literal[False]
    inspect_labels_before_stop: Literal[False]


class FinalDiscoveryPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["league-ews-final-discovery-plan-v1"]
    plan_id: str
    frozen_on: date
    status: Literal["frozen-after-duration-rule-before-final-details"]
    sampling_frame: SamplingFrameBinding
    duration_rule: DurationRuleBinding
    pilot_selection: PilotSelectionBinding
    ladder: LadderDiscoveryPolicy
    history: MatchHistoryPolicy
    stopping: FinalStoppingPolicy
    outputs: DiscoveryOutputPolicy


class FinalCandidatePoolCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    regional_route: Literal["americas", "asia", "europe", "sea"]
    platform_id: str = Field(pattern=r"^[A-Z0-9]+$")
    game_version_patch: str = Field(pattern=r"^\d+\.\d+$")
    minimum_candidates: int = Field(gt=0)
    candidate_count: int = Field(ge=0)
    excluded_pilot_matches_discovered: int = Field(ge=0)
    minimum_met: bool
    match_ids: tuple[str, ...]


class FinalCandidatePool(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-final-candidate-pool-v1"]
    stage: Literal["final"]
    frame_id: str
    frame_sha256: str = Field(pattern=SHA256_PATTERN)
    plan_id: str
    plan_sha256: str = Field(pattern=SHA256_PATTERN)
    duration_rule_sha256: str = Field(pattern=SHA256_PATTERN)
    pilot_selected_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    snapshot_sha256: str = Field(pattern=SHA256_PATTERN)
    complete: bool
    globally_deduplicated: bool
    excluded_pilot_match_ids_discovered: int = Field(ge=0)
    cells: tuple[FinalCandidatePoolCell, ...]
    contains_match_identifiers: Literal[True]
    contains_player_identifiers: Literal[False]
    redistribution: Literal["not-authorized"]


class FinalCandidateWindowSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    regional_route: Literal["americas", "asia", "europe", "sea"]
    platform_id: str = Field(pattern=r"^[A-Z0-9]+$")
    game_version_patch: str = Field(pattern=r"^\d+\.\d+$")
    minimum_candidates: int = Field(gt=0)
    candidate_count: int = Field(ge=0)
    excluded_pilot_matches_discovered: int = Field(ge=0)
    minimum_met: bool


class FinalDiscoveryManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-final-candidate-discovery-manifest-v1"]
    completed_at: datetime
    complete: bool
    frame_id: str
    frame_sha256: str = Field(pattern=SHA256_PATTERN)
    plan_id: str
    plan_sha256: str = Field(pattern=SHA256_PATTERN)
    duration_rule_sha256: str = Field(pattern=SHA256_PATTERN)
    duration_analysis_sha256: str = Field(pattern=SHA256_PATTERN)
    pilot_selected_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    ladder_snapshot_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    resolution_cache_sha256: str = Field(pattern=SHA256_PATTERN)
    history_cache_sha256: str = Field(pattern=SHA256_PATTERN)
    players_processed_per_platform: int = Field(gt=0)
    balanced_waves_completed: int = Field(gt=0)
    resolution_files: int = Field(gt=0)
    history_page_files: int = Field(gt=0)
    candidate_match_ids: int = Field(gt=0)
    excluded_pilot_match_ids_discovered: int = Field(ge=0)
    candidate_windows: tuple[FinalCandidateWindowSummary, ...]
    contains_player_identifiers_in_private_files: Literal[True]
    identifiers_in_summary: Literal[False]
    redistribution: Literal["not-authorized"]


@dataclass(frozen=True)
class FinalDiscoveryCheck:
    check_id: str
    passed: bool
    message: str


@dataclass(frozen=True)
class FinalDiscoveryContext:
    frame: SamplingFrame
    frame_sha256: str
    plan: FinalDiscoveryPlan
    plan_sha256: str
    pilot: FrozenPilotSelection


def _check(check_id: str, passed: bool, success: str, failure: str) -> FinalDiscoveryCheck:
    return FinalDiscoveryCheck(check_id, passed, success if passed else failure)


def _load_plan_bytes(path: Path) -> tuple[bytes, FinalDiscoveryPlan]:
    content = path.read_bytes()
    payload = yaml.safe_load(content)
    if not isinstance(payload, Mapping):
        raise ValueError("final discovery plan must contain a mapping")
    return content, FinalDiscoveryPlan.model_validate(payload)


def _plan_checks(
    plan: FinalDiscoveryPlan,
    *,
    frame: SamplingFrame,
    frame_sha256: str,
) -> list[FinalDiscoveryCheck]:
    duration = plan.duration_rule
    pilot = plan.pilot_selection
    return [
        FinalDiscoveryCheck(
            "plan-schema",
            True,
            f"Final discovery plan conforms to {FINAL_DISCOVERY_PLAN_SCHEMA_VERSION}",
        ),
        _check(
            "freeze-stage",
            plan.plan_id == REGISTERED_PLAN_ID
            and plan.frozen_on == REGISTERED_FROZEN_ON
            and plan.frozen_on > frame.frozen_on,
            "Final discovery was frozen after the pilot decision and before final details",
            "Final discovery identity or freeze stage differs from the registered plan",
        ),
        _check(
            "sampling-frame-binding",
            plan.sampling_frame.frame_id == frame.frame_id == REGISTERED_FRAME_ID
            and plan.sampling_frame.sha256 == frame_sha256 == REGISTERED_FRAME_SHA256,
            "Final discovery is bound to the immutable sampling frame",
            "Final discovery does not match the registered sampling frame",
        ),
        _check(
            "duration-rule-binding",
            duration.rule_id == REGISTERED_DURATION_RULE_ID
            and duration.rule_sha256 == REGISTERED_DURATION_RULE_SHA256
            and duration.analysis_sha256 == REGISTERED_DURATION_ANALYSIS_SHA256
            and duration.final_minimum_seconds == REGISTERED_FINAL_MINIMUM_SECONDS,
            "Final discovery is bound to the frozen 180-second duration rule",
            "Duration-rule identity or checksum differs from the registered freeze",
        ),
        _check(
            "pilot-selection-binding",
            pilot.discovery_plan_id == REGISTERED_PILOT_PLAN_ID
            and pilot.discovery_plan_sha256 == REGISTERED_PILOT_PLAN_SHA256
            and pilot.discovery_manifest_sha256 == REGISTERED_PILOT_DISCOVERY_MANIFEST_SHA256
            and pilot.candidate_pool_sha256 == REGISTERED_PILOT_CANDIDATE_POOL_SHA256
            and pilot.selected_pool_sha256 == REGISTERED_PILOT_SELECTED_POOL_SHA256
            and pilot.selected_match_ids == REGISTERED_PILOT_MATCHES,
            "All 5,000 frozen pilot identities are checksum-bound for exclusion",
            "Pilot-selection provenance differs from the registered final plan",
        ),
        _check(
            "balanced-player-waves",
            plan.ladder.wave_size_per_platform == REGISTERED_WAVE_SIZE
            and plan.ladder.max_players_per_platform == REGISTERED_MAX_PLAYERS
            and plan.ladder.max_players_per_platform % plan.ladder.wave_size_per_platform == 0,
            "Final discovery uses equal deterministic 32-player waves up to 512 players",
            "Final player-wave limits differ from the registered plan",
        ),
        _check(
            "bounded-history",
            plan.history.queue_id == frame.eligibility.queue_id
            and plan.history.count_per_player_window == REGISTERED_HISTORY_COUNT,
            "Every final history query is queue-bound and capped at 100 IDs",
            "Final history lookup differs from the registered queue or page cap",
        ),
        _check(
            "outcome-blind-stop",
            plan.stopping.candidate_multiplier_per_cell == REGISTERED_CANDIDATE_MULTIPLIER
            and plan.stopping.exclude_pilot_match_ids_before_stop
            and not plan.stopping.inspect_match_details_before_stop
            and not plan.stopping.inspect_labels_before_stop,
            "Discovery stops at 6,000 pilot-excluded IDs per cell without details or labels",
            "Final stopping could retain pilot IDs or depend on details or labels",
        ),
    ]


def load_registered_final_discovery_plan(
    path: str | Path,
    *,
    frame: SamplingFrame,
    frame_sha256: str,
) -> tuple[FinalDiscoveryPlan, str]:
    """Load the final plan only when every public freeze check passes."""

    try:
        content, plan = _load_plan_bytes(Path(path))
    except ValidationError as error:
        raise ValueError(
            f"final discovery plan schema rejected: {_safe_validation_error(error)}"
        ) from error
    except yaml.YAMLError as error:
        raise ValueError("final discovery plan contains invalid YAML") from error
    except OSError as error:
        raise ValueError("final discovery plan is missing or unreadable") from error
    if not all(
        check.passed for check in _plan_checks(plan, frame=frame, frame_sha256=frame_sha256)
    ):
        raise ValueError("final discovery plan fails the registered contract")
    return plan, hashlib.sha256(content).hexdigest()


def validate_final_discovery_plan(
    plan_path: str | Path,
    sampling_frame_path: str | Path,
) -> dict[str, object]:
    """Validate the public final-discovery plan without private data or network access."""

    try:
        frame, frame_sha256 = load_registered_sampling_frame(sampling_frame_path)
        content, plan = _load_plan_bytes(Path(plan_path))
        checks = _plan_checks(plan, frame=frame, frame_sha256=frame_sha256)
    except (OSError, ValueError, yaml.YAMLError, ValidationError) as error:
        if isinstance(error, ValidationError):
            reason = _safe_validation_error(error)
        elif isinstance(error, yaml.YAMLError):
            reason = "invalid YAML"
        elif isinstance(error, OSError):
            reason = "missing or unreadable file"
        else:
            reason = str(error)
        check = FinalDiscoveryCheck(
            "plan-schema",
            False,
            f"Final discovery plan rejected: {reason}",
        )
        return {
            "schema_version": FINAL_DISCOVERY_PLAN_VALIDATION_SCHEMA_VERSION,
            "plan_id": None,
            "plan_sha256": None,
            "passed": False,
            "checks": [asdict(check)],
            "summary": None,
        }

    cells = sampling_cells(frame)
    return {
        "schema_version": FINAL_DISCOVERY_PLAN_VALIDATION_SCHEMA_VERSION,
        "plan_id": plan.plan_id,
        "plan_sha256": hashlib.sha256(content).hexdigest(),
        "sampling_frame_sha256": frame_sha256,
        "passed": all(check.passed for check in checks),
        "checks": [asdict(check) for check in checks],
        "summary": {
            "wave_size_per_platform": plan.ladder.wave_size_per_platform,
            "max_players_per_platform": plan.ladder.max_players_per_platform,
            "history_requests_per_wave": (
                plan.ladder.wave_size_per_platform * len(frame.route_platforms) * len(frame.patches)
            ),
            "minimum_candidates_per_cell": [
                {
                    "regional_route": cell.regional_route,
                    "platform_id": cell.platform_id,
                    "game_version_patch": cell.game_version_patch,
                    "minimum_candidates": (
                        cell.final_target * plan.stopping.candidate_multiplier_per_cell
                    ),
                }
                for cell in cells
            ],
            "pilot_match_ids_excluded": plan.pilot_selection.selected_match_ids,
            "identifiers_in_summary": False,
        },
    }


def _load_context(
    sampling_frame_path: str | Path,
    final_plan_path: str | Path,
    duration_rule_path: str | Path,
    duration_analysis_path: str | Path,
    pilot_discovery_plan_path: str | Path,
    pilot_discovery_root: str | Path,
    pilot_selection_root: str | Path,
) -> FinalDiscoveryContext:
    frame, frame_sha256 = load_registered_sampling_frame(sampling_frame_path)
    plan, plan_sha256 = load_registered_final_discovery_plan(
        final_plan_path,
        frame=frame,
        frame_sha256=frame_sha256,
    )
    duration = validate_duration_rule(
        duration_rule_path,
        sampling_frame_path,
        duration_analysis_path,
    )
    if (
        not duration["passed"]
        or duration.get("rule_id") != plan.duration_rule.rule_id
        or duration.get("rule_sha256") != plan.duration_rule.rule_sha256
        or duration.get("analysis_sha256") != plan.duration_rule.analysis_sha256
    ):
        raise ValueError("final discovery duration binding is missing, invalid, or changed")
    pilot = load_frozen_pilot_selection(
        sampling_frame_path,
        pilot_discovery_plan_path,
        pilot_discovery_root,
        pilot_selection_root,
    )
    binding = plan.pilot_selection
    pilot_valid = (
        pilot.frame_sha256 == frame_sha256
        and pilot.plan_id == binding.discovery_plan_id
        and pilot.plan_sha256 == binding.discovery_plan_sha256
        and pilot.discovery_manifest_sha256 == binding.discovery_manifest_sha256
        and pilot.candidate_pool_sha256 == binding.candidate_pool_sha256
        and pilot.selected_pool_sha256 == binding.selected_pool_sha256
        and len(pilot.selected_matches) == binding.selected_match_ids
    )
    if not pilot_valid:
        raise ValueError("final discovery pilot exclusion binding is invalid or changed")
    return FinalDiscoveryContext(frame, frame_sha256, plan, plan_sha256, pilot)


def final_candidate_discovery_preflight(
    authority_record: str | Path,
    sampling_frame_path: str | Path,
    final_plan_path: str | Path,
    duration_rule_path: str | Path,
    duration_analysis_path: str | Path,
    pilot_discovery_plan_path: str | Path,
    pilot_discovery_root: str | Path,
    pilot_selection_root: str | Path,
    *,
    environment: Mapping[str, str] | None = None,
    as_of: date | None = None,
) -> dict[str, object]:
    """Validate final discovery authority and every local freeze binding."""

    try:
        context = _load_context(
            sampling_frame_path,
            final_plan_path,
            duration_rule_path,
            duration_analysis_path,
            pilot_discovery_plan_path,
            pilot_discovery_root,
            pilot_selection_root,
        )
    except ValueError as error:
        return {
            "schema_version": FINAL_DISCOVERY_PREFLIGHT_SCHEMA_VERSION,
            "passed": False,
            "authority": None,
            "bindings": {"passed": False, "message": str(error)},
        }
    authority = collection_preflight(
        authority_record,
        requested_regions=(route.regional_route for route in context.frame.route_platforms),
        required_endpoints=DISCOVERY_ENDPOINTS,
        environment=environment,
        as_of=as_of,
    )
    return {
        "schema_version": FINAL_DISCOVERY_PREFLIGHT_SCHEMA_VERSION,
        "passed": bool(authority["passed"]),
        "authority": authority,
        "bindings": {
            "passed": True,
            "frame_id": context.frame.frame_id,
            "plan_id": context.plan.plan_id,
            "duration_rule_id": context.plan.duration_rule.rule_id,
            "pilot_match_ids_excluded": len(context.pilot.selected_matches),
            "identifiers_in_summary": False,
        },
    }


def _candidate_pool(
    root: Path,
    context: FinalDiscoveryContext,
    *,
    snapshot_sha256: str,
    processed_members: Mapping[str, tuple[SnapshotMember, ...]],
) -> tuple[dict[str, object], list[dict[str, object]], bool]:
    frame = context.frame
    plan = context.plan
    pilot_ids = {entry.match_id for entry in context.pilot.selected_matches}
    assignments: dict[str, tuple[str, str, str]] = {}
    excluded_pilot_ids: set[str] = set()
    cells: list[dict[str, object]] = []
    for patch in frame.patches:
        for route in frame.route_platforms:
            discovered: set[str] = set()
            for member in processed_members[route.platform_id]:
                player_key = _player_key_sha256(
                    frame,
                    platform_id=route.platform_id,
                    member=member,
                )
                path = _history_path(
                    root,
                    route.platform_id,
                    patch.game_version_patch,
                    player_key,
                )
                try:
                    history = HistoryPage.model_validate_json(path.read_bytes())
                except (OSError, ValidationError) as error:
                    raise ValueError(
                        "A completed final-discovery wave has a missing history page"
                    ) from error
                discovered.update(history.match_ids)

            overlap = discovered.intersection(pilot_ids)
            excluded_pilot_ids.update(overlap)
            eligible_candidates = discovered - pilot_ids
            key = (route.regional_route, route.platform_id, patch.game_version_patch)
            for match_id in eligible_candidates:
                prior = assignments.setdefault(match_id, key)
                if prior != key:
                    raise ValueError("One final candidate was returned for multiple cells")
            ordered = order_candidate_match_ids(frame, tuple(eligible_candidates))
            final_target = next(
                cell.final_target
                for cell in sampling_cells(frame)
                if (
                    cell.regional_route,
                    cell.platform_id,
                    cell.game_version_patch,
                )
                == key
            )
            minimum = final_target * plan.stopping.candidate_multiplier_per_cell
            cells.append(
                {
                    "regional_route": route.regional_route,
                    "platform_id": route.platform_id,
                    "game_version_patch": patch.game_version_patch,
                    "minimum_candidates": minimum,
                    "candidate_count": len(ordered),
                    "excluded_pilot_matches_discovered": len(overlap),
                    "minimum_met": len(ordered) >= minimum,
                    "match_ids": list(ordered),
                }
            )

    complete = all(bool(cell["minimum_met"]) for cell in cells)
    pool: dict[str, object] = {
        "schema_version": FINAL_CANDIDATE_POOL_SCHEMA_VERSION,
        "stage": "final",
        "frame_id": frame.frame_id,
        "frame_sha256": context.frame_sha256,
        "plan_id": plan.plan_id,
        "plan_sha256": context.plan_sha256,
        "duration_rule_sha256": plan.duration_rule.rule_sha256,
        "pilot_selected_pool_sha256": plan.pilot_selection.selected_pool_sha256,
        "snapshot_sha256": snapshot_sha256,
        "complete": complete,
        "globally_deduplicated": len(assignments)
        == sum(cast(int, cell["candidate_count"]) for cell in cells),
        "excluded_pilot_match_ids_discovered": len(excluded_pilot_ids),
        "cells": cells,
        "contains_match_identifiers": True,
        "contains_player_identifiers": False,
        "redistribution": "not-authorized",
    }
    summaries = [
        {
            key: cell[key]
            for key in (
                "regional_route",
                "platform_id",
                "game_version_patch",
                "minimum_candidates",
                "candidate_count",
                "excluded_pilot_matches_discovered",
                "minimum_met",
            )
        }
        for cell in cells
    ]
    return pool, summaries, complete


def _roots_overlap(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents


def discover_final_candidate_pool(
    sampling_frame_path: str | Path,
    final_plan_path: str | Path,
    duration_rule_path: str | Path,
    duration_analysis_path: str | Path,
    pilot_discovery_plan_path: str | Path,
    pilot_discovery_root: str | Path,
    pilot_selection_root: str | Path,
    *,
    output_root: str | Path,
    platform_fetchers: Mapping[str, PlatformDiscoveryFetcher],
    regional_fetchers: Mapping[str, RegionalDiscoveryFetcher],
    discovered_at: datetime | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, object]:
    """Build or resume a final candidate pool after removing every pilot ID."""

    context = _load_context(
        sampling_frame_path,
        final_plan_path,
        duration_rule_path,
        duration_analysis_path,
        pilot_discovery_plan_path,
        pilot_discovery_root,
        pilot_selection_root,
    )
    frame = context.frame
    plan = context.plan
    timestamp = discovered_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("discovered_at must be timezone-aware")
    root = Path(output_root)
    resolved = root.resolve()
    for private_root in (Path(pilot_discovery_root), Path(pilot_selection_root)):
        if _roots_overlap(resolved, private_root.resolve()):
            raise ValueError("Final discovery requires an output root separate from pilot data")
    if list(root.rglob("*.partial")):
        raise ValueError("Final candidate discovery contains an incomplete partial file")

    snapshot, snapshot_content = _load_or_create_snapshot(
        root,
        frame,
        frame_sha256=context.frame_sha256,
        plan=cast(Any, plan),
        plan_sha256=context.plan_sha256,
        platform_fetchers=platform_fetchers,
        created_at=timestamp,
    )
    snapshot_sha256 = _sha256(snapshot_content)
    if progress is not None:
        progress(f"Final ladder snapshot ready for {len(snapshot.platforms)} platforms")

    snapshot_by_platform = {platform.platform_id: platform for platform in snapshot.platforms}
    ordered_by_platform = {
        platform_id: _ordered_members(frame, snapshot_by_platform[platform_id])
        for platform_id in snapshot_by_platform
    }
    maximum_balanced_players = min(
        plan.ladder.max_players_per_platform,
        *(len(members) for members in ordered_by_platform.values()),
    )
    maximum_balanced_players -= maximum_balanced_players % plan.ladder.wave_size_per_platform
    if maximum_balanced_players < plan.ladder.wave_size_per_platform:
        raise ValueError("Final ladder snapshot cannot supply one balanced player wave")

    complete = False
    pool: dict[str, object] = {}
    cell_summaries: list[dict[str, object]] = []
    players_processed = 0
    processed_members: dict[str, tuple[SnapshotMember, ...]] = {}
    for wave_end in range(
        plan.ladder.wave_size_per_platform,
        maximum_balanced_players + 1,
        plan.ladder.wave_size_per_platform,
    ):
        for route in frame.route_platforms:
            platform_fetcher = platform_fetchers.get(route.platform_id)
            regional_fetcher = regional_fetchers.get(route.regional_route)
            if platform_fetcher is None or regional_fetcher is None:
                raise ValueError("Final discovery clients do not cover every route-platform")
            members = ordered_by_platform[route.platform_id][:wave_end]
            for member in members[players_processed:wave_end]:
                player_key = _player_key_sha256(
                    frame,
                    platform_id=route.platform_id,
                    member=member,
                )
                resolution = _resolve_player(
                    root,
                    frame_sha256=context.frame_sha256,
                    plan_sha256=context.plan_sha256,
                    snapshot_sha256=snapshot_sha256,
                    platform_id=route.platform_id,
                    member=member,
                    player_key=player_key,
                    fetcher=platform_fetcher,
                )
                for patch in frame.patches:
                    _load_or_fetch_history(
                        root,
                        frame_sha256=context.frame_sha256,
                        plan=cast(Any, plan),
                        plan_sha256=context.plan_sha256,
                        snapshot_sha256=snapshot_sha256,
                        regional_route=route.regional_route,
                        platform_id=route.platform_id,
                        game_version_patch=patch.game_version_patch,
                        released_on=patch.released_on,
                        closed_on=patch.closed_on,
                        player_key=player_key,
                        puuid=resolution.puuid,
                        fetcher=regional_fetcher,
                    )

        players_processed = wave_end
        processed_members = {
            platform_id: members[:wave_end] for platform_id, members in ordered_by_platform.items()
        }
        pool, cell_summaries, complete = _candidate_pool(
            root,
            context,
            snapshot_sha256=snapshot_sha256,
            processed_members=processed_members,
        )
        _atomic_write(root / "candidate-pool.json", _canonical_json(pool))
        if progress is not None:
            ready = sum(bool(cell["minimum_met"]) for cell in cell_summaries)
            progress(
                f"Final balanced wave {wave_end // plan.ladder.wave_size_per_platform} "
                f"complete: {ready}/{len(cell_summaries)} cells meet the 2x buffer"
            )
        if complete:
            break

    expected_resolution_paths = {
        _resolution_path(
            root,
            route.platform_id,
            _player_key_sha256(
                frame,
                platform_id=route.platform_id,
                member=member,
            ),
        )
        for route in frame.route_platforms
        for member in processed_members[route.platform_id]
    }
    expected_history_paths = {
        _history_path(
            root,
            route.platform_id,
            patch.game_version_patch,
            _player_key_sha256(
                frame,
                platform_id=route.platform_id,
                member=member,
            ),
        )
        for route in frame.route_platforms
        for patch in frame.patches
        for member in processed_members[route.platform_id]
    }
    resolution_paths = set((root / "resolutions").rglob("*.json"))
    history_paths = set((root / "histories").rglob("*.json"))
    if resolution_paths != expected_resolution_paths or history_paths != expected_history_paths:
        raise ValueError("Final candidate-discovery cache inventory is inconsistent")

    pool_content = (root / "candidate-pool.json").read_bytes()
    manifest: dict[str, object] = {
        "schema_version": FINAL_DISCOVERY_MANIFEST_SCHEMA_VERSION,
        "completed_at": timestamp.astimezone(UTC).isoformat(),
        "complete": complete,
        "frame_id": frame.frame_id,
        "frame_sha256": context.frame_sha256,
        "plan_id": plan.plan_id,
        "plan_sha256": context.plan_sha256,
        "duration_rule_sha256": plan.duration_rule.rule_sha256,
        "duration_analysis_sha256": plan.duration_rule.analysis_sha256,
        "pilot_selected_pool_sha256": plan.pilot_selection.selected_pool_sha256,
        "ladder_snapshot_sha256": snapshot_sha256,
        "candidate_pool_sha256": _sha256(pool_content),
        "resolution_cache_sha256": _aggregate_digest(root, list(resolution_paths)),
        "history_cache_sha256": _aggregate_digest(root, list(history_paths)),
        "players_processed_per_platform": players_processed,
        "balanced_waves_completed": players_processed // plan.ladder.wave_size_per_platform,
        "resolution_files": len(resolution_paths),
        "history_page_files": len(history_paths),
        "candidate_match_ids": sum(cast(int, cell["candidate_count"]) for cell in cell_summaries),
        "excluded_pilot_match_ids_discovered": pool["excluded_pilot_match_ids_discovered"],
        "candidate_windows": cell_summaries,
        "contains_player_identifiers_in_private_files": True,
        "identifiers_in_summary": False,
        "redistribution": "not-authorized",
    }
    _atomic_write(root / "discovery-manifest.json", _canonical_json(manifest))
    return manifest


def _load_final_candidate_pool(
    context: FinalDiscoveryContext,
    discovery_root: str | Path,
) -> tuple[FinalDiscoveryManifest, FinalCandidatePool, str, str]:
    root = Path(discovery_root)
    if list(root.rglob("*.partial")):
        raise ValueError("Final candidate discovery contains an incomplete partial file")
    try:
        manifest_content = (root / "discovery-manifest.json").read_bytes()
        pool_content = (root / "candidate-pool.json").read_bytes()
        snapshot_content = (root / "ladder-snapshot.json").read_bytes()
        manifest = FinalDiscoveryManifest.model_validate_json(manifest_content)
        pool = FinalCandidatePool.model_validate_json(pool_content)
        snapshot = LadderSnapshot.model_validate_json(snapshot_content)
    except OSError as error:
        raise ValueError("Final discovery artifacts are missing or unreadable") from error
    except ValidationError as error:
        raise ValueError(
            f"Final discovery artifact schema rejected: {_safe_validation_error(error)}"
        ) from error

    manifest_sha256 = _sha256(manifest_content)
    pool_sha256 = _sha256(pool_content)
    snapshot_sha256 = _sha256(snapshot_content)
    plan = context.plan
    bindings_valid = (
        manifest.completed_at.tzinfo is not None
        and manifest.complete
        and pool.complete
        and pool.globally_deduplicated
        and manifest.frame_id == pool.frame_id == context.frame.frame_id
        and manifest.frame_sha256 == pool.frame_sha256 == context.frame_sha256
        and manifest.plan_id == pool.plan_id == plan.plan_id
        and manifest.plan_sha256 == pool.plan_sha256 == context.plan_sha256
        and manifest.duration_rule_sha256
        == pool.duration_rule_sha256
        == plan.duration_rule.rule_sha256
        and manifest.duration_analysis_sha256 == plan.duration_rule.analysis_sha256
        and manifest.pilot_selected_pool_sha256
        == pool.pilot_selected_pool_sha256
        == plan.pilot_selection.selected_pool_sha256
        and manifest.ladder_snapshot_sha256 == pool.snapshot_sha256 == snapshot_sha256
        and manifest.candidate_pool_sha256 == pool_sha256
        and snapshot.frame_id == context.frame.frame_id
        and snapshot.frame_sha256 == context.frame_sha256
        and snapshot.plan_id == plan.plan_id
        and snapshot.plan_sha256 == context.plan_sha256
    )
    if not bindings_valid:
        raise ValueError("Final candidate pool is not bound to its frozen provenance")

    registered_cells = sampling_cells(context.frame)
    expected_coordinates = tuple(
        (cell.regional_route, cell.platform_id, cell.game_version_patch)
        for cell in registered_cells
    )
    observed_coordinates = tuple(
        (cell.regional_route, cell.platform_id, cell.game_version_patch) for cell in pool.cells
    )
    if observed_coordinates != expected_coordinates or len(manifest.candidate_windows) != len(
        pool.cells
    ):
        raise ValueError("Final candidate pool does not contain every registered cell")

    pilot_ids = {entry.match_id for entry in context.pilot.selected_matches}
    all_ids: list[str] = []
    summaries: list[dict[str, object]] = []
    for registered, cell in zip(registered_cells, pool.cells, strict=True):
        minimum = registered.final_target * plan.stopping.candidate_multiplier_per_cell
        ids = cell.match_ids
        valid = (
            cell.minimum_candidates == minimum
            and cell.candidate_count == len(ids)
            and cell.minimum_met == (len(ids) >= minimum)
            and cell.minimum_met
            and all(
                MATCH_ID_PATTERN.fullmatch(match_id) is not None
                and match_id.startswith(f"{cell.platform_id}_")
                and match_id not in pilot_ids
                for match_id in ids
            )
            and ids == order_candidate_match_ids(context.frame, ids)
        )
        if not valid:
            raise ValueError("Final candidate cell count, order, or pilot exclusion is invalid")
        all_ids.extend(ids)
        summaries.append(
            {
                "regional_route": cell.regional_route,
                "platform_id": cell.platform_id,
                "game_version_patch": cell.game_version_patch,
                "minimum_candidates": cell.minimum_candidates,
                "candidate_count": cell.candidate_count,
                "excluded_pilot_matches_discovered": (cell.excluded_pilot_matches_discovered),
                "minimum_met": cell.minimum_met,
            }
        )
    if (
        len(all_ids) != len(set(all_ids))
        or manifest.candidate_match_ids != len(all_ids)
        or [item.model_dump(mode="json") for item in manifest.candidate_windows] != summaries
    ):
        raise ValueError("Final candidate inventory or identifier-free summary has changed")

    snapshot_by_platform = {platform.platform_id: platform for platform in snapshot.platforms}
    if set(snapshot_by_platform) != {route.platform_id for route in context.frame.route_platforms}:
        raise ValueError("Final ladder snapshot route inventory is invalid")
    processed = manifest.players_processed_per_platform
    processed_members = {
        route.platform_id: _ordered_members(
            context.frame,
            snapshot_by_platform[route.platform_id],
        )[:processed]
        for route in context.frame.route_platforms
    }
    expected_resolution_paths = {
        _resolution_path(
            root,
            route.platform_id,
            _player_key_sha256(
                context.frame,
                platform_id=route.platform_id,
                member=member,
            ),
        )
        for route in context.frame.route_platforms
        for member in processed_members[route.platform_id]
    }
    expected_history_paths = {
        _history_path(
            root,
            route.platform_id,
            patch.game_version_patch,
            _player_key_sha256(
                context.frame,
                platform_id=route.platform_id,
                member=member,
            ),
        )
        for route in context.frame.route_platforms
        for patch in context.frame.patches
        for member in processed_members[route.platform_id]
    }
    resolution_paths = set((root / "resolutions").rglob("*.json"))
    history_paths = set((root / "histories").rglob("*.json"))
    caches_valid = (
        resolution_paths == expected_resolution_paths
        and history_paths == expected_history_paths
        and manifest.resolution_files == len(resolution_paths)
        and manifest.history_page_files == len(history_paths)
        and manifest.resolution_cache_sha256 == _aggregate_digest(root, list(resolution_paths))
        and manifest.history_cache_sha256 == _aggregate_digest(root, list(history_paths))
    )
    if not caches_valid:
        raise ValueError("Final discovery cache inventory or checksum has changed")
    derived_pool, derived_summaries, derived_complete = _candidate_pool(
        root,
        context,
        snapshot_sha256=snapshot_sha256,
        processed_members=processed_members,
    )
    if (
        not derived_complete
        or _canonical_json(derived_pool) != pool_content
        or derived_summaries != summaries
        or manifest.excluded_pilot_match_ids_discovered != pool.excluded_pilot_match_ids_discovered
    ):
        raise ValueError("Final candidate pool does not reproduce from its history cache")
    return manifest, pool, manifest_sha256, pool_sha256


def validate_final_candidate_pool(
    sampling_frame_path: str | Path,
    final_plan_path: str | Path,
    duration_rule_path: str | Path,
    duration_analysis_path: str | Path,
    pilot_discovery_plan_path: str | Path,
    pilot_discovery_root: str | Path,
    pilot_selection_root: str | Path,
    final_discovery_root: str | Path,
) -> dict[str, object]:
    """Validate final candidates and all private bindings without returning an ID."""

    try:
        context = _load_context(
            sampling_frame_path,
            final_plan_path,
            duration_rule_path,
            duration_analysis_path,
            pilot_discovery_plan_path,
            pilot_discovery_root,
            pilot_selection_root,
        )
        manifest, pool, manifest_sha256, pool_sha256 = _load_final_candidate_pool(
            context,
            final_discovery_root,
        )
    except ValueError as error:
        return {
            "schema_version": FINAL_CANDIDATE_POOL_VALIDATION_SCHEMA_VERSION,
            "passed": False,
            "checks": [
                asdict(
                    FinalDiscoveryCheck(
                        "final-candidate-binding",
                        False,
                        str(error),
                    )
                )
            ],
            "summary": None,
        }

    checks = [
        FinalDiscoveryCheck(
            "artifact-schema",
            True,
            "Final discovery manifest and candidate pool conform to strict schemas",
        ),
        FinalDiscoveryCheck(
            "checksum-binding",
            True,
            "Final candidates are bound to the frame, duration rule, pilot and snapshot",
        ),
        FinalDiscoveryCheck(
            "pilot-exclusion",
            True,
            "No frozen pilot match ID is present in the final candidate pool",
        ),
        FinalDiscoveryCheck(
            "candidate-capacity",
            True,
            "Every route-patch cell has at least 6,000 deterministically ordered candidates",
        ),
        FinalDiscoveryCheck(
            "cache-integrity",
            True,
            "All private ladder, resolution and history artifacts retain their checksums",
        ),
    ]
    return {
        "schema_version": FINAL_CANDIDATE_POOL_VALIDATION_SCHEMA_VERSION,
        "passed": True,
        "frame_id": context.frame.frame_id,
        "plan_id": context.plan.plan_id,
        "discovery_manifest_sha256": manifest_sha256,
        "candidate_pool_sha256": pool_sha256,
        "checks": [asdict(check) for check in checks],
        "summary": {
            "candidate_match_ids": manifest.candidate_match_ids,
            "excluded_pilot_match_ids_discovered": (pool.excluded_pilot_match_ids_discovered),
            "players_processed_per_platform": manifest.players_processed_per_platform,
            "balanced_waves_completed": manifest.balanced_waves_completed,
            "registered_cells": len(pool.cells),
            "minimum_candidates_per_cell": min(cell.candidate_count for cell in pool.cells),
            "identifiers_in_summary": False,
        },
    }
