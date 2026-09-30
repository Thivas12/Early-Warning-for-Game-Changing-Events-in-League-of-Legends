"""Strict public-data adapter and prefix-only features for the pre-contact pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from research.objective_onset import Contact, reactive_alarms, segment_episodes


def hero_key(value: str) -> str:
    value = value.lower().replace("cdota_unit_hero_", "").replace("npc_dota_hero_", "")
    return re.sub("[^a-z0-9]", "", value)


def prefix_indices(observed: np.ndarray, requested: np.ndarray) -> np.ndarray:
    """Last actually observed frame at or before each requested replay tick."""
    if len(observed) == 0 or np.any(np.diff(observed) <= 0):
        raise ValueError("Observation ticks must be strictly increasing")
    indices = np.searchsorted(observed, requested, side="right") - 1
    if np.any(indices < 0):
        raise ValueError("History precedes first observation")
    return indices


def assert_unpaused_clock(ticks: np.ndarray, times: np.ndarray, start: int) -> None:
    """No retrospective clock repair: reject pauses and inconsistent offsets."""
    error = np.abs(times - (ticks - start) / 30)
    if not np.all(np.isfinite(times)) or np.max(error) > 0.2:
        raise ValueError(f"unverified_pause_clock:max_error_seconds={float(np.max(error)):.3f}")


def teams_before_horn(combat: pd.DataFrame, heroes: list[str], start: int) -> np.ndarray:
    early = combat[
        (combat.tick <= start)
        & combat.is_target_hero.eq(True)
        & combat.is_target_illusion.eq(False)
        & combat.target_team.isin([2, 3])
        & combat.target_name.notna()
    ].copy()
    early["key"] = early.target_name.map(hero_key)
    mapping = {key: set(group.target_team.astype(int)) for key, group in early.groupby("key")}
    teams = []
    for hero in heroes:
        values = mapping.get(hero_key(hero), set())
        if len(values) != 1:
            raise ValueError("missing_or_conflicting_pregame_team")
        teams.append(next(iter(values)))
    if sorted(teams) != [2] * 5 + [3] * 5:
        raise ValueError("pregame_team_cardinality")
    return np.asarray(teams)


def coordination_features(
    pos: np.ndarray, past: np.ndarray, alive: np.ndarray, target: np.ndarray, teams: np.ndarray
) -> np.ndarray:
    """Explicit geometry/motion; all arrays are current or older observations."""
    velocity = (pos - past) / 10
    pieces = []
    for team in (2, 3):
        mask = teams == team
        p, v, living = pos[:, mask], velocity[:, mask], alive[:, mask]
        delta = p[:, :, None] - p[:, None, :]
        distances = np.linalg.norm(delta, axis=-1)
        upper = np.triu_indices(5, 1)
        pair_dist = distances[:, upper[0], upper[1]]
        to_target = target[:, None, :] - p
        target_dist = np.linalg.norm(to_target, axis=-1)
        speed = np.linalg.norm(v, axis=-1)
        radial_speed = (v * to_target).sum(-1) / np.maximum(target_dist, 1e-6)
        align = (v[:, :, None] * v[:, None, :]).sum(-1)
        align /= np.maximum(speed[:, :, None] * speed[:, None, :], 1e-6)
        centre = p.mean(1)
        pieces.extend(
            [
                living.sum(1),
                pair_dist.mean(1),
                pair_dist.min(1),
                pair_dist.max(1),
                target_dist.mean(1),
                target_dist.min(1),
                target_dist.max(1),
                ((target_dist < 1500 / 10000) & (living > 0.5)).sum(1),
                ((target_dist < 3000 / 10000) & (living > 0.5)).sum(1),
                radial_speed.mean(1),
                (radial_speed > 0.005).sum(1),
                align[:, upper[0], upper[1]].mean(1),
                np.linalg.norm(centre - target, axis=-1),
                speed.mean(1),
            ]
        )
    return np.column_stack(pieces)


def build_one(root: Path, row: dict) -> tuple[dict, dict]:
    mid = str(row["match_id"])
    folder = root / mid
    hero = pd.read_parquet(folder / "hero_state_ticks.parquet")
    roshan = pd.read_parquet(folder / "roshan_state_ticks.parquet")
    combat = pd.read_parquet(folder / "combat_events.parquet")
    for table in (hero, roshan, combat):
        if set(table.match_id.astype(str)) != {mid}:
            raise ValueError("embedded_match_id_mismatch")
    states = combat[combat.event_type.eq("DOTA_COMBATLOG_GAME_STATE")]
    starts = states.loc[states.value.eq(5), "tick"].unique()
    ends = states.loc[states.value.eq(6), "tick"].unique()
    if len(starts) != 1 or len(ends) != 1:
        raise ValueError("missing_unique_game_boundaries")
    start, end = int(starts[0]), int(ends[0])
    hero = hero[hero.tick.between(start, end)].sort_values(["tick", "slot"])
    roshan = roshan[roshan.tick.between(start, end)].sort_values("tick")
    combat_live = combat[combat.tick.between(start, end)]
    if hero.empty or roshan.empty:
        raise ValueError("empty_live_states")
    ticks = hero.tick.unique().astype(np.int64)
    if hero.duplicated(["tick", "slot"]).any() or not hero.groupby("tick").size().eq(10).all():
        raise ValueError("incomplete_or_duplicate_hero_frame")
    if (
        sorted(hero.slot.unique()) != list(range(10))
        or not hero.groupby("slot").hero_name.nunique().eq(1).all()
    ):
        raise ValueError("unstable_hero_identity")
    if not hero.groupby("tick").game_time_sec.nunique().eq(1).all():
        raise ValueError("inconsistent_frame_clock")
    clock = hero.groupby("tick", sort=True).game_time_sec.first().to_numpy()
    assert_unpaused_clock(ticks, clock, start)
    assert_unpaused_clock(roshan.tick.to_numpy(), roshan.game_time_sec.to_numpy(), start)
    if ticks[0] != start or end - ticks[-1] > 31 or np.max(np.diff(ticks)) > 31:
        raise ValueError("incomplete_snapshot_coverage")
    if abs((end - start) / 30 - row["duration_sec"]) > 3:
        raise ValueError("metadata_duration_disagreement")
    first = hero.iloc[:10]
    teams = teams_before_horn(combat, first.hero_name.tolist(), start)
    # Exported team labels are audited but never consumed as input.
    reported = first.team_side.map({"radiant": 2, "dire": 3}).to_numpy()
    ros_contacts = combat_live[
        combat_live.target_name.eq("npc_dota_roshan")
        & (
            combat_live.event_type.eq("DOTA_COMBATLOG_DEATH")
            | (combat_live.event_type.eq("DOTA_COMBATLOG_DAMAGE") & combat_live.value.gt(0))
        )
    ].sort_values("tick", kind="stable")
    contacts = [
        Contact(int(r.tick), "DEATH" if r.event_type.endswith("DEATH") else "DAMAGE")
        for r in ros_contacts.itertuples()
    ]
    episodes, orphans = segment_episodes(contacts, quiet_ticks=300, recording_end=end)
    if orphans:
        raise ValueError("orphan_objective_death")
    # Independent entity health must show a decrease at every combat-defined onset.
    rt, rh = roshan.tick.to_numpy(), roshan.hp.to_numpy()
    damage_ticks = np.asarray([c.tick for c in contacts if c.kind == "DAMAGE"], dtype=np.int64)
    # Reverse check: do not certify a no-event match just because combat rows are absent.
    for i in np.flatnonzero(np.diff(rh) < 0) + 1:
        recent = damage_ticks[(damage_ticks > rt[i - 1] - 30) & (damage_ticks <= rt[i] + 30)]
        if not len(recent):
            raise ValueError("entity_hp_loss_without_combat_damage")
    for episode in episodes:
        before = np.searchsorted(rt, episode.onset, side="left") - 1
        after = (rt >= episode.onset) & (rt <= episode.onset + 60)
        if before < 0 or not after.any() or not np.any(rh[after] < rh[before]):
            raise ValueError("onset_without_entity_hp_confirmation")
    # Also ensure every combat death is followed by entity HP zero within two seconds.
    deaths = [c.tick for c in contacts if c.kind == "DEATH"]
    for death in deaths:
        after = (rt >= death) & (rt <= death + 60)
        if not after.any() or not np.any(rh[after] == 0):
            raise ValueError("death_without_entity_hp_confirmation")
    decisions = np.arange(start + 300 * 30, end + 1, 5 * 30, dtype=np.int64)
    if len(decisions) < 12:
        raise ValueError("too_short_for_pilot")
    indices = prefix_indices(ticks, decisions)
    index10 = prefix_indices(ticks, decisions - 10 * 30)
    index30 = prefix_indices(ticks, decisions - 30 * 30)
    ri = prefix_indices(rt, decisions)
    cols = ["pos_x", "pos_y", "hp", "max_hp", "mana", "max_mana", "level", "alive"]
    values = hero[cols].to_numpy(dtype=float).reshape(len(ticks), 10, len(cols))
    if not np.isfinite(values).all() or np.any(values[:, :, 3] <= 0):
        raise ValueError("missing_entity_local_features")
    # Group by actual pregame team, preserving fixed player ordering within each team.
    order = np.argsort(teams, kind="stable")
    teams = teams[order]
    values = values[:, order]
    pos = values[:, :, :2] / 10000
    features = np.concatenate(
        (
            pos,
            values[:, :, 2:3] / values[:, :, 3:4],
            values[:, :, 4:5] / np.maximum(values[:, :, 5:6], 1),
            values[:, :, 6:7] / 30,
            values[:, :, 7:8],
        ),
        axis=2,
    )
    target_pos = roshan[["pos_x", "pos_y"]].to_numpy(dtype=float)[ri] / 10000
    # A dead objective may have no position. Missing stays missing for the tree model.
    target_hp = roshan.hp.to_numpy(dtype=float)[ri] / np.maximum(
        roshan.max_hp.to_numpy(dtype=float)[ri], 1
    )
    history = []
    for kind in ("DAMAGE", "DEATH"):
        event_ticks = np.asarray([c.tick for c in contacts if c.kind == kind], dtype=np.int64)
        previous = np.searchsorted(event_ticks, decisions, side="right") - 1
        elapsed = np.full(len(decisions), 1200.0, dtype=float)
        valid = previous >= 0
        elapsed[valid] = np.minimum((decisions[valid] - event_ticks[previous[valid]]) / 30, 1200)
        history.append(elapsed)
    base = np.column_stack(
        ((decisions - start) / 30, *history, roshan.alive.to_numpy(dtype=float)[ri], target_hp)
    )
    current = features[indices].reshape(len(decisions), -1)
    distances = np.linalg.norm(pos[indices] - target_pos[:, None], axis=-1)
    current = np.column_stack((base, current, distances, target_pos))
    historical = np.column_stack(
        (
            current,
            features[index10].reshape(len(decisions), -1),
            features[index30].reshape(len(decisions), -1),
        )
    )
    coordination = coordination_features(
        pos[indices], pos[index10], features[indices, :, -1], target_pos, teams
    )
    full = np.column_stack((historical, coordination))
    targets = np.asarray(
        [e.onset for e in episodes if e.onset >= decisions[0] + 600], dtype=np.int64
    )
    kill_targets = np.asarray([d for d in deaths if d >= decisions[0] + 600], dtype=np.int64)

    def labels(target: np.ndarray) -> np.ndarray:
        return (
            np.searchsorted(target, decisions + 1800, side="right")
            > np.searchsorted(target, decisions + 600, side="left")
        ).astype(np.int8)

    arrays = {
        "X": full.astype(np.float32),
        "ticks": decisions,
        "onset_y": labels(targets),
        "kill_y": labels(kill_targets),
        "onsets": targets,
        "kills": kill_targets,
        "reactive": np.asarray(
            [
                t
                for t in reactive_alarms(contacts, quiet_ticks=300, cooldown_ticks=1800)
                if decisions[0] <= t <= end
            ],
            dtype=np.int64,
        ),
    }
    details = {
        **row,
        "status": "accepted",
        "start_tick": start,
        "end_tick": end,
        "hero_rows": len(hero),
        "combat_rows": len(combat_live),
        "decision_rows": len(decisions),
        "onsets": len(targets),
        "kills": len(kill_targets),
        "nonterminal_episodes": sum(e.terminal is None for e in episodes),
        "exported_team_disagreements": int(np.sum(reported != teams[np.argsort(order)])),
        "feature_boundaries": {
            "clock": base.shape[1],
            "current": current.shape[1],
            "history": historical.shape[1],
            "coordination": full.shape[1],
        },
    }
    return arrays, details


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    ledger = json.loads((args.root / "acquisition.json").read_text())
    acquired = {r["match_id"]: r for r in ledger["results"]}
    if len(acquired) != len(manifest["matches"]):
        raise ValueError("Acquisition incomplete; refusing to select partial cohort")
    report = {
        "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "acquisition": ledger,
        "matches": [],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for row in manifest["matches"]:
        mid = str(row["match_id"])
        try:
            acquisition = acquired[mid]
            if acquisition["status"] != "complete":
                raise ValueError("download_unavailable")
            for f in acquisition["files"]:
                path = args.root / mid / f["name"]
                if hashlib.sha256(path.read_bytes()).hexdigest() != f["sha256"]:
                    raise ValueError("source_hash_mismatch")
            arrays, details = build_one(args.root, row)
            output = args.output_dir / f"{mid}.npz"
            np.savez_compressed(output, **arrays)
            details["arrays_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
        except (ValueError, KeyError, OSError) as error:
            details = {**row, "status": "excluded", "reason": str(error)}
        report["matches"].append(details)
        print(mid, details["status"], details.get("reason", ""), flush=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
