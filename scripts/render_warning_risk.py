"""Publish the complete warning-risk tradeoffs and fixed architecture contrasts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from scripts.analyse_warning_risk import PRIMARY
from scripts.render_timely_neural import contrast_row
from scripts.render_warning_efficiency import compact_aggregate_json
from scripts.warning_efficiency import BUDGETS
from scripts.warning_risk import FAMILIES, POLICIES, REGIONS

EVENTS = ("baron", "dragon", "teamfight", "macro")
LABELS = ("Uncapped empirical", "Cap 4 empirical", "Cap 4 empirical sequence", "Cap 4 KL sequence")
COLORS = ("#555555", "#3784a8", "#a273ae", "#c5721b")
HEADER = [
    "| Comparison | Recall difference, pp [95%] | Burden difference [95%] | "
    "Recall difference by seed, pp |",
    "|---|---:|---:|---|",
]


def render(folder, plots=False):
    for name in ("analysis.json", "early-policies.json"):
        compact_aggregate_json(folder / name)
    data = json.loads((folder / "analysis.json").read_bytes())
    results = data["results"]
    lines = [
        "# Capped warning-risk evidence",
        "",
        "Recall is percent; recall differences are percentage points. Burden is false-plus-late "
        "warnings per match per event. Intervals are pointwise conditional 95% paired whole-match "
        "bootstrap intervals, with fixed seed order 20260930, 20261001, 20261002. "
        "Four-budget means "
        "average operating points. Repeated calibration inspection prevents a fresh confirmation "
        "or certification claim. All study rules and failures remain visible.",
        "",
    ]
    for h in ("30", "60"):
        lines += [f"## {'10-30' if h == '30' else '20-60'}-second warnings", ""]
        for policy in POLICIES:
            group = results["overall"][h][policy]["mean"]
            lines += [
                f"### {policy}, four-budget mean",
                "",
                "| Model | Baron recall / burden | Dragon recall / burden | "
                "Teamfight recall / burden | Macro recall / burden |",
                "|---|---:|---:|---:|---:|",
            ]
            for f in FAMILIES:
                values = group["models"][f]
                cells = [
                    f"{values[e]['timely_recall']['mean'] * 100:.3f} / "
                    f"{values[e]['false_plus_late_per_match']['mean']:.4f}"
                    for e in EVENTS
                ]
                lines.append(f"| {f} | " + " | ".join(cells) + " |")
            lines += ["", *HEADER]
            for name, values in group["contrasts"].items():
                for event in EVENTS:
                    lines.append(contrast_row(f"{name}: {event}", values[event]))
            lines += ["", "Primary architecture contrast by budget:", "", *HEADER]
            for budget in BUDGETS:
                lines.append(
                    contrast_row(
                        str(budget),
                        results["overall"][h][policy][str(budget)]["contrasts"][PRIMARY]["macro"],
                    )
                )
        for region in ("overall", *REGIONS):
            lines += [
                f"### {region}: every within-model policy effect, four-budget mean",
                "",
                *HEADER,
            ]
            for f in FAMILIES:
                for name, values in data["policy_effects"][region][h]["mean"][f].items():
                    for event in EVENTS:
                        lines.append(contrast_row(f"{f}: {name}: {event}", values[event]))
        lines += ["", "### Regional primary architecture results", "", *HEADER]
        for region in REGIONS:
            for policy in POLICIES:
                for budget in ("1.0", "mean"):
                    for event, values in results[region][h][policy][budget]["contrasts"][
                        PRIMARY
                    ].items():
                        lines.append(contrast_row(f"{region}: {policy}: {budget}: {event}", values))
    lines += ["", "## Prespecified descriptive rules", "", "| Rule | Result |", "|---|---|"]
    lines.extend(f"| {k} | {v} |" for k, v in data["frozen_rules"].items())
    violations = data["nominal_budget_violations"]
    lines += [
        "",
        "## Regional violations",
        "",
        "Each row counts event/region/seed/budget cells out of 72. The full CSV lists every "
        "nominal-budget violation, including those below the hard-one level.",
        "",
        "| Family / window / policy | Nominal budget violations | Hard-one violations |",
        "|---|---:|---:|",
    ]
    for f in FAMILIES:
        for h in (30, 60):
            for p in POLICIES:
                rows = [
                    v
                    for v in violations
                    if v["family"] == f and v["horizon"] == h and v["policy"] == p
                ]
                lines.append(
                    f"| {f} / {h} / {p} | {len(rows)} | {sum(v['above_hard_one'] for v in rows)} |"
                )
    selected = json.loads((folder / "early-policies.json").read_bytes())
    lines += [
        "",
        "## Silent policies",
        "",
        "| Policy | Silent head/budget cells out of 360 |",
        "|---|---:|",
    ]
    for p in POLICIES:
        count = sum(i == 0 for head in selected.values() for i in head["policies"][p].values())
        lines.append(f"| {p} | {count} |")
    lines += [
        "",
        "Precision and cap activity are descriptive points. The aggregate counts retain "
        "every warning, timely hit and event denominator; `analysis.json` retains cap activity "
        "per head, region, policy and budget. A match at the cap is not necessarily truncated: "
        "activity counts matches where the same threshold would emit more than four warnings.",
        "",
    ]
    with (folder / "aggregate-counts.csv").open() as stream:
        raw = list(csv.DictReader(stream))
    lines += [
        "## Budget-one event precision for the primary architectures",
        "",
        "Precision pools timely hits and alerts over the three fixed seeds within each event; "
        "it is descriptive and does not treat seeds as independent matches. "
        "A dash means zero alerts.",
        "",
        "| Window / policy / model | Baron timely precision | Dragon timely precision | "
        "Teamfight timely precision |",
        "|---|---:|---:|---:|",
    ]
    for h in ("30", "60"):
        for p in POLICIES:
            for f in FAMILIES[:2]:
                cells = []
                for event in EVENTS[:3]:
                    rows = [
                        v
                        for v in raw
                        if v["region"] == "overall"
                        and v["horizon"] == h
                        and v["policy"] == p
                        and v["budget"] == "1.0"
                        and v["family"] == f
                        and v["event"] == event
                    ]
                    alerts = sum(int(v["alerts"]) for v in rows)
                    hits = sum(int(v["timely"]) for v in rows)
                    cells.append(f"{100 * hits / alerts:.3f}%" if alerts else "—")
                lines.append(f"| {h} / {p} / {f} | " + " | ".join(cells) + " |")
    (folder / "tables.md").write_text("\n".join(lines) + "\n")
    with (folder / "budget-violations.csv").open("w") as stream:
        writer = csv.DictWriter(
            stream,
            lineterminator="\n",
            fieldnames=(
                "family",
                "policy",
                "horizon",
                "budget",
                "region",
                "seed",
                "event",
                "burden",
                "above_nominal",
                "above_hard_one",
            ),
        )
        writer.writeheader()
        writer.writerows(violations)
    if plots:
        make_plots(folder, results)


def make_plots(folder, results):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update(
        {"font.size": 10, "svg.fonttype": "none", "svg.hashsalt": "league-warning-risk-v1"}
    )
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), layout="constrained")
    for row, h in enumerate(("30", "60")):
        for col, f in enumerate(FAMILIES[:2]):
            ax = axes[row, col]
            for p, label, color in zip(POLICIES, LABELS, COLORS, strict=True):
                stats = [results["overall"][h][p][str(b)]["models"][f]["macro"] for b in BUDGETS]
                x = [v["false_plus_late_per_match"]["mean"] for v in stats]
                y = [v["timely_recall"]["mean"] * 100 for v in stats]
                ax.plot(x, y, "o-", color=color, label=label, ms=4)
            ax.axvline(1, color="#777777", ls="--", lw=0.8)
            ax.set_title(
                f"{'LeagueEWS' if col == 0 else 'TCN'}, {'10-30' if h == '30' else '20-60'} seconds"
            )
            ax.set_xlabel("Later false + late warnings / match / event")
            ax.set_ylabel("Later macro timely recall (%)")
            ax.grid(alpha=0.2)
            ax.legend(fontsize=8)
    fig.suptitle(
        "Causal cap and uncertainty allowance: four fixed early budgets\n"
        "Points are descriptive means; intervals and regional failures are in the tables"
    )
    for suffix in ("png", "svg"):
        fig.savefig(folder / f"policy-tradeoffs.{suffix}", dpi=180, bbox_inches="tight")
    path = folder / "policy-tradeoffs.svg"
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), layout="constrained")
    for row, h in enumerate(("30", "60")):
        for col, (metric, scale, label) in enumerate(
            (
                ("timely_recall", 100, "Recall difference (percentage points)"),
                ("false_plus_late_per_match", 1, "False + late difference / match / event"),
            )
        ):
            ax = axes[row, col]
            for pi, offset in ((0, -0.13), (3, 0.13)):
                values = results["overall"][h][POLICIES[pi]]["mean"]["contrasts"][PRIMARY]
                point = np.array([values[e][metric]["mean"] for e in EVENTS]) * scale
                ci = np.array([values[e][metric]["ci95"] for e in EVENTS]) * scale
                ax.errorbar(
                    point,
                    np.arange(4) + offset,
                    xerr=np.stack((point - ci[:, 0], ci[:, 1] - point)),
                    fmt="o",
                    capsize=3,
                    color=COLORS[pi],
                    label=LABELS[pi],
                )
            ax.axvline(0, color="#555555", ls="--", lw=0.8)
            ax.set_yticks(np.arange(4), EVENTS)
            ax.invert_yaxis()
            ax.set_xlabel(label)
            ax.set_title(f"{'10-30' if h == '30' else '20-60'}-second warnings")
            ax.grid(axis="x", alpha=0.2)
            ax.legend(fontsize=8)
    fig.suptitle(
        "Equal-weight LeagueEWS minus equal-weight TCN\n"
        "Four-budget means; pointwise conditional 95% paired intervals"
    )
    for suffix in ("png", "svg"):
        fig.savefig(folder / f"risk-architecture-effects.{suffix}", dpi=180, bbox_inches="tight")
    path = folder / "risk-architecture-effects.svg"
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plots", action="store_true")
    args = parser.parse_args()
    render(args.output, args.plots)
