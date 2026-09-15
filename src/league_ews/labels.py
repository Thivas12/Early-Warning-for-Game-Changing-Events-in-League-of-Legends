"""Exact event extraction and future-label construction for research-v2."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from league_ews.constants import RIFTHAZARD_HORIZONS_SECONDS
from league_ews.timeline import NormalizedTimeline, TimelineEvent


@dataclass(frozen=True)
class EventIndex:
    """One timestamp per objective kill or qualifying combat episode."""

    baron_ms: tuple[int, ...]
    dragon_ms: tuple[int, ...]
    teamfight_ms: tuple[int, ...]

    def for_event(self, event: str) -> tuple[int, ...]:
        if event == "baron":
            return self.baron_ms
        if event == "dragon":
            return self.dragon_ms
        if event == "teamfight":
            return self.teamfight_ms
        raise ValueError(f"Unsupported event: {event}")


def _combat_episode_starts(
    events: list[TimelineEvent], *, min_kills: int, max_gap_seconds: int
) -> tuple[int, ...]:
    if min_kills < 2 or max_gap_seconds < 1:
        raise ValueError("Combat episodes require at least two kills and a positive gap")
    kill_times = sorted(
        event.timestamp_ms for event in events if event.event_type == "CHAMPION_KILL"
    )
    if not kill_times:
        return ()
    episodes: list[list[int]] = [[kill_times[0]]]
    max_gap_ms = max_gap_seconds * 1000
    for timestamp in kill_times[1:]:
        if timestamp - episodes[-1][-1] <= max_gap_ms:
            episodes[-1].append(timestamp)
        else:
            episodes.append([timestamp])
    return tuple(episode[0] for episode in episodes if len(episode) >= min_kills)


def extract_event_index(
    timeline: NormalizedTimeline,
    *,
    teamfight_min_kills: int = 3,
    teamfight_max_gap_seconds: int = 10,
) -> EventIndex:
    """Extract exact objective timestamps and deduplicated combat episodes."""

    events = [event for observation in timeline.observations for event in observation.events]
    baron = sorted(
        {
            event.timestamp_ms
            for event in events
            if event.event_type == "ELITE_MONSTER_KILL" and event.monster_type == "BARON_NASHOR"
        }
    )
    dragon = sorted(
        {
            event.timestamp_ms
            for event in events
            if event.event_type == "ELITE_MONSTER_KILL" and event.monster_type == "DRAGON"
        }
    )
    return EventIndex(
        baron_ms=tuple(baron),
        dragon_ms=tuple(dragon),
        teamfight_ms=_combat_episode_starts(
            events,
            min_kills=teamfight_min_kills,
            max_gap_seconds=teamfight_max_gap_seconds,
        ),
    )


def future_event_labels(
    observation_times_ms: tuple[int, ...],
    event_index: EventIndex,
    *,
    horizons_seconds: tuple[int, ...] = RIFTHAZARD_HORIZONS_SECONDS,
) -> pd.DataFrame:
    """Label strictly future events on genuine observation timestamps."""

    if not horizons_seconds or any(horizon <= 0 for horizon in horizons_seconds):
        raise ValueError("Horizons must be positive")
    if tuple(sorted(horizons_seconds)) != horizons_seconds:
        raise ValueError("Horizons must be sorted")
    times = np.asarray(observation_times_ms, dtype=np.int64)
    if len(times) and np.any(np.diff(times) <= 0):
        raise ValueError("Observation times must increase")

    payload: dict[str, np.ndarray] = {"timestamp_ms": times}
    for event in ("baron", "dragon", "teamfight"):
        event_times = np.asarray(event_index.for_event(event), dtype=np.int64)
        next_indices = np.searchsorted(event_times, times, side="right")
        has_next = next_indices < len(event_times)
        next_times = np.full(len(times), np.iinfo(np.int64).max, dtype=np.int64)
        next_times[has_next] = event_times[next_indices[has_next]]
        delay = next_times - times
        for horizon in horizons_seconds:
            payload[f"y_{event}_{horizon}"] = ((delay > 0) & (delay <= horizon * 1000)).astype(
                np.int8
            )
    return pd.DataFrame(payload)
