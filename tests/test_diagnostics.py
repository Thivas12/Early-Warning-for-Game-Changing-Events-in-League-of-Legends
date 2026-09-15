from __future__ import annotations

import pandas as pd
import pytest

from league_ews.diagnostics import diagnose_legacy_sequence_split


def _long_matches(matches: int = 40, rows: int = 80) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "match_id": [f"m{match}" for match in range(matches) for _ in range(rows)],
            "t": [step * 10 for _ in range(matches) for step in range(rows)],
        }
    )


def test_legacy_sequence_split_reproduces_contamination() -> None:
    report = diagnose_legacy_sequence_split(_long_matches())
    assert report.base_windows == 360
    assert report.augmented_windows == 1080
    assert report.partitions["test"].family_seen_elsewhere_rate > 0.95
    assert report.partitions["test"].match_seen_elsewhere_rate == 1.0
    assert report.partitions["test"].overlapping_window_elsewhere_rate == 1.0
    assert report.to_dict()["passed"] is False


def test_sequence_split_diagnostic_is_deterministic() -> None:
    frame = _long_matches(matches=5)
    assert diagnose_legacy_sequence_split(frame) == diagnose_legacy_sequence_split(frame)


@pytest.mark.parametrize(
    ("sequence_length", "step", "copies"),
    [(0, 5, 3), (40, 0, 3), (40, 5, 0)],
)
def test_invalid_window_configuration_is_rejected(
    sequence_length: int, step: int, copies: int
) -> None:
    with pytest.raises(ValueError, match="positive"):
        diagnose_legacy_sequence_split(
            _long_matches(),
            sequence_length=sequence_length,
            step=step,
            augmented_copies=copies,
        )


def test_too_short_matches_are_rejected() -> None:
    with pytest.raises(ValueError, match="long enough"):
        diagnose_legacy_sequence_split(_long_matches(rows=10))
