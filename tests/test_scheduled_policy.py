"""Falsify mathematical credit assignment, causality, and source isolation."""

from __future__ import annotations

import copy
import itertools
import json

import numpy as np
import pytest

from league_ews.coordination_experiment import sha
from league_ews.scheduled_experiment import completed, evaluate, freeze, run
from league_ews.scheduled_model import MODELS, Settings, fit, predict, runtime
from league_ews.scheduled_policy import (
    action_probabilities,
    decision_trace,
    exclusion_matrix,
    marginal_counts,
    select_policy,
    summary,
    torch_marginals,
)
from tests.test_timely_experiment import arrays, cached_fixture


def exhaustive(times, events, probabilities):
    counts = np.zeros(6)
    for coins in itertools.product((False, True), repeat=len(times)):
        weight = np.prod([p if c else 1 - p for p, c in zip(probabilities, coins, strict=True)])
        last = -(10**9)
        row = np.zeros(6)
        row[0] = len(events)
        for t, coin in zip(times, coins, strict=True):
            if not coin or t - last < 60_000:
                continue
            last = t
            row[3] += 1
            future = [e for e in events if t < e <= t + 60_000]
            if future:
                row[1] += 1
                row[2] += future[0] - t >= 20_000
            else:
                row[4] += 1
        counts += weight * row
    return counts


def test_exact_marginals_equal_exhaustive_policy_enumeration_and_gradients():
    torch = pytest.importorskip("torch")
    times = np.array([0, 10_000, 35_000, 60_000, 71_000, 130_000])
    events = (30_000, 80_000, 100_000, 170_000)
    terminal = tuple([*times, 180_000])
    trace = decision_trace(terminal, events, frame_only=True)
    p = np.array([0.2, 0.9, 0.4, 0.8, 0.5, 0.3])
    analytic = marginal_counts([trace], [p])[0]
    np.testing.assert_allclose(analytic[:5], exhaustive(times, events, p)[:5], atol=1e-12)
    t = torch.tensor(times[None, :])
    blocked = exclusion_matrix(t, torch.ones_like(t, dtype=torch.bool))
    probabilities = torch.tensor(p[None, :], dtype=torch.float64, requires_grad=True)
    assert torch.autograd.gradcheck(lambda v: torch_marginals(v, blocked), (probabilities,))
    marginals = torch_marginals(probabilities, blocked)
    assert float(marginals.sum().detach()) == pytest.approx(analytic[3])
    # Exact boundary is available: an alert at 0 does not block one at 60 seconds.
    deterministic = marginal_counts([trace], [np.ones(6)])[0]
    assert deterministic[3] == 3
    # No duplicate event credit even when the event sequence is unusually dense.
    assert analytic[2] <= len(events)


def test_credit_gradient_penalizes_blocking_a_better_future_alarm():
    torch = pytest.importorskip("torch")
    p = torch.tensor([[0.5, 0.9]], dtype=torch.float64, requires_grad=True)
    block = exclusion_matrix(torch.tensor([[0, 30_000]]), torch.tensor([[True, True]]))
    expected_reward = (torch_marginals(p, block) * torch.tensor([[0.6, 1.0]])).sum()
    expected_reward.backward()
    # Independent utility would assign a positive .6 gradient to the first alarm.
    assert p.grad[0, 0] == pytest.approx(-0.3)
    assert p.grad[0, 1] == pytest.approx(0.5)


def test_causal_ticks_do_not_receive_future_frames_or_unobserved_event_feedback():
    t = (3_000, 65_000, 141_000)
    before = decision_trace(t, (61_000, 95_000))
    after = decision_trace(t, ())
    np.testing.assert_array_equal(before.rows, after.rows)
    np.testing.assert_array_equal(before.ages, after.ages)
    assert before.times.tolist() == [
        10_000,
        20_000,
        30_000,
        40_000,
        50_000,
        60_000,
        70_000,
        80_000,
        90_000,
        100_000,
        110_000,
        120_000,
    ]
    assert np.all(np.asarray(t)[before.rows] <= before.times)
    assert np.all(before.ages < 60_000)
    # A new snapshot after a prefix cannot alter that prefix, including for irregular cadence.
    extension = decision_trace((3_000, 65_000, 150_000, 200_000), ())
    keep = extension.times < 141_000
    np.testing.assert_array_equal(before.times, extension.times[keep])
    np.testing.assert_array_equal(before.rows, extension.rows[keep])
    # Boundary labels: next event only; past event at the tick itself is not forecast.
    trace = decision_trace((0, 100_000), (20_000, 60_000))
    assert trace.timely[:5].tolist() == [True, False, True, True, True]
    assert trace.late[:5].tolist() == [False, True, False, False, False]
    assert decision_trace((0,), ()).events == 0
    for stamps, events in (((1, 1), ()), ((0, 1), (2,)), ((0, 2), (1, 1))):
        with pytest.raises(ValueError):
            decision_trace(stamps, events)


def test_between_frame_opportunities_are_not_new_observations():
    times, events = (0, 60_000, 120_000), (75_000,)
    frames, ticks = decision_trace(times, events, frame_only=True), decision_trace(times, events)
    assert frames.opportunities == 0
    assert ticks.opportunities == 1
    # At 20 seconds, a causal decision still sees observation zero.
    assert ticks.rows[2] == 0 and ticks.ages[2] == 20_000
    assert summary(marginal_counts([ticks], [ticks.timely.astype(float)]))["timely_recall"] == 1


