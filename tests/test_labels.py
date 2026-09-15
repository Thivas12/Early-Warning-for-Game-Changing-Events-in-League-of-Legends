from __future__ import annotations

import pytest

from league_ews.constants import LEGACY_HORIZONS_SECONDS, RIFTHAZARD_HORIZONS_SECONDS
from league_ews.labels import EventIndex, extract_event_index, future_event_labels
from league_ews.timeline import NormalizedTimeline, Observation, TimelineEvent


def _timeline() -> NormalizedTimeline:
    events = (
        TimelineEvent(
            timestamp_ms=20_000,
            event_type="ELITE_MONSTER_KILL",
            monster_type="DRAGON",
        ),
        TimelineEvent(timestamp_ms=31_000, event_type="CHAMPION_KILL"),
        TimelineEvent(timestamp_ms=37_000, event_type="CHAMPION_KILL"),
        TimelineEvent(timestamp_ms=40_000, event_type="CHAMPION_KILL"),
        TimelineEvent(timestamp_ms=90_000, event_type="CHAMPION_KILL"),
        TimelineEvent(
            timestamp_ms=100_000,
            event_type="ELITE_MONSTER_KILL",
            monster_type="BARON_NASHOR",
        ),
    )
    return NormalizedTimeline(
        match_id="EUW1_1",
        game_version="test",
        game_creation_ms=1,
        platform_id="EUW1",
        observations=(Observation(timestamp_ms=0, participants=(), events=events),),
    )


def test_event_index_deduplicates_teamfight_episode() -> None:
    index = extract_event_index(_timeline())
    assert index.baron_ms == (100_000,)
    assert index.dragon_ms == (20_000,)
    assert index.teamfight_ms == (31_000,)


def test_future_labels_are_nested_and_strictly_future() -> None:
    labels = future_event_labels(
        (0, 10_000, 20_000, 30_000),
        EventIndex(baron_ms=(), dragon_ms=(20_000,), teamfight_ms=(31_000,)),
    )
    assert labels.loc[0, ["y_dragon_10", "y_dragon_20", "y_dragon_30"]].tolist() == [0, 1, 1]
    assert labels.loc[1, ["y_dragon_10", "y_dragon_20", "y_dragon_30"]].tolist() == [1, 1, 1]
    assert labels.loc[2, ["y_dragon_10", "y_dragon_20", "y_dragon_30"]].tolist() == [0, 0, 0]
    assert labels.loc[0, ["y_teamfight_10", "y_teamfight_20", "y_teamfight_30"]].tolist() == [
        0,
        0,
        0,
    ]
    assert labels.loc[1, "y_teamfight_30"] == 1
    assert labels.loc[0, "y_teamfight_60"] == 1
    assert labels.loc[3, "y_baron_60"] == 0


def test_research_horizons_include_registered_60_seconds_without_changing_legacy() -> None:
    assert RIFTHAZARD_HORIZONS_SECONDS == (10, 20, 30, 60)
    assert LEGACY_HORIZONS_SECONDS == (10, 20, 30)


@pytest.mark.parametrize("horizons", [(), (0, 10), (20, 10)])
def test_invalid_horizons_are_rejected(horizons: tuple[int, ...]) -> None:
    with pytest.raises(ValueError, match="Horizons"):
        future_event_labels((0,), EventIndex((), (), ()), horizons_seconds=horizons)


def test_non_increasing_observations_are_rejected() -> None:
    with pytest.raises(ValueError, match="increase"):
        future_event_labels((10, 10), EventIndex((), (), ()))


def test_invalid_teamfight_definition_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least two"):
        extract_event_index(_timeline(), teamfight_min_kills=1)
