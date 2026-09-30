"""Implementation checks only; synthetic fixtures are not research evidence."""

from copy import deepcopy

import numpy as np
import pytest

from league_ews.alert_policy import MatchRisk
from league_ews.b4_sequence import SEQUENCE_FEATURES, build_causal_sequences
from league_ews.baseline_floor import LABELS
from league_ews.notebook_ews import FAMILIES, NotebookEWSBackend
from league_ews.notebook_policy import replay, select


def batch():
    rng = np.random.default_rng(4)
    x = rng.normal(size=(4, 8, len(SEQUENCE_FEATURES))).astype(np.float32)
    mask = np.arange(8)[None, :] >= 8 - np.asarray([1, 3, 5, 8])[:, None]
    x[~mask] = 0
    targets = rng.integers(0, 2, (4, len(LABELS)), dtype=np.int8)
    return x, mask, targets


@pytest.mark.parametrize("family", FAMILIES)
def test_all_original_event_heads_train_and_padding_cannot_change_predictions(family):
    backend = NotebookEWSBackend(10, family=family)
    x, mask, y = batch()
    initial = backend.predict_shard(x, mask)
    contaminated = x.copy()
    contaminated[~mask] = np.nan
    np.testing.assert_array_equal(initial, backend.predict_shard(contaminated, mask))
    loss, rows = backend.train_shard(x, mask, y, seed=10)
    assert np.isfinite(loss) and rows == 4
    predicted = backend.predict_shard(x, mask)
    assert predicted.shape == (4, 12)
    assert np.isfinite(predicted).all()
    for event in range(3):
        assert not np.array_equal(
            initial[:, event * 4 : (event + 1) * 4], predicted[:, event * 4 : (event + 1) * 4]
        )
    assert all(p.grad is not None for p in backend.model.parameters())


def test_checkpoint_resume_reproduces_the_next_optimizer_step(tmp_path):
    first = NotebookEWSBackend(5)
    x, mask, y = batch()
    first.train_shard(x, mask, y, seed=5)
    path = tmp_path / "checkpoint.pt"
    first.torch.save(first.state_dict(), path)
    loss1, _ = first.train_shard(x, mask, y, seed=6)
    expected = first.predict_shard(x, mask)
    resumed = NotebookEWSBackend(99)
    resumed.load_state_dict(resumed.torch.load(path, weights_only=True))
    loss2, _ = resumed.train_shard(x, mask, y, seed=6)
    assert loss1 == loss2
    np.testing.assert_array_equal(expected, resumed.predict_shard(x, mask))


def test_snapshot_control_cannot_use_history_while_full_model_can():
    x, mask, _ = batch()
    changed = x.copy()
    changed[:, :-1] *= -10
    snapshot = NotebookEWSBackend(4, family="snapshot")
    np.testing.assert_array_equal(
        snapshot.predict_shard(x, mask), snapshot.predict_shard(changed, mask)
    )
    full = NotebookEWSBackend(4)
    assert not np.allclose(full.predict_shard(x, mask)[1:], full.predict_shard(changed, mask)[1:])


def test_future_observations_cannot_change_any_earlier_model_prediction():
    participants = [
        {
            "participant_id": i,
            "team_id": 100 if i <= 5 else 200,
            "total_gold": 500,
            "xp": 0,
            "level": 1,
            "lane_minions": 0,
            "jungle_minions": 0,
            "position": None,
        }
        for i in range(1, 11)
    ]
    times = (0, 60000, 120000)
    payload = {
        "schema_version": "league-ews-processed-match-v1",
        "timeline": {
            "match_id": "EUW1_1",
            "platform_id": "EUW1",
            "game_version": "16.16.1",
            "game_creation_ms": 1,
            "observations": [
                {"timestamp_ms": t, "participants": deepcopy(participants), "events": []}
                for t in times
            ],
        },
        "labels": [{"timestamp_ms": t, **dict.fromkeys(LABELS, 0)} for t in times],
    }
    original = build_causal_sequences(payload, "EUW1_1")
    payload["timeline"]["observations"][2]["participants"][0]["total_gold"] = 50000
    altered = build_causal_sequences(payload, "EUW1_1")
    backend = NotebookEWSBackend(1)
    before = backend.predict_shard(original.inputs, original.history_mask)
    after = backend.predict_shard(altered.inputs, altered.history_mask)
    np.testing.assert_array_equal(before[:2], after[:2])


