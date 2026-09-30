"""Acquire a deterministic, outcome-independent public replay derivative cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

REPOSITORY = "wolframko/betty-dota2-canonical-v1"
REVISION = "29aca0551be317948d0a181e9630c9a583fadc32"
FILES = ("hero_state_ticks.parquet", "roshan_state_ticks.parquet", "combat_events.parquet")
METADATA_REVISION = "b20e01577af2f4f5dffcdc4f1d5bad5c3807abca"
METADATA_SHA256 = "4f5c2152ba188ced430e5680775d57107bf77e2a51d2b099f816bf34faffe4bb"


def acquire(job: tuple[str, str]) -> dict:
    match_id, root = job
    result = {"match_id": match_id, "files": [], "status": "complete"}
    for name in FILES:
        path = Path(root) / match_id / name
        path.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://huggingface.co/datasets/{REPOSITORY}/resolve/{REVISION}/{match_id}/{name}"
        try:
            if not path.exists():
                with urlopen(url, timeout=50) as response:
                    raw = response.read(30_000_001)
                if len(raw) > 30_000_000 or raw[:4] != b"PAR1" or raw[-4:] != b"PAR1":
                    raise ValueError("Not a bounded complete Parquet file")
                temporary = path.with_suffix(".partial")
                temporary.write_bytes(raw)
                temporary.replace(path)
            raw = path.read_bytes()
            result["files"].append(
                {"name": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            )
        except Exception as error:
            result.update(status="unavailable", error=f"{type(error).__name__}: {error}")
            break
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--count", type=int, default=300)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if not args.metadata.exists():
        url = (
            "https://huggingface.co/datasets/wolframko/betty-dota2/resolve/"
            f"{METADATA_REVISION}/matches.parquet"
        )
        with urlopen(url, timeout=60) as response:
            raw = response.read(30_000_001)
        if hashlib.sha256(raw).hexdigest() != METADATA_SHA256:
            raise ValueError("Downloaded metadata does not match pinned SHA256")
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_bytes(raw)
    if hashlib.sha256(args.metadata.read_bytes()).hexdigest() != METADATA_SHA256:
        raise ValueError("Metadata does not match pinned SHA256")
    metadata = pd.read_parquet(
        args.metadata, columns=["match_id", "start_time", "duration_sec", "league_id"]
    )
    # First ten were examined during schema discovery. Exclude them from model evaluation.
    metadata = metadata.sort_values("match_id").iloc[10:].copy()
    metadata["selection_key"] = metadata.match_id.map(
        lambda mid: hashlib.sha256(f"precontact-v1:{mid}".encode()).hexdigest()
    )
    selected = (
        metadata.sort_values("selection_key")
        .head(args.count)
        .sort_values(["start_time", "match_id"])
    )
    records = selected.drop(columns="selection_key").to_dict("records")
    for i, row in enumerate(records):
        row["split"] = (
            "train"
            if i < int(0.6 * len(records))
            else "calibration"
            if i < int(0.8 * len(records))
            else "evaluation"
        )
    manifest = {
        "repository": REPOSITORY,
        "revision": REVISION,
        "metadata_sha256": hashlib.sha256(args.metadata.read_bytes()).hexdigest(),
        "selection": (
            "Lowest SHA256(precontact-v1:match_id), excluding first ten schema-development "
            "matches; chronological 60/20/20 split before quality exclusions"
        ),
        "matches": records,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    if args.manifest.exists() and json.loads(args.manifest.read_text()) != manifest:
        raise ValueError("Refusing to change existing frozen cohort")
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ledger = {
        "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "results": [],
    }
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(acquire, (str(row["match_id"]), str(args.output_dir))) for row in records
        ]
        for future in as_completed(futures):
            row = future.result()
            ledger["results"].append(row)
            print(
                f"Acquired {len(ledger['results'])}/{len(records)} "
                f"{row['match_id']} {row['status']}",
                flush=True,
            )
            (args.output_dir / "acquisition.json").write_text(json.dumps(ledger, indent=2) + "\n")


if __name__ == "__main__":
    main()
