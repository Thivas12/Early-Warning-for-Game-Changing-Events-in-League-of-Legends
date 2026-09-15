"""Small, auditable Riot Match-V5 client and resumable raw collector."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, Self
from urllib.error import HTTPError
from urllib.request import Request, urlopen

REGIONAL_ROUTES = frozenset({"americas", "asia", "europe", "sea"})
MATCH_ID_PATTERN = re.compile(r"^[A-Z0-9]+_[0-9]+$")


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
        if self.base_delay_seconds < 0 or self.max_delay_seconds < 0:
            raise ValueError("retry delays cannot be negative")


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


class RiotMatchClient:
    """Synchronous Match-V5 client with bounded 429/5xx retry handling."""

    def __init__(
        self,
        api_key: str,
        *,
        regional_route: str,
        retry_policy: RetryPolicy | None = None,
        transport: HTTPTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        route = regional_route.lower()
        if route not in REGIONAL_ROUTES:
            raise ValueError(f"Unsupported regional route: {regional_route}")
        if not api_key.strip():
            raise ValueError("A non-empty Riot API key is required")
        self._api_key = api_key
        self._route = route
        self._retry = retry_policy or RetryPolicy()
        self._transport = transport or UrllibTransport()
        self._sleep = sleep

    @classmethod
    def from_environment(cls, *, regional_route: str) -> Self:
        key = os.environ.get("RIOT_API_KEY", "")
        if not key:
            raise RuntimeError("RIOT_API_KEY is not configured")
        return cls(key, regional_route=regional_route)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Retained for a stable context-manager API; the transport is stateless."""

    def _request(self, path: str) -> Mapping[str, Any]:
        url = f"https://{self._route}.api.riotgames.com{path}"
        for attempt in range(1, self._retry.max_attempts + 1):
            response = self._transport.get(url, headers={"X-Riot-Token": self._api_key})
            if response.status_code == 200:
                try:
                    payload = json.loads(response.body)
                except json.JSONDecodeError as error:
                    raise RiotAPIError("Riot API returned invalid JSON") from error
                if not isinstance(payload, Mapping):
                    raise RiotAPIError("Riot API returned a non-object JSON payload")
                return payload
            retriable = response.status_code == 429 or response.status_code >= 500
            if not retriable or attempt == self._retry.max_attempts:
                raise RiotAPIError(
                    f"Riot API request failed with HTTP {response.status_code} for {path}"
                )
            retry_after = response.headers.get("Retry-After")
            delay = (
                float(retry_after)
                if retry_after is not None
                else self._retry.base_delay_seconds * (2 ** (attempt - 1))
            )
            self._sleep(min(delay, self._retry.max_delay_seconds))
        raise AssertionError("bounded retry loop terminated unexpectedly")

    def get_match(self, match_id: str) -> Mapping[str, Any]:
        _validate_match_id(match_id)
        return self._request(f"/lol/match/v5/matches/{match_id}")

    def get_timeline(self, match_id: str) -> Mapping[str, Any]:
        _validate_match_id(match_id)
        return self._request(f"/lol/match/v5/matches/{match_id}/timeline")


@dataclass(frozen=True)
class CollectedMatch:
    match_id: str
    game_version: str
    game_creation_ms: int
    match_sha256: str
    timeline_sha256: str


def _validate_match_id(match_id: str) -> None:
    if not MATCH_ID_PATTERN.fullmatch(match_id):
        raise ValueError(f"Unsafe or malformed match ID: {match_id!r}")


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


def collect_match_bundles(
    match_ids: Iterable[str],
    *,
    output_root: str | Path,
    fetcher: MatchFetcher,
    overwrite: bool = False,
    collected_at: datetime | None = None,
) -> dict[str, object]:
    """Fetch match/timeline pairs atomically and write a privacy-minimal manifest."""

    identifiers = tuple(
        dict.fromkeys(match_id.strip() for match_id in match_ids if match_id.strip())
    )
    if not identifiers:
        raise ValueError("At least one match ID is required")
    for match_id in identifiers:
        _validate_match_id(match_id)

    root = Path(output_root)
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
        if (
            _payload_match_id(match_payload) != match_id
            or _payload_match_id(timeline_payload) != match_id
        ):
            raise RiotAPIError(f"Payload identity mismatch for {match_id}")

        match_bytes = _canonical_json(match_payload)
        timeline_bytes = _canonical_json(timeline_payload)
        _atomic_write(match_path, match_bytes)
        _atomic_write(timeline_path, timeline_bytes)
        info = match_payload.get("info")
        safe_info = info if isinstance(info, Mapping) else {}
        collected.append(
            CollectedMatch(
                match_id=match_id,
                game_version=str(safe_info.get("gameVersion", "unknown")),
                game_creation_ms=int(safe_info.get("gameCreation", 0)),
                match_sha256=hashlib.sha256(match_bytes).hexdigest(),
                timeline_sha256=hashlib.sha256(timeline_bytes).hexdigest(),
            )
        )

    timestamp = collected_at or datetime.now(UTC)
    manifest: dict[str, object] = {
        "schema_version": "riot-raw-collection-v1",
        "collected_at": timestamp.astimezone(UTC).isoformat(),
        "requested": len(identifiers),
        "collected": [asdict(record) for record in collected],
        "skipped_existing": skipped,
        "contains_raw_player_identifiers": True,
        "redistribution": "not-authorized-by-this-manifest",
    }
    _atomic_write(root / "collection-manifest.json", _canonical_json(manifest))
    return manifest
