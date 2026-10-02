"""Render aggregate tables for the completed task-sharing comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from league_ews.constants import EVENTS
from league_ews.notebook_experiment import SEEDS
from scripts.render_neural_tables import interval


def render(data):
    lines = [
        "# League task sharing results",
        "",
        "Recall is a percentage; recall differences are percentage points. Burdens are "
        "warnings per match per event. Macro burden averages events, rather than representing "
        "a combined attention budget. Intervals are paired whole-match conditional 95% intervals, "
        "with region strata and identical sampled matches across events and seeds. Seed means "
        "average fixed fitted performances, not predictions or independent populations.",
        "",
    ]
    for h, lead in (("30", "10 to 30"), ("60", "20 to 60")):
        lines += [f"## Useful lead of {lead} seconds", ""]
        for region in ("overall", "europe", "americas"):
            section = data["analysis"][region][h]
            lines += [
                f"### {region.capitalize()} means over three seeds",
                "",
                "| Model | Event | Recall | False | Late | False plus late |",
                "|---|---|---:|---:|---:|---:|",
            ]
            for model, events in section["families"].items():
                for event in (*EVENTS, "macro"):
                    v = events[event]["mean_over_fixed_seeds"]
                    lines.append(
                        f"| {model} | {event} | {100 * v['timely_recall']['estimate']:.3f} | "
                        f"{v['false_per_match']['estimate']:.3f} | "
                        f"{v['late_per_match']['estimate']:.3f} | "
                        f"{v['false_plus_late_per_match']['estimate']:.3f} |"
                    )
            lines += [
                "",
                f"### {region.capitalize()} joint minus independent differences",
                "",
                "| Event | Recall and interval | False and interval | Late and interval | "
                "False plus late and interval |",
                "|---|---:|---:|---:|---:|",
            ]
            for event in (*EVENTS, "macro"):
                v = section["contrasts"]["leagueews_minus_independent"][event][
                    "mean_over_fixed_seeds"
                ]
                lines.append(
                    f"| {event} | {interval(v['timely_recall'], 100)} | "
                    f"{interval(v['false_per_match'])} | {interval(v['late_per_match'])} | "
                    f"{interval(v['false_plus_late_per_match'])} |"
                )
            lines += [""]
        overall = data["analysis"]["overall"][h]
        lines += [
            "### Every seed at each event",
            "",
            "| Seed | Event | Joint recall | Independent recall | Difference and interval |",
            "|---|---|---:|---:|---:|",
        ]
        for seed in SEEDS:
            for event in (*EVENTS, "macro"):
                a = overall["families"]["leagueews"][event]["by_seed"][str(seed)]["timely_recall"]
                b = overall["families"]["independent"][event]["by_seed"][str(seed)]["timely_recall"]
                d = overall["contrasts"]["leagueews_minus_independent"][event]["by_seed"][
                    str(seed)
                ]["timely_recall"]
                lines.append(
                    f"| {seed} | {event} | {100 * a['estimate']:.3f} | "
                    f"{100 * b['estimate']:.3f} | {interval(d, 100)} |"
                )
        lines += [
            "",
            "### Seed variability in timely recall",
            "",
            "| Model | Event | Minimum percent | Maximum percent | Sample SD in points |",
            "|---|---|---:|---:|---:|",
        ]
        for model, events in overall["families"].items():
            for event in (*EVENTS, "macro"):
                v = events[event]["seed_variability"]["timely_recall"]
                lines.append(
                    f"| {model} | {event} | {100 * v['min']:.3f} | "
                    f"{100 * v['max']:.3f} | {100 * v['sample_sd']:.3f} |"
                )
        lines += [
            "",
            "### Regional warning budget failures",
            "",
            "| Model | Seed | Event | Region | False plus late per match |",
            "|---|---|---|---|---:|",
        ]
        failures = 0
        for region in ("europe", "americas"):
            for model, events in data["analysis"][region][h]["families"].items():
                for event in EVENTS:
                    for seed, v in events[event]["by_seed"].items():
                        burden = v["false_plus_late_per_match"]["estimate"]
                        if burden > 1:
                            failures += 1
                            lines.append(
                                f"| {model} | {seed} | {event} | {region} | {burden:.6f} |"
                            )
        if not failures:
            lines.append("| None | | | | |")
        lines += [""]
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(render(json.loads(args.input.read_bytes())))
