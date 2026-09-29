"""Publication-style local figure for the audited follow-up denominator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def render(source: Path, output: Path) -> None:
    report = json.loads(source.read_text())
    if (
        report.get("schema_version") != "league-ews-confirmed-followup-audit-v1"
        or report.get("identifiers_in_report") is not False
        or report.get("test_matches_unread") != 6000
        or report.get("horizons_seconds") != [10, 20, 30, 60]
    ):
        raise ValueError("The figure requires a complete identifier-free follow-up audit")
    partitions = report["partitions"]
    if set(partitions) != {"train", "calibration"}:
        raise ValueError("Follow-up partitions differ from the sealed split")
    colors = {"baron": "#F2B66D", "dragon": "#79D0BE", "teamfight": "#A7A9F2"}
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 4.9), layout="constrained")
    fig.patch.set_facecolor("#101923")
    for axes in (ax, ax2):
        axes.set_facecolor("#152230")
        axes.spines[["top", "right"]].set_visible(False)
        axes.spines[["bottom", "left"]].set_color("#748292")
        axes.tick_params(colors="#DCE6EC")
        axes.grid(axis="y", color="#576473", alpha=0.25)
        axes.set_axisbelow(True)
    x = np.arange(4)
    for event_index, event in enumerate(colors):
        for partition, style, marker in (("train", "-", "o"), ("calibration", "--", "s")):
            row = partitions[partition]
            percentages = []
            for horizon_index in range(4):
                index = 4 * event_index + horizon_index
                censored = row["negative_labels_without_full_followup"][index]
                followed = row["fully_followed_negative_labels"][index]
                percentages.append(100 * censored / (censored + followed))
            ax.plot(
                x, percentages, linestyle=style, marker=marker, linewidth=2,
                markersize=5, color=colors[event], label=f"{event.title()} · {partition}",
            )
    ax.set_xticks(x, ["10", "20", "30", "60"])
    ax.set_xlabel("Forecast horizon (seconds)", color="#DCE6EC")
    ax.set_ylabel("Negative rows without full follow-up (%)", color="#DCE6EC")
    ax.set_title("How much of the negative tail is unverified?", color="white", loc="left")
    ax.legend(ncol=2, fontsize=8, facecolor="#152230", labelcolor="white", edgecolor="#576473")

    names = ("Training", "Calibration")
    original = np.array(
        [partitions[key]["original_loss_bins"] for key in ("train", "calibration")]
    )
    confirmed = np.array(
        [partitions[key]["confirmed_loss_bins"] for key in ("train", "calibration")]
    )
    i = np.arange(2)
    ax2.bar(i - 0.18, original / 1_000_000, width=0.34, color="#A7A9F2", label="Original")
    ax2.bar(i + 0.18, confirmed / 1_000_000, width=0.34, color="#79D0BE", label="Confirmed")
    ax2.set_xticks(i, names)
    ax2.set_ylabel("At-risk event bins (millions)", color="#DCE6EC")
    ax2.set_title("Hazard loss exposure", color="white", loc="left")
    ax2.legend(facecolor="#152230", labelcolor="white", edgecolor="#576473")
    for position, (before, after) in enumerate(zip(original, confirmed, strict=True)):
        ax2.text(
            position, max(before, after) / 1_000_000 + 0.03,
            f"{100 * (before - after) / before:.1f}% censored",
            ha="center", color="white", fontsize=9,
        )
    fig.suptitle("Confirmed follow-up at genuine Riot frames", color="white", fontsize=17)
    fig.text(
        0.5, -0.03,
        "Exploratory train/calibration audit · duration ∩ final frame · sealed test unread",
        ha="center", color="#B9C6D1", fontsize=9,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    render(options.input, options.output)
