"""Outcome-blind, checksum-bound screening and selection of the final sample."""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from league_ews.authority import collection_preflight
from league_ews.duration_rule import DurationRule, load_duration_rule
from league_ews.final_discovery import (
    FinalCandidatePool,
    FinalDiscoveryContext,
    FinalDiscoveryManifest,
    _load_final_candidate_pool,
    _roots_overlap,
    load_registered_final_discovery_plan,
)
from league_ews.final_discovery import (
    _load_context as _load_final_discovery_context,
)
from league_ews.pilot_collection import FrozenPilotSelection
from league_ews.sampling import (
    Region,
    SamplingFrame,
    candidate_rank_sha256,
    load_registered_sampling_frame,
    order_candidate_match_ids,
    sampling_cells,
)
from league_ews.selection import (
    CandidateReference,
    DetailScreenFetcher,
    ScreenOutcome,
    _aggregate_digest,
    _atomic_write,
    _canonical_json,
    _detail_record_path,
    _load_cached_outcomes,
    _new_screen_record,
    _safe_validation_error,
    _sha256,
)

FINAL_SELECTION_PLAN_SCHEMA_VERSION = "league-ews-final-selection-plan-v1"
FINAL_SELECTION_PLAN_VALIDATION_SCHEMA_VERSION = "league-ews-final-selection-plan-validation-v1"
FINAL_SELECTION_PREFLIGHT_SCHEMA_VERSION = "riot-final-selection-preflight-v1"
FINAL_SELECTED_POOL_SCHEMA_VERSION = "riot-final-selected-pool-v1"
FINAL_SELECTION_MANIFEST_SCHEMA_VERSION = "riot-final-selection-manifest-v1"
FINAL_SELECTION_VALIDATION_SCHEMA_VERSION = "riot-frozen-final-selection-validation-v1"

REGISTERED_PLAN_ID = "rifthazard-final-selection-2026-09-21"
REGISTERED_FROZEN_ON = date(2026, 9, 21)
REGISTERED_FRAME_ID = "rifthazard-2026-09-15"
REGISTERED_FRAME_SHA256 = "2355ec26182aa6862e8a110ff94f0ab402e9a4e77c0a52a0a5c81f1892033f6b"
REGISTERED_DURATION_RULE_ID = "rifthazard-duration-2026-09-20"
REGISTERED_DURATION_RULE_SHA256 = "b957947597e9fa64dec89bcd2b762ca9c37f4d3941ff26be02e59c09cf8856fe"
REGISTERED_FINAL_MINIMUM_SECONDS = 180
REGISTERED_PILOT_SELECTED_POOL_SHA256 = (
    "05f566c3c36d5402a9f2ef26bd3c63dae33737bd550dae0c735dbe5f87a656eb"
)
REGISTERED_PILOT_MATCHES = 5_000
REGISTERED_FINAL_DISCOVERY_PLAN_ID = "rifthazard-final-discovery-2026-09-20"
REGISTERED_FINAL_DISCOVERY_PLAN_SHA256 = (
    "e8fcdf0781e080fd19259db77ce2304e946dd62ed9d47296924a731c78794c1a"
)
REGISTERED_FINAL_DISCOVERY_MANIFEST_SHA256 = (
    "f8a9afd2332632a59f774bd841f31a40f349cd104414481c4cecb5a15762cdb0"
)
REGISTERED_FINAL_CANDIDATE_POOL_SHA256 = (
    "b452e60496dc4bb38e4f7d79a2057aaf2a6e05f93ff826859695dfeda1fedecc"
)
REGISTERED_FINAL_CANDIDATES = 110_838
REGISTERED_EXCLUDED_PILOT_IDS = 4_292
REGISTERED_PLAYERS_PER_PLATFORM = 288
REGISTERED_BALANCED_WAVES = 9
REGISTERED_FINAL_TARGET = 36_000
REGISTERED_MATCHES_PER_CELL = 3_000
REGISTERED_CELLS = 12
SHA256_PATTERN = r"^[0-9a-f]{64}$"

REGISTERED_CANDIDATE_WINDOWS = (
    ("europe", "EUW1", "16.12", 9_234),
    ("americas", "NA1", "16.12", 6_574),
    ("europe", "EUW1", "16.13", 12_116),
    ("americas", "NA1", "16.13", 9_486),
    ("europe", "EUW1", "16.14", 8_442),
    ("americas", "NA1", "16.14", 7_811),
    ("europe", "EUW1", "16.15", 9_604),
    ("americas", "NA1", "16.15", 8_302),
    ("europe", "EUW1", "16.16", 10_611),
    ("americas", "NA1", "16.16", 8_739),
    ("europe", "EUW1", "16.17", 10_699),
    ("americas", "NA1", "16.17", 9_220),
)


class FrameBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    frame_id: Literal["rifthazard-2026-09-15"]
    sha256: str = Field(pattern=SHA256_PATTERN)


class DurationBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: Literal["rifthazard-duration-2026-09-20"]
    rule_sha256: str = Field(pattern=SHA256_PATTERN)
    final_minimum_seconds: int = Field(gt=0)
    comparison: Literal["greater-than-or-equal"]


class PilotBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    selected_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    selected_match_ids: int = Field(gt=0)
    exclude_from_final: Literal[True]


class CandidateCellBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    regional_route: Region
    platform_id: str = Field(pattern=r"^[A-Z0-9]+$")
    game_version_patch: str = Field(pattern=r"^\d+\.\d+$")
    candidate_count: int = Field(gt=0)


class FinalDiscoveryBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-final-candidate-discovery-manifest-v1"]
    plan_id: Literal["rifthazard-final-discovery-2026-09-20"]
    plan_sha256: str = Field(pattern=SHA256_PATTERN)
    manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_match_ids: int = Field(gt=0)
    excluded_pilot_match_ids_discovered: int = Field(ge=0)
    players_processed_per_platform: int = Field(gt=0)
    balanced_waves_completed: int = Field(gt=0)
    cells: tuple[CandidateCellBinding, ...]


class FinalSelectionRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    stage: Literal["final"]
    target_matches: int = Field(gt=0)
    matches_per_cell: int = Field(gt=0)
    registered_cells: int = Field(gt=0)
    candidate_order: Literal["seeded-sha256-global-prefix-v1"]
    authoritative_cell_source: Literal["match-v5-detail-platform-gameVersion-v1"]
    provisional_patch_mismatch: Literal["reassign-within-registered-frame-v1"]
    unavailable_detail: Literal["reject-and-continue-v1"]
    stopping_rule: Literal["first-3000-eligible-per-authoritative-cell-v1"]


