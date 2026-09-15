"""Private, checksum-bound and resumable Riot candidate discovery."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any, Literal, Protocol, cast

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from league_ews.authority import DISCOVERY_ENDPOINTS, collection_preflight
from league_ews.riot import LadderTier
from league_ews.sampling import (
    SamplingFrame,
    load_registered_sampling_frame,
    order_candidate_match_ids,
    sampling_cells,
)

DISCOVERY_PLAN_SCHEMA_VERSION = "league-ews-candidate-discovery-plan-v1"
DISCOVERY_PLAN_VALIDATION_SCHEMA_VERSION = "league-ews-candidate-discovery-plan-validation-v1"
DISCOVERY_PREFLIGHT_SCHEMA_VERSION = "riot-candidate-discovery-preflight-v1"
LADDER_SNAPSHOT_SCHEMA_VERSION = "riot-ladder-snapshot-v1"
PLAYER_RESOLUTION_SCHEMA_VERSION = "riot-player-resolution-v1"
HISTORY_PAGE_SCHEMA_VERSION = "riot-match-history-page-v1"
CANDIDATE_POOL_SCHEMA_VERSION = "riot-candidate-pool-v1"
DISCOVERY_MANIFEST_SCHEMA_VERSION = "riot-candidate-discovery-manifest-v1"

REGISTERED_PLAN_ID = "rifthazard-pilot-discovery-2026-09-15"
REGISTERED_FRAME_ID = "rifthazard-2026-09-15"
REGISTERED_FRAME_SHA256 = "2355ec26182aa6862e8a110ff94f0ab402e9a4e77c0a52a0a5c81f1892033f6b"
REGISTERED_WAVE_SIZE = 32
REGISTERED_MAX_PLAYERS = 256
REGISTERED_HISTORY_COUNT = 100
REGISTERED_CANDIDATE_MULTIPLIER = 2

IdentifierKind = Literal["puuid", "summoner-id"]


class SamplingFrameBinding(BaseModel):
    """Immutable reference to the previously frozen sampling frame."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    frame_id: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class LadderDiscoveryPolicy(BaseModel):
    """Outcome-blind ordering and bounded player waves."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    member_identity: Literal["prefer-puuid-else-resolve-summoner-id-v1"]
    member_order: Literal["seeded-sha256-platform-kind-identifier-v1"]
    hash_material: Literal["decimal-seed-nul-platform-nul-kind-nul-identifier-utf8-v1"]
    wave_size_per_platform: int = Field(gt=0)
    max_players_per_platform: int = Field(gt=0)
    equal_platform_waves: Literal[True]


class MatchHistoryPolicy(BaseModel):
    """One bounded Match-V5 query for every player-patch pair."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    queue_id: Literal[420]
    start_index: Literal[0]
    count_per_player_window: int = Field(gt=0, le=100)
    patch_windows: Literal["sampling-frame-half-open-utc-v1"]
    pagination: Literal["one-bounded-page-per-player-window-v1"]


class DiscoveryStoppingPolicy(BaseModel):
    """Pre-detail stopping rule for the pilot candidate pool."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    stage: Literal["pilot"]
    candidate_multiplier_per_cell: int = Field(gt=1)
    rule: Literal["first-complete-balanced-wave-v1"]
    inspect_match_details_before_stop: Literal[False]
    inspect_labels_before_stop: Literal[False]


class DiscoveryOutputPolicy(BaseModel):
    """Private persistence and identifier-minimized reporting rules."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    storage: Literal["private"]
    snapshot: Literal["checksum-bound-canonical-json-v1"]
    resumable_history_cache: Literal[True]
    candidate_pool: Literal["globally-deduplicated-checksum-bound-v1"]
    identifiers_in_public_summary: Literal[False]