def test_policy_tuning_never_reads_later_outcomes_and_handles_no_events():
    traces = [decision_trace((0, 60_000, 120_000), (30_000,)) for _ in range(8)]
    logits = [np.where(t.timely, 2.0, -3.0) for t in traces]
    early, later, routes = list(range(4)), list(range(4, 8)), ["a", "b"] * 4
    first, _ = evaluate(traces, logits, early, later, routes)
    altered = traces[:4] + [decision_trace((0, 60_000, 120_000), ()) for _ in later]
    second, _ = evaluate(altered, logits, early, later, routes)
    assert first["selected_policy"] == second["selected_policy"]
    assert second["evaluation"]["timely_recall"] is None
    assert first["all_route_budgets_met"]
    with pytest.raises(ValueError):
        evaluate(traces, logits, early, early, routes)
    with pytest.raises(ValueError):
        select_policy(traces, logits, [], budget=-1)
    for probabilities in ([np.array([np.nan])], []):
        with pytest.raises(ValueError):
            marginal_counts(traces[:1], probabilities)
    with pytest.raises(ValueError):
        action_probabilities(np.zeros(3), 0, "invalid")
    empty = decision_trace((0,), ())
    assert marginal_counts([empty], [np.empty(0)]).shape == (1, 6)


def test_all_matched_models_train_and_future_features_do_not_change_past_predictions():
    torch = pytest.importorskip("torch")
    data = arrays(12)
    traces = [decision_trace(t, e) for t, e in zip(data["times"], data["events"], strict=True)]
    settings = Settings(epochs=3, warm_epochs=1, batch_matches=6, width=8)
    for name in MODELS:
        payload, info = fit(data, traces, ["a", "b"] * 6, name, 2, settings, "cpu", progress=False)
        scores = predict(data, traces, payload, settings, "cpu")
        assert all(np.isfinite(s).all() for s in scores)
        assert len(info["training"]) == 3
        assert info["device"] == "cpu"
        changed = copy.deepcopy(data)
        changed["x"][1:4] = 99999
        later = predict(changed, traces, payload, settings, "cpu")
        np.testing.assert_array_equal(scores[0][:6], later[0][:6])
        # Labels are never consumed by the network forward pass.
        changed["events"] = [()] * 12
        no_events = predict(changed, traces, payload, settings, "cpu")
        np.testing.assert_array_equal(later[0], no_events[0])
    with pytest.raises(ValueError):
        fit(data, traces, [], "unknown", 0, settings, "cpu")
    assert runtime("auto")[1] in ("cuda", "cpu")
    with pytest.raises(ValueError):
        runtime("bad-device")
    if not torch.cuda.is_available():
        with pytest.raises(RuntimeError, match="CUDA is unavailable"):
            runtime("cuda")


def test_end_to_end_resume_freeze_integrity_and_sealed_test(tmp_path, monkeypatch):
    pytest.importorskip("torch")
    import league_ews.scheduled_experiment as experiment

    source, processed, split, audit, output = cached_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        experiment, "_chronological_halves", lambda rows: (list(range(12)), list(range(12, 24)))
    )
    original = {str(p.relative_to(source)): sha(p) for p in source.rglob("*") if p.is_file()}
    settings = Settings(epochs=3, warm_epochs=1, batch_matches=12, width=8)
    args = (source, processed, split, audit, output)
    result = run(*args, settings=settings, seeds=(3,), device="cpu", max_new_models=1)
    assert result["status"].startswith("paused")
    checkpoint = sha(output / "history-bce-3" / "model.pt")
    result = run(*args, settings=settings, seeds=(3,), device="cpu")
    assert result["test_matches_unread"] == 6000
    assert len(result["models"]) == len(MODELS)
    assert not result["decision"]["supports_further_study"]  # requires >=3 training seeds
    assert sha(output / "history-bce-3" / "model.pt") == checkpoint
    assert original == {
        str(p.relative_to(source)): sha(p) for p in source.rglob("*") if p.is_file()
    }
    assert run(*args, settings=settings, seeds=(3,), device="cpu") == result
    for altered in ((4,), (3, 4)):
        with pytest.raises(ValueError, match="freeze differs"):
            freeze(*args, settings, altered, "cpu")
    with pytest.raises(ValueError, match="separate"):
        freeze(source, processed, split, audit, source, settings, (3,), "cpu")
    with pytest.raises(ValueError, match="seeds"):
        run(*args, settings=settings, seeds=(), device="cpu")
    folder = output / "history-bce-3"
    (folder / "model.pt").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="binding"):
        completed(folder, sha(output / "freeze.json"))
    frozen = json.loads((output / "freeze.json").read_text())
    assert "test" not in " ".join(frozen["source_shards"])


def test_padding_and_unequal_cadence_do_not_change_match_expectations():
    short = decision_trace((0, 60_000), (30_000,))
    long = decision_trace((0, 70_000, 140_000, 210_000), (50_000, 160_000))
    p, q = np.full(len(short.times), 0.35), np.full(len(long.times), 0.65)
    alone = marginal_counts([short], [p])[0]
    together = marginal_counts([short, long], [p, q])[0]
    np.testing.assert_array_equal(alone, together)
    assert short.times[-1] < 60_000
