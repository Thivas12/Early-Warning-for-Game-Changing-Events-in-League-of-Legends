"""Checksum-bound, resumable eligibility screening and pilot selection."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from league_ews.discovery import (
    DiscoveryPlan,
    candidate_discovery_preflight,
    load_registered_discovery_plan,
)
from league_ews.sampling import (
    MATCH_ID_PATTERN,
    Region,
    SamplingFrame,
    candidate_rank_sha256,
    load_registered_sampling_frame,
    order_candidate_match_ids,
    sampling_cells,
)

CANDIDATE_POOL_VALIDATION_SCHEMA_VERSION = "riot-candidate-pool-validation-v1"
PILOT_SELECTION_PREFLIGHT_SCHEMA_VERSION = "riot-pilot-selection-preflight-v1"
DETAIL_SCREEN_SCHEMA_VERSION: Literal["riot-match-detail-screen-v1"] = "riot-match-detail-screen-v1"
SELECTED_POOL_SCHEMA_VERSION = "riot-pilot-selected-pool-v1"
PILOT_SELECTION_MANIFEST_SCHEMA_VERSION = "riot-pilot-selection-manifest-v1"

SHA256_PATTERN = r"^[0-9a-f]{64}$"
GAME_VERSION_PATTERN = re.compile(r"^\d+\.\d+(?:\.\d+)*$")


class CandidatePoolCell(BaseModel):
    """One provisional calendar-window cell from candidate discovery."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    regional_route: Literal["americas", "asia", "europe", "sea"]
    platform_id: str = Field(pattern=r"^[A-Z0-9]+$")
    game_version_patch: str = Field(pattern=r"^\d+\.\d+$")
    minimum_candidates: int = Field(gt=0)
    candidate_count: int = Field(ge=0)
    minimum_met: bool
    match_ids: tuple[str, ...]


class CandidatePool(BaseModel):
    """Private, globally deduplicated discovery result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-candidate-pool-v1"]
    frame_id: str
    frame_sha256: str = Field(pattern=SHA256_PATTERN)
    plan_id: str
    plan_sha256: str = Field(pattern=SHA256_PATTERN)
    snapshot_sha256: str = Field(pattern=SHA256_PATTERN)
    complete: bool
    globally_deduplicated: bool
    cells: tuple[CandidatePoolCell, ...]
    contains_match_identifiers: Literal[True]
    redistribution: Literal["not-authorized"]


class CandidateWindowSummary(BaseModel):
    """Identifier-free discovery summary for one provisional cell."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    regional_route: Literal["americas", "asia", "europe", "sea"]
    platform_id: str = Field(pattern=r"^[A-Z0-9]+$")
    game_version_patch: str = Field(pattern=r"^\d+\.\d+$")
    minimum_candidates: int = Field(gt=0)
    candidate_count: int = Field(ge=0)
    minimum_met: bool


class DiscoveryManifest(BaseModel):
    """Strict shape of the identifier-free discovery manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-candidate-discovery-manifest-v1"]
    completed_at: datetime
    complete: bool
    frame_id: str
    frame_sha256: str = Field(pattern=SHA256_PATTERN)
    plan_id: str
    plan_sha256: str = Field(pattern=SHA256_PATTERN)
    ladder_snapshot_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    resolution_cache_sha256: str = Field(pattern=SHA256_PATTERN)
    history_cache_sha256: str = Field(pattern=SHA256_PATTERN)
    players_processed_per_platform: int = Field(gt=0)
    balanced_waves_completed: int = Field(gt=0)
    resolution_files: int = Field(gt=0)
    history_page_files: int = Field(gt=0)
    candidate_match_ids: int = Field(gt=0)
    candidate_windows: tuple[CandidateWindowSummary, ...]
    contains_player_identifiers_in_private_files: Literal[True]
    identifiers_in_summary: Literal[False]
    redistribution: Literal["not-authorized"]


class DetailScreenRecord(BaseModel):
    """One immutable private Match-V5 detail response or 404 marker."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-match-detail-screen-v1"]
    fetched_at: datetime
    frame_sha256: str = Field(pattern=SHA256_PATTERN)
    discovery_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_rank_sha256: str = Field(pattern=SHA256_PATTERN)
    match_id: str
    regional_route: Literal["americas", "asia", "europe", "sea"]
    platform_id: str = Field(pattern=r"^[A-Z0-9]+$")
    fetch_status: Literal["found", "not-found"]
    payload: dict[str, Any] | None


