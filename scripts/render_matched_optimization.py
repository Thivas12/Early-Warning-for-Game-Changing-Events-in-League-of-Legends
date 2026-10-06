"""Render all matched-architecture comparisons without selecting favorable cells."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from scripts.evaluate_matched_optimization import FAMILIES, POLICIES
from scripts.render_timely_neural import contrast_row
from scripts.render_warning_efficiency import compact_aggregate_json
from scripts.warning_efficiency import BUDGETS

EVENTS = ("baron", "dragon", "teamfight", "macro")
PRIMARY = "timely_equal_sum-minus-timely_equal_tcn"
GRU = "timely_equal_sum-minus-timely_equal_gru"
ORIGINAL_TCN = "timely_leagueews-minus-timely_tcn"
ORIGINAL_GRU = "timely_leagueews-minus-timely_original_gru"
TCN_INTERACTION = "leagueews_tcn_by_weighting_interaction"
GRU_INTERACTION = "leagueews_gru_by_weighting_interaction"
MECHANISMS = (PRIMARY, GRU, ORIGINAL_TCN, ORIGINAL_GRU, TCN_INTERACTION, GRU_INTERACTION)


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
        "# Matched useful-lead architecture evidence",
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
        lines += [
            "",
            "### Matched architecture effects and weighting interactions by event",
            "",
            *header,
        ]
        for name in MECHANISMS:
            for event in EVENTS:
                lines.append(contrast_row(f"{name}: {event}", group["contrasts"][name][event]))
        for policy in POLICIES:
            lines += [
                "",
                f"### Primary equal-weight LeagueEWS minus TCN: {policy}",
                "",
                *header,
            ]
            for budget in (*BUDGETS, "mean"):
                value = results["overall"][h][policy][str(budget)]["contrasts"][PRIMARY]["macro"]
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
    lines.extend(
        f"| {k} | {v} |"
        for k, v in data["frozen_rules"].items()
        if k != "regional_hard_one_violations"
    )
    lines += [
        "",
        "## Hard-one burden violations",
        "",
        "Counts are event/region/seed/budget cells out of 72 for each row. "
        "Every one of the four budgets is included; nominal-budget violations are retained in CSV.",
        "",
        "| Family / window | " + " | ".join(POLICIES) + " |",
        "|---|" + "---:|" * len(POLICIES),
    ]
    for family, horizons in data["frozen_rules"]["regional_hard_one_violations"].items():
        for h, policies in horizons.items():
            window = "10-30" if h == "30" else "20-60"
            lines.append(
                f"| {family} / {window} | " + " | ".join(str(policies[p]) for p in POLICIES) + " |"
            )
    lines += [
        "",
        "All model/event/region/seed results and paired intervals are retained in "
        "`analysis.json`, `aggregate-counts.csv`, `by-seed.csv` and `budget-violations.csv`. "
        "Neither a diagnostic pass nor an optimizer change establishes novelty or a causal "
        "effect of game actions. Previously failed regional gates remain failed.",
        "",
    ]
    (folder / "tables.md").write_text("\n".join(lines))
    with (folder / "budget-violations.csv").open("w") as stream:
        writer = csv.DictWriter(
            stream,
            lineterminator="\n",
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
        {"font.size": 10, "svg.fonttype": "none", "svg.hashsalt": "league-matched-optimization-v1"}
    )
    panels = (
        (
            "LeagueEWS minus TCN",
            (
                (ORIGINAL_TCN, "Original weights", "#237b81"),
                (PRIMARY, "Equal weights", "#b26b20"),
            ),
        ),
        (
            "LeagueEWS minus GRU",
            (
                (ORIGINAL_GRU, "Original weights", "#237b81"),
                (GRU, "Equal weights", "#b26b20"),
            ),
        ),
        (
            "Architecture-by-weighting interaction",
            (
                (TCN_INTERACTION, "Against TCN", "#7544a4"),
                (GRU_INTERACTION, "Against GRU", "#3970af"),
            ),
        ),
    )
    for metric, scale, xlabel, filename in (
        ("timely_recall", 100, "Recall difference (percentage points)", "architecture-recall"),
        (
            "false_plus_late_per_match",
            1,
            "False + late difference / match / event",
            "architecture-burden",
        ),
    ):
        fig, axes = plt.subplots(2, 3, figsize=(16, 9), layout="constrained")
        for row, h in enumerate(("30", "60")):
            values = results["overall"][h]["matched_early_mixture"]["mean"]["contrasts"]
            for col, (title, comparisons) in enumerate(panels):
                ax = axes[row, col]
                for offset, (name, label, color) in zip((-0.12, 0.12), comparisons, strict=True):
                    point = np.array([values[name][e][metric]["mean"] for e in EVENTS]) * scale
                    ci = np.array([values[name][e][metric]["ci95"] for e in EVENTS]) * scale
                    ax.errorbar(
                        point,
                        np.arange(4) + offset,
                        xerr=np.stack((point - ci[:, 0], ci[:, 1] - point)),
                        fmt="o",
                        capsize=3,
                        label=label,
                        color=color,
                    )
                ax.axvline(0, color="#444444", lw=0.8, ls="--")
                ax.set_yticks(np.arange(4), EVENTS)
                ax.invert_yaxis()
                ax.set_xlabel(xlabel)
                window = "10-30" if h == "30" else "20-60"
                ax.set_title(f"{title}\n{window}-second warnings")
                ax.grid(alpha=0.15)
                if row == 0:
                    ax.legend(fontsize=8)
        fig.suptitle("LeagueEWS: matched useful-lead architecture controls", fontsize=14)
        fig.savefig(folder / f"{filename}.svg", metadata={"Date": None})
        fig.savefig(folder / f"{filename}.png", dpi=170)
        plt.close(fig)
        path = folder / f"{filename}.svg"
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plots", action="store_true")
    args = parser.parse_args()
    render(args.output, args.plots)
