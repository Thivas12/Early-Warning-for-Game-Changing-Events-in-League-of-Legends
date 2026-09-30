"""Preserve compact numerical evidence and reproduce the corpus-level audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from research.objective_onset import audit_match

UPSTREAM = "e276f3ea5e77b5b8652a68ef7687b5c494592853"


def pack_evidence(root: Path) -> dict:
    ledger = json.loads((root / "acquisition.json").read_text())
    if len(ledger["results"]) != ledger["attempted_matches"]:
        raise ValueError("Acquisition is still running; do not report a selected partial corpus")
    matches = []
    for row in sorted(ledger["results"], key=lambda r: r["match_id"]):
        if row["status"] != "complete":
            continue
        raw = (root / f"{row['match_id']}.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["output_sha256"]:
            raise ValueError("Extracted contact artifact changed after acquisition")
        data = json.loads(raw)
        matches.append(
            {
                "match_id": data["match_id"],
                "start_tick": data["game_start_tick"],
                "end_tick": data["game_end_tick"],
                "source_combat_records": data["source_combat_records"],
                "contacts": [
                    [e["tick"], int(e["log_type"] == "DEATH")] for e in data["combat_log"]
                ],
                "raw_replay_contact_ticks": [
                    e["tick"] for e in data["provenance"]["raw_replay_contacts"]
                ],
                "raw_dem_sha256": data["provenance"]["raw_dem_sha256"],
                "clock": data["provenance"]["clock"],
                "terminal_clock_crosscheck": data["provenance"]["terminal_clock_crosscheck"],
                "opendota_reference_sha256": data["provenance"]["opendota_reference_sha256"],
            }
        )
    return {
        "schema": "objective-contact-facts-v1",
        "source_repository": "https://github.com/whanyu1212/gem-dota",
        "source_revision": UPSTREAM,
        "contact_encoding": (
            "[pause-corrected tick, death indicator]; all other contacts positive damage"
        ),
        "scope": (
            "Dota parser fixture convenience sample; no League or population performance claim"
        ),
        "acquisition": ledger,
        "matches": matches,
    }


def expand_match(match: dict) -> dict:
    # Each retained non-death row was verified as strictly positive damage.
    return {
        "match_id": match["match_id"],
        "game_start_tick": match["start_tick"],
        "game_end_tick": match["end_tick"],
        "combat_log": [
            {
                "tick": tick,
                "log_type": "DEATH" if death else "DAMAGE",
                "target_name": "npc_dota_roshan",
                "value": 1,
            }
            for tick, death in match["contacts"]
        ],
        "roshans": [{"tick": tick} for tick, death in match["contacts"] if death],
        "source_combat_records": match["source_combat_records"],
        "onset_audit_clock_scope": "pause-corrected ticks at 30 Hz; leads are game time",
    }


def summarize(evidence: dict) -> dict:
    audits = [audit_match(expand_match(m)) for m in evidence["matches"]]
    counts = {}
    matches = []
    for audit in audits:
        primary = audit["scenarios"][1]
        if any(s["orphan_death_ticks"] for s in audit["scenarios"]):
            raise ValueError("Unresolved onset coverage: report orphan deaths before aggregation")
        per_match = {
            "match_id": audit["match_id"],
            "combat_records": audit["combat_records"],
            "primary_episodes": primary["episodes"],
            "terminal_events": audit["terminal_events"],
            "primary_metrics": [],
        }
        for scenario in audit["scenarios"]:
            for metric in scenario["metrics"]:
                key = (
                    scenario["quiet_gap_nominal_seconds"],
                    metric["delivery_delay_nominal_seconds"],
                    metric["minimum_lead_nominal_seconds"],
                )
                row = counts.setdefault(
                    key,
                    {
                        "quiet_gap_seconds": key[0],
                        "delivery_delay_seconds": key[1],
                        "minimum_lead_seconds": key[2],
                        "maximum_lead_seconds": 60,
                        "alarms": 0,
                        "completion_targets": 0,
                        "completion_hits": 0,
                        "onset_targets": 0,
                        "onset_hits": 0,
                    },
                )
                row["alarms"] += metric["completion"]["alarms"]
                for name, field in (("completion", "completion"), ("onset", "damage_onset")):
                    row[f"{name}_targets"] += metric[field]["targets"]
                    row[f"{name}_hits"] += metric[field]["hits"]
                if key[0] == 10 and key[1] == 0:
                    per_match["primary_metrics"].append(metric)
        matches.append(per_match)
    for row in counts.values():
        for name in ("completion", "onset"):
            denom = row[f"{name}_targets"]
            row[f"{name}_recall"] = row[f"{name}_hits"] / denom if denom else None
            row[f"{name}_unmatched_per_match"] = (row["alarms"] - row[f"{name}_hits"]) / len(audits)
    return {
        "status": "exploratory_label_audit; no trained predictor; no population inference",
        "independent_matches": len(audits),
        "attempted_matches": evidence["acquisition"]["attempted_matches"],
        "source_combat_records": sum(a["combat_records"] for a in audits),
        "source_revision": evidence["source_revision"],
        "source_hashes": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                Path("research/objective_onset.py"),
                Path("research/compile_objective_onset.py"),
            )
        },
        "metrics": [counts[k] for k in sorted(counts)],
        "matches": matches,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--contacts", type=Path)
    group.add_argument("--evidence", type=Path)
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args()
    evidence = (
        pack_evidence(args.contacts) if args.contacts else json.loads(args.evidence.read_text())
    )
    report = summarize(evidence)
    prefix = str(args.output_prefix)
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    if args.contacts:
        Path(prefix + "-evidence.json").write_text(
            json.dumps(evidence, separators=(",", ":")) + "\n"
        )
    Path(prefix + ".json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("independent_matches", "source_combat_records")}))
    for row in report["metrics"]:
        if row["quiet_gap_seconds"] == 10 and row["delivery_delay_seconds"] == 0:
            print(json.dumps(row))


if __name__ == "__main__":
    main()