class DetailScreenFetcher(Protocol):
    """Minimal Match-V5 surface used before timeline collection."""

    def get_match_for_screening(self, match_id: str) -> Mapping[str, Any] | None: ...


@dataclass(frozen=True)
class CandidateReference:
    match_id: str
    regional_route: Region
    platform_id: str


@dataclass(frozen=True)
class BoundCandidatePool:
    frame: SamplingFrame
    frame_sha256: str
    plan: DiscoveryPlan
    plan_sha256: str
    discovery_manifest: DiscoveryManifest
    discovery_manifest_sha256: str
    candidate_pool: CandidatePool
    candidate_pool_sha256: str
    ordered_candidates: tuple[CandidateReference, ...]


@dataclass(frozen=True)
class ScreenOutcome:
    match_id: str
    candidate_rank_sha256: str
    screen_record_sha256: str
    match_payload_sha256: str | None
    eligible_cell: tuple[str, str, str] | None
    game_version: str | None
    game_creation_ms: int | None
    rejection_reasons: tuple[str, ...]


@dataclass(frozen=True)
class SelectionCheck:
    check_id: str
    passed: bool
    message: str


def _canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_bytes(content)
    temporary.replace(path)


def _write_once_or_verify(path: Path, content: bytes) -> None:
    if path.is_file():
        if path.read_bytes() != content:
            raise ValueError("Existing frozen pilot-selection output does not match recomputation")
        return
    _atomic_write(path, content)


def _safe_validation_error(error: ValidationError) -> str:
    issues = []
    for item in error.errors(include_input=False, include_context=False):
        location = ".".join(str(part) for part in item["loc"]) or "document"
        issues.append(f"{location}: {item['type']}")
    return "; ".join(issues)


def _check(check_id: str, passed: bool, success: str, failure: str) -> SelectionCheck:
    return SelectionCheck(check_id, passed, success if passed else failure)


def _patch(game_version: str) -> str:
    parts = game_version.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else game_version


