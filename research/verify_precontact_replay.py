"""Cross-check one public derivative against a separately parsed archived replay."""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd

RAW_REVISION = "d113b4eb79592d99beb174e1b45b994f0a9e6537"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--match-id", required=True)
    parser.add_argument("--compressed-sha256", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    folder = args.root / args.match_id
    compressed = folder / "source.dem.bz2"
    url = (
        "https://huggingface.co/datasets/wolframko/betty-dota2-raw-v2/resolve/"
        f"{RAW_REVISION}/replays/{args.match_id}.dem.bz2"
    )
    if not compressed.exists():
        with urlopen(url, timeout=60) as response:
            data = response.read(200_000_001)
        if len(data) > 200_000_000:
            raise ValueError("Replay exceeds download cap")
        compressed.write_bytes(data)
    data = compressed.read_bytes()
    if hashlib.sha256(data).hexdigest() != args.compressed_sha256:
        raise ValueError("Archived replay SHA256 mismatch")
    raw = bz2.decompress(data)
    replay = folder / "source.dem"
    replay.write_bytes(raw)
    from gem.parser import ReplayParser

    source = ReplayParser(replay)
    contacts = []

    def on_entry(event):
        if event.target_name == "npc_dota_roshan" and (
            event.log_type.name == "DEATH" or (event.log_type.name == "DAMAGE" and event.value > 0)
        ):
            contacts.append([event.tick, event.log_type.name, event.value])

    source.on_combat_log_entry(on_entry)
    source.parse()
    if source.parse_error is not None or str(source.match_id) != args.match_id:
        raise ValueError(f"Independent parse failed: {source.parse_error}")
    hero = pd.read_parquet(folder / "hero_state_ticks.parquet")
    clock = hero.groupby("tick", sort=True).game_time_sec.first()
    clock_errors = [
        abs(float(value) - source.game_clock.game_time_at(int(tick)))
        for tick, value in clock.items()
    ]
    combat = pd.read_parquet(folder / "combat_events.parquet")
    wanted = combat[
        combat.target_name.eq("npc_dota_roshan")
        & (
            combat.event_type.eq("DOTA_COMBATLOG_DEATH")
            | (combat.event_type.eq("DOTA_COMBATLOG_DAMAGE") & combat.value.gt(0))
        )
    ]
    canonical = [
        [int(r.tick), r.event_type.replace("DOTA_COMBATLOG_", ""), int(r.value)]
        for r in wanted.itertuples()
    ]

    # Death value fields are not damage magnitudes and can be parser-specific defaults.
    def normalize(rows):
        return [[t, kind, value if kind == "DAMAGE" else 0] for t, kind, value in rows]

    result = {
        "match_id": args.match_id,
        "source_url": url,
        "compressed_sha256": args.compressed_sha256,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "gem_revision": "e276f3ea5e77b5b8652a68ef7687b5c494592853",
        "clock_rows": len(clock),
        "clock_max_absolute_error_seconds": max(clock_errors),
        "clock_median_absolute_error_seconds": float(np.median(clock_errors)),
        "gem_contact_rows": len(contacts),
        "canonical_contact_rows": len(canonical),
        "contacts_exact": normalize(contacts) == normalize(canonical),
        "gem_game_start_tick": source.game_clock.game_start_tick,
        "gem_post_game_tick": source.post_game_tick,
        "scope": "One training match; independent parser agreement is not population validation",
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
