"""Descriptive first-damage-per-life check using unchanged frozen command alarms."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from research.objective_onset import score_alarms
from research.run_precontact_pilot import aggregate


def first_damage_per_life(combat: pd.DataFrame, start: int, end: int) -> list[int]:
    contact = combat[
        combat.target_name.eq("npc_dota_roshan")
        & combat.tick.between(start, end)
        & (
            combat.event_type.eq("DOTA_COMBATLOG_DEATH")
            | (combat.event_type.eq("DOTA_COMBATLOG_DAMAGE") & combat.value.gt(0))
        )
    ].sort_values("tick", kind="stable")
    seen_damage = False
    targets = []
    for row in contact.itertuples():
        if row.event_type == "DOTA_COMBATLOG_DEATH":
            seen_damage = False
        elif not seen_damage:
            targets.append(int(row.tick))
            seen_damage = True
    return targets


def main() -> None:
    results = json.loads(Path("reports/command-anticipation-results-2026-09-30.json").read_text())
    quality = json.loads(Path("reports/command-anticipation-quality-2026-09-30.json").read_text())
    matches = [
        r for r in quality["matches"] if r["status"] == "accepted" and r["split"] == "evaluation"
    ]
    targets = {}
    for row in matches:
        mid = str(row["match_id"])
        combat = pd.read_parquet(
            Path("data/external/betty-commands") / mid / "combat_events.parquet"
        )
        targets[mid] = [
            t
            for t in first_damage_per_life(combat, row["start_tick"], row["end_tick"])
            if t >= row["start_tick"] + 320 * 30
        ]
    report = {
        "scope": "declared secondary analysis; no refitting or threshold changes",
        "models": [],
    }
    for model in results["models"]:
        rows = []
        for old in model["per_match_onset"]:
            mid = old["match_id"]
            score = score_alarms(old["alarm_ticks"], targets[mid], min_lead=600, max_lead=1800)
            rows.append({"match_id": mid, "day": old["day"], **score})
        report["models"].append(
            {"name": model["name"], "first_damage_per_life": aggregate(rows), "per_match": rows}
        )
    Path("reports/command-first-contact-2026-09-30.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    for row in report["models"]:
        print(row["name"], row["first_damage_per_life"])


if __name__ == "__main__":
    main()
