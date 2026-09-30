"""Freeze and acquire the third, disjoint public replay experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

from research.acquire_precontact import FILES, METADATA_SHA256, REPOSITORY, REVISION


def acquire_files(root: Path, row: dict, names: tuple[str, ...]) -> dict:
    result = {"match_id": str(row["match_id"]), "split": row["split"], "files": []}
    for name in names:
        path = root / str(row["match_id"]) / name
        url = f"https://huggingface.co/datasets/{REPOSITORY}/resolve/{REVISION}/{row['match_id']}/{name}"
        try:
            if not path.exists():
                with urlopen(url, timeout=90) as response:
                    raw = response.read(30_000_001)
                if len(raw) > 30_000_000 or raw[:4] != b"PAR1" or raw[-4:] != b"PAR1":
                    raise ValueError("Not a bounded complete Parquet file")
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix(".partial")
                temporary.write_bytes(raw)
                temporary.replace(path)
            raw = path.read_bytes()
            result["files"].append(
                {"name": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            )
        except (OSError, ValueError) as exc:
            return {**result, "status": "unavailable", "error": str(exc)}
    return {**result, "status": "complete"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--workers", type=int, default=24)
    args = parser.parse_args()
    metadata_path = Path("data/external/betty/matches.parquet")
    if hashlib.sha256(metadata_path.read_bytes()).hexdigest() != METADATA_SHA256:
        raise ValueError("Metadata hash mismatch")
    meta = pd.read_parquet(
        metadata_path, columns=["match_id", "start_time", "duration_sec", "league_id"]
    )
    old_paths = [
        Path("reports/precontact-cohort-2026-09-30.json"),
        Path("reports/precontact-replication-cohort-2026-09-30.json"),
    ]
    excluded = set(meta.sort_values("match_id").head(10).match_id)
    for path in old_paths:
        excluded.update(r["match_id"] for r in json.loads(path.read_text())["matches"])
    eligible = meta[~meta.match_id.isin(excluded) & (meta.start_time >= 1760390736)].copy()
    eligible["key"] = eligible.match_id.map(
        lambda mid: hashlib.sha256(f"command-anticipation-v1:{mid}".encode()).hexdigest()
    )
    records = (
        eligible.sort_values("key")
        .head(250)
        .drop(columns="key")
        .sort_values(["start_time", "match_id"])
        .to_dict("records")
    )
    if len(records) != 250:
        raise ValueError("Insufficient fresh matches")
    for row in records:
        row["split"] = "evaluation"
    manifest = {
        "repository": REPOSITORY,
        "revision": REVISION,
        "metadata_sha256": METADATA_SHA256,
        "selection": "250 lowest SHA256(command-anticipation-v1:match_id), late and disjoint",
        "late_period_cutoff": 1760390736,
        "excluded_manifest_sha256": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in old_paths
        },
        "matches": records,
    }
    manifest_path = Path("reports/command-anticipation-cohort-2026-09-30.json")
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise ValueError("Frozen manifest changed")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    if args.plan_only:
        print(f"Frozen {len(records)} fresh matches", flush=True)
        return
    quality = json.loads(Path("reports/precontact-quality-2026-09-30.json").read_text())
    development = [
        r for r in quality["matches"] if r["status"] == "accepted" and r["split"] != "evaluation"
    ]
    old_root = Path("data/external/betty-canonical")
    new_root = Path("data/external/betty-commands")
    new_root.mkdir(parents=True, exist_ok=True)
    ledger = {
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "results": [],
    }
    jobs = [(old_root, r, ("actions_normalized.parquet",)) for r in development]
    jobs += [(new_root, r, (*FILES, "actions_normalized.parquet")) for r in records]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(acquire_files, *job) for job in jobs]
        for future in as_completed(futures):
            result = future.result()
            ledger["results"].append(result)
            print(len(ledger["results"]), "/", len(jobs), result["status"], flush=True)
            (new_root / "acquisition.json").write_text(json.dumps(ledger, indent=2) + "\n")


if __name__ == "__main__":
    main()
