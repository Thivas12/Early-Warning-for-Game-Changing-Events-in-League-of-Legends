"""Selection-bound, resumable collection of the registered pilot timelines."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from league_ews.riot import (
    CollectedMatch,
    RiotAPIError,
    canonical_riot_json,
    collected_match_from_payloads,
)
from league_ews.sampling import (
    MATCH_ID_PATTERN,
    Region,
    SamplingFrame,
    candidate_rank_sha256,
    sampling_cells,
)
from league_ews.selection import (
    DetailScreenRecord,
    derive_pilot_selection_state,
    load_bound_candidate_pool,
    load_cached_screen_outcomes,
    pilot_selection_preflight,
    screening_cache_sha256,
)

FROZEN_SELECTION_VALIDATION_SCHEMA_VERSION = "riot-frozen-pilot-validation-v1"
PILOT_COLLECTION_PREFLIGHT_SCHEMA_VERSION = "riot-pilot-collection-preflight-v1"
PILOT_COLLECTION_BINDING_SCHEMA_VERSION: Literal["riot-pilot-collection-binding-v1"] = (
    "riot-pilot-collection-binding-v1"
)
PILOT_CHECKPOINT_PENDING_SCHEMA_VERSION: Literal["riot-pilot-checkpoint-pending-v1"] = (
    "riot-pilot-checkpoint-pending-v1"
)
SHA256_PATTERN = r"^[0-9a-f]{64}$"


class SelectedMatchEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    match_id: str = Field(pattern=r"^[A-Z0-9]+_[0-9]+$")
    candidate_rank_sha256: str = Field(pattern=SHA256_PATTERN)
    screen_record_sha256: str = Field(pattern=SHA256_PATTERN)
    match_payload_sha256: str = Field(pattern=SHA256_PATTERN)
    game_version: str = Field(pattern=r"^\d+\.\d+(?:\.\d+)*$")
    game_creation_ms: int = Field(gt=0)


class SelectedCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    regional_route: Region
    platform_id: str = Field(pattern=r"^[A-Z0-9]+$")
    game_version_patch: str = Field(pattern=r"^\d+\.\d+$")
    target: int = Field(gt=0)
    selected_count: int = Field(gt=0)
    selected: tuple[SelectedMatchEntry, ...]


class SelectedRouteFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    regional_route: Region
    selected_count: int = Field(gt=0)
    sha256: str = Field(pattern=SHA256_PATTERN)


class SelectedPool(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-pilot-selected-pool-v1"]
    stage: Literal["pilot"]
    frame_id: str
    frame_sha256: str = Field(pattern=SHA256_PATTERN)
    plan_id: str
    plan_sha256: str = Field(pattern=SHA256_PATTERN)
    discovery_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    selection_order: Literal["seeded-sha256-within-authoritative-cell-v1"]
    authoritative_cell_source: Literal["match-v5-detail-gameVersion-v1"]
    selected_match_ids: int = Field(gt=0)
    globally_deduplicated: Literal[True]
    cells: tuple[SelectedCell, ...]
    route_files: tuple[SelectedRouteFile, ...]
    contains_match_identifiers: Literal[True]
    contains_player_identifiers: Literal[False]
    redistribution: Literal["not-authorized"]


class SelectionCellSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    regional_route: Region
    platform_id: str = Field(pattern=r"^[A-Z0-9]+$")
    game_version_patch: str = Field(pattern=r"^\d+\.\d+$")
    target: int = Field(gt=0)
    eligible_screened: int = Field(ge=0)
    selected: int = Field(ge=0)
    complete: bool


class PilotSelectionManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-pilot-selection-manifest-v1"]
    recorded_at: datetime
    complete: bool
    frame_id: str
    frame_sha256: str = Field(pattern=SHA256_PATTERN)
    plan_id: str
    plan_sha256: str = Field(pattern=SHA256_PATTERN)
    discovery_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_match_ids: int = Field(gt=0)
    screened_match_ids: int = Field(gt=0)
    new_requests: int = Field(ge=0)
    eligible_screened: int = Field(ge=0)
    rejected_screened: int = Field(ge=0)
    selected_match_ids: int = Field(ge=0)
    screening_cache_sha256: str = Field(pattern=SHA256_PATTERN)
    selected_pool_sha256: str | None
    route_files: tuple[SelectedRouteFile, ...]
    rejection_reasons: dict[str, int]
    cells: tuple[SelectionCellSummary, ...]
    contains_player_identifiers_in_private_files: Literal[True]
    identifiers_in_summary: Literal[False]
    redistribution: Literal["not-authorized"]


class PilotCollectionBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-pilot-collection-binding-v1"]
    recorded_at: datetime
    complete: bool
    frame_id: str
    frame_sha256: str = Field(pattern=SHA256_PATTERN)
    plan_id: str
    plan_sha256: str = Field(pattern=SHA256_PATTERN)
    discovery_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    selected_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    collection_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    expected_selected_match_ids: int = Field(gt=0)
    available_bundles: int = Field(ge=0)
    new_timeline_requests: int = Field(ge=0)
    recovered_unpaired_bundles: int = Field(ge=0)
    identifiers_in_summary: Literal[False]
    redistribution: Literal["not-authorized"]


class PilotRawBundleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    match_id: str = Field(pattern=r"^[A-Z0-9]+_[0-9]+$")
    regional_route: Region
    game_version: str = Field(pattern=r"^\d+\.\d+(?:\.\d+)*$")
    game_creation_ms: int = Field(gt=0)
    match_sha256: str = Field(pattern=SHA256_PATTERN)
    timeline_sha256: str = Field(pattern=SHA256_PATTERN)


class PilotRawCollectionManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-raw-collection-v2"]
    collected_at: datetime
    requested: int = Field(ge=0)
    collected: tuple[PilotRawBundleRecord, ...]
    skipped_existing: tuple[str, ...]
    available: tuple[PilotRawBundleRecord, ...]
    contains_raw_player_identifiers: Literal[True]
    redistribution: Literal["not-authorized-by-this-manifest"]


class PilotCheckpointPending(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-pilot-checkpoint-pending-v1"]
    selected_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    collection_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    available_bundles: int = Field(ge=0)


class TimelineFetcher(Protocol):
    def get_timeline(self, match_id: str) -> Mapping[str, Any]: ...


class RawRecordLike(Protocol):
    match_id: str
    regional_route: str
    game_version: str
    game_creation_ms: int
    match_sha256: str


@dataclass(frozen=True)
class FrozenSelectedMatch:
    match_id: str
    regional_route: Region
    platform_id: str
    game_version_patch: str
    candidate_rank_sha256: str
    screen_record_sha256: str
    match_payload_sha256: str
    game_version: str
    game_creation_ms: int
    screen_record_path: Path


@dataclass(frozen=True)
class FrozenPilotSelection:
    frame: SamplingFrame
    frame_sha256: str
    plan_id: str
    plan_sha256: str
    discovery_manifest_sha256: str
    candidate_pool_sha256: str
    selected_pool_sha256: str
    selected_matches: tuple[FrozenSelectedMatch, ...]


def _canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_bytes(content)
    temporary.replace(path)


def _safe_validation_error(error: ValidationError) -> str:
    issues = []
    for item in error.errors(include_input=False, include_context=False):
        location = ".".join(str(part) for part in item["loc"]) or "document"
        issues.append(f"{location}: {item['type']}")
    return "; ".join(issues)


def _patch(game_version: str) -> str:
    return ".".join(game_version.split(".")[:2])


def load_frozen_pilot_selection(
    sampling_frame_path: str | Path,
    discovery_plan_path: str | Path,
    discovery_root: str | Path,
    selection_root: str | Path,
) -> FrozenPilotSelection:
    """Load the frozen pilot only after validating its complete provenance chain."""

    bound = load_bound_candidate_pool(
        sampling_frame_path,
        discovery_plan_path,
        discovery_root,
    )
    root = Path(selection_root)
    if list(root.rglob("*.partial")):
        raise ValueError("Frozen pilot selection contains an incomplete partial file")
    try:
        manifest_content = (root / "selection-manifest.json").read_bytes()
        pool_content = (root / "selected-pool.json").read_bytes()
        manifest = PilotSelectionManifest.model_validate_json(manifest_content)
        pool = SelectedPool.model_validate_json(pool_content)
    except OSError as error:
        raise ValueError("Frozen pilot-selection artifacts are missing or unreadable") from error
    except ValidationError as error:
        raise ValueError(
            f"Frozen pilot-selection schema rejected: {_safe_validation_error(error)}"
        ) from error

    pool_sha256 = _sha256(pool_content)
    binding_valid = (
        manifest.recorded_at.tzinfo is not None
        and manifest.complete
        and manifest.frame_id == bound.frame.frame_id
        and manifest.frame_sha256 == bound.frame_sha256
        and manifest.plan_id == bound.plan.plan_id
        and manifest.plan_sha256 == bound.plan_sha256
        and manifest.discovery_manifest_sha256 == bound.discovery_manifest_sha256
        and manifest.candidate_pool_sha256 == bound.candidate_pool_sha256
        and manifest.selected_pool_sha256 == pool_sha256
        and pool.frame_id == bound.frame.frame_id
        and pool.frame_sha256 == bound.frame_sha256
        and pool.plan_id == bound.plan.plan_id
        and pool.plan_sha256 == bound.plan_sha256
        and pool.discovery_manifest_sha256 == bound.discovery_manifest_sha256
        and pool.candidate_pool_sha256 == bound.candidate_pool_sha256
    )
    if not binding_valid:
        raise ValueError("Frozen pilot selection is not bound to its discovery provenance")

    outcomes = load_cached_screen_outcomes(root, bound)
    selected_by_cell, eligible_counts, rejection_reasons = derive_pilot_selection_state(
        bound,
        outcomes,
    )
    screening_valid = (
        manifest.candidate_match_ids == len(bound.ordered_candidates)
        and manifest.screened_match_ids == len(outcomes)
        and manifest.new_requests <= manifest.screened_match_ids
        and manifest.eligible_screened
        == sum(outcome.eligible_cell is not None for outcome in outcomes)
        and manifest.rejected_screened == sum(outcome.eligible_cell is None for outcome in outcomes)
        and manifest.rejection_reasons == dict(sorted(rejection_reasons.items()))
        and manifest.screening_cache_sha256 == screening_cache_sha256(root)
    )
    if not screening_valid:
        raise ValueError("Frozen pilot screening cache or summary has changed")

    registered_cells = sampling_cells(bound.frame)
    expected_coordinates = tuple(
        (cell.regional_route, cell.platform_id, cell.game_version_patch)
        for cell in registered_cells
    )
    observed_coordinates = tuple(
        (cell.regional_route, cell.platform_id, cell.game_version_patch) for cell in pool.cells
    )
    if observed_coordinates != expected_coordinates or len(manifest.cells) != len(pool.cells):
        raise ValueError("Frozen pilot selection does not contain the registered cell inventory")

    candidate_ids = {reference.match_id for reference in bound.ordered_candidates}
    selected_ids: set[str] = set()
    frozen: list[FrozenSelectedMatch] = []
    for registered, selected_cell, summary in zip(
        registered_cells,
        pool.cells,
        manifest.cells,
        strict=True,
    ):
        target = registered.pilot_target
        key = (
            registered.regional_route,
            registered.platform_id,
            registered.game_version_patch,
        )
        derived_selected = selected_by_cell[key]
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
            or len(derived_selected) != target
            or not summary_valid
        ):
            raise ValueError("Frozen pilot selection does not meet every exact cell quota")
        for entry, outcome in zip(selected_cell.selected, derived_selected, strict=True):
            if (
                entry.match_id in selected_ids
                or entry.match_id not in candidate_ids
                or not entry.match_id.startswith(f"{selected_cell.platform_id}_")
                or candidate_rank_sha256(bound.frame, entry.match_id) != entry.candidate_rank_sha256
                or _patch(entry.game_version) != selected_cell.game_version_patch
                or entry.match_id != outcome.match_id
                or entry.candidate_rank_sha256 != outcome.candidate_rank_sha256
                or entry.screen_record_sha256 != outcome.screen_record_sha256
                or entry.match_payload_sha256 != outcome.match_payload_sha256
                or entry.game_version != outcome.game_version
                or entry.game_creation_ms != outcome.game_creation_ms
            ):
                raise ValueError("Frozen selected-match identity or rank is invalid")
            selected_ids.add(entry.match_id)
            screen_path = root / "details" / selected_cell.regional_route / f"{entry.match_id}.json"
            try:
                screen_content = screen_path.read_bytes()
            except OSError as error:
                raise ValueError("A selected detail-screen record is missing") from error
            if _sha256(screen_content) != entry.screen_record_sha256:
                raise ValueError("A selected detail-screen checksum has changed")
            frozen.append(
                FrozenSelectedMatch(
                    match_id=entry.match_id,
                    regional_route=selected_cell.regional_route,
                    platform_id=selected_cell.platform_id,
                    game_version_patch=selected_cell.game_version_patch,
                    candidate_rank_sha256=entry.candidate_rank_sha256,
                    screen_record_sha256=entry.screen_record_sha256,
                    match_payload_sha256=entry.match_payload_sha256,
                    game_version=entry.game_version,
                    game_creation_ms=entry.game_creation_ms,
                    screen_record_path=screen_path,
                )
            )

    target_total = sum(cell.pilot_target for cell in registered_cells)
    if (
        len(frozen) != target_total
        or pool.selected_match_ids != target_total
        or manifest.selected_match_ids != target_total
        or manifest.eligible_screened < target_total
        or manifest.screened_match_ids != manifest.eligible_screened + manifest.rejected_screened
    ):
        raise ValueError("Frozen pilot selection total is inconsistent")

    expected_route_files: list[SelectedRouteFile] = []
    for route in bound.frame.route_platforms:
        route_ids = [
            entry.match_id for entry in frozen if entry.regional_route == route.regional_route
        ]
        expected_content = ("\n".join(route_ids) + "\n").encode()
        path = root / "selected-match-ids" / f"{route.regional_route}.txt"
        try:
            content = path.read_bytes()
        except OSError as error:
            raise ValueError("A frozen regional selected-ID file is missing") from error
        if content != expected_content:
            raise ValueError("A frozen regional selected-ID file has changed")
        expected_route_files.append(
            SelectedRouteFile(
                regional_route=route.regional_route,
                selected_count=len(route_ids),
                sha256=_sha256(content),
            )
        )
    expected_route_tuple = tuple(expected_route_files)
    if pool.route_files != expected_route_tuple or manifest.route_files != expected_route_tuple:
        raise ValueError("Frozen pilot regional file checksums are inconsistent")

    return FrozenPilotSelection(
        frame=bound.frame,
        frame_sha256=bound.frame_sha256,
        plan_id=bound.plan.plan_id,
        plan_sha256=bound.plan_sha256,
        discovery_manifest_sha256=bound.discovery_manifest_sha256,
        candidate_pool_sha256=bound.candidate_pool_sha256,
        selected_pool_sha256=pool_sha256,
        selected_matches=tuple(frozen),
    )


def validate_frozen_pilot_selection(
    sampling_frame_path: str | Path,
    discovery_plan_path: str | Path,
    discovery_root: str | Path,
    selection_root: str | Path,
) -> dict[str, object]:
    """Return an identifier-free validation report for the frozen pilot."""

    try:
        frozen = load_frozen_pilot_selection(
            sampling_frame_path,
            discovery_plan_path,
            discovery_root,
            selection_root,
        )
    except ValueError as error:
        return {
            "schema_version": FROZEN_SELECTION_VALIDATION_SCHEMA_VERSION,
            "passed": False,
            "checks": [
                {
                    "check_id": "frozen-selection-binding",
                    "passed": False,
                    "message": str(error),
                }
            ],
            "summary": None,
        }
    return {
        "schema_version": FROZEN_SELECTION_VALIDATION_SCHEMA_VERSION,
        "passed": True,
        "frame_id": frozen.frame.frame_id,
        "frame_sha256": frozen.frame_sha256,
        "selected_pool_sha256": frozen.selected_pool_sha256,
        "checks": [
            {
                "check_id": "frozen-selection-binding",
                "passed": True,
                "message": "All selected matches and route files retain their frozen checksums",
            },
            {
                "check_id": "exact-pilot-allocation",
                "passed": True,
                "message": "The frozen selection contains every exact registered pilot quota",
            },
        ],
        "summary": {
            "selected_match_ids": len(frozen.selected_matches),
            "registered_cells": len(sampling_cells(frozen.frame)),
            "identifiers_in_summary": False,
        },
    }


def pilot_collection_preflight(
    authority_record: str | Path,
    sampling_frame_path: str | Path,
    discovery_plan_path: str | Path,
    discovery_root: str | Path,
    selection_root: str | Path,
    *,
    environment: Mapping[str, str] | None = None,
    as_of: date | None = None,
) -> dict[str, object]:
    """Validate collection authority and the complete frozen selection offline."""

    authority = pilot_selection_preflight(
        authority_record,
        sampling_frame_path,
        discovery_plan_path,
        discovery_root,
        environment=environment,
        as_of=as_of,
    )
    selection = validate_frozen_pilot_selection(
        sampling_frame_path,
        discovery_plan_path,
        discovery_root,
        selection_root,
    )
    return {
        "schema_version": PILOT_COLLECTION_PREFLIGHT_SCHEMA_VERSION,
        "passed": bool(authority["passed"] and selection["passed"]),
        "authority": authority,
        "selection": selection,
    }


def _load_cached_match(
    frozen: FrozenPilotSelection,
    entry: FrozenSelectedMatch,
) -> tuple[bytes, Mapping[str, Any]]:
    content = entry.screen_record_path.read_bytes()
    if _sha256(content) != entry.screen_record_sha256:
        raise ValueError("A selected detail-screen checksum changed during collection")
    try:
        record = DetailScreenRecord.model_validate_json(content)
    except ValidationError as error:
        raise ValueError(
            f"Selected detail-screen schema rejected: {_safe_validation_error(error)}"
        ) from error
    expected = (
        record.fetch_status == "found"
        and record.payload is not None
        and record.frame_sha256 == frozen.frame_sha256
        and record.discovery_manifest_sha256 == frozen.discovery_manifest_sha256
        and record.candidate_pool_sha256 == frozen.candidate_pool_sha256
        and record.candidate_rank_sha256 == entry.candidate_rank_sha256
        and record.match_id == entry.match_id
        and record.regional_route == entry.regional_route
        and record.platform_id == entry.platform_id
    )
    if not expected:
        raise ValueError("Selected detail-screen record no longer matches its frozen entry")
    payload = cast(dict[str, Any], record.payload)
    payload_content = canonical_riot_json(payload)
    if _sha256(payload_content) != entry.match_payload_sha256:
        raise ValueError("Selected Match-V5 detail payload checksum has changed")
    return payload_content, payload


def _json_object(path: Path) -> tuple[bytes, Mapping[str, Any]]:
    content = path.read_bytes()
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("A registered-pilot raw file contains invalid JSON") from error
    if not isinstance(payload, Mapping):
        raise ValueError("A registered-pilot raw file is not a JSON object")
    return content, cast(Mapping[str, Any], payload)


def _record_matches_selection(record: CollectedMatch, entry: FrozenSelectedMatch) -> bool:
    return (
        record.match_id == entry.match_id
        and record.regional_route == entry.regional_route
        and record.game_version == entry.game_version
        and record.game_creation_ms == entry.game_creation_ms
        and record.match_sha256 == entry.match_payload_sha256
    )


def _existing_record(root: Path, entry: FrozenSelectedMatch) -> CollectedMatch:
    match_content, match_payload = _json_object(root / "matches" / f"{entry.match_id}.json")
    timeline_content, timeline_payload = _json_object(root / "timelines" / f"{entry.match_id}.json")
    try:
        record = collected_match_from_payloads(
            entry.match_id,
            regional_route=entry.regional_route,
            match_content=match_content,
            timeline_content=timeline_content,
            match_payload=match_payload,
            timeline_payload=timeline_payload,
        )
    except RiotAPIError:
        raise ValueError("An existing registered-pilot bundle is invalid") from None
    if not _record_matches_selection(record, entry):
        raise ValueError("An existing registered-pilot bundle differs from its selection")
    return record


def _discard_recoverable_partials(root: Path, selected_ids: set[str]) -> None:
    allowed_root_names = {
        "collection-manifest.json.partial",
        "selection-binding.json.partial",
        "collection-checkpoint.pending.partial",
    }
    for path in root.rglob("*.partial"):
        allowed = path.parent == root and path.name in allowed_root_names
        if path.parent.parent == root and path.parent.name in {"matches", "timelines"}:
            suffix = ".json.partial"
            match_id = path.name[: -len(suffix)] if path.name.endswith(suffix) else ""
            allowed = match_id in selected_ids and MATCH_ID_PATTERN.fullmatch(match_id) is not None
        if not allowed:
            raise ValueError("Registered-pilot output contains an unexpected partial file")
        path.unlink()


def _record_from_model(record: PilotRawBundleRecord) -> CollectedMatch:
    return CollectedMatch(**record.model_dump())


def _load_existing_checkpoint(
    root: Path,
    frozen: FrozenPilotSelection,
) -> dict[str, CollectedMatch]:
    manifest_path = root / "collection-manifest.json"
    binding_path = root / "selection-binding.json"
    pending_path = root / "collection-checkpoint.pending"
    pending: PilotCheckpointPending | None = None
    if pending_path.exists():
        try:
            pending = PilotCheckpointPending.model_validate_json(pending_path.read_bytes())
        except (OSError, ValidationError) as error:
            reason = (
                _safe_validation_error(error)
                if isinstance(error, ValidationError)
                else "unreadable"
            )
            raise ValueError(f"Registered-pilot checkpoint marker is invalid: {reason}") from error
        if pending.selected_pool_sha256 != frozen.selected_pool_sha256:
            raise ValueError("Registered-pilot checkpoint marker belongs to another selection")
    if not manifest_path.is_file():
        if binding_path.exists():
            raise ValueError("Registered-pilot binding exists without its collection manifest")
        return {}
    try:
        manifest_content = manifest_path.read_bytes()
        manifest = PilotRawCollectionManifest.model_validate_json(manifest_content)
    except (OSError, ValidationError) as error:
        reason = (
            _safe_validation_error(error) if isinstance(error, ValidationError) else "unreadable"
        )
        raise ValueError(f"Existing registered-pilot manifest is invalid: {reason}") from error

    available = tuple(_record_from_model(record) for record in manifest.available)
    collected_ids = tuple(record.match_id for record in manifest.collected)
    skipped_ids = manifest.skipped_existing
    available_ids = tuple(record.match_id for record in available)
    expected_entries = frozen.selected_matches[: len(available)]
    inventory_valid = (
        manifest.collected_at.tzinfo is not None
        and len(available) <= len(frozen.selected_matches)
        and manifest.requested == len(available)
        and len(available_ids) == len(set(available_ids))
        and len(collected_ids) == len(set(collected_ids))
        and len(skipped_ids) == len(set(skipped_ids))
        and not set(collected_ids).intersection(skipped_ids)
        and set(collected_ids).union(skipped_ids) == set(available_ids)
        and tuple(entry.match_id for entry in expected_entries) == available_ids
        and all(
            _record_matches_selection(record, entry)
            for record, entry in zip(available, expected_entries, strict=True)
        )
    )
    if not inventory_valid:
        raise ValueError("Existing registered-pilot manifest is not an exact selected prefix")

    manifest_sha256 = _sha256(manifest_content)
    pending_matches_manifest = (
        pending is not None
        and pending.collection_manifest_sha256 == manifest_sha256
        and pending.available_bundles == len(available)
    )
    if binding_path.is_file():
        try:
            binding = PilotCollectionBinding.model_validate_json(binding_path.read_bytes())
        except (OSError, ValidationError) as error:
            reason = (
                _safe_validation_error(error)
                if isinstance(error, ValidationError)
                else "unreadable"
            )
            raise ValueError(f"Existing registered-pilot binding is invalid: {reason}") from error
        binding_provenance_valid = (
            binding.recorded_at.tzinfo is not None
            and binding.frame_id == frozen.frame.frame_id
            and binding.frame_sha256 == frozen.frame_sha256
            and binding.plan_id == frozen.plan_id
            and binding.plan_sha256 == frozen.plan_sha256
            and binding.discovery_manifest_sha256 == frozen.discovery_manifest_sha256
            and binding.candidate_pool_sha256 == frozen.candidate_pool_sha256
            and binding.selected_pool_sha256 == frozen.selected_pool_sha256
            and binding.expected_selected_match_ids == len(frozen.selected_matches)
        )
        binding_matches_manifest = (
            binding.recorded_at == manifest.collected_at
            and binding.complete == (len(available) == len(frozen.selected_matches))
            and binding.collection_manifest_sha256 == manifest_sha256
            and binding.available_bundles == len(available)
            and binding.new_timeline_requests + binding.recovered_unpaired_bundles
            <= len(available)
        )
        if not binding_provenance_valid or not (
            binding_matches_manifest or pending_matches_manifest
        ):
            raise ValueError("Existing registered-pilot binding no longer matches its checkpoint")
    elif not pending_matches_manifest:
        raise ValueError("Registered-pilot manifest has no valid selection binding")
    return {record.match_id: record for record in available}


def _write_collection_outputs(
    root: Path,
    frozen: FrozenPilotSelection,
    *,
    timestamp: datetime,
    prior_records: list[CollectedMatch],
    new_records: list[CollectedMatch],
    new_timeline_requests: int,
    recovered_unpaired_bundles: int,
) -> dict[str, object]:
    available = [*prior_records, *new_records]
    manifest: dict[str, object] = {
        "schema_version": "riot-raw-collection-v2",
        "collected_at": timestamp.astimezone(UTC).isoformat(),
        "requested": len(available),
        "collected": [asdict(record) for record in new_records],
        "skipped_existing": [record.match_id for record in prior_records],
        "available": [asdict(record) for record in available],
        "contains_raw_player_identifiers": True,
        "redistribution": "not-authorized-by-this-manifest",
    }
    manifest_content = _canonical_json(manifest)
    manifest_sha256 = _sha256(manifest_content)
    pending = {
        "schema_version": PILOT_CHECKPOINT_PENDING_SCHEMA_VERSION,
        "selected_pool_sha256": frozen.selected_pool_sha256,
        "collection_manifest_sha256": manifest_sha256,
        "available_bundles": len(available),
    }
    _atomic_write(root / "collection-checkpoint.pending", _canonical_json(pending))
    _atomic_write(root / "collection-manifest.json", manifest_content)
    complete = len(available) == len(frozen.selected_matches)
    binding: dict[str, object] = {
        "schema_version": PILOT_COLLECTION_BINDING_SCHEMA_VERSION,
        "recorded_at": timestamp.astimezone(UTC).isoformat(),
        "complete": complete,
        "frame_id": frozen.frame.frame_id,
        "frame_sha256": frozen.frame_sha256,
        "plan_id": frozen.plan_id,
        "plan_sha256": frozen.plan_sha256,
        "discovery_manifest_sha256": frozen.discovery_manifest_sha256,
        "candidate_pool_sha256": frozen.candidate_pool_sha256,
        "selected_pool_sha256": frozen.selected_pool_sha256,
        "collection_manifest_sha256": manifest_sha256,
        "expected_selected_match_ids": len(frozen.selected_matches),
        "available_bundles": len(available),
        "new_timeline_requests": new_timeline_requests,
        "recovered_unpaired_bundles": recovered_unpaired_bundles,
        "identifiers_in_summary": False,
        "redistribution": "not-authorized",
    }
    _atomic_write(root / "selection-binding.json", _canonical_json(binding))
    (root / "collection-checkpoint.pending").unlink()
    return binding


def collect_selected_pilot_bundles(
    sampling_frame_path: str | Path,
    discovery_plan_path: str | Path,
    discovery_root: str | Path,
    selection_root: str | Path,
    *,
    output_root: str | Path,
    regional_fetchers: Mapping[str, TimelineFetcher],
    collected_at: datetime | None = None,
    max_new_requests: int | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, object]:
    """Reuse frozen details and fetch only timelines for the selected pilot."""

    if max_new_requests is not None and max_new_requests <= 0:
        raise ValueError("max_new_requests must be positive when supplied")
    frozen = load_frozen_pilot_selection(
        sampling_frame_path,
        discovery_plan_path,
        discovery_root,
        selection_root,
    )
    root = Path(output_root)
    resolved_root = root.resolve()
    private_roots = (Path(discovery_root).resolve(), Path(selection_root).resolve())
    if any(
        resolved_root == private_root
        or resolved_root in private_root.parents
        or private_root in resolved_root.parents
        for private_root in private_roots
    ):
        raise ValueError("Registered-pilot raw output requires a separate directory")
    timestamp = collected_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("collected_at must be timezone-aware")

    selected_ids = {entry.match_id for entry in frozen.selected_matches}
    _discard_recoverable_partials(root, selected_ids)
    checkpoint = _load_existing_checkpoint(root, frozen)
    match_files = {path.stem: path for path in (root / "matches").glob("*.json")}
    timeline_files = {path.stem: path for path in (root / "timelines").glob("*.json")}
    if set(match_files).union(timeline_files) - selected_ids:
        raise ValueError("Registered-pilot raw output contains an unselected bundle")
    if set(match_files) - set(timeline_files):
        raise ValueError("Registered-pilot raw output contains an unrecoverable match-only bundle")
    timeline_only = set(timeline_files) - set(match_files)
    if len(timeline_only) > 1:
        raise ValueError("Registered-pilot raw output contains multiple interrupted bundles")

    paired_ids = set(match_files).intersection(timeline_files)
    expected_prefix = tuple(entry.match_id for entry in frozen.selected_matches[: len(paired_ids)])
    if paired_ids != set(expected_prefix):
        raise ValueError("Registered-pilot bundles are not a contiguous selected prefix")
    if not set(checkpoint).issubset(paired_ids):
        raise ValueError("A checksum-bound registered-pilot checkpoint bundle is missing")
    if timeline_only:
        next_index = len(paired_ids)
        if next_index >= len(frozen.selected_matches) or timeline_only != {
            frozen.selected_matches[next_index].match_id
        }:
            raise ValueError("Interrupted timeline is not the next selected bundle")

    prior_records = [
        _existing_record(root, entry) for entry in frozen.selected_matches[: len(paired_ids)]
    ]
    if any(
        checkpoint.get(record.match_id, record) != record
        for record in prior_records
        if record.match_id in checkpoint
    ):
        raise ValueError("An existing registered-pilot bundle changed after checkpointing")
    new_records: list[CollectedMatch] = []
    recovered = 0
    start_index = len(prior_records)
    if timeline_only:
        entry = frozen.selected_matches[start_index]
        timeline_content, timeline_payload = _json_object(
            root / "timelines" / f"{entry.match_id}.json"
        )
        match_content, match_payload = _load_cached_match(frozen, entry)
        try:
            record = collected_match_from_payloads(
                entry.match_id,
                regional_route=entry.regional_route,
                match_content=match_content,
                timeline_content=timeline_content,
                match_payload=match_payload,
                timeline_payload=timeline_payload,
            )
        except RiotAPIError:
            raise ValueError("Interrupted registered-pilot bundle is invalid") from None
        if not _record_matches_selection(record, entry):
            raise ValueError("Interrupted bundle differs from its frozen selection")
        _atomic_write(root / "matches" / f"{entry.match_id}.json", match_content)
        new_records.append(record)
        recovered = 1
        start_index += 1

    new_requests = 0
    for entry in frozen.selected_matches[start_index:]:
        if max_new_requests is not None and new_requests >= max_new_requests:
            break
        fetcher = regional_fetchers.get(entry.regional_route)
        if fetcher is None:
            raise ValueError("Timeline clients do not cover every registered regional route")
        match_content, match_payload = _load_cached_match(frozen, entry)
        try:
            timeline_payload = fetcher.get_timeline(entry.match_id)
        except RiotAPIError:
            raise RiotAPIError(
                "A selected timeline request failed; no replacement was made"
            ) from None
        timeline_content = canonical_riot_json(timeline_payload)
        try:
            record = collected_match_from_payloads(
                entry.match_id,
                regional_route=entry.regional_route,
                match_content=match_content,
                timeline_content=timeline_content,
                match_payload=match_payload,
                timeline_payload=timeline_payload,
            )
        except RiotAPIError:
            raise RiotAPIError(
                "Fetched timeline identity or required metadata is invalid"
            ) from None
        if not _record_matches_selection(record, entry):
            raise RiotAPIError("Fetched bundle differs from its frozen pilot selection")
        _atomic_write(root / "timelines" / f"{entry.match_id}.json", timeline_content)
        _atomic_write(root / "matches" / f"{entry.match_id}.json", match_content)
        new_records.append(record)
        new_requests += 1
        available_count = len(prior_records) + len(new_records)
        if progress is not None and (
            new_requests % 100 == 0 or available_count == len(frozen.selected_matches)
        ):
            progress(
                f"Collected {available_count}/{len(frozen.selected_matches)} selected bundles; "
                f"new timeline requests {new_requests}"
            )

    return _write_collection_outputs(
        root,
        frozen,
        timestamp=timestamp,
        prior_records=prior_records,
        new_records=new_records,
        new_timeline_requests=new_requests,
        recovered_unpaired_bundles=recovered,
    )


def validate_pilot_collection_binding(
    raw_root: str | Path,
    sampling_frame_path: str | Path,
    discovery_plan_path: str | Path,
    discovery_root: str | Path,
    selection_root: str | Path,
    *,
    manifest_content: bytes,
    available_by_id: Mapping[str, RawRecordLike],
) -> dict[str, object]:
    """Verify that raw inventory exactly materializes the frozen selected pool."""

    try:
        frozen = load_frozen_pilot_selection(
            sampling_frame_path,
            discovery_plan_path,
            discovery_root,
            selection_root,
        )
        binding = PilotCollectionBinding.model_validate_json(
            (Path(raw_root) / "selection-binding.json").read_bytes()
        )
        manifest = PilotRawCollectionManifest.model_validate_json(manifest_content)
    except (OSError, ValueError, ValidationError) as error:
        message = (
            f"Pilot collection binding rejected: {_safe_validation_error(error)}"
            if isinstance(error, ValidationError)
            else "Pilot collection binding is missing, unreadable, or invalid"
        )
        return {"passed": False, "message": message, "summary": None}

    expected = {entry.match_id: entry for entry in frozen.selected_matches}
    inventory_valid = set(available_by_id) == set(expected) and all(
        (
            available_by_id[match_id].regional_route == entry.regional_route
            and available_by_id[match_id].game_version == entry.game_version
            and available_by_id[match_id].game_creation_ms == entry.game_creation_ms
            and available_by_id[match_id].match_sha256 == entry.match_payload_sha256
        )
        for match_id, entry in expected.items()
    )
    binding_valid = (
        binding.recorded_at.tzinfo is not None
        and binding.recorded_at == manifest.collected_at
        and binding.complete
        and binding.frame_id == frozen.frame.frame_id
        and binding.frame_sha256 == frozen.frame_sha256
        and binding.plan_id == frozen.plan_id
        and binding.plan_sha256 == frozen.plan_sha256
        and binding.discovery_manifest_sha256 == frozen.discovery_manifest_sha256
        and binding.candidate_pool_sha256 == frozen.candidate_pool_sha256
        and binding.selected_pool_sha256 == frozen.selected_pool_sha256
        and binding.collection_manifest_sha256 == _sha256(manifest_content)
        and binding.expected_selected_match_ids == len(expected)
        and binding.available_bundles == len(expected)
        and manifest.requested == len(expected)
        and binding.new_timeline_requests + binding.recovered_unpaired_bundles
        <= len(expected)
    )
    passed = inventory_valid and binding_valid
    return {
        "passed": passed,
        "message": (
            "Raw pilot inventory exactly materializes the checksum-bound frozen selection"
            if passed
            else "Raw pilot inventory or its selection binding does not match the frozen pilot"
        ),
        "summary": {
            "selected_pool_sha256": frozen.selected_pool_sha256,
            "expected_selected_match_ids": len(expected),
            "available_bundles": len(available_by_id),
            "identifiers_in_summary": False,
        },
    }
