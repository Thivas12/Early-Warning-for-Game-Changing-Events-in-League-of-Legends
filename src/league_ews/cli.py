"""Command-line entry point for auditable research workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from league_ews.audit import audit_legacy_frame
from league_ews.authority import collection_preflight
from league_ews.benchmark import run_legacy_benchmark
from league_ews.diagnostics import diagnose_legacy_sequence_split
from league_ews.io import load_legacy_csv, sha256_file
from league_ews.processing import process_raw_collection
from league_ews.provenance import source_provenance
from league_ews.raw_validation import create_event_spot_check_record, validate_raw_collection
from league_ews.riot import RiotMatchClient, collect_match_bundles


def _write_json(payload: object, output: Path | None) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if output is None:
        print(rendered, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")


def _audit(args: argparse.Namespace) -> int:
    frame = load_legacy_csv(args.csv, nrows=args.nrows)
    report = audit_legacy_frame(frame).to_dict()
    report["dataset_sha256"] = sha256_file(args.csv)
    report["source"] = source_provenance()
    _write_json(report, args.output)
    return 2 if args.strict and not report["passed"] else 0


def _benchmark(args: argparse.Namespace) -> int:
    names = tuple(value.strip() for value in args.baselines.split(",") if value.strip())
    allowed = {"time", "history", "causal", "postmatch_leak"}
    unknown = sorted(set(names) - allowed)
    if unknown:
        raise ValueError(f"Unknown baselines: {', '.join(unknown)}")
    result = run_legacy_benchmark(
        args.csv,
        baselines=names,
        max_matches=args.max_matches,
        max_iter=args.max_iter,
        threshold_candidates=args.threshold_candidates,
    )
    output = Path(args.output)
    if output.suffix.lower() != ".json":
        output = output / "benchmark.json"
    _write_json(result, output)
    print(f"Wrote {output}")
    return 0


def _diagnose_split(args: argparse.Namespace) -> int:
    frame = load_legacy_csv(args.csv, usecols=("match_id", "t"))
    result = diagnose_legacy_sequence_split(
        frame,
        sequence_length=args.sequence_length,
        step=args.step,
        augmented_copies=args.augmented_copies,
        random_state=args.random_state,
    ).to_dict()
    result["dataset_sha256"] = sha256_file(args.csv)
    result["source"] = source_provenance()
    _write_json(result, args.output)
    return 0


def _collect(args: argparse.Namespace) -> int:
    preflight = collection_preflight(
        args.authority_record,
        requested_region=args.region,
    )
    if not preflight["passed"]:
        _write_json(preflight, None)
        return 2

    match_ids = args.match_ids.read_text(encoding="utf-8").splitlines()
    with RiotMatchClient.from_environment(regional_route=args.region) as client:
        result = collect_match_bundles(
            match_ids,
            regional_route=args.region,
            output_root=args.output,
            fetcher=client,
            overwrite=args.overwrite,
        )
    collected = cast(list[object], result["collected"])
    skipped = cast(list[object], result["skipped_existing"])
    print(
        f"Collected {len(collected)}; "
        f"skipped {len(skipped)}; manifest: "
        f"{args.output / 'collection-manifest.json'}"
    )
    return 0


def _preflight_collection(args: argparse.Namespace) -> int:
    report = collection_preflight(args.record, requested_region=args.region)
    _write_json(report, args.output)
    return 0 if report["passed"] else 2


def _process(args: argparse.Namespace) -> int:
    validation = validate_raw_collection(
        args.raw,
        min_routes=args.min_routes,
        min_patches=args.min_patches,
    )
    if not validation["passed"]:
        _write_json(validation, None)
        return 2
    result = process_raw_collection(args.raw, output_root=args.output)
    matches = cast(list[object], result["matches"])
    print(f"Processed {len(matches)} matches; manifest: {args.output / 'processing-manifest.json'}")
    return 0


def _validate_raw(args: argparse.Namespace) -> int:
    report = validate_raw_collection(
        args.raw,
        min_routes=args.min_routes,
        min_patches=args.min_patches,
        event_spot_check=args.event_spot_check,
        processed_root=args.processed,
    )
    _write_json(report, args.output)
    return 0 if report["passed"] else 2


def _record_event_spot_check(args: argparse.Namespace) -> int:
    record = create_event_spot_check_record(
        args.raw,
        args.processed,
        tuple(args.match_id),
        objective_events_match_source=args.confirm_objective_events,
        teamfight_episodes_match_source=args.confirm_teamfight_episodes,
        strict_future_labels_match_processed=args.confirm_future_labels,
    )
    _write_json(record, args.output)
    print(f"Recorded {len(args.match_id)} checksum-bound event spot-check sample(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="league-ews")
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="audit a legacy derived CSV")
    audit.add_argument("--csv", type=Path, required=True)
    audit.add_argument("--output", type=Path)
    audit.add_argument("--nrows", type=int)
    audit.add_argument("--strict", action="store_true")
    audit.set_defaults(handler=_audit)

    benchmark = subparsers.add_parser("benchmark", help="run group-safe legacy baselines")
    benchmark.add_argument("--csv", type=Path, required=True)
    benchmark.add_argument("--output", type=Path, required=True)
    benchmark.add_argument("--baselines", default="time,history,causal")
    benchmark.add_argument("--max-matches", type=int)
    benchmark.add_argument("--max-iter", type=int, default=100)
    benchmark.add_argument("--threshold-candidates", type=int, default=31)
    benchmark.set_defaults(handler=_benchmark)

    diagnostic = subparsers.add_parser(
        "diagnose-split", help="measure contamination in the legacy sequence split"
    )
    diagnostic.add_argument("--csv", type=Path, required=True)
    diagnostic.add_argument("--output", type=Path)
    diagnostic.add_argument("--sequence-length", type=int, default=40)
    diagnostic.add_argument("--step", type=int, default=5)
    diagnostic.add_argument("--augmented-copies", type=int, default=3)
    diagnostic.add_argument("--random-state", type=int, default=42)
    diagnostic.set_defaults(handler=_diagnose_split)

    preflight = subparsers.add_parser(
        "preflight-collection",
        help="validate private Riot collection authority without making an API request",
    )
    preflight.add_argument("--record", type=Path, required=True)
    preflight.add_argument("--region", choices=("americas", "asia", "europe", "sea"), required=True)
    preflight.add_argument("--output", type=Path)
    preflight.set_defaults(handler=_preflight_collection)

    collect = subparsers.add_parser("collect", help="fetch private Match-V5 raw bundles")
    collect.add_argument("--authority-record", type=Path, required=True)
    collect.add_argument("--match-ids", type=Path, required=True)
    collect.add_argument("--output", type=Path, default=Path("data/raw"))
    collect.add_argument("--region", choices=("americas", "asia", "europe", "sea"), required=True)
    collect.add_argument("--overwrite", action="store_true")
    collect.set_defaults(handler=_collect)

    validate_raw = subparsers.add_parser(
        "validate-raw",
        help="validate private raw bundle integrity and coverage without network access",
    )
    validate_raw.add_argument("--raw", type=Path, default=Path("data/raw"))
    validate_raw.add_argument("--output", type=Path)
    validate_raw.add_argument("--min-routes", type=int, default=2)
    validate_raw.add_argument("--min-patches", type=int, default=6)
    validate_raw.add_argument("--event-spot-check", type=Path)
    validate_raw.add_argument("--processed", type=Path)
    validate_raw.set_defaults(handler=_validate_raw)

    spot_check = subparsers.add_parser(
        "record-event-spot-check",
        help="record private human review of source events and processed labels",
    )
    spot_check.add_argument("--raw", type=Path, default=Path("data/raw"))
    spot_check.add_argument("--processed", type=Path, required=True)
    spot_check.add_argument("--match-id", action="append", required=True)
    spot_check.add_argument("--output", type=Path, required=True)
    spot_check.add_argument("--confirm-objective-events", action="store_true", required=True)
    spot_check.add_argument("--confirm-teamfight-episodes", action="store_true", required=True)
    spot_check.add_argument("--confirm-future-labels", action="store_true", required=True)
    spot_check.set_defaults(handler=_record_event_spot_check)

    process = subparsers.add_parser("process", help="normalize and label private raw bundles")
    process.add_argument("--raw", type=Path, default=Path("data/raw"))
    process.add_argument("--output", type=Path, default=Path("data/processed"))
    process.add_argument("--min-routes", type=int, default=2)
    process.add_argument("--min-patches", type=int, default=6)
    process.set_defaults(handler=_process)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handler = args.handler
    return int(handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
