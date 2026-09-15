"""Small, auditable Riot Match-V5 client and resumable raw collector."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol, Self, cast
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

REGIONAL_ROUTES = frozenset({"americas", "asia", "europe", "sea"})
PLATFORM_ROUTES = frozenset(
    {
        "br1",
        "eun1",
        "euw1",
        "jp1",
        "kr",
        "la1",
        "la2",
        "na1",
        "oc1",
        "ph2",
        "ru",
        "sg2",
        "th2",
        "tr1",
        "tw2",
        "vn2",
    }
)
MATCH_ID_PATTERN = re.compile(r"^[A-Z0-9]+_[0-9]+$")
RIOT_API_USER_AGENT = "league-ews-research/0.1"
LadderTier = Literal["CHALLENGER", "GRANDMASTER", "MASTER"]


class RiotAPIError(RuntimeError):
    """A sanitized Riot API failure that never contains credentials."""


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 5
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if (
            not math.isfinite(self.base_delay_seconds)
            or not math.isfinite(self.max_delay_seconds)
            or self.base_delay_seconds < 0
            or self.max_delay_seconds < 0
        ):
            raise ValueError("retry delays must be finite and non-negative")


class MatchFetcher(Protocol):
    def get_match(self, match_id: str) -> Mapping[str, Any]: ...

    def get_timeline(self, match_id: str) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class TransportResponse:
    status_code: int
    body: bytes
    headers: Mapping[str, str]


class HTTPTransport(Protocol):
    def get(self, url: str, *, headers: Mapping[str, str]) -> TransportResponse: ...


class UrllibTransport:
    """Standard-library HTTPS transport so collection adds no runtime dependency."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._timeout_seconds = timeout_seconds

    def get(self, url: str, *, headers: Mapping[str, str]) -> TransportResponse:
        request = Request(url, headers=dict(headers))
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                return TransportResponse(
                    status_code=int(response.status),
                    body=response.read(),
                    headers=dict(response.headers.items()),
                )
        except HTTPError as error:
            return TransportResponse(
                status_code=error.code,
                body=error.read(),
                headers=dict(error.headers.items()),
            )


