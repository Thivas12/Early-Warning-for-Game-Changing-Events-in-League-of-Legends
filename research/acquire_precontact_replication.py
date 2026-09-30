"""Frozen disjoint late-period validation cohort for the invariant-feature follow-up."""

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
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--original-manifest", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=24)
    args = parser.parse_args()
    if hashlib.sha256(args.metadata.read_bytes()).hexdigest() != METADATA_SHA256:
        raise ValueError("Metadata SHA256 mismatch")
    original = json.loads(args.original_manifest.read_text())
    excluded = {r["match_id"] for r in original["matches"]}
    cutoff = min(r["start_time"] for r in original["matches"] if r["split"] == "evaluation")
    meta = pd.read_parquet(
        args.metadata, columns=["match_id", "start_time", "duration_sec", "league_id"]
    )
    eligible = meta[~meta.match_id.isin(excluded) & (meta.start_time >= cutoff)].copy()
    eligible["key"] = eligible.match_id.map(
        lambda mid: hashlib.sha256(f"precontact-replication-v1:{mid}".encode()).hexdigest()
    )
    selected = (
        eligible.sort_values("key")
        .head(200)
        .drop(columns="key")
        .sort_values(["start_time", "match_id"])
    )
    records = selected.to_dict("records")
    for row in records:
        row["split"] = "evaluation"
    if len(records) != 200:
        raise ValueError("Insufficient eligible fresh matches")
    manifest = {
        "repository": REPOSITORY,
        "revision": REVISION,
        "metadata_sha256": METADATA_SHA256,
        "selection": (
            "200 lowest SHA256(precontact-replication-v1:match_id), disjoint from "
            "original 300, at or after original evaluation start"
        ),
        "late_period_cutoff": cutoff,
        "original_manifest_sha256": hashlib.sha256(args.original_manifest.read_bytes()).hexdigest(),
        "matches": records,
    }
    if args.manifest.exists() and json.loads(args.manifest.read_text()) != manifest:
        raise ValueError("Frozen replication cohort changed")
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ledger = {
        "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "results": [],
    }
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(acquire, (str(r["match_id"]), str(args.output_dir))) for r in records
        ]
        for future in as_completed(futures):
            row = future.result()
            ledger["results"].append(row)
            print(
                f"Acquired {len(ledger['results'])}/200 {row['match_id']} {row['status']}",
                flush=True,
            )
            (args.output_dir / "acquisition.json").write_text(json.dumps(ledger, indent=2) + "\n")


if __name__ == "__main__":
    main()
