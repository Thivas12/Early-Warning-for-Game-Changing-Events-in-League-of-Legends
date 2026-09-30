"""Tiny synthetic contract fixtures only; these are not League experiment results."""

import json
import zipfile
from pathlib import Path

import numpy as np
import pytest

from scripts import export_league_development as exporter


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(exporter.encoded(value))


@pytest.fixture
def source(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter, "CELL_MATCHES", 1)
    monkeypatch.setattr(exporter, "SHARD_MATCHES", 2)
    repo = tmp_path / "repo"
    cache = repo / "data/private/coordination-screen-v1"
    partitions = {}
    serial = 1
    for partition, patches in exporter.PATCHES.items():
        entries = []
        for patch in patches:
            for prefix, route in (("EUW1", "europe"), ("NA1", "americas")):
                entries.append(
                    {
                        "match_id": f"{prefix}_{serial}",
                        "regional_route": route,
                        "game_version_patch": patch,
                        "game_creation_ms": serial,
                        "puuid": "MUST-NOT-EXPORT-PLAYER-ID",
                    }
                )
                serial += 1
        partitions[partition] = entries
    split = {
        "schema_version": "league-ews-final-split-v1",
        "partitions": partitions,
        "processed_audit_sha256": "a" * 64,
        "processing_manifest_sha256": "b" * 64,
    }
    split_path = repo / "data/private/final-split.json"
    write_json(split_path, split)
    freeze = {
        "schema_version": "league-ews-coordination-screen-freeze-v1",
        "plan": {
            "schema_version": "league-ews-coordination-screen-plan-v1",
            "target": "dragon-within-60-seconds-in-actual-match",
            "test_access": "prohibited",
            "variants": exporter.VARIANTS,
            "final_fit_patches": list(exporter.PATCHES["train"]),
            "features": [f"feature_{i}" for i in range(179)],
        },
        "split_sha256": exporter.file_digest(split_path),
        "processed_audit_sha256": split["processed_audit_sha256"],
        "processing_manifest_sha256": split["processing_manifest_sha256"],
        "test_matches_unread": 2,
        "feature_storage_bytes": 10 * 179 * 4,
    }
    write_json(cache / "freeze.json", freeze)
    binding = exporter.file_digest(cache / "freeze.json")
    monkeypatch.setattr(exporter, "SOURCE_FREEZE_SHA256", binding)
    write_json(
        cache / "summary.json",
        {
            "schema_version": "league-ews-coordination-screen-summary-v1",
            "status": "complete-exploratory-calibration-screen",
            "freeze_sha256": binding,
            "test_matches_unread": 2,
            "models": {name: {} for name in exporter.VARIANTS},
        },
    )
    (cache / "shards").mkdir()
    for partition in ("train", "calibration"):
        for start in range(0, len(partitions[partition]), 2):
            path = cache / "shards" / f"{partition}.{start:05d}.npz"
            np.savez_compressed(
                path,
                x=np.zeros((2, 179), dtype=np.float32),
                y=np.zeros(2, dtype=np.int8),
                times=np.zeros(2, dtype=np.int64),
                events=np.array([], dtype=np.int64),
                offsets=np.arange(3, dtype=np.int64),
                event_offsets=np.zeros(3, dtype=np.int64),
            )
            write_json(
                path.with_suffix(".json"),
                {
                    "freeze_sha256": binding,
                    "sha256": exporter.file_digest(path),
                    "rows": 2,
                    "matches": 2,
                    "extra": "MUST-NOT-EXPORT-SIDECAR-SECRET",
                },
            )
    return repo, cache


