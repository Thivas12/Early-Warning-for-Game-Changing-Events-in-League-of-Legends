"""Render aggregate evidence without changing analyses or selecting policies."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from scripts.run_warning_efficiency import FAMILIES, POLICIES
from scripts.warning_efficiency import BUDGETS


def interval(v, scale=1):
    return f"{v['mean'] * scale:+.4f} [{v['ci95'][0] * scale:+.4f}, {v['ci95'][1] * scale:+.4f}]"


def compact_aggregate_json(path):
    """Lossless publication formatting: keep arrays and short records together."""
    data = json.loads(path.read_bytes())

    def encode(value, depth=0):
        flat = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
        if isinstance(value, list) and value and isinstance(value[0], dict) and len(flat) > 350:
            padding = "  " * (depth + 1)
            rows = [padding + encode(v, depth + 1) for v in value]
            return "[\n" + ",\n".join(rows) + "\n" + "  " * depth + "]"
        if not isinstance(value, dict) or len(flat) <= 350:
            return flat
        padding = "  " * (depth + 1)
        rows = [
            padding + json.dumps(k) + ": " + encode(v, depth + 1) for k, v in sorted(value.items())
        ]
        return "{\n" + ",\n".join(rows) + "\n" + "  " * depth + "}"

    encoded = encode(data) + "\n"
    if json.loads(encoded) != data:
        raise ValueError("Publication formatting changed aggregate evidence")
    path.write_text(encoded)


def render(folder, plots=False):
    for name in ("analysis.json", "early-policies.json"):
        compact_aggregate_json(folder / name)
    data = json.loads((folder / "analysis.json").read_bytes())
    results = data["results"]
    lines = [
        "# Warning-efficiency aggregate tables",
        "",
        "Recall is percent; differences are percentage points. Burden is false-plus-late "
        "warnings per match per event. Mixtures match EARLY cost, not later cost. Intervals "
        "are paired whole-match conditional 95% intervals. Budget means give equal weight "
        "to four fixed points, not additional matches.",
        "",
    ]
    for h in ("30", "60"):
        lead = "10-30" if h == "30" else "20-60"
        group = results["overall"][h]["matched_early_mixture"]["mean"]
        lines += [
            f"## {lead} seconds: four-budget mean, matched-early policy",
            "",
            "| Model | Baron recall / burden | Dragon recall / burden | "
            "Teamfight recall / burden | Macro recall / burden |",
            "|---|---:|---:|---:|---:|",
        ]
        for family in FAMILIES:
            event = group["models"][family]
            cells = [
                f"{event[e]['timely_recall']['mean'] * 100:.3f} / "
                f"{event[e]['false_plus_late_per_match']['mean']:.4f}"
                for e in ("baron", "dragon", "teamfight", "macro")
            ]
            lines.append(f"| {family} | " + " | ".join(cells) + " |")
        lines += [
            "",
            "| Contrast | Macro recall difference [95%] | Burden difference [95%] | "
            "False difference | Late difference | Recall differences by seed |",
            "|---|---:|---:|---:|---:|---|",
        ]
        for contrast, events in group["contrasts"].items():
            v = events["macro"]
            lines.append(
                f"| {contrast} | {interval(v['timely_recall'], 100)} | "
                f"{interval(v['false_plus_late_per_match'])} | "
                f"{v['false_per_match']['mean']:+.5f} | {v['late_per_match']['mean']:+.5f} | "
                + ", ".join(f"{n * 100:+.4f}" for n in v["timely_recall"]["seeds"])
                + " |"
            )
        for policy in POLICIES:
            lines += [
                "",
                f"### PCGrad-joint, {policy}",
                "",
                "| Early budget | Recall difference [95%] | Burden difference [95%] | "
                "Recall differences by seed |",
                "|---|---:|---:|---|",
            ]
            for b in (*BUDGETS, "mean"):
                v = results["overall"][h][policy][str(b)]["contrasts"]["pcgrad-minus-leagueews"][
                    "macro"
                ]
                lines.append(
                    f"| {b} | {interval(v['timely_recall'], 100)} | "
                    f"{interval(v['false_plus_late_per_match'])} | "
                    + ", ".join(f"{n * 100:+.4f}" for n in v["timely_recall"]["seeds"])
                    + " |"
                )
    lines += ["", "## All prespecified gates", "", "| Gate | Result |", "|---|---|"]
    lines.extend(f"| {k} | {v} |" for k, v in data["frozen_rules"].items())
    lines += [
        "",
        "## Regional PCGrad-joint, budget-mean matched-early primary",
        "",
        "| Region | Event | Recall difference [95%] | Burden difference [95%] |",
        "|---|---|---:|---:|",
    ]
    for region in ("europe", "americas"):
        for event, v in results[region]["30"]["matched_early_mixture"]["mean"]["contrasts"][
            "pcgrad-minus-leagueews"
        ].items():
            lines.append(
                f"| {region} | {event} | {interval(v['timely_recall'], 100)} | "
                f"{interval(v['false_plus_late_per_match'])} |"
            )
    lines += [
        "",
        "All seed/region/event/lead/budget failures, including below the hard-one limit, "
        "are in `budget-violations.csv`; denominators and expected counts are in "
        "`aggregate-counts.csv`. All models' seed points are in `by-seed.csv`; every "
        "conditional interval is in `analysis.json`. Seed order is 20260930, 20261001, 20261002.",
        "",
    ]
    (folder / "tables.md").write_text("\n".join(lines))
    with (folder / "budget-violations.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(data["nominal_budget_violations"][0]))
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
        {"font.size": 10, "svg.fonttype": "none", "svg.hashsalt": "league-warning-efficiency-v1"}
    )
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
    for row, h in enumerate(("30", "60")):
        for col, (metric, scale, label) in enumerate(
            (
                ("timely_recall", 100, "Macro recall difference (percentage points)"),
                ("false_plus_late_per_match", 1, "Extra false + late warnings / match / event"),
            )
        ):
            ax = axes[row, col]
            for offset, policy, color, name in (
                (-0.012, "deterministic", "#687786", "Original grid rule"),
                (0.012, "matched_early_mixture", "#7544a4", "Exact early-cost mixture"),
            ):
                v = [
                    results["overall"][h][policy][str(b)]["contrasts"]["pcgrad-minus-leagueews"][
                        "macro"
                    ][metric]
                    for b in BUDGETS
                ]
                y = np.array([x["mean"] for x in v]) * scale
                ci = np.array([x["ci95"] for x in v]) * scale
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
            ax.set_title(f"PCGrad - joint LeagueEWS, {'10-30' if h == '30' else '20-60'} s")
            ax.grid(alpha=0.15)
    axes[0, 0].legend(fontsize=9)
    fig.suptitle("PCGrad's apparent gain depends on the warning-policy comparison", fontsize=14)
    fig.savefig(folder / "pcgrad-budget-curves.svg", metadata={"Date": None})
    fig.savefig(folder / "pcgrad-budget-curves.png", dpi=170)
    plt.close(fig)
    contrasts = list(results["overall"]["30"]["matched_early_mixture"]["mean"]["contrasts"])
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), layout="constrained", sharey=True)
    for ax, metric, scale, label in zip(
        axes,
        ("timely_recall", "false_plus_late_per_match"),
        (100, 1),
        (
            "Macro recall difference (percentage points)",
            "Extra false + late warnings / match / event",
        ),
        strict=True,
    ):
        v = [
            results["overall"]["30"]["matched_early_mixture"]["mean"]["contrasts"][k]["macro"][
                metric
            ]
            for k in contrasts
        ]
        x = np.array([a["mean"] for a in v]) * scale
        ci = np.array([a["ci95"] for a in v]) * scale
        ax.errorbar(
            x,
            np.arange(len(x)),
            xerr=np.stack((x - ci[:, 0], ci[:, 1] - x)),
            fmt="o",
            capsize=3,
            color="#237b81",
        )
        ax.axvline(0, color="#444444", lw=0.8, ls="--")
        ax.set_xlabel(label)
        ax.grid(alpha=0.15)
    axes[0].set_yticks(
        np.arange(len(contrasts)),
        [x.replace("-minus-", " - ").replace("current_only", "current-only") for x in contrasts],
    )
    axes[0].invert_yaxis()
    fig.suptitle(
        "Primary warning efficiency: four fixed budgets, exact EARLY cost\n"
        "Paired match intervals conditional on three fitted seeds and selected policies",
        fontsize=12,
    )
    fig.savefig(folder / "mechanism-contrasts.svg", metadata={"Date": None})
    fig.savefig(folder / "mechanism-contrasts.png", dpi=170)
    plt.close(fig)
    for name in ("pcgrad-budget-curves.svg", "mechanism-contrasts.svg"):
        path = folder / name
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plots", action="store_true")
    args = parser.parse_args()
    render(args.output, args.plots)
