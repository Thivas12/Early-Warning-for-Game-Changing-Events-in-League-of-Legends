"""Policy provenance and paired-analysis checks using synthetic software fixtures."""

import json
from copy import deepcopy

import numpy as np
import pytest

from scripts.analyse_neural_screen import resample_weights
from scripts.analyse_warning_risk import PRIMARY, analyse, prior_reproduction
from scripts.evaluate_dense_policy import GRID
from scripts.evaluate_warning_risk import bind_release, evaluate_head
from scripts.warning_efficiency import BUDGETS, replay_thresholds
from scripts.warning_risk import FAMILIES, POLICIES, calibration_inputs


def test_release_is_immutable_and_cannot_be_backfilled(tmp_path):
    binding = bind_release(tmp_path, "freeze-a", "commit-a", {"source": "digest"})
    assert bind_release(tmp_path, "freeze-a", "commit-a", {"source": "digest"}) == binding
    with pytest.raises(ValueError, match="release changed"):
        bind_release(tmp_path, "freeze-b", "commit-a", {"source": "digest"})
    other = tmp_path / "other"
    (other / "early").mkdir(parents=True)
    (other / "early" / "head.json").write_text("{}")
    with pytest.raises(ValueError, match="Cannot backfill"):
        bind_release(other, "freeze-a", "commit-a", {"source": "digest"})


def test_release_blocks_existing_later_artifacts(tmp_path):
    (tmp_path / "later").mkdir()
    (tmp_path / "later" / "orphan.npz").write_bytes(b"not a real dataset")
    with pytest.raises(ValueError, match="Cannot backfill"):
        bind_release(tmp_path, "freeze-a", "commit-a", {"source": "digest"})


def test_later_replay_preserves_baseline_and_audits_every_new_policy():
    times = np.arange(7) * 60_000
    cal = {
        "match_offsets": np.array([0, 7, 14]),
        "times_ms": np.tile(times, 2),
        "baron_offsets": np.array([0, 2, 4]),
        "baron_ms": np.tile(np.array([20_000, 380_000]), 2),
    }
    probabilities = np.ones(14)
    later = np.array([0, 1])
    indices = [0, 1, len(GRID) // 2, len(GRID) - 1]
    choices = dict(zip(map(str, BUDGETS), indices, strict=True))
    selected = {"policies": {p: choices.copy() for p in POLICIES}}
    inputs = calibration_inputs(cal, probabilities, "baron", later)
    original = replay_thresholds(*inputs, tuple(GRID[i] for i in indices), 30)
    previous = {"dense_deterministic": np.moveaxis(original, 1, 0)}
    values, full, sample, activity = evaluate_head(
        cal,
        probabilities,
        {"event": "baron", "horizon": 30},
        selected,
        later,
        np.array(["europe", "americas"]),
        previous,
    )
    assert full == 6
    assert sample == 8
    np.testing.assert_array_equal(values[POLICIES[0]], previous["dense_deterministic"])
    assert values[POLICIES[1]][-1, 0, 3] == 4
    assert values[POLICIES[0]][-1, 0, 3] == 7
    assert activity[POLICIES[3]]["1.0"] == {"europe": 1, "americas": 1}
    previous["dense_deterministic"][0, 0, 0] += 1
    with pytest.raises(ValueError, match="Previous later"):
        evaluate_head(
            cal,
            probabilities,
            {"event": "baron", "horizon": 30},
            selected,
            later,
            np.array(["europe", "americas"]),
            previous,
        )


@pytest.fixture(scope="module")
def paired_fixture():
    rng = np.random.default_rng(981)
    routes = np.array(["europe"] * 8 + ["americas"] * 8)
    counts = {}
    for policy in POLICIES:
        counts[policy] = {}
        for family in FAMILIES:
            counts[policy][family] = {}
            for h in (30, 60):
                c = np.zeros((4, 3, 3, 16, 6))
                c[..., 0] = c[..., 5] = 3
                c[..., 1] = c[..., 2] = rng.integers(0, 3, size=c.shape[:-1])
                c[..., 3] = 3
                c[..., 4] = c[..., 3] - c[..., 1]
                counts[policy][family][h] = c
    results, effects, _ = analyse(counts, routes, draws=31)
    return counts, routes, results, effects


def direct_recall_draws(counts, weights):
    # Explicit match resampling totals, independent of the production einsum.
    out = []
    for w in weights:
        by_budget = []
        for budget in counts:
            by_seed = []
            for seed in budget:
                by_event = [np.dot(w, event[:, 2]) / np.dot(w, event[:, 0]) for event in seed]
                by_seed.append(np.mean(by_event))
            by_budget.append(by_seed)
        out.append(np.mean(by_budget, axis=0))
    return np.array(out)


@pytest.mark.parametrize("region", ["overall", "europe", "americas"])
def test_architecture_interval_uses_same_match_draws_for_both_models(paired_fixture, region):
    counts, routes, results, _ = paired_fixture
    idx = np.arange(16) if region == "overall" else np.flatnonzero(routes == region)
    weights = resample_weights(routes[idx], draws=31)
    a = direct_recall_draws(counts[POLICIES[3]][FAMILIES[0]][30][:, :, :, idx], weights)
    b = direct_recall_draws(counts[POLICIES[3]][FAMILIES[1]][30][:, :, :, idx], weights)
    expected = np.percentile((a - b).mean(1), [2.5, 97.5])
    got = results[region]["30"][POLICIES[3]]["mean"]["contrasts"][PRIMARY]["macro"]["timely_recall"]
    np.testing.assert_allclose(got["ci95"], expected, atol=1e-15, rtol=0)


def test_policy_effects_pair_before_bootstrap_reduction(paired_fixture):
    counts, routes, _, effects = paired_fixture
    weights = resample_weights(routes, draws=31)
    a = direct_recall_draws(counts[POLICIES[3]][FAMILIES[0]][30], weights)
    b = direct_recall_draws(counts[POLICIES[2]][FAMILIES[0]][30], weights)
    expected = np.percentile((a - b).mean(1), [2.5, 97.5])
    got = effects["overall"]["30"]["mean"][FAMILIES[0]][f"{POLICIES[3]}-minus-{POLICIES[2]}"][
        "macro"
    ]["timely_recall"]
    np.testing.assert_allclose(got["ci95"], expected, atol=1e-15, rtol=0)


def test_prior_reproduction_requires_every_shared_estimate(paired_fixture):
    _, _, results, _ = paired_fixture
    old = {
        "results": {
            r: {h: {"dense_deterministic": v[POLICIES[0]]} for h, v in hs.items()}
            for r, hs in results.items()
        }
    }
    assert prior_reproduction(results, old) == {
        "model_event_metric_groups": 150,
        "contrast_event_metric_groups": 150,
    }
    tampered = deepcopy(old)
    tampered["results"]["europe"]["60"]["dense_deterministic"]["mean"]["models"][FAMILIES[0]][
        "baron"
    ]["timely_recall"]["mean"] += 0.01
    with pytest.raises(ValueError, match="Prior model"):
        prior_reproduction(results, tampered)


def test_release_record_contains_only_bound_inputs_and_timestamp(tmp_path):
    bind_release(tmp_path, "f", "c", {"code.py": "x"})
    value = json.loads((tmp_path / "analysis-release.json").read_bytes())
    assert set(value) == {"freeze_sha256", "analysis_commit", "source_sha256", "recorded_at_utc"}
