"""Validate and read the user's three-event League development export."""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np

from league_ews.b4_sequence import SEQUENCE_FEATURES, STEPS
from league_ews.baseline_floor import LABELS
from league_ews.constants import EVENTS
from league_ews.tabular_baseline import FEATURES
from scripts.export_league_development import SOURCE_FREEZE_SHA256, file_digest, require

EXPECTED_ARCHIVE = "3bdee868abe445947a8573167d4b3b561b60f5d2247f1857f6b538ff603e6a23"
EXPECTED_SPLIT = "747b92567f7c8cc869ba06e4c8a6f81bb66c74fa5607e83c4240d3dc9ecd3ecb"
EXPECTED_BINDING = {
    "processed_audit_sha256": "a3d771c0eb44dd1d4448b6fc689e9bce75842e6023f80dceaacfdd1ff82cd500",
    "processing_manifest_sha256": (
        "7696855efa99dd5d96bf3d4c92ccc9c4248215f5aa26adaea7613cc29af4b284"
    ),
    "split_sha256": "265a10f2ae7dc9ad6a956e11a52562b1091c08c5c57e3d0721db18578dd89770",
}
TOTALS = {
    "train": {"matches": 24000, "rows": 704967},
    "calibration": {"matches": 6000, "rows": 175031},
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_array_bytes(content: bytes) -> dict[str, np.ndarray]:
    with zipfile.ZipFile(io.BytesIO(content)) as inner:
        require(sum(i.file_size for i in inner.infolist()) < 64 * 1024**2, "Oversized NPZ")
        require(len(inner.namelist()) == len(set(inner.namelist())), "Duplicate NPZ names")
    with np.load(io.BytesIO(content), allow_pickle=False) as loaded:
        return {key: loaded[key] for key in loaded.files}


def validate_arrays(arrays: dict[str, np.ndarray], rows: int, matches: int) -> None:
    expected = {
        "values": (np.dtype("float32"), (rows, len(FEATURES))),
        "missing": (np.dtype("bool"), (rows, len(FEATURES))),
        "times_ms": (np.dtype("int64"), (rows,)),
        "targets": (np.dtype("int8"), (rows, len(LABELS))),
        "match_offsets": (np.dtype("int64"), (matches + 1,)),
    }
    for event in EVENTS:
        expected[f"{event}_ms"] = (np.dtype("int64"), (len(arrays.get(f"{event}_ms", [])),))
        expected[f"{event}_offsets"] = (np.dtype("int64"), (matches + 1,))
    require(set(arrays) == set(expected), "Wrong numeric array inventory")
    require(
        all(a.dtype == expected[k][0] and a.shape == expected[k][1] for k, a in arrays.items()),
        "Wrong array dtype/shape",
    )
    require(bool(np.isfinite(arrays["values"]).all()), "Nonfinite values")
    require(bool(np.all(arrays["values"][arrays["missing"]] == 0)), "Missing values are not zero")
    require(bool(np.isin(arrays["targets"], (0, 1)).all()), "Nonbinary targets")
    offsets = arrays["match_offsets"]
    require(
        offsets[0] == 0 and offsets[-1] == rows and bool(np.all(np.diff(offsets) > 0)),
        "Invalid match offsets",
    )
    for event in EVENTS:
        ends = arrays[f"{event}_offsets"]
        require(
            ends[0] == 0
            and ends[-1] == len(arrays[f"{event}_ms"])
            and bool(np.all(np.diff(ends) >= 0)),
            "Invalid event offsets",
        )
    for m in range(matches):
        a, b = offsets[m : m + 2]
        times = arrays["times_ms"][a:b]
        require(bool(np.all(times >= 0) and np.all(np.diff(times) > 0)), "Invalid match chronology")
        # Clock is independently recoverable from observation timestamps.
        require(
            np.allclose(arrays["values"][a:b, 0], times / 60000, rtol=1e-6, atol=1e-6),
            "Clock differs from observed time",
        )
        for e, event in enumerate(EVENTS):
            left, right = arrays[f"{event}_offsets"][m : m + 2]
            events = arrays[f"{event}_ms"][left:right]
            require(
                bool(
                    np.all(events >= 0)
                    and np.all(events <= times[-1])
                    and np.all(np.diff(events) > 0)
                ),
                "Invalid event chronology",
            )
            for h, horizon in enumerate((10, 20, 30, 60)):
                expected_target = np.searchsorted(
                    events, times + horizon * 1000, side="right"
                ) > np.searchsorted(events, times, side="right")
                require(
                    np.array_equal(expected_target, arrays["targets"][a:b, e * 4 + h]),
                    "Labels differ from event times",
                )


def validate_archive(path: Path, repo: Path) -> dict:
    require(file_digest(path) == EXPECTED_ARCHIVE, "Archive is not the uploaded development file")
    with zipfile.ZipFile(path) as archive:
        require(len(archive.infolist()) == 62, "Wrong archive member count")
        require(len(archive.namelist()) == len(set(archive.namelist())), "Duplicate archive names")
        manifest = json.loads(archive.read("manifest.json"))
        split_bytes = archive.read("development-split.json")
        require(
            sha(split_bytes) == EXPECTED_SPLIT == manifest["development_split_sha256"],
            "Development split changed",
        )
        split = json.loads(split_bytes)
        require(
            manifest["schema_version"] == "league-ews-three-event-development-v1"
            and manifest["game"] == "League of Legends"
            and manifest["source_freeze_sha256"] == SOURCE_FREEZE_SHA256
            and manifest["source_binding"] == EXPECTED_BINDING
            and manifest["partitions"] == TOTALS
            and manifest["features"] == list(FEATURES)
            and manifest["sequence_features"] == list(SEQUENCE_FEATURES)
            and manifest["sequence_steps"] == STEPS
            and manifest["targets"] == list(LABELS)
            and manifest["test_payloads_opened"] == 0
            and manifest["test_membership_exported"] is False
            and manifest["player_identifiers_exported"] is False,
            "Export contract differs",
        )
        require(set(split["partitions"]) == {"train", "calibration"}, "Unexpected partition")
        seen = set()
        for partition, patches in (
            ("train", ("16.12", "16.13", "16.14", "16.15")),
            ("calibration", ("16.16",)),
        ):
            entries = split["partitions"][partition]
            require(len(entries) == TOTALS[partition]["matches"], "Wrong match count")
            cells, previous = Counter(), (-1, "")
            for row in entries:
                require(
                    set(row)
                    == {"match_id", "regional_route", "game_version_patch", "game_creation_ms"},
                    "Unexpected membership fields",
                )
                mid, route, patch, created = (
                    row[k]
                    for k in (
                        "match_id",
                        "regional_route",
                        "game_version_patch",
                        "game_creation_ms",
                    )
                )
                require(
                    isinstance(mid, str)
                    and re.fullmatch(r"(?:EUW1|NA1)_\d+", mid) is not None
                    and mid not in seen,
                    "Invalid or repeated match",
                )
                require(
                    route in ("europe", "americas")
                    and patch in patches
                    and type(created) is int
                    and created >= 0,
                    "Invalid route/patch/time",
                )
                require(
                    mid.startswith("EUW1_" if route == "europe" else "NA1_")
                    and (created, mid) >= previous,
                    "Split chronology or route mismatch",
                )
                seen.add(mid)
                previous = (created, mid)
                cells[(route, patch)] += 1
            require(
                cells == Counter({(r, p): 3000 for r in ("europe", "americas") for p in patches}),
                "Unbalanced cohort",
            )
        source_mismatches = [
            p
            for p, value in manifest["source_sha256"].items()
            if not (repo / p).is_file() or file_digest(repo / p) != value
        ]
        require(not source_mismatches, f"Export source differs: {source_mismatches}")
        require(len(manifest["shards"]) == 60, "Wrong shard count")
        require(
            set(archive.namelist())
            == {
                "manifest.json",
                "development-split.json",
                *(e["file"] for e in manifest["shards"]),
            },
            "Unexpected archive members",
        )
        totals = {p: Counter() for p in TOTALS}
        for index, entry in enumerate(manifest["shards"]):
            partition = "train" if index < 48 else "calibration"
            start = (index if index < 48 else index - 48) * 500
            require(
                entry["file"] == f"shards/{partition}.{start:05d}.npz"
                and entry["partition"] == partition
                and entry["start"] == start
                and entry["matches"] == 500,
                "Wrong shard membership",
            )
            require(
                len(entry["processed_match_sha256_in_split_order"]) == 500
                and all(
                    re.fullmatch(r"[a-f0-9]{64}", v)
                    for v in entry["processed_match_sha256_in_split_order"]
                ),
                "Invalid source hashes",
            )
            content = archive.read(entry["file"])
            require(
                len(content) == entry["bytes"] and sha(content) == entry["sha256"],
                "Shard checksum mismatch",
            )
            arrays = load_array_bytes(content)
            validate_arrays(arrays, entry["rows"], 500)
            totals[partition]["rows"] += entry["rows"]
            totals[partition]["matches"] += 500
            for event in EVENTS:
                totals[partition][f"{event}_events"] += len(arrays[f"{event}_ms"])
            if (index + 1) % 12 == 0:
                print(f"Validated {index + 1}/60 League shards", flush=True)
        require(
            all(all(totals[p][k] == v for k, v in TOTALS[p].items()) for p in TOTALS),
            "Totals differ",
        )
    return {
        "schema_version": "league-compact-validation-v1",
        "archive_sha256": EXPECTED_ARCHIVE,
        "source_files_matched": len(manifest["source_sha256"]),
        "shards_validated": 60,
        "partitions": {p: dict(v) for p, v in totals.items()},
        "test_payloads_present": 0,
        "status": "passed",
        "limit": (
            "Checks the uploaded export and recorded provenance, "
            "not unavailable original raw payloads"
        ),
    }


def load_partition(path: Path, partition: str) -> tuple[dict[str, np.ndarray], list[dict]]:
    require(partition in TOTALS, "Only development partitions can be read")
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        rows = json.loads(archive.read("development-split.json"))["partitions"][partition]
        blocks = []
        for entry in manifest["shards"]:
            if entry["partition"] == partition:
                content = archive.read(entry["file"])
                require(sha(content) == entry["sha256"], "Shard changed after validation")
                blocks.append(load_array_bytes(content))
    arrays = {}
    for key in blocks[0]:
        if key.endswith("offsets"):
            parts, end = [np.array([0], dtype=np.int64)], 0
            for block in blocks:
                parts.append(block[key][1:] + end)
                end += int(block[key][-1])
            arrays[key] = np.concatenate(parts)
        else:
            arrays[key] = np.concatenate([b[key] for b in blocks])
    return arrays, rows


def tabular_features(data: dict[str, np.ndarray], family: str) -> np.ndarray:
    """Current values and missingness; history adds actual lag-1/3/7 frames and age."""
    require(family in ("snapshot", "history"), "Unknown representation")
    current = np.column_stack((data["values"], data["missing"])).astype(np.float32)
    if family == "snapshot":
        return current
    offsets, times = data["match_offsets"], data["times_ms"]
    starts = np.repeat(offsets[:-1], np.diff(offsets))
    indices = np.arange(len(times))
    parts = [current]
    for lag in (1, 3, 7):
        earlier = np.maximum(indices - lag, starts)
        # Use oldest available frame for short histories; elapsed age makes this explicit.
        parts.extend(
            (current[earlier], ((times - times[earlier]) / 60000).astype(np.float32)[:, None])
        )
    return np.concatenate(parts, axis=1)
