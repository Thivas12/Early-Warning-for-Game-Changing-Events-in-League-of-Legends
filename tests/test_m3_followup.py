"""Terminal follow-up must not turn unknown future time into a negative."""

import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest

from league_ews.cli import build_parser
from league_ews.m3_followup import censored_hazard_bce, confirmed_followup_masks
from league_ews.m3_followup_audit import _accumulate, _counts, _source_times_and_hazards
from league_ews import m3_followup_audit as audit_module


def test_positive_partial_bin_is_known_but_unobserved_negative_tail_is_censored() -> None:
    times = np.array([0, 25_000], dtype=np.int64)
    hazards = np.zeros((2, 3, 6), np.float32)
    hazards[0, 0, 2] = 1
    exposure, labels_known = confirmed_followup_masks(times, hazards)
    assert exposure.shape == (2, 3, 6)
    assert exposure[0, 0].tolist() == [1, 1, 1, 0, 0, 0]
    assert exposure[0, 1].tolist() == [1, 1, 0, 0, 0, 0]
    assert exposure[1].sum() == 0
    assert labels_known[0, 0].tolist() == [True, True, True, True]
    assert labels_known[0, 1].tolist() == [True, True, False, False]
    assert not labels_known[1].any()


def test_full_bin_boundary_is_known_and_no_future_frame_is_imputed() -> None:
    times = np.array([0, 10_000], dtype=np.int64)
    hazards = np.zeros((2, 3, 6), np.float32)
    exposure, labels_known = confirmed_followup_masks(times, hazards)
    assert exposure[0, :, 0].tolist() == [1, 1, 1]
    assert exposure[0, :, 1:].sum() == 0
    assert labels_known[0, :, 0].all()
    assert not labels_known[0, :, 1:].any()


def test_screened_duration_shortens_exposure_without_erasing_observed_positives() -> None:
    times = np.array([0, 25_000], dtype=np.int64)
    hazards = np.zeros((2, 3, 6), np.float32)
    hazards[0, 0, 2] = 1  # Recorded event at 22 s; detail duration may be rounded to 21 s.
    exposure, known = confirmed_followup_masks(times, hazards, game_duration_ms=21_000)
    assert exposure[0, 0].tolist() == [1, 1, 1, 0, 0, 0]
    assert exposure[0, 1].tolist() == [1, 1, 0, 0, 0, 0]
    assert known[0, 0, 2] and not known[0, 1, 2]
    with pytest.raises(ValueError, match="strictly increasing"):
        confirmed_followup_masks(times, hazards, game_duration_ms=0)


def test_source_event_contract_and_negative_counts() -> None:
    payload = {
        "schema_version": "league-ews-processed-match-v1",
        "timeline": {
            "match_id": "EUW1_1",
            "observations": [{"timestamp_ms": 0}, {"timestamp_ms": 25_000}],
        },
        "event_index": {"baron_ms": [22_000], "dragon_ms": [], "teamfight_ms": []},
    }
    times, hazard = _source_times_and_hazards(payload, "EUW1_1")
    assert hazard[0, 0].tolist() == [0, 0, 1, 0, 0, 0]
    labels = np.maximum.accumulate(hazard, axis=-1)[:, :, [0, 1, 2, 5]].reshape(-1, 12)
    counts = _counts()
    _accumulate(counts, times, hazard, labels, 21_000)
    assert counts["matches"] == 1
    assert counts["rows"] == 2
    assert counts["positive_labels"][2:4] == [1, 1]
    assert counts["negative_labels_without_full_followup"][7] == 2
    assert counts["original_loss_bins"] > counts["confirmed_loss_bins"]
    assert counts["last_frame_after_duration"] == 1
    assert counts["maximum_absolute_gap_ms"] == 4000
    payload["event_index"]["baron_ms"] = [26_000]
    with pytest.raises(ValueError, match="outside confirmed follow-up"):
        _source_times_and_hazards(payload, "EUW1_1")


def test_censored_loss_ignores_unknown_negative_and_checks_exposure() -> None:
    torch = pytest.importorskip("torch")
    logits = torch.tensor([[[0.0] * 6] * 3], requires_grad=True)
    truth = torch.zeros((1, 3, 6))
    exposure = torch.zeros_like(truth)
    exposure[0, :, 0] = 1
    loss = censored_hazard_bce(logits, truth, exposure)
    assert float(loss) == pytest.approx(np.log(2))
    loss.backward()
    assert logits.grad is not None
    assert torch.count_nonzero(logits.grad) == 3
    truth[0, 0, 1] = 1
    with pytest.raises(ValueError, match="exposed binary"):
        censored_hazard_bce(logits, truth, exposure)


def test_cli_requires_bound_inputs() -> None:
    parser = build_parser()
    arguments = parser.parse_args(
        [
            "audit-confirmed-followup",
            "--processed",
            "processed",
            "--split",
            "split.json",
            "--staging-root",
            "stage",
            "--selection-root",
            "selected",
            "--output",
            "audit.json",
        ]
    )
    assert arguments.command == "audit-confirmed-followup"


