"""Selection-bound, resumable collection of the registered final sample."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from league_ews.authority import collection_preflight
from league_ews.final_selection import (
    FrozenFinalSelectedMatch,
    FrozenFinalSelection,
    load_frozen_final_selection,
    validate_frozen_final_selection,
)
from league_ews.pilot_collection import (
    PilotRawBundleRecord,
    PilotRawCollectionManifest,
    RawRecordLike,
)
from league_ews.riot import (
    CollectedMatch,
    RiotAPIError,
    canonical_riot_json,
    collected_match_from_payloads,
)
from league_ews.sampling import MATCH_ID_PATTERN
from league_ews.selection import DetailScreenRecord, _atomic_write, _canonical_json, _sha256

FINAL_COLLECTION_PREFLIGHT_SCHEMA_VERSION = "riot-final-collection-preflight-v1"
FINAL_COLLECTION_BINDING_SCHEMA_VERSION: Literal["riot-final-collection-binding-v1"] = (
    "riot-final-collection-binding-v1"
)
FINAL_CHECKPOINT_PENDING_SCHEMA_VERSION: Literal["riot-final-checkpoint-pending-v1"] = (
    "riot-final-checkpoint-pending-v1"
)
SHA256_PATTERN = r"^[0-9a-f]{64}$"


class TimelineFetcher(Protocol):
    def get_timeline(self, match_id: str) -> Mapping[str, Any]: ...


class FinalCollectionBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-final-collection-binding-v1"]
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
    selected_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    collection_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    expected_selected_match_ids: int = Field(gt=0)
    available_bundles: int = Field(ge=0)
    new_timeline_requests: int = Field(ge=0)
    recovered_unpaired_bundles: int = Field(ge=0)
    identifiers_in_summary: Literal[False]
    redistribution: Literal["not-authorized"]


class FinalCheckpointPending(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-final-checkpoint-pending-v1"]
    selected_pool_sha256: str = Field(pattern=SHA256_PATTERN)
    collection_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    available_bundles: int = Field(ge=0)


def _safe_validation_error(error: ValidationError) -> str:
    issues = []
    for item in error.errors(include_input=False, include_context=False):
        location = ".".join(str(part) for part in item["loc"]) or "document"
        issues.append(f"{location}: {item['type']}")
    return "; ".join(issues)


def final_collection_preflight(
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
    final_selection_root: str | Path,
    *,
    environment: Mapping[str, str] | None = None,
    as_of: date | None = None,
) -> dict[str, object]:
    """Validate timeline authority and the checksum-bound final selection."""

    selection = validate_frozen_final_selection(
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
    if not selection["passed"]:
        return {
            "schema_version": FINAL_COLLECTION_PREFLIGHT_SCHEMA_VERSION,
            "passed": False,
            "authority": None,
            "selection": selection,
        }
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
    authority = collection_preflight(
        authority_record,
        requested_regions=(route.regional_route for route in frozen.frame.route_platforms),
        required_endpoints=("match-v5.timeline",),
        environment=environment,
        as_of=as_of,
    )
    return {
        "schema_version": FINAL_COLLECTION_PREFLIGHT_SCHEMA_VERSION,
        "passed": bool(authority["passed"] and selection["passed"]),
        "authority": authority,
        "selection": selection,
    }


def _json_object(path: Path) -> tuple[bytes, Mapping[str, Any]]:
    content = path.read_bytes()
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("A registered-final raw file contains invalid JSON") from error
    if not isinstance(payload, Mapping):
        raise ValueError("A registered-final raw file is not a JSON object")
    return content, cast(Mapping[str, Any], payload)


def _load_cached_match(
    frozen: FrozenFinalSelection,
    entry: FrozenFinalSelectedMatch,
) -> tuple[bytes, Mapping[str, Any]]:
    content = entry.screen_record_path.read_bytes()
    if _sha256(content) != entry.screen_record_sha256:
        raise ValueError("A selected final detail checksum changed during collection")
    try:
        record = DetailScreenRecord.model_validate_json(content)
    except ValidationError as error:
        raise ValueError(
            f"Selected final detail schema rejected: {_safe_validation_error(error)}"
        ) from error
    valid = (
        record.fetch_status == "found"
        and record.payload is not None
        and record.frame_sha256 == frozen.frame_sha256
        and record.discovery_manifest_sha256 == frozen.final_discovery_manifest_sha256
        and record.candidate_pool_sha256 == frozen.candidate_pool_sha256
        and record.candidate_rank_sha256 == entry.candidate_rank_sha256
        and record.match_id == entry.match_id
        and record.regional_route == entry.regional_route
        and record.platform_id == entry.platform_id
    )
    if not valid:
        raise ValueError("Selected final detail no longer matches its frozen entry")
    payload = cast(dict[str, Any], record.payload)
    payload_content = canonical_riot_json(payload)
    if _sha256(payload_content) != entry.match_payload_sha256:
        raise ValueError("Selected final Match-V5 detail checksum has changed")
    return payload_content, payload


def _record_matches_selection(
    record: CollectedMatch,
    entry: FrozenFinalSelectedMatch,
) -> bool:
    return (
        record.match_id == entry.match_id
        and record.regional_route == entry.regional_route
        and record.game_version == entry.game_version
        and record.game_creation_ms == entry.game_creation_ms
        and record.match_sha256 == entry.match_payload_sha256
    )


def _existing_record(
    root: Path,
    entry: FrozenFinalSelectedMatch,
) -> CollectedMatch:
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
        raise ValueError("An existing registered-final bundle is invalid") from None
    if not _record_matches_selection(record, entry):
        raise ValueError("An existing registered-final bundle differs from its selection")
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
            raise ValueError("Registered-final output contains an unexpected partial file")
        path.unlink()


def _record_from_model(record: PilotRawBundleRecord) -> CollectedMatch:
    return CollectedMatch(**record.model_dump())


def _binding_provenance_valid(
    binding: FinalCollectionBinding,
    frozen: FrozenFinalSelection,
) -> bool:
    return (
        binding.recorded_at.tzinfo is not None
        and binding.frame_id == frozen.frame.frame_id
        and binding.frame_sha256 == frozen.frame_sha256
        and binding.selection_plan_id == frozen.selection_plan_id
        and binding.selection_plan_sha256 == frozen.selection_plan_sha256
        and binding.final_discovery_plan_sha256 == frozen.final_discovery_plan_sha256
        and binding.final_discovery_manifest_sha256 == frozen.final_discovery_manifest_sha256
        and binding.candidate_pool_sha256 == frozen.candidate_pool_sha256
        and binding.duration_rule_sha256 == frozen.duration_rule_sha256
        and binding.pilot_selected_pool_sha256 == frozen.pilot_selected_pool_sha256
        and binding.selected_pool_sha256 == frozen.selected_pool_sha256
        and binding.expected_selected_match_ids == len(frozen.selected_matches)
    )


def _load_existing_checkpoint(
    root: Path,
    frozen: FrozenFinalSelection,
) -> dict[str, CollectedMatch]:
    manifest_path = root / "collection-manifest.json"
    binding_path = root / "selection-binding.json"
    pending_path = root / "collection-checkpoint.pending"
    pending: FinalCheckpointPending | None = None
    if pending_path.exists():
        try:
            pending = FinalCheckpointPending.model_validate_json(pending_path.read_bytes())
        except (OSError, ValidationError) as error:
            reason = (
                _safe_validation_error(error)
                if isinstance(error, ValidationError)
                else "unreadable"
            )
            raise ValueError(f"Registered-final checkpoint marker is invalid: {reason}") from error
        if pending.selected_pool_sha256 != frozen.selected_pool_sha256:
            raise ValueError("Registered-final checkpoint belongs to another selection")
    if not manifest_path.is_file():
        if binding_path.exists():
            raise ValueError("Registered-final binding exists without its manifest")
        return {}
    try:
        manifest_content = manifest_path.read_bytes()
        manifest = PilotRawCollectionManifest.model_validate_json(manifest_content)
    except (OSError, ValidationError) as error:
        reason = (
            _safe_validation_error(error) if isinstance(error, ValidationError) else "unreadable"
        )
        raise ValueError(f"Existing registered-final manifest is invalid: {reason}") from error

    available = tuple(_record_from_model(record) for record in manifest.available)
    available_ids = tuple(record.match_id for record in available)
    collected_ids = tuple(record.match_id for record in manifest.collected)
    skipped_ids = manifest.skipped_existing
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
        raise ValueError("Existing registered-final manifest is not an exact selected prefix")

    manifest_sha256 = _sha256(manifest_content)
    pending_matches = (
        pending is not None
        and pending.collection_manifest_sha256 == manifest_sha256
        and pending.available_bundles == len(available)
    )
    if binding_path.is_file():
        try:
            binding = FinalCollectionBinding.model_validate_json(binding_path.read_bytes())
        except (OSError, ValidationError) as error:
            reason = (
                _safe_validation_error(error)
                if isinstance(error, ValidationError)
                else "unreadable"
            )
            raise ValueError(f"Existing registered-final binding is invalid: {reason}") from error
        binding_matches = (
            binding.recorded_at == manifest.collected_at
            and binding.complete == (len(available) == len(frozen.selected_matches))
            and binding.collection_manifest_sha256 == manifest_sha256
            and binding.available_bundles == len(available)
            and binding.new_timeline_requests + binding.recovered_unpaired_bundles <= len(available)
        )
        if not _binding_provenance_valid(binding, frozen) or not (
            binding_matches or pending_matches
        ):
            raise ValueError("Existing registered-final binding no longer matches its checkpoint")
    elif not pending_matches:
        raise ValueError("Registered-final manifest has no valid selection binding")
    return {record.match_id: record for record in available}


def _write_collection_outputs(
    root: Path,
    frozen: FrozenFinalSelection,
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
        "schema_version": FINAL_CHECKPOINT_PENDING_SCHEMA_VERSION,
        "selected_pool_sha256": frozen.selected_pool_sha256,
        "collection_manifest_sha256": manifest_sha256,
        "available_bundles": len(available),
    }
    _atomic_write(root / "collection-checkpoint.pending", _canonical_json(pending))
    _atomic_write(root / "collection-manifest.json", manifest_content)
    complete = len(available) == len(frozen.selected_matches)
    binding: dict[str, object] = {
        "schema_version": FINAL_COLLECTION_BINDING_SCHEMA_VERSION,
        "recorded_at": timestamp.astimezone(UTC).isoformat(),
        "complete": complete,
        "frame_id": frozen.frame.frame_id,
        "frame_sha256": frozen.frame_sha256,
        "selection_plan_id": frozen.selection_plan_id,
        "selection_plan_sha256": frozen.selection_plan_sha256,
        "final_discovery_plan_sha256": frozen.final_discovery_plan_sha256,
        "final_discovery_manifest_sha256": frozen.final_discovery_manifest_sha256,
        "candidate_pool_sha256": frozen.candidate_pool_sha256,
        "duration_rule_sha256": frozen.duration_rule_sha256,
        "pilot_selected_pool_sha256": frozen.pilot_selected_pool_sha256,
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


def collect_selected_final_bundles(
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
    *,
    output_root: str | Path,
    regional_fetchers: Mapping[str, TimelineFetcher],
    collected_at: datetime | None = None,
    max_new_requests: int | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, object]:
    """Reuse frozen details and fetch only timelines for the final sample."""

    if max_new_requests is not None and max_new_requests <= 0:
        raise ValueError("max_new_requests must be positive when supplied")
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
    root = Path(output_root)
    resolved_root = root.resolve()
    private_roots = tuple(
        Path(value).resolve()
        for value in (
            pilot_discovery_root,
            pilot_selection_root,
            final_discovery_root,
            final_selection_root,
        )
    )
    if any(
        resolved_root == private_root
        or resolved_root in private_root.parents
        or private_root in resolved_root.parents
        for private_root in private_roots
    ):
        raise ValueError("Registered-final raw output requires a separate directory")
    timestamp = collected_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("collected_at must be timezone-aware")

    selected_ids = {entry.match_id for entry in frozen.selected_matches}
    _discard_recoverable_partials(root, selected_ids)
    checkpoint = _load_existing_checkpoint(root, frozen)
    match_files = {path.stem: path for path in (root / "matches").glob("*.json")}
    timeline_files = {path.stem: path for path in (root / "timelines").glob("*.json")}
    if set(match_files).union(timeline_files) - selected_ids:
        raise ValueError("Registered-final output contains an unselected bundle")
    if set(match_files) - set(timeline_files):
        raise ValueError("Registered-final output contains an unrecoverable match-only bundle")
    timeline_only = set(timeline_files) - set(match_files)
    if len(timeline_only) > 1:
        raise ValueError("Registered-final output contains multiple interrupted bundles")

    paired_ids = set(match_files).intersection(timeline_files)
    expected_prefix = tuple(entry.match_id for entry in frozen.selected_matches[: len(paired_ids)])
    if paired_ids != set(expected_prefix):
        raise ValueError("Registered-final bundles are not a contiguous selected prefix")
    if not set(checkpoint).issubset(paired_ids):
        raise ValueError("A checksum-bound registered-final checkpoint bundle is missing")
    if timeline_only:
        next_index = len(paired_ids)
        if next_index >= len(frozen.selected_matches) or timeline_only != {
            frozen.selected_matches[next_index].match_id
        }:
            raise ValueError("Interrupted timeline is not the next selected final bundle")

    prior_records = [
        _existing_record(root, entry) for entry in frozen.selected_matches[: len(paired_ids)]
    ]
    if any(
        checkpoint.get(record.match_id, record) != record
        for record in prior_records
        if record.match_id in checkpoint
    ):
        raise ValueError("An existing registered-final bundle changed after checkpointing")
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
            raise ValueError("Interrupted registered-final bundle is invalid") from None
        if not _record_matches_selection(record, entry):
            raise ValueError("Interrupted final bundle differs from its frozen selection")
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
            raise ValueError("Timeline clients do not cover every final regional route")
        match_content, match_payload = _load_cached_match(frozen, entry)
        try:
            timeline_payload = fetcher.get_timeline(entry.match_id)
        except RiotAPIError:
            raise RiotAPIError(
                "A selected final timeline request failed; no replacement was made"
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
                "Fetched final timeline identity or required metadata is invalid"
            ) from None
        if not _record_matches_selection(record, entry):
            raise RiotAPIError("Fetched bundle differs from its frozen final selection")
        _atomic_write(root / "timelines" / f"{entry.match_id}.json", timeline_content)
        _atomic_write(root / "matches" / f"{entry.match_id}.json", match_content)
        new_records.append(record)
        new_requests += 1
        available_count = len(prior_records) + len(new_records)
        if progress is not None and (
            new_requests % 100 == 0 or available_count == len(frozen.selected_matches)
        ):
            progress(
                f"Collected {available_count}/{len(frozen.selected_matches)} final bundles; "
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


def validate_final_collection_binding(
    raw_root: str | Path,
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
    *,
    manifest_content: bytes,
    available_by_id: Mapping[str, RawRecordLike],
) -> dict[str, object]:
    """Verify that raw inventory exactly materializes the final selected pool."""

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
        binding = FinalCollectionBinding.model_validate_json(
            (Path(raw_root) / "selection-binding.json").read_bytes()
        )
        manifest = PilotRawCollectionManifest.model_validate_json(manifest_content)
    except (OSError, ValueError, ValidationError) as error:
        message = (
            f"Final collection binding rejected: {_safe_validation_error(error)}"
            if isinstance(error, ValidationError)
            else "Final collection binding is missing, unreadable, or invalid"
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
        _binding_provenance_valid(binding, frozen)
        and binding.recorded_at == manifest.collected_at
        and binding.complete
        and binding.collection_manifest_sha256 == _sha256(manifest_content)
        and binding.available_bundles == len(expected)
        and manifest.requested == len(expected)
        and binding.new_timeline_requests + binding.recovered_unpaired_bundles <= len(expected)
    )
    passed = inventory_valid and binding_valid
    return {
        "passed": passed,
        "message": (
            "Raw final inventory exactly materializes the checksum-bound final selection"
            if passed
            else "Raw final inventory or its binding does not match the final selection"
        ),
        "summary": {
            "selected_pool_sha256": frozen.selected_pool_sha256,
            "expected_selected_match_ids": len(expected),
            "available_bundles": len(available_by_id),
            "identifiers_in_summary": False,
        },
    }