def _load_bound_candidate_pool(
    sampling_frame_path: str | Path,
    discovery_plan_path: str | Path,
    discovery_root: str | Path,
) -> BoundCandidatePool:
    frame, frame_sha256 = load_registered_sampling_frame(sampling_frame_path)
    plan, plan_sha256 = load_registered_discovery_plan(
        discovery_plan_path,
        frame=frame,
        frame_sha256=frame_sha256,
    )
    root = Path(discovery_root)
    try:
        manifest_content = (root / "discovery-manifest.json").read_bytes()
        pool_content = (root / "candidate-pool.json").read_bytes()
    except OSError as error:
        raise ValueError(
            "Completed candidate-discovery artifacts are missing or unreadable"
        ) from error
    try:
        manifest = DiscoveryManifest.model_validate_json(manifest_content)
        pool = CandidatePool.model_validate_json(pool_content)
    except ValidationError as error:
        raise ValueError(
            f"Candidate-discovery artifact schema rejected: {_safe_validation_error(error)}"
        ) from error

    if manifest.completed_at.tzinfo is None:
        raise ValueError("Candidate-discovery manifest timestamp is not timezone-aware")
    if not manifest.complete or not pool.complete or not pool.globally_deduplicated:
        raise ValueError("Candidate discovery is not complete and globally deduplicated")
    pool_sha256 = _sha256(pool_content)
    manifest_sha256 = _sha256(manifest_content)
    binding_valid = (
        manifest.frame_id == frame.frame_id
        and manifest.frame_sha256 == frame_sha256
        and manifest.plan_id == plan.plan_id
        and manifest.plan_sha256 == plan_sha256
        and manifest.candidate_pool_sha256 == pool_sha256
        and pool.frame_id == frame.frame_id
        and pool.frame_sha256 == frame_sha256
        and pool.plan_id == plan.plan_id
        and pool.plan_sha256 == plan_sha256
        and pool.snapshot_sha256 == manifest.ladder_snapshot_sha256
    )
    if not binding_valid:
        raise ValueError("Candidate pool is not checksum-bound to its frame, plan and manifest")

    registered_cells = sampling_cells(frame)
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
        raise ValueError("Candidate pool does not contain the exact registered cell inventory")

    references: list[CandidateReference] = []
    summaries: list[dict[str, object]] = []
    for registered, cell in zip(registered_cells, pool.cells, strict=True):
        minimum = registered.pilot_target * plan.stopping.candidate_multiplier_per_cell
        safe_ids = all(
            MATCH_ID_PATTERN.fullmatch(match_id) is not None
            and match_id.startswith(f"{cell.platform_id}_")
            for match_id in cell.match_ids
        )
        ordered = safe_ids and cell.match_ids == order_candidate_match_ids(frame, cell.match_ids)
        cell_valid = (
            cell.minimum_candidates == minimum
            and cell.candidate_count == len(cell.match_ids)
            and cell.minimum_met == (cell.candidate_count >= minimum)
            and cell.minimum_met
            and ordered
        )
        if not cell_valid:
            raise ValueError("Candidate pool cell counts, IDs or deterministic order are invalid")
        references.extend(
            CandidateReference(
                match_id=match_id,
                regional_route=cell.regional_route,
                platform_id=cell.platform_id,
            )
            for match_id in cell.match_ids
        )
        summaries.append(
            {
                "regional_route": cell.regional_route,
                "platform_id": cell.platform_id,
                "game_version_patch": cell.game_version_patch,
                "minimum_candidates": cell.minimum_candidates,
                "candidate_count": cell.candidate_count,
                "minimum_met": cell.minimum_met,
            }
        )

    identifiers = tuple(reference.match_id for reference in references)
    manifest_summaries = [summary.model_dump(mode="json") for summary in manifest.candidate_windows]
    if (
        len(identifiers) != len(set(identifiers))
        or manifest.candidate_match_ids != len(identifiers)
        or manifest_summaries != summaries
    ):
        raise ValueError("Candidate pool and identifier-free discovery inventory disagree")

    by_id = {reference.match_id: reference for reference in references}
    globally_ordered = order_candidate_match_ids(frame, identifiers)
    return BoundCandidatePool(
        frame=frame,
        frame_sha256=frame_sha256,
        plan=plan,
        plan_sha256=plan_sha256,
        discovery_manifest=manifest,
        discovery_manifest_sha256=manifest_sha256,
        candidate_pool=pool,
        candidate_pool_sha256=pool_sha256,
        ordered_candidates=tuple(by_id[match_id] for match_id in globally_ordered),
    )


