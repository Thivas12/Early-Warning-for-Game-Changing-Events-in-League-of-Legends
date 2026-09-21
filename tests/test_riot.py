from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pytest

from league_ews.riot import (
    HTTPTransport,
    RequestPacer,
    RetryPolicy,
    RiotAPIError,
    RiotMatchClient,
    RiotPlatformClient,
    TransportResponse,
    collect_match_bundles,
)


def _bundle(match_id: str) -> tuple[dict[str, object], dict[str, object]]:
    match = {
        "metadata": {"matchId": match_id, "participants": ["private-puuid"]},
        "info": {"gameVersion": "16.18.1", "gameCreation": 123},
    }
    timeline = {
        "metadata": {"matchId": match_id, "participants": ["private-puuid"]},
        "info": {"frames": []},
    }
    return match, timeline


class FakeFetcher:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def get_match(self, match_id: str) -> dict[str, object]:
        self.calls.append(("match", match_id))
        return _bundle(match_id)[0]

    def get_timeline(self, match_id: str) -> dict[str, object]:
        self.calls.append(("timeline", match_id))
        return _bundle(match_id)[1]


class FakeTransport(HTTPTransport):
    def __init__(self, responses: list[TransportResponse]) -> None:
        self.responses = responses
        self.requests: list[tuple[str, dict[str, str]]] = []

    def get(self, url: str, *, headers: dict[str, str]) -> TransportResponse:
        self.requests.append((url, headers))
        return self.responses.pop(0)


def _response(status: int, payload: Any = None, **headers: str) -> TransportResponse:
    return TransportResponse(
        status_code=status,
        body=json.dumps(payload).encode() if payload is not None else b"",
        headers=headers,
    )


def test_riot_client_uses_regional_route_and_identified_secret_request() -> None:
    transport = FakeTransport([_response(200, {"metadata": {"matchId": "EUW1_1"}})])
    client = RiotMatchClient("secret", regional_route="europe", transport=transport)
    client.get_match("EUW1_1")
    client.close()

    assert transport.requests[0][0].startswith("https://europe.api.riotgames.com/")
    assert transport.requests[0][1] == {
        "User-Agent": "league-ews-research/0.1",
        "X-Riot-Token": "secret",
    }


def test_detail_screening_treats_only_404_as_unavailable() -> None:
    missing = RiotMatchClient(
        "secret",
        regional_route="europe",
        transport=FakeTransport([_response(404)]),
    )
    assert missing.get_match_for_screening("EUW1_1") is None

    forbidden = RiotMatchClient(
        "secret",
        regional_route="europe",
        transport=FakeTransport([_response(403)]),
    )
    with pytest.raises(RiotAPIError, match="HTTP 403"):
        forbidden.get_match_for_screening("EUW1_1")


def test_riot_client_obeys_retry_after_without_leaking_key() -> None:
    delays: list[float] = []
    limited = TransportResponse(status_code=429, body=b"", headers={"Retry-After": "2"})
    transport = FakeTransport([limited, _response(503)])
    client = RiotMatchClient(
        "never-print-this",
        regional_route="europe",
        retry_policy=RetryPolicy(max_attempts=2),
        transport=transport,
        sleep=delays.append,
    )
    with pytest.raises(RiotAPIError) as error:
        client.get_timeline("EUW1_1")

    assert delays == [2.0]
    assert len(transport.requests) == 2
    assert "never-print-this" not in str(error.value)


def test_discovery_clients_use_platform_and_regional_routes() -> None:
    platform_transport = FakeTransport(
        [
            _response(200, {"entries": [{"summonerId": "encrypted-id"}]}),
            _response(200, {"puuid": "resolved-puuid"}),
        ]
    )
    platform = RiotPlatformClient(
        "secret",
        platform_id="EUW1",
        transport=platform_transport,
    )
    ladder = platform.get_top_league("MASTER")
    summoner = platform.get_summoner_by_id("encrypted-id")

    assert ladder["entries"]
    assert summoner["puuid"] == "resolved-puuid"
    assert platform_transport.requests[0][0] == (
        "https://euw1.api.riotgames.com/lol/league/v4/masterleagues/by-queue/RANKED_SOLO_5x5"
    )
    assert platform_transport.requests[1][0].endswith("/lol/summoner/v4/summoners/encrypted-id")

    regional_transport = FakeTransport([_response(200, ["EUW1_2", "EUW1_1"])])
    regional = RiotMatchClient(
        "secret",
        regional_route="europe",
        transport=regional_transport,
    )
    match_ids = regional.get_match_ids_by_puuid(
        "private/puuid",
        start_time=100,
        end_time=200,
        queue_id=420,
    )
    assert match_ids == ("EUW1_2", "EUW1_1")
    url = regional_transport.requests[0][0]
    assert url.startswith(
        "https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/private%2Fpuuid/ids?"
    )
    assert "startTime=100" in url
    assert "endTime=200" in url
    assert "queue=420" in url
    assert "count=100" in url


