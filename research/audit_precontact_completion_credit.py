"""Post-hoc mechanism check with the same completed encounters as denominator."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from research.objective_onset import Contact, reactive_alarms, score_alarms, segment_episodes


def main() -> None:
    output = {
        "scope": "Post-hoc descriptive mechanism check; no fitting or threshold selection",
        "lead_seconds": [20, 60],
        "cooldown_seconds": 60,
        "cohorts": [],
    }
    for name, quality_name, directory in [
        ("initial", "precontact-quality", "betty-canonical"),
        ("fresh", "precontact-replication-quality", "betty-replication"),
    ]:
        quality = json.loads(Path(f"reports/{quality_name}-2026-09-30.json").read_text())
        rows = [
            r
            for r in quality["matches"]
            if r["status"] == "accepted" and r["split"] == "evaluation"
        ]
        counts = {
            gap: {
                "quiet_gap_seconds": gap,
                "matches": len(rows),
                "alarms": 0,
                "completed_encounters": 0,
                "completion_hits": 0,
                "same_encounter_onset_hits": 0,
                "completion_hits_at_or_after_own_onset": 0,
                "all_onsets": 0,
                "all_onset_hits": 0,
                "orphan_deaths": 0,
            }
            for gap in (5, 10, 20, 30)
        }
        for row in rows:
            path = Path(f"data/external/{directory}/{row['match_id']}/combat_events.parquet")
            combat = pd.read_parquet(path, columns=["tick", "target_name", "event_type", "value"])
            combat = combat[
                combat.tick.between(row["start_tick"], row["end_tick"])
                & combat.target_name.eq("npc_dota_roshan")
            ]
            wanted = combat[
                combat.event_type.eq("DOTA_COMBATLOG_DEATH")
                | (combat.event_type.eq("DOTA_COMBATLOG_DAMAGE") & combat.value.gt(0))
            ].sort_values("tick", kind="stable")
            contacts = [
                Contact(int(r.tick), "DEATH" if r.event_type.endswith("DEATH") else "DAMAGE")
                for r in wanted.itertuples()
            ]
            first_decision = row["start_tick"] + 300 * 30
            for gap, count in counts.items():
                episodes, orphan = segment_episodes(
                    contacts, quiet_ticks=gap * 30, recording_end=row["end_tick"]
                )
                alarms = [
                    t
                    for t in reactive_alarms(contacts, quiet_ticks=gap * 30, cooldown_ticks=1800)
                    if t >= first_decision
                ]
                eligible = [e for e in episodes if e.onset >= first_decision + 600]
                completed = [e for e in eligible if e.terminal is not None]
                onset = score_alarms(
                    alarms, [e.onset for e in eligible], min_lead=600, max_lead=1800
                )
                completion = score_alarms(
                    alarms, [e.terminal for e in completed], min_lead=600, max_lead=1800
                )
                paired_onset = score_alarms(
                    alarms, [e.onset for e in completed], min_lead=600, max_lead=1800
                )
                by_terminal = {e.terminal: e for e in completed}
                count["alarms"] += len(alarms)
                count["completed_encounters"] += len(completed)
                count["completion_hits"] += completion["hits"]
                count["same_encounter_onset_hits"] += paired_onset["hits"]
                count["completion_hits_at_or_after_own_onset"] += sum(
                    p["alarm"] >= by_terminal[p["target"]].onset for p in completion["matches"]
                )
                count["all_onsets"] += onset["targets"]
                count["all_onset_hits"] += onset["hits"]
                count["orphan_deaths"] += len(orphan)
        for count in counts.values():
            n = count["completed_encounters"]
            count["completion_recall"] = count["completion_hits"] / n if n else None
            count["same_encounter_onset_recall"] = (
                count["same_encounter_onset_hits"] / n if n else None
            )
            count["unmatched_per_match_for_completion"] = (
                count["alarms"] - count["completion_hits"]
            ) / len(rows)
            count["unmatched_per_match_for_paired_onset"] = (
                count["alarms"] - count["same_encounter_onset_hits"]
            ) / len(rows)
        output["cohorts"].append({"name": name, "sensitivities": list(counts.values())})
    Path("reports/precontact-completion-credit-2026-09-30.json").write_text(
        json.dumps(output, indent=2) + "\n"
    )
    for cohort in output["cohorts"]:
        print(
            cohort["name"], next(r for r in cohort["sensitivities"] if r["quiet_gap_seconds"] == 10)
        )


if __name__ == "__main__":
    main()
