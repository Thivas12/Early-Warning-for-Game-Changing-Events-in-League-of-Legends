"""Publish aggregate timely-target evidence; no fitting or policy selection."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from scripts.evaluate_timely_neural import FAMILIES, POLICIES
from scripts.render_warning_efficiency import compact_aggregate_json, interval
from scripts.warning_efficiency import BUDGETS

EVENTS = ("baron", "dragon", "teamfight", "macro")
TARGET_CONTRASTS = (
    "timely_leagueews-minus-leagueews",
    "timely_tcn-minus-tcn",
    "timely_leagueews-minus-timely_tcn",
    "target_effect_difference_leagueews_minus_tcn",
)


def contrast_row(name, values):
    return (
        f"| {name} | {interval(values['timely_recall'], 100)} | "
        f"{interval(values['false_plus_late_per_match'])} | "
        + ", ".join(f"{v * 100:+.4f}" for v in values["timely_recall"]["seeds"])
        + " |"
    )


def render(folder, plots=False):
    for name in ("analysis.json", "early-policies.json"):
        compact_aggregate_json(folder / name)
    data = json.loads((folder / "analysis.json").read_bytes())
    results = data["results"]
    lines = [
        "# Timely-target neural evidence",
        "",
        "Recall is percent, differences percentage points. Burden is expected false-plus-late "
        "warnings per match per event. Intervals are paired whole-match conditional 95% "
        "intervals, pointwise and unadjusted. Early cost equality does not imply later equality. "
        "The four-budget mean averages fixed policies, not independent matches. Seed order: "
        "20260930, 20261001, 20261002.",
        "",
    ]
    header = [
        "| Contrast / event | Recall difference [95%] | Burden difference [95%] | "
        "Recall differences by seed |",
        "|---|---:|---:|---|",
    ]
    for h, lead in (("30", "10-30"), ("60", "20-60")):
        group = results["overall"][h]["matched_early_mixture"]["mean"]
        lines += [
            f"## {lead} seconds, four-budget matched-early mean",
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
        lines += ["", "### Target effects by event", "", *header]
        for name in TARGET_CONTRASTS:
            for event in EVENTS[:-1]:
                lines.append(contrast_row(f"{name}: {event}", group["contrasts"][name][event]))
        for policy in POLICIES:
            lines += ["", f"### LeagueEWS target effect: {policy}", "", *header]
            for budget in (*BUDGETS, "mean"):
                value = results["overall"][h][policy][str(budget)]["contrasts"][
                    "timely_leagueews-minus-leagueews"
                ]["macro"]
                lines.append(contrast_row(str(budget), value))
        lines += ["", "### Regional target effects, four-budget matched-early mean", "", *header]
        for region in ("europe", "americas"):
            for name in TARGET_CONTRASTS[:3]:
                for event in EVENTS:
                    value = results[region][h]["matched_early_mixture"]["mean"]["contrasts"][name][
                        event
                    ]
                    lines.append(contrast_row(f"{region}: {name}: {event}", value))
        lines += ["", "### Policy changes, four-budget mean", "", *header]
        for family, effects in data["policy_effects"]["overall"][h]["mean"].items():
            for name, values in effects.items():
                lines.append(contrast_row(f"{family}: {name}", values["macro"]))
    lines += ["", "## Frozen gates", "", "| Gate | Pass |", "|---|---|"]
    lines.extend(f"| {k} | {v} |" for k, v in data["frozen_rules"].items())
    lines += [
        "",
        "All regional failures are in `budget-violations.csv`. `aggregate-counts.csv` "
        "contains denominators and expected counts, `by-seed.csv` every seed point, and "
        "`analysis.json` all paired intervals, seed ranges/SD, policy effects and gates.",
        "",
    ]
    (folder / "tables.md").write_text("\n".join(lines))
    with (folder / "budget-violations.csv").open("w") as stream:
        fields = (
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
        )
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data["nominal_budget_violations"])
    if plots:
        make_plots(folder, results)
        for name in ("target-effects.svg", "event-target-effects.svg"):
            path = folder / name
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


def make_plots(folder, results):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update(
        {"font.size": 10, "svg.fonttype": "none", "svg.hashsalt": "league-timely-neural-v1"}
    )
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
    for row, h in enumerate(("30", "60")):
        for col, (metric, scale, label) in enumerate(
            (
                ("timely_recall", 100, "Macro recall change (percentage points)"),
                ("false_plus_late_per_match", 1, "Change in false + late / match / event"),
            )
        ):
            ax = axes[row, col]
            for offset, name, label_name, color in (
                (-0.01, TARGET_CONTRASTS[0], "LeagueEWS target effect", "#237b81"),
                (0.01, TARGET_CONTRASTS[1], "TCN target effect", "#7544a4"),
            ):
                values = [
                    results["overall"][h]["matched_early_mixture"][str(b)]["contrasts"][name][
                        "macro"
                    ][metric]
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
                    label=label_name,
                    color=color,
                )
            ax.axhline(0, color="#444444", lw=0.8, ls="--")
            ax.set_xticks(BUDGETS)
            ax.set_xlabel("Prespecified EARLY warning budget")
            ax.set_ylabel(label)
            ax.set_title(f"{'10-30' if h == '30' else '20-60'}-second warnings")
            ax.grid(alpha=0.15)
    axes[0, 0].legend(fontsize=9)
    fig.suptitle("Changing evaluated targets to useful next-event lead windows", fontsize=14)
    for suffix in ("svg", "png"):
        fig.savefig(
            folder / f"target-effects.{suffix}",
            dpi=170,
            metadata={"Date": None} if suffix == "svg" else None,
        )
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained", sharey=True)
    for ax, h in zip(axes, ("30", "60"), strict=True):
        for offset, name, label_name, color in (
            (-0.1, TARGET_CONTRASTS[0], "LeagueEWS", "#237b81"),
            (0.1, TARGET_CONTRASTS[1], "TCN", "#7544a4"),
        ):
            values = results["overall"][h]["matched_early_mixture"]["mean"]["contrasts"][name]
            x = np.array([values[e]["timely_recall"]["mean"] for e in EVENTS]) * 100
            ci = np.array([values[e]["timely_recall"]["ci95"] for e in EVENTS]) * 100
            ax.errorbar(
                x,
                np.arange(4) + offset,
                xerr=np.stack((x - ci[:, 0], ci[:, 1] - x)),
                fmt="o",
                capsize=3,
                label=label_name,
                color=color,
            )
        ax.axvline(0, color="#444444", lw=0.8, ls="--")
        ax.set_xlabel("Recall change (percentage points), four-budget mean")
        ax.set_title(f"{'10-30' if h == '30' else '20-60'}-second warnings")
        ax.set_yticks(np.arange(4), EVENTS)
        ax.grid(alpha=0.15)
    axes[0].invert_yaxis()
    axes[0].legend()
    fig.suptitle("Objective alignment: per-event effects with paired match uncertainty")
    for suffix in ("svg", "png"):
        fig.savefig(
            folder / f"event-target-effects.{suffix}",
            dpi=170,
            metadata={"Date": None} if suffix == "svg" else None,
        )
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plots", action="store_true")
    args = parser.parse_args()
    render(args.output, args.plots)
