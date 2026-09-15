"""Reproduce legacy sequence-split contamination without allocating feature tensors."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import numpy.typing as npt
import pandas as pd
from sklearn.model_selection import train_test_split


@dataclass(frozen=True)
class PartitionContamination:
    examples: int
    source_matches: int
    family_seen_elsewhere_rate: float
    match_seen_elsewhere_rate: float
    overlapping_window_elsewhere_rate: float


@dataclass(frozen=True)
class SequenceSplitDiagnostic:
    policy: str
    sequence_length: int
    step: int
    augmented_copies: int
    base_windows: int
    augmented_windows: int
    partitions: dict[str, PartitionContamination]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["passed"] = False
        payload["finding"] = (
            "Random splitting after windowing and augmentation contaminates evaluation. "
            "Split complete matches before either operation."
        )
        return payload


def _window_metadata(
    frame: pd.DataFrame,
    *,
    sequence_length: int,
    step: int,
    augmented_copies: int,
) -> pd.DataFrame:
    if sequence_length < 1 or step < 1 or augmented_copies < 1:
        raise ValueError("sequence_length, step and augmented_copies must be positive")
    if not {"match_id", "t"}.issubset(frame):
        raise ValueError("match_id and t are required")

    records: list[tuple[str, int, int, int]] = []
    family = 0
    for match_id, match in frame.groupby("match_id", sort=True, observed=True):
        rows = len(match)
        for start in range(0, rows - sequence_length + 1, step):
            records.append((str(match_id), start, start + sequence_length - 1, family))
            family += 1
    if not records:
        raise ValueError("No match is long enough to create a sequence")

    base = pd.DataFrame(records, columns=["match_id", "start", "end", "family"])
    copies = [base.assign(augmentation=copy) for copy in range(augmented_copies)]
    return pd.concat(copies, ignore_index=True)


def _overlap_rate(metadata: pd.DataFrame, partition: str) -> float:
    selected = metadata.loc[metadata["partition"].eq(partition)]
    other = metadata.loc[~metadata["partition"].eq(partition)]
    starts_by_match: dict[str, npt.NDArray[np.int64]] = {
        str(match_id): np.sort(group["start"].to_numpy(dtype=np.int64))
        for match_id, group in other.groupby("match_id", observed=True)
    }
    overlap = 0
    columns = selected[["match_id", "start", "end"]]
    for match_id, raw_start, raw_end in columns.itertuples(index=False, name=None):
        starts = starts_by_match.get(str(match_id))
        if starts is None:
            continue
        start = int(str(raw_start))
        end = int(str(raw_end))
        position = int(starts.searchsorted(end, side="right"))
        if position and int(starts[position - 1]) <= end:
            other_start = int(starts[position - 1])
            if other_start <= end and other_start + (end - start) >= start:
                overlap += 1
    return overlap / len(selected) if len(selected) else 0.0


def diagnose_legacy_sequence_split(
    frame: pd.DataFrame,
    *,
    sequence_length: int = 40,
    step: int = 5,
    augmented_copies: int = 3,
    random_state: int = 42,
) -> SequenceSplitDiagnostic:
    """Recreate the MSc v1 split and measure cross-partition relationships."""

    metadata = _window_metadata(
        frame,
        sequence_length=sequence_length,
        step=step,
        augmented_copies=augmented_copies,
    )
    indices = np.arange(len(metadata), dtype=np.int64)
    train_validation, test = train_test_split(indices, test_size=0.10, random_state=random_state)
    train, validation = train_test_split(
        train_validation, test_size=0.20, random_state=random_state
    )
    assignment = np.empty(len(metadata), dtype=object)
    assignment[train] = "train"
    assignment[validation] = "validation"
    assignment[test] = "test"
    metadata["partition"] = assignment

    partitions: dict[str, PartitionContamination] = {}
    for name in ("train", "validation", "test"):
        selected = metadata.loc[metadata["partition"].eq(name)]
        other = metadata.loc[~metadata["partition"].eq(name)]
        partitions[name] = PartitionContamination(
            examples=len(selected),
            source_matches=int(selected["match_id"].nunique()),
            family_seen_elsewhere_rate=float(selected["family"].isin(set(other["family"])).mean()),
            match_seen_elsewhere_rate=float(
                selected["match_id"].isin(set(other["match_id"])).mean()
            ),
            overlapping_window_elsewhere_rate=_overlap_rate(metadata, name),
        )

    return SequenceSplitDiagnostic(
        policy="msc-v1-window-jitter-then-random-split",
        sequence_length=sequence_length,
        step=step,
        augmented_copies=augmented_copies,
        base_windows=len(metadata) // augmented_copies,
        augmented_windows=len(metadata),
        partitions=partitions,
    )
