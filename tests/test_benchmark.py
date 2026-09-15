from __future__ import annotations

import pytest

from league_ews.benchmark import run_legacy_benchmark
from tests.helpers import synthetic_legacy_frame


def test_legacy_benchmark_runs_match_disjoint_pipeline(tmp_path) -> None:
    path = tmp_path / "legacy.csv"
    synthetic_legacy_frame().to_csv(path, index=False)

    result = run_legacy_benchmark(
        path,
        baselines=("time",),
        max_iter=2,
        threshold_candidates=3,
    )

    assert result["schema_version"] == "legacy-benchmark-v1"
    assert result["dataset"]["matches"] == 12
    assert result["partitions"]["train"]["matches"] == 8
    assert len(result["results"]) == 3
    first = result["results"][0]
    assert first["feature_count"] == 1
    assert first["features"] == ["t"]
    assert 0 <= first["test"]["operational"]["threshold"] <= 1


def test_legacy_benchmark_rejects_too_small_match_limit(tmp_path) -> None:
    path = tmp_path / "legacy.csv"
    synthetic_legacy_frame(matches=3).to_csv(path, index=False)
    with pytest.raises(ValueError, match="at least three"):
        run_legacy_benchmark(path, max_matches=2)
