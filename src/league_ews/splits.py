"""Group-safe chronological splitting."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

import pandas as pd

from league_ews.constants import SPLIT_POLICY_VERSION


def _match_sort_key(match_id: str) -> tuple[str, int, str]:
    match = re.search(r"^(.*?)[_-]?(\d+)$", match_id)
    if match is None:
        return (match_id, -1, match_id)
    return (match.group(1), int(match.group(2)), match_id)


@dataclass(frozen=True)
class MatchSplit:
    """Immutable split membership at complete-match granularity."""

    train: tuple[str, ...]
    validation: tuple[str, ...]
    test: tuple[str, ...]
    policy_version: str = SPLIT_POLICY_VERSION

    def __post_init__(self) -> None:
        sets = [set(self.train), set(self.validation), set(self.test)]
        if sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2]:
            raise ValueError("Match split contains overlapping groups")
        if not all(sets):
            raise ValueError("Train, validation and test splits must all be non-empty")

    @property
    def digest(self) -> str:
        payload = json.dumps(
            {
                "policy_version": self.policy_version,
                "train": self.train,
                "validation": self.validation,
                "test": self.test,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def assignment(self) -> dict[str, str]:
        return {
            **dict.fromkeys(self.train, "train"),
            **dict.fromkeys(self.validation, "validation"),
            **dict.fromkeys(self.test, "test"),
        }


def chronological_match_split(
    match_ids: pd.Series,
    *,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> MatchSplit:
    """Split complete matches using stable numeric match-ID order.

    Match ID is only a chronology proxy in the legacy release. Research-v2 raw
    manifests must use game-creation timestamps and patch boundaries instead.
    """

    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between zero and one")
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between zero and one")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("train and validation fractions must leave a test split")

    unique = sorted({str(value) for value in match_ids.dropna().unique()}, key=_match_sort_key)
    if len(unique) < 3:
        raise ValueError("At least three matches are required")
    train_end = max(1, int(len(unique) * train_fraction))
    validation_end = max(train_end + 1, int(len(unique) * (train_fraction + validation_fraction)))
    validation_end = min(validation_end, len(unique) - 1)
    return MatchSplit(
        train=tuple(unique[:train_end]),
        validation=tuple(unique[train_end:validation_end]),
        test=tuple(unique[validation_end:]),
    )


def apply_split(frame: pd.DataFrame, split: MatchSplit) -> dict[str, pd.DataFrame]:
    """Return copied train/validation/test frames with no shared matches."""

    membership = frame["match_id"].astype(str).map(split.assignment())
    if membership.isna().any():
        raise ValueError("Frame contains matches absent from split manifest")
    return {name: frame.loc[membership.eq(name)].copy() for name in ("train", "validation", "test")}
