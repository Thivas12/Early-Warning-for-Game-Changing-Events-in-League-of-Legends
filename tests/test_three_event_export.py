"""Export-contract checks; fixtures are not empirical League results."""

import io
import json
import zipfile
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from league_ews.b4_sequence import build_causal_sequences
from league_ews.baseline_floor import LABELS
from league_ews.constants import EVENTS
from scripts import export_league_three_events as export


def payload(mid="EUW1_1"):
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
    times = [0, 60000, 121000, 180000, 240000, 300000, 361000, 420000, 480000]
    events = {"baron_ms": [450000], "dragon_ms": [130000, 460000], "teamfight_ms": [70000, 80000]}
    labels = []
    for t in times:
        # Keep the registered label spelling authoritative.
        labels.append(
            {
                "timestamp_ms": t,
                **{
                    label: int(any(t < v <= t + h * 1000 for v in events[f"{e}_ms"]))
                    for label, (e, h) in zip(
                        LABELS, ((e, h) for e in EVENTS for h in (10, 20, 30, 60)), strict=True
                    )
                },
            }
        )
    return {
        "schema_version": "league-ews-processed-match-v1",
        "timeline": {
            "match_id": mid,
            "platform_id": mid.split("_")[0],
            "game_version": "16.16.1",
            "game_creation_ms": 1,
            "observations": [
                {"timestamp_ms": t, "participants": deepcopy(participants), "events": []}
                for t in times
            ],
        },
        "labels": labels,
        "event_index": events,
        "unexported_player_identifier": "fixture-secret",
    }


def test_all_three_targets_and_irregular_histories_roundtrip_exactly():
    source = payload()
    arrays = export.compact_match(source, "EUW1_1")
    windows, mask = export.rebuild_histories(arrays)
    reference = build_causal_sequences(source, "EUW1_1")
    np.testing.assert_array_equal(windows, reference.inputs)
    np.testing.assert_array_equal(mask, reference.history_mask)
    np.testing.assert_array_equal(arrays["targets"], reference.targets)
    assert arrays["targets"].shape == (9, 12)
    assert all(arrays["targets"][:, e * 4 : (e + 1) * 4].any() for e in range(3))
    assert not any(value.dtype.hasobject for value in arrays.values())


def test_future_values_and_other_matches_cannot_change_earlier_histories():
    original = export.compact_match(payload(), "EUW1_1")
    changed = deepcopy(original)
    changed["values"][-1] += 100
    changed["missing"][-1] = False
    before, _ = export.rebuild_histories(original)
    after, _ = export.rebuild_histories(changed)
    np.testing.assert_array_equal(before[:-1], after[:-1])
    joined = export.join_matches([original, changed])
    assert joined["match_offsets"].tolist() == [0, 9, 18]
    for event in EVENTS:
        n = len(original[f"{event}_ms"])
        assert joined[f"{event}_offsets"].tolist() == [0, n, 2 * n]


@pytest.mark.parametrize("change", ["label", "negative_event", "duplicate_event", "after_end"])
def test_invalid_event_truth_is_rejected(change):
    source = payload()
    if change == "label":
        source["labels"][0][LABELS[0]] = 1
    elif change == "negative_event":
        source["event_index"]["baron_ms"] = [-1]
    elif change == "duplicate_event":
        source["event_index"]["baron_ms"] = [1000, 1000]
    else:
        source["event_index"]["baron_ms"] = [999999]
    with pytest.raises(ValueError):
        export.compact_match(source, "EUW1_1")


def prepared(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    for name in ("export_league_three_events.py", "export_league_development.py"):
        (scripts / name).write_text("# export fixture\n")
    monkeypatch.setattr(export, "__file__", str(scripts / "export_league_three_events.py"))
    (root / "src/league_ews").mkdir(parents=True)
    folder = root / "data/processed/registered-final/matches"
    folder.mkdir(parents=True)
    partitions, records = {}, {}
    for partition, mid in (("train", "EUW1_1"), ("calibration", "NA1_2")):
        content = export.encoded(payload(mid))
        (folder / f"{mid}.json").write_bytes(content)
        records[mid] = SimpleNamespace(sha256=export.digest(content), observations=9)
        partitions[partition] = [{"match_id": mid}]
    # It exists but must never be read; its content is deliberately invalid.
    (folder / "NA1_3.json").write_text("sealed-test-payload")
    records["NA1_3"] = SimpleNamespace(sha256="forbidden", observations=9)
    development = {"partitions": partitions, "test_membership_exported": False}
    monkeypatch.setattr(
        export, "source_binding", lambda repo, data_repo: (development, records, {}, {})
    )
    original_read = Path.read_bytes

    def guarded_read(path):
        assert path.name != "NA1_3.json", "Opened sealed test payload"
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read)
    return root, folder


def test_export_omits_test_and_identifiers_and_publishes_verifiable_numeric_shards(
    tmp_path, monkeypatch
):
    root, _ = prepared(tmp_path, monkeypatch)
    result = export.export(root)
    target = Path(result["path"])
    assert export.file_digest(target) == result["sha256"]
    with zipfile.ZipFile(target) as archive:
        assert set(archive.namelist()) == {
            "manifest.json",
            "development-split.json",
            "shards/train.00000.npz",
            "shards/calibration.00000.npz",
        }
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["test_payloads_opened"] == 0
        assert manifest["partitions"] == {
            "train": {"matches": 1, "rows": 9},
            "calibration": {"matches": 1, "rows": 9},
        }
        for entry in manifest["shards"]:
            content = archive.read(entry["file"])
            assert export.digest(content) == entry["sha256"]
            with np.load(io.BytesIO(content), allow_pickle=False) as arrays:
                assert arrays["targets"].shape == (9, 12)
                assert all(not arrays[key].dtype.hasobject for key in arrays.files)
        for member in ("manifest.json", "development-split.json"):
            assert b"NA1_3" not in archive.read(member)
            assert b"fixture-secret" not in archive.read(member)
    with pytest.raises(ValueError, match="already exists"):
        export.export(root)


@pytest.mark.parametrize("damage", ["checksum", "symlink", "bad_labels"])
def test_failed_export_leaves_no_archive_or_partial(tmp_path, monkeypatch, damage):
    root, folder = prepared(tmp_path, monkeypatch)
    source = folder / "EUW1_1.json"
    if damage == "checksum":
        source.write_text("changed")
    elif damage == "symlink":
        source.unlink()
        source.symlink_to(folder / "NA1_3.json")
    else:
        original = export.compact_match

        def broken(payload, match_id):
            payload["labels"][0][LABELS[0]] = 1
            return original(payload, match_id)

        monkeypatch.setattr(export, "compact_match", broken)
    with pytest.raises(ValueError):
        export.export(root)
    output_dir = root / "data/private/league-three-event-export-v1"
    assert not list(output_dir.iterdir())


def test_export_code_worktree_reads_existing_data_checkout_without_copying(tmp_path, monkeypatch):
    root, _ = prepared(tmp_path, monkeypatch)
    existing = tmp_path / "existing-checkout"
    existing.mkdir()
    (root / "data").rename(existing / "data")
    result = export.export(root, data_repo=existing)
    assert Path(result["path"]).is_relative_to(existing)
    assert not (root / "data").exists()
    assert (existing / "data/processed/registered-final/matches/EUW1_1.json").exists()
