"""
Task Discovery Orchestrator.

Discovers tasks from one or more platforms, ranks them by reward/time
ratio, deduplicates against ``task_state.json``, and writes the result
to ``tasks_found.json`` for the executor to consume.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from src.platforms.sproutgigs import SproutGigsPlatform
from src.platforms.coinpayu import CoinPayuPlatform
from src.platforms.timebucks import TimeBucksPlatform
from src.platforms.prizerebel import PrizeRebelPlatform
from src.utils.logger import get_logger
from src.utils.state import TaskState

log = get_logger("discover")

PLATFORM_MAP = {
    "sproutgigs": SproutGigsPlatform,
    "coinpayu": CoinPayuPlatform,
    "timebucks": TimeBucksPlatform,
    "prizerebel": PrizeRebelPlatform,
}


def discover_platform(platform_name: str, max_tasks: int = 5) -> List[Dict[str, Any]]:
    log.info("discovering tasks from %s (max=%d)", platform_name, max_tasks)
    platform_class = PLATFORM_MAP.get(platform_name)
    if not platform_class:
        log.error("unknown platform: %s", platform_name)
        return []
    try:
        with platform_class() as platform:
            tasks = platform.discover_tasks()
            tasks.sort(
                key=lambda t: t.reward / max(t.estimated_time, 1), reverse=True
            )
            tasks = tasks[:max_tasks]
            log.info("found %d task(s) on %s", len(tasks), platform_name)
            return [t.to_dict() for t in tasks]
    except Exception as exc:  # noqa: BLE001
        log.exception("error with %s: %s", platform_name, exc)
        return []


def discover_all(max_tasks_per_platform: int = 5) -> List[Dict[str, Any]]:
    all_tasks: List[Dict[str, Any]] = []
    for platform_name in PLATFORM_MAP:
        tasks = discover_platform(platform_name, max_tasks_per_platform)
        all_tasks.extend(tasks)
    all_tasks.sort(
        key=lambda t: t.get("reward", 0) / max(t.get("estimated_time", 1), 1),
        reverse=True,
    )
    return all_tasks


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover microwork tasks")
    parser.add_argument(
        "--platform",
        default="all",
        choices=["all", "sproutgigs", "coinpayu", "timebucks", "prizerebel"],
    )
    parser.add_argument("--max-tasks", type=int, default=5)
    parser.add_argument(
        "--state-file",
        default="task_state.json",
        help="Path to dedup state file (default: task_state.json)",
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Skip deduplication (re-discover already-completed tasks)",
    )
    args = parser.parse_args()

    if args.platform == "all":
        tasks = discover_all(args.max_tasks)
    else:
        tasks = discover_platform(args.platform, args.max_tasks)

    # Deduplicate against state
    if not args.no_dedup and tasks:
        state = TaskState(path=args.state_file)
        state.prune()
        before = len(tasks)
        tasks = state.filter_pending(tasks)
        log.info("dedup: %d -> %d task(s)", before, len(tasks))

    # Write outputs
    Path("tasks_found.json").write_text(
        json.dumps(tasks, indent=2, default=str), encoding="utf-8"
    )
    Path("tasks_found_count.txt").write_text(str(len(tasks)), encoding="utf-8")
    Path("discovery_log.json").write_text(
        json.dumps(
            {
                "platform": args.platform,
                "total_found": len(tasks),
                "tasks": tasks,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    log.info("total tasks discovered: %d", len(tasks))
    return 0 if tasks else 1


if __name__ == "__main__":
    sys.exit(main())
