import pandas as pd
import pytest

from league_ews.splits import MatchSplit, apply_split, chronological_match_split


def test_chronological_match_split_is_group_disjoint_and_stable() -> None:
    match_ids = pd.Series([f"EUW1_{number}" for number in [11, 10, 13, 12, 14, 15]] * 2)
    split = chronological_match_split(match_ids, train_fraction=0.5, validation_fraction=0.25)
    assert split.train == ("EUW1_10", "EUW1_11", "EUW1_12")
    assert split.validation == ("EUW1_13",)
    assert split.test == ("EUW1_14", "EUW1_15")
    assert len(split.digest) == 64


def test_apply_split_never_shares_a_match() -> None:
    frame = pd.DataFrame({"match_id": ["a", "a", "b", "c"], "t": [0, 10, 0, 0]})
    split = MatchSplit(train=("a",), validation=("b",), test=("c",))
    partitions = apply_split(frame, split)
    assert set(partitions["train"]["match_id"]) == {"a"}
    assert set(partitions["validation"]["match_id"]) == {"b"}
    assert set(partitions["test"]["match_id"]) == {"c"}


def test_overlapping_manifest_is_rejected() -> None:
    with pytest.raises(ValueError, match="overlapping"):
        MatchSplit(train=("a",), validation=("a",), test=("c",))


@pytest.mark.parametrize(
    ("train", "validation"),
    [(0, 0.2), (1, 0.2), (0.7, 0), (0.9, 0.2)],
)
def test_invalid_split_fractions_are_rejected(train: float, validation: float) -> None:
    with pytest.raises(ValueError):
        chronological_match_split(
            pd.Series(["a", "b", "c"]),
            train_fraction=train,
            validation_fraction=validation,
        )
