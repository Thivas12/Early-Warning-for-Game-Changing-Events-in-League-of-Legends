"""Render the editorial revision without changing frozen development artifacts."""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

import build_publication_package as base
from pypdf import PdfReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/publication-review-2026-10-08"
SOURCE = ROOT / "docs/leagueews-paper-revised.md"
PDF = ROOT / "paper/leagueews-2026-10/leagueews-reviewed-paper.pdf"
DOCUMENTS = (
    "README.md",
    "RESEARCH_HISTORY.md",
    "docs/leagueews-paper-revised.md",
    "docs/recruiter-walkthrough.md",
    "docs/submission-readiness.md",
    "reports/publication-review-2026-10-08/README.md",
)
base.REMOTE = base.REMOTE.replace(
    "research/league-publication-package-20261007/", "docs/league-publication-finish-20261008/"
)


def verify_sources():
    manifest = json.loads((base.OUT / "published-artifacts.json").read_text())
    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        if base.digest(path) != artifact["sha256"]:
            raise ValueError(f"Frozen artifact changed: {path}")
    evidence = json.loads((OUT / "absolute-baselines.json").read_text())
    path = ROOT / evidence["source"]
    if base.digest(path) != evidence["source_sha256"]:
        raise ValueError("Baseline source checksum mismatch")
    source = json.loads(path.read_text())
    for record in evidence["records"]:
        value = source
        for key in record["json_pointer"].strip("/").split("/"):
            value = value[key]
        if value != record["value"]:
            raise ValueError(f"Baseline value mismatch: {record['json_pointer']}")
    manuscript = SOURCE.read_text()
    families = source["analysis"]["overall"]["30"]["families"]
    for family, label in (
        ("leagueews", "LeagueEWS"),
        ("tcn", "TCN"),
        ("gru", "GRU"),
        ("snapshot", "Snapshot"),
    ):
        values = families[family]
        cells = [label]
        for event in ("baron", "dragon", "teamfight"):
            recall = values[event]["mean_over_fixed_seeds"]["timely_recall"]
            cells.append(f"{100 * recall['estimate']:.3f}")
        macro = values["macro"]["mean_over_fixed_seeds"]
        recall = macro["timely_recall"]
        lo, hi = recall["conditional_95_interval"]
        cells.append(f"{100 * recall['estimate']:.3f} [{100 * lo:.3f}, {100 * hi:.3f}]")
        cells.append(f"{macro['false_plus_late_per_match']['estimate']:.3f}")
        if "| " + " | ".join(cells) + " |" not in manuscript:
            raise ValueError(f"Displayed baseline row mismatch: {family}")
    runtime = json.loads((base.OUT / "runtime.json").read_text())
    for architecture in ("leagueews", "tcn"):
        for device in ("cpu", "cuda"):
            for batch in (1, 128):
                median = statistics.median(
                    r["median_ms"]
                    for r in runtime["records"]
                    if r["architecture"] == architecture
                    and r["device"] == device
                    and r["batch"] == batch
                )
                if f"{median:.3f}" not in manuscript:
                    raise ValueError(f"Missing runtime value: {architecture}, {device}, {batch}")
    return len(manifest["artifacts"]), len(evidence["records"])


def paragraph(lines, index):
    text = []
    while index < len(lines) and lines[index].strip():
        if lines[index].startswith(("#", "|", "![")):
            break
        text.append(lines[index])
        index += 1
    return " ".join(text), index


