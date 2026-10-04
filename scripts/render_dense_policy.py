"""Render aggregate threshold-resolution evidence without selecting policies."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from scripts.evaluate_dense_policy import FAMILIES, POLICIES
from scripts.render_timely_neural import contrast_row
from scripts.render_warning_efficiency import compact_aggregate_json
from scripts.warning_efficiency import BUDGETS

TARGET = "timely_leagueews-minus-leagueews"
EVENTS = ("baron", "dragon", "teamfight", "macro")


def render(folder, plots=False):
    for name in ("analysis.json", "early-policies.json"):
        compact_aggregate_json(folder / name)
    data = json.loads((folder / "analysis.json").read_bytes())
    results = data["results"]
    header = [
        "| Comparison | Recall difference, pp [95%] | Burden difference [95%] | "
        "Seed differences, pp |",
        "|---|---:|---:|---|",
    ]
    lines = [
        "# Threshold-resolution results",
        "",
        "Intervals are pointwise conditional paired whole-match 95% intervals. Burden is "
        "false-plus-late warnings per match per event. Budget means average four fixed "
        "operating points, not independent matches. Seed order: 20260930, 20261001, 20261002.",
        "",
    ]
    for h in ("30", "60"):
        lines += [f"## {'10-30' if h == '30' else '20-60'}-second warnings", ""]
        for policy in POLICIES:
            lines += [f"### {policy}: LeagueEWS target effect", "", *header]
            for budget in (*BUDGETS, "mean"):
                value = results["overall"][h][policy][str(budget)]["contrasts"][TARGET]["macro"]
                lines.append(contrast_row(str(budget), value))
            lines += [
                "",
                "Budget-one model recall percent / burden:",
                "",
                "| Model | Baron | Dragon | Teamfight | Macro |",
                "|---|---:|---:|---:|---:|",
            ]
            for family in FAMILIES:
                values = results["overall"][h][policy]["1.0"]["models"][family]
                cells = [
                    f"{values[e]['timely_recall']['mean'] * 100:.3f} / "
                    f"{values[e]['false_plus_late_per_match']['mean']:.4f}"
                    for e in EVENTS
                ]
                lines.append(f"| {family} | " + " | ".join(cells) + " |")
            lines += [""]
        lines += ["### Dense common budget-one contrasts", "", *header]
        for name, values in results["overall"][h]["dense_deterministic"]["1.0"][
            "contrasts"
        ].items():
            for event in EVENTS:
                lines.append(contrast_row(f"{name}: {event}", values[event]))
        lines += ["", "### Regional LeagueEWS target effect, dense common budget one", "", *header]
        for region in ("europe", "americas"):
            for event, value in results[region][h]["dense_deterministic"]["1.0"]["contrasts"][
                TARGET
            ].items():
                lines.append(contrast_row(f"{region}: {event}", value))
        lines += ["", "### Budget-one policy effects and target interactions", "", *header]
        for family, effects in data["policy_effects"]["overall"][h]["1.0"].items():
            for name, values in effects.items():
                lines.append(contrast_row(f"{family}: {name}", values["macro"]))
        lines += [""]
    lines += ["## Frozen gates", "", "| Gate | Pass |", "|---|---|"]
    lines.extend(f"| {k} | {v} |" for k, v in data["frozen_rules"].items())
    lines += [
        "",
        "All intervals, event/region/seed values and negative results are retained in "
        "`analysis.json`, `aggregate-counts.csv`, `by-seed.csv` and `budget-violations.csv`.",
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
        make_plot(folder, results)


def make_plot(folder, results):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update(
        {"font.size": 10, "svg.fonttype": "none", "svg.hashsalt": "league-dense-v1"}
    )
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
    for row, h in enumerate(("30", "60")):
        for col, (metric, scale, label) in enumerate(
            (
                ("timely_recall", 100, "Target effect on macro recall (percentage points)"),
                ("false_plus_late_per_match", 1, "Target effect on false + late / match / event"),
            )
        ):
            ax = axes[row, col]
            for offset, policy, name, color in (
                (-0.015, "deterministic", "Original common grid", "#687786"),
                (0, "dense_deterministic", "Fine common grid", "#237b81"),
                (0.015, "matched_early_mixture", "Original regional mixture", "#7544a4"),
            ):
                values = [
                    results["overall"][h][policy][str(b)]["contrasts"][TARGET]["macro"][metric]
                    for b in BUDGETS
                ]
                y = np.array([v["mean"] for v in values]) * scale
                ci = np.array([v["ci95"] for v in values]) * scale
                ax.errorbar(
                    np.array(BUDGETS) + offset,
                    y,
                    yerr=np.stack((y - ci[:, 0], ci[:, 1] - y)),
                    fmt="o-",
                    capsize=3,
                    label=name,
                    color=color,
                )
            ax.axhline(0, color="#444444", lw=0.8, ls="--")
            ax.set_xticks(BUDGETS)
            ax.set_xlabel("Prespecified EARLY warning budget")
            ax.set_ylabel(label)
            ax.set_title(f"{'10-30' if h == '30' else '20-60'}-second warnings")
            ax.grid(alpha=0.15)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("LeagueEWS useful-lead target effect: threshold-resolution control", fontsize=14)
    fig.savefig(folder / "resolution-effects.svg", metadata={"Date": None})
    fig.savefig(folder / "resolution-effects.png", dpi=170)
    plt.close(fig)
    path = folder / "resolution-effects.svg"
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plots", action="store_true")
    args = parser.parse_args()
    render(args.output, args.plots)
