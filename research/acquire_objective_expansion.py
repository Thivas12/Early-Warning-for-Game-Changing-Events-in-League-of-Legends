"""Outcome-independent, chronological expansion of development data only."""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from research.acquire_precontact import METADATA_SHA256, REPOSITORY, REVISION, acquire


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--workers", type=int, default=32)
    args = parser.parse_args()
    path = Path("data/external/betty/matches.parquet")
    if hashlib.sha256(path.read_bytes()).hexdigest() != METADATA_SHA256:
        raise ValueError("Metadata changed")
    meta = pd.read_parquet(path, columns=["match_id", "start_time", "duration_sec", "league_id"])
    excluded = set(meta.sort_values("match_id").head(10).match_id)
    previous_paths = [
        Path("reports") / f"{stem}-cohort-2026-09-30.json"
        for stem in ("precontact", "precontact-replication", "command-anticipation")
    ]
    for old in previous_paths:
        excluded.update(r["match_id"] for r in json.loads(old.read_text())["matches"])
    unused = meta[~meta.match_id.isin(excluded)]
    records = []
    for split, count in (("train", 600), ("calibration", 150)):
        subset = (
            unused[unused.start_time < 1756021999].copy()
            if split == "train"
            else unused[unused.start_time.between(1756021999, 1760390735)].copy()
        )
        subset["key"] = subset.match_id.map(
            lambda mid, split=split: hashlib.sha256(
                f"objective-expansion-v1:{split}:{mid}".encode()
            ).hexdigest()
        )
        chosen = (
            subset.sort_values("key")
            .head(count)
            .drop(columns="key")
            .sort_values(["start_time", "match_id"])
            .to_dict("records")
        )
        if len(chosen) != count:
            raise ValueError("Insufficient unused development candidates")
        for row in chosen:
            row["split"] = split
        records.extend(chosen)
    manifest = {
        "repository": REPOSITORY,
        "revision": REVISION,
        "metadata_sha256": METADATA_SHA256,
        "excluded_manifests": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in previous_paths
        },
        "selection": (
            "600 train + 150 calibration, lowest split-specific SHA256, "
            "disjoint chronological development only"
        ),
        "matches": records,
    }
    destination = Path("reports/objective-expansion-cohort-2026-09-30.json")
    if destination.exists() and json.loads(destination.read_text()) != manifest:
        raise ValueError("Frozen expansion changed")
    destination.write_text(json.dumps(manifest, indent=2) + "\n")
    if args.plan_only:
        print("Frozen 600 training and 150 calibration candidates", flush=True)
        return
    root = Path("data/external/betty-objective-expansion")
    root.mkdir(parents=True, exist_ok=True)
    ledger = {
        "manifest_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "results": [],
    }
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(acquire, (str(r["match_id"]), str(root))) for r in records]
        for future in as_completed(futures):
            row = future.result()
            ledger["results"].append(row)
            print(len(ledger["results"]), "/ 750", row["status"], flush=True)
            temporary = root / "acquisition.partial"
            temporary.write_text(json.dumps(ledger, indent=2) + "\n")
            temporary.replace(root / "acquisition.json")


if __name__ == "__main__":
    main()
