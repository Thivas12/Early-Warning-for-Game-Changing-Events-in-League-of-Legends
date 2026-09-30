"""Prefix-only command counts and destinations, with strict source checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.precontact_data import assert_unpaused_clock, build_one

WINDOWS_SECONDS = (5, 15, 30)
RADII = np.asarray([500, 1500, 3000])


def summaries(actions: pd.DataFrame, ticks: np.ndarray, target_xy: np.ndarray) -> dict:
    """Orders in (t-window,t]; target coordinates already observed at t."""
    action_ticks = actions.tick.to_numpy()
    orders = actions.order_type.to_numpy()
    entities = actions.issuer_player_id.to_numpy()
    queues = actions.queue.to_numpy()
    positions = actions[["pos_x", "pos_y"]].to_numpy()
    if np.any(np.diff(action_ticks) < 0):
        raise ValueError("command_ticks_out_of_order")
    outputs = {name: [] for name in ("rate", "destination", "rotated")}
    for tick, target in zip(ticks, target_xy, strict=True):
        features = {name: [] for name in outputs}
        for seconds in WINDOWS_SECONDS:
            left, right = np.searchsorted(action_ticks, [tick - 30 * seconds, tick], side="right")
            order = orders[left:right]
            issuer = entities[left:right]
            _, counts = np.unique(issuer, return_counts=True)
            movement_mask = (order == 1) | (order == 3)
            features["rate"].extend(
                [
                    len(order),
                    int(movement_mask.sum()),
                    int((order == 4).sum()),
                    int(((order >= 5) & (order <= 9)).sum()),
                    int(((order == 10) | (order == 21)).sum()),
                    int(queues[left:right].sum()),
                    len(counts),
                    int(counts.max()) if len(counts) else 0,
                ]
            )
            move = positions[left:right][movement_mask]
            issuers = issuer[movement_mask]
            _, reversed_index = np.unique(issuers[::-1], return_index=True)
            last = len(issuers) - 1 - reversed_index
            for name, sign in (("destination", 1), ("rotated", -1)):
                # Snapshot XY is cell*128+offset; command XY uses the centered map origin.
                destination = sign * move + 16384
                distances = np.linalg.norm(destination - target, axis=1)
                latest = distances[last]

                def three(values: np.ndarray) -> list[float]:
                    return (
                        [float(np.min(values)), float(np.median(values)), float(np.max(values))]
                        if len(values)
                        else [float("nan")] * 3
                    )

                if len(move) and not np.isfinite(target).all():
                    features[name].extend([float("nan")] * 15)
                    continue
                features[name].extend(
                    [
                        *three(distances),
                        *(int(np.sum(distances < r)) for r in RADII),
                        *(len(np.unique(issuers[distances < r])) for r in RADII),
                        *three(latest),
                        *(int(np.sum(latest < r)) for r in RADII),
                    ]
                )
        for name in outputs:
            outputs[name].append(features[name])
    return {name: np.asarray(values, dtype=np.float32) for name, values in outputs.items()}


def validate_actions(actions: pd.DataFrame, mid: str, start: int, end: int) -> pd.DataFrame:
    if actions.empty or set(actions.match_id.astype(str)) != {mid}:
        raise ValueError("missing_commands_or_match_id_mismatch")
    if (
        not np.isfinite(actions.tick).all()
        or not np.equal(actions.tick, actions.tick.astype(np.int64)).all()
    ):
        raise ValueError("noninteger_command_ticks")
    if np.any(np.diff(actions.tick.to_numpy()) < 0):
        raise ValueError("command_ticks_out_of_order")
    live = actions[actions.tick.between(start, end)].copy()
    if live.empty:
        raise ValueError("no_live_commands")
    assert_unpaused_clock(live.tick.to_numpy(), live.game_time_sec.to_numpy(), start)
    if not np.isfinite(live[["issuer_player_id", "order_type"]].to_numpy()).all():
        raise ValueError("invalid_command_identity_or_type")
    move = live[live.order_type.isin([1, 3])]
    if not np.isfinite(move[["pos_x", "pos_y"]].to_numpy()).all():
        raise ValueError("missing_movement_destination")
    return live


def main() -> None:
    original_path = Path("reports/precontact-quality-2026-09-30.json")
    original = json.loads(original_path.read_text())
    new_manifest = Path("reports/command-anticipation-cohort-2026-09-30.json")
    fresh = json.loads(new_manifest.read_text())
    ledger_path = Path("data/external/betty-commands/acquisition.json")
    ledger = json.loads(ledger_path.read_text())
    if ledger["manifest_sha256"] != hashlib.sha256(new_manifest.read_bytes()).hexdigest():
        raise ValueError("Acquisition manifest differs")
    acquired = {r["match_id"]: r for r in ledger["results"]}
    development = [
        r for r in original["matches"] if r["status"] == "accepted" and r["split"] != "evaluation"
    ]
    rows = development + fresh["matches"]
    if len(acquired) != len(rows) or set(acquired) != {str(r["match_id"]) for r in rows}:
        raise ValueError("Acquisition incomplete or duplicated")
    output_dir = Path("data/processed/commands")
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "manifest_sha256": hashlib.sha256(new_manifest.read_bytes()).hexdigest(),
        "original_quality_sha256": hashlib.sha256(original_path.read_bytes()).hexdigest(),
        "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "base_adapter_sha256": hashlib.sha256(
            Path("research/precontact_data.py").read_bytes()
        ).hexdigest(),
        "acquisition": ledger,
        "matches": [],
    }
    for row in rows:
        mid = str(row["match_id"])
        root = Path(
            "data/external/betty-commands"
            if row["split"] == "evaluation"
            else "data/external/betty-canonical"
        )
        try:
            source = acquired[mid]
            if source["status"] != "complete":
                raise ValueError("download_unavailable")
            for f in source["files"]:
                if hashlib.sha256((root / mid / f["name"]).read_bytes()).hexdigest() != f["sha256"]:
                    raise ValueError("source_hash_mismatch")
            if row["split"] == "evaluation":
                arrays, details = build_one(root, row)
            else:
                cached = Path("data/processed/precontact") / f"{mid}.npz"
                if hashlib.sha256(cached.read_bytes()).hexdigest() != row["arrays_sha256"]:
                    raise ValueError("Original features changed")
                arrays, details = dict(np.load(cached, allow_pickle=False)), dict(row)
            actions = validate_actions(
                pd.read_parquet(root / mid / "actions_normalized.parquet"),
                mid,
                details["start_tick"],
                details["end_tick"],
            )
            features = summaries(actions, arrays["ticks"], arrays["X"][:, 75:77] * 10000)
            arrays.update({f"command_{name}": values for name, values in features.items()})
            output = output_dir / f"{mid}.npz"
            np.savez_compressed(output, **arrays)
            details.update(
                command_rows=len(actions),
                arrays_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
            )
        except (ValueError, KeyError, OSError) as exc:
            details = {**row, "status": "excluded", "reason": str(exc)}
        report["matches"].append(details)
        print(mid, details["status"], details.get("reason", ""), flush=True)
        Path("reports/command-anticipation-quality-2026-09-30.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )


if __name__ == "__main__":
    main()