@pytest.mark.parametrize("horizon", [30, 60])
def test_warning_exact_boundaries_late_and_one_to_one_credit(horizon):
    matches = [
        MatchRisk((0,), (lead,), (0.9,))
        for lead in (
            0,
            horizon * 1000 // 3 - 1,
            horizon * 1000 // 3,
            horizon * 1000,
            horizon * 1000 + 1,
        )
    ]
    result, counts = replay(matches, 0.5, horizon)
    assert counts[:, 1].tolist() == [0, 1, 1, 1, 0]
    assert counts[:, 2].tolist() == [0, 0, 1, 1, 0]
    assert result["non_timely_alerts_per_match"] == 3 / 5
    match = MatchRisk((0, 60000), (20000, 25000), (0.9, 0.9))
    _, counts = replay([match], 0.5, horizon)
    assert counts[0, 1] == 1  # first alert cannot claim both events


def test_cooldown_uses_actual_time_and_no_alert_policy_is_explicit():
    match = MatchRisk((0, 30000, 60000), (20000, 80000), (0.9, 0.9, 0.9))
    result, _ = replay([match], 0.5, 30)
    assert result["alerts"] == 2 and result["timely_matched_events"] == 2
    assert replay([match], None, 30)[0]["alerts"] == 0


def test_tuning_budget_is_enforced_in_each_route():
    matches = [MatchRisk((0, 60000), (), (1.0, 1.0)), MatchRisk((0,), (), (0.0,))]
    # Aggregate burden at threshold 1 would be one, but Europe's would be two.
    assert select(matches, ["europe", "americas"], 30) is None


def test_runner_pauses_before_calibration_and_passes_only_audited_train_entries(
    tmp_path, monkeypatch
):
    from league_ews import notebook_experiment as experiment

    x, mask, y = batch()
    backend_calls = []

    class Backend:
        def __init__(self, seed, device, *, family):
            import torch

            self.torch, self.version = torch, str(torch.__version__)
            self.model = torch.nn.Linear(1, 1)

        def train_shard(self, inputs, mask, target, *, seed):
            backend_calls.append(seed)
            return 0.5, len(inputs)

        def state_dict(self):
            return {}

        def load_state_dict(self, state):
            pass

    stage = tmp_path / "data/private/b4-sequences"
    (stage / "shards").mkdir(parents=True)
    shard = stage / "shards/train.00000.npz"
    shard.write_bytes(b"fixture")
    entry = {"partition": "train", "file": shard.name, "sha256": experiment.sha(shard)}
    manifest = {"shards": [entry] * 48}
    output = tmp_path / "output"
    output.mkdir()
    (output / "freeze.json").write_text("{}")
    monkeypatch.setattr(experiment, "NotebookEWSBackend", Backend)
    monkeypatch.setattr(experiment, "freeze", lambda *args: ({}, {}, manifest, {}))
    monkeypatch.setattr(
        experiment,
        "_shard",
        lambda root, item, norm: (
            (x, mask, y) if item["partition"] == "train" else pytest.fail("opened calibration")
        ),
    )
    monkeypatch.setattr(
        experiment, "calibration_metadata", lambda *args: pytest.fail("early calibration access")
    )
    result = experiment.run(tmp_path, output, "cpu", 1)
    assert result["status"] == "training-paused-resume-same-command"
    assert len(backend_calls) == 1
    experiment.run(tmp_path, output, "cpu", 1)
    assert len(backend_calls) == 2
    assert backend_calls[1] == backend_calls[0] + 1