def test_export_preserves_sources_and_never_reads_excluded_payloads(source, monkeypatch):
    repo, cache = source
    forbidden = [
        cache / "shards/test.00000.npz",
        cache / "model.pkl",
        repo / "data/private/riot-key.txt",
        repo / "data/processed/registered-final/EUW1_11.json",
    ]
    for path in forbidden:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"MUST-NOT-READ")
    original = {p: p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    path_open = Path.open

    def guarded_open(self, *args, **kwargs):
        assert self not in forbidden, f"Opened excluded payload: {self}"
        return path_open(self, *args, **kwargs)

    with monkeypatch.context() as guard:
        guard.setattr(Path, "open", guarded_open)
        result = exporter.export(repo)
    output = Path(result["path"])
    assert result["sha256"] == exporter.file_digest(output)
    with zipfile.ZipFile(output) as archive:
        assert len(archive.namelist()) == 13  # five shards, five sidecars, three metadata files
        assert all("test." not in name for name in archive.namelist())
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["partitions"] == {
            "train": {"matches": 8, "rows": 8},
            "calibration": {"matches": 2, "rows": 2},
        }
        for name, checksum in manifest["entries_sha256"].items():
            assert exporter.digest(archive.read(name)) == checksum
        development = json.loads(archive.read("split-development.json"))
        assert set(development["partitions"]) == {"train", "calibration"}
        assert b"EUW1_11" not in archive.read("split-development.json")
        for name in archive.namelist():
            assert b"MUST-NOT" not in archive.read(name)
    assert all(path.read_bytes() == value for path, value in original.items())
    with pytest.raises(ValueError, match="Output already exists"):
        exporter.export(repo)
    assert exporter.file_digest(output) == result["sha256"]


@pytest.mark.parametrize("failure", ["checksum", "missing", "binding", "split", "freeze"])
def test_inconsistent_sources_never_publish_an_archive(source, failure):
    repo, cache = source
    shard = cache / "shards/calibration.00000.npz"
    if failure == "checksum":
        shard.write_bytes(shard.read_bytes() + b"changed")
    elif failure == "missing":
        shard.unlink()
    elif failure == "binding":
        sidecar = shard.with_suffix(".json")
        meta = json.loads(sidecar.read_bytes())
        meta["freeze_sha256"] = "wrong"
        write_json(sidecar, meta)
    elif failure == "split":
        split = repo / "data/private/final-split.json"
        split.write_bytes(split.read_bytes() + b" ")
    else:
        freeze = cache / "freeze.json"
        freeze.write_bytes(freeze.read_bytes() + b" ")
    with pytest.raises(ValueError):
        exporter.export(repo)
    assert not (repo / "data/private/league-development-export-v1").exists()


def test_another_game_cannot_pass_even_with_a_rebound_checksum(source, monkeypatch):
    repo, cache = source
    path = cache / "freeze.json"
    freeze = json.loads(path.read_bytes())
    freeze["plan"]["target"] = "dota-first-damage"
    write_json(path, freeze)
    monkeypatch.setattr(exporter, "SOURCE_FREEZE_SHA256", exporter.file_digest(path))
    with pytest.raises(ValueError, match="expected League experiment"):
        exporter.export(repo)


@pytest.mark.parametrize("case", ["object", "extra", "shape"])
def test_npz_payload_contract_rejects_non_numeric_or_unexpected_content(source, case):
    repo, cache = source
    path = cache / "shards/train.00000.npz"
    with np.load(path, allow_pickle=False) as loaded:
        data = dict(loaded)
    if case == "object":
        data["x"] = np.full((2, 179), "player identifier", dtype=object)
    elif case == "extra":
        data["puuid"] = np.array(["player identifier"])
    else:
        data["x"] = np.zeros((2, 178), dtype=np.float32)
    np.savez_compressed(path, **data)
    meta = json.loads(path.with_suffix(".json").read_bytes())
    meta["sha256"] = exporter.file_digest(path)
    write_json(path.with_suffix(".json"), meta)
    with pytest.raises(ValueError, match="Unexpected"):
        exporter.export(repo)


def test_shard_symlink_to_test_payload_is_rejected_without_reading_it(source, monkeypatch):
    repo, cache = source
    path = cache / "shards/train.00000.npz"
    sealed = cache / "shards/test.00000.npz"
    path.rename(sealed)
    path.symlink_to(sealed)
    path_open = Path.open

    def guard(self, *args, **kwargs):
        assert self not in (path, sealed)
        return path_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guard)
    with pytest.raises(ValueError, match="Symbolic link"):
        exporter.export(repo)


def test_split_rejects_duplicate_membership_and_wrong_game_identifiers(source):
    repo, _ = source
    split = json.loads((repo / "data/private/final-split.json").read_bytes())
    split["partitions"]["calibration"][0]["match_id"] = "EUW1_1"
    with pytest.raises(ValueError, match="Duplicate"):
        exporter.development_split(split)
    split["partitions"]["calibration"][0]["match_id"] = "1234567890"
    with pytest.raises(ValueError, match="Invalid League"):
        exporter.development_split(split)


def test_copy_failure_removes_partial_and_does_not_publish(source, monkeypatch):
    repo, _ = source
    archive_open = zipfile.ZipFile.open

    def fail_write(self, name, mode="r", **kwargs):
        if mode == "w" and str(name).endswith(".npz"):
            raise OSError("simulated disk full")
        return archive_open(self, name, mode=mode, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "open", fail_write)
    with pytest.raises(OSError, match="simulated disk full"):
        exporter.export(repo)
    destination = repo / "data/private/league-development-export-v1"
    assert list(destination.iterdir()) == []
