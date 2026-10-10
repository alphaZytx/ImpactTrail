from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from impacttrail.config import get_settings
from impacttrail.ingestion.bluesky import BlueskyAdapter
from impacttrail.ingestion.gdelt import GdeltAdapter
from impacttrail.ingestion.replay import ReplayAdapter
from impacttrail.services.factory import get_pipeline, get_repository


def _doctor() -> int:
    settings = get_settings()
    checks = {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "python_supported": (sys.version_info.major, sys.version_info.minor) == (3, 11),
        "taxonomy": settings.taxonomy_path.exists(),
        "scenarios": settings.scenarios_path.exists(),
        "companies": settings.companies_path.exists(),
        "portfolio": settings.portfolio_path.exists(),
        "demo_fixture": (settings.project_root / "data/demo/mixed_source_events.jsonl").exists(),
        "database": True,
    }
    repository = get_repository()
    repository.init_schema()
    pipeline = get_pipeline()
    checks["sentiment_backend"] = getattr(pipeline.sentiment_analyzer, "backend", "unknown")
    checks["event_backend"] = pipeline.event_classifier.backend
    checks["ready"] = all(value for key, value in checks.items() if isinstance(value, bool))
    print(json.dumps(checks, indent=2))
    return 0 if checks["ready"] else 1


async def _replay(path: Path) -> int:
    summary = await get_pipeline().process_adapter(ReplayAdapter(path))
    print(json.dumps(summary.as_dict(), indent=2))
    return 0 if summary.failed == 0 else 1


async def _live(query: str) -> int:
    pipeline = get_pipeline()
    summaries = {}
    for adapter in (GdeltAdapter(), BlueskyAdapter()):
        summaries[adapter.name] = (await pipeline.process_adapter(adapter, query)).as_dict()
    print(json.dumps(summaries, indent=2))
    return 0 if all(summary["failed"] == 0 for summary in summaries.values()) else 1


async def _watch(query: str, interval_seconds: int, iterations: int) -> int:
    """Poll live sources continuously, or for a bounded number of demo iterations."""
    iteration = 0
    while iterations == 0 or iteration < iterations:
        iteration += 1
        print(f"Live ingestion iteration {iteration}", flush=True)
        result = await _live(query)
        if result != 0:
            return result
        if iterations == 0 or iteration < iterations:
            await asyncio.sleep(interval_seconds)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="impacttrail")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="Validate local data, configuration, and model readiness")
    replay = subparsers.add_parser("replay", help="Process a deterministic JSONL fixture")
    replay.add_argument("--fixture", default="data/demo/mixed_source_events.jsonl")
    live = subparsers.add_parser("live", help="Fetch one batch from GDELT and Bluesky")
    live.add_argument("--query", default="financial markets")
    watch = subparsers.add_parser("watch", help="Continuously poll GDELT and Bluesky")
    watch.add_argument("--query", default="financial markets")
    watch.add_argument(
        "--interval-seconds",
        type=int,
        default=None,
        help="Defaults to IMPACTTRAIL_POLL_INTERVAL_SECONDS (300 seconds)",
    )
    watch.add_argument("--iterations", type=int, default=0, help="0 runs until interrupted")
    reset = subparsers.add_parser("reset", help="Clear runtime database records")
    reset.add_argument("--yes", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()
    if args.command == "doctor":
        raise SystemExit(_doctor())
    if args.command == "replay":
        fixture = Path(args.fixture)
        if not fixture.is_absolute():
            fixture = settings.project_root / fixture
        raise SystemExit(asyncio.run(_replay(fixture)))
    if args.command == "live":
        raise SystemExit(asyncio.run(_live(args.query)))
    if args.command == "watch":
        interval_seconds = args.interval_seconds or settings.poll_interval_seconds
        if interval_seconds < 15:
            print("--interval-seconds must be at least 15", file=sys.stderr)
            raise SystemExit(2)
        if args.iterations < 0:
            print("--iterations must be non-negative", file=sys.stderr)
            raise SystemExit(2)
        raise SystemExit(asyncio.run(_watch(args.query, interval_seconds, args.iterations)))
    if args.command == "reset":
        if not args.yes:
            print("Refusing to clear runtime data without --yes", file=sys.stderr)
            raise SystemExit(2)
        get_repository().clear_runtime()
        print("Runtime data cleared.")


if __name__ == "__main__":
    main()