class DiscoveryPlan(BaseModel):
    """Executable supplement that closes the ladder-crawl stopping rule."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["league-ews-candidate-discovery-plan-v1"]
    plan_id: str
    frozen_on: date
    sampling_frame: SamplingFrameBinding
    ladder: LadderDiscoveryPolicy
    history: MatchHistoryPolicy
    stopping: DiscoveryStoppingPolicy
    outputs: DiscoveryOutputPolicy


@dataclass(frozen=True)
class DiscoveryCheck:
    check_id: str
    passed: bool
    message: str


class SnapshotMember(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identifier_kind: IdentifierKind
    identifier: str


class SnapshotTier(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tier: LadderTier
    members: tuple[SnapshotMember, ...]


class SnapshotPlatform(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    regional_route: str
    platform_id: str
    tiers: tuple[SnapshotTier, ...]


class LadderSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-ladder-snapshot-v1"]
    created_at: datetime
    frame_id: str
    frame_sha256: str
    plan_id: str
    plan_sha256: str
    platforms: tuple[SnapshotPlatform, ...]
    contains_player_identifiers: Literal[True]
    redistribution: Literal["not-authorized"]


class PlayerResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-player-resolution-v1"]
    frame_sha256: str
    plan_sha256: str
    snapshot_sha256: str
    platform_id: str
    player_key_sha256: str
    source_kind: IdentifierKind
    source_identifier: str
    puuid: str


class HistoryPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["riot-match-history-page-v1"]
    frame_sha256: str
    plan_sha256: str
    snapshot_sha256: str
    regional_route: str
    platform_id: str
    game_version_patch: str
    player_key_sha256: str
    start_time: int
    end_time: int
    queue_id: int
    start_index: int
    count_limit: int
    match_ids: tuple[str, ...]


class PlatformDiscoveryFetcher(Protocol):
    def get_top_league(
        self,
        tier: LadderTier,
        *,
        queue: str = "RANKED_SOLO_5x5",
    ) -> Mapping[str, Any]: ...

    def get_summoner_by_id(self, summoner_id: str) -> Mapping[str, Any]: ...


class RegionalDiscoveryFetcher(Protocol):
    def get_match_ids_by_puuid(
        self,
        puuid: str,
        *,
        start_time: int,
        end_time: int,
        queue_id: int,
        start: int = 0,
        count: int = 100,
    ) -> tuple[str, ...]: ...


def _check(
    check_id: str,
    passed: bool,
    success: str,
    failure: str,
) -> DiscoveryCheck:
    return DiscoveryCheck(check_id, passed, success if passed else failure)


def _safe_validation_error(error: ValidationError) -> str:
    issues = []
    for item in error.errors(include_input=False, include_context=False):
        location = ".".join(str(part) for part in item["loc"]) or "record"
        issues.append(f"{location}: {item['type']}")
    return "; ".join(issues)


def _load_plan_bytes(path: Path) -> tuple[bytes, DiscoveryPlan]:
    content = path.read_bytes()
    payload = yaml.safe_load(content)
    if not isinstance(payload, Mapping):
        raise ValueError("discovery plan must contain a mapping")
    return content, DiscoveryPlan.model_validate(payload)


def _plan_checks(
    plan: DiscoveryPlan,
    *,
    frame: SamplingFrame,
    frame_sha256: str,
) -> list[DiscoveryCheck]:
    ladder = plan.ladder
    history = plan.history
    stopping = plan.stopping
    return [
        DiscoveryCheck(
            "plan-schema",
            True,
            f"Discovery plan conforms to {DISCOVERY_PLAN_SCHEMA_VERSION}",
        ),
        _check(
            "sampling-frame-binding",
            plan.sampling_frame.frame_id == frame.frame_id == REGISTERED_FRAME_ID
            and plan.sampling_frame.sha256 == frame_sha256 == REGISTERED_FRAME_SHA256,
            "Discovery plan is bound to the exact frozen sampling frame",
            "Discovery plan does not match the frozen sampling frame bytes",
        ),
        _check(
            "freeze-stage",
            plan.plan_id == REGISTERED_PLAN_ID and plan.frozen_on == frame.frozen_on,
            "Discovery stopping rules were frozen before candidate requests",
            "Discovery plan identity or freeze date differs from the registered supplement",
        ),
        _check(
            "balanced-player-waves",
            ladder.wave_size_per_platform == REGISTERED_WAVE_SIZE
            and ladder.max_players_per_platform == REGISTERED_MAX_PLAYERS
            and ladder.max_players_per_platform % ladder.wave_size_per_platform == 0,
            "Ladder members are processed in equal deterministic 32-player waves",
            "Player-wave size or maximum differs from the registered discovery rule",
        ),
        _check(
            "bounded-history",
            history.queue_id == frame.eligibility.queue_id
            and history.count_per_player_window == REGISTERED_HISTORY_COUNT,
            "Every player-patch query is queue-bound and capped at 100 IDs",
            "Match-history query differs from the frozen queue or page cap",
        ),
        _check(
            "outcome-blind-stop",
            stopping.candidate_multiplier_per_cell == REGISTERED_CANDIDATE_MULTIPLIER
            and not stopping.inspect_match_details_before_stop
            and not stopping.inspect_labels_before_stop,
            "Discovery stops at the first balanced wave with a two-times cell buffer",
            "Discovery stopping could depend on details, labels or an unfrozen buffer",
        ),
    ]


def load_registered_discovery_plan(
    path: str | Path,
    *,
    frame: SamplingFrame,
    frame_sha256: str,
) -> tuple[DiscoveryPlan, str]:
    """Load one plan only when its exact sampling-frame binding passes."""

    try:
        content, plan = _load_plan_bytes(Path(path))
    except ValidationError as error:
        raise ValueError(
            f"discovery plan schema rejected: {_safe_validation_error(error)}"
        ) from error
    except yaml.YAMLError as error:
        raise ValueError("discovery plan contains invalid YAML") from error
    except OSError as error:
        raise ValueError("discovery plan is missing or unreadable") from error
    if not all(
        check.passed for check in _plan_checks(plan, frame=frame, frame_sha256=frame_sha256)
    ):
        raise ValueError("discovery plan fails the registered contract")
    return plan, hashlib.sha256(content).hexdigest()


def validate_discovery_plan(
    plan_path: str | Path,
    sampling_frame_path: str | Path,
) -> dict[str, object]:
    """Validate the discovery supplement without credentials or network access."""

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
        check = DiscoveryCheck("plan-schema", False, f"Discovery plan rejected: {reason}")
        return {
            "schema_version": DISCOVERY_PLAN_VALIDATION_SCHEMA_VERSION,
            "plan_id": None,
            "plan_sha256": None,
            "sampling_frame_sha256": None,
            "passed": False,
            "checks": [asdict(check)],
            "summary": None,
        }

    cells = sampling_cells(frame)
    return {
        "schema_version": DISCOVERY_PLAN_VALIDATION_SCHEMA_VERSION,
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
            "candidate_multiplier_per_cell": plan.stopping.candidate_multiplier_per_cell,
            "minimum_candidates_per_cell": [
                {
                    "regional_route": cell.regional_route,
                    "platform_id": cell.platform_id,
                    "game_version_patch": cell.game_version_patch,
                    "minimum_candidates": (
                        cell.pilot_target * plan.stopping.candidate_multiplier_per_cell
                    ),
                }
                for cell in cells
            ],
        },
    }


def candidate_discovery_preflight(
    authority_record: str | Path,
    sampling_frame_path: str | Path,
    discovery_plan_path: str | Path,
    *,
    environment: Mapping[str, str] | None = None,
    as_of: date | None = None,
) -> dict[str, object]:
    """Bind frame, plan, authority scope and runtime credential without a request."""

    try:
        frame, frame_sha256 = load_registered_sampling_frame(sampling_frame_path)
        plan, plan_sha256 = load_registered_discovery_plan(
            discovery_plan_path,
            frame=frame,
            frame_sha256=frame_sha256,
        )
    except ValueError as error:
        return {
            "schema_version": DISCOVERY_PREFLIGHT_SCHEMA_VERSION,
            "passed": False,
            "sampling_frame_sha256": None,
            "discovery_plan_sha256": None,
            "authority": None,
            "message": str(error),
        }

    authority = collection_preflight(
        authority_record,
        requested_regions=(route.regional_route for route in frame.route_platforms),
        required_endpoints=DISCOVERY_ENDPOINTS,
        environment=environment,
        as_of=as_of,
    )
    return {
        "schema_version": DISCOVERY_PREFLIGHT_SCHEMA_VERSION,
        "passed": bool(authority["passed"]),
        "sampling_frame_sha256": frame_sha256,
        "discovery_plan_sha256": plan_sha256,
        "plan_id": plan.plan_id,
        "authority": authority,
    }


def _canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_bytes(content)
    temporary.replace(path)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _safe_identifier(value: object, *, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Ladder response has no valid {name}")
    identifier = value.strip()
    if (
        not identifier
        or identifier != value
        or len(identifier) > 256
        or any(character.isspace() or ord(character) < 32 for character in identifier)
    ):
        raise ValueError(f"Ladder response has no valid {name}")
    return identifier


def _player_key_sha256(
    frame: SamplingFrame,
    *,
    platform_id: str,
    member: SnapshotMember,
) -> str:
    material = (
        f"{frame.selection.random_seed}\0{platform_id}\0"
        f"{member.identifier_kind}\0{member.identifier}"
    ).encode()
    return hashlib.sha256(material).hexdigest()


def _ordered_members(
    frame: SamplingFrame,
    platform: SnapshotPlatform,
) -> tuple[SnapshotMember, ...]:
    unique = {
        (member.identifier_kind, member.identifier): member
        for tier in platform.tiers
        for member in tier.members
    }
    return tuple(
        sorted(
            unique.values(),
            key=lambda member: (
                _player_key_sha256(frame, platform_id=platform.platform_id, member=member),
                member.identifier_kind,
                member.identifier,
            ),
        )
    )


def _snapshot_member(entry: Mapping[str, Any]) -> SnapshotMember:
    puuid = entry.get("puuid")
    if isinstance(puuid, str) and puuid:
        return SnapshotMember(
            identifier_kind="puuid",
            identifier=_safe_identifier(puuid, name="PUUID"),
        )
    return SnapshotMember(
        identifier_kind="summoner-id",
        identifier=_safe_identifier(entry.get("summonerId"), name="summoner ID"),
    )


def _fetch_ladder_snapshot(
    frame: SamplingFrame,
    *,
    frame_sha256: str,
    plan: DiscoveryPlan,
    plan_sha256: str,
    platform_fetchers: Mapping[str, PlatformDiscoveryFetcher],
    created_at: datetime,
) -> LadderSnapshot:
    platforms: list[SnapshotPlatform] = []
    for route in frame.route_platforms:
        fetcher = platform_fetchers.get(route.platform_id)
        if fetcher is None:
            raise ValueError(f"No platform client configured for {route.platform_id}")
        tiers: list[SnapshotTier] = []
        for raw_tier in frame.candidates.ladder_tiers:
            tier = raw_tier
            payload = fetcher.get_top_league(tier, queue=frame.candidates.ladder_queue)
            raw_entries = payload.get("entries")
            if not isinstance(raw_entries, list) or not raw_entries:
                raise ValueError(f"Riot returned no usable {tier} ladder entries")
            members = []
            for raw_entry in raw_entries:
                if not isinstance(raw_entry, Mapping):
                    raise ValueError(f"Riot returned a malformed {tier} ladder entry")
                members.append(_snapshot_member(cast(Mapping[str, Any], raw_entry)))
            tiers.append(
                SnapshotTier(
                    tier=tier,
                    members=tuple(
                        sorted(
                            dict.fromkeys(members),
                            key=lambda member: (member.identifier_kind, member.identifier),
                        )
                    ),
                )
            )
        platforms.append(
            SnapshotPlatform(
                regional_route=route.regional_route,
                platform_id=route.platform_id,
                tiers=tuple(tiers),
            )
        )
    return LadderSnapshot(
        schema_version="riot-ladder-snapshot-v1",
        created_at=created_at.astimezone(UTC),
        frame_id=frame.frame_id,
        frame_sha256=frame_sha256,
        plan_id=plan.plan_id,
        plan_sha256=plan_sha256,
        platforms=tuple(platforms),
        contains_player_identifiers=True,
        redistribution="not-authorized",
    )


def _load_or_create_snapshot(
    root: Path,
    frame: SamplingFrame,
    *,
    frame_sha256: str,
    plan: DiscoveryPlan,
    plan_sha256: str,
    platform_fetchers: Mapping[str, PlatformDiscoveryFetcher],
    created_at: datetime,
) -> tuple[LadderSnapshot, bytes]:
    path = root / "ladder-snapshot.json"
    if path.is_file():
        content = path.read_bytes()
        try:
            snapshot = LadderSnapshot.model_validate_json(content)
        except ValidationError as error:
            raise ValueError(
                f"Existing ladder snapshot rejected: {_safe_validation_error(error)}"
            ) from error
    else:
        snapshot = _fetch_ladder_snapshot(
            frame,
            frame_sha256=frame_sha256,
            plan=plan,
            plan_sha256=plan_sha256,
            platform_fetchers=platform_fetchers,
            created_at=created_at,
        )
        content = _canonical_json(snapshot.model_dump(mode="json"))
        _atomic_write(path, content)

    expected_pairs = tuple(
        (route.regional_route, route.platform_id) for route in frame.route_platforms
    )
    observed_pairs = tuple(
        (platform.regional_route, platform.platform_id) for platform in snapshot.platforms
    )
    if (
        snapshot.frame_id != frame.frame_id
        or snapshot.frame_sha256 != frame_sha256
        or snapshot.plan_id != plan.plan_id
        or snapshot.plan_sha256 != plan_sha256
        or observed_pairs != expected_pairs
        or snapshot.created_at.tzinfo is None
    ):
        raise ValueError("Existing ladder snapshot does not match the registered discovery run")
    required_tiers = frame.candidates.ladder_tiers
    if any(
        tuple(tier.tier for tier in platform.tiers) != required_tiers
        for platform in snapshot.platforms
    ):
        raise ValueError("Existing ladder snapshot has incomplete or reordered tiers")
    return snapshot, content


def _resolution_path(root: Path, platform_id: str, player_key: str) -> Path:
    return root / "resolutions" / platform_id / f"{player_key}.json"


def _resolve_player(
    root: Path,
    *,
    frame_sha256: str,
    plan_sha256: str,
    snapshot_sha256: str,
    platform_id: str,
    member: SnapshotMember,
    player_key: str,
    fetcher: PlatformDiscoveryFetcher,
) -> PlayerResolution:
    path = _resolution_path(root, platform_id, player_key)
    if path.is_file():
        try:
            resolution = PlayerResolution.model_validate_json(path.read_bytes())
        except ValidationError as error:
            raise ValueError(
                f"Existing player resolution rejected: {_safe_validation_error(error)}"
            ) from error
    else:
        if member.identifier_kind == "puuid":
            puuid = member.identifier
        else:
            payload = fetcher.get_summoner_by_id(member.identifier)
            puuid = _safe_identifier(payload.get("puuid"), name="resolved PUUID")
        resolution = PlayerResolution(
            schema_version="riot-player-resolution-v1",
            frame_sha256=frame_sha256,
            plan_sha256=plan_sha256,
            snapshot_sha256=snapshot_sha256,
            platform_id=platform_id,
            player_key_sha256=player_key,
            source_kind=member.identifier_kind,
            source_identifier=member.identifier,
            puuid=puuid,
        )
        _atomic_write(path, _canonical_json(resolution.model_dump(mode="json")))

    if (
        resolution.frame_sha256 != frame_sha256
        or resolution.plan_sha256 != plan_sha256
        or resolution.snapshot_sha256 != snapshot_sha256
        or resolution.platform_id != platform_id
        or resolution.player_key_sha256 != player_key
        or resolution.source_kind != member.identifier_kind
        or resolution.source_identifier != member.identifier
    ):
        raise ValueError("Existing player resolution does not match its snapshot member")
    _safe_identifier(resolution.puuid, name="resolved PUUID")
    return resolution


def _window_timestamp(value: date) -> int:
    return int(datetime.combine(value, time.min, tzinfo=UTC).timestamp())


def _history_path(
    root: Path,
    platform_id: str,
    game_version_patch: str,
    player_key: str,
) -> Path:
    return root / "histories" / platform_id / game_version_patch / f"{player_key}.json"


def _load_or_fetch_history(
    root: Path,
    *,
    frame_sha256: str,
    plan: DiscoveryPlan,
    plan_sha256: str,
    snapshot_sha256: str,
    regional_route: str,
    platform_id: str,
    game_version_patch: str,
    released_on: date,
    closed_on: date,
    player_key: str,
    puuid: str,
    fetcher: RegionalDiscoveryFetcher,
) -> HistoryPage:
    start_time = _window_timestamp(released_on)
    # Riot filters in whole epoch seconds. Subtracting one represents the
    # sampling frame's closed-date-exclusive boundary without overlapping the
    # next patch query at midnight.
    end_time = _window_timestamp(closed_on) - 1
    path = _history_path(root, platform_id, game_version_patch, player_key)
    if path.is_file():
        try:
            history = HistoryPage.model_validate_json(path.read_bytes())
        except ValidationError as error:
            raise ValueError(
                f"Existing match-history page rejected: {_safe_validation_error(error)}"
            ) from error
    else:
        match_ids = fetcher.get_match_ids_by_puuid(
            puuid,
            start_time=start_time,
            end_time=end_time,
            queue_id=plan.history.queue_id,
            start=plan.history.start_index,
            count=plan.history.count_per_player_window,
        )
        expected_prefix = f"{platform_id}_"
        if any(not match_id.startswith(expected_prefix) for match_id in match_ids):
            raise ValueError("Match history returned an ID for a different platform")
        history = HistoryPage(
            schema_version="riot-match-history-page-v1",
            frame_sha256=frame_sha256,
            plan_sha256=plan_sha256,
            snapshot_sha256=snapshot_sha256,
            regional_route=regional_route,
            platform_id=platform_id,
            game_version_patch=game_version_patch,
            player_key_sha256=player_key,
            start_time=start_time,
            end_time=end_time,
            queue_id=plan.history.queue_id,
            start_index=plan.history.start_index,
            count_limit=plan.history.count_per_player_window,
            match_ids=tuple(dict.fromkeys(match_ids)),
        )
        _atomic_write(path, _canonical_json(history.model_dump(mode="json")))

    expected = (
        history.frame_sha256 == frame_sha256
        and history.plan_sha256 == plan_sha256
        and history.snapshot_sha256 == snapshot_sha256
        and history.regional_route == regional_route
        and history.platform_id == platform_id
        and history.game_version_patch == game_version_patch
        and history.player_key_sha256 == player_key
        and history.start_time == start_time
        and history.end_time == end_time
        and history.queue_id == plan.history.queue_id
        and history.start_index == plan.history.start_index
        and history.count_limit == plan.history.count_per_player_window
        and len(history.match_ids) == len(set(history.match_ids))
        and all(match_id.startswith(f"{platform_id}_") for match_id in history.match_ids)
    )
    if not expected:
        raise ValueError("Existing match-history page does not match its registered query")
    return history


def _aggregate_digest(root: Path, paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        content = path.read_bytes()
        digest.update(str(path.relative_to(root)).encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(content).hexdigest().encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _candidate_pool(
    root: Path,
    frame: SamplingFrame,
    *,
    frame_sha256: str,
    plan: DiscoveryPlan,
    plan_sha256: str,
    snapshot_sha256: str,
    processed_members: Mapping[str, tuple[SnapshotMember, ...]],
) -> tuple[dict[str, object], list[dict[str, object]], bool]:
    assignments: dict[str, tuple[str, str, str]] = {}
    cells: list[dict[str, object]] = []
    target_by_cell = {
        (cell.regional_route, cell.platform_id, cell.game_version_patch): (
            cell.pilot_target * plan.stopping.candidate_multiplier_per_cell
        )
        for cell in sampling_cells(frame)
    }
    for patch in frame.patches:
        for route in frame.route_platforms:
            members = processed_members[route.platform_id]
            discovered: set[str] = set()
            for member in members:
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
                        "A completed discovery wave has a missing history page"
                    ) from error
                discovered.update(history.match_ids)

            key = (route.regional_route, route.platform_id, patch.game_version_patch)
            for match_id in discovered:
                prior = assignments.setdefault(match_id, key)
                if prior != key:
                    raise ValueError(
                        "One candidate match was returned for multiple discovery cells"
                    )
            ordered = order_candidate_match_ids(frame, tuple(discovered))
            minimum = target_by_cell[key]
            cells.append(
                {
                    "regional_route": route.regional_route,
                    "platform_id": route.platform_id,
                    "game_version_patch": patch.game_version_patch,
                    "minimum_candidates": minimum,
                    "candidate_count": len(ordered),
                    "minimum_met": len(ordered) >= minimum,
                    "match_ids": list(ordered),
                }
            )

    complete = all(bool(cell["minimum_met"]) for cell in cells)
    pool: dict[str, object] = {
        "schema_version": CANDIDATE_POOL_SCHEMA_VERSION,
        "frame_id": frame.frame_id,
        "frame_sha256": frame_sha256,
        "plan_id": plan.plan_id,
        "plan_sha256": plan_sha256,
        "snapshot_sha256": snapshot_sha256,
        "complete": complete,
        "globally_deduplicated": len(assignments)
        == sum(cast(int, cell["candidate_count"]) for cell in cells),
        "cells": cells,
        "contains_match_identifiers": True,
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
                "minimum_met",
            )
        }
        for cell in cells
    ]
    return pool, summaries, complete


def discover_candidate_pool(
    sampling_frame_path: str | Path,
    discovery_plan_path: str | Path,
    *,
    output_root: str | Path,
    platform_fetchers: Mapping[str, PlatformDiscoveryFetcher],
    regional_fetchers: Mapping[str, RegionalDiscoveryFetcher],
    discovered_at: datetime | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, object]:
    """Build or resume the private pre-detail candidate pool in equal waves."""

    frame, frame_sha256 = load_registered_sampling_frame(sampling_frame_path)
    plan, plan_sha256 = load_registered_discovery_plan(
        discovery_plan_path,
        frame=frame,
        frame_sha256=frame_sha256,
    )
    timestamp = discovered_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("discovered_at must be timezone-aware")
    root = Path(output_root)
    if list(root.rglob("*.partial")):
        raise ValueError("Candidate discovery contains an incomplete partial file")

    snapshot, snapshot_content = _load_or_create_snapshot(
        root,
        frame,
        frame_sha256=frame_sha256,
        plan=plan,
        plan_sha256=plan_sha256,
        platform_fetchers=platform_fetchers,
        created_at=timestamp,
    )
    snapshot_sha256 = _sha256(snapshot_content)
    if progress is not None:
        progress(f"Ladder snapshot ready for {len(snapshot.platforms)} platforms")

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
        raise ValueError("Ladder snapshot cannot supply one complete balanced player wave")

    complete = False
    pool: dict[str, object] = {}
    cell_summaries: list[dict[str, object]] = []
    players_processed = 0
    for wave_end in range(
        plan.ladder.wave_size_per_platform,
        maximum_balanced_players + 1,
        plan.ladder.wave_size_per_platform,
    ):
        for route in frame.route_platforms:
            platform_fetcher = platform_fetchers.get(route.platform_id)
            regional_fetcher = regional_fetchers.get(route.regional_route)
            if platform_fetcher is None or regional_fetcher is None:
                raise ValueError("Discovery clients do not cover every registered route-platform")
            members = ordered_by_platform[route.platform_id][:wave_end]
            for member in members[players_processed:wave_end]:
                player_key = _player_key_sha256(
                    frame,
                    platform_id=route.platform_id,
                    member=member,
                )
                resolution = _resolve_player(
                    root,
                    frame_sha256=frame_sha256,
                    plan_sha256=plan_sha256,
                    snapshot_sha256=snapshot_sha256,
                    platform_id=route.platform_id,
                    member=member,
                    player_key=player_key,
                    fetcher=platform_fetcher,
                )
                for patch in frame.patches:
                    _load_or_fetch_history(
                        root,
                        frame_sha256=frame_sha256,
                        plan=plan,
                        plan_sha256=plan_sha256,
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
            frame,
            frame_sha256=frame_sha256,
            plan=plan,
            plan_sha256=plan_sha256,
            snapshot_sha256=snapshot_sha256,
            processed_members=processed_members,
        )
        _atomic_write(root / "candidate-pool.json", _canonical_json(pool))
        if progress is not None:
            ready = sum(bool(cell["minimum_met"]) for cell in cell_summaries)
            progress(
                f"Balanced wave {wave_end // plan.ladder.wave_size_per_platform} complete: "
                f"{ready}/{len(cell_summaries)} candidate windows meet their buffer"
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
        raise ValueError("Candidate discovery cache inventory is inconsistent")
    pool_content = (root / "candidate-pool.json").read_bytes()
    manifest: dict[str, object] = {
        "schema_version": DISCOVERY_MANIFEST_SCHEMA_VERSION,
        "completed_at": timestamp.astimezone(UTC).isoformat(),
        "complete": complete,
        "frame_id": frame.frame_id,
        "frame_sha256": frame_sha256,
        "plan_id": plan.plan_id,
        "plan_sha256": plan_sha256,
        "ladder_snapshot_sha256": snapshot_sha256,
        "candidate_pool_sha256": _sha256(pool_content),
        "resolution_cache_sha256": _aggregate_digest(root, list(resolution_paths)),
        "history_cache_sha256": _aggregate_digest(root, list(history_paths)),
        "players_processed_per_platform": players_processed,
        "balanced_waves_completed": players_processed // plan.ladder.wave_size_per_platform,
        "resolution_files": len(resolution_paths),
        "history_page_files": len(history_paths),
        "candidate_match_ids": sum(cast(int, cell["candidate_count"]) for cell in cell_summaries),
        "candidate_windows": cell_summaries,
        "contains_player_identifiers_in_private_files": True,
        "identifiers_in_summary": False,
        "redistribution": "not-authorized",
    }
    _atomic_write(root / "discovery-manifest.json", _canonical_json(manifest))
    return manifest