def test_discovery_error_redacts_player_identifier_and_validates_shapes() -> None:
    private_puuid = "private-puuid-never-echo"
    forbidden = RiotMatchClient(
        "secret",
        regional_route="europe",
        transport=FakeTransport([_response(403)]),
    )
    with pytest.raises(RiotAPIError) as error:
        forbidden.get_match_ids_by_puuid(
            private_puuid,
            start_time=100,
            end_time=200,
            queue_id=420,
        )
    assert private_puuid not in str(error.value)
    assert "match-v5.ids-by-puuid" in str(error.value)

    malformed = RiotMatchClient(
        "secret",
        regional_route="europe",
        transport=FakeTransport([_response(200, {"not": "a list"})]),
    )
    with pytest.raises(RiotAPIError, match="non-list"):
        malformed.get_match_ids_by_puuid(
            "valid-puuid",
            start_time=100,
            end_time=200,
            queue_id=420,
        )

    class BrokenTransport:
        def __init__(self) -> None:
            self.calls = 0

        def get(self, url: str, *, headers: dict[str, str]) -> TransportResponse:
            self.calls += 1
            raise OSError(f"network failed for {url}")

    delays: list[float] = []
    broken = BrokenTransport()
    disconnected = RiotMatchClient(
        "secret",
        regional_route="europe",
        retry_policy=RetryPolicy(max_attempts=3),
        transport=broken,
        sleep=delays.append,
    )
    with pytest.raises(RiotAPIError) as transport_error:
        disconnected.get_match_ids_by_puuid(
            private_puuid,
            start_time=100,
            end_time=200,
            queue_id=420,
        )
    assert private_puuid not in str(transport_error.value)
    assert broken.calls == 3
    assert delays == [1.0, 2.0]


def test_riot_client_recovers_from_transient_transport_failure() -> None:
    class FlakyTransport:
        def __init__(self) -> None:
            self.calls = 0

        def get(self, url: str, *, headers: dict[str, str]) -> TransportResponse:
            self.calls += 1
            if self.calls == 1:
                raise OSError("temporary network interruption")
            return _response(200, {"metadata": {"matchId": "EUW1_1"}})

    delays: list[float] = []
    transport = FlakyTransport()
    client = RiotMatchClient(
        "secret",
        regional_route="europe",
        retry_policy=RetryPolicy(max_attempts=2),
        transport=transport,
        sleep=delays.append,
    )

    assert client.get_match("EUW1_1")["metadata"]["matchId"] == "EUW1_1"
    assert transport.calls == 2
    assert delays == [1.0]


def test_invalid_retry_after_falls_back_to_exponential_delay() -> None:
    delays: list[float] = []
    transport = FakeTransport(
        [
            TransportResponse(status_code=429, body=b"", headers={"Retry-After": "invalid"}),
            _response(200, {"metadata": {"matchId": "EUW1_1"}}),
        ]
    )
    client = RiotMatchClient(
        "secret",
        regional_route="europe",
        transport=transport,
        sleep=delays.append,
    )

    client.get_match("EUW1_1")

    assert delays == [1.0]


def test_request_pacer_spaces_sequential_calls() -> None:
    clock_value = [10.0]
    delays: list[float] = []

    def sleep(delay: float) -> None:
        delays.append(delay)
        clock_value[0] += delay

    pacer = RequestPacer(
        1.25,
        sleep=sleep,
        clock=lambda: clock_value[0],
    )
    pacer()
    clock_value[0] += 0.25
    pacer()
    clock_value[0] += 2.0
    pacer()

    assert delays == [1.0]


