"""Download a pinned replay manifest and extract objective contact facts.

Requires the pinned Gem checkout on PYTHONPATH plus python-snappy, protobuf,
and zstandard. This is a measurement pipeline, not a trained predictor.
All manifest entries are attempted; unsuccessful downloads/parses are recorded.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from urllib.request import urlopen


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_one(job: tuple[dict, str, str, str]) -> dict:
    entry, cache_root, output_root, reference_root = job
    match_id = entry["match_id"]
    cache = Path(cache_root)
    output = Path(output_root) / f"{match_id}.json"
    started = time.monotonic()
    base = {"match_id": match_id, "source_url": entry["replay_url"]}
    try:
        dem = cache / entry["dem"]
        if not dem.exists() or sha256(dem) != entry["dem_sha256"]:
            compressed = cache / f"{match_id}.download"
            if not compressed.exists():
                temporary = compressed.with_suffix(".partial")
                with (
                    urlopen(entry["replay_url"], timeout=40) as response,
                    temporary.open("wb") as sink,
                ):
                    total = 0
                    while block := response.read(1024 * 1024):
                        total += len(block)
                        if total > 400_000_000:
                            raise ValueError("Compressed download exceeded cap")
                        sink.write(block)
                temporary.replace(compressed)
            with compressed.open("rb") as stream:
                magic = stream.read(4)
            if magic == b"\x28\xb5\x2f\xfd":
                import zstandard

                opener = zstandard.open
            elif magic[:3] == b"BZh":
                opener = bz2.open
            else:
                raise ValueError(f"Unrecognized compression magic {magic.hex()}")
            temporary = dem.with_suffix(".partial")
            with opener(compressed, "rb") as reader, temporary.open("wb") as sink:
                total = 0
                while block := reader.read(1024 * 1024):
                    total += len(block)
                    if total > entry["dem_size_bytes"]:
                        raise ValueError("Decompressed replay exceeds pinned length")
                    sink.write(block)
            if total != entry["dem_size_bytes"] or sha256(temporary) != entry["dem_sha256"]:
                raise ValueError("Replay does not match pinned byte length and SHA256")
            temporary.replace(dem)

        from gem.parser import ReplayParser

        parser = ReplayParser(dem)
        contacts = []
        count = 0

        def on_entry(event):
            nonlocal count
            count += 1
            if event.target_name == "npc_dota_roshan" and (
                event.log_type.name == "DEATH"
                or (event.log_type.name == "DAMAGE" and event.value > 0)
            ):
                contacts.append(
                    {
                        "tick": event.tick,
                        "log_type": event.log_type.name,
                        "target_name": event.target_name,
                        "value": event.value,
                    }
                )

        parser.on_combat_log_entry(on_entry)
        parser.parse()
        if parser.parse_error is not None:
            raise ValueError(f"Incomplete parse: {parser.parse_error}")
        clock = parser.game_clock
        if clock.game_start_tick is None or parser.post_game_tick is None:
            raise ValueError("Missing game start or end; cannot certify complete observation")
        if parser.match_id != match_id:
            raise ValueError("Embedded replay ID differs from manifest")

        def unpaused(tick):
            return tick - clock.paused_ticks_before(tick)

        raw_contacts = [
            e for e in contacts if clock.game_start_tick <= e["tick"] <= parser.post_game_tick
        ]
        corrected = [{**e, "tick": unpaused(e["tick"])} for e in raw_contacts]
        deaths = [e for e in raw_contacts if e["log_type"] == "DEATH"]
        reference_path = Path(reference_root) / entry["opendota_json"]
        reference = json.loads(reference_path.read_text())
        reference_deaths = [
            e for e in reference.get("objectives", []) if e["type"] == "CHAT_MESSAGE_ROSHAN_KILL"
        ]
        if len(deaths) != len(reference_deaths):
            raise ValueError("Roshan death count disagrees with saved OpenDota reference")
        # Same raw replay, separate parser: useful cross-check, not independent data.
        pairs = [
            {
                "gem_game_time": clock.game_time_at(death["tick"]),
                "opendota_game_time": other["time"],
            }
            for death, other in zip(deaths, reference_deaths, strict=True)
        ]
        if any(abs(p["gem_game_time"] - p["opendota_game_time"]) > 2 for p in pairs):
            raise ValueError("Roshan clocks differ by more than two seconds across parsers")
        result = {
            "match_id": match_id,
            "game_start_tick": unpaused(clock.game_start_tick),
            "game_end_tick": unpaused(parser.post_game_tick),
            "combat_log": corrected,
            "roshans": [{"tick": unpaused(e["tick"])} for e in deaths],
            "source_combat_records": count,
            "onset_audit_clock_scope": "pause-corrected ticks at 30 Hz; leads are game time",
            "provenance": {
                "raw_dem_sha256": entry["dem_sha256"],
                "raw_dem_size_bytes": entry["dem_size_bytes"],
                "clock": asdict(clock),
                "raw_replay_contacts": raw_contacts,
                "opendota_reference_sha256": sha256(reference_path),
                "terminal_clock_crosscheck": pairs,
                "sampling_scope": "complete pinned parser fixture manifest; convenience sample",
            },
        }
        output.write_text(json.dumps(result, indent=2) + "\n")
        return {
            **base,
            "status": "complete",
            "seconds": time.monotonic() - started,
            "output_sha256": sha256(output),
            "terminal_events": len(deaths),
        }
    except Exception as error:
        return {
            **base,
            "status": "unavailable",
            "error": f"{type(error).__name__}: {error}",
            "seconds": time.monotonic() - started,
        }


def main() -> None:
    argument = argparse.ArgumentParser(description=__doc__)
    argument.add_argument("--manifest", type=Path, required=True)
    argument.add_argument("--cache-dir", type=Path, required=True)
    argument.add_argument("--output-dir", type=Path, required=True)
    argument.add_argument("--workers", type=int, default=2)
    args = argument.parse_args()
    for path in (args.cache_dir, args.output_dir):
        path.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(args.manifest.read_text())
    jobs = [
        (entry, str(args.cache_dir), str(args.output_dir), str(args.manifest.parent))
        for entry in manifest["matches"]
    ]
    result = {
        "manifest_sha256": sha256(args.manifest),
        "extractor_sha256": sha256(Path(__file__)),
        "attempted_matches": len(jobs),
        "results": [],
    }
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(prepare_one, job) for job in jobs]
        for future in as_completed(futures):
            row = future.result()
            result["results"].append(row)
            print(json.dumps(row), flush=True)
            (args.output_dir / "acquisition.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
