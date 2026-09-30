"""Checkpoint the unchanged strict adapter while the frozen cohort downloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from research.precontact_data import build_one


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()
    manifest_path = Path("reports/objective-expansion-cohort-2026-09-30.json")
    manifest = json.loads(manifest_path.read_text())
    root = Path("data/external/betty-objective-expansion")
    output = Path("data/processed/objective-expansion")
    output.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output / "quality-checkpoint.json"
    bindings = {
        "manifest_sha256": digest(manifest_path),
        "adapter_sha256": digest(Path("research/precontact_data.py")),
    }
    checkpoint = (
        json.loads(checkpoint_path.read_text())
        if checkpoint_path.exists()
        else {**bindings, "matches": {}}
    )
    if any(checkpoint[k] != v for k, v in bindings.items()):
        raise ValueError("Staging inputs changed")
    for row in checkpoint["matches"].values():
        if (
            row["status"] == "accepted"
            and digest(output / f"{row['match_id']}.npz") != row["arrays_sha256"]
        ):
            raise ValueError("Staged arrays changed")
    expected = {str(r["match_id"]) for r in manifest["matches"]}
    if len(expected) != 750:
        raise ValueError("Wrong expansion manifest")
    while True:
        ledger = json.loads((root / "acquisition.json").read_text())
        if ledger["manifest_sha256"] != bindings["manifest_sha256"]:
            raise ValueError("Acquisition uses a different manifest")
        acquired = {r["match_id"]: r for r in ledger["results"]}
        if not set(acquired).issubset(expected) or len(acquired) != len(ledger["results"]):
            raise ValueError("Unexpected or duplicate acquisition")
        if not args.watch and len(acquired) != 750:
            raise ValueError("Acquisition incomplete")
        for row in manifest["matches"]:
            mid = str(row["match_id"])
            if mid not in acquired or mid in checkpoint["matches"]:
                continue
            entry = acquired[mid]
            try:
                if entry["status"] != "complete":
                    raise ValueError("download_unavailable")
                for source in entry["files"]:
                    if digest(root / mid / source["name"]) != source["sha256"]:
                        raise ValueError("source_hash_mismatch")
                arrays, details = build_one(root, row)
                path = output / f"{mid}.npz"
                np.savez_compressed(path, **arrays)
                details["arrays_sha256"] = digest(path)
            except (ValueError, KeyError, OSError) as error:
                details = {**row, "status": "excluded", "reason": str(error)}
            checkpoint["matches"][mid] = details
            save(checkpoint_path, checkpoint)
            print(len(checkpoint["matches"]), mid, details["status"], flush=True)
        if len(acquired) == 750:
            if set(checkpoint["matches"]) != expected:
                raise ValueError("Incomplete quality audit")
            report = {
                **bindings,
                "acquisition": ledger,
                "matches": [checkpoint["matches"][str(r["match_id"])] for r in manifest["matches"]],
            }
            save(Path("reports/objective-expansion-quality-2026-09-30.json"), report)
            print("Complete frozen-cohort quality report written", flush=True)
            return
        time.sleep(2)


if __name__ == "__main__":
    main()
