"""Causal, within-match sequence windows for the registered B4 temporal baseline."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np

from league_ews.baseline_floor import LABELS
from league_ews.tabular_baseline import FEATURES
from league_ews.tabular_baseline import _rows as tabular_rows

STEPS = 8
SEQUENCE_FEATURES = (
    *(f"value.{name}" for name in FEATURES),
    *(f"missing.{name}" for name in FEATURES),
    "age_minutes",
)


@dataclass(frozen=True)
class CausalSequences:
    """One match's masked windows and separately stored future targets."""

    inputs: np.ndarray
    history_mask: np.ndarray
    targets: np.ndarray
    times_ms: np.ndarray


def build_causal_sequences(payload: Mapping[str, Any], match_id: str) -> CausalSequences:
    """Right-align up to eight real observations ending at the prediction time.

    Missing numeric values become zero with an explicit missingness channel.
    Zero padding is distinguished by history_mask. Values are still unscaled;
    a future B4 trainer must fit scaling on the training partition alone.
    """

    rows = list(tabular_rows(payload, match_id, LABELS[0]))
    observations = payload["timeline"]["observations"]
    label_rows = payload["labels"]
    if not rows or len(rows) != len(observations) or len(rows) != len(label_rows):
        raise ValueError("B4 sequence observations or labels are incomplete")
    times = np.asarray([row["timestamp_ms"] for row in observations], dtype=np.int64)
    if (times < 0).any() or (np.diff(times) <= 0).any():
        raise ValueError("B4 observation times must strictly increase")
    base = np.asarray([vector for vector, _ in rows], dtype=np.float64)
    if base.shape != (len(times), len(FEATURES)) or np.isinf(base).any():
        raise ValueError("B4 features must have supported finite or missing values")
    targets = np.empty((len(times), len(LABELS)), dtype=np.int8)
    for index, label_row in enumerate(label_rows):
        if not isinstance(label_row, dict) or label_row.get("timestamp_ms") != times[index]:
            raise ValueError("B4 label time differs from prediction time")
        for column, label in enumerate(LABELS):
            value = label_row.get(label)
            if type(value) is not int or value not in (0, 1):
                raise ValueError("B4 targets must be binary integers")
            targets[index, column] = value
        if targets[index, 0] != rows[index][1]:
            raise ValueError("B4 target differs from the causal tabular path")
    channels = len(SEQUENCE_FEATURES)
    windows = np.zeros((len(times), STEPS, channels), dtype=np.float32)
    mask = np.zeros((len(times), STEPS), dtype=np.bool_)
    cleaned = np.nan_to_num(base, nan=0.0).astype(np.float32)
    missing = np.isnan(base).astype(np.float32)
    for index, current in enumerate(times):
        start = max(0, index - STEPS + 1)
        count = index - start + 1
        output = windows[index, STEPS - count :]
        output[:, : len(FEATURES)] = cleaned[start : index + 1]
        output[:, len(FEATURES) : 2 * len(FEATURES)] = missing[start : index + 1]
        output[:, -1] = (current - times[start : index + 1]) / 60_000
        mask[index, STEPS - count :] = True
    return CausalSequences(windows, mask, targets, times)
