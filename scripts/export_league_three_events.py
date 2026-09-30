#!/usr/bin/env python3
"""Export compact, numeric League development data for all original event heads.

Uses the existing audited processed matches, not API collection or model training.
Stores each observed frame once; eight-frame B4 histories reconstruct exactly.
Only train/calibration payloads are opened. Test membership is not exported.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.b4_sequence import SEQUENCE_FEATURES, STEPS, build_causal_sequences
from league_ews.baseline_floor import LABELS, _read_match
from league_ews.constants import EVENTS
from league_ews.coordination_experiment import bind_inputs
from league_ews.tabular_baseline import FEATURES
from scripts.export_league_development import (
    SOURCE_FREEZE_SHA256,
    development_split,
    digest,
    encoded,
    file_digest,
    require,
    source_path,
)

SHARD_MATCHES = 500
SCHEMA = "league-ews-three-event-development-v1"


def compact_match(payload: dict[str, Any], match_id: str) -> dict[str, np.ndarray]:
    """Use the audited feature builder; keep outcomes separate from input arrays."""
    sequence = build_causal_sequences(payload, match_id)
    n = len(FEATURES)
    current = sequence.inputs[:, -1]
    arrays = {
        "values": current[:, :n].copy(),
        "missing": current[:, n : 2 * n].astype(np.bool_),
        "times_ms": sequence.times_ms.copy(),
        "targets": sequence.targets.copy(),
    }
    times = arrays["times_ms"]
    for index, event in enumerate(EVENTS):
        raw = payload["event_index"][f"{event}_ms"]
        require(
            isinstance(raw, list) and all(type(t) is int and 0 <= t <= times[-1] for t in raw),
            "Invalid complete-match event index",
        )
        event_times = np.asarray(raw, dtype=np.int64)
        require(bool(np.all(np.diff(event_times) > 0)), "Events must be strictly ordered")
        arrays[f"{event}_ms"] = event_times
        for h, horizon in enumerate((10, 20, 30, 60)):
            expected = (
                np.searchsorted(event_times, times + horizon * 1000, side="right")
                - np.searchsorted(event_times, times, side="right")
            ) > 0
            require(
                np.array_equal(expected, arrays["targets"][:, index * 4 + h]),
                "Stored labels differ from exact event times",
            )
    restored, mask = rebuild_histories(arrays)
    require(
        np.array_equal(restored, sequence.inputs) and np.array_equal(mask, sequence.history_mask),
        "Compact representation does not reproduce the audited B4 inputs",
    )
    return arrays


def rebuild_histories(arrays: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """Reconstruct one complete match, with no cross-match or future observations."""
    values, missing, times = (arrays[k] for k in ("values", "missing", "times_ms"))
    count, width = len(times), len(FEATURES)
    require(
        count > 0
        and values.shape == missing.shape == (count, width)
        and values.dtype == np.float32
        and missing.dtype == np.bool_
        and times.dtype == np.int64
        and times.shape == (count,)
        and bool(np.all(times >= 0) and np.all(np.diff(times) > 0))
        and bool(np.isfinite(values).all())
        and bool(np.all(values[missing] == 0)),
        "Invalid compact frame arrays",
    )
    windows = np.zeros((count, STEPS, len(SEQUENCE_FEATURES)), dtype=np.float32)
    mask = np.zeros((count, STEPS), dtype=np.bool_)
    for row, timestamp in enumerate(times):
        start = max(0, row - STEPS + 1)
        length = row - start + 1
        target = windows[row, -length:]
        target[:, :width] = values[start : row + 1]
        target[:, width : 2 * width] = missing[start : row + 1]
        target[:, -1] = (timestamp - times[start : row + 1]) / 60_000
        mask[row, -length:] = True
    return windows, mask


def join_matches(matches: list[dict[str, np.ndarray]]) -> dict[str, np.ndarray]:
    require(bool(matches), "Empty export shard")
    arrays = {key: np.concatenate([m[key] for m in matches]) for key in matches[0]}
    for key, output in (
        ("times_ms", "match_offsets"),
        *((f"{event}_ms", f"{event}_offsets") for event in EVENTS),
    ):
        arrays[output] = np.cumsum([0, *(len(m[key]) for m in matches)], dtype=np.int64)
    return arrays


def source_binding(repo: Path, data_repo: Path) -> tuple[dict, dict, dict, dict]:
    """Bind to the already reviewed cohort, including its original split hashes."""
    require(
        Path(build_causal_sequences.__code__.co_filename).resolve()
        == repo / "src/league_ews/b4_sequence.py",
        "Imported feature code is not from the requested checkout",
    )
    freeze_path = source_path(data_repo, "data/private/coordination-screen-v1/freeze.json")
    require(file_digest(freeze_path) == SOURCE_FREEZE_SHA256, "Wrong reviewed source freeze")
    freeze = json.loads(freeze_path.read_bytes())
    paths = {
        "split_sha256": "data/private/final-split.json",
        "processed_audit_sha256": "data/private/final-processed-validation.json",
        "processing_manifest_sha256": "data/processed/registered-final/processing-manifest.json",
    }
    binding = {
        key: file_digest(source_path(data_repo, relative)) for key, relative in paths.items()
    }
    require(
        all(value == freeze.get(key) for key, value in binding.items()), "Source binding changed"
    )
    split, records = bind_inputs(
        data_repo / "data/processed/registered-final",
        data_repo / paths["split_sha256"],
        data_repo / paths["processed_audit_sha256"],
    )
    development = development_split(split)
    return development, records, binding, paths


def export(
    repo: Path, output: Path | None = None, *, data_repo: Path | None = None
) -> dict[str, Any]:
    repo = repo.resolve(strict=True)
    data_repo = (data_repo or repo).resolve(strict=True)
    output = (
        output or data_repo / "data/private/league-three-event-export-v1/development.zip"
    ).absolute()
    require(not output.exists() and not output.is_symlink(), "Output already exists")
    require(
        not output.resolve().is_relative_to((data_repo / "data/processed").resolve()),
        "Output cannot be placed inside processed source data",
    )
    development, records, binding, bound_paths = source_binding(repo, data_repo)
    source_files = [
        *sorted((repo / "src/league_ews").glob("*.py")),
        repo / "scripts/export_league_development.py",
        Path(__file__).resolve(),
    ]
    source_hashes = {str(p.relative_to(repo)): file_digest(p) for p in source_files}
    require(
        Path(__file__).resolve() == repo / "scripts/export_league_three_events.py",
        "Run this exporter from its own checkout",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".league-three-event-", dir=output.parent)
    os.close(descriptor)
    temporary = Path(name)
    inventory: list[dict[str, Any]] = []
    totals: dict[str, Any] = {}
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED) as archive:
            membership_bytes = encoded(development)
            archive.writestr("development-split.json", membership_bytes)
            for partition in ("train", "calibration"):
                entries = development["partitions"][partition]
                rows_total = 0
                for start in range(0, len(entries), SHARD_MATCHES):
                    batch = entries[start : start + SHARD_MATCHES]
                    compact = []
                    payload_hashes = []
                    for row in batch:
                        mid = row["match_id"]
                        source_path(
                            data_repo, f"data/processed/registered-final/matches/{mid}.json"
                        )
                        record = records[mid]
                        payload = dict(
                            _read_match(
                                data_repo / "data/processed/registered-final", mid, record.sha256
                            )
                        )
                        arrays = compact_match(payload, mid)
                        require(len(arrays["times_ms"]) == record.observations, "Row count changed")
                        compact.append(arrays)
                        payload_hashes.append(record.sha256)
                    joined = join_matches(compact)
                    buffer = io.BytesIO()
                    np.savez_compressed(buffer, **joined)
                    content = buffer.getvalue()
                    filename = f"shards/{partition}.{start:05d}.npz"
                    archive.writestr(filename, content)
                    rows = len(joined["times_ms"])
                    inventory.append(
                        {
                            "file": filename,
                            "sha256": digest(content),
                            "bytes": len(content),
                            "partition": partition,
                            "start": start,
                            "matches": len(batch),
                            "rows": rows,
                            "processed_match_sha256_in_split_order": payload_hashes,
                        }
                    )
                    rows_total += rows
                    print(
                        f"Exported {partition}: {start + len(batch)}/{len(entries)} matches",
                        flush=True,
                    )
                totals[partition] = {"matches": len(entries), "rows": rows_total}
            require(
                all(
                    file_digest(source_path(data_repo, bound_paths[k])) == v
                    for k, v in binding.items()
                )
                and all(file_digest(repo / k) == v for k, v in source_hashes.items()),
                "Sources changed while exporting",
            )
            manifest = {
                "schema_version": SCHEMA,
                "game": "League of Legends",
                "source_freeze_sha256": SOURCE_FREEZE_SHA256,
                "source_binding": binding,
                "source_sha256": source_hashes,
                "features": list(FEATURES),
                "sequence_features": list(SEQUENCE_FEATURES),
                "sequence_steps": STEPS,
                "targets": list(LABELS),
                "partitions": totals,
                "shards": inventory,
                "development_split_sha256": digest(membership_bytes),
                "test_payloads_opened": 0,
                "test_membership_exported": False,
                "player_identifiers_exported": False,
                "normalizer": "not exported; fit on training current frames only",
                "input_roundtrip": "checked bit-for-bit against B4 for every exported match",
                "interpretation": "development data; calibration already examined; no fresh test",
            }
            archive.writestr("manifest.json", encoded(manifest))
        os.link(temporary, output)  # Atomic publication; never overwrite an existing file.
    finally:
        temporary.unlink(missing_ok=True)
    return {"path": str(output), "bytes": output.stat().st_size, "sha256": file_digest(output)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--data-repo", type=Path, help="Existing WSL data checkout; defaults to --repo"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = export(args.repo, args.output, data_repo=args.data_repo)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"League three-event export stopped: {error}\nNo training ran.\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
