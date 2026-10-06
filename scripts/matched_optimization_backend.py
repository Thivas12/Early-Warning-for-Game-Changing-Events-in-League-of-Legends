"""Matched useful-lead loss weighting for the original GRU and TCN controls."""

from league_ews.notebook_ews import NotebookEWSBackend
from scripts.timely_optimization_backend import TimelyOptimizationBackend

VARIANTS = {
    f"{weight}_{architecture}": {
        "architecture": architecture,
        "weights": (1.0, 2.0, 2.5) if weight == "original" else (11 / 6,) * 3,
        "aggregation": "sum",
    }
    for architecture in ("leagueews", "tcn", "gru")
    for weight in ("original", "equal")
}
NEW_VARIANTS = ("equal_tcn", "original_gru", "equal_gru")


class MatchedOptimizationBackend(TimelyOptimizationBackend):
    """Reuse the verified update stream; change only the original encoder family."""

    def __init__(self, seed, device="cpu", *, variant):
        if variant not in VARIANTS:
            raise ValueError("Unknown matched architecture control")
        spec = VARIANTS[variant]
        NotebookEWSBackend.__init__(self, seed, device, family=spec["architecture"])
        self.variant = variant
        self.weights = spec["weights"]
        self.aggregation = spec["aggregation"]
