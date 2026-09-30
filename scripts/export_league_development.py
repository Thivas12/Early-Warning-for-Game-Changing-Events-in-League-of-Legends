#!/usr/bin/env python3
"""Export the reviewed League development cache without opening test payloads.

Standalone standard-library script: no package installation, GPU or training.
The source freeze is pinned to the user's completed coordination-screen run.
This checks provenance and numeric array envelopes, not scientific validity.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import re
import struct
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

SOURCE_FREEZE_SHA256 = "29930b83632e79a527e856595cfbf1f3e4ee99fa55824448009c55ca86dedd8f"
CELL_MATCHES = 3000
SHARD_MATCHES = 100
PATCHES = {
    "train": ("16.12", "16.13", "16.14", "16.15"),
    "calibration": ("16.16",),
    "test": ("16.17",),
}
VARIANTS = {"b3": 27, "snapshot": 52, "history": 158, "coordination": 179}
ROW_KEYS = ("match_id", "regional_route", "game_version_patch", "game_creation_ms")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def source_path(root: Path, relative: str) -> Path:
    """Refuse symbolic links, including intermediate components."""
    path = root
    for part in Path(relative).parts:
        path = path / part
        require(not path.is_symlink(), f"Symbolic link is not an export source: {path}")
    require(path.is_file(), f"Missing League prerequisite: {path}")
    return path


def development_split(split: dict) -> dict:
    require(split.get("schema_version") == "league-ews-final-split-v1", "Wrong split schema")
    partitions = split.get("partitions", {})
    require(set(partitions) == set(PATCHES), "Wrong split partitions")
    seen = set()
    exported = {}
    for partition, patches in PATCHES.items():
        entries = partitions[partition]
        require(len(entries) == CELL_MATCHES * 2 * len(patches), "Wrong split population")
        cells = Counter()
        previous = (-1, "")
        cleaned = []
        for row in entries:
            match_id, route, patch, created = (row[key] for key in ROW_KEYS)
            require(
                isinstance(match_id, str)
                and re.fullmatch(r"(?:EUW1|NA1)_[0-9]+", match_id) is not None
                and route in ("europe", "americas")
                and match_id.startswith("EUW1_" if route == "europe" else "NA1_")
                and patch in patches
                and type(created) is int
                and created >= 0,
                "Invalid League split membership",
            )
            order = (created, match_id)
            require(match_id not in seen and order >= previous, "Duplicate/unordered split")
            seen.add(match_id)
            previous = order
            cells[(route, patch)] += 1
            if partition != "test":
                cleaned.append({key: row[key] for key in ROW_KEYS})
        require(
            cells
            == Counter({(r, p): CELL_MATCHES for r in ("europe", "americas") for p in patches}),
            "Wrong route/patch population",
        )
        if partition != "test":
            exported[partition] = cleaned
    return {
        "schema_version": "league-ews-development-split-v1",
        "partitions": exported,
        "test_membership_exported": False,
    }


def check_numeric_envelopes(path: Path, rows: int, matches: int) -> None:
    """Inspect bounded NPY headers without NumPy or pickle deserialization."""
    expected = {
        "x.npy": ("<f4", (rows, VARIANTS["coordination"])),
        "y.npy": ("|i1", (rows,)),
        "times.npy": ("<i8", (rows,)),
        "events.npy": ("<i8", None),
        "offsets.npy": ("<i8", (matches + 1,)),
        "event_offsets.npy": ("<i8", (matches + 1,)),
    }
    with zipfile.ZipFile(path) as archive:
        require(
            len(archive.namelist()) == len(expected) and set(archive.namelist()) == set(expected),
            f"Unexpected array members: {path.name}",
        )
        for name, (dtype, shape) in expected.items():
            with archive.open(name) as stream:
                require(stream.read(6) == b"\x93NUMPY", "Invalid NPY magic")
                version = stream.read(2)
                require(version in (b"\x01\x00", b"\x02\x00"), "Unsupported NPY version")
                size_bytes = 2 if version == b"\x01\x00" else 4
                header_size = struct.unpack(
                    "<H" if size_bytes == 2 else "<I", stream.read(size_bytes)
                )[0]
                require(header_size <= 16384, "Oversized array header")
                header = ast.literal_eval(stream.read(header_size).decode("latin1"))
                require(isinstance(header, dict), "Invalid array header")
                dimensions = header.get("shape")
                require(
                    header.get("descr") == dtype
                    and header.get("fortran_order") is False
                    and isinstance(dimensions, tuple)
                    and all(type(n) is int and n >= 0 for n in dimensions)
                    and (dimensions == shape if shape is not None else len(dimensions) == 1),
                    f"Unexpected numeric dtype or shape: {path.name}/{name}",
                )
                expected_bytes = (
                    8 + size_bytes + header_size + math.prod(dimensions) * int(dtype[-1])
                )
                require(archive.getinfo(name).file_size == expected_bytes, "Wrong array byte count")


def export(repo: Path, output: Path | None = None) -> dict:
    repo = repo.resolve(strict=True)
    cache = "data/private/coordination-screen-v1"
    freeze_bytes = source_path(repo, f"{cache}/freeze.json").read_bytes()
    binding = digest(freeze_bytes)
    require(binding == SOURCE_FREEZE_SHA256, "Cache is not the reviewed League source freeze")
    freeze = json.loads(freeze_bytes)
    plan = freeze.get("plan", {})
    test_count = CELL_MATCHES * 2
    require(
        freeze.get("schema_version") == "league-ews-coordination-screen-freeze-v1"
        and plan.get("schema_version") == "league-ews-coordination-screen-plan-v1"
        and plan.get("target") == "dragon-within-60-seconds-in-actual-match"
        and plan.get("test_access") == "prohibited"
        and plan.get("variants") == VARIANTS
        and plan.get("final_fit_patches") == list(PATCHES["train"])
        and len(plan.get("features", [])) == VARIANTS["coordination"]
        and freeze.get("test_matches_unread") == test_count,
        "Cache does not describe the expected League experiment",
    )
    summary_bytes = source_path(repo, f"{cache}/summary.json").read_bytes()
    summary = json.loads(summary_bytes)
    require(
        summary.get("schema_version") == "league-ews-coordination-screen-summary-v1"
        and summary.get("status") == "complete-exploratory-calibration-screen"
        and summary.get("freeze_sha256") == binding
        and summary.get("test_matches_unread") == test_count
        and set(summary.get("models", {})) == set(VARIANTS),
        "Completed League summary is missing or does not bind to this freeze",
    )
    split_bytes = source_path(repo, "data/private/final-split.json").read_bytes()
    require(digest(split_bytes) == freeze.get("split_sha256"), "Split checksum differs from freeze")
    split = json.loads(split_bytes)
    for key in ("processed_audit_sha256", "processing_manifest_sha256"):
        require(
            split.get(key) == freeze.get(key) and isinstance(split.get(key), str), f"Wrong {key}"
        )
    development = development_split(split)
    development["source_split_sha256"] = digest(split_bytes)
    members: dict[str, bytes | Path] = {
        "freeze.json": freeze_bytes,
        "split-development.json": encoded(development),
    }
    hashes = {name: digest(value) for name, value in members.items() if isinstance(value, bytes)}
    totals = {}
    for partition, entries in development["partitions"].items():
        row_count = 0
        for start in range(0, len(entries), SHARD_MATCHES):
            name = f"shards/{partition}.{start:05d}.npz"
            path = source_path(repo, f"{cache}/{name}")
            meta_path = source_path(repo, f"{cache}/{name[:-4]}.json")
            meta = json.loads(meta_path.read_bytes())
            count = min(SHARD_MATCHES, len(entries) - start)
            require(
                meta.get("freeze_sha256") == binding
                and meta.get("matches") == count
                and type(meta.get("rows")) is int
                and meta["rows"] >= count,
                f"Invalid shard binding or population: {name}",
            )
            checksum = file_digest(path)
            require(checksum == meta.get("sha256"), f"Shard checksum mismatch: {name}")
            check_numeric_envelopes(path, meta["rows"], count)
            members[name] = path
            hashes[name] = checksum
            sidecar = name[:-4] + ".json"
            members[sidecar] = encoded(
                {k: meta[k] for k in ("freeze_sha256", "sha256", "rows", "matches")}
            )
            hashes[sidecar] = digest(members[sidecar])
            row_count += meta["rows"]
        totals[partition] = {"matches": len(entries), "rows": row_count}
        print(f"Validated {partition}: {len(entries):,} matches, {row_count:,} rows", flush=True)
    require(
        sum(item["rows"] for item in totals.values()) * VARIANTS["coordination"] * 4
        == freeze.get("feature_storage_bytes"),
        "Total feature rows differ from frozen population",
    )
    manifest = {
        "schema_version": "league-ews-development-export-v1",
        "game": "League of Legends",
        "source_freeze_sha256": binding,
        "source_summary_sha256": digest(summary_bytes),
        "source_split_sha256": digest(split_bytes),
        "target": plan["target"],
        "partitions": totals,
        "test_payloads_opened_by_exporter": 0,
        "test_membership_exported": False,
        "entries_sha256": hashes,
        "validation_limit": "Bindings and numeric headers; validate array contents before fitting",
    }
    members["manifest.json"] = encoded(manifest)
    output = (
        output or repo / "data/private/league-development-export-v1/development.zip"
    ).absolute()
    require(not output.exists() and not output.is_symlink(), f"Output already exists: {output}")
    require(
        not output.resolve().is_relative_to((repo / cache).resolve()),
        "Output is inside source cache",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".league-export-", dir=output.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED) as archive:
            for name, value in members.items():
                if isinstance(value, bytes):
                    archive.writestr(name, value)
                else:
                    # Hash exactly the bytes copied, rejecting a concurrently changed shard.
                    copied = hashlib.sha256()
                    with (
                        value.open("rb") as source,
                        archive.open(name, "w", force_zip64=True) as target,
                    ):
                        for chunk in iter(lambda: source.read(1024 * 1024), b""):
                            copied.update(chunk)
                            target.write(chunk)
                    require(
                        copied.hexdigest() == hashes[name], f"Source changed during export: {name}"
                    )
        # Same-directory hard link publishes atomically and never replaces an existing file.
        os.link(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return {"path": str(output), "bytes": output.stat().st_size, "sha256": file_digest(output)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output", type=Path, help="New ZIP path; existing files are never replaced"
    )
    args = parser.parse_args()
    try:
        result = export(args.repo, args.output)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        SyntaxError,
        struct.error,
        zipfile.BadZipFile,
    ) as error:
        parser.exit(
            1, f"League export stopped: {error}\nNo test payloads were opened; no training ran.\n"
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