def test_calibration_reader_never_opens_train_or_test_payloads(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from league_ews import notebook_experiment as experiment

    calls = []

    def read(root, mid, checksum):
        assert mid == "EUW1_2"
        calls.append(mid)
        return {
            "timeline": {"observations": [{"timestamp_ms": 0}, {"timestamp_ms": 60000}]},
            "labels": [{"timestamp_ms": t, **dict.fromkeys(LABELS, 0)} for t in (0, 60000)],
            "event_index": {f"{event}_ms": [] for event in experiment.EVENTS},
        }

    monkeypatch.setattr(experiment, "_read_match", read)
    split = {
        "partitions": {
            "train": [{"match_id": "EUW1_1"}],
            "calibration": [{"match_id": "EUW1_2"}],
            "test": [{"match_id": "EUW1_3"}],
        }
    }
    result = experiment.calibration_metadata(
        tmp_path, split, {"EUW1_2": SimpleNamespace(sha256="x", observations=2)}
    )
    assert calls == ["EUW1_2"] and result[2].shape == (2, 12)


def test_scoring_preserves_events_horizons_and_exact_match_alignment(tmp_path, monkeypatch):
    import torch

    from league_ews import notebook_experiment as experiment

    class Backend:
        def __init__(self, *args, **kwargs):
            self.torch = torch

        def load_state_dict(self, state):
            pass

        def predict_shard(self, x, mask):
            scores = np.full((8, 12), 0.1, dtype=np.float32)
            scores[::2, :] = 0.9
            return scores

    stage = tmp_path / "data/private/b4-sequences/shards"
    stage.mkdir(parents=True)
    path = stage / "calibration.00000.npz"
    path.write_bytes(b"fixture")
    manifest = {
        "shards": [{}] * 48
        + [{"file": path.name, "partition": "calibration", "sha256": experiment.sha(path)}]
    }
    offsets = np.arange(0, 9, 2)
    truth = np.zeros((8, 12), dtype=np.int8)
    truth[::2, :] = 1
    metadata = (
        [(0, 60000)] * 4,
        {event: [(20000,)] * 4 for event in experiment.EVENTS},
        truth,
        offsets,
    )
    split = {
        "partitions": {
            "calibration": [
                {"regional_route": route} for route in ("europe", "americas", "europe", "americas")
            ]
        }
    }
    folder = tmp_path / "output/leagueews/seed-1"
    folder.mkdir(parents=True)
    torch.save(
        {
            "completed_units": 48 * experiment.EPOCHS,
            "freeze_sha256": "binding",
            "backend": {},
            "parameters": 10,
        },
        folder / "checkpoint.pt",
    )
    monkeypatch.setattr(experiment, "NotebookEWSBackend", Backend)
    monkeypatch.setattr(
        experiment,
        "_load_calibration_shard",
        lambda *args: (None, None, truth.copy(), offsets.copy()),
    )
    monkeypatch.setattr(experiment, "_chronological_halves", lambda *args: ([0, 1], [2, 3]))
    result = experiment.score_fit(
        tmp_path,
        tmp_path / "output",
        manifest,
        {},
        "binding",
        "leagueews",
        1,
        "cpu",
        split,
        metadata,
    )
    assert set(result["row_metrics_later_calibration"]) == set(LABELS)
    assert set(result["warnings"]) == {
        f"{event}_{h}" for event in experiment.EVENTS for h in (30, 60)
    }
    for value in result["warnings"].values():
        assert value["regional_budget_met"]
        assert value["later"]["timely_matched_events"] == 2
        assert value["later"]["matches"] == 2
    broken = (metadata[0], metadata[1], truth.copy(), offsets.copy())
    broken[2][0, 0] = 0
    with pytest.raises(ValueError, match="do not align"):
        experiment.score_fit(
            tmp_path,
            tmp_path / "output",
            manifest,
            {},
            "binding",
            "leagueews",
            1,
            "cpu",
            split,
            broken,
        )
