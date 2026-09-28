"""Rebuild fixed-minute histories from frozen processed-derived graph snapshots."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np

from league_ews.m1_backend import right_pad_graphs
from league_ews.m1_graph_staging import MATCHES_PER_SHARD
from league_ews.m1_graph_window import STEPS


def verified_match_offsets(root: Path, entry: dict[str, Any]) -> np.ndarray:
    """Read the partition boundaries from a checksum-bound staged shard."""

    path = root / "shards" / entry["file"]
    if entry["partition"] not in ("train", "calibration") or (
        hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]
    ):
        raise ValueError("Fixed-minute source shard differs from the frozen manifest")
    with np.load(path, allow_pickle=False) as shard:
        offsets = shard["match_offsets"]
    if (
        offsets.shape != (MATCHES_PER_SHARD + 1,)
        or offsets.dtype != np.int64
        or offsets[0] != 0
        or offsets[-1] != entry["observations"]
        or np.any(np.diff(offsets) <= 0)
    ):
        raise ValueError("Fixed-minute match boundaries differ from the frozen shard")
    return offsets


def fixed_minute_grid(
    nodes: np.ndarray,
    edges: np.ndarray,
    mask: np.ndarray,
    ages: np.ndarray,
    offsets: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Select latest genuine frame at each elapsed-minute anchor per match.

    Frozen native windows contain every genuine prediction frame as their last
    frame. Their adjacent age records the exact timestamp gap (rounded back
    to integer milliseconds); the other ages cross-check that reconstruction.
    The absolute match start time cancels when choosing relative anchors.
    """

    right_pad_graphs(nodes, edges, mask, ages)
    if (
        offsets.ndim != 1
        or offsets.dtype != np.int64
        or len(offsets) != MATCHES_PER_SHARD + 1
        or offsets[0] != 0
        or offsets[-1] != len(nodes)
        or np.any(np.diff(offsets) <= 0)
    ):
        raise ValueError("Fixed-minute grid requires exact match boundaries")
    result_nodes = np.zeros_like(nodes)
    result_edges = np.zeros_like(edges)
    result_mask = np.zeros_like(mask)
    result_ages = np.zeros_like(ages)
    for start, end in zip(offsets[:-1], offsets[1:], strict=True):
        first, last = int(start), int(end)
        count = last - first
        expected_lengths = np.minimum(np.arange(count) + 1, STEPS)
        if not np.array_equal(mask[first:last].sum(axis=1), expected_lengths):
            raise ValueError("Fixed-minute source histories cross a match boundary")
        times = np.zeros(count, dtype=np.int64)
        for local in range(1, count):
            row = first + local
            interval = int(np.rint(float(ages[row, -2]) * 60_000))
            if interval <= 0 or abs(float(ages[row, -2]) * 60_000 - interval) >= 0.5:
                raise ValueError("Fixed-minute source cadence cannot be reconstructed")
            times[local] = times[local - 1] + interval
            for lag in range(1, min(STEPS, local + 1)):
                expected_ms = times[local] - times[local - lag]
                observed_ms = float(ages[row, -1 - lag]) * 60_000
                if abs(observed_ms - expected_ms) >= 0.5:
                    raise ValueError("Fixed-minute source ages disagree with genuine frames")
        for local in range(count):
            anchor_times = times[local] - np.arange(STEPS - 1, -1, -1) * 60_000
            chosen = np.searchsorted(times[: local + 1], anchor_times, side="right") - 1
            # Preserve order while removing repeated observations from sparse cadence.
            unique = list(dict.fromkeys(int(index) for index in chosen if index >= 0))
            length = len(unique)
            row = first + local
            selected = first + np.asarray(unique, dtype=np.int64)
            result_nodes[row, -length:] = nodes[selected, -1]
            result_edges[row, -length:] = edges[selected, -1]
            result_mask[row, -length:] = True
            result_ages[row, -length:] = (times[local] - times[unique]) / 60_000
            if unique[-1] != local:
                raise ValueError("Fixed-minute grid lost the current genuine observation")
    right_pad_graphs(result_nodes, result_edges, result_mask, result_ages)
    return result_nodes, result_edges, result_mask, result_ages