def validate_candidate_pool(
    sampling_frame_path: str | Path,
    discovery_plan_path: str | Path,
    discovery_root: str | Path,
) -> dict[str, object]:
    """Validate discovery artifacts without returning any private identifier."""

    try:
        bound = _load_bound_candidate_pool(
            sampling_frame_path,
            discovery_plan_path,
            discovery_root,
        )
    except ValueError as error:
        return {
            "schema_version": CANDIDATE_POOL_VALIDATION_SCHEMA_VERSION,
            "passed": False,
            "checks": [
                asdict(
                    SelectionCheck(
                        "candidate-pool-binding",
                        False,
                        str(error),
                    )
                )
            ],
            "summary": None,
        }

    checks = [
        SelectionCheck(
            "artifact-schema",
            True,
            "Discovery manifest and candidate pool conform to their registered schemas",
        ),
        SelectionCheck(
            "checksum-binding",
            True,
            "Candidate pool is bound to the exact frame, plan, snapshot and manifest",
        ),
        SelectionCheck(
            "candidate-inventory",
            True,
            "All candidate IDs are safe, globally unique and deterministically ordered",
        ),
        SelectionCheck(
            "registered-cells",
            True,
            "All 12 registered cells retain their frozen pre-detail candidate buffer",
        ),
    ]
    return {
        "schema_version": CANDIDATE_POOL_VALIDATION_SCHEMA_VERSION,
        "passed": True,
        "frame_id": bound.frame.frame_id,
        "frame_sha256": bound.frame_sha256,
        "plan_id": bound.plan.plan_id,
        "plan_sha256": bound.plan_sha256,
        "discovery_manifest_sha256": bound.discovery_manifest_sha256,
        "candidate_pool_sha256": bound.candidate_pool_sha256,
        "checks": [asdict(item) for item in checks],
        "summary": {
            "candidate_match_ids": len(bound.ordered_candidates),
            "registered_cells": len(bound.candidate_pool.cells),
            "identifiers_in_summary": False,
        },
    }


def pilot_selection_preflight(
    authority_record: str | Path,
    sampling_frame_path: str | Path,
    discovery_plan_path: str | Path,
    discovery_root: str | Path,
    *,
    environment: Mapping[str, str] | None = None,
    as_of: date | None = None,
) -> dict[str, object]:
    """Bind authority and complete private discovery artifacts before requests."""

    authority = candidate_discovery_preflight(
        authority_record,
        sampling_frame_path,
        discovery_plan_path,
        environment=environment,
        as_of=as_of,
    )
    candidate_pool = validate_candidate_pool(
        sampling_frame_path,
        discovery_plan_path,
        discovery_root,
    )
    return {
        "schema_version": PILOT_SELECTION_PREFLIGHT_SCHEMA_VERSION,
        "passed": bool(authority["passed"] and candidate_pool["passed"]),
        "authority": authority,
        "candidate_pool": candidate_pool,
    }


def _detail_record_path(root: Path, reference: CandidateReference) -> Path:
    return root / "details" / reference.regional_route / f"{reference.match_id}.json"


