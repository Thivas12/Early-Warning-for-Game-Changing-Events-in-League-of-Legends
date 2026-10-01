"""Render reproducible tables from the paired analysis JSON, without recomputing policies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from league_ews.constants import EVENTS
from league_ews.notebook_ews import FAMILIES
from league_ews.notebook_experiment import SEEDS

NAMES = {"leagueews": "LeagueEWS", "gru": "GRU", "tcn": "TCN", "snapshot": "Snapshot"}


def interval(value: dict, scale: float = 1) -> str:
    a, b = value["conditional_95_interval"]
    return f"{value['estimate'] * scale:.3f} [{a * scale:.3f}, {b * scale:.3f}]"


def render(data: dict) -> str:
    lines = [
        "# League neural study tables",
        "",
        "Recall is a percentage; recall differences are percentage points. "
        "Burden is false-plus-late warnings per match. Brackets contain conditional "
        "95% paired whole-match bootstrap intervals. Seed means average fixed model "
        "performances; the three seeds are not independent match populations.",
        "",
    ]
    for h, lead in ((30, "10 to 30"), (60, "20 to 60")):
        overall = data["analysis"]["overall"][str(h)]
        lines += [
            f"## Useful lead of {lead} seconds",
            "",
            "| Family | Event | Mean recall and interval | "
            "Recall seed range | Mean burden and interval |",
            "|---|---|---|---|---|",
        ]
        for family in FAMILIES:
            for event in (*EVENTS, "macro"):
                r = overall["families"][family][event]
                m = r["mean_over_fixed_seeds"]
                v = r["seed_variability"]["timely_recall"]
                lines.append(
                    f"| {NAMES[family]} | {event} | {interval(m['timely_recall'], 100)} | "
                    f"{100 * v['min']:.3f} to {100 * v['max']:.3f} | "
                    f"{interval(m['false_plus_late_per_match'])} |"
                )
        lines += [
            "",
            "### Macro recall by seed",
            "",
            "| Family | Seed | Macro recall and interval | All event and region budgets met |",
            "|---|---|---|---|",
        ]
        for family in FAMILIES:
            r = overall["families"][family]["macro"]
            for seed in SEEDS:
                budget = all(
                    data["reports"][family][str(seed)]["warnings"][f"{e}_{h}"][
                        "regional_budget_met"
                    ]
                    for e in EVENTS
                )
                lines.append(
                    f"| {NAMES[family]} | {seed} | "
                    f"{interval(r['by_seed'][str(seed)]['timely_recall'], 100)} | {budget} |"
                )
        lines += [
            "",
            "### Paired macro recall differences",
            "",
            "LeagueEWS minus GRU at 10-30 seconds is primary. Other contrasts are exploratory.",
            "",
            "| Contrast | Mean difference and interval | 20260930 | 20261001 | 20261002 |",
            "|---|---|---|---|---|",
        ]
        for name, r in overall["contrasts"].items():
            r = r["macro"]
            cells = [interval(r["by_seed"][str(s)]["timely_recall"], 100) for s in SEEDS]
            lines.append(
                f"| {name.replace('_', ' ')} | "
                f"{interval(r['mean_over_fixed_seeds']['timely_recall'], 100)} | "
                f"{' | '.join(cells)} |"
            )
        lines += [
            "",
            "### Regional event results averaged over fixed seeds",
            "",
            "| Family | Event | Europe recall | Europe burden | "
            "Americas recall | Americas burden |",
            "|---|---|---|---|---|---|",
        ]
        for family in FAMILIES:
            for event in EVENTS:
                values = [
                    data["analysis"][route][str(h)]["families"][family][event][
                        "mean_over_fixed_seeds"
                    ]
                    for route in ("europe", "americas")
                ]
                cells = [
                    f"{100 * v['timely_recall']['estimate']:.3f} | "
                    f"{v['false_plus_late_per_match']['estimate']:.3f}"
                    for v in values
                ]
                lines.append(f"| {NAMES[family]} | {event} | {' | '.join(cells)} |")
        lines += [
            "",
            "### Regional budget failures",
            "",
            "Each budget is per event and region. A mean below one does not erase a failing seed.",
            "",
            "| Family | Seed | Event | Route | False plus late per match |",
            "|---|---|---|---|---|",
        ]
        failures = 0
        for family in FAMILIES:
            for seed in SEEDS:
                for event in EVENTS:
                    r = data["reports"][family][str(seed)]["warnings"][f"{event}_{h}"]
                    for route, value in r["by_route"].items():
                        burden = value["non_timely_alerts_per_match"]
                        if burden > 1:
                            failures += 1
                            lines.append(
                                f"| {NAMES[family]} | {seed} | {event} | {route} | {burden:.6f} |"
                            )
        if not failures:
            lines.append("| None | — | — | — | — |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(render(json.loads(args.input.read_bytes())))
