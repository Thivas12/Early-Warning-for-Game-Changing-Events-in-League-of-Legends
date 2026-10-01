"""Boundary checks for the independent audit; no empirical data or training."""

import numpy as np
import pytest

from scripts.audit_neural_results import check_report, reference_counts


def test_reference_replay_obeys_cooldown_and_excludes_simultaneous_events():
    got = reference_counts(
        np.array([0, 5000, 10000, 60000, 120000]),
        np.array([10000, 25000, 60000, 150000]),
        np.full(5, 0.9),
        0.5,
        30,
    )
    assert got == [4, 2, 2, 3, 1, 3]


def test_reference_counts_one_credit_and_late_warning_burden():
    got = reference_counts(np.array([0]), np.array([9999, 30000]), np.array([0.9]), 0.5, 30)
    assert got == [2, 1, 0, 1, 0, 1]


@pytest.mark.parametrize("horizon", [30, 60])
def test_reference_accepts_exact_useful_lead_boundaries(horizon):
    for event in (horizon * 1000 // 3, horizon * 1000):
        assert reference_counts(
            np.array([0]), np.array([event]), np.array([0.5]), 0.5, horizon
        ) == [1, 1, 1, 1, 0, 1]


def test_no_warning_policy_preserves_opportunities():
    assert reference_counts(np.array([0]), np.array([10000]), np.array([1.0]), None, 30) == [
        1,
        0,
        0,
        0,
        0,
        1,
    ]


def test_reference_preserves_saved_float32_score_semantics():
    score = np.float32(0.1)
    threshold = float(score) + 1e-10
    assert reference_counts(np.array([0]), np.array([10000]), np.array([score]), threshold, 30) == [
        1,
        0,
        0,
        0,
        0,
        1,
    ]


def test_report_check_rejects_incorrect_burden():
    report = {
        "matches": 1,
        "events": 2,
        "matched_events": 1,
        "timely_matched_events": 0,
        "alerts": 1,
        "timely_opportunities": 1,
        "event_recall": 0.5,
        "timely_event_recall": 0,
        "timely_precision": 0,
        "false_alerts_per_match": 0,
        "late_alerts_per_match": 1,
        "non_timely_alerts_per_match": 1,
    }
    counts = np.array([[2, 1, 0, 1, 0, 1]])
    check_report(counts, report)
    with pytest.raises(ValueError, match="non_timely_alerts_per_match"):
        check_report(counts, {**report, "non_timely_alerts_per_match": 0})
