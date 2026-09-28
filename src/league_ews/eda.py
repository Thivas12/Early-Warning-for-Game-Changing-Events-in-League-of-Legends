"""Identifier-free, self-contained EDA from the audited final collection."""

# The embedded HTML and SVG markup is kept together for an offline, single-file report.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import html
import json
import re
from bisect import bisect_left, bisect_right
from collections import Counter
from itertools import pairwise
from pathlib import Path
from statistics import median
from typing import Any, cast

EVENTS = ("baron", "dragon", "teamfight")
HORIZONS = (10, 20, 30, 60)
PATCHES = ("16.12", "16.13", "16.14", "16.15", "16.16", "16.17")
ROUTES = ("europe", "americas")
COLORS = {"baron": "#f4bd78", "dragon": "#5bd6c0", "teamfight": "#ad9cff"}


def _read(path: Path) -> tuple[dict[str, Any], str]:
    content = path.read_bytes()
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("EDA source must be a JSON object")
    return payload, hashlib.sha256(content).hexdigest()


def _training_calibration_aggregates(
    partitions: dict[str, Any], processed_root: Path, manifest_sha: str
) -> dict[str, Any]:
    manifest, actual_sha = _read(processed_root / "processing-manifest.json")
    records = manifest.get("matches")
    if (
        actual_sha != manifest_sha
        or manifest.get("schema_version") != "league-ews-processing-manifest-v1"
        or manifest.get("contains_player_identifiers") is not False
        or not isinstance(records, list)
        or len(records) != 36000
    ):
        raise ValueError("EDA processed inventory differs from audited split")
    by_id = {row.get("match_id"): row for row in records if isinstance(row, dict)}
    if len(by_id) != 36000:
        raise ValueError("EDA processed inventory contains duplicate matches")
    counts: Counter[str] = Counter()
    labelable: Counter[tuple[str, int]] = Counter()
    positives: Counter[tuple[str, str, int]] = Counter()
    rows_by_split: Counter[str] = Counter()
    rows_by_cell: Counter[tuple[str, str]] = Counter()
    positive_by_cell: Counter[tuple[str, str, str, int]] = Counter()
    onset_by_time: Counter[tuple[str, int]] = Counter()
    intervals: list[int] = []
    observations = 0
    position_known = 0
    participant_states = 0
    for partition in ("train", "calibration"):
        for member in partitions[partition]:
            match_id = member.get("match_id")
            route, patch = member.get("regional_route"), member.get("game_version_patch")
            record = by_id.get(match_id)
            if (
                not isinstance(match_id, str)
                or re.fullmatch(r"[A-Z0-9]+_[0-9]+", match_id) is None
                or not isinstance(record, dict)
                or route not in ROUTES
                or patch not in PATCHES[:5]
                or (partition == "calibration") != (patch == PATCHES[4])
            ):
                raise ValueError("EDA processed member is absent from the audit")
            content = (processed_root / "matches" / f"{match_id}.json").read_bytes()
            if hashlib.sha256(content).hexdigest() != record.get("sha256"):
                raise ValueError("EDA processed match checksum differs from audit")
            payload = json.loads(content)
            if (
                not isinstance(payload, dict)
                or payload.get("schema_version") != "league-ews-processed-match-v1"
            ):
                raise ValueError("EDA processed match schema differs")
            timeline = payload.get("timeline")
            index = payload.get("event_index")
            labels = payload.get("labels")
            if not isinstance(timeline, dict) or not isinstance(index, dict):
                raise ValueError("EDA processed timeline or event index is missing")
            frames = timeline.get("observations")
            if (
                timeline.get("match_id") != match_id
                or not isinstance(frames, list)
                or not isinstance(labels, list)
                or len(labels) != len(frames)
            ):
                raise ValueError("EDA processed match identity differs")
            raw_times = [frame.get("timestamp_ms") for frame in frames if isinstance(frame, dict)]
            if (
                len(raw_times) != len(frames)
                or len(raw_times) != record.get("observations")
                or not raw_times
                or any(not isinstance(time, int) or time < 0 for time in raw_times)
            ):
                raise ValueError("EDA processed observation timing differs")
            times = cast(list[int], raw_times)
            if any(second <= first for first, second in pairwise(times)):
                raise ValueError("EDA processed observation timing differs")
            observations += len(times)
            rows_by_split[partition] += len(times)
            rows_by_cell[route, patch] += len(times)
            intervals.extend(second - first for first, second in pairwise(times))
            event_index: dict[str, list[int]] = {}
            for event in EVENTS:
                values = index.get(f"{event}_ms")
                if (
                    not isinstance(values, list)
                    or any(not isinstance(value, int) or value < 0 for value in values)
                    or values != sorted(values)
                    or len(values) != record.get(f"{event}_events")
                ):
                    raise ValueError("EDA processed event count differs from audit")
                counts[event] += len(values)
                event_index[event] = values
                for onset in values:
                    onset_by_time[event, min(onset // 300_000, 7)] += 1
                    position = bisect_left(times, onset) - 1
                    if position < 0:
                        continue
                    delay = onset - times[position]
                    for horizon in HORIZONS:
                        if 0 < delay <= horizon * 1000:
                            labelable[event, horizon] += 1
            for frame, row, timestamp in zip(frames, labels, times, strict=True):
                participants = frame.get("participants")
                if (
                    not isinstance(participants, list)
                    or len(participants) != 10
                    or not isinstance(row, dict)
                    or row.get("timestamp_ms") != timestamp
                ):
                    raise ValueError("EDA participant or label inventory differs")
                for participant in participants:
                    if not isinstance(participant, dict):
                        raise ValueError("EDA participant state differs")
                    participant_states += 1
                    if participant.get("position") is not None:
                        position_known += 1
                for event in EVENTS:
                    events = event_index[event]
                    next_index = bisect_right(events, timestamp)
                    for horizon in HORIZONS:
                        name = f"y_{event}_{horizon}"
                        value = row.get(name)
                        expected = int(
                            next_index < len(events)
                            and events[next_index] <= timestamp + horizon * 1000
                        )
                        if type(value) is not int or value != expected:
                            raise ValueError(
                                "EDA strict future label differs from source event index"
                            )
                        positives[partition, event, horizon] += value
                        positive_by_cell[route, patch, event, horizon] += value
    analyzed_matches = len(partitions["train"]) + len(partitions["calibration"])
    if len(intervals) != observations - analyzed_matches or any(
        not counts[event] for event in EVENTS
    ):
        raise ValueError("EDA train/calibration observations or events are incomplete")
    return {
        "observations": observations,
        "cadence_ms": {
            "minimum": min(intervals),
            "median": median(intervals),
            "maximum": max(intervals),
        },
        "event_counts": {event: counts[event] for event in EVENTS},
        "positive_rows": {
            partition: {
                event: {str(h): positives[partition, event, h] for h in HORIZONS}
                for event in EVENTS
            }
            for partition in ("train", "calibration")
        },
        "rows_by_split": dict(rows_by_split),
        "cell_prevalence_percent": [
            {
                "route": route,
                "patch": patch,
                "observations": rows_by_cell[route, patch],
                "positive_percent": {
                    event: {
                        str(h): round(
                            100
                            * positive_by_cell[route, patch, event, h]
                            / rows_by_cell[route, patch]
                            if rows_by_cell[route, patch]
                            else 0,
                            4,
                        )
                        for h in HORIZONS
                    }
                    for event in EVENTS
                },
            }
            for patch in PATCHES[:5]
            for route in ROUTES
        ],
        "onsets_by_five_minute_bin": {
            event: [onset_by_time[event, bin_index] for bin_index in range(8)] for event in EVENTS
        },
        "position_coverage": {
            "known": position_known,
            "participant_states": participant_states,
            "percent": round(100 * position_known / participant_states, 4),
        },
        "opportunity_percent": {
            event: [
                round(100 * labelable[event, horizon] / counts[event], 4) for horizon in HORIZONS
            ]
            for event in EVENTS
        },
    }


def audited_eda_data(
    g2_path: str | Path,
    split_path: str | Path,
    audit_path: str | Path,
    processed_root: str | Path,
) -> dict[str, Any]:
    """Check provenance, then aggregate split metadata without exporting IDs."""

    g2, g2_sha = _read(Path(g2_path))
    split, split_sha = _read(Path(split_path))
    audit, audit_sha = _read(Path(audit_path))
    summary = g2.get("summary")
    audit_summary = audit.get("summary")
    split_summary = split.get("summary")
    if not (
        g2.get("schema_version") == "riot-raw-validation-v5"
        and g2.get("passed") is True
        and g2.get("automated_passed") is True
        and g2.get("g2_complete") is True
        and isinstance(g2.get("sampling_frame"), dict)
        and g2["sampling_frame"].get("status") == "passed"
        and isinstance(summary, dict)
        and summary.get("valid_bundles") == 36000
        and audit.get("schema_version") == "league-ews-processed-validation-v1"
        and audit.get("passed") is True
        and isinstance(audit_summary, dict)
        and audit_summary.get("validated_matches") == 36000
        and audit_summary.get("contains_player_identifiers") is False
        and split.get("schema_version") == "league-ews-final-split-v1"
        and split.get("g2_report_sha256") == g2_sha
        and split.get("processed_audit_sha256") == audit_sha
        and split.get("raw_manifest_sha256") == g2.get("manifest_sha256")
        and split.get("processing_manifest_sha256") == audit.get("processing_manifest_sha256")
        and isinstance(split_summary, dict)
        and split_summary.get("counts") == {"train": 24000, "calibration": 6000, "test": 6000}
    ):
        raise ValueError("EDA requires the passed, checksum-bound final G2, audit and split")

    partitions = split.get("partitions")
    if not isinstance(partitions, dict) or set(partitions) != {"train", "calibration", "test"}:
        raise ValueError("EDA split partitions are incomplete")
    cells: Counter[tuple[str, str]] = Counter()
    for name, patches in (
        ("train", PATCHES[:4]),
        ("calibration", PATCHES[4:5]),
        ("test", PATCHES[5:]),
    ):
        entries = partitions[name]
        if not isinstance(entries, list) or len(entries) != split_summary["counts"][name]:
            raise ValueError("EDA split count differs from frozen membership")
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("EDA split entry is invalid")
            route, patch = entry.get("regional_route"), entry.get("game_version_patch")
            if not isinstance(route, str) or not isinstance(patch, str):
                raise ValueError("EDA split contains a route or patch outside its partition")
            if route not in ROUTES or patch not in patches:
                raise ValueError("EDA split contains a route or patch outside its partition")
            cells[route, patch] += 1
    if any(cells[route, patch] != 3000 for route in ROUTES for patch in PATCHES):
        raise ValueError("EDA requires exactly 3,000 matches in every route-patch cell")
    if summary.get("regional_routes") != {"americas": 18000, "europe": 18000} or summary.get(
        "patches"
    ) != dict.fromkeys(PATCHES, 6000):
        raise ValueError("EDA raw coverage disagrees with frozen split")

    aggregates = _training_calibration_aggregates(
        partitions, Path(processed_root), str(split["processing_manifest_sha256"])
    )
    return {
        "schema_version": "league-ews-public-eda-v2",
        "matches": 30000,
        "frozen_matches": 36000,
        **aggregates,
        "cells": [
            {"route": route, "patch": patch, "matches": cells[route, patch]}
            for route in ROUTES
            for patch in PATCHES
        ],
        "split_counts": split_summary["counts"],
        "horizons_seconds": list(HORIZONS),
        "g2_sha256": g2_sha,
        "split_sha256": split_sha,
        "processed_audit_sha256": audit_sha,
        "test_outcomes_unread": True,
        "contains_player_identifiers": False,
    }


def _cell_chart() -> str:
    parts = [
        '<svg viewBox="0 0 800 260" role="img" aria-labelledby="cells-title cells-desc">',
        '<title id="cells-title">Frozen route and patch sampling matrix</title>',
        '<desc id="cells-desc">Every EUW1 and NA1 patch cell has 3,000 matches. Four train patches, one calibration patch, one sealed test patch.</desc>',
    ]
    for index, patch in enumerate(PATCHES):
        x = 120 + index * 110
        color = "#4ac8ba" if index < 4 else "#e9ad66" if index == 4 else "#ad9cff"
        parts.append(f'<text x="{x + 44}" y="29" text-anchor="middle">{patch}</text>')
        for row in range(2):
            y = 58 + row * 84
            parts.append(
                f'<rect x="{x}" y="{y}" width="89" height="65" rx="13" fill="{color}" fill-opacity=".14" stroke="{color}" stroke-opacity=".6"><title>3,000 matches</title></rect>'
                f'<text x="{x + 44}" y="{y + 39}" text-anchor="middle" class="value">3,000</text>'
            )
    parts.extend(
        [
            '<text x="11" y="98">EUW1</text><text x="11" y="182">NA1</text>',
            '<text x="280" y="240" text-anchor="middle" class="small">TRAIN · 24,000</text>',
            '<text x="604" y="240" text-anchor="middle" class="small">CAL · 6,000</text>',
            '<text x="714" y="240" text-anchor="middle" class="small">TEST · 6,000</text>',
            "</svg>",
        ]
    )
    return "".join(parts)


def _opportunity_chart(values: dict[str, list[float]]) -> str:
    parts = [
        '<svg viewBox="0 0 800 360" role="img" aria-labelledby="opp-title opp-desc">',
        '<title id="opp-title">Fraction of events with a strictly prior observation within each horizon</title>',
        '<desc id="opp-desc">Lines for Baron, Dragon and teamfight across ten, twenty, thirty and sixty seconds. This is an opportunity measure, not model recall.</desc>',
    ]
    for pct in (0, 25, 50, 75, 100):
        y = 294 - pct * 2.55
        parts.append(
            f'<path d="M82 {y:.1f} H739" stroke="#31435a" stroke-dasharray="4 7"/>'
            f'<text x="68" y="{y + 4:.1f}" text-anchor="end" class="small">{pct}%</text>'
        )
    for index, horizon in enumerate(HORIZONS):
        x = 105 + index * 207
        parts.append(f'<text x="{x}" y="326" text-anchor="middle" class="small">{horizon} s</text>')
    for event in EVENTS:
        positions = [
            (105 + i * 207, 294 - min(value, 100) * 2.55) for i, value in enumerate(values[event])
        ]
        line = " ".join(f"{x:.1f},{y:.1f}" for x, y in positions)
        parts.append(
            f'<polyline points="{line}" fill="none" stroke="{COLORS[event]}" stroke-width="3.5" stroke-linejoin="round"/>'
        )
        for (x, y), value in zip(positions, values[event], strict=True):
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{COLORS[event]}" stroke="#132338" stroke-width="2"><title>{html.escape(event.title())}: {value:.1f}%</title></circle>'
            )
    parts.append("</svg>")
    return "".join(parts)


def _event_chart(counts: dict[str, int], matches: int) -> str:
    maximum = max(counts.values())
    parts = [
        '<svg viewBox="0 0 800 285" role="img" aria-labelledby="mix-title mix-desc">',
        '<title id="mix-title">Event onsets in the audited final collection</title>',
        '<desc id="mix-desc">Baron, Dragon and qualifying teamfight episodes. Counts are event onsets, not unique games.</desc>',
    ]
    for index, event in enumerate(EVENTS):
        y = 42 + index * 83
        width = 490 * counts[event] / maximum
        parts.append(
            f'<text x="12" y="{y + 19}">{html.escape(event.title())}</text>'
            f'<rect x="137" y="{y}" width="490" height="29" rx="9" fill="#26394f"/>'
            f'<rect x="137" y="{y}" width="{width:.1f}" height="29" rx="9" fill="{COLORS[event]}"/>'
            f'<text x="646" y="{y + 20}" class="value">{counts[event]:,}</text>'
            f'<text x="137" y="{y + 49}" class="small">{counts[event] / matches:.2f} onsets per match</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _prevalence_chart(data: dict[str, Any]) -> str:
    """Compare row-level target prevalence on a shared, explicitly labeled scale."""

    positives = data["positive_rows"]
    totals = data["rows_by_split"]
    maximum = max(
        100 * positives[split][event][str(h)] / totals[split]
        for split in ("train", "calibration")
        for event in EVENTS
        for h in HORIZONS
    )
    scale = max(1, int(maximum + 0.9999))
    parts = [
        '<svg viewBox="0 0 860 580" role="img" aria-labelledby="prev-title prev-desc">',
        '<title id="prev-title">Positive observation rates by target</title>',
        '<desc id="prev-desc">Paired training and calibration bars for twelve event and horizon targets. The bars use the same linear percentage scale.</desc>',
    ]
    for tick in (0, scale / 2, scale):
        x = 170 + 470 * tick / scale
        parts.append(
            f'<path d="M{x:.1f} 30 V530" stroke="#31435a" stroke-dasharray="4 7"/>'
            f'<text x="{x:.1f}" y="550" text-anchor="middle" class="small">{tick:g}%</text>'
        )
    for index, (event, horizon) in enumerate(
        (event, horizon) for event in EVENTS for horizon in HORIZONS
    ):
        y = 43 + index * 40
        parts.append(f'<text x="8" y="{y + 13}" class="small">{event.title()} · {horizon}s</text>')
        for split, offset, color in (
            ("train", 0, "#5bd6c0"),
            ("calibration", 16, "#e9ad66"),
        ):
            rate = 100 * positives[split][event][str(horizon)] / totals[split]
            width = 470 * rate / scale
            parts.append(
                f'<rect x="170" y="{y + offset}" width="{width:.2f}" height="13" rx="4" fill="{color}"><title>{split.title()}: {rate:.3f}% ({positives[split][event][str(horizon)]:,}/{totals[split]:,})</title></rect>'
                f'<text x="655" y="{y + offset + 11}" class="small">{rate:.2f}%</text>'
            )
    parts.append("</svg>")
    return "".join(parts)


def _timing_chart(counts: dict[str, list[int]]) -> str:
    """Show within-type onset timing without hiding the rare Baron series."""

    parts = [
        '<svg viewBox="0 0 850 420" role="img" aria-labelledby="time-title time-desc">',
        '<title id="time-title">Event onset timing by five-minute match-time bin</title>',
        '<desc id="time-desc">Each event series is scaled to its own maximum; tooltip gives the actual onset count. The last bin contains all onsets at 35 minutes or later.</desc>',
    ]
    for row, event in enumerate(EVENTS):
        top = 38 + row * 125
        maximum = max(counts[event])
        parts.append(f'<text x="12" y="{top + 15}" class="value">{event.title()}</text>')
        parts.append(f'<path d="M125 {top + 82} H816" stroke="#31435a"/>')
        for index, value in enumerate(counts[event]):
            x = 137 + index * 95
            height = 65 * value / maximum if maximum else 0
            label = f"{index * 5}-{index * 5 + 5}m" if index < 7 else "35m+"
            parts.append(
                f'<rect x="{x}" y="{top + 82 - height:.1f}" width="55" height="{height:.1f}" rx="5" fill="{COLORS[event]}"><title>{label}: {value:,} onsets</title></rect>'
            )
            if row == 2:
                parts.append(
                    f'<text x="{x + 27}" y="{top + 102}" text-anchor="middle" class="small">{label}</text>'
                )
    parts.append("</svg>")
    return "".join(parts)


def render_eda_html(data: dict[str, Any]) -> str:
    """Render only aggregates assembled by audited_eda_data."""

    cadence = data["cadence_ms"]
    styles = """
    :root{color-scheme:dark;--ink:#e8f1f5;--muted:#9db0c3;--line:#304258}
    *{box-sizing:border-box}body{margin:0;background:#0b1625;color:var(--ink);font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
    body:before{content:"";position:fixed;inset:0;pointer-events:none;background:radial-gradient(circle at 85% 0%,#174a55a8,transparent 38%),radial-gradient(circle at 0% 80%,#32325b77,transparent 43%)}
    main{position:relative;max-width:1160px;margin:auto;padding:58px 28px 100px}.eyebrow{color:#5bd6c0;text-transform:uppercase;letter-spacing:.2em;font-size:.8rem;font-weight:700}
    h1{font-size:clamp(2.6rem,6vw,5.5rem);line-height:1.04;letter-spacing:-.065em;margin:.18em 0}.subtitle{max-width:720px;color:var(--muted);font-size:1.16rem}
    .rule{height:1px;background:linear-gradient(90deg,#5bd6c0,transparent);margin:35px 0}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:15px}
    .metric,.panel{background:#15263adf;border:1px solid #3a5368;border-radius:20px;box-shadow:0 16px 40px #06111d44}
    .metric{padding:23px}.metric strong{display:block;font-size:2rem;letter-spacing:-.05em}.metric span,.meta{font-size:.83rem;color:var(--muted)}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px}.panel{padding:26px;min-width:0}.wide{grid-column:1/-1}
    h2{font-size:1.45rem;letter-spacing:-.025em;margin:0 0 5px}p{color:var(--muted);margin:0 0 15px;max-width:78ch}svg{width:100%;height:auto;display:block;font:15px system-ui,sans-serif;fill:#e8f1f5}svg .small{font-size:13px;fill:#9db0c3}svg .value{font-weight:750}
    .legend{display:flex;gap:21px;flex-wrap:wrap}.legend span:before{content:"";display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--swatch);margin-right:7px}
    .note{border-left:3px solid #e9ad66;padding:15px 20px;background:#e9ad6616;color:#d7e3e9;margin-top:20px;border-radius:0 12px 12px 0}
    .table-scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}th,td{text-align:right;padding:10px;border-bottom:1px solid #304258;white-space:nowrap}th:first-child,td:first-child{text-align:left}thead th{color:#9db0c3;font-weight:600}
    footer{margin-top:45px;color:var(--muted);font-size:.81rem;overflow-wrap:anywhere}code{color:#b9eee4}@media(max-width:760px){.metrics,.grid{grid-template-columns:1fr 1fr}.panel{grid-column:1/-1}}
    @media(max-width:480px){main{padding:35px 16px 70px}.metrics{grid-template-columns:1fr 1fr}.metric{padding:14px}.metric strong{font-size:1.5rem}}
    @media print{body{background:#0b1625!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}.panel,.metric{break-inside:avoid}}
    """
    legend = "".join(
        f'<span style="--swatch:{COLORS[event]}">{event.title()}</span>' for event in EVENTS
    )
    prevalence_legend = '<span style="--swatch:#5bd6c0">Train</span><span style="--swatch:#e9ad66">Calibration</span>'
    cell_rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['route'].title())} / {html.escape(row['patch'])}</td>"
        f"<td>{row['observations']:,}</td>"
        + "".join(
            f"<td>{row['positive_percent'][event]['10']:.2f}% / {row['positive_percent'][event]['60']:.2f}%</td>"
            for event in EVENTS
        )
        + "</tr>"
        for row in data["cell_prevalence_percent"]
    )
    coverage = data["position_coverage"]
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RiftHazard | Audited data atlas</title><style>{styles}</style></head>
<body><main><div class="eyebrow">RiftHazard / research v2 / data atlas</div><h1>Before the warning.</h1>
<p class="subtitle">The shape of the frozen League of Legends research sample, and the limits imposed by genuine timeline observations. Built from passed validation and split artifacts.</p>
<div class="rule"></div><section class="metrics" aria-label="Dataset at a glance">
<div class="metric"><strong>{data["matches"]:,}</strong><span>train and calibration matches</span></div>
<div class="metric"><strong>{data["observations"]:,}</strong><span>genuine prediction snapshots</span></div>
<div class="metric"><strong>12</strong><span>route by patch cells</span></div>
<div class="metric"><strong>{float(cadence["median"]) / 1000:.2f} s</strong><span>median within-match interval</span></div></section>
<div class="grid"><section class="panel wide"><h2>01 / The frozen population</h2><p>Equal route and patch allocation prevents one region or patch from dominating the sample. Entire matches stay in a single chronological patch partition.</p>{_cell_chart()}</section>
<section class="panel wide"><h2>02 / The opportunity to warn</h2><p>Share of event onsets with at least one strictly earlier genuine snapshot inside each forecast horizon. This is a data availability ceiling, not recall or accuracy.</p><div class="legend">{legend}</div>{_opportunity_chart(data["opportunity_percent"])}</section>
<section class="panel"><h2>03 / What occurs</h2><p>Source event onsets in 30,000 train and calibration matches. The teamfight series uses the frozen qualifying kill-episode proxy.</p>{_event_chart(data["event_counts"], data["matches"])}</section>
<section class="panel"><h2>04 / Native timeline timing</h2><p>Intervals are measured only between genuine observations within each match. The minimum, median and maximum are shown; they are not a full interval distribution.</p>
<div class="metric"><strong>{float(cadence["minimum"]) / 1000:.3f} s</strong><span>shortest observed interval</span></div><br>
<div class="metric"><strong>{float(cadence["median"]) / 1000:.3f} s</strong><span>median observed interval</span></div><br>
<div class="metric"><strong>{float(cadence["maximum"]) / 1000:.3f} s</strong><span>longest observed interval</span></div></section>
<section class="panel wide"><h2>05 / The actual class imbalance</h2><p>Positive prediction rows divided by all genuine rows in that partition. Train and calibration share the same horizontal scale; these rates are distinct from the event opportunity plot above.</p><div class="legend">{prevalence_legend}</div>{_prevalence_chart(data)}</section>
<section class="panel wide"><h2>06 / Patch and route slices</h2><p>Positive row rate at 10s / 60s for each event type. Equal match allocations need not yield equal observation or label counts. Test-patch labels remain sealed.</p><div class="table-scroll"><table><thead><tr><th>Route / patch</th><th>Rows</th><th>Baron 10s / 60s</th><th>Dragon 10s / 60s</th><th>Teamfight 10s / 60s</th></tr></thead><tbody>{cell_rows}</tbody></table></div></section>
<section class="panel"><h2>07 / When events start</h2><p>Source onsets by five-minute game-time bin. Each type has its own height scale, so compare the shape within a type, not bar heights between types. Hover for exact counts.</p>{_timing_chart(data["onsets_by_five_minute_bin"])}</section>
<section class="panel"><h2>08 / Position availability</h2><p>Position is present in {coverage["known"]:,} of {coverage["participant_states"]:,} player frame states ({coverage["percent"]:.2f}%). Missing positions have an explicit indicator in M1. This processed-data check cannot reveal numeric fields defaulted during raw normalization.</p><div class="metric"><strong>{coverage["percent"]:.2f}%</strong><span>player states with observed position</span></div></section></div>
<div class="note">Short horizons can miss an event even with a perfect model when no genuine observation exists in that window. The test-patch match files were not opened to make these figures.</div>
<footer>Validated final G2 SHA-256: <code>{data["g2_sha256"]}</code><br>Frozen split SHA-256: <code>{data["split_sha256"]}</code><br>Processed audit SHA-256: <code>{data["processed_audit_sha256"]}</code><br>Aggregates only · no match IDs, PUUIDs, raw payloads or prediction scores.</footer></main></body></html>"""


def write_eda(
    g2_path: str | Path,
    split_path: str | Path,
    audit_path: str | Path,
    processed_root: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    data = audited_eda_data(g2_path, split_path, audit_path, processed_root)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".partial")
    temporary.write_text(render_eda_html(data), encoding="utf-8")
    temporary.replace(output)
    summary = {key: value for key, value in data.items() if key != "cells"}
    summary_path = output.with_name("summary.json")
    summary_temporary = summary_path.with_suffix(".json.partial")
    summary_temporary.write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    summary_temporary.replace(summary_path)
    return summary
