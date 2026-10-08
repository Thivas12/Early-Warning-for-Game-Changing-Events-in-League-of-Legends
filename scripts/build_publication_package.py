"""Build source-linked research figures, a paper PDF and a two-page project brief."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import quote

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/publication-package-2026-10-07"
PAPER = ROOT / "paper/leagueews-2026-10"
REMOTE = (
    "https://github.com/Thivas12/"
    "Early-Warning-for-Game-Changing-Events-in-League-of-Legends/"
    "blob/research/league-publication-package-20261007/"
)
INK, TEAL, RUST, GREY = "#162b37", "#087e83", "#ac492f", "#647680"
EFFECTS = (
    (
        "Past state beyond current state and timers",
        "clock-history-2026-10-04",
        "timely_leagueews-minus-timely_clock_history",
    ),
    (
        "Useful-lead targets, same hybrid",
        "timely-neural-2026-10-03",
        "timely_leagueews-minus-leagueews",
    ),
    (
        "Joint minus independent event encoders",
        "timely-sharing-2026-10-05",
        "timely_leagueews-minus-timely_independent",
    ),
    (
        "Equal-weight hybrid minus equal-weight TCN",
        "matched-optimization-2026-10-06",
        "timely_equal_sum-minus-timely_equal_tcn",
    ),
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_evidence():
    records, sources = [], {}
    for label, study, contrast in EFFECTS:
        path = ROOT / "reports" / study / "analysis.json"
        source = json.loads(path.read_bytes())
        relative = str(path.relative_to(ROOT))
        sources[relative] = digest(path)
        for horizon in (30, 60):
            pointer = [
                "results",
                "overall",
                str(horizon),
                "matched_early_mixture",
                "mean",
                "contrasts",
                contrast,
                "macro",
                "timely_recall",
            ]
            value = source
            for key in pointer:
                value = value[key]
            records.append(
                {
                    "label": label,
                    "horizon": horizon,
                    "source": relative,
                    "json_pointer": "/" + "/".join(pointer),
                    "recall_difference_pp": 100 * value["mean"],
                    "ci95_pp": [100 * x for x in value["ci95"]],
                    "seeds_pp": [100 * x for x in value["seeds"]],
                }
            )
    result = {
        "schema": "league-publication-evidence-v1",
        "new_empirical_analysis": False,
        "interpretation": (
            "Selected completed contrasts under four-budget matched-early averaging. "
            "Different controlled changes; not additive, a model ranking or a meta-analysis. "
            "Pointwise conditional 95% intervals; adaptive development, not confirmation."
        ),
        "source_sha256": sources,
        "effects": records,
    }
    (OUT / "evidence.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def figures(evidence, runtime):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelcolor": INK,
            "text.color": INK,
            "svg.hashsalt": "league-publication-20261007",
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.0))
    for ax, horizon in zip(axes, (30, 60), strict=True):
        rows = [r for r in evidence["effects"] if r["horizon"] == horizon]
        for i, row in enumerate(rows):
            point, (low, high) = row["recall_difference_pp"], row["ci95_pp"]
            color = TEAL if point >= 0 else RUST
            ax.errorbar(
                point,
                3 - i,
                xerr=[[point - low], [high - point]],
                fmt="o",
                color=color,
                capsize=4,
                linewidth=2,
                markersize=7,
            )
            ax.text(
                0.02,
                3 - i + 0.28,
                f"{point:+.3f} [{low:+.3f}, {high:+.3f}]",
                transform=ax.get_yaxis_transform(),
                fontsize=8,
                color=color,
            )
        ax.axvline(0, color=GREY, linewidth=1, linestyle="--")
        ax.set_ylim(-0.7, 3.7)
        ax.set_yticks(range(4), [r["label"] for r in rows[::-1]] if horizon == 30 else [""] * 4)
        ax.tick_params(axis="y", length=0, pad=10)
        ax.set_title(
            "10-30 seconds of lead" if horizon == 30 else "20-60 seconds of lead",
            loc="left",
            fontweight="bold",
            pad=14,
        )
        ax.set_xlabel("Macro recall difference (percentage points)")
        ax.grid(axis="x", alpha=0.15)
    fig.suptitle(
        "Which explanations survive controlled comparison?",
        x=0.025,
        ha="left",
        fontsize=17,
        fontweight="bold",
    )
    fig.subplots_adjust(left=0.36, right=0.98, top=0.82, bottom=0.16, wspace=0.2)
    fig.text(
        0.025,
        0.025,
        "Exploratory development • conditional intervals • different recipes and "
        "contrasts, not additive effects",
        fontsize=9,
        color=GREY,
    )
    save_figure(fig, "evidence-overview")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    for ax, device in zip(axes, ("cpu", "cuda"), strict=True):
        for j, architecture in enumerate(("tcn", "leagueews")):
            for k, batch in enumerate((1, 128)):
                values = [
                    r["median_ms"]
                    for r in runtime["records"]
                    if r["architecture"] == architecture
                    and r["device"] == device
                    and r["batch"] == batch
                ]
                x = k + (j - 0.5) * 0.28
                ax.scatter(
                    [x] * 3,
                    values,
                    color=TEAL if j == 0 else RUST,
                    label=architecture.upper() if k == 0 else None,
                    s=30,
                )
                ax.plot(
                    [x - 0.07, x + 0.07],
                    [np.median(values)] * 2,
                    color=TEAL if j == 0 else RUST,
                    linewidth=2,
                )
        ax.set_yscale("log")
        ax.set_xticks([0, 1], ["Batch 1", "Batch 128"])
        ax.set_xlim(-0.5, 1.5)
        ax.set_title(device.upper(), loc="left", fontweight="bold")
        ax.set_ylabel("Median forward + sigmoid time (ms, log scale)")
        ax.grid(axis="y", alpha=0.15)
        ax.legend(frameon=False)
    fig.suptitle(
        "Measured cost of the saved architectures",
        x=0.06,
        ha="left",
        fontsize=17,
        fontweight="bold",
    )
    fig.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.22, wspace=0.38)
    fig.text(
        0.06,
        0.045,
        "Three fitted seeds per cell • resident training inputs • IEEE float32 • "
        "one RTX 4060 laptop\nCPU: 2 threads. Excludes data preparation, transfers and serving. "
        "Points are repeated timing summaries, not confidence intervals.",
        fontsize=8,
        color=GREY,
    )
    save_figure(fig, "runtime-overview")


def save_figure(fig, name):
    for suffix in ("png", "svg", "pdf"):
        fig.savefig(OUT / f"{name}.{suffix}", dpi=180, facecolor="white")
    svg = OUT / f"{name}.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    plt.close(fig)


def setup_styles():
    fonts = Path(matplotlib.get_data_path()) / "fonts/ttf"
    for name, filename in (
        ("Research", "DejaVuSans.ttf"),
        ("Research-Bold", "DejaVuSans-Bold.ttf"),
        ("Research-Italic", "DejaVuSans-Oblique.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))
    pdfmetrics.registerFontFamily(
        "Research",
        normal="Research",
        bold="Research-Bold",
        italic="Research-Italic",
        boldItalic="Research-Bold",
    )
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = "Research"
        style.textColor = colors.HexColor(INK)
    styles["BodyText"].fontSize = 9.1
    styles["BodyText"].leading = 13.1
    styles["BodyText"].spaceAfter = 7
    styles["Title"].fontSize = 22
    styles["Title"].leading = 27
    styles["Title"].alignment = TA_LEFT
    styles["Title"].fontName = "Research-Bold"
    styles["Title"].spaceAfter = 14
    for name, size in (("Heading1", 14), ("Heading2", 11)):
        styles[name].fontName = "Research-Bold"
        styles[name].fontSize = size
        styles[name].leading = size + 4
        styles[name].spaceBefore = 11
        styles[name].spaceAfter = 6
    styles.add(ParagraphStyle("Small", parent=styles["BodyText"], fontSize=7.4, leading=10))
    styles.add(
        ParagraphStyle(
            "Kicker",
            parent=styles["BodyText"],
            fontSize=9,
            textColor=colors.HexColor(TEAL),
            spaceAfter=10,
        )
    )
    return styles


def inline(text, directory):
    saved = []

    def link(match):
        label, target = match.groups()
        if not target.startswith("https://"):
            target = REMOTE + quote(str((directory / target).resolve().relative_to(ROOT)), safe="/")
        saved.append(
            f'<link href="{html.escape(target, quote=True)}" color="{TEAL}">'
            f"{html.escape(label)}</link>"
        )
        return f"ZZLINK{len(saved) - 1}ZZ"

    text = re.sub(r"\[([^]]+)\]\(([^)]+)\)", link, text)
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    for i, value in enumerate(saved):
        text = text.replace(f"ZZLINK{i}ZZ", value)
    return text


def table(rows, styles, widths=None):
    formatted = [[Paragraph(cell, styles["Small"]) for cell in row] for row in rows]
    widths = widths or [470 / len(rows[0])] * len(rows[0])
    obj = Table(formatted, colWidths=widths, repeatRows=1, hAlign="LEFT")
    obj.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f2f2")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor(TEAL)),
                ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#d9e1e5")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return obj


def markdown_story(path, styles):
    lines, story = path.read_text().splitlines(), []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            style = "Title" if level == 1 else "Heading1" if level == 2 else "Heading2"
            story.append(Paragraph(inline(line[level:].strip(), path.parent), styles[style]))
            if level == 1:
                story.append(
                    Paragraph(
                        "Keerthivasan Kannan · LeagueEWS Research · Working paper", styles["Kicker"]
                    )
                )
            i += 1
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [x.strip() for x in lines[i].strip("|").split("|")]
                if not all(re.fullmatch(r"[-:]+", x) for x in cells):
                    rows.append([inline(x, path.parent) for x in cells])
                i += 1
            story.extend([table(rows, styles), Spacer(1, 9)])
        else:
            paragraph = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|")):
                paragraph.append(lines[i])
                i += 1
            story.append(Paragraph(inline(" ".join(paragraph), path.parent), styles["BodyText"]))
    return story


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d9e1e5"))
    canvas.line(52, 42, 543, 42)
    canvas.setFont("Research", 7)
    canvas.setFillColor(colors.HexColor(GREY))
    canvas.drawString(52, 28, "LeagueEWS · Exploratory research · 7 October 2026")
    canvas.drawRightString(543, 28, str(doc.page))
    canvas.restoreState()


def pdf(path, story, title):
    SimpleDocTemplate(
        str(path),
        pagesize=(595.28, 841.89),
        rightMargin=60,
        leftMargin=60,
        topMargin=48,
        bottomMargin=57,
        title=title,
        author="Keerthivasan Kannan",
    ).build(story, onFirstPage=footer, onLaterPages=footer)


def runtime_rows(runtime, batch=1):
    rows = [["Device / batch", "Model", "Median across seeds (ms)", "Seed median range (ms)"]]
    for device in ("cpu", "cuda"):
        for architecture in ("tcn", "leagueews"):
            values = [
                r["median_ms"]
                for r in runtime["records"]
                if r["device"] == device
                and r["architecture"] == architecture
                and r["batch"] == batch
            ]
            rows.append(
                [
                    f"{device.upper()} / {batch}",
                    architecture.upper(),
                    f"{np.median(values):.3f}",
                    f"{min(values):.3f}-{max(values):.3f}",
                ]
            )
    return rows


def documents(runtime, styles):
    source = ROOT / "docs/leagueews-paper-draft.md"
    story = markdown_story(source, styles)
    story.extend(
        [
            PageBreak(),
            Paragraph("Appendix A. Visual evidence and inference cost", styles["Heading1"]),
            Image(str(OUT / "evidence-overview.png"), width=475, height=207),
            Paragraph(
                "Figure A1. Exact completed-study estimates extracted from the "
                "source analysis JSON. Each row represents a different controlled "
                "comparison; effects are not additive. Intervals condition on fixed "
                "fits and policies and omit adaptive-search uncertainty.",
                styles["Small"],
            ),
            Image(str(OUT / "runtime-overview.png"), width=475, height=214),
        ]
    )
    story.extend([PageBreak(), Paragraph("Appendix B. Saved-model runtime", styles["Heading1"])])
    for batch in (1, 128):
        story.extend([table(runtime_rows(runtime, batch), styles), Spacer(1, 8)])
    story.append(
        Paragraph(
            "The runtime study reuses six saved fits and training inputs only. "
            "Each cell has 20 warmup "
            "and 100 measured forward-plus-sigmoid calls. CPU uses two threads; CUDA uses the "
            "RTX 4060 Laptop GPU. Inputs are resident and IEEE float32 is explicit. "
            "Loading, feature "
            "construction, transfers, output conversion and policy execution are excluded. All six "
            "CPU/CUDA output checks passed their fixed tolerances after disabling cuDNN TF32. "
            "The aborted first run and precision amendment are preserved. Timings do not establish "
            "service latency or production readiness; power, temperature and background load were "
            "not controlled.",
            styles["BodyText"],
        )
    )
    story.append(
        Paragraph(
            inline(
                "[Protocol and precision amendment](../reports/publication-package-2026-10-07/"
                "runtime-protocol-v2.md) · [All timings and checkpoint hashes](../reports/"
                "publication-package-2026-10-07/runtime.json) · "
                "[AI-use disclosure](ai-usage.md)",
                ROOT / "docs",
            ),
            styles["Small"],
        )
    )
    story.append(Paragraph("References", styles["Heading1"]))
    references = [
        (
            "Yang, Z., et al. (2022). Predicting Events in MOBA Games: Prediction, Attribution, "
            "and Evaluation. IEEE Transactions on Games. doi:10.1109/TG.2022.3159704.",
            "https://arxiv.org/abs/2012.09424",
        ),
        (
            "Vardakis, M., et al. (2026). Prediction of MOBA game events based on In-Game Data. "
            "Entertainment Computing, 57, 101091. doi:10.1016/j.entcom.2026.101091. "
            "Publisher abstract reviewed; full-text comparison remains pending.",
            "https://www.sciencedirect.com/science/article/pii/S1875952126000133",
        ),
        (
            "Yèche, H., Burger, M., Veshchezerova, D., and Ratsch, G. (2024). Dynamic Survival "
            "Analysis for Early Event Prediction. Proceedings of CHIL, PMLR 248, 540-557.",
            "https://proceedings.mlr.press/v248/yeche24a.html",
        ),
        (
            "Angelopoulos, A. N., Bates, S., Candès, E. J., Jordan, M. I., and Lei, L. (2022). "
            "Learn then Test: Calibrating Predictive Algorithms to Achieve Risk Control. "
            "arXiv:2110.01052v5. Version pinned for the risk-control assumptions.",
            "https://arxiv.org/pdf/2110.01052v5",
        ),
    ]
    for citation, url in references:
        story.append(
            Paragraph(
                html.escape(citation) + f' <link href="{url}" color="{TEAL}">Primary source</link>',
                styles["Small"],
            )
        )
    PAPER.mkdir(parents=True, exist_ok=True)
    pdf(
        PAPER / "leagueews-working-paper.pdf", story, "LeagueEWS: controlled early-warning research"
    )

    p = lambda text, style="BodyText": Paragraph(text, styles[style])  # noqa: E731
    brief = [
        p("APPLIED ML / RESEARCH ENGINEERING", "Kicker"),
        p("LeagueEWS<br/>Making early-warning claims testable", "Title"),
        p("Keerthivasan Kannan · PyTorch · temporal models · causal evaluation", "Kicker"),
        p(
            "An end-to-end investigation of Baron, Dragon and teamfight warnings in League "
            "of Legends: recover a legacy model, audit leakage, rebuild causal inputs, run "
            "controlled GPU experiments and measure the cost of useful alerts."
        ),
        table(
            [
                ["30,000", "69", "3"],
                ["development matches", "preserved neural fits", "event types / fitted seeds"],
            ],
            styles,
        ),
        Spacer(1, 12),
        p("The result", "Heading1"),
        p(
            "History helps selectively. Shared learning creates task tradeoffs. "
            "The hybrid's margin over a strong TCN is small. Meeting an observed alert "
            "budget costs recall. The project measures these distinctions rather than "
            "relying on the original, contaminated AUC scores."
        ),
        Image(str(OUT / "evidence-overview.png"), width=475, height=207),
        p(
            "The figure uses four-budget matched-early operating comparisons. Recall changes "
            "are percentage points; the pointwise intervals are conditional on fixed models "
            "and policies. All findings are exploratory. No fresh-patch superiority or "
            "new-method claim is established.",
            "Small",
        ),
        p(
            f'<link href="{REMOTE}docs/leagueews-paper-draft.md" color="{TEAL}">'
            "Read the paper</link>"
            f' · <link href="{REMOTE}reports/publication-package-2026-10-07/evidence.json" '
            f'color="{TEAL}">Inspect the exact estimates</link>',
            "Small",
        ),
        PageBreak(),
        p("ENGINEERING EVIDENCE", "Kicker"),
        p("From notebook to auditable experiments", "Title"),
    ]
    for title, body in (
        (
            "Data correctness",
            "Whole-match chronological splits, training-only normalization, "
            "native observations and explicit feature availability; objective-completion labels "
            "are not misrepresented as engagement onset.",
        ),
        (
            "Reliable execution",
            "Checkpointed GPU training, optimizer/RNG resume, source/data "
            "hashes, committed scoring releases and complete seed inventories.",
        ),
        (
            "Independent verification",
            "The latest policy study records 740 passing tests and "
            "810,000 full scalar replay checks, with exact prior-result reproduction. These are "
            "implementation checks, not additional scientific replications.",
        ),
        (
            "Model judgment",
            "The equal-weight hybrid uses 1.75M parameters versus TCN's 0.56M. "
            "Its +0.242-point short-lead recall margin is reported with regional uncertainty "
            "and unequal capacity, instead of being presented as broad superiority.",
        ),
    ):
        brief.append(KeepTogether([p(title, "Heading2"), p(body)]))
    brief.extend(
        [
            p("Measured inference cost", "Heading2"),
            table(runtime_rows(runtime), styles),
            Spacer(1, 6),
            p(
                "Six saved fits; resident training inputs; explicit float32; "
                "100 measured calls per cell. Values summarize the three seed-specific medians. "
                "CPU: two threads. GPU: RTX 4060 Laptop. Excludes loading, transfers and serving. "
                "The full record includes batch 128, p95, all raw timings and numerical checks.",
                "Small",
            ),
            p("Publication boundary", "Heading2"),
            p(
                "Working paper, not an accepted publication. The completed evidence supports "
                "an exploratory empirical contribution. Fresh confirmation and final literature "
                "review remain outstanding; the reserved test is unopened."
            ),
            p(
                "AI assistance is disclosed. Project ownership and original notebooks belong "
                "to Keerthivasan Kannan; implementation, analysis and writing received material "
                "Codex assistance. Human submission review is pending.",
                "Small",
            ),
        ]
    )
    pdf(OUT / "leagueews-project-brief.pdf", brief, "LeagueEWS project brief — Keerthivasan Kannan")
    assert len(PdfReader(OUT / "leagueews-project-brief.pdf").pages) == 2, "Brief must be two pages"


def run(args):
    OUT.mkdir(parents=True, exist_ok=True)
    runtime = json.loads(args.runtime.read_bytes())
    assert runtime["status"] == "complete-system-microbenchmark"
    assert len(runtime["records"]) == 24
    assert runtime["test_payloads_opened"] == runtime["new_outcome_evaluations"] == 0
    (OUT / "runtime.json").write_text(json.dumps(runtime, indent=2) + "\n")
    evidence = extract_evidence()
    figures(evidence, runtime)
    documents(runtime, setup_styles())
    pdfs = [OUT / "leagueews-project-brief.pdf", PAPER / "leagueews-working-paper.pdf"]
    checks = []
    for path in pdfs:
        reader = PdfReader(path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert len(text) > 1000 and "LeagueEWS" in text and "exploratory" in text.lower()
        checks.append(
            {
                "path": str(path.relative_to(ROOT)),
                "pages": len(reader.pages),
                "extracted_characters": len(text),
                "sha256": digest(path),
            }
        )
    (OUT / "document-checks.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    run(parser.parse_args())
