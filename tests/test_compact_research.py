"""Input-isolation and resume checks; small fixtures are not research evidence."""

import io
import zipfile
from copy import deepcopy

import numpy as np
import pytest

from league_ews.b4_normalizer import apply_b4_normalizer
from league_ews.b4_sequence import build_causal_sequences
from league_ews.notebook_ews import NotebookEWSBackend
from league_ews.tabular_baseline import FEATURES
from scripts import run_compact_notebook as runner
from scripts.export_league_three_events import compact_match, join_matches
from scripts.league_compact_data import tabular_features, validate_arrays
from scripts.run_three_event_timing import timely_targets
from tests.test_three_event_export import payload


def sample():
    first = compact_match(payload(), "EUW1_1")
    second = deepcopy(first)
    second["values"][:, 1] += 10000
    return join_matches([first, second])


def norm():
    return {
        "schema_version": "league-ews-b4-normalizer-v1",
        "features": list(FEATURES),
        "mean": [0.0] * len(FEATURES),
        "scale": [1.0] * len(FEATURES),
    }


def test_validated_compact_arrays_have_no_label_event_or_chronology_mismatch():
    data = sample()
    validate_arrays(data, 18, 2)
    wrong = deepcopy(data)
    wrong["targets"][0, 0] = 1
    with pytest.raises(ValueError, match="Labels differ"):
        validate_arrays(wrong, 18, 2)
    wrong = deepcopy(data)
    wrong["times_ms"][1] = 0
    with pytest.raises(ValueError, match="chronology"):
        validate_arrays(wrong, 18, 2)


def test_history_features_are_causal_and_do_not_cross_match_boundaries():
    data = sample()
    history = tabular_features(data, "history")
    assert history.shape == (18, 219)
    # At the start of match two, every lag is its own current frame, never match one's tail.
    for start in (54, 109, 164):
        np.testing.assert_array_equal(history[9, :54], history[9, start : start + 54])
        assert history[9, start + 54] == 0
    changed = deepcopy(data)
    changed["values"][8, 1] += 100
    revised = tabular_features(changed, "history")
    np.testing.assert_array_equal(history[:8], revised[:8])
    np.testing.assert_array_equal(history[9:], revised[9:])
    changed["targets"][:] = 1 - changed["targets"]
    changed["dragon_ms"][:] += 1000
    np.testing.assert_array_equal(revised, tabular_features(changed, "history"))


def test_compact_sequences_equal_original_b4_features_and_predictions():
    source = payload()
    original = build_causal_sequences(source, "EUW1_1")
    data = join_matches([compact_match(source, "EUW1_1")])
    normalized = norm()
    normalized["mean"][1] = 350
    normalized["scale"][1] = 120
    x, mask, y = runner.sequences(data, normalized)
    reference = apply_b4_normalizer(original.inputs, original.history_mask, normalized)
    np.testing.assert_array_equal(x, reference)
    np.testing.assert_array_equal(mask, original.history_mask)
    np.testing.assert_array_equal(y, original.targets)
    backend = NotebookEWSBackend(8)
    np.testing.assert_array_equal(
        backend.predict_shard(x, mask), backend.predict_shard(reference, original.history_mask)
    )


def archive(tmp_path, data):
    content = io.BytesIO()
    np.savez_compressed(content, **data)
    content = content.getvalue()
    entry = {
        "partition": "train",
        "file": "shards/train.00000.npz",
        "sha256": runner.digest(content),
    }
    path = tmp_path / "fixture.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(entry["file"], content)
        z.writestr("calibration-must-not-be-read", b"not numeric")
    return path, entry


def test_training_normalizer_ignores_calibration_and_matches_direct_moments(tmp_path):
    data = sample()
    path, entry = archive(tmp_path, data)
    manifest = {
        "shards": [entry, {"partition": "calibration", "file": "calibration-must-not-be-read"}]
    }
    normalized = runner.fit_normalizer(path, manifest)
    expected = data["values"][:, 1].astype(np.float64)
    assert normalized["training_observations"] == 18
    assert normalized["mean"][1] == expected.mean()
    assert normalized["scale"][1] == expected.std()
    assert normalized["fit_partitions"] == ["train"]


def test_compact_checkpoint_resume_reproduces_training_and_keeps_targets_separate(
    tmp_path, monkeypatch
):
    data = sample()
    path, entry = archive(tmp_path, data)
    manifest = {"shards": [entry] * 48}
    monkeypatch.setattr(runner, "EPOCHS", 1)
    split = tmp_path / "resumed"
    direct = tmp_path / "direct"
    # Same real training function on tiny implementation fixtures.
    runner.train_fit(path, manifest, norm(), split, "fixture", "snapshot", 9, "cpu", 1)
    runner.train_fit(path, manifest, norm(), split, "fixture", "snapshot", 9, "cpu", 1)
    runner.train_fit(path, manifest, norm(), direct, "fixture", "snapshot", 9, "cpu", 2)
    backend = NotebookEWSBackend(9, family="snapshot")
    a = backend.torch.load(split / "snapshot/seed-9/checkpoint.pt", weights_only=True)
    b = backend.torch.load(direct / "snapshot/seed-9/checkpoint.pt", weights_only=True)
    assert a["completed_units"] == b["completed_units"] == 2
    for key in a["backend"]["model"]:
        assert backend.torch.equal(a["backend"]["model"][key], b["backend"]["model"][key])
    assert a["last_loss"] == b["last_loss"]


def test_cuda_request_does_not_silently_fall_back_to_cpu():
    import torch

    if not torch.cuda.is_available():
        with pytest.raises(RuntimeError, match="unavailable"):
            NotebookEWSBackend(1, "cuda")


def test_shard_checksum_is_checked_before_loading_arrays(tmp_path):
    path, entry = archive(tmp_path, sample())
    entry["sha256"] = "0" * 64
    with zipfile.ZipFile(path) as z, pytest.raises(ValueError, match="changed"):
        runner.read_shard(z, entry)


def test_timely_target_uses_exact_closed_boundaries_and_next_strict_event():
    data = {
        "times_ms": np.array([0, 10000, 20000, 25000, 30000, 40000], dtype=np.int64),
        "match_offsets": np.array([0, 6]),
        "dragon_offsets": np.array([0, 2]),
        "dragon_ms": np.array([30000, 31000]),
    }
    assert timely_targets(data, "dragon").tolist() == [1, 1, 1, 0, 0, 0]


def test_portable_runner_pauses_before_fitted_model_calibration(tmp_path, monkeypatch):
    from pathlib import Path

    data = sample()
    archive_path, entry = archive(tmp_path, data)
    with zipfile.ZipFile(archive_path, "a") as z:
        z.writestr("manifest.json", __import__("json").dumps({"shards": [entry] * 48}))
    monkeypatch.setattr(runner, "validate_archive", lambda *args: {"status": "fixture"})
    monkeypatch.setattr(
        runner,
        "load_partition",
        lambda *args: pytest.fail("Scored calibration before training grid completed"),
    )
    output = tmp_path / "portable"
    result = runner.run(archive_path, output, Path.cwd(), "cpu", 1)
    assert result["status"] == "paused-resume-same-command"
    assert result["new_training_shards"] == 1
    assert result["calibration_scored"] is False