def _classify_detail(
    record: DetailScreenRecord,
    frame: SamplingFrame,
    *,
    screen_record_sha256: str,
) -> ScreenOutcome:
    if record.fetch_status == "not-found":
        if record.payload is not None:
            raise ValueError("A not-found detail-screen record unexpectedly contains a payload")
        return ScreenOutcome(
            match_id=record.match_id,
            candidate_rank_sha256=record.candidate_rank_sha256,
            screen_record_sha256=screen_record_sha256,
            match_payload_sha256=None,
            eligible_cell=None,
            game_version=None,
            game_creation_ms=None,
            rejection_reasons=("not-found",),
        )
    if record.payload is None:
        raise ValueError("A found detail-screen record is missing its payload")

    payload = record.payload
    metadata = payload.get("metadata")
    if not isinstance(metadata, Mapping) or metadata.get("matchId") != record.match_id:
        raise ValueError("Match detail payload identity does not match its screened candidate")
    info = payload.get("info")
    if not isinstance(info, Mapping):
        reasons = ("missing-info",)
        return ScreenOutcome(
            record.match_id,
            record.candidate_rank_sha256,
            screen_record_sha256,
            _sha256(_canonical_json(payload)),
            None,
            None,
            None,
            reasons,
        )

    reasons_list: list[str] = []
    if info.get("platformId") != record.platform_id:
        reasons_list.append("platform-mismatch")
    if info.get("queueId") != frame.eligibility.queue_id:
        reasons_list.append("queue")
    if info.get("mapId") != frame.eligibility.map_id:
        reasons_list.append("map")
    if info.get("gameMode") != frame.eligibility.game_mode:
        reasons_list.append("game-mode")
    if info.get("gameType") != frame.eligibility.game_type:
        reasons_list.append("game-type")
    info_participants = info.get("participants")
    metadata_participants = metadata.get("participants")
    if not isinstance(info_participants, list) or (
        len(info_participants) != frame.eligibility.participant_count
    ):
        reasons_list.append("info-participants")
    if not isinstance(metadata_participants, list) or (
        len(metadata_participants) != frame.eligibility.participant_count
    ):
        reasons_list.append("metadata-participants")

    raw_version = info.get("gameVersion")
    game_version = raw_version if isinstance(raw_version, str) else ""
    registered_patches = {patch.game_version_patch for patch in frame.patches}
    game_patch = _patch(game_version) if GAME_VERSION_PATTERN.fullmatch(game_version) else ""
    if game_patch not in registered_patches:
        reasons_list.append("game-version")

    raw_creation = info.get("gameCreation")
    game_creation_ms = (
        raw_creation if isinstance(raw_creation, int) and not isinstance(raw_creation, bool) else 0
    )
    if game_creation_ms <= 0:
        reasons_list.append("game-creation")

    eligible_cell = None
    if not reasons_list:
        eligible_cell = (record.regional_route, record.platform_id, game_patch)
    return ScreenOutcome(
        match_id=record.match_id,
        candidate_rank_sha256=record.candidate_rank_sha256,
        screen_record_sha256=screen_record_sha256,
        match_payload_sha256=_sha256(_canonical_json(payload)),
        eligible_cell=eligible_cell,
        game_version=game_version or None,
        game_creation_ms=game_creation_ms or None,
        rejection_reasons=tuple(reasons_list),
    )


def _load_cached_outcomes(root: Path, bound: BoundCandidatePool) -> list[ScreenOutcome]:
    if list(root.rglob("*.partial")):
        raise ValueError("Pilot-selection cache contains an incomplete partial file")
    paths = set((root / "details").rglob("*.json"))
    if len(paths) > len(bound.ordered_candidates):
        raise ValueError("Pilot-selection cache contains too many detail records")
    expected_references = bound.ordered_candidates[: len(paths)]
    expected_paths = {_detail_record_path(root, reference) for reference in expected_references}
    if paths != expected_paths:
        raise ValueError("Pilot-selection cache is not a contiguous deterministic prefix")

    outcomes: list[ScreenOutcome] = []
    for reference in expected_references:
        path = _detail_record_path(root, reference)
        content = path.read_bytes()
        try:
            record = DetailScreenRecord.model_validate_json(content)
        except ValidationError as error:
            raise ValueError(
                f"Detail-screen cache schema rejected: {_safe_validation_error(error)}"
            ) from error
        expected = (
            record.fetched_at.tzinfo is not None
            and record.frame_sha256 == bound.frame_sha256
            and record.discovery_manifest_sha256 == bound.discovery_manifest_sha256
            and record.candidate_pool_sha256 == bound.candidate_pool_sha256
            and record.candidate_rank_sha256
            == candidate_rank_sha256(bound.frame, reference.match_id)
            and record.match_id == reference.match_id
            and record.regional_route == reference.regional_route
            and record.platform_id == reference.platform_id
        )
        if not expected:
            raise ValueError("Detail-screen cache record does not match its frozen candidate")
        outcomes.append(
            _classify_detail(record, bound.frame, screen_record_sha256=_sha256(content))
        )
    return outcomes


