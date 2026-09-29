"""Boundary-coverage sensitivity masks for event-specific hazard forecasts.

The cutoff is the earlier of duration and final source frame. This criterion
does not distinguish verified completed termination from actual truncation:
excluded negatives may still be known actual-match outcomes. Partial-bin
inclusion also introduces a discretization approximation. See the research
assessment dated 2026-09-29 before applying these masks to training. They are
target/loss metadata, never prediction inputs; M1/M2 do not use them.
"""

from __future__ import annotations

import importlib
from typing import cast

import numpy as np

from league_ews.m1_backend import at_risk_mask


def confirmed_followup_masks(
    times_ms: np.ndarray,
    hazard_targets: np.ndarray,
    *,
    bin_seconds: int = 10,
    game_duration_ms: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return boundary masks shaped [rows, events, bins] and [rows, events, 4].

    Game duration comes from the checksum-bound Match-V5 detail screening
    record. Last source frame is a separate recorded boundary. Neither may
    silently lengthen the other. These are boundary-coverage indicators, not
    validated ascertainment status. Complete match termination can establish
    negative actual-match labels beyond the boundary. Without duration, this
    is a frame-cutoff sensitivity analysis only.
    """

    times = np.asarray(times_ms)
    targets = np.asarray(hazard_targets)
    if (
        times.ndim != 1
        or times.dtype.kind not in "iu"
        or len(times) == 0
        or times[0] < 0
        or np.any(np.diff(times) <= 0)
        or targets.shape != (len(times), 3, 6)
        or bin_seconds <= 0
        or (game_duration_ms is not None and game_duration_ms <= 0)
    ):
        raise ValueError("Follow-up requires a strictly increasing match and 3x6 hazards")
    risk = at_risk_mask(targets)
    ends = times[:, None] + (np.arange(1, 7, dtype=np.int64) * bin_seconds * 1000)
    cutoff = min(int(times[-1]), game_duration_ms) if game_duration_ms is not None else times[-1]
    complete = ends <= cutoff
    # A recorded onset is known even if the remainder of its bin is censored.
    known = complete[:, None, :] | (targets == 1)
    exposure = risk * known.astype(np.float32)
    if np.any((targets == 1) & (ends[:, None, :] - bin_seconds * 1000 >= times[-1])):
        raise ValueError("Hazard onset lies after the final source frame")
    cumulative = np.maximum.accumulate(targets, axis=-1)
    indices = np.asarray([0, 1, 2, 5])
    label_known = complete[:, None, indices] | (cumulative[:, :, indices] == 1)
    return exposure.astype(np.float32), label_known


def censored_hazard_bce(logits: object, targets: object, exposure: object) -> object:
    """Unweighted binary log loss over user-supplied exposed event bins.

    Accepts PyTorch tensors; the optional dependency is imported at call time.
    The exposure policy must be justified for the intended estimand; binary
    partial-bin masking is not an exact continuous-time exposure likelihood.
    This primitive is not used by the M1/M2 registered objectives.
    """

    torch = importlib.import_module("torch")

    if (
        not isinstance(logits, torch.Tensor)
        or not isinstance(targets, torch.Tensor)
        or not isinstance(exposure, torch.Tensor)
        or logits.shape != targets.shape
        or logits.shape != exposure.shape
        or logits.ndim != 3
        or logits.shape[1:] != (3, 6)
        or not torch.isfinite(logits).all()
        or not torch.isfinite(targets).all()
        or not torch.isfinite(exposure).all()
        or bool(torch.any(exposure < 0))
        or bool(torch.any(exposure > 1))
        or bool(torch.any((targets != 0) & (targets != 1)))
        or bool(torch.any((targets == 1) & (exposure != 1)))
        or float(exposure.sum()) <= 0
    ):
        raise ValueError("Censored hazard loss requires valid, exposed binary 3x6 targets")
    per_bin = torch.nn.functional.binary_cross_entropy_with_logits(
        logits, targets, reduction="none"
    )
    return cast(object, (per_bin * exposure).sum() / exposure.sum())
