import numpy as np
import pytest

from league_ews.metrics import probabilistic_metrics


def test_probabilistic_metrics_include_calibration_and_prevalence() -> None:
    result = probabilistic_metrics(np.asarray([0, 0, 1, 1]), np.asarray([0.1, 0.2, 0.8, 0.9]))
    assert result["roc_auc"] == pytest.approx(1.0)
    assert result["average_precision"] == pytest.approx(1.0)
    assert result["prevalence"] == pytest.approx(0.5)
    assert result["brier"] == pytest.approx(0.025)


def test_single_class_auc_is_null() -> None:
    result = probabilistic_metrics(np.asarray([0, 0]), np.asarray([0.1, 0.2]))
    assert result["roc_auc"] is None


def test_bad_probabilities_are_rejected() -> None:
    with pytest.raises(ValueError, match="finite"):
        probabilistic_metrics(np.asarray([0]), np.asarray([np.nan]))