def story(styles):
    lines, items, i = SOURCE.read_text().splitlines(), [], 0
    styles.add(ParagraphStyle("Caption", parent=styles["BodyText"], fontSize=8.2, leading=11.5))
    styles.add(ParagraphStyle("TableIntro", parent=styles["BodyText"], keepWithNext=True))
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            style = "Title" if level == 1 else "Heading1" if level == 2 else "Heading2"
            items.append(Paragraph(base.inline(line[level:].strip(), SOURCE.parent), styles[style]))
            i += 1
        elif line.startswith("!["):
            match = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", line)
            if match is None:
                raise ValueError(f"Invalid image: {line}")
            image = Image(str((SOURCE.parent / match[2]).resolve()))
            image.drawHeight *= 470 / image.drawWidth
            image.drawWidth = 470
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            caption, i = paragraph(lines, i)
            items.append(
                KeepTogether(
                    [
                        image,
                        Spacer(1, 6),
                        Paragraph(base.inline(caption, SOURCE.parent), styles["Caption"]),
                    ]
                )
            )
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [x.strip() for x in lines[i].strip("|").split("|")]
                if not all(re.fullmatch(r"[-:]+", x) for x in cells):
                    rows.append([base.inline(x, SOURCE.parent) for x in cells])
                i += 1
            widths = {
                "Prior work": [90, 170, 210],
                "Partition": [85, 75, 60, 80, 170],
            }.get(rows[0][0])
            if len(rows[0]) == 6:
                widths = [70, 62, 62, 66, 140, 70]
            items.extend([base.table(rows, styles, widths), Spacer(1, 9)])
        else:
            text, i = paragraph(lines, i)
            style = "TableIntro" if text.startswith("**Table") else "BodyText"
            items.append(Paragraph(base.inline(text, SOURCE.parent), styles[style]))
    return items


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Research", 7)
    canvas.setFillColor(base.colors.HexColor(base.GREY))
    canvas.drawString(60, 28, "LeagueEWS · Exploratory working paper · 8 October 2026")
    canvas.drawRightString(535, 28, str(doc.page))
    canvas.restoreState()


def run():
    frozen_count, baseline_count = verify_sources()
    styles = base.setup_styles()
    styles["BodyText"].spaceAfter = 6
    styles["BodyText"].spaceBefore = 0
    styles["BodyText"].leading = 12.5
    styles["Heading1"].keepWithNext = True
    styles["Heading2"].keepWithNext = True
    SimpleDocTemplate(
        str(PDF),
        pagesize=(595.28, 841.89),
        rightMargin=60,
        leftMargin=60,
        topMargin=48,
        bottomMargin=57,
        invariant=1,
        title="Useful Early Warnings in League of Legends: History, Supervision and Alert Costs",
        author="Keerthivasan Kannan",
    ).build(story(styles), onFirstPage=footer, onLaterPages=footer)
    checked = 0
    for document in DOCUMENTS:
        path = ROOT / document
        for target in re.findall(r"!?\[[^]]*\]\(([^)]+)\)", path.read_text()):
            if target.startswith(("http:", "https:", "#")):
                continue
            resolved = (path.parent / target.split("#", 1)[0]).resolve()
            if not resolved.exists() and resolved != OUT / "verification.json":
                raise ValueError(f"Missing link: {document}: {target}")
            checked += 1
    reader = PdfReader(PDF)
    text = "\n".join(page.extract_text() for page in reader.pages)
    for required in ("Table 2.", "12.379", "0.785", "0.242", "3.14", "References"):
        if required not in text:
            raise ValueError(f"PDF missing required content: {required}")
    artifacts = (
        *DOCUMENTS,
        str(PDF.relative_to(ROOT)),
        "reports/publication-review-2026-10-08/absolute-baselines.json",
        "scripts/build_publication_review.py",
    )
    result = {
        "status": "passed-editorial-artifact-checks",
        "date": "2026-10-08",
        "base_commit": "8d3a903db3c1da3af87e5c07c58cf53b7d9a90eb",
        "frozen_artifacts_unchanged": frozen_count,
        "baseline_records_exact": baseline_count,
        "displayed_baseline_rows_verified": 4,
        "runtime_display_values_verified": 8,
        "local_link_targets_checked": checked,
        "pdf_pages": len(reader.pages),
        "pdf_page_characters": [len(p.extract_text()) for p in reader.pages],
        "new_fits": 0,
        "new_outcome_evaluations": 0,
        "test_payloads_opened": 0,
        "artifacts": [{"path": p, "sha256": base.digest(ROOT / p)} for p in artifacts],
        "scope": "Artifact checks; not independent empirical replication or peer review.",
    }
    (OUT / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "artifacts"}, indent=2))


if __name__ == "__main__":
    run()
