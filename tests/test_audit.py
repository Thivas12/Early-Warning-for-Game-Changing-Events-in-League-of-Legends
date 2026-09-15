import pandas as pd

from league_ews.audit import audit_legacy_frame
from league_ews.constants import LEGACY_LABEL_COLUMNS


def _frame() -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for match_index in range(3):
        for timestamp in (0, 10, 20):
            row: dict[str, float | int | str] = {
                "match_id": f"EUW1_{match_index}",
                "t": timestamp,
                "gold_blue": 2500 + timestamp,
                "gold_red": 2500 + timestamp,
                "xp_blue": timestamp,
                "xp_red": timestamp,
                "alive_t1": 0,
                "low_hp_t1": 5,
                "kills_blue": match_index + 10,
            }
            row.update(dict.fromkeys(LEGACY_LABEL_COLUMNS, 0))
            rows.append(row)
    return pd.DataFrame(rows)


def test_legacy_audit_identifies_broken_and_leaked_columns() -> None:
    report = audit_legacy_frame(_frame())
    codes = {finding.code for finding in report.findings}
    assert not report.passed
    assert "broken-features" in codes
    assert "future-leakage" in codes
    assert "missing-patch" in codes
    assert report.rows == 9
    assert report.matches == 3


def test_horizon_nesting_violation_is_an_error() -> None:
    frame = _frame()
    frame.loc[0, "y_baron_10"] = 1
    report = audit_legacy_frame(frame)
    assert any(finding.code == "horizon-nesting" for finding in report.findings)


def test_duplicate_match_time_is_an_error() -> None:
    frame = pd.concat([_frame(), _frame().iloc[[0]]], ignore_index=True)
    report = audit_legacy_frame(frame)
    assert any(finding.code == "duplicate-time" for finding in report.findings)


def test_audit_serialisation_is_plain_data() -> None:
    payload = audit_legacy_frame(_frame()).to_dict()
    assert payload["rows"] == 9
    assert isinstance(payload["findings"], list)
