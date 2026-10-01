"""Render the completed matched-architecture history comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from league_ews.constants import EVENTS
from league_ews.notebook_experiment import SEEDS
from scripts.render_neural_tables import interval


def render(data: dict, original: dict) -> str:
    family = data["family"]
    lines = [
        "# League history ablation tables",
        "",
        "The two variants have the same architecture, parameter count, training data, "
        "initial seeds and update budget. Current-only replaces past values and "
        "missingness with current state, retaining ages and valid lengths. Recall is "
        "a percentage and differences are percentage points. Burden is false-plus-late "
        "warnings per match. Brackets are conditional paired 95% intervals.",
        "",
    ]
    for h, lead in ((30, "10 to 30"), (60, "20 to 60")):
        r = data["analysis"]["overall"][str(h)]
        contrast = r["contrasts"]["full_history_minus_current_only"]
        lines += [
            f"## Useful lead of {lead} seconds",
            "",
            "| Event | Full history recall | Current-only recall | "
            "Recall difference and interval | Full burden | Current-only burden |",
            "|---|---|---|---|---|---|",
        ]
        for event in (*EVENTS, "macro"):
            full = r["families"]["full_history"][event]["mean_over_fixed_seeds"]
            current = r["families"]["current_only"][event]["mean_over_fixed_seeds"]
            diff = contrast[event]["mean_over_fixed_seeds"]["timely_recall"]
            lines.append(
                f"| {event} | {100 * full['timely_recall']['estimate']:.3f} | "
                f"{100 * current['timely_recall']['estimate']:.3f} | {interval(diff, 100)} | "
                f"{full['false_plus_late_per_match']['estimate']:.3f} | "
                f"{current['false_plus_late_per_match']['estimate']:.3f} |"
            )
        lines += [
            "",
            "### Macro recall by seed",
            "",
            "| Seed | Full history | Current-only | Difference and interval | "
            "Both variants meet all regional budgets |",
            "|---|---|---|---|---|",
        ]
        for seed in SEEDS:
            s = str(seed)
            full = r["families"]["full_history"]["macro"]["by_seed"][s]["timely_recall"]
            current = r["families"]["current_only"]["macro"]["by_seed"][s]["timely_recall"]
            diff = contrast["macro"]["by_seed"][s]["timely_recall"]
            budget = all(
                reports[family][s]["warnings"][f"{e}_{h}"]["regional_budget_met"]
                for reports in (original["reports"], data["followup_reports"])
                for e in EVENTS
            )
            lines.append(
                f"| {seed} | {100 * full['estimate']:.3f} | "
                f"{100 * current['estimate']:.3f} | {interval(diff, 100)} | {budget} |"
            )
        lines += [
            "",
            "### Regional event comparisons averaged over fixed seeds",
            "",
            "| Region | Event | Full history recall | Current-only recall | "
            "Difference and interval | Full burden | Current-only burden |",
            "|---|---|---|---|---|---|---|",
        ]
        for route in ("europe", "americas"):
            region = data["analysis"][route][str(h)]
            for event in EVENTS:
                full = region["families"]["full_history"][event]["mean_over_fixed_seeds"]
                current = region["families"]["current_only"][event]["mean_over_fixed_seeds"]
                diff = region["contrasts"]["full_history_minus_current_only"][event][
                    "mean_over_fixed_seeds"
                ]["timely_recall"]
                lines.append(
                    f"| {route} | {event} | {100 * full['timely_recall']['estimate']:.3f} | "
                    f"{100 * current['timely_recall']['estimate']:.3f} | "
                    f"{interval(diff, 100)} | "
                    f"{full['false_plus_late_per_match']['estimate']:.3f} | "
                    f"{current['false_plus_late_per_match']['estimate']:.3f} |"
                )
        lines += [
            "",
            "### Regional budget failures",
            "",
            "| Variant | Seed | Event | Route | False plus late per match |",
            "|---|---|---|---|---|",
        ]
        failures = 0
        for variant, reports in (
            ("Full history", original["reports"]),
            ("Current-only", data["followup_reports"]),
        ):
            for s, report in reports[family].items():
                for event in EVENTS:
                    for route, m in report["warnings"][f"{event}_{h}"]["by_route"].items():
                        if m["non_timely_alerts_per_match"] > 1:
                            failures += 1
                            lines.append(
                                f"| {variant} | {s} | {event} | {route} | "
                                f"{m['non_timely_alerts_per_match']:.6f} |"
                            )
        if not failures:
            lines.append("| None | - | - | - | - |")
        lines.append("")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("original", "followup", "output"):
        parser.add_argument(f"--{flag}", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(
        render(json.loads(args.followup.read_bytes()), json.loads(args.original.read_bytes()))
    )
