"""Verify the intervention and exact resume, using implementation fixtures only."""

import json
import zipfile
from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest

from league_ews.notebook_ews import NotebookEWSBackend
from scripts import run_history_ablation as runner
from scripts.run_compact_notebook import sequences
from tests.test_compact_research import archive, norm, sample


def test_ablation_removes_past_states_preserves_age_padding_and_current():
    x, mask, _ = sequences(sample(), norm())
    original = x.copy()
    got = runner.current_only(x, mask)
    np.testing.assert_array_equal(x, original)
    np.testing.assert_array_equal(got[:, -1], x[:, -1])
    np.testing.assert_array_equal(got[..., -1], x[..., -1])
    np.testing.assert_array_equal(got[~mask], x[~mask])
    changed = x.copy()
    changed[:, :-1, :54] += 1000 * mask[:, :-1, None]
    np.testing.assert_array_equal(got, runner.current_only(changed, mask))
    assert np.any(got[mask] != x[mask])


def test_ablation_does_not_import_future_rows_events_or_targets():
    data = sample()
    x, mask, targets = runner.ablated_sequences(data, norm())
    changed = deepcopy(data)
    changed["values"][8, 1] += 100
    changed["targets"][:] = 1 - changed["targets"]
    changed["dragon_ms"][:] += 1000
    revised, revised_mask, revised_targets = runner.ablated_sequences(changed, norm())
    np.testing.assert_array_equal(x[:8], revised[:8])
    np.testing.assert_array_equal(x[9:], revised[9:])
    np.testing.assert_array_equal(mask, revised_mask)
    np.testing.assert_array_equal(revised_targets, 1 - targets)


def test_ablation_rejects_missing_current_frame():
    x, mask, _ = sequences(sample(), norm())
    mask[0, -1] = False
    with pytest.raises(ValueError, match="Current frame"):
        runner.current_only(x, mask)


def test_ablation_checkpoint_resume_matches_uninterrupted_optimizer_and_model(tmp_path):
    path, entry = archive(tmp_path, sample())
    manifest = {"shards": [entry] * 48}
    resumed, direct = tmp_path / "resumed", tmp_path / "direct"
    for _ in range(2):
        runner.train_fit(path, manifest, norm(), resumed, "fixture", "tcn", 9, "cpu", 1)
    runner.train_fit(path, manifest, norm(), direct, "fixture", "tcn", 9, "cpu", 2)
    backend = NotebookEWSBackend(9, family="tcn")
    a = backend.torch.load(resumed / "tcn/seed-9/checkpoint.pt", weights_only=True)
    b = backend.torch.load(direct / "tcn/seed-9/checkpoint.pt", weights_only=True)

    def same(left, right):
        if backend.torch.is_tensor(left):
            assert backend.torch.equal(left, right)
        elif isinstance(left, dict):
            assert left.keys() == right.keys()
            for key in left:
                same(left[key], right[key])
        elif isinstance(left, list):
            assert len(left) == len(right)
            for p, q in zip(left, right, strict=True):
                same(p, q)
        else:
            assert left == right

    same(a["backend"], b["backend"])
    assert a["completed_units"] == b["completed_units"] == 2
    assert a["last_loss"] == b["last_loss"]


def test_followup_pauses_without_fitted_calibration_access(tmp_path, monkeypatch):
    import torch

    path, entry = archive(tmp_path, sample())
    manifest = {"shards": [entry] * 48}
    with zipfile.ZipFile(path, "a") as z:
        z.writestr("manifest.json", json.dumps(manifest))
    control = tmp_path / "control"
    control.mkdir()
    runner.write_json(control / "summary.json", {"status": "fixture"})
    runner.write_json(
        control / "freeze.json",
        {
            "source_sha256": {},
            "runtime": {
                "device": "cpu",
                "torch": str(torch.__version__),
                "cuda_build": torch.version.cuda,
                "gpu_name": None,
            },
        },
    )
    runner.write_json(control / "normalizer.json", runner.fit_normalizer(path, manifest))
    for family in runner.PLAN["families"]:
        for seed in runner.SEEDS:
            p = control / family / f"seed-{seed}"
            p.mkdir(parents=True)
            (p / "checkpoint.pt").write_bytes(b"fixture")
            (p / "calibration-scores.npz").write_bytes(b"fixture")
            runner.write_json(p / "progress.json", {"completed_units": 576})
            runner.write_json(
                p / "report.json",
                {
                    "checkpoint_sha256": runner.sha(p / "checkpoint.pt"),
                    "scores_sha256": runner.sha(p / "calibration-scores.npz"),
                },
            )
    plan = tmp_path / "plan.json"
    runner.write_json(
        plan,
        {
            "family": "tcn",
            "original_plan": runner.PLAN,
            "seeds": list(runner.SEEDS),
            "control_summary_sha256": runner.sha(control / "summary.json"),
            "control_freeze_sha256": runner.sha(control / "freeze.json"),
        },
    )
    monkeypatch.setattr(runner, "validate_archive", lambda *a: {"status": "fixture"})
    monkeypatch.setattr(runner, "load_partition", lambda *a: pytest.fail("Premature calibration"))
    args = SimpleNamespace(
        plan=plan,
        control=control,
        archive=path,
        output=tmp_path / "output",
        device="cpu",
        max_new_shards=1,
        preflight=False,
    )
    result = runner.run(args)
    assert result == {"status": "paused-resume-same-command", "new_shards": 1}


def test_scoring_uses_same_ablation_and_all_event_horizon_columns(tmp_path, monkeypatch):
    import torch

    data = sample()
    path, entry = archive(tmp_path, data)
    manifest = {"shards": [{}] * 48 + [{**entry, "partition": "calibration"}]}
    expected, expected_mask, _ = runner.ablated_sequences(data, norm())
    scores = np.tile(np.arange(1, 13, dtype=np.float32) / 20, (len(expected), 1))

    class Backend:
        def __init__(self, *args, **kwargs):
            self.torch = torch

        def load_state_dict(self, state):
            pass

        def predict_shard(self, x, mask):
            np.testing.assert_array_equal(x, expected)
            np.testing.assert_array_equal(mask, expected_mask)
            return scores

    calls = []

    def policy(cal, rows, probabilities, event, horizon):
        column = runner.EVENTS.index(event) * 4 + (2 if horizon == 30 else 3)
        np.testing.assert_array_equal(probabilities, scores[:, column])
        calls.append((event, horizon))
        return {}, np.zeros((1, 6), dtype=int)

    p = tmp_path / "output/tcn/seed-9"
    p.mkdir(parents=True)
    torch.save(
        {
            "freeze_sha256": "fixture",
            "completed_units": 576,
            "backend": {},
            "parameters": 10,
            "training_seconds": 1.0,
        },
        p / "checkpoint.pt",
    )
    monkeypatch.setattr(runner, "NotebookEWSBackend", Backend)
    monkeypatch.setattr(runner, "_chronological_halves", lambda *a: ([0], [1]))
    monkeypatch.setattr(runner, "policy_report", policy)
    report = runner.score_fit(
        path, manifest, norm(), tmp_path / "output", "fixture", "tcn", 9, "cpu", data, []
    )
    assert len(calls) == 6
    assert len(report["row_metrics"]) == 12
    with np.load(p / "calibration-scores.npz") as z:
        np.testing.assert_array_equal(z["targets"], data["targets"])
        np.testing.assert_array_equal(z["match_offsets"], data["match_offsets"])
        np.testing.assert_array_equal(z["probabilities"], scores)