def test_bound_audit_reads_train_and_calibration_only_and_rejects_tampering(
    tmp_path, monkeypatch
) -> None:
    for name, value in (
        ("TRAIN_MATCHES", 2),
        ("CALIBRATION_MATCHES", 1),
        ("TEST_MATCHES", 1),
        ("CELL_MATCHES", 1),
        ("REGISTERED_CELLS", 4),
    ):
        monkeypatch.setattr(audit_module, name, value)
    processed = tmp_path / "processed"
    matches = processed / "matches"
    matches.mkdir(parents=True)
    stage = tmp_path / "stage"
    (stage / "shards").mkdir(parents=True)
    selection = tmp_path / "selection"
    selection.mkdir()
    chosen = [
        ("EUW1_1", "train", "16.12"),
        ("EUW1_2", "train", "16.13"),
        ("EUW1_3", "calibration", "16.16"),
        ("EUW1_4", "test", "16.17"),
    ]
    records = []
    for match_id, partition, patch in chosen:
        content = json.dumps(
            {
                "schema_version": "league-ews-processed-match-v1",
                "timeline": {"match_id": match_id, "observations": [{"timestamp_ms": 1000}]},
                "event_index": {"baron_ms": [], "dragon_ms": [], "teamfight_ms": []},
            }
        ).encode()
        if partition != "test":
            (matches / f"{match_id}.json").write_bytes(content)
        records.append(
            {
                "match_id": match_id,
                "game_version": f"{patch}.1",
                "observations": 1,
                "baron_events": 0,
                "dragon_events": 0,
                "teamfight_events": 0,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    inventory_bytes = json.dumps(
        {
            "schema_version": "league-ews-processing-manifest-v1",
            "normalizer": "riot-match-v5-normalized-v1",
            "label_policy": "exact-future-events-v1",
            "matches": records,
            "contains_player_identifiers": False,
        }
    ).encode()
    (processed / "processing-manifest.json").write_bytes(inventory_bytes)
    partitions = {name: [] for name in ("train", "calibration", "test")}
    for match_id, partition, patch in chosen:
        partitions[partition].append(
            {"match_id": match_id, "regional_route": "europe", "game_version_patch": patch}
        )
    split_path = tmp_path / "split.json"
    split_path.write_text(
        json.dumps(
            {
                "schema_version": "league-ews-final-split-v1",
                "processing_manifest_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
                "frame_sha256": "a" * 64,
                "summary": {"counts": {"train": 2, "calibration": 1, "test": 1}},
                "partitions": partitions,
            }
        )
    )
    pool_bytes = b"synthetic selected pool"
    (selection / "selected-pool.json").write_bytes(pool_bytes)
    (selection / "selection-manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "riot-final-selection-manifest-v1",
                "complete": True,
                "selected_match_ids": 4,
                "selected_pool_sha256": hashlib.sha256(pool_bytes).hexdigest(),
            }
        )
    )
    cells = [
        SimpleNamespace(
            selected_count=1,
            selected=(SimpleNamespace(match_id=match_id, game_duration_seconds=180),),
            regional_route="europe",
            game_version_patch=patch,
        )
        for match_id, _, patch in chosen
    ]
    monkeypatch.setattr(
        audit_module.FinalSelectedPool,
        "model_validate_json",
        lambda unused: SimpleNamespace(frame_sha256="a" * 64, selected_match_ids=4, cells=cells),
    )
    entries = []
    for partition, n in (("train", 2), ("calibration", 1)):
        filename = f"{partition}.00000.npz"
        np.savez_compressed(
            stage / "shards" / filename,
            nodes=np.zeros((n, 1)),
            edges=np.zeros((n, 1)),
            history_mask=np.zeros((n, 1)),
            ages_minutes=np.zeros((n, 1)),
            targets=np.zeros((n, 12), np.int8),
            hazard_targets=np.zeros((n, 3, 6), np.float32),
            match_offsets=np.arange(n + 1, dtype=np.int64),
        )
        entries.append(
            {"partition": partition, "file": filename, "matches": n, "start": 0,
             "observations": n}
        )
    monkeypatch.setattr(
        audit_module,
        "_validated_manifest",
        lambda unused: (
            b"synthetic staging",
            {
                "split_sha256": hashlib.sha256(split_path.read_bytes()).hexdigest(),
                "processing_manifest_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
                "shards": entries,
            },
        ),
    )
    output = tmp_path / "audit.json"
    result = audit_module.audit_confirmed_followup(
        processed, split_path, stage, selection, output
    )
    assert result["partitions"]["train"]["matches"] == 2
    assert result["partitions"]["calibration"]["matches"] == 1
    assert result["test_matches_unread"] == 1
    assert "EUW1_" not in output.read_text()
    # A changed selection pool breaks the bound even with identical in-memory records.
    (selection / "selected-pool.json").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="frozen split or processed inventory"):
        audit_module.audit_confirmed_followup(processed, split_path, stage, selection, output)
