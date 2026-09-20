"""Command-line entry point for auditable research workflows."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import cast

from league_ews.audit import audit_legacy_frame
from league_ews.authority import collection_preflight
from league_ews.benchmark import run_legacy_benchmark
from league_ews.diagnostics import diagnose_legacy_sequence_split
from league_ews.discovery import (
    PlatformDiscoveryFetcher,
    RegionalDiscoveryFetcher,
    candidate_discovery_preflight,
    discover_candidate_pool,
    validate_discovery_plan,
)
from league_ews.duration import analyze_pilot_duration
from league_ews.io import load_legacy_csv, sha256_file
from league_ews.pilot_collection import (
    TimelineFetcher,
    collect_selected_pilot_bundles,
    pilot_collection_preflight,
    validate_frozen_pilot_selection,
)
from league_ews.processing import process_raw_collection
from league_ews.provenance import source_provenance
from league_ews.raw_validation import create_event_spot_check_record, validate_raw_collection
from league_ews.riot import (
    RequestPacer,
    RiotMatchClient,
    RiotPlatformClient,
    collect_match_bundles,
)
from league_ews.sampling import load_registered_sampling_frame, validate_sampling_frame
from league_ews.selection import (
    DetailScreenFetcher,
    pilot_selection_preflight,
    select_pilot_matches,
    validate_candidate_pool,
)


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


def _validate_sampling_frame(args: argparse.Namespace) -> int:
    report = validate_sampling_frame(args.frame)
    _write_json(report, args.output)
    return 0 if report["passed"] else 2


def _validate_discovery_plan(args: argparse.Namespace) -> int:
    report = validate_discovery_plan(args.plan, args.sampling_frame)
    _write_json(report, args.output)
    return 0 if report["passed"] else 2


def _preflight_discovery(args: argparse.Namespace) -> int:
    report = candidate_discovery_preflight(
        args.authority_record,
        args.sampling_frame,
        args.discovery_plan,
    )
    _write_json(report, args.output)
    return 0 if report["passed"] else 2


def _discover_candidates(args: argparse.Namespace) -> int:
    preflight = candidate_discovery_preflight(
        args.authority_record,
        args.sampling_frame,
        args.discovery_plan,
    )
    if not preflight["passed"]:
        _write_json(preflight, None)
        return 2

    frame, _ = load_registered_sampling_frame(args.sampling_frame)
    pacer = RequestPacer(args.request_interval)
    with ExitStack() as stack:
        platform_fetchers: dict[str, PlatformDiscoveryFetcher] = {
            route.platform_id: stack.enter_context(
                RiotPlatformClient.from_environment(
                    platform_id=route.platform_id,
                    pace=pacer,
                )
            )
            for route in frame.route_platforms
        }
        regional_fetchers: dict[str, RegionalDiscoveryFetcher] = {
            route.regional_route: stack.enter_context(
                RiotMatchClient.from_environment(
                    regional_route=route.regional_route,
                    pace=pacer,
                )
            )
            for route in frame.route_platforms
        }
        manifest = discover_candidate_pool(
            args.sampling_frame,
            args.discovery_plan,
            output_root=args.output,
            platform_fetchers=platform_fetchers,
            regional_fetchers=regional_fetchers,
            progress=lambda message: print(message, file=sys.stderr),
        )
    _write_json(manifest, None)
    return 0 if manifest["complete"] else 2


def _validate_candidate_pool(args: argparse.Namespace) -> int:
    report = validate_candidate_pool(
        args.sampling_frame,
        args.discovery_plan,
        args.discovery_root,
    )
    _write_json(report, args.output)
    return 0 if report["passed"] else 2


def _preflight_pilot_selection(args: argparse.Namespace) -> int:
    report = pilot_selection_preflight(
        args.authority_record,
        args.sampling_frame,
        args.discovery_plan,
        args.discovery_root,
    )
    _write_json(report, args.output)
    return 0 if report["passed"] else 2


def _select_pilot(args: argparse.Namespace) -> int:
    preflight = pilot_selection_preflight(
        args.authority_record,
        args.sampling_frame,
        args.discovery_plan,
        args.discovery_root,
    )
    if not preflight["passed"]:
        _write_json(preflight, None)
        return 2

    frame, _ = load_registered_sampling_frame(args.sampling_frame)
    pacer = RequestPacer(args.request_interval)
    with ExitStack() as stack:
        regional_fetchers: dict[str, DetailScreenFetcher] = {
            route.regional_route: stack.enter_context(
                RiotMatchClient.from_environment(
                    regional_route=route.regional_route,
                    pace=pacer,
                )
            )
            for route in frame.route_platforms
        }
        manifest = select_pilot_matches(
            args.sampling_frame,
            args.discovery_plan,
            args.discovery_root,
            output_root=args.output,
            regional_fetchers=regional_fetchers,
            max_new_requests=args.max_new_requests,
            progress=lambda message: print(message, file=sys.stderr),
        )
    _write_json(manifest, None)
    return 0 if manifest["complete"] else 2


def _validate_pilot_selection(args: argparse.Namespace) -> int:
    report = validate_frozen_pilot_selection(
        args.sampling_frame,
        args.discovery_plan,
        args.discovery_root,
        args.selection_root,
    )
    _write_json(report, args.output)
    return 0 if report["passed"] else 2


def _preflight_pilot_collection(args: argparse.Namespace) -> int:
    report = pilot_collection_preflight(
        args.authority_record,
        args.sampling_frame,
        args.discovery_plan,
        args.discovery_root,
        args.selection_root,
    )
    _write_json(report, args.output)
    return 0 if report["passed"] else 2


def _collect_selected_pilot(args: argparse.Namespace) -> int:
    preflight = pilot_collection_preflight(
        args.authority_record,
        args.sampling_frame,
        args.discovery_plan,
        args.discovery_root,
        args.selection_root,
    )
    if not preflight["passed"]:
        _write_json(preflight, None)
        return 2

    frame, _ = load_registered_sampling_frame(args.sampling_frame)
    pacer = RequestPacer(args.request_interval)
    with ExitStack() as stack:
        regional_fetchers: dict[str, TimelineFetcher] = {
            route.regional_route: stack.enter_context(
                RiotMatchClient.from_environment(
                    regional_route=route.regional_route,
                    pace=pacer,
                )
            )
            for route in frame.route_platforms
        }
        binding = collect_selected_pilot_bundles(
            args.sampling_frame,
            args.discovery_plan,
            args.discovery_root,
            args.selection_root,
            output_root=args.output,
            regional_fetchers=regional_fetchers,
            max_new_requests=args.max_new_requests,
            progress=lambda message: print(message, file=sys.stderr),
        )
    _write_json(binding, None)
    return 0 if binding["complete"] else 2


def _process(args: argparse.Namespace) -> int:
    validation = validate_raw_collection(
        args.raw,
        min_routes=args.min_routes,
        min_patches=args.min_patches,
        sampling_frame=args.sampling_frame,
        sampling_stage=args.sampling_stage,
        discovery_plan=args.discovery_plan,
        discovery_root=args.discovery_root,
        selection_root=args.selection_root,
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
        sampling_frame=args.sampling_frame,
        sampling_stage=args.sampling_stage,
        discovery_plan=args.discovery_plan,
        discovery_root=args.discovery_root,
        selection_root=args.selection_root,
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


def _analyze_pilot_duration(args: argparse.Namespace) -> int:
    validation = validate_raw_collection(
        args.raw,
        min_routes=2,
        min_patches=6,
        processed_root=args.processed,
        sampling_frame=args.sampling_frame,
        sampling_stage="pilot",
        discovery_plan=args.discovery_plan,
        discovery_root=args.discovery_root,
        selection_root=args.selection_root,
    )
    if not validation["passed"]:
        _write_json(validation, None)
        return 2
    report = analyze_pilot_duration(
        args.raw,
        args.processed,
        args.sampling_frame,
    )
    _write_json(report, args.output)
    print(f"Wrote checksum-bound pilot duration analysis: {args.output}")
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

    sampling_frame = subparsers.add_parser(
        "validate-sampling-frame",
        help="validate the frozen sampling frame without making an API request",
    )
    sampling_frame.add_argument("--frame", type=Path, required=True)
    sampling_frame.add_argument("--output", type=Path)
    sampling_frame.set_defaults(handler=_validate_sampling_frame)

    discovery_plan = subparsers.add_parser(
        "validate-discovery-plan",
        help="validate the frozen candidate-discovery supplement without network access",
    )
    discovery_plan.add_argument("--plan", type=Path, required=True)
    discovery_plan.add_argument("--sampling-frame", type=Path, required=True)
    discovery_plan.add_argument("--output", type=Path)
    discovery_plan.set_defaults(handler=_validate_discovery_plan)

    discovery_preflight = subparsers.add_parser(
        "preflight-discovery",
        help="validate frame-bound authority for candidate discovery without a request",
    )
    discovery_preflight.add_argument("--authority-record", type=Path, required=True)
    discovery_preflight.add_argument("--sampling-frame", type=Path, required=True)
    discovery_preflight.add_argument("--discovery-plan", type=Path, required=True)
    discovery_preflight.add_argument("--output", type=Path)
    discovery_preflight.set_defaults(handler=_preflight_discovery)

    discover = subparsers.add_parser(
        "discover-candidates",
        help="build or resume the private, frame-bound candidate ID pool",
    )
    discover.add_argument("--authority-record", type=Path, required=True)
    discover.add_argument("--sampling-frame", type=Path, required=True)
    discover.add_argument("--discovery-plan", type=Path, required=True)
    discover.add_argument("--output", type=Path, required=True)
    discover.add_argument("--request-interval", type=float, default=1.25)
    discover.set_defaults(handler=_discover_candidates)

    candidate_pool = subparsers.add_parser(
        "validate-candidate-pool",
        help="validate the completed private candidate pool without network access",
    )
    candidate_pool.add_argument("--sampling-frame", type=Path, required=True)
    candidate_pool.add_argument("--discovery-plan", type=Path, required=True)
    candidate_pool.add_argument("--discovery-root", type=Path, required=True)
    candidate_pool.add_argument("--output", type=Path)
    candidate_pool.set_defaults(handler=_validate_candidate_pool)

    selection_preflight = subparsers.add_parser(
        "preflight-pilot-selection",
        help="validate authority and discovery bindings before detail screening",
    )
    selection_preflight.add_argument("--authority-record", type=Path, required=True)
    selection_preflight.add_argument("--sampling-frame", type=Path, required=True)
    selection_preflight.add_argument("--discovery-plan", type=Path, required=True)
    selection_preflight.add_argument("--discovery-root", type=Path, required=True)
    selection_preflight.add_argument("--output", type=Path)
    selection_preflight.set_defaults(handler=_preflight_pilot_selection)

    select_pilot = subparsers.add_parser(
        "select-pilot",
        help="screen candidate details and freeze the exact registered pilot",
    )
    select_pilot.add_argument("--authority-record", type=Path, required=True)
    select_pilot.add_argument("--sampling-frame", type=Path, required=True)
    select_pilot.add_argument("--discovery-plan", type=Path, required=True)
    select_pilot.add_argument("--discovery-root", type=Path, required=True)
    select_pilot.add_argument("--output", type=Path, required=True)
    select_pilot.add_argument("--request-interval", type=float, default=1.25)
    select_pilot.add_argument("--max-new-requests", type=int)
    select_pilot.set_defaults(handler=_select_pilot)

    validate_selection = subparsers.add_parser(
        "validate-pilot-selection",
        help="validate the checksum-bound frozen pilot selection without network access",
    )
    validate_selection.add_argument("--sampling-frame", type=Path, required=True)
    validate_selection.add_argument("--discovery-plan", type=Path, required=True)
    validate_selection.add_argument("--discovery-root", type=Path, required=True)
    validate_selection.add_argument("--selection-root", type=Path, required=True)
    validate_selection.add_argument("--output", type=Path)
    validate_selection.set_defaults(handler=_validate_pilot_selection)

    collection_preflight = subparsers.add_parser(
        "preflight-pilot-collection",
        help="validate authority and frozen selection before timeline requests",
    )
    collection_preflight.add_argument("--authority-record", type=Path, required=True)
    collection_preflight.add_argument("--sampling-frame", type=Path, required=True)
    collection_preflight.add_argument("--discovery-plan", type=Path, required=True)
    collection_preflight.add_argument("--discovery-root", type=Path, required=True)
    collection_preflight.add_argument("--selection-root", type=Path, required=True)
    collection_preflight.add_argument("--output", type=Path)
    collection_preflight.set_defaults(handler=_preflight_pilot_collection)

    collect_selected = subparsers.add_parser(
        "collect-selected-pilot",
        help="resume timeline collection for the exact frozen registered pilot",
    )
    collect_selected.add_argument("--authority-record", type=Path, required=True)
    collect_selected.add_argument("--sampling-frame", type=Path, required=True)
    collect_selected.add_argument("--discovery-plan", type=Path, required=True)
    collect_selected.add_argument("--discovery-root", type=Path, required=True)
    collect_selected.add_argument("--selection-root", type=Path, required=True)
    collect_selected.add_argument("--output", type=Path, required=True)
    collect_selected.add_argument("--request-interval", type=float, default=1.25)
    collect_selected.add_argument("--max-new-requests", type=int)
    collect_selected.set_defaults(handler=_collect_selected_pilot)

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
    validate_raw.add_argument("--sampling-frame", type=Path)
    validate_raw.add_argument("--sampling-stage", choices=("pilot", "final"))
    validate_raw.add_argument("--discovery-plan", type=Path)
    validate_raw.add_argument("--discovery-root", type=Path)
    validate_raw.add_argument("--selection-root", type=Path)
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

    duration = subparsers.add_parser(
        "analyze-pilot-duration",
        help="describe the registered pilot duration distribution without outcome inputs",
    )
    duration.add_argument("--raw", type=Path, required=True)
    duration.add_argument("--processed", type=Path, required=True)
    duration.add_argument("--sampling-frame", type=Path, required=True)
    duration.add_argument("--discovery-plan", type=Path, required=True)
    duration.add_argument("--discovery-root", type=Path, required=True)
    duration.add_argument("--selection-root", type=Path, required=True)
    duration.add_argument("--output", type=Path, required=True)
    duration.set_defaults(handler=_analyze_pilot_duration)

    process = subparsers.add_parser("process", help="normalize and label private raw bundles")
    process.add_argument("--raw", type=Path, default=Path("data/raw"))
    process.add_argument("--output", type=Path, default=Path("data/processed"))
    process.add_argument("--min-routes", type=int, default=2)
    process.add_argument("--min-patches", type=int, default=6)
    process.add_argument("--sampling-frame", type=Path)
    process.add_argument("--sampling-stage", choices=("pilot", "final"))
    process.add_argument("--discovery-plan", type=Path)
    process.add_argument("--discovery-root", type=Path)
    process.add_argument("--selection-root", type=Path)
    process.set_defaults(handler=_process)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handler = args.handler
    return int(handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