class RequestPacer:
    """Conservatively space sequential calls across Riot endpoint families."""

    def __init__(
        self,
        interval_seconds: float = 1.25,
        *,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not math.isfinite(interval_seconds) or interval_seconds < 0:
            raise ValueError("request interval must be finite and non-negative")
        self._interval_seconds = interval_seconds
        self._sleep = sleep
        self._clock = clock
        self._last_request: float | None = None

    def __call__(self) -> None:
        now = self._clock()
        if self._last_request is not None:
            delay = self._interval_seconds - (now - self._last_request)
            if delay > 0:
                self._sleep(delay)
                now = self._clock()
        self._last_request = now


class _RiotAPIClient:
    """Shared authenticated JSON transport with bounded retry behavior."""

    def __init__(
        self,
        api_key: str,
        *,
        routing_value: str,
        allowed_routes: frozenset[str],
        retry_policy: RetryPolicy | None = None,
        transport: HTTPTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        pace: Callable[[], None] | None = None,
    ) -> None:
        route = routing_value.lower()
        if route not in allowed_routes:
            raise ValueError(f"Unsupported Riot route: {routing_value}")
        if not api_key.strip():
            raise ValueError("A non-empty Riot API key is required")
        self._api_key = api_key
        self._route = route
        self._retry = retry_policy or RetryPolicy()
        self._transport = transport or UrllibTransport()
        self._sleep = sleep
        self._pace = pace

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Retained for a stable context-manager API; the transport is stateless."""

    def _request_json(self, path: str, *, safe_endpoint: str) -> object:
        url = f"https://{self._route}.api.riotgames.com{path}"
        for attempt in range(1, self._retry.max_attempts + 1):
            if self._pace is not None:
                self._pace()
            try:
                response = self._transport.get(
                    url,
                    headers={
                        "User-Agent": RIOT_API_USER_AGENT,
                        "X-Riot-Token": self._api_key,
                    },
                )
            except OSError:
                raise RiotAPIError(f"Riot API transport failed for {safe_endpoint}") from None
            if response.status_code == 200:
                try:
                    payload = json.loads(response.body)
                except json.JSONDecodeError as error:
                    raise RiotAPIError("Riot API returned invalid JSON") from error
                return payload
            retriable = response.status_code == 429 or response.status_code >= 500
            if not retriable or attempt == self._retry.max_attempts:
                raise RiotAPIError(
                    f"Riot API request failed with HTTP {response.status_code} for {safe_endpoint}"
                )
            retry_after = response.headers.get("Retry-After")
            try:
                delay = float(retry_after) if retry_after is not None else None
            except ValueError:
                delay = None
            if delay is None or not math.isfinite(delay) or delay < 0:
                delay = self._retry.base_delay_seconds * (2 ** (attempt - 1))
            self._sleep(min(delay, self._retry.max_delay_seconds))
        raise AssertionError("bounded retry loop terminated unexpectedly")

    def _request_object(self, path: str, *, safe_endpoint: str) -> Mapping[str, Any]:
        payload = self._request_json(path, safe_endpoint=safe_endpoint)
        if not isinstance(payload, Mapping):
            raise RiotAPIError("Riot API returned a non-object JSON payload")
        return cast(Mapping[str, Any], payload)

    def _request_list(self, path: str, *, safe_endpoint: str) -> list[object]:
        payload = self._request_json(path, safe_endpoint=safe_endpoint)
        if not isinstance(payload, list):
            raise RiotAPIError("Riot API returned a non-list JSON payload")
        return cast(list[object], payload)


class RiotMatchClient(_RiotAPIClient):
    """Synchronous regional Match-V5 client."""

    def __init__(
        self,
        api_key: str,
        *,
        regional_route: str,
        retry_policy: RetryPolicy | None = None,
        transport: HTTPTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        pace: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(
            api_key,
            routing_value=regional_route,
            allowed_routes=REGIONAL_ROUTES,
            retry_policy=retry_policy,
            transport=transport,
            sleep=sleep,
            pace=pace,
        )

    @classmethod
    def from_environment(
        cls,
        *,
        regional_route: str,
        pace: Callable[[], None] | None = None,
    ) -> Self:
        key = os.environ.get("RIOT_API_KEY", "")
        if not key:
            raise RuntimeError("RIOT_API_KEY is not configured")
        return cls(key, regional_route=regional_route, pace=pace)

    def get_match(self, match_id: str) -> Mapping[str, Any]:
        _validate_match_id(match_id)
        return self._request_object(
            f"/lol/match/v5/matches/{match_id}",
            safe_endpoint="match-v5.match",
        )

    def get_timeline(self, match_id: str) -> Mapping[str, Any]:
        _validate_match_id(match_id)
        return self._request_object(
            f"/lol/match/v5/matches/{match_id}/timeline",
            safe_endpoint="match-v5.timeline",
        )

    def get_match_ids_by_puuid(
        self,
        puuid: str,
        *,
        start_time: int,
        end_time: int,
        queue_id: int,
        start: int = 0,
        count: int = 100,
    ) -> tuple[str, ...]:
        """Return one explicitly bounded Match-V5 history page."""

        identifier = _validate_opaque_identifier(puuid, name="PUUID")
        if start_time < 0 or end_time <= start_time:
            raise ValueError("Match-history timestamps must form a positive half-open window")
        if queue_id <= 0 or start < 0 or not 1 <= count <= 100:
            raise ValueError("Invalid Match-V5 history pagination or queue parameters")
        query = urlencode(
            {
                "startTime": start_time,
                "endTime": end_time,
                "queue": queue_id,
                "start": start,
                "count": count,
            }
        )
        payload = self._request_list(
            f"/lol/match/v5/matches/by-puuid/{quote(identifier, safe='')}/ids?{query}",
            safe_endpoint="match-v5.ids-by-puuid",
        )
        match_ids = tuple(str(item) for item in payload)
        if any(not isinstance(item, str) for item in payload):
            raise RiotAPIError("Riot API returned a malformed match-ID list")
        for match_id in match_ids:
            _validate_match_id(match_id)
        return match_ids


class RiotPlatformClient(_RiotAPIClient):
    """Synchronous platform-routed League-V4 and Summoner-V4 client."""

    def __init__(
        self,
        api_key: str,
        *,
        platform_id: str,
        retry_policy: RetryPolicy | None = None,
        transport: HTTPTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        pace: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(
            api_key,
            routing_value=platform_id,
            allowed_routes=PLATFORM_ROUTES,
            retry_policy=retry_policy,
            transport=transport,
            sleep=sleep,
            pace=pace,
        )

    @classmethod
    def from_environment(
        cls,
        *,
        platform_id: str,
        pace: Callable[[], None] | None = None,
    ) -> Self:
        key = os.environ.get("RIOT_API_KEY", "")
        if not key:
            raise RuntimeError("RIOT_API_KEY is not configured")
        return cls(key, platform_id=platform_id, pace=pace)

    def get_top_league(
        self,
        tier: LadderTier,
        *,
        queue: str = "RANKED_SOLO_5x5",
    ) -> Mapping[str, Any]:
        paths = {
            "CHALLENGER": "challengerleagues",
            "GRANDMASTER": "grandmasterleagues",
            "MASTER": "masterleagues",
        }
        if tier not in paths:
            raise ValueError(f"Unsupported ladder tier: {tier}")
        if queue != "RANKED_SOLO_5x5":
            raise ValueError("Only the frozen Ranked Solo ladder queue is supported")
        return self._request_object(
            f"/lol/league/v4/{paths[tier]}/by-queue/{queue}",
            safe_endpoint=f"league-v4.{tier.lower()}",
        )

    def get_summoner_by_id(self, summoner_id: str) -> Mapping[str, Any]:
        identifier = _validate_opaque_identifier(summoner_id, name="summoner ID")
        return self._request_object(
            f"/lol/summoner/v4/summoners/{quote(identifier, safe='')}",
            safe_endpoint="summoner-v4.by-summoner-id",
        )


@dataclass(frozen=True)
class CollectedMatch:
    match_id: str
    regional_route: str
    game_version: str
    game_creation_ms: int
    match_sha256: str
    timeline_sha256: str


def _validate_match_id(match_id: str) -> None:
    if not MATCH_ID_PATTERN.fullmatch(match_id):
        raise ValueError(f"Unsafe or malformed match ID: {match_id!r}")


def _validate_opaque_identifier(value: str, *, name: str) -> str:
    identifier = value.strip()
    if (
        not identifier
        or len(identifier) > 256
        or identifier != value
        or any(character.isspace() or ord(character) < 32 for character in identifier)
    ):
        raise ValueError(f"Unsafe or malformed {name}")
    return identifier


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_bytes(content)
    temporary.replace(path)


def _payload_match_id(payload: Mapping[str, Any]) -> str:
    metadata = payload.get("metadata")
    if not isinstance(metadata, Mapping):
        return ""
    return str(metadata.get("matchId", ""))


def _json_object(path: Path) -> tuple[bytes, Mapping[str, Any]]:
    content = path.read_bytes()
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {path.name}") from error
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected a JSON object in {path.name}")
    return content, payload


def _bundle_record(
    match_id: str,
    *,
    regional_route: str,
    match_content: bytes,
    timeline_content: bytes,
    match_payload: Mapping[str, Any],
    timeline_payload: Mapping[str, Any],
) -> CollectedMatch:
    if (
        _payload_match_id(match_payload) != match_id
        or _payload_match_id(timeline_payload) != match_id
    ):
        raise RiotAPIError(f"Payload identity mismatch for {match_id}")
    info = match_payload.get("info")
    safe_info = info if isinstance(info, Mapping) else {}
    game_version = str(safe_info.get("gameVersion", ""))
    try:
        game_creation_ms = int(safe_info.get("gameCreation", 0))
    except (TypeError, ValueError) as error:
        raise RiotAPIError("Payload has invalid required match metadata") from error
    if not re.fullmatch(r"\d+\.\d+(?:\.\d+)*", game_version) or game_creation_ms <= 0:
        raise RiotAPIError("Payload is missing required match version or creation metadata")
    return CollectedMatch(
        match_id=match_id,
        regional_route=regional_route,
        game_version=game_version,
        game_creation_ms=game_creation_ms,
        match_sha256=hashlib.sha256(match_content).hexdigest(),
        timeline_sha256=hashlib.sha256(timeline_content).hexdigest(),
    )


def _previous_records(root: Path) -> dict[str, CollectedMatch]:
    manifest_path = root / "collection-manifest.json"
    if not manifest_path.is_file():
        return {}
    _, payload = _json_object(manifest_path)
    if payload.get("schema_version") != "riot-raw-collection-v2":
        return {}
    available = payload.get("available")
    if not isinstance(available, list):
        raise ValueError("Existing v2 collection manifest has no available inventory")
    records: dict[str, CollectedMatch] = {}
    for raw_entry in available:
        if not isinstance(raw_entry, Mapping):
            raise ValueError("Existing v2 collection manifest has an invalid entry")
        try:
            record = CollectedMatch(
                match_id=str(raw_entry.get("match_id", "")),
                regional_route=str(raw_entry.get("regional_route", "")),
                game_version=str(raw_entry.get("game_version", "")),
                game_creation_ms=int(raw_entry.get("game_creation_ms", -1)),
                match_sha256=str(raw_entry.get("match_sha256", "")),
                timeline_sha256=str(raw_entry.get("timeline_sha256", "")),
            )
        except (TypeError, ValueError) as error:
            raise ValueError("Existing v2 collection manifest has an invalid entry") from error
        _validate_match_id(record.match_id)
        valid_hashes = all(
            re.fullmatch(r"[0-9a-f]{64}", value)
            for value in (record.match_sha256, record.timeline_sha256)
        )
        if (
            record.regional_route not in REGIONAL_ROUTES
            or not record.game_version
            or record.game_creation_ms <= 0
            or not valid_hashes
            or record.match_id in records
        ):
            raise ValueError("Existing v2 collection manifest has invalid bundle metadata")
        records[record.match_id] = record
    return records


def _read_bundle_record(
    root: Path,
    match_id: str,
    *,
    regional_route: str,
) -> CollectedMatch:
    match_content, match_payload = _json_object(root / "matches" / f"{match_id}.json")
    timeline_content, timeline_payload = _json_object(root / "timelines" / f"{match_id}.json")
    return _bundle_record(
        match_id,
        regional_route=regional_route,
        match_content=match_content,
        timeline_content=timeline_content,
        match_payload=match_payload,
        timeline_payload=timeline_payload,
    )


def collect_match_bundles(
    match_ids: Iterable[str],
    *,
    regional_route: str,
    output_root: str | Path,
    fetcher: MatchFetcher,
    overwrite: bool = False,
    collected_at: datetime | None = None,
) -> dict[str, object]:
    """Fetch match/timeline pairs atomically and write a privacy-minimal manifest."""

    route = regional_route.lower()
    if route not in REGIONAL_ROUTES:
        raise ValueError(f"Unsupported regional route: {regional_route}")
    identifiers = tuple(
        dict.fromkeys(match_id.strip() for match_id in match_ids if match_id.strip())
    )
    if not identifiers:
        raise ValueError("At least one match ID is required")
    for match_id in identifiers:
        _validate_match_id(match_id)

    root = Path(output_root)
    previous_records = _previous_records(root)
    requested_ids = set(identifiers)
    if list(root.rglob("*.partial")):
        raise ValueError("Raw collection contains incomplete partial files")
    match_files = {path.stem: path for path in (root / "matches").glob("*.json")}
    timeline_files = {path.stem: path for path in (root / "timelines").glob("*.json")}
    if set(match_files) != set(timeline_files):
        raise ValueError("Raw collection contains unpaired match/timeline files")
    overwrite_ids = requested_ids if overwrite else set()
    for match_id in match_files:
        _validate_match_id(match_id)
        prior_record = previous_records.get(match_id)
        if prior_record is None:
            if match_id not in overwrite_ids:
                raise ValueError("Raw collection contains an untracked existing bundle")
            continue
        if match_id in requested_ids and prior_record.regional_route != route:
            raise ValueError("A resumed bundle cannot change regional route")
        if match_id not in overwrite_ids:
            existing_record = _read_bundle_record(
                root,
                match_id,
                regional_route=prior_record.regional_route,
            )
            if existing_record != prior_record:
                raise ValueError("Existing bundle differs from its recorded manifest")

    collected: list[CollectedMatch] = []
    skipped: list[str] = []
    for match_id in identifiers:
        match_path = root / "matches" / f"{match_id}.json"
        timeline_path = root / "timelines" / f"{match_id}.json"
        if not overwrite and match_path.is_file() and timeline_path.is_file():
            skipped.append(match_id)
            continue

        match_payload = fetcher.get_match(match_id)
        timeline_payload = fetcher.get_timeline(match_id)
        match_bytes = _canonical_json(match_payload)
        timeline_bytes = _canonical_json(timeline_payload)
        record = _bundle_record(
            match_id,
            regional_route=route,
            match_content=match_bytes,
            timeline_content=timeline_bytes,
            match_payload=match_payload,
            timeline_payload=timeline_payload,
        )
        _atomic_write(match_path, match_bytes)
        _atomic_write(timeline_path, timeline_bytes)
        collected.append(record)

    if list(root.rglob("*.partial")):
        raise ValueError("Raw collection contains incomplete partial files")
    match_files = {path.stem: path for path in (root / "matches").glob("*.json")}
    timeline_files = {path.stem: path for path in (root / "timelines").glob("*.json")}
    if set(match_files) != set(timeline_files):
        raise ValueError("Raw collection contains unpaired match/timeline files")

    collected_ids = {record.match_id for record in collected}
    available: list[CollectedMatch] = []
    for match_id in sorted(match_files):
        _validate_match_id(match_id)
        prior_record = previous_records.get(match_id)
        prior_route = prior_record.regional_route if prior_record is not None else None
        if match_id in requested_ids:
            if prior_route is not None and prior_route != route:
                raise ValueError("A resumed bundle cannot change regional route")
            bundle_route = route
        elif prior_route is not None:
            bundle_route = prior_route
        else:
            raise ValueError("Raw collection contains an untracked existing bundle")
        record = _read_bundle_record(
            root,
            match_id,
            regional_route=bundle_route,
        )
        if prior_record is not None and match_id not in collected_ids and record != prior_record:
            raise ValueError("Existing bundle differs from its recorded manifest")
        available.append(record)

    timestamp = collected_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("collected_at must be timezone-aware")
    manifest: dict[str, object] = {
        "schema_version": "riot-raw-collection-v2",
        "collected_at": timestamp.astimezone(UTC).isoformat(),
        "requested": len(identifiers),
        "collected": [asdict(record) for record in collected],
        "skipped_existing": skipped,
        "available": [asdict(record) for record in available],
        "contains_raw_player_identifiers": True,
        "redistribution": "not-authorized-by-this-manifest",
    }
    _atomic_write(root / "collection-manifest.json", _canonical_json(manifest))
    return manifest
