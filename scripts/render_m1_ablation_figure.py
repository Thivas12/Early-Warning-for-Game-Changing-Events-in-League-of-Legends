"""Render the identifier-free M1 graph ablation calibration comparison."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["svg.fonttype"] = "none"


def main() -> None:
    source = Path("reports/m1-graph-ablation-calibration-2026-09-28.json")
    output = Path("reports/figures/m1-graph-ablation-calibration.svg")
    data = json.loads(source.read_text())
    if (
        data.get("schema_version") != "league-ews-m1-graph-ablation-calibration-transcription-v1"
        or data.get("partition") != "calibration"
        or data.get("matches") != 6000
        or data.get("seed_count") != 10
        or data.get("test_matches_unread") != 6000
        or set(data.get("variants", {}))
        != {
            "no-objective-nodes",
            "no-positions-or-proximity",
            "no-interaction-edges",
            "no-assistance-history",
        }
    ):
        raise ValueError("Figure source differs from the audited aggregate transcription")

    labels = [
        "Without objective nodes",
        "Original M1",
        "Without interaction edges",
        "Without assistance history",
        "B3 tabular reference",
        "Without positions or proximity",
    ]
    variants = data["variants"]
    records = [
        variants["no-objective-nodes"],
        data["m1"],
        variants["no-interaction-edges"],
        variants["no-assistance-history"],
        None,
        variants["no-positions-or-proximity"],
    ]
    means = [record["mean"] if record is not None else data["b3"] for record in records]
    if any(
        record is not None
        and not (0 <= record["minimum"] <= record["mean"] <= record["maximum"] <= 1)
        for record in records
    ):
        raise ValueError("Seed range does not contain its mean")

    background, foreground = "#101724", "#EDF4F8"
    muted, grid = "#A9BCCC", "#31465A"
    accents = ["#41D6B0", "#54B5F4", "#B29CF5", "#D0A3EC", "#A9BCCC", "#F4A78A"]
    fig, ax = plt.subplots(figsize=(10.2, 5.25), dpi=160)
    fig.patch.set_facecolor(background)
    ax.set_facecolor(background)
    y = np.arange(len(labels))[::-1]
    ax.set_xlim(0.0, 0.60)
    ax.set_ylim(-0.8, len(labels) - 0.25)
    ax.set_xticks(np.arange(0, 0.61, 0.1))
    ax.set_xticklabels([f"{tick:.1f}" for tick in np.arange(0, 0.61, 0.1)], color=muted)
    ax.set_yticks(y, labels=labels, color=foreground, fontsize=10.5)
    ax.tick_params(axis="both", length=0, pad=10)
    ax.grid(axis="x", color=grid, linewidth=0.8, alpha=0.65)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for row, mean, record, color in zip(y, means, records, accents, strict=True):
        ax.plot([0, mean], [row, row], color=color, alpha=0.44, linewidth=5, solid_capstyle="round")
        if record is not None:
            ax.plot(
                [record["minimum"], record["maximum"]],
                [row, row],
                color=color,
                linewidth=9,
                solid_capstyle="round",
            )
        ax.scatter(
            [mean], [row], color=color, edgecolors=background, s=92, linewidths=1.5, zorder=3
        )
        ax.text(
            min(mean + 0.022, 0.59),
            row,
            f"{mean:.3f}",
            va="center",
            ha="left",
            color=foreground,
            fontsize=10,
            fontweight="semibold",
        )
    ax.set_xlabel("Macro average precision · 12 event/horizon targets", color=muted, labelpad=17)
    fig.suptitle(
        "Which graph inputs help the warning model?",
        x=0.08,
        ha="left",
        y=0.965,
        fontsize=17,
        fontweight="bold",
        color=foreground,
    )
    fig.text(
        0.08,
        0.89,
        "Patch 16.16 calibration  ·  6,000 matches  ·  10 seeds per M1 variant",
        color=muted,
        fontsize=10,
    )
    fig.text(
        0.08,
        0.025,
        "Dot = seed mean   •   Thick segment = observed seed range   •   B3 = single reference",
        color=muted,
        fontsize=9,
    )
    fig.subplots_adjust(left=0.31, right=0.96, top=0.82, bottom=0.20)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, facecolor=background)
    # Matplotlib writes insignificant trailing spaces in multiline path data.
    output.write_text("\n".join(line.rstrip() for line in output.read_text().splitlines()) + "\n")
    fig.savefig(output.with_suffix(".png"), facecolor=background, dpi=180)
    plt.close(fig)
    print(f"Rendered {output}")


if __name__ == "__main__":
    main()