def test_collection_is_atomic_resumable_and_privacy_minimal(tmp_path) -> None:
    fetcher = FakeFetcher()
    timestamp = datetime(2026, 9, 15, tzinfo=UTC)
    manifest = collect_match_bundles(
        ["EUW1_1", "EUW1_1", "EUW1_2"],
        regional_route="europe",
        output_root=tmp_path,
        fetcher=fetcher,
        collected_at=timestamp,
    )

    assert len(manifest["collected"]) == 2
    assert len(manifest["available"]) == 2
    assert manifest["schema_version"] == "riot-raw-collection-v2"
    assert manifest["contains_raw_player_identifiers"] is True
    assert "private-puuid" not in json.dumps(manifest)
    assert (tmp_path / "matches" / "EUW1_1.json").is_file()
    assert not list(tmp_path.rglob("*.partial"))

    second = collect_match_bundles(
        ["EUW1_1"],
        regional_route="europe",
        output_root=tmp_path,
        fetcher=fetcher,
        collected_at=timestamp,
    )
    assert second["skipped_existing"] == ["EUW1_1"]
    assert len(second["available"]) == 2
    assert len(fetcher.calls) == 4


def test_resumed_bundle_cannot_change_regional_route(tmp_path) -> None:
    collect_match_bundles(
        ["EUW1_1"],
        regional_route="europe",
        output_root=tmp_path,
        fetcher=FakeFetcher(),
    )

    with pytest.raises(ValueError, match="cannot change regional route"):
        collect_match_bundles(
            ["EUW1_1"],
            regional_route="americas",
            output_root=tmp_path,
            fetcher=FakeFetcher(),
        )


def test_resume_rejects_existing_bytes_that_no_longer_match_manifest(tmp_path) -> None:
    collect_match_bundles(
        ["EUW1_1"],
        regional_route="europe",
        output_root=tmp_path,
        fetcher=FakeFetcher(),
    )
    timeline_path = tmp_path / "timelines" / "EUW1_1.json"
    timeline_path.write_text(
        timeline_path.read_text(encoding="utf-8") + " ",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="differs from its recorded manifest"):
        collect_match_bundles(
            ["EUW1_1"],
            regional_route="europe",
            output_root=tmp_path,
            fetcher=FakeFetcher(),
        )


def test_invalid_existing_inventory_blocks_new_fetches(tmp_path) -> None:
    fetcher = FakeFetcher()
    collect_match_bundles(
        ["EUW1_1"],
        regional_route="europe",
        output_root=tmp_path,
        fetcher=fetcher,
    )
    timeline_path = tmp_path / "timelines" / "EUW1_1.json"
    timeline_path.write_text(
        timeline_path.read_text(encoding="utf-8") + " ",
        encoding="utf-8",
    )
    fetcher.calls.clear()

    with pytest.raises(ValueError, match="differs from its recorded manifest"):
        collect_match_bundles(
            ["EUW1_2"],
            regional_route="europe",
            output_root=tmp_path,
            fetcher=fetcher,
        )

    assert fetcher.calls == []
    assert not (tmp_path / "matches" / "EUW1_2.json").exists()


@pytest.mark.parametrize("match_id", ["../secret", "", "EUW1-123"])
def test_unsafe_match_ids_are_rejected(match_id: str, tmp_path) -> None:
    with pytest.raises(ValueError):
        collect_match_bundles(
            [match_id],
            regional_route="europe",
            output_root=tmp_path,
            fetcher=FakeFetcher(),
        )


def test_payload_identity_mismatch_is_rejected(tmp_path) -> None:
    class MismatchFetcher(FakeFetcher):
        def get_match(self, match_id: str) -> dict[str, object]:
            return _bundle("EUW1_999")[0]

    with pytest.raises(RiotAPIError, match="identity mismatch"):
        collect_match_bundles(
            ["EUW1_1"],
            regional_route="europe",
            output_root=tmp_path,
            fetcher=MismatchFetcher(),
        )


def test_client_configuration_is_validated(monkeypatch) -> None:
    with pytest.raises(ValueError, match="route"):
        RiotMatchClient("secret", regional_route="moon")
    with pytest.raises(ValueError, match="non-empty"):
        RiotMatchClient("", regional_route="europe")
    with pytest.raises(ValueError, match="positive"):
        RetryPolicy(max_attempts=0)
    monkeypatch.delenv("RIOT_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="not configured"):
        RiotMatchClient.from_environment(regional_route="europe")
