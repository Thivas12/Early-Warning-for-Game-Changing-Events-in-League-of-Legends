"""Terminal follow-up must not turn unknown future time into a negative."""

import numpy as np
import pytest

from league_ews.cli import build_parser
from league_ews.m3_followup import censored_hazard_bce, confirmed_followup_masks
from league_ews.m3_followup_audit import _accumulate, _counts, _source_times_and_hazards


def test_positive_partial_bin_is_known_but_unobserved_negative_tail_is_censored() -> None:
    times = np.array([0, 25_000], dtype=np.int64)
    hazards = np.zeros((2, 3, 6), np.float32)
    hazards[0, 0, 2] = 1
    exposure, labels_known = confirmed_followup_masks(times, hazards)
    assert exposure.shape == (2, 3, 6)
    assert exposure[0, 0].tolist() == [1, 1, 1, 0, 0, 0]
    assert exposure[0, 1].tolist() == [1, 1, 0, 0, 0, 0]
    assert exposure[1].sum() == 0
    assert labels_known[0, 0].tolist() == [True, True, True, True]
    assert labels_known[0, 1].tolist() == [True, True, False, False]
    assert not labels_known[1].any()


def test_full_bin_boundary_is_known_and_no_future_frame_is_imputed() -> None:
    times = np.array([0, 10_000], dtype=np.int64)
    hazards = np.zeros((2, 3, 6), np.float32)
    exposure, labels_known = confirmed_followup_masks(times, hazards)
    assert exposure[0, :, 0].tolist() == [1, 1, 1]
    assert exposure[0, :, 1:].sum() == 0
    assert labels_known[0, :, 0].all()
    assert not labels_known[0, :, 1:].any()


def test_screened_duration_shortens_exposure_without_erasing_observed_positives() -> None:
    times = np.array([0, 25_000], dtype=np.int64)
    hazards = np.zeros((2, 3, 6), np.float32)
    hazards[0, 0, 2] = 1  # Recorded event at 22 s; detail duration may be rounded to 21 s.
    exposure, known = confirmed_followup_masks(times, hazards, game_duration_ms=21_000)
    assert exposure[0, 0].tolist() == [1, 1, 1, 0, 0, 0]
    assert exposure[0, 1].tolist() == [1, 1, 0, 0, 0, 0]
    assert known[0, 0, 2] and not known[0, 1, 2]
    with pytest.raises(ValueError, match="strictly increasing"):
        confirmed_followup_masks(times, hazards, game_duration_ms=0)


def test_source_event_contract_and_negative_counts() -> None:
    payload = {
        "schema_version": "league-ews-processed-match-v1",
        "timeline": {
            "match_id": "EUW1_1",
            "observations": [{"timestamp_ms": 0}, {"timestamp_ms": 25_000}],
        },
        "event_index": {"baron_ms": [22_000], "dragon_ms": [], "teamfight_ms": []},
    }
    times, hazard = _source_times_and_hazards(payload, "EUW1_1")
    assert hazard[0, 0].tolist() == [0, 0, 1, 0, 0, 0]
    labels = np.maximum.accumulate(hazard, axis=-1)[:, :, [0, 1, 2, 5]].reshape(-1, 12)
    counts = _counts()
    _accumulate(counts, times, hazard, labels, 21_000)
    assert counts["matches"] == 1
    assert counts["rows"] == 2
    assert counts["positive_labels"][2:4] == [1, 1]
    assert counts["negative_labels_without_full_followup"][7] == 2
    assert counts["original_loss_bins"] > counts["confirmed_loss_bins"]
    assert counts["last_frame_after_duration"] == 1
    assert counts["maximum_absolute_gap_ms"] == 4000
    payload["event_index"]["baron_ms"] = [26_000]
    with pytest.raises(ValueError, match="outside confirmed follow-up"):
        _source_times_and_hazards(payload, "EUW1_1")


def test_censored_loss_ignores_unknown_negative_and_checks_exposure() -> None:
    torch = pytest.importorskip("torch")
    logits = torch.tensor([[[0.0] * 6] * 3], requires_grad=True)
    truth = torch.zeros((1, 3, 6))
    exposure = torch.zeros_like(truth)
    exposure[0, :, 0] = 1
    loss = censored_hazard_bce(logits, truth, exposure)
    assert float(loss) == pytest.approx(np.log(2))
    loss.backward()
    assert logits.grad is not None
    assert torch.count_nonzero(logits.grad) == 3
    truth[0, 0, 1] = 1
    with pytest.raises(ValueError, match="exposed binary"):
        censored_hazard_bce(logits, truth, exposure)


def test_cli_requires_bound_inputs() -> None:
    parser = build_parser()
    arguments = parser.parse_args(
        [
            "audit-confirmed-followup",
            "--processed",
            "processed",
            "--split",
            "split.json",
            "--staging-root",
            "stage",
            "--selection-root",
            "selected",
            "--output",
            "audit.json",
        ]
    )
    assert arguments.command == "audit-confirmed-followup"