def _new_screen_record(
    bound: BoundCandidatePool,
    reference: CandidateReference,
    payload: Mapping[str, Any] | None,
    *,
    fetched_at: datetime,
) -> tuple[bytes, ScreenOutcome]:
    record = DetailScreenRecord(
        schema_version=DETAIL_SCREEN_SCHEMA_VERSION,
        fetched_at=fetched_at.astimezone(UTC),
        frame_sha256=bound.frame_sha256,
        discovery_manifest_sha256=bound.discovery_manifest_sha256,
        candidate_pool_sha256=bound.candidate_pool_sha256,
        candidate_rank_sha256=candidate_rank_sha256(bound.frame, reference.match_id),
        match_id=reference.match_id,
        regional_route=reference.regional_route,
        platform_id=reference.platform_id,
        fetch_status="found" if payload is not None else "not-found",
        payload=dict(payload) if payload is not None else None,
    )
    content = _canonical_json(record.model_dump(mode="json"))
    outcome = _classify_detail(record, bound.frame, screen_record_sha256=_sha256(content))
    return content, outcome


def _aggregate_digest(root: Path, paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        content = path.read_bytes()
        digest.update(str(path.relative_to(root)).encode())
        digest.update(b"\0")
        digest.update(_sha256(content).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _selection_state(
    bound: BoundCandidatePool,
    outcomes: list[ScreenOutcome],
) -> tuple[
    dict[tuple[str, str, str], list[ScreenOutcome]],
    Counter[tuple[str, str, str]],
    Counter[str],
]:
    cells = sampling_cells(bound.frame)
    targets = {
        (cell.regional_route, cell.platform_id, cell.game_version_patch): cell.pilot_target
        for cell in cells
    }
    selected: dict[tuple[str, str, str], list[ScreenOutcome]] = {key: [] for key in targets}
    eligible_counts: Counter[tuple[str, str, str]] = Counter()
    rejection_reasons: Counter[str] = Counter()
    for outcome in outcomes:
        if outcome.eligible_cell is None:
            rejection_reasons.update(outcome.rejection_reasons)
            continue
        if outcome.eligible_cell not in targets:
            raise ValueError("A screened detail produced an unregistered eligible cell")
        eligible_counts[outcome.eligible_cell] += 1
        if len(selected[outcome.eligible_cell]) < targets[outcome.eligible_cell]:
            selected[outcome.eligible_cell].append(outcome)
    return selected, eligible_counts, rejection_reasons


def _selection_complete(
    bound: BoundCandidatePool,
    selected: Mapping[tuple[str, str, str], list[ScreenOutcome]],
) -> bool:
    return all(
        len(selected[(cell.regional_route, cell.platform_id, cell.game_version_patch)])
        == cell.pilot_target
        for cell in sampling_cells(bound.frame)
    )


def _freeze_selected_pool(
    root: Path,
    bound: BoundCandidatePool,
    selected: Mapping[tuple[str, str, str], list[ScreenOutcome]],
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
        entries = []
        for outcome in selected[key]:
            if (
                outcome.match_payload_sha256 is None
                or outcome.game_version is None
                or outcome.game_creation_ms is None
            ):
                raise ValueError("Selected match is missing required detail provenance")
            entries.append(
                {
                    "match_id": outcome.match_id,
                    "candidate_rank_sha256": outcome.candidate_rank_sha256,
                    "screen_record_sha256": outcome.screen_record_sha256,
                    "match_payload_sha256": outcome.match_payload_sha256,
                    "game_version": outcome.game_version,
                    "game_creation_ms": outcome.game_creation_ms,
                }
            )
        cells_payload.append(
            {
                "regional_route": cell.regional_route,
                "platform_id": cell.platform_id,
                "game_version_patch": cell.game_version_patch,
                "target": cell.pilot_target,
                "selected_count": len(entries),
                "selected": entries,
            }
        )

    pool = {
        "schema_version": SELECTED_POOL_SCHEMA_VERSION,
        "stage": "pilot",
        "frame_id": bound.frame.frame_id,
        "frame_sha256": bound.frame_sha256,
        "plan_id": bound.plan.plan_id,
        "plan_sha256": bound.plan_sha256,
        "discovery_manifest_sha256": bound.discovery_manifest_sha256,
        "candidate_pool_sha256": bound.candidate_pool_sha256,
        "selection_order": "seeded-sha256-within-authoritative-cell-v1",
        "authoritative_cell_source": "match-v5-detail-gameVersion-v1",
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


def select_pilot_matches(
    sampling_frame_path: str | Path,
    discovery_plan_path: str | Path,
    discovery_root: str | Path,
    *,
    output_root: str | Path,
    regional_fetchers: Mapping[str, DetailScreenFetcher],
    screened_at: datetime | None = None,
    max_new_requests: int | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, object]:
    """Screen the global candidate order and freeze the exact 5,000-match pilot."""

    if max_new_requests is not None and max_new_requests <= 0:
        raise ValueError("max_new_requests must be positive when supplied")
    bound = _load_bound_candidate_pool(
        sampling_frame_path,
        discovery_plan_path,
        discovery_root,
    )
    root = Path(output_root)
    if root.resolve() == Path(discovery_root).resolve():
        raise ValueError("Pilot selection and candidate discovery require separate output roots")
    timestamp = screened_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("screened_at must be timezone-aware")

    outcomes = _load_cached_outcomes(root, bound)
    selected, eligible_counts, rejection_reasons = _selection_state(bound, outcomes)
    registered_cells = sampling_cells(bound.frame)
    target_total = sum(cell.pilot_target for cell in registered_cells)
    new_requests = 0
    for reference in bound.ordered_candidates[len(outcomes) :]:
        if _selection_complete(bound, selected):
            break
        if max_new_requests is not None and new_requests >= max_new_requests:
            break
        fetcher = regional_fetchers.get(reference.regional_route)
        if fetcher is None:
            raise ValueError("Detail-screen clients do not cover every registered regional route")
        payload = fetcher.get_match_for_screening(reference.match_id)
        content, outcome = _new_screen_record(
            bound,
            reference,
            payload,
            fetched_at=timestamp,
        )
        _atomic_write(_detail_record_path(root, reference), content)
        outcomes.append(outcome)
        new_requests += 1
        if outcome.eligible_cell is None:
            rejection_reasons.update(outcome.rejection_reasons)
        else:
            eligible_counts[outcome.eligible_cell] += 1
            target = next(
                cell.pilot_target
                for cell in sampling_cells(bound.frame)
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
                == cell.pilot_target
                for cell in registered_cells
            )
            progress(
                f"Screened {len(outcomes)}/{len(bound.ordered_candidates)} candidates; "
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
        raise ValueError("Frozen selection outputs exist before all registered quotas are complete")

    cells_summary = []
    for cell in sampling_cells(bound.frame):
        key = (cell.regional_route, cell.platform_id, cell.game_version_patch)
        cells_summary.append(
            {
                "regional_route": cell.regional_route,
                "platform_id": cell.platform_id,
                "game_version_patch": cell.game_version_patch,
                "target": cell.pilot_target,
                "eligible_screened": eligible_counts[key],
                "selected": len(selected[key]),
                "complete": len(selected[key]) == cell.pilot_target,
            }
        )

    detail_paths = list((root / "details").rglob("*.json"))
    manifest: dict[str, object] = {
        "schema_version": PILOT_SELECTION_MANIFEST_SCHEMA_VERSION,
        "recorded_at": timestamp.astimezone(UTC).isoformat(),
        "complete": complete,
        "frame_id": bound.frame.frame_id,
        "frame_sha256": bound.frame_sha256,
        "plan_id": bound.plan.plan_id,
        "plan_sha256": bound.plan_sha256,
        "discovery_manifest_sha256": bound.discovery_manifest_sha256,
        "candidate_pool_sha256": bound.candidate_pool_sha256,
        "candidate_match_ids": len(bound.ordered_candidates),
        "screened_match_ids": len(outcomes),
        "new_requests": new_requests,
        "eligible_screened": sum(eligible_counts.values()),
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
