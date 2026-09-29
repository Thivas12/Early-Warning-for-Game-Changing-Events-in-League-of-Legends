"""Causal, permutation-invariant features for the coordination signal screen.

Displacements connect observed endpoints; they are not reconstructed paths,
instantaneous velocities, intentions, or causal effects.
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np

from league_ews.tabular_baseline import FEATURES as B3_FEATURES
from league_ews.tabular_baseline import _rows
from league_ews.timeline import NormalizedTimeline, Observation

PITS = {"baron": np.array([5007.0, 10471.0]), "dragon": np.array([9866.0, 4414.0])}
MAX_HISTORY_AGE_MS = 180_000
TEAMS = ((100, "blue"), (200, "red"))
GEOMETRY_NAMES = (
    *tuple(
        f"{team}_{name}"
        for _, team in TEAMS
        for name in (
            "position_count",
            "mean_x",
            "mean_y",
            "pair_distance_min",
            "pair_distance_mean",
            "baron_distance_min",
            "baron_distance_mean",
            "baron_near_count",
            "dragon_distance_min",
            "dragon_distance_mean",
            "dragon_near_count",
        )
    ),
    "enemy_distance_min",
    "enemy_distance_mean",
    "enemy_near_pairs",
)
SNAPSHOT_NAMES = B3_FEATURES + GEOMETRY_NAMES
HISTORY_NAMES = tuple(
    name
    for lag in (1, 2)
    for name in (f"lag{lag}_age_seconds", *(f"lag{lag}_{key}" for key in SNAPSHOT_NAMES))
)
COORDINATION_NAMES = (
    "motion_age_seconds",
    *tuple(
        f"{team}_{name}"
        for _, team in TEAMS
        for name in (
            "tracked_count",
            "displacement_rate_mean",
            "direction_coherence",
            "baron_approach_rate_mean",
            "baron_approach_rate_std",
            "baron_approaching_fraction",
            "dragon_approach_rate_mean",
            "dragon_approach_rate_std",
            "dragon_approaching_fraction",
        )
    ),
    "enemy_closing_rate_mean",
    "enemy_closing_fraction",
)
FEATURE_NAMES = SNAPSHOT_NAMES + HISTORY_NAMES + COORDINATION_NAMES
VARIANT_WIDTHS = {
    "b3": len(B3_FEATURES),
    "snapshot": len(SNAPSHOT_NAMES),
    "history": len(SNAPSHOT_NAMES) + len(HISTORY_NAMES),
    "coordination": len(FEATURE_NAMES),
}


def _positions(observation: Observation, team: int) -> dict[int, np.ndarray]:
    return {
        person.participant_id: np.array([person.position.x, person.position.y])
        for person in observation.participants
        if person.team_id == team and person.position is not None
    }


def _distance_stats(values: np.ndarray) -> list[float]:
    return [float(values.min()), float(values.mean())] if values.size else [np.nan, np.nan]


def _geometry(observation: Observation) -> list[float]:
    output: list[float] = []
    teams = [_positions(observation, team) for team, _ in TEAMS]
    for positions in teams:
        coords = np.array(list(positions.values())).reshape(-1, 2)
        output += [float(len(coords))]
        output += list(coords.mean(axis=0)) if len(coords) else [np.nan, np.nan]
        distances = np.linalg.norm(coords[:, None] - coords[None, :], axis=-1)
        output += _distance_stats(distances[np.triu_indices(len(coords), k=1)])
        for pit in PITS.values():
            values = np.linalg.norm(coords - pit, axis=1)
            output += [*_distance_stats(values), float(np.sum(values <= 1500))]
    blue, red = (np.array(list(team.values())).reshape(-1, 2) for team in teams)
    distances = np.linalg.norm(blue[:, None] - red[None, :], axis=-1)
    output += [*_distance_stats(distances), float(np.sum(distances <= 1500))]
    return output


def _motion(previous: Observation | None, current: Observation) -> list[float]:
    if previous is None or current.timestamp_ms - previous.timestamp_ms > MAX_HISTORY_AGE_MS:
        return [np.nan] * len(COORDINATION_NAMES)
    seconds = (current.timestamp_ms - previous.timestamp_ms) / 1000
    output: list[float] = [seconds]
    endpoints = []
    for team, _ in TEAMS:
        before, after = _positions(previous, team), _positions(current, team)
        ids = sorted(before.keys() & after.keys())
        old = np.array([before[i] for i in ids]).reshape(-1, 2)
        new = np.array([after[i] for i in ids]).reshape(-1, 2)
        endpoints.append((old, new))
        if not ids:
            output += [0.0] + [np.nan] * 8
            continue
        displacement = new - old
        lengths = np.linalg.norm(displacement, axis=1)
        moving = lengths > 0
        # Coherence is defined only with at least two observed moving players.
        coherence = (
            float(np.linalg.norm((displacement[moving] / lengths[moving, None]).mean(axis=0)))
            if moving.sum() >= 2
            else np.nan
        )
        output += [float(len(ids)), float(lengths.mean() / seconds), coherence]
        for pit in PITS.values():
            approach = np.linalg.norm(old - pit, axis=1) - np.linalg.norm(new - pit, axis=1)
            approach /= seconds
            output += [float(approach.mean()), float(approach.std()), float((approach > 0).mean())]
    if all(len(old) for old, _ in endpoints):
        (old_blue, new_blue), (old_red, new_red) = endpoints
        closing = (
            np.linalg.norm(old_blue[:, None] - old_red[None, :], axis=-1)
            - np.linalg.norm(new_blue[:, None] - new_red[None, :], axis=-1)
        ) / seconds
        output += [float(closing.mean()), float((closing > 0).mean())]
    else:
        output += [np.nan, np.nan]
    return output


def coordination_matrix(timeline: NormalizedTimeline) -> np.ndarray:
    """Build features from a timeline alone, without labels or a future event index."""
    observations = timeline.observations
    if not observations or any(
        later.timestamp_ms <= earlier.timestamp_ms for earlier, later in pairwise(observations)
    ):
        raise ValueError("Coordination features require nonempty ordered observations")
    for observation in observations:
        people = observation.participants
        if len({person.participant_id for person in people}) != 10 or any(
            sum(person.team_id == team for person in people) != 5 for team, _ in TEAMS
        ):
            raise ValueError("Expected ten unique participants and five per team")
    identities = {(p.participant_id, p.team_id) for p in observations[0].participants}
    if any(
        {(p.participant_id, p.team_id) for p in obs.participants} != identities
        for obs in observations
    ):
        raise ValueError("Participant identities or teams changed within match")
    # Reuse the audited B3 input logic with dummy targets, never actual labels.
    payload = {
        "schema_version": "league-ews-processed-match-v1",
        "timeline": timeline.model_dump(),
        "labels": [{"timestamp_ms": obs.timestamp_ms, "y_dragon_60": 0} for obs in observations],
    }
    snapshots = [
        vector + _geometry(obs)
        for (vector, _), obs in zip(
            _rows(payload, timeline.match_id, "y_dragon_60"), observations, strict=True
        )
    ]
    rows = []
    for index, observation in enumerate(observations):
        row = list(snapshots[index])
        for lag in (1, 2):
            age = (
                observation.timestamp_ms - observations[index - lag].timestamp_ms
                if index >= lag
                else None
            )
            if age is not None and age <= MAX_HISTORY_AGE_MS:
                row += [age / 1000, *snapshots[index - lag]]
            else:
                row += [np.nan] * (1 + len(SNAPSHOT_NAMES))
        row += _motion(observations[index - 1] if index else None, observation)
        rows.append(row)
    matrix = np.asarray(rows, dtype=np.float32)
    if matrix.shape != (len(observations), len(FEATURE_NAMES)) or np.isinf(matrix).any():
        raise ValueError("Invalid coordination feature matrix")
    return matrix