class FinalSelectionControls(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    eligibility_source: Literal["sampling-frame-plus-duration-rule-v1"]
    inspect_timeline: Literal[False]
    inspect_event_labels: Literal[False]
    inspect_winner: Literal[False]
    inspect_features: Literal[False]
    inspect_model_outputs: Literal[False]
    inspect_downstream_performance: Literal[False]


class FinalSelectionOutputs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    storage: Literal["private"]
    detail_cache: Literal["atomic-contiguous-global-prefix-v1"]
    selected_pool: Literal["checksum-bound-exact-cell-allocation-v1"]
    identifiers_in_public_summary: Literal[False]
    redistribution: Literal["not-authorized"]


class FinalSelectionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["league-ews-final-selection-plan-v1"]
    plan_id: str
    frozen_on: date
    status: Literal["frozen-after-final-candidate-validation-before-final-detail-screening"]
    sampling_frame: FrameBinding
    duration_rule: DurationBinding
    pilot_selection: PilotBinding
    final_discovery: FinalDiscoveryBinding
    selection: FinalSelectionRule
    controls: FinalSelectionControls
    outputs: FinalSelectionOutputs


class FinalSelectedMatchEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    match_id: str = Field(pattern=r"^[A-Z0-9]+_[0-9]+$")
    candidate_rank_sha256: str = Field(pattern=SHA256_PATTERN)
    screen_record_sha256: str = Field(pattern=SHA256_PATTERN)
    match_payload_sha256: str = Field(pattern=SHA256_PATTERN)
    game_version: str = Field(pattern=r"^\d+\.\d+(?:\.\d+)*$")
    game_creation_ms: int = Field(gt=0)
    game_duration_seconds: int = Field(gt=0)


class FinalSelectedCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    regional_route: Region
    platform_id: str = Field(pattern=r"^[A-Z0-9]+$")
    game_version_patch: str = Field(pattern=r"^\d+\.\d+$")
    target: int = Field(gt=0)
    selected_count: int = Field(gt=0)
    selected: tuple[FinalSelectedMatchEntry, ...]


class FinalSelectedRouteFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    regional_route: Region
    selected_count: int = Field(gt=0)
    sha256: str = Field(pattern=SHA256_PATTERN)


class FinalSelectedPool(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-final-selected-pool-v1"]
    stage: Literal["final"]
    frame_id: str
    frame_sha256: str = Field(pattern=SHA256_PATTERN)
    selection_plan_id: str
    selection_plan_sha256: str = Field(pattern=SHA256_PATTERN)
    final_discovery_plan_sha256: str = Field(pattern=SHA256_PATTERN)
    final_discovery_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    duration_rule_sha256: str = Field(pattern=SHA256_PATTERN)
    pilot_selected_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    selection_order: Literal["seeded-sha256-global-prefix-first-eligible-per-cell-v1"]
    authoritative_cell_source: Literal["match-v5-detail-platform-gameVersion-v1"]
    duration_eligibility: Literal["info.gameDuration>=180-v1"]
    selected_match_ids: int = Field(gt=0)
    globally_deduplicated: Literal[True]
    cells: tuple[FinalSelectedCell, ...]
    route_files: tuple[FinalSelectedRouteFile, ...]
    contains_match_identifiers: Literal[True]
    contains_player_identifiers: Literal[False]
    redistribution: Literal["not-authorized"]


class FinalSelectionCellSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    regional_route: Region
    platform_id: str = Field(pattern=r"^[A-Z0-9]+$")
    game_version_patch: str = Field(pattern=r"^\d+\.\d+$")
    target: int = Field(gt=0)
    eligible_screened: int = Field(ge=0)
    selected: int = Field(ge=0)
    complete: bool


class FinalSelectionManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-final-selection-manifest-v1"]
    recorded_at: datetime
    complete: bool
    frame_id: str
    frame_sha256: str = Field(pattern=SHA256_PATTERN)
    selection_plan_id: str
    selection_plan_sha256: str = Field(pattern=SHA256_PATTERN)
    final_discovery_plan_sha256: str = Field(pattern=SHA256_PATTERN)
    final_discovery_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    duration_rule_sha256: str = Field(pattern=SHA256_PATTERN)
    pilot_selected_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_match_ids: int = Field(gt=0)
    screened_match_ids: int = Field(gt=0)
    new_requests: int = Field(ge=0)
    eligible_screened: int = Field(ge=0)
    rejected_screened: int = Field(ge=0)
    selected_match_ids: int = Field(ge=0)
    screening_cache_sha256: str = Field(pattern=SHA256_PATTERN)
    selected_pool_sha256: str | None
    route_files: tuple[FinalSelectedRouteFile, ...]
    rejection_reasons: dict[str, int]
    cells: tuple[FinalSelectionCellSummary, ...]
    contains_player_identifiers_in_private_files: Literal[True]
    identifiers_in_summary: Literal[False]
    redistribution: Literal["not-authorized"]


@dataclass(frozen=True)
class FinalSelectionCheck:
    check_id: str
    passed: bool
    message: str


@dataclass(frozen=True)
class BoundFinalCandidatePool:
    frame: SamplingFrame
    frame_sha256: str
    selection_plan: FinalSelectionPlan
    selection_plan_sha256: str
    final_discovery_context: FinalDiscoveryContext
    discovery_manifest: FinalDiscoveryManifest
    discovery_manifest_sha256: str
    candidate_pool: FinalCandidatePool
    candidate_pool_sha256: str
    pilot: FrozenPilotSelection
    ordered_candidates: tuple[CandidateReference, ...]


@dataclass(frozen=True)
class FrozenFinalSelectedMatch:
    match_id: str
    regional_route: Region
    platform_id: str
    game_version_patch: str
    candidate_rank_sha256: str
    screen_record_sha256: str
    match_payload_sha256: str
    game_version: str
    game_creation_ms: int
    game_duration_seconds: int
    screen_record_path: Path


@dataclass(frozen=True)
class FrozenFinalSelection:
    frame: SamplingFrame
    frame_sha256: str
    selection_plan_id: str
    selection_plan_sha256: str
    final_discovery_plan_sha256: str
    final_discovery_manifest_sha256: str
    candidate_pool_sha256: str
    duration_rule_sha256: str
    pilot_selected_pool_sha256: str
    selected_pool_sha256: str
    selected_matches: tuple[FrozenFinalSelectedMatch, ...]


def _check(check_id: str, passed: bool, success: str, failure: str) -> FinalSelectionCheck:
    return FinalSelectionCheck(check_id, passed, success if passed else failure)


def _load_plan_bytes(path: Path) -> tuple[bytes, FinalSelectionPlan]:
    content = path.read_bytes()
    payload = yaml.safe_load(content)
    if not isinstance(payload, Mapping):
        raise ValueError("final selection plan must contain a mapping")
    return content, FinalSelectionPlan.model_validate(payload)


def _registered_cell_bindings() -> tuple[tuple[str, str, str, int], ...]:
    return REGISTERED_CANDIDATE_WINDOWS


def _plan_checks(
    plan: FinalSelectionPlan,
    *,
    frame: SamplingFrame,
    frame_sha256: str,
    final_discovery_plan_sha256: str,
    duration_rule: DurationRule,
    duration_rule_sha256: str,
) -> list[FinalSelectionCheck]:
    discovery = plan.final_discovery
    candidate_cells = tuple(
        (
            cell.regional_route,
            cell.platform_id,
            cell.game_version_patch,
            cell.candidate_count,
        )
        for cell in discovery.cells
    )
    registered_cells = sampling_cells(frame)
    controls = plan.controls
    return [
        FinalSelectionCheck(
            "plan-schema",
            True,
            f"Final selection plan conforms to {FINAL_SELECTION_PLAN_SCHEMA_VERSION}",
        ),
        _check(
            "freeze-stage",
            plan.plan_id == REGISTERED_PLAN_ID
            and plan.frozen_on == REGISTERED_FROZEN_ON
            and plan.frozen_on > frame.frozen_on,
            "Final selection was frozen after candidate validation and before detail screening",
            "Final selection identity or freeze stage differs from the registered protocol",
        ),
        _check(
            "sampling-frame-binding",
            plan.sampling_frame.frame_id == frame.frame_id == REGISTERED_FRAME_ID
            and plan.sampling_frame.sha256 == frame_sha256 == REGISTERED_FRAME_SHA256,
            "Final selection is bound to the immutable sampling frame",
            "Final selection does not match the registered sampling frame",
        ),
        _check(
            "duration-rule-binding",
            plan.duration_rule.rule_id == duration_rule.rule_id == REGISTERED_DURATION_RULE_ID
            and plan.duration_rule.rule_sha256
            == duration_rule_sha256
            == REGISTERED_DURATION_RULE_SHA256
            and plan.duration_rule.final_minimum_seconds
            == duration_rule.decision.final_minimum_seconds
            == REGISTERED_FINAL_MINIMUM_SECONDS,
            "Final selection enforces the frozen inclusive 180-second duration rule",
            "Final duration identity, checksum or cutoff differs from the freeze",
        ),
        _check(
            "pilot-exclusion-binding",
            plan.pilot_selection.selected_pool_sha256 == REGISTERED_PILOT_SELECTED_POOL_SHA256
            and plan.pilot_selection.selected_match_ids == REGISTERED_PILOT_MATCHES
            and plan.pilot_selection.exclude_from_final,
            "The exact 5,000-match pilot remains excluded from final selection",
            "Pilot exclusion no longer matches the frozen pilot selection",
        ),
        _check(
            "final-discovery-binding",
            discovery.plan_id == REGISTERED_FINAL_DISCOVERY_PLAN_ID
            and discovery.plan_sha256
            == final_discovery_plan_sha256
            == REGISTERED_FINAL_DISCOVERY_PLAN_SHA256
            and discovery.manifest_sha256 == REGISTERED_FINAL_DISCOVERY_MANIFEST_SHA256
            and discovery.candidate_pool_sha256 == REGISTERED_FINAL_CANDIDATE_POOL_SHA256
            and discovery.candidate_match_ids == REGISTERED_FINAL_CANDIDATES
            and discovery.excluded_pilot_match_ids_discovered == REGISTERED_EXCLUDED_PILOT_IDS
            and discovery.players_processed_per_platform == REGISTERED_PLAYERS_PER_PLATFORM
            and discovery.balanced_waves_completed == REGISTERED_BALANCED_WAVES
            and candidate_cells == _registered_cell_bindings(),
            "All 110,838 final candidates and 12 cell inventories are checksum-bound",
            "Final candidate provenance or identifier-free inventory differs from the freeze",
        ),
        _check(
            "exact-final-allocation",
            plan.selection.target_matches == REGISTERED_FINAL_TARGET
            and plan.selection.matches_per_cell == REGISTERED_MATCHES_PER_CELL
            and plan.selection.registered_cells == REGISTERED_CELLS
            and len(registered_cells) == REGISTERED_CELLS
            and sum(cell.final_target for cell in registered_cells) == REGISTERED_FINAL_TARGET
            and all(cell.final_target == REGISTERED_MATCHES_PER_CELL for cell in registered_cells),
            "Selection requires exactly 3,000 matches in each of 12 cells",
            "Final allocation differs from the registered 36,000-match target",
        ),
        _check(
            "deterministic-selection",
            plan.selection.candidate_order == "seeded-sha256-global-prefix-v1"
            and plan.selection.authoritative_cell_source
            == "match-v5-detail-platform-gameVersion-v1"
            and plan.selection.provisional_patch_mismatch == "reassign-within-registered-frame-v1"
            and plan.selection.unavailable_detail == "reject-and-continue-v1"
            and plan.selection.stopping_rule == "first-3000-eligible-per-authoritative-cell-v1",
            "Candidate order, authoritative cells, rejection and stopping are deterministic",
            "One or more final selection rules differ from the frozen protocol",
        ),
        _check(
            "outcome-blind-controls",
            not controls.inspect_timeline
            and not controls.inspect_event_labels
            and not controls.inspect_winner
            and not controls.inspect_features
            and not controls.inspect_model_outputs
            and not controls.inspect_downstream_performance,
            "Final screening cannot inspect timelines, outcomes, labels or model results",
            "One or more forbidden downstream inputs are enabled",
        ),
        _check(
            "private-outputs",
            plan.outputs.storage == "private"
            and not plan.outputs.identifiers_in_public_summary
            and plan.outputs.redistribution == "not-authorized",
            "Details and selected identifiers remain private and non-redistributable",
            "Final selection output controls are not privacy preserving",
        ),
    ]


def _public_plan_context(
    sampling_frame_path: str | Path,
    final_discovery_plan_path: str | Path,
    duration_rule_path: str | Path,
) -> tuple[SamplingFrame, str, str, DurationRule, str]:
    frame, frame_sha256 = load_registered_sampling_frame(sampling_frame_path)
    _, final_discovery_plan_sha256 = load_registered_final_discovery_plan(
        final_discovery_plan_path,
        frame=frame,
        frame_sha256=frame_sha256,
    )
    duration_path = Path(duration_rule_path)
    duration_content = duration_path.read_bytes()
    duration_rule = load_duration_rule(duration_path)
    return (
        frame,
        frame_sha256,
        final_discovery_plan_sha256,
        duration_rule,
        hashlib.sha256(duration_content).hexdigest(),
    )


def load_registered_final_selection_plan(
    plan_path: str | Path,
    sampling_frame_path: str | Path,
    final_discovery_plan_path: str | Path,
    duration_rule_path: str | Path,
) -> tuple[FinalSelectionPlan, str]:
    """Load the final-selection plan only when every public freeze check passes."""

    try:
        content, plan = _load_plan_bytes(Path(plan_path))
        frame, frame_sha256, discovery_sha256, duration_rule, duration_sha256 = (
            _public_plan_context(
                sampling_frame_path,
                final_discovery_plan_path,
                duration_rule_path,
            )
        )
    except ValidationError as error:
        raise ValueError(
            f"final selection plan schema rejected: {_safe_validation_error(error)}"
        ) from error
    except yaml.YAMLError as error:
        raise ValueError("final selection plan contains invalid YAML") from error
    except OSError as error:
        raise ValueError("final selection plan input is missing or unreadable") from error
    checks = _plan_checks(
        plan,
        frame=frame,
        frame_sha256=frame_sha256,
        final_discovery_plan_sha256=discovery_sha256,
        duration_rule=duration_rule,
        duration_rule_sha256=duration_sha256,
    )
    if not all(check.passed for check in checks):
        raise ValueError("final selection plan fails the registered contract")
    return plan, hashlib.sha256(content).hexdigest()


def validate_final_selection_plan(
    plan_path: str | Path,
    sampling_frame_path: str | Path,
    final_discovery_plan_path: str | Path,
    duration_rule_path: str | Path,
) -> dict[str, object]:
    """Validate the public final-selection freeze without private data or network access."""

    try:
        content, plan = _load_plan_bytes(Path(plan_path))
        frame, frame_sha256, discovery_sha256, duration_rule, duration_sha256 = (
            _public_plan_context(
                sampling_frame_path,
                final_discovery_plan_path,
                duration_rule_path,
            )
        )
        checks = _plan_checks(
            plan,
            frame=frame,
            frame_sha256=frame_sha256,
            final_discovery_plan_sha256=discovery_sha256,
            duration_rule=duration_rule,
            duration_rule_sha256=duration_sha256,
        )
    except (OSError, ValueError, yaml.YAMLError, ValidationError) as error:
        reason = _safe_validation_error(error) if isinstance(error, ValidationError) else str(error)
        check = FinalSelectionCheck(
            "plan-schema",
            False,
            f"Final selection plan rejected: {reason}",
        )
        return {
            "schema_version": FINAL_SELECTION_PLAN_VALIDATION_SCHEMA_VERSION,
            "plan_id": None,
            "plan_sha256": None,
            "passed": False,
            "checks": [asdict(check)],
            "summary": None,
        }
    return {
        "schema_version": FINAL_SELECTION_PLAN_VALIDATION_SCHEMA_VERSION,
        "plan_id": plan.plan_id,
        "plan_sha256": hashlib.sha256(content).hexdigest(),
        "passed": all(check.passed for check in checks),
        "checks": [asdict(check) for check in checks],
        "summary": {
            "candidate_match_ids": plan.final_discovery.candidate_match_ids,
            "registered_cells": plan.selection.registered_cells,
            "matches_per_cell": plan.selection.matches_per_cell,
            "target_matches": plan.selection.target_matches,
            "final_minimum_seconds": plan.duration_rule.final_minimum_seconds,
            "pilot_match_ids_excluded": plan.pilot_selection.selected_match_ids,
            "identifiers_in_summary": False,
        },
    }


def _load_bound_final_candidates(
    sampling_frame_path: str | Path,
    final_selection_plan_path: str | Path,
    final_discovery_plan_path: str | Path,
    duration_rule_path: str | Path,
    duration_analysis_path: str | Path,
    pilot_discovery_plan_path: str | Path,
    pilot_discovery_root: str | Path,
    pilot_selection_root: str | Path,
    final_discovery_root: str | Path,
) -> BoundFinalCandidatePool:
    context = _load_final_discovery_context(
        sampling_frame_path,
        final_discovery_plan_path,
        duration_rule_path,
        duration_analysis_path,
        pilot_discovery_plan_path,
        pilot_discovery_root,
        pilot_selection_root,
    )
    selection_plan, selection_plan_sha256 = load_registered_final_selection_plan(
        final_selection_plan_path,
        sampling_frame_path,
        final_discovery_plan_path,
        duration_rule_path,
    )
    manifest, pool, manifest_sha256, pool_sha256 = _load_final_candidate_pool(
        context,
        final_discovery_root,
    )
    binding = selection_plan.final_discovery
    cells = tuple(
        (
            cell.regional_route,
            cell.platform_id,
            cell.game_version_patch,
            cell.candidate_count,
        )
        for cell in pool.cells
    )
    bound = (
        context.frame.frame_id == selection_plan.sampling_frame.frame_id
        and context.frame_sha256 == selection_plan.sampling_frame.sha256
        and context.plan.plan_id == binding.plan_id
        and context.plan_sha256 == binding.plan_sha256
        and manifest_sha256 == binding.manifest_sha256
        and pool_sha256 == binding.candidate_pool_sha256
        and manifest.candidate_match_ids == binding.candidate_match_ids
        and manifest.excluded_pilot_match_ids_discovered
        == binding.excluded_pilot_match_ids_discovered
        and manifest.players_processed_per_platform == binding.players_processed_per_platform
        and manifest.balanced_waves_completed == binding.balanced_waves_completed
        and cells
        == tuple(
            (
                cell.regional_route,
                cell.platform_id,
                cell.game_version_patch,
                cell.candidate_count,
            )
            for cell in binding.cells
        )
        and context.plan.duration_rule.rule_sha256 == selection_plan.duration_rule.rule_sha256
        and context.pilot.selected_pool_sha256
        == selection_plan.pilot_selection.selected_pool_sha256
    )
    if not bound:
        raise ValueError("final selection plan does not match the completed candidate pool")

    pilot_ids = {entry.match_id for entry in context.pilot.selected_matches}
    references: list[CandidateReference] = []
    for cell in pool.cells:
        references.extend(
            CandidateReference(
                match_id=match_id,
                regional_route=cell.regional_route,
                platform_id=cell.platform_id,
            )
            for match_id in cell.match_ids
        )
    identifiers = tuple(reference.match_id for reference in references)
    if pilot_ids.intersection(identifiers):
        raise ValueError("final candidate pool contains a frozen pilot match ID")
    by_id = {reference.match_id: reference for reference in references}
    ordered_ids = order_candidate_match_ids(context.frame, identifiers)
    return BoundFinalCandidatePool(
        frame=context.frame,
        frame_sha256=context.frame_sha256,
        selection_plan=selection_plan,
        selection_plan_sha256=selection_plan_sha256,
        final_discovery_context=context,
        discovery_manifest=manifest,
        discovery_manifest_sha256=manifest_sha256,
        candidate_pool=pool,
        candidate_pool_sha256=pool_sha256,
        pilot=context.pilot,
        ordered_candidates=tuple(by_id[match_id] for match_id in ordered_ids),
    )


def final_selection_preflight(
    authority_record: str | Path,
    sampling_frame_path: str | Path,
    final_selection_plan_path: str | Path,
    final_discovery_plan_path: str | Path,
    duration_rule_path: str | Path,
    duration_analysis_path: str | Path,
    pilot_discovery_plan_path: str | Path,
    pilot_discovery_root: str | Path,
    pilot_selection_root: str | Path,
    final_discovery_root: str | Path,
    *,
    environment: Mapping[str, str] | None = None,
    as_of: date | None = None,
) -> dict[str, object]:
    """Validate authority and every frozen input before final detail requests."""

    try:
        bound = _load_bound_final_candidates(
            sampling_frame_path,
            final_selection_plan_path,
            final_discovery_plan_path,
            duration_rule_path,
            duration_analysis_path,
            pilot_discovery_plan_path,
            pilot_discovery_root,
            pilot_selection_root,
            final_discovery_root,
        )
    except ValueError as error:
        return {
            "schema_version": FINAL_SELECTION_PREFLIGHT_SCHEMA_VERSION,
            "passed": False,
            "authority": None,
            "bindings": {"passed": False, "message": str(error)},
        }
    authority = collection_preflight(
        authority_record,
        requested_regions=(route.regional_route for route in bound.frame.route_platforms),
        required_endpoints=("match-v5.match",),
        environment=environment,
        as_of=as_of,
    )
    return {
        "schema_version": FINAL_SELECTION_PREFLIGHT_SCHEMA_VERSION,
        "passed": bool(authority["passed"]),
        "authority": authority,
        "bindings": {
            "passed": True,
            "frame_id": bound.frame.frame_id,
            "selection_plan_id": bound.selection_plan.plan_id,
            "candidate_match_ids": len(bound.ordered_candidates),
            "pilot_match_ids_excluded": len(bound.pilot.selected_matches),
            "target_matches": bound.selection_plan.selection.target_matches,
            "identifiers_in_summary": False,
        },
    }


def _selection_state(
    bound: BoundFinalCandidatePool,
    outcomes: Sequence[ScreenOutcome],
) -> tuple[
    dict[tuple[str, str, str], list[ScreenOutcome]],
    Counter[tuple[str, str, str]],
    Counter[str],
]:
    targets = {
        (cell.regional_route, cell.platform_id, cell.game_version_patch): cell.final_target
        for cell in sampling_cells(bound.frame)
    }
    selected: dict[tuple[str, str, str], list[ScreenOutcome]] = {key: [] for key in targets}
    eligible_counts: Counter[tuple[str, str, str]] = Counter()
    rejection_reasons: Counter[str] = Counter()
    for outcome in outcomes:
        if outcome.eligible_cell is None:
            rejection_reasons.update(outcome.rejection_reasons)
            continue
        if outcome.eligible_cell not in targets:
            raise ValueError("A final detail produced an unregistered eligible cell")
        eligible_counts[outcome.eligible_cell] += 1
        if len(selected[outcome.eligible_cell]) < targets[outcome.eligible_cell]:
            selected[outcome.eligible_cell].append(outcome)
    return selected, eligible_counts, rejection_reasons


def _selection_complete(
    bound: BoundFinalCandidatePool,
    selected: Mapping[tuple[str, str, str], Sequence[ScreenOutcome]],
) -> bool:
    return all(
        len(selected[(cell.regional_route, cell.platform_id, cell.game_version_patch)])
        == cell.final_target
        for cell in sampling_cells(bound.frame)
    )


def _write_once_or_verify(path: Path, content: bytes) -> None:
    if path.is_file():
        if path.read_bytes() != content:
            raise ValueError("Existing frozen final-selection output does not match recomputation")
        return
    _atomic_write(path, content)


def _freeze_selected_pool(
    root: Path,
    bound: BoundFinalCandidatePool,
    selected: Mapping[tuple[str, str, str], Sequence[ScreenOutcome]],
) -> tuple[str, list[dict[str, object]]]:
    route_file_records: list[dict[str, object]] = []
    for route in bound.frame.route_platforms:
        identifiers = [
            outcome.match_id
            for cell in sampling_cells(bound.frame)
            if cell.regional_route == route.regional_route
            for outcome in selected[
                (cell.regional_route, cell.platform_id, cell.game_version_patch)
            ]
        ]
        content = ("\n".join(identifiers) + "\n").encode()
        _write_once_or_verify(root / "selected-match-ids" / f"{route.regional_route}.txt", content)
        route_file_records.append(
            {
                "regional_route": route.regional_route,
                "selected_count": len(identifiers),
                "sha256": _sha256(content),
            }
        )

    cells_payload: list[dict[str, object]] = []
    for cell in sampling_cells(bound.frame):
        key = (cell.regional_route, cell.platform_id, cell.game_version_patch)
        entries: list[dict[str, object]] = []
        for outcome in selected[key]:
            if (
                outcome.match_payload_sha256 is None
                or outcome.game_version is None
                or outcome.game_creation_ms is None
                or outcome.game_duration_seconds is None
            ):
                raise ValueError("A selected final match is missing detail provenance")
            entries.append(
                {
                    "match_id": outcome.match_id,
                    "candidate_rank_sha256": outcome.candidate_rank_sha256,
                    "screen_record_sha256": outcome.screen_record_sha256,
                    "match_payload_sha256": outcome.match_payload_sha256,
                    "game_version": outcome.game_version,
                    "game_creation_ms": outcome.game_creation_ms,
                    "game_duration_seconds": outcome.game_duration_seconds,
                }
            )
        cells_payload.append(
            {
                "regional_route": cell.regional_route,
                "platform_id": cell.platform_id,
                "game_version_patch": cell.game_version_patch,
                "target": cell.final_target,
                "selected_count": len(entries),
                "selected": entries,
            }
        )

    plan = bound.selection_plan
    pool = {
        "schema_version": FINAL_SELECTED_POOL_SCHEMA_VERSION,
        "stage": "final",
        "frame_id": bound.frame.frame_id,
        "frame_sha256": bound.frame_sha256,
        "selection_plan_id": plan.plan_id,
        "selection_plan_sha256": bound.selection_plan_sha256,
        "final_discovery_plan_sha256": bound.final_discovery_context.plan_sha256,
        "final_discovery_manifest_sha256": bound.discovery_manifest_sha256,
        "candidate_pool_sha256": bound.candidate_pool_sha256,
        "duration_rule_sha256": plan.duration_rule.rule_sha256,
        "pilot_selected_pool_sha256": plan.pilot_selection.selected_pool_sha256,
        "selection_order": "seeded-sha256-global-prefix-first-eligible-per-cell-v1",
        "authoritative_cell_source": "match-v5-detail-platform-gameVersion-v1",
        "duration_eligibility": "info.gameDuration>=180-v1",
        "selected_match_ids": sum(len(values) for values in selected.values()),
        "globally_deduplicated": True,
        "cells": cells_payload,
        "route_files": route_file_records,
        "contains_match_identifiers": True,
        "contains_player_identifiers": False,
        "redistribution": "not-authorized",
    }
    content = _canonical_json(pool)
    _write_once_or_verify(root / "selected-pool.json", content)
    return _sha256(content), route_file_records


def select_final_matches(
    sampling_frame_path: str | Path,
    final_selection_plan_path: str | Path,
    final_discovery_plan_path: str | Path,
    duration_rule_path: str | Path,
    duration_analysis_path: str | Path,
    pilot_discovery_plan_path: str | Path,
    pilot_discovery_root: str | Path,
    pilot_selection_root: str | Path,
    final_discovery_root: str | Path,
    *,
    output_root: str | Path,
    regional_fetchers: Mapping[str, DetailScreenFetcher],
    screened_at: datetime | None = None,
    max_new_requests: int | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, object]:
    """Screen a deterministic prefix and freeze exactly 36,000 final matches."""

    if max_new_requests is not None and max_new_requests <= 0:
        raise ValueError("max_new_requests must be positive when supplied")
    bound = _load_bound_final_candidates(
        sampling_frame_path,
        final_selection_plan_path,
        final_discovery_plan_path,
        duration_rule_path,
        duration_analysis_path,
        pilot_discovery_plan_path,
        pilot_discovery_root,
        pilot_selection_root,
        final_discovery_root,
    )
    root = Path(output_root)
    for private_root in (
        Path(pilot_discovery_root),
        Path(pilot_selection_root),
        Path(final_discovery_root),
    ):
        if _roots_overlap(root.resolve(), private_root.resolve()):
            raise ValueError("Final selection requires an output root separate from input data")
    timestamp = screened_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("screened_at must be timezone-aware")

    minimum = bound.selection_plan.duration_rule.final_minimum_seconds
    outcomes = _load_cached_outcomes(
        root,
        bound,
        minimum_duration_seconds=minimum,
    )
    selected, eligible_counts, rejection_reasons = _selection_state(bound, outcomes)
    registered_cells = sampling_cells(bound.frame)
    target_total = sum(cell.final_target for cell in registered_cells)
    new_requests = 0
    for reference in bound.ordered_candidates[len(outcomes) :]:
        if _selection_complete(bound, selected):
            break
        if max_new_requests is not None and new_requests >= max_new_requests:
            break
        fetcher = regional_fetchers.get(reference.regional_route)
        if fetcher is None:
            raise ValueError("Final detail clients do not cover every registered regional route")
        payload = fetcher.get_match_for_screening(reference.match_id)
        content, outcome = _new_screen_record(
            bound,
            reference,
            payload,
            fetched_at=timestamp,
            minimum_duration_seconds=minimum,
        )
        _atomic_write(_detail_record_path(root, reference), content)
        outcomes.append(outcome)
        new_requests += 1
        if outcome.eligible_cell is None:
            rejection_reasons.update(outcome.rejection_reasons)
        else:
            eligible_counts[outcome.eligible_cell] += 1
            target = next(
                cell.final_target
                for cell in registered_cells
                if (
                    cell.regional_route,
                    cell.platform_id,
                    cell.game_version_patch,
                )
                == outcome.eligible_cell
            )
            if len(selected[outcome.eligible_cell]) < target:
                selected[outcome.eligible_cell].append(outcome)
        should_report = new_requests % 100 == 0 or _selection_complete(bound, selected)
        if progress is not None and should_report:
            complete_cells = sum(
                len(selected[(cell.regional_route, cell.platform_id, cell.game_version_patch)])
                == cell.final_target
                for cell in registered_cells
            )
            progress(
                f"Screened {len(outcomes)}/{len(bound.ordered_candidates)} final candidates; "
                f"selected {sum(len(values) for values in selected.values())}/{target_total}; "
                f"complete cells {complete_cells}/{len(registered_cells)}"
            )

    complete = _selection_complete(bound, selected)
    selected_count = sum(len(values) for values in selected.values())
    selected_pool_sha256: str | None = None
    route_file_records: list[dict[str, object]] = []
    if complete:
        selected_pool_sha256, route_file_records = _freeze_selected_pool(root, bound, selected)
    elif (root / "selected-pool.json").exists() or (root / "selected-match-ids").exists():
        raise ValueError("Frozen final-selection outputs exist before every quota is complete")

    cells_summary: list[dict[str, object]] = []
    for cell in registered_cells:
        key = (cell.regional_route, cell.platform_id, cell.game_version_patch)
        cells_summary.append(
            {
                "regional_route": cell.regional_route,
                "platform_id": cell.platform_id,
                "game_version_patch": cell.game_version_patch,
                "target": cell.final_target,
                "eligible_screened": eligible_counts[key],
                "selected": len(selected[key]),
                "complete": len(selected[key]) == cell.final_target,
            }
        )

    detail_paths = list((root / "details").rglob("*.json"))
    plan = bound.selection_plan
    manifest: dict[str, object] = {
        "schema_version": FINAL_SELECTION_MANIFEST_SCHEMA_VERSION,
        "recorded_at": timestamp.astimezone(UTC).isoformat(),
        "complete": complete,
        "frame_id": bound.frame.frame_id,
        "frame_sha256": bound.frame_sha256,
        "selection_plan_id": plan.plan_id,
        "selection_plan_sha256": bound.selection_plan_sha256,
        "final_discovery_plan_sha256": bound.final_discovery_context.plan_sha256,
        "final_discovery_manifest_sha256": bound.discovery_manifest_sha256,
        "candidate_pool_sha256": bound.candidate_pool_sha256,
        "duration_rule_sha256": plan.duration_rule.rule_sha256,
        "pilot_selected_pool_sha256": plan.pilot_selection.selected_pool_sha256,
        "candidate_match_ids": len(bound.ordered_candidates),
        "screened_match_ids": len(outcomes),
        "new_requests": new_requests,
        "eligible_screened": sum(outcome.eligible_cell is not None for outcome in outcomes),
        "rejected_screened": sum(outcome.eligible_cell is None for outcome in outcomes),
        "selected_match_ids": selected_count,
        "screening_cache_sha256": _aggregate_digest(root, detail_paths),
        "selected_pool_sha256": selected_pool_sha256,
        "route_files": route_file_records,
        "rejection_reasons": dict(sorted(rejection_reasons.items())),
        "cells": cells_summary,
        "contains_player_identifiers_in_private_files": True,
        "identifiers_in_summary": False,
        "redistribution": "not-authorized",
    }
    _atomic_write(root / "selection-manifest.json", _canonical_json(manifest))
    return manifest


def _patch(game_version: str) -> str:
    return ".".join(game_version.split(".")[:2])


def load_frozen_final_selection(
    sampling_frame_path: str | Path,
    final_selection_plan_path: str | Path,
    final_discovery_plan_path: str | Path,
    duration_rule_path: str | Path,
    duration_analysis_path: str | Path,
    pilot_discovery_plan_path: str | Path,
    pilot_discovery_root: str | Path,
    pilot_selection_root: str | Path,
    final_discovery_root: str | Path,
    final_selection_root: str | Path,
) -> FrozenFinalSelection:
    """Load the exact final selection after recomputing every private binding."""

    bound = _load_bound_final_candidates(
        sampling_frame_path,
        final_selection_plan_path,
        final_discovery_plan_path,
        duration_rule_path,
        duration_analysis_path,
        pilot_discovery_plan_path,
        pilot_discovery_root,
        pilot_selection_root,
        final_discovery_root,
    )
    root = Path(final_selection_root)
    if list(root.rglob("*.partial")):
        raise ValueError("Frozen final selection contains an incomplete partial file")
    try:
        manifest_content = (root / "selection-manifest.json").read_bytes()
        pool_content = (root / "selected-pool.json").read_bytes()
        manifest = FinalSelectionManifest.model_validate_json(manifest_content)
        pool = FinalSelectedPool.model_validate_json(pool_content)
    except OSError as error:
        raise ValueError("Frozen final-selection artifacts are missing or unreadable") from error
    except ValidationError as error:
        raise ValueError(
            f"Frozen final-selection schema rejected: {_safe_validation_error(error)}"
        ) from error

    pool_sha256 = _sha256(pool_content)
    plan = bound.selection_plan
    binding_valid = (
        manifest.recorded_at.tzinfo is not None
        and manifest.complete
        and manifest.frame_id == pool.frame_id == bound.frame.frame_id
        and manifest.frame_sha256 == pool.frame_sha256 == bound.frame_sha256
        and manifest.selection_plan_id == pool.selection_plan_id == plan.plan_id
        and manifest.selection_plan_sha256
        == pool.selection_plan_sha256
        == bound.selection_plan_sha256
        and manifest.final_discovery_plan_sha256
        == pool.final_discovery_plan_sha256
        == bound.final_discovery_context.plan_sha256
        and manifest.final_discovery_manifest_sha256
        == pool.final_discovery_manifest_sha256
        == bound.discovery_manifest_sha256
        and manifest.candidate_pool_sha256
        == pool.candidate_pool_sha256
        == bound.candidate_pool_sha256
        and manifest.duration_rule_sha256
        == pool.duration_rule_sha256
        == plan.duration_rule.rule_sha256
        and manifest.pilot_selected_pool_sha256
        == pool.pilot_selected_pool_sha256
        == plan.pilot_selection.selected_pool_sha256
        and manifest.selected_pool_sha256 == pool_sha256
    )
    if not binding_valid:
        raise ValueError("Frozen final selection is not bound to its registered provenance")

    outcomes = _load_cached_outcomes(
        root,
        bound,
        minimum_duration_seconds=plan.duration_rule.final_minimum_seconds,
    )
    selected_by_cell, eligible_counts, rejection_reasons = _selection_state(bound, outcomes)
    screening_valid = (
        manifest.candidate_match_ids == len(bound.ordered_candidates)
        and manifest.screened_match_ids == len(outcomes)
        and manifest.new_requests <= manifest.screened_match_ids
        and manifest.eligible_screened
        == sum(outcome.eligible_cell is not None for outcome in outcomes)
        and manifest.rejected_screened == sum(outcome.eligible_cell is None for outcome in outcomes)
        and manifest.screened_match_ids == manifest.eligible_screened + manifest.rejected_screened
        and manifest.rejection_reasons == dict(sorted(rejection_reasons.items()))
        and manifest.screening_cache_sha256
        == _aggregate_digest(root, list((root / "details").rglob("*.json")))
    )
    if not screening_valid:
        raise ValueError("Frozen final screening cache or summary has changed")

    registered_cells = sampling_cells(bound.frame)
    expected_coordinates = tuple(
        (cell.regional_route, cell.platform_id, cell.game_version_patch)
        for cell in registered_cells
    )
    observed_coordinates = tuple(
        (cell.regional_route, cell.platform_id, cell.game_version_patch) for cell in pool.cells
    )
    if observed_coordinates != expected_coordinates or len(manifest.cells) != len(pool.cells):
        raise ValueError("Frozen final selection does not contain every registered cell")

    candidate_ids = {reference.match_id for reference in bound.ordered_candidates}
    pilot_ids = {entry.match_id for entry in bound.pilot.selected_matches}
    selected_ids: set[str] = set()
    frozen: list[FrozenFinalSelectedMatch] = []
    for registered, selected_cell, summary in zip(
        registered_cells,
        pool.cells,
        manifest.cells,
        strict=True,
    ):
        target = registered.final_target
        key = (
            registered.regional_route,
            registered.platform_id,
            registered.game_version_patch,
        )
        derived = selected_by_cell[key]
        summary_valid = (
            summary.regional_route == selected_cell.regional_route
            and summary.platform_id == selected_cell.platform_id
            and summary.game_version_patch == selected_cell.game_version_patch
            and summary.target == target
            and summary.selected == target
            and summary.eligible_screened == eligible_counts.get(key, 0)
            and summary.complete
        )
        if (
            selected_cell.target != target
            or selected_cell.selected_count != target
            or len(selected_cell.selected) != target
            or len(derived) != target
            or not summary_valid
        ):
            raise ValueError("Frozen final selection does not meet every exact cell quota")
        for entry, outcome in zip(selected_cell.selected, derived, strict=True):
            if (
                entry.match_id in selected_ids
                or entry.match_id in pilot_ids
                or entry.match_id not in candidate_ids
                or not entry.match_id.startswith(f"{selected_cell.platform_id}_")
                or candidate_rank_sha256(bound.frame, entry.match_id) != entry.candidate_rank_sha256
                or _patch(entry.game_version) != selected_cell.game_version_patch
                or entry.game_duration_seconds < plan.duration_rule.final_minimum_seconds
                or entry.match_id != outcome.match_id
                or entry.candidate_rank_sha256 != outcome.candidate_rank_sha256
                or entry.screen_record_sha256 != outcome.screen_record_sha256
                or entry.match_payload_sha256 != outcome.match_payload_sha256
                or entry.game_version != outcome.game_version
                or entry.game_creation_ms != outcome.game_creation_ms
                or entry.game_duration_seconds != outcome.game_duration_seconds
            ):
                raise ValueError("Frozen final selected-match identity or eligibility is invalid")
            selected_ids.add(entry.match_id)
            screen_path = root / "details" / selected_cell.regional_route / f"{entry.match_id}.json"
            try:
                screen_content = screen_path.read_bytes()
            except OSError as error:
                raise ValueError("A selected final detail-screen record is missing") from error
            if _sha256(screen_content) != entry.screen_record_sha256:
                raise ValueError("A selected final detail-screen checksum has changed")
            frozen.append(
                FrozenFinalSelectedMatch(
                    match_id=entry.match_id,
                    regional_route=selected_cell.regional_route,
                    platform_id=selected_cell.platform_id,
                    game_version_patch=selected_cell.game_version_patch,
                    candidate_rank_sha256=entry.candidate_rank_sha256,
                    screen_record_sha256=entry.screen_record_sha256,
                    match_payload_sha256=entry.match_payload_sha256,
                    game_version=entry.game_version,
                    game_creation_ms=entry.game_creation_ms,
                    game_duration_seconds=entry.game_duration_seconds,
                    screen_record_path=screen_path,
                )
            )

    if (
        len(frozen) != REGISTERED_FINAL_TARGET
        or pool.selected_match_ids != REGISTERED_FINAL_TARGET
        or manifest.selected_match_ids != REGISTERED_FINAL_TARGET
        or len(selected_ids) != REGISTERED_FINAL_TARGET
    ):
        raise ValueError("Frozen final selection total is inconsistent")

    expected_route_files: list[FinalSelectedRouteFile] = []
    for route in bound.frame.route_platforms:
        route_ids = [
            entry.match_id for entry in frozen if entry.regional_route == route.regional_route
        ]
        expected_content = ("\n".join(route_ids) + "\n").encode()
        path = root / "selected-match-ids" / f"{route.regional_route}.txt"
        try:
            content = path.read_bytes()
        except OSError as error:
            raise ValueError("A frozen final regional selected-ID file is missing") from error
        if content != expected_content:
            raise ValueError("A frozen final regional selected-ID file has changed")
        expected_route_files.append(
            FinalSelectedRouteFile(
                regional_route=route.regional_route,
                selected_count=len(route_ids),
                sha256=_sha256(content),
            )
        )
    expected_routes = tuple(expected_route_files)
    if pool.route_files != expected_routes or manifest.route_files != expected_routes:
        raise ValueError("Frozen final regional file checksums are inconsistent")

    return FrozenFinalSelection(
        frame=bound.frame,
        frame_sha256=bound.frame_sha256,
        selection_plan_id=plan.plan_id,
        selection_plan_sha256=bound.selection_plan_sha256,
        final_discovery_plan_sha256=bound.final_discovery_context.plan_sha256,
        final_discovery_manifest_sha256=bound.discovery_manifest_sha256,
        candidate_pool_sha256=bound.candidate_pool_sha256,
        duration_rule_sha256=plan.duration_rule.rule_sha256,
        pilot_selected_pool_sha256=plan.pilot_selection.selected_pool_sha256,
        selected_pool_sha256=pool_sha256,
        selected_matches=tuple(frozen),
    )


def validate_frozen_final_selection(
    sampling_frame_path: str | Path,
    final_selection_plan_path: str | Path,
    final_discovery_plan_path: str | Path,
    duration_rule_path: str | Path,
    duration_analysis_path: str | Path,
    pilot_discovery_plan_path: str | Path,
    pilot_discovery_root: str | Path,
    pilot_selection_root: str | Path,
    final_discovery_root: str | Path,
    final_selection_root: str | Path,
) -> dict[str, object]:
    """Return an identifier-free report for the exact frozen final selection."""

    try:
        frozen = load_frozen_final_selection(
            sampling_frame_path,
            final_selection_plan_path,
            final_discovery_plan_path,
            duration_rule_path,
            duration_analysis_path,
            pilot_discovery_plan_path,
            pilot_discovery_root,
            pilot_selection_root,
            final_discovery_root,
            final_selection_root,
        )
    except ValueError as error:
        return {
            "schema_version": FINAL_SELECTION_VALIDATION_SCHEMA_VERSION,
            "passed": False,
            "checks": [
                {
                    "check_id": "frozen-final-selection-binding",
                    "passed": False,
                    "message": str(error),
                }
            ],
            "summary": None,
        }
    return {
        "schema_version": FINAL_SELECTION_VALIDATION_SCHEMA_VERSION,
        "passed": True,
        "frame_id": frozen.frame.frame_id,
        "selection_plan_id": frozen.selection_plan_id,
        "selected_pool_sha256": frozen.selected_pool_sha256,
        "checks": [
            {
                "check_id": "frozen-final-selection-binding",
                "passed": True,
                "message": "Every selected match retains its candidate and detail checksums",
            },
            {
                "check_id": "exact-final-allocation",
                "passed": True,
                "message": "The final selection contains exactly 3,000 matches in every cell",
            },
            {
                "check_id": "duration-eligibility",
                "passed": True,
                "message": "Every final match satisfies the inclusive 180-second minimum",
            },
            {
                "check_id": "pilot-exclusion",
                "passed": True,
                "message": "No frozen pilot match appears in the final selection",
            },
        ],
        "summary": {
            "selected_match_ids": len(frozen.selected_matches),
            "registered_cells": len(sampling_cells(frozen.frame)),
            "matches_per_cell": REGISTERED_MATCHES_PER_CELL,
            "identifiers_in_summary": False,
        },
    }
