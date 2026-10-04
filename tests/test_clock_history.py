"""Matched input interventions, checkpoint preservation and all-fit scoring gates."""

import json
import zipfile
from types import SimpleNamespace

import numpy as np
import pytest

from league_ews.notebook_ews import NotebookEWSBackend
from scripts import run_clock_history as runner
from scripts.clock_history_control import intervene
from scripts.run_compact_notebook import sequences
from scripts.timely_input_controls import CLOCK_COLUMNS, CLOCK_FEATURES
from scripts.timely_neural_targets import fitted_targets
from tests.test_compact_research import archive, norm, sample


def test_only_past_non_timing_state_is_removed():
    data = sample()
    x, mask, _ = sequences(data, norm())
    before = x.copy()
    c = intervene(x, mask, "clock_history")
    retained = list(CLOCK_COLUMNS) + [i + 27 for i in CLOCK_COLUMNS] + [54]
    removed = [i for i in range(54) if i not in retained]
    np.testing.assert_array_equal(c[..., retained], x[..., retained])
    np.testing.assert_array_equal(c[:, -1], x[:, -1])
    for i in range(len(x)):
        expected = np.repeat(x[i, -1:, removed].T, int(mask[i].sum()), axis=0)
        np.testing.assert_array_equal(c[i, mask[i]][:, removed], expected)
    assert np.all(c[~mask] == 0)
    changed = x.copy()
    changed[:, :-1, :][:, :, removed] = 987
    changed[~mask] = x[~mask]
    np.testing.assert_array_equal(intervene(changed, mask, "clock_history"), c)
    np.testing.assert_array_equal(x, before)
    with pytest.raises(ValueError, match="Unknown"):
        intervene(x, mask, "other")


def test_exact_resume_and_missing_checkpoint_rejected(tmp_path):
    path, entry = archive(tmp_path, sample())
    manifest = {"shards": [entry] * 48}
    resumed, direct = tmp_path / "resumed", tmp_path / "direct"
    for _ in range(2):
        runner.train_fit(path, manifest, norm(), resumed, "fixture", "clock_history", 9, "cpu", 1)
    runner.train_fit(path, manifest, norm(), direct, "fixture", "clock_history", 9, "cpu", 2)
    backend = NotebookEWSBackend(9, family="leagueews")
    a = backend.torch.load(resumed / "clock_history/seed-9/checkpoint.pt", weights_only=True)
    b = backend.torch.load(direct / "clock_history/seed-9/checkpoint.pt", weights_only=True)

    def same(x, y):
        if backend.torch.is_tensor(x):
            assert backend.torch.equal(x, y)
        elif isinstance(x, dict):
            assert x.keys() == y.keys()
            for k in x:
                same(x[k], y[k])
        elif isinstance(x, list):
            for p, q in zip(x, y, strict=True):
                same(p, q)
        else:
            assert x == y

    same(a["backend"], b["backend"])
    assert a["last_loss"] == b["last_loss"]
    assert a["completed_units"] == b["completed_units"] == 2
    with pytest.raises(ValueError, match="checkpoint mismatch"):
        runner.train_fit(path, manifest, norm(), resumed, "different", "clock_history", 9, "cpu", 1)
    (resumed / "clock_history/seed-9/checkpoint.pt").unlink()
    with pytest.raises(ValueError, match="Missing checkpoint"):
        runner.train_fit(path, manifest, norm(), resumed, "fixture", "clock_history", 9, "cpu", 1)


def fixture_run(tmp_path, monkeypatch):
    import torch

    path, entry = archive(tmp_path, sample())
    manifest = {"shards": [entry] * 48}
    with zipfile.ZipFile(path, "a") as z:
        z.writestr("manifest.json", json.dumps(manifest))
    control = tmp_path / "control"
    control.mkdir()
    summary = {
        "status": "complete-exploratory-architecture-screen",
        "test_payloads_opened": 0,
        "models": {},
    }
    frozen = {
        "source_sha256": {},
        "runtime": {
            "device": "cpu",
            "torch": str(torch.__version__),
            "cuda_build": torch.version.cuda,
            "gpu_name": None,
        },
    }
    runner.write_json(control / "freeze.json", frozen)
    summary["freeze_sha256"] = runner.sha(control / "freeze.json")
    runner.write_json(control / "normalizer.json", runner.fit_normalizer(path, manifest))
    for family in runner.PLAN["families"]:
        for seed in runner.SEEDS:
            p = control / family / f"seed-{seed}"
            p.mkdir(parents=True)
            (p / "checkpoint.pt").write_bytes(b"fixture")
            (p / "calibration-scores.npz").write_bytes(b"fixture")
            runner.write_json(p / "progress.json", {"completed_units": 576})
            r = {
                "checkpoint_sha256": runner.sha(p / "checkpoint.pt"),
                "scores_sha256": runner.sha(p / "calibration-scores.npz"),
            }
            runner.write_json(p / "report.json", r)
            summary["models"][f"{family}/{seed}"] = r
    runner.write_json(control / "summary.json", summary)
    timely = tmp_path / "timely"
    runner.write_json(timely / "freeze.json", {"source_sha256": {}})
    runner.write_json(
        timely / "summary.json",
        {
            "status": "complete-exploratory-timely-neural-predictions",
            "test_payloads_opened": 0,
            "models": {},
        },
    )
    input_controls = tmp_path / "input_controls"
    runner.write_json(input_controls / "freeze.json", {"source_sha256": {}})
    input_summary = {
        "status": "complete-exploratory-timely-inputs-predictions",
        "test_payloads_opened": 0,
        "models": {},
    }
    for f in ("current_only", "clock_only"):
        for seed in runner.SEEDS:
            p = input_controls / f / f"seed-{seed}"
            p.mkdir(parents=True)
            (p / "checkpoint.pt").write_bytes(b"fixture")
            (p / "calibration-scores.npz").write_bytes(b"fixture")
            report = {
                "checkpoint_sha256": runner.sha(p / "checkpoint.pt"),
                "scores_sha256": runner.sha(p / "calibration-scores.npz"),
            }
            runner.write_json(p / "report.json", report)
            runner.write_json(p / "progress.json", {"completed_units": 576})
            input_summary["models"][f"{f}/{seed}"] = report
    runner.write_json(input_controls / "summary.json", input_summary)
    plan = tmp_path / "plan.json"
    runner.write_json(
        plan,
        {
            "families": list(runner.FAMILIES),
            "input_control_freeze_sha256": runner.sha(input_controls / "freeze.json"),
            "input_control_summary_sha256": runner.sha(input_controls / "summary.json"),
            "events": list(runner.EVENTS),
            "seeds": list(runner.SEEDS),
            "original_plan": runner.PLAN,
            "clock_features": list(CLOCK_FEATURES),
            "timely_freeze_sha256": runner.sha(timely / "freeze.json"),
            "timely_summary_sha256": runner.sha(timely / "summary.json"),
            "control_summary_sha256": runner.sha(control / "summary.json"),
            "control_freeze_sha256": runner.sha(control / "freeze.json"),
        },
    )
    monkeypatch.setattr(runner, "validate_archive", lambda *_: {"fixture": True})
    return SimpleNamespace(
        archive=path,
        control=control,
        timely=timely,
        input_controls=input_controls,
        control_source=tmp_path,
        output=tmp_path / "output",
        plan=plan,
        device="cpu",
        max_new_shards=0,
        preflight=False,
    )


