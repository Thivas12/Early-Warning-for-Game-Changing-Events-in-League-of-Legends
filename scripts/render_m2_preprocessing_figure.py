"""Render identifier-free position-coverage diagnostics as a static figure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

EVENT_LABELS = ("y_baron_60", "y_dragon_60", "y_teamfight_60")
GROUPS = ("No positions", "Partial", "All ten")
COLORS = {"train": "#226C92", "calibration": "#DB7458"}


def render(source: Path, output: Path) -> None:
    report = json.loads(source.read_bytes())
    if (
        report.get("schema_version") != "league-ews-m2-preprocessing-audit-v1"
        or report.get("identifiers_in_report") is not False
        or report.get("test_matches_unread") != 6000
        or set(report.get("partitions", {})) != {"train", "calibration"}
    ):
        raise ValueError("The figure requires an identifier-free, train/calibration M2 audit")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none"})
    fig = plt.figure(figsize=(12.4, 5.6), facecolor="#F7F7F3")
    gs = fig.add_gridspec(1, 2, left=0.075, right=0.88, bottom=0.2, top=0.69, wspace=0.36)
    left, right = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    for axis in (left, right):
        axis.set_facecolor("#F7F7F3")
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_color("#B9C3C6")
        axis.grid(axis="y", color="#DDE3E0", linewidth=0.8, zorder=0)
        axis.set_axisbelow(True)
        axis.tick_params(length=0, pad=7, colors="#263B45")

    fig.text(
        0.075,
        0.96,
        "RIFTHAZARD / PREPROCESSING ATLAS",
        fontsize=10,
        color="#54717E",
        weight="bold",
    )
    fig.text(
        0.075,
        0.875,
        "What do the recorded positions actually cover?",
        fontsize=20,
        color="#183542",
        weight="bold",
    )
    fig.text(
        0.075,
        0.805,
        "Real prediction frames · patches 16.12-16.16 · test patch unread",
        fontsize=10,
        color="#54717E",
    )

    x = np.arange(3)
    for i, partition in enumerate(("train", "calibration")):
        block = report["partitions"][partition]
        counts = np.asarray(block["position_count_rows"], dtype=np.float64)
        if counts.shape != (11,) or int(counts.sum()) != block["rows"] or block["rows"] < 1:
            raise ValueError("Position strata disagree with audited row inventory")
        grouped = np.array([counts[0], counts[1:10].sum(), counts[10]])
        left.bar(
            x + (i - 0.5) * 0.34,
            grouped / counts.sum() * 100,
            width=0.31,
            color=COLORS[partition],
            label=partition.title(),
            zorder=3,
        )
    left.set_xticks(x, GROUPS)
    left.set_ylabel("Prediction frames (%)", color="#263B45")
    left.set_ylim(bottom=0)
    left.set_title(
        "01  Observed participant positions",
        loc="left",
        fontsize=12,
        color="#183542",
        weight="bold",
        pad=14,
    )
    left.legend(frameon=False, loc="upper left", fontsize=9)

    offsets = {"train": -0.08, "calibration": 0.08}
    symbols = {"train": "o", "calibration": "s"}
    for event_number, label in enumerate(EVENT_LABELS):
        for partition in ("train", "calibration"):
            block = report["partitions"][partition]
            counts = np.asarray(block["position_count_rows"], dtype=np.float64)
            positives = np.asarray(block["position_count_positive_rows"][label], dtype=np.float64)
            if positives.shape != (11,) or np.any(positives > counts):
                raise ValueError("Target counts exceed the audited position strata")
            grouped_n = np.array([counts[0], counts[1:10].sum(), counts[10]])
            grouped_y = np.array([positives[0], positives[1:10].sum(), positives[10]])
            valid = grouped_n > 0
            rates = np.divide(grouped_y, grouped_n, out=np.zeros(3), where=valid) * 100
            y = event_number * 4 + np.arange(3) + offsets[partition]
            right.scatter(
                rates[valid],
                y[valid],
                s=57,
                marker=symbols[partition],
                color=COLORS[partition],
                edgecolor="white",
                linewidth=0.8,
                zorder=4,
            )
    right.set_yticks(
        np.concatenate([np.arange(3), np.arange(4, 7), np.arange(8, 11)]),
        list(GROUPS) * 3,
    )
    right.invert_yaxis()
    right.set_xlabel("60-second positive rows within coverage stratum (%)", color="#263B45")
    right.set_title(
        "02  Event labels by coverage",
        loc="left",
        fontsize=12,
        color="#183542",
        weight="bold",
        pad=14,
    )
    for boundary in (3, 7):
        right.axhline(boundary - 0.5, color="#B9C3C6", linewidth=0.8)
    for center, event in ((1, "BARON"), (5, "DRAGON"), (9, "TEAMFIGHT")):
        right.text(
            1.01,
            center,
            event,
            va="center",
            transform=right.get_yaxis_transform(),
            color="#54717E",
            fontsize=8,
            weight="bold",
        )
    right.set_xlim(left=0)
    fig.text(
        0.075,
        0.073,
        "Association across observed frames; match phase and missingness may confound it. "
        "No synthetic frames or player IDs.",
        fontsize=9,
        color="#54717E",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(args.input, args.output)
    print(f"Rendered identifier-free position audit: {args.output}")
