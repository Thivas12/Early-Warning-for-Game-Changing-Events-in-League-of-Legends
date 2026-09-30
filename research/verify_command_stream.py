"""Verify canonical commands against raw protobuf messages, before model fitting."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def decode(replay: Path) -> pd.DataFrame:
    from gem.binary.packet import read_inner_messages
    from gem.binary.stream import DemoStream
    from gem.proto.demo_pb2 import (
        CDemoFullPacket,
        CDemoPacket,
        DEM_FullPacket,
        DEM_Packet,
        DEM_SignonPacket,
    )
    from gem.proto.dota_usermessages_pb2 import (
        CDOTAUserMsg_SpectatorPlayerUnitOrders,
        DOTA_UM_SpectatorPlayerUnitOrders,
    )

    rows = []
    with DemoStream(replay) as stream:
        for tick, kind, payload in stream:
            if kind in (DEM_Packet, DEM_SignonPacket):
                packet = CDemoPacket()
                packet.ParseFromString(payload)
                raw = packet.data
            elif kind == DEM_FullPacket:
                full = CDemoFullPacket()
                full.ParseFromString(payload)
                raw = full.packet.data
            else:
                continue
            for message_type, data in read_inner_messages(raw):
                if message_type != DOTA_UM_SpectatorPlayerUnitOrders:
                    continue
                order = CDOTAUserMsg_SpectatorPlayerUnitOrders()
                order.ParseFromString(data)
                rows.append(
                    {
                        "tick": tick,
                        "order_type": order.order_type,
                        "issuer_player_id": order.entindex,
                        "ability_id": order.ability_id if order.HasField("ability_id") else -1,
                        "target_index": order.target_index
                        if order.HasField("target_index")
                        else None,
                        **{
                            f"pos_{axis}": getattr(order.position, axis)
                            if order.HasField("position")
                            else None
                            for axis in "xyz"
                        },
                        "queue": order.queue,
                        "sequence_number": order.sequence_number,
                        "units": list(order.units),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    root = Path("data/external/betty-canonical/7616388415")
    replay = root / "source.dem"
    expected_raw_hash = "d286429839593847f0edc818c455dd12582cacfa172a15896c1446884b764af4"
    if hashlib.sha256(replay.read_bytes()).hexdigest() != expected_raw_hash:
        raise ValueError("Raw replay changed")
    raw = decode(replay)
    canonical = pd.read_parquet(root / "actions_normalized.parquet")
    if len(raw) != len(canonical):
        raise ValueError("Command row counts differ")
    equal = {
        c: int((canonical[c].eq(raw[c]) | (canonical[c].isna() & raw[c].isna())).sum())
        for c in canonical.columns.intersection(raw.columns)
    }
    if set(equal.values()) != {len(canonical)}:
        raise ValueError(f"Canonical command differences: {equal}")
    # Mechanism diagnostic only. Subsequent unit locations NEVER enter model features.
    hero = pd.read_parquet(root / "hero_state_ticks.parquet")
    movement = raw[(raw.order_type == 1) & raw.units.map(len).eq(1)].copy()
    movement["unit"] = movement.units.map(lambda units: units[0])
    errors = {shift: [] for shift in (0, 16384)}
    for unit, group in movement.groupby("unit"):
        snapshots = hero[hero.entity_id.eq(unit)].sort_values("tick")
        if snapshots.empty:
            continue
        ticks = snapshots.tick.to_numpy()
        # First snapshot at least one second after the command, at most two seconds.
        index = np.searchsorted(ticks, group.tick.to_numpy() + 30)
        valid = index < len(ticks)
        index, group = index[valid], group.iloc[np.flatnonzero(valid)]
        valid = ticks[index] <= group.tick.to_numpy() + 60
        index, group = index[valid], group.iloc[np.flatnonzero(valid)]
        position = snapshots[["pos_x", "pos_y"]].to_numpy()[index]
        command = group[["pos_x", "pos_y"]].to_numpy()
        for shift in errors:
            errors[shift].extend(np.linalg.norm(position - (command + shift), axis=1).tolist())
    coordinate_check = {
        str(shift): {
            "rows": len(values),
            "median_distance": float(np.median(values)),
            "within_50_units": int(np.sum(np.asarray(values) < 50)),
        }
        for shift, values in errors.items()
    }
    if coordinate_check["16384"]["within_50_units"] < 100:
        raise ValueError("Insufficient independent coordinate-alignment evidence")
    result = {
        "match_id": "7616388415",
        "raw_sha256": expected_raw_hash,
        "canonical_sha256": hashlib.sha256(
            (root / "actions_normalized.parquet").read_bytes()
        ).hexdigest(),
        "gem_revision": "e276f3ea5e77b5b8652a68ef7687b5c494592853",
        "commands": len(raw),
        "equal_fields": equal,
        "movement_selected_unit_counts": raw.loc[raw.order_type.eq(1), "units"]
        .map(len)
        .value_counts()
        .to_dict(),
        "issuer_field_semantics": "raw protobuf entindex, not a verified player slot",
        "coordinate_check": coordinate_check,
        "limitations": [
            "One replay validation, not all-match verification",
            "Selected units omitted from canonical derivative",
            "Future positions used solely for coordinate diagnostic, never as features",
            "Commands are issued orders, not verified intent or execution",
        ],
    }
    Path("reports/command-stream-verification-2026-09-30.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