def test_all_three_fits_must_complete_before_predictions(tmp_path, monkeypatch):
    args = fixture_run(tmp_path, monkeypatch)
    trained = []

    def train(*a):
        trained.append((a[5], a[6]))
        return 576, len(trained) != 3

    monkeypatch.setattr(runner, "train_fit", train)
    monkeypatch.setattr(
        runner, "load_partition", lambda *_: pytest.fail("Premature calibration scoring")
    )
    result = runner.run(args)
    assert result["status"] == "paused-resume-same-command" and len(trained) == 3
    assert not (args.output / "summary.json").exists()
    trained.clear()

    def complete(*a):
        trained.append((a[5], a[6]))
        return 0, True

    monkeypatch.setattr(runner, "train_fit", complete)

    def calibration(*a):
        assert len(trained) == 3
        return {}, []

    monkeypatch.setattr(runner, "load_partition", calibration)
    scored = []

    def score(*a):
        assert len(trained) == 3
        scored.append((a[5], a[6]))
        return {"fixture": True}

    monkeypatch.setattr(runner, "score_fit", score)
    assert runner.run(args)["status"] == "complete-exploratory-clock-history-predictions"
    assert len(scored) == 3


def test_prediction_scoring_saves_both_target_definitions_without_evaluation(tmp_path, monkeypatch):
    import torch

    data = sample()
    path, entry = archive(tmp_path, data)
    manifest = {"shards": [{}] * 48 + [{**entry, "partition": "calibration"}]}
    expected, mask, _ = sequences(data, norm())
    expected = intervene(expected, mask, "clock_history")
    scores = np.full((18, 12), 0.25, dtype=np.float32)

    class Backend:
        def __init__(self, *args, **kwargs):
            self.torch, self.version = torch, str(torch.__version__)

        def load_state_dict(self, state):
            pass

        def predict_shard(self, x, m):
            np.testing.assert_array_equal(x, expected)
            np.testing.assert_array_equal(m, mask)
            return scores

    monkeypatch.setattr(runner, "NotebookEWSBackend", Backend)
    folder = tmp_path / "output/clock_history/seed-9"
    folder.mkdir(parents=True)
    torch.save(
        {
            "freeze_sha256": "fixture",
            "completed_units": 576,
            "family": "clock_history",
            "seed": 9,
            "device": "cpu",
            "torch_version": str(torch.__version__),
            "backend": {},
            "parameters": 1,
            "training_seconds": 1,
        },
        folder / "checkpoint.pt",
    )
    report = runner.score_fit(
        path, manifest, norm(), tmp_path / "output", "fixture", "clock_history", 9, "cpu", data, []
    )
    assert "warnings" not in report and "row_metrics" not in report
    with np.load(folder / "calibration-scores.npz", allow_pickle=False) as saved:
        np.testing.assert_array_equal(saved["fitted_targets"], fitted_targets(data))
        np.testing.assert_array_equal(saved["targets"], data["targets"])
        np.testing.assert_array_equal(saved["probabilities"], scores)


def test_nonfinite_update_preserves_last_valid_checkpoint(tmp_path, monkeypatch):
    path, entry = archive(tmp_path, sample())
    manifest = {"shards": [entry] * 48}
    output = tmp_path / "study"
    runner.train_fit(path, manifest, norm(), output, "fixture", "clock_history", 9, "cpu", 1)
    checkpoint = output / "clock_history/seed-9/checkpoint.pt"
    digest = runner.sha(checkpoint)

    def invalid(self, inputs, *args, **kwargs):
        with self.torch.no_grad():
            next(self.model.parameters()).fill_(float("nan"))
        return 0.0, len(inputs)

    monkeypatch.setattr(runner.NotebookEWSBackend, "train_shard", invalid)
    with pytest.raises(ValueError, match="Nonfinite parameters"):
        runner.train_fit(path, manifest, norm(), output, "fixture", "clock_history", 9, "cpu", 1)
    assert runner.sha(checkpoint) == digest
    assert json.loads((checkpoint.parent / "progress.json").read_text())["completed_units"] == 1
