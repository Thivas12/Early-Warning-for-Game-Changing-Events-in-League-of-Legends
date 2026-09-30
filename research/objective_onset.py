"""Audit completion warnings against observable damage onsets.

This module uses integer replay ticks, not inferred in-game seconds. A quiet
gap defines a damage episode; it does not establish intent, abandonment, or a
health reset. Target deaths are labels, never inputs to the reactive detector.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import pairwise
from typing import Any


@dataclass(frozen=True)
class Contact:
    tick: int
    kind: str


@dataclass(frozen=True)
class Episode:
    onset: int
    last_damage: int
    terminal: int | None
    closure: str
    damage_records: int


def contacts_from_gem(payload: dict[str, Any], target: str) -> list[Contact]:
    """Retain positive target damage and death, including non-hero attackers.

    Replay order is preserved within a tick, so fatal damage followed by death
    is one episode. Missing required source fields fail closed.
    """
    contacts: list[Contact] = []
    for row in payload["combat_log"]:
        if row["target_name"] != target:
            continue
        kind = row["log_type"]
        if kind == "DEATH" or (kind == "DAMAGE" and row["value"] > 0):
            tick = row["tick"]
            if not isinstance(tick, int) or isinstance(tick, bool):
                raise ValueError("Combat ticks must be integers")
            contacts.append(Contact(tick, kind))
    if any(a.tick > b.tick for a, b in pairwise(contacts)):
        raise ValueError("Combat log is not ordered")
    return contacts


def segment_episodes(
    contacts: list[Contact], *, quiet_ticks: int, recording_end: int
) -> tuple[list[Episode], list[int]]:
    """Split at an observed death or a damage gap strictly greater than quiet_ticks.

    An episode without a death is quiet-closed only after the recording supplies
    that much follow-up. Otherwise it is right-censored. Orphan deaths are
    returned separately; never invent their missing damage onsets.
    """
    if quiet_ticks <= 0:
        raise ValueError("quiet_ticks must be positive")
    if any(e.kind not in {"DAMAGE", "DEATH"} for e in contacts):
        raise ValueError("Only damage and death contacts are supported")
    if any(a.tick > b.tick for a, b in pairwise(contacts)):
        raise ValueError("Contacts must be ordered")
    if contacts and contacts[-1].tick > recording_end:
        raise ValueError("Contact after recording end")
    episodes: list[Episode] = []
    orphan_deaths: list[int] = []
    onset: int | None = None
    last_damage = count = 0

    for contact in contacts:
        if onset is not None and contact.tick - last_damage > quiet_ticks:
            episodes.append(Episode(onset, last_damage, None, "quiet", count))
            onset = None
        if contact.kind == "DAMAGE":
            if onset is None:
                onset, count = contact.tick, 0
            last_damage = contact.tick
            count += 1
        elif onset is None:
            orphan_deaths.append(contact.tick)
        else:
            episodes.append(Episode(onset, last_damage, contact.tick, "death", count))
            onset = None
    if onset is not None:
        closure = "quiet" if recording_end - last_damage > quiet_ticks else "right_censored"
        episodes.append(Episode(onset, last_damage, None, closure, count))
    return episodes, orphan_deaths


def reactive_alarms(
    contacts: list[Contact], *, quiet_ticks: int, cooldown_ticks: int, delay_ticks: int = 0
) -> list[int]:
    """Emit on first positive damage after a quiet gap, with past-only cooldown.

    The detector deliberately cannot use a future death, successful-outcome
    selection, or an offline episode's closure. Fixed nonnegative delivery delay
    models observation latency; it is not measured from this replay export.
    """
    if quiet_ticks <= 0 or cooldown_ticks < 0 or delay_ticks < 0:
        raise ValueError("Invalid detector timing")
    alarms: list[int] = []
    previous_damage: int | None = None
    for contact in contacts:
        if contact.kind != "DAMAGE":
            continue
        if previous_damage is not None and contact.tick < previous_damage:
            raise ValueError("Damage must be ordered")
        new_episode = previous_damage is None or contact.tick - previous_damage > quiet_ticks
        emit = contact.tick + delay_ticks
        if new_episode and (not alarms or emit - alarms[-1] >= cooldown_ticks):
            alarms.append(emit)
        previous_damage = contact.tick
    return alarms


def score_alarms(
    alarms: list[int], targets: list[int], *, min_lead: int, max_lead: int
) -> dict[str, Any]:
    """Maximum one-to-one matching for a common closed lead interval.

    Ordered equal-width eligibility intervals permit earliest-target greedy
    matching. There is no credit at the target time: min_lead must be positive.
    Unmatched alarms include false, late, early, and duplicate notifications.
    """
    if not 0 < min_lead <= max_lead:
        raise ValueError("Require 0 < min_lead <= max_lead")
    if alarms != sorted(alarms) or targets != sorted(targets):
        raise ValueError("Alarm and target times must be ordered")
    pairs: list[dict[str, int]] = []
    index = 0
    for alarm in alarms:
        while index < len(targets) and targets[index] < alarm + min_lead:
            index += 1
        if index < len(targets) and targets[index] <= alarm + max_lead:
            pairs.append({"alarm": alarm, "target": targets[index], "lead": targets[index] - alarm})
            index += 1
    hits = len(pairs)
    return {
        "targets": len(targets),
        "alarms": len(alarms),
        "hits": hits,
        "unmatched_alarms": len(alarms) - hits,
        "recall": hits / len(targets) if targets else None,
        "precision": hits / len(alarms) if alarms else None,
        "matches": pairs,
    }


def completion_window_overlap(episode: Episode, *, min_lead: int, max_lead: int) -> float:
    """Continuous-time fraction of a completion-positive window after damage onset.

    This geometric statistic assumes an unrestricted action clock. It is not
    learned-model contamination, attainable recall, or an opportunity bound.
    """
    if episode.terminal is None or not 0 < min_lead < max_lead:
        raise ValueError("Need a completed episode and a nonempty lead window")
    duration = episode.terminal - episode.onset
    return max(0, min(duration, max_lead) - min_lead) / (max_lead - min_lead)


def audit_match(
    payload: dict[str, Any], *, target: str = "npc_dota_roshan", nominal_tick_rate: int = 30
) -> dict[str, Any]:
    """A deterministic audit grid; no fitting, threshold tuning, or train/test split."""
    if nominal_tick_rate <= 0:
        raise ValueError("nominal_tick_rate must be positive")
    contacts = contacts_from_gem(payload, target)
    deaths = [e.tick for e in contacts if e.kind == "DEATH"]
    # An independent source field catches missing/duplicated terminal log events.
    if target == "npc_dota_roshan":
        listed_deaths = sorted(row["tick"] for row in payload["roshans"])
        if deaths != listed_deaths:
            raise ValueError("Roshan terminal log does not match independent objective list")
    scenarios = []
    for gap_seconds in (5, 10, 20, 30):
        quiet = gap_seconds * nominal_tick_rate
        episodes, orphan_deaths = segment_episodes(
            contacts, quiet_ticks=quiet, recording_end=payload["game_end_tick"]
        )
        completed = [e for e in episodes if e.terminal is not None]
        onset_times = [e.onset for e in episodes]
        metrics = []
        for delay_seconds in (0, 1, 5):
            alarms = reactive_alarms(
                contacts,
                quiet_ticks=quiet,
                cooldown_ticks=60 * nominal_tick_rate,
                delay_ticks=delay_seconds * nominal_tick_rate,
            )
            # Ignore notifications delivered after the available recording.
            alarms = [tick for tick in alarms if tick <= payload["game_end_tick"]]
            for minimum in (5, 20):
                timing = {
                    "min_lead": minimum * nominal_tick_rate,
                    "max_lead": 60 * nominal_tick_rate,
                }
                metrics.append(
                    {
                        "minimum_lead_nominal_seconds": minimum,
                        "delivery_delay_nominal_seconds": delay_seconds,
                        "alarm_ticks": alarms,
                        "completion": score_alarms(alarms, deaths, **timing),
                        "damage_onset": score_alarms(alarms, onset_times, **timing),
                        "completion_window_after_onset_fractions": [
                            completion_window_overlap(e, **timing) for e in completed
                        ],
                    }
                )
        scenarios.append(
            {
                "quiet_gap_nominal_seconds": gap_seconds,
                "episodes": [asdict(e) for e in episodes],
                "orphan_death_ticks": orphan_deaths,
                "metrics": metrics,
            }
        )
    return {
        "match_id": str(payload["match_id"]),
        "target": target,
        "game_start_tick": payload["game_start_tick"],
        "recording_end_tick": payload["game_end_tick"],
        "combat_records": payload.get("source_combat_records", len(payload["combat_log"])),
        "target_damage_records": sum(e.kind == "DAMAGE" for e in contacts),
        "terminal_events": len(deaths),
        "nominal_tick_rate": nominal_tick_rate,
        "clock_scope": payload.get(
            "onset_audit_clock_scope",
            "replay_ticks; dividing by tick rate is NOT pause-corrected game time",
        ),
        "observation_scope": (
            "observer combat log; no verified player-visible or live release times"
        ),
        "scenarios": scenarios,
    }
