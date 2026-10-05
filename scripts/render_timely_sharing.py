"""Render frozen aggregate task-sharing evidence without selecting results."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from scripts.evaluate_timely_sharing import FAMILIES, POLICIES
from scripts.render_timely_neural import contrast_row
from scripts.render_warning_efficiency import compact_aggregate_json
from scripts.warning_efficiency import BUDGETS

EVENTS = ("baron", "dragon", "teamfight", "macro")
SHARING = "timely_leagueews-minus-timely_independent"
CUMULATIVE = "leagueews-minus-independent"
INTERACTION = "sharing_effect_difference_timely_minus_cumulative"
MECHANISMS = (SHARING, CUMULATIVE, INTERACTION)


def render(folder, plots=False):
    for name in ("analysis.json", "early-policies.json"):
        compact_aggregate_json(folder / name)
    data = json.loads((folder / "analysis.json").read_bytes())
    results = data["results"]
    header = [
        "| Comparison | Recall difference, pp [95%] | Burden difference [95%] | "
        "Recall difference by seed, pp |",
        "|---|---:|---:|---|",
    ]
    lines = [
        "# Useful-lead task-sharing evidence",
        "",
        "Recall is percent; differences are percentage points. Burden is false-plus-late "
        "warnings per match per event. Intervals are pointwise conditional 95% intervals "
        "from paired whole-match bootstrap draws. The four-budget mean averages fixed "
        "operating points, not independent matches. Seed order: 20260930, 20261001, 20261002. "
        "These adaptively selected studies use previously inspected calibration matches.",
        "",
    ]
    for h in ("30", "60"):
        lines += [f"## {'10-30' if h == '30' else '20-60'}-second warnings", ""]
        group = results["overall"][h]["matched_early_mixture"]["mean"]
        lines += [
            "### Four-budget matched-early mean",
            "",
            "| Model | Baron recall / burden | Dragon recall / burden | "
            "Teamfight recall / burden | Macro recall / burden |",
            "|---|---:|---:|---:|---:|",
        ]
        for family in FAMILIES:
            values = group["models"][family]
            cells = [
                f"{values[e]['timely_recall']['mean'] * 100:.3f} / "
                f"{values[e]['false_plus_late_per_match']['mean']:.4f}"
                for e in EVENTS
            ]
            lines.append(f"| {family} | " + " | ".join(cells) + " |")
        lines += ["", *header]
        for name, values in group["contrasts"].items():
            lines.append(contrast_row(name, values["macro"]))
        lines += ["", "### Sharing effects and target interaction by event", "", *header]
        for name in MECHANISMS:
            for event in EVENTS:
                lines.append(contrast_row(f"{name}: {event}", group["contrasts"][name][event]))
        for policy in POLICIES:
            lines += ["", f"### Useful-lead joint minus independent: {policy}", "", *header]
            for budget in (*BUDGETS, "mean"):
                value = results["overall"][h][policy][str(budget)]["contrasts"][SHARING]["macro"]
                lines.append(contrast_row(str(budget), value))
        lines += ["", "### Regional mechanisms, four-budget matched-early mean", "", *header]
        for region in ("europe", "americas"):
            for name in MECHANISMS:
                values = results[region][h]["matched_early_mixture"]["mean"]["contrasts"][name]
                for event in EVENTS:
                    lines.append(contrast_row(f"{region}: {name}: {event}", values[event]))
        lines += ["", "### Fine common grid, budget-one mechanisms", "", *header]
        for name in MECHANISMS:
            values = results["overall"][h]["dense_deterministic"]["1.0"]["contrasts"][name]
            for event in EVENTS:
                lines.append(contrast_row(f"{name}: {event}", values[event]))
        lines += ["", "### Original registered model comparisons, unchanged policy", "", *header]
        for other in ("gru", "tcn", "snapshot"):
            name = f"leagueews-minus-{other}"
            values = results["overall"][h]["deterministic"]["1.0"]["contrasts"][name]
            for event in EVENTS:
                lines.append(contrast_row(f"{name}: {event}", values[event]))
    lines += ["", "## Prespecified descriptive rules", "", "| Rule | Result |", "|---|---|"]
    lines.extend(f"| {k} | {v} |" for k, v in data["frozen_rules"].items())
    lines += [
        "",
        "All model/event/region/seed results and paired intervals are retained in "
        "`analysis.json`, `aggregate-counts.csv`, `by-seed.csv` and `budget-violations.csv`. "
        "Neither a diagnostic pass nor input exclusion establishes novelty or a causal "
        "effect of game actions. Previously failed regional gates remain failed.",
        "",
    ]
    (folder / "tables.md").write_text("\n".join(lines))
    with (folder / "budget-violations.csv").open("w") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=(
                "policy",
                "horizon",
                "budget",
                "family",
                "region",
                "seed",
                "event",
                "burden",
                "above_nominal",
                "above_hard_one",
            ),
        )
        writer.writeheader()
        writer.writerows(data["nominal_budget_violations"])
    if plots:
        make_plots(folder, results)


def make_plots(folder, results):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update(
        {"font.size": 10, "svg.fonttype": "none", "svg.hashsalt": "league-timely-sharing-v1"}
    )
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
    for row, h in enumerate(("30", "60")):
        values = results["overall"][h]["matched_early_mixture"]["mean"]["contrasts"]
        for col, (metric, scale, label) in enumerate(
            (
                ("timely_recall", 100, "Recall difference (percentage points)"),
                ("false_plus_late_per_match", 1, "False + late difference / match / event"),
            )
        ):
            ax = axes[row, col]
            for offset, name, title, color in (
                (-0.12, SHARING, "Sharing: useful-lead targets", "#237b81"),
                (0, CUMULATIVE, "Sharing: cumulative targets", "#7544a4"),
                (0.12, INTERACTION, "Change in sharing effect with targets", "#ae6334"),
            ):
                x = np.array([values[name][e][metric]["mean"] for e in EVENTS]) * scale
                ci = np.array([values[name][e][metric]["ci95"] for e in EVENTS]) * scale
                ax.errorbar(
                    x,
                    np.arange(4) + offset,
                    xerr=np.stack((x - ci[:, 0], ci[:, 1] - x)),
                    fmt="o",
                    capsize=3,
                    label=title,
                    color=color,
                )
            ax.axvline(0, color="#444444", lw=0.8, ls="--")
            ax.set_yticks(np.arange(4), EVENTS)
            ax.invert_yaxis()
            ax.set_xlabel(label)
            ax.set_title(f"{'10-30' if h == '30' else '20-60'}-second warnings")
            ax.grid(alpha=0.15)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("LeagueEWS: task sharing under useful-lead supervision", fontsize=14)
    fig.savefig(folder / "sharing-effects.svg", metadata={"Date": None})
    fig.savefig(folder / "sharing-effects.png", dpi=170)
    plt.close(fig)
    path = folder / "sharing-effects.svg"
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plots", action="store_true")
    args = parser.parse_args()
    render(args.output, args.plots)
