"""Dataset integrity audit used as a gate before modelling."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
import pandas as pd

from league_ews.constants import (
    EVENTS,
    LEGACY_BROKEN_COLUMNS,
    LEGACY_HORIZONS_SECONDS,
    LEGACY_LABEL_COLUMNS,
    LEGACY_POST_MATCH_COLUMNS,
)

Severity = Literal["error", "warning", "info"]


@dataclass(frozen=True)
class Finding:
    severity: Severity
    code: str
    message: str
    columns: tuple[str, ...] = ()


@dataclass(frozen=True)
class DatasetAudit:
    rows: int
    columns: int
    matches: int
    positive_rates: dict[str, float]
    constant_columns: tuple[str, ...]
    findings: tuple[Finding, ...]

    @property
    def passed(self) -> bool:
        return not any(finding.severity == "error" for finding in self.findings)

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "rows": self.rows,
            "columns": self.columns,
            "matches": self.matches,
            "positive_rates": self.positive_rates,
            "constant_columns": list(self.constant_columns),
            "findings": [asdict(finding) for finding in self.findings],
        }


def _label_findings(frame: pd.DataFrame) -> list[Finding]:
    findings: list[Finding] = []
    missing = tuple(column for column in LEGACY_LABEL_COLUMNS if column not in frame)
    if missing:
        findings.append(Finding("error", "missing-labels", "Required labels are absent", missing))
        return findings

    non_binary = tuple(
        column
        for column in LEGACY_LABEL_COLUMNS
        if not set(frame[column].dropna().unique()).issubset({0, 1})
    )
    if non_binary:
        findings.append(Finding("error", "non-binary-labels", "Labels must be binary", non_binary))

    for event in EVENTS:
        columns = [f"y_{event}_{horizon}" for horizon in LEGACY_HORIZONS_SECONDS]
        values = frame[columns].to_numpy()
        violations = int(((values[:, 0] > values[:, 1]) | (values[:, 1] > values[:, 2])).sum())
        if violations:
            findings.append(
                Finding(
                    "error",
                    "horizon-nesting",
                    f"{event} labels violate 10s <= 20s <= 30s in {violations} rows",
                    tuple(columns),
                )
            )
    return findings


def _temporal_findings(frame: pd.DataFrame) -> list[Finding]:
    findings: list[Finding] = []
    if not {"match_id", "t"}.issubset(frame.columns):
        return [Finding("error", "missing-index", "match_id and t are required")]
    duplicate_count = int(frame.duplicated(["match_id", "t"]).sum())
    if duplicate_count:
        findings.append(
            Finding(
                "error", "duplicate-time", f"Found {duplicate_count} duplicate match timestamps"
            )
        )
    if (frame["t"] < 0).any():
        findings.append(Finding("error", "negative-time", "Timestamps cannot be negative", ("t",)))

    ordered = frame.sort_values(["match_id", "t"])
    deltas = ordered.groupby("match_id", observed=True)["t"].diff().dropna()
    if not deltas.empty and (deltas <= 0).any():
        findings.append(Finding("error", "non-monotonic-time", "Match time must increase"))
    if not deltas.empty and float(deltas.median()) == 10.0:
        snapshot = [
            column for column in ("gold_blue", "gold_red", "xp_blue", "xp_red") if column in frame
        ]
        if snapshot:
            changed = ordered.groupby("match_id", observed=True)[snapshot].diff().ne(0).any(axis=1)
            changed_rate = float(changed.mean())
            if changed_rate < 0.30:
                findings.append(
                    Finding(
                        "warning",
                        "synthetic-cadence",
                        "The 10-second grid mostly forward-fills lower-frequency "
                        f"participant frames; core snapshots change in {changed_rate:.1%} of rows",
                        tuple(snapshot),
                    )
                )
    return findings


def audit_legacy_frame(frame: pd.DataFrame) -> DatasetAudit:
    """Audit the released legacy table without silently repairing it."""

    findings = [*_label_findings(frame), *_temporal_findings(frame)]
    constants = tuple(
        sorted(column for column in frame.columns if frame[column].nunique(dropna=False) <= 1)
    )

    broken_present = tuple(column for column in LEGACY_BROKEN_COLUMNS if column in frame)
    broken_constant = tuple(column for column in broken_present if column in constants)
    if broken_constant:
        findings.append(
            Finding(
                "error",
                "broken-features",
                "Known legacy fields contain generator defaults instead of observations",
                broken_constant,
            )
        )

    leaked = tuple(column for column in LEGACY_POST_MATCH_COLUMNS if column in frame)
    if leaked:
        constant_within_match = tuple(
            column
            for column in leaked
            if int(frame.groupby("match_id", observed=True)[column].nunique(dropna=False).max())
            <= 1
        )
        findings.append(
            Finding(
                "error",
                "future-leakage",
                "End-of-match aggregates are repeated at prediction timestamps",
                constant_within_match or leaked,
            )
        )

    if "game_version" not in frame and "gameVersion" not in frame:
        findings.append(
            Finding(
                "warning",
                "missing-patch",
                "The release has no patch identifier, so future-patch evaluation is impossible",
            )
        )

    if any(isinstance(column, str) and column.startswith("y_teamfight_") for column in frame):
        findings.append(
            Finding(
                "warning",
                "teamfight-proxy",
                "The legacy generator can emit several pseudo-events for one three-kill episode",
                tuple(column for column in LEGACY_LABEL_COLUMNS if "teamfight" in column),
            )
        )

    rates = {
        column: float(np.mean(frame[column].to_numpy(dtype=np.float64)))
        for column in LEGACY_LABEL_COLUMNS
        if column in frame
    }
    matches = int(frame["match_id"].nunique()) if "match_id" in frame else 0
    return DatasetAudit(
        rows=len(frame),
        columns=len(frame.columns),
        matches=matches,
        positive_rates=rates,
        constant_columns=constants,
        findings=tuple(findings),
    )
