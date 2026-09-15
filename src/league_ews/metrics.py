"""Row-level diagnostics kept secondary to event-level utility."""

from __future__ import annotations

import math

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


def probabilistic_metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, float | None]:
    """Calculate discrimination and calibration metrics safely."""

    truth = np.asarray(labels, dtype=np.int8)
    risk = np.asarray(probabilities, dtype=np.float64)
    if truth.shape != risk.shape:
        raise ValueError("labels and probabilities must have identical shapes")
    if not np.isfinite(risk).all() or ((risk < 0) | (risk > 1)).any():
        raise ValueError("probabilities must be finite values in [0, 1]")
    classes = np.unique(truth)
    auc = float(roc_auc_score(truth, risk)) if len(classes) == 2 else math.nan
    average_precision = float(average_precision_score(truth, risk)) if np.any(truth == 1) else 0.0
    return {
        "roc_auc": None if math.isnan(auc) else auc,
        "average_precision": average_precision,
        "brier": float(brier_score_loss(truth, risk)),
        "prevalence": float(np.mean(truth)),
    }
