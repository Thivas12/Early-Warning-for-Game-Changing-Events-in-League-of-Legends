from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

import pytest

from league_ews.cli import main
from league_ews.final_split import freeze_final_split
from league_ews.sampling import load_registered_sampling_frame, sampling_cells


def _save(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def inputs(tmp_path):
    frame_path = "configs/rifthazard-sampling-frame.yaml"
    frame, _ = load_registered_sampling_frame(frame_path)
    raw_root = tmp_path / "raw"
    processed_root = tmp_path / "processed"
    raw_records = []
    processed_records = []
    for cell in sampling_cells(frame):
        for index in range(cell.final_target):
            match_id = f"{cell.platform_id}_{len(raw_records) + 1}"
            raw_records.append(
                {
                    "match_id": match_id,
                    "regional_route": cell.regional_route,
                    "game_version": f"{cell.game_version_patch}.1",
                    "game_creation_ms": index + 1,
                    "match_sha256": "a" * 64,
                    "timeline_sha256": "b" * 64,
                }
            )
            processed_records.append(
                {
                    "match_id": match_id,
                    "game_version": f"{cell.game_version_patch}.1",
                    "observations": 1,
                    "baron_events": 0,
                    "dragon_events": 0,
                    "teamfight_events": 0,
                    "sha256": "c" * 64,
                }
            )
    raw_sha = _save(
        raw_root / "collection-manifest.json",
        {
            "schema_version": "riot-raw-collection-v2",
            "collected_at": datetime.now(UTC).isoformat(),
            "requested": 36000,
            "collected": [],
            "skipped_existing": [],
            "available": raw_records,
            "contains_raw_player_identifiers": True,
            "redistribution": "not-authorized-by-this-manifest",
        },
    )
    processed_sha = _save(
        processed_root / "processing-manifest.json",
        {
            "schema_version": "league-ews-processing-manifest-v1",
            "normalizer": "riot-match-v5-normalized-v1",
            "label_policy": "exact-future-events-v1",
            "matches": processed_records,
            "contains_player_identifiers": False,
        },
    )
    g2 = tmp_path / "g2.json"
    _save(
        g2,
        {
            "schema_version": "riot-raw-validation-v5",
            "passed": True,
            "automated_passed": True,
            "g2_complete": True,
            "manifest_sha256": raw_sha,
            "manual_event_spot_check": {"status": "passed"},
            "sampling_frame": {"status": "passed"},
            "summary": {"valid_bundles": 36000},
        },
    )
    audit = tmp_path / "audit.json"
    _save(
        audit,
        {
            "schema_version": "league-ews-processed-validation-v1",
            "passed": True,
            "raw_manifest_sha256": raw_sha,
            "processing_manifest_sha256": processed_sha,
            "summary": {"validated_matches": 36000, "contains_player_identifiers": False},
        },
    )
    return raw_root, processed_root, frame_path, g2, audit


def test_freeze_final_split_has_registered_counts_order_and_no_public_ids(inputs, tmp_path, capsys):
    raw, processed, frame, g2, audit = inputs
    manifest = freeze_final_split(raw, processed, frame, g2, audit)
    assert manifest["summary"]["counts"] == {"train": 24000, "calibration": 6000, "test": 6000}
    assert manifest["summary"]["identifiers_in_summary"] is False
    assert "EUW1_1" not in json.dumps(manifest["summary"])
    assert manifest["partitions"]["test"][0]["game_version_patch"] == "16.17"
    assert all(
        entries == sorted(entries, key=lambda row: (row["game_creation_ms"], row["match_id"]))
        for entries in manifest["partitions"].values()
    )
    output = tmp_path / "private" / "split.json"
    args = [
        "freeze-final-split",
        "--raw",
        str(raw),
        "--processed",
        str(processed),
        "--sampling-frame",
        frame,
        "--g2-report",
        str(g2),
        "--processed-audit",
        str(audit),
        "--output",
        str(output),
    ]
    assert main(args) == 0
    assert "EUW1_1" not in capsys.readouterr().out
    assert main(args) == 0  # deterministic rerun
    assert json.loads(output.read_text()) == manifest


def test_freeze_rejects_stale_g2_or_audit(inputs):
    raw, processed, frame, g2, audit = inputs
    report = json.loads(g2.read_text())
    report["manual_event_spot_check"]["status"] = "pending"
    _save(g2, report)
    with pytest.raises(ValueError, match="G2 report"):
        freeze_final_split(raw, processed, frame, g2, audit)
    report["manual_event_spot_check"]["status"] = "passed"
    _save(g2, report)
    payload = json.loads(audit.read_text())
    payload["processing_manifest_sha256"] = "0" * 64
    _save(audit, payload)
    with pytest.raises(ValueError, match="Processed audit"):
        freeze_final_split(raw, processed, frame, g2, audit)


def test_freeze_rejects_cell_inventory_drift(inputs):
    raw, processed, frame, g2, audit = inputs
    manifest_path = raw / "collection-manifest.json"
    payload = json.loads(manifest_path.read_text())
    payload["available"][0]["regional_route"] = "americas"
    _save(manifest_path, payload)
    g2_payload = json.loads(g2.read_text())
    g2_payload["manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    _save(g2, g2_payload)
    audit_payload = json.loads(audit.read_text())
    audit_payload["raw_manifest_sha256"] = g2_payload["manifest_sha256"]
    _save(audit, audit_payload)
    with pytest.raises(ValueError, match="registered route-patch"):
        freeze_final_split(raw, processed, frame, g2, audit)


def test_freeze_rejects_changed_existing_manifest(inputs, tmp_path):
    raw, processed, frame, g2, audit = inputs
    output = tmp_path / "private" / "split.json"
    _save(output, {"schema_version": "different"})
    with pytest.raises(ValueError, match="refusing to overwrite"):
        main(
            [
                "freeze-final-split",
                "--raw",
                str(raw),
                "--processed",
                str(processed),
                "--sampling-frame",
                frame,
                "--g2-report",
                str(g2),
                "--processed-audit",
                str(audit),
                "--output",
                str(output),
            ]
        )
    assert json.loads(output.read_text()) == {"schema_version": "different"}


def test_freeze_rejects_missing_processed_match(inputs):
    raw, processed, frame, g2, audit = inputs
    path = processed / "processing-manifest.json"
    payload = json.loads(path.read_text())
    payload["matches"].pop()
    new_sha = _save(path, payload)
    audit_payload = json.loads(audit.read_text())
    audit_payload["processing_manifest_sha256"] = new_sha
    _save(audit, audit_payload)
    with pytest.raises(ValueError, match="same 36,000 matches"):
        freeze_final_split(raw, processed, frame, g2, audit)
