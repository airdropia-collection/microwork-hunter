"""
Task Discovery Orchestrator.

Discovers tasks from one or more platforms, ranks them by reward/time
ratio, applies the smart task filter (to reject tasks that require
manual user action), deduplicates against ``task_state.json``, and
writes the result to ``tasks_found.json`` for the executor to consume.

Each allowed task is also saved as an individual JSON file under
``tasks_queue/`` so the bot can pick them up one-by-one.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.platforms.sproutgigs import SproutGigsPlatform
from src.platforms.coinpayu import CoinPayuPlatform
from src.platforms.timebucks import TimeBucksPlatform
from src.platforms.prizerebel import PrizeRebelPlatform
from src.utils.logger import get_logger
from src.utils.state import TaskState
from src.utils.task_filter import TaskFilter

log = get_logger("discover")

PLATFORM_MAP = {
    "sproutgigs": SproutGigsPlatform,
    "coinpayu": CoinPayuPlatform,
    "timebucks": TimeBucksPlatform,
    "prizerebel": PrizeRebelPlatform,
}

TASKS_QUEUE_DIR = Path("tasks_queue")


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


def save_task_to_queue(task: Dict[str, Any]) -> Path:
    """Save a single task as an individual JSON file in tasks_queue/."""
    TASKS_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    task_id = task.get("id", "unknown")
    # Sanitize filename: replace non-alphanumerics with underscore
    safe_id = "".join(c if c.isalnum() else "_" for c in task_id)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_id}_{ts}.json"
    path = TASKS_QUEUE_DIR / filename
    path.write_text(json.dumps(task, indent=2, default=str), encoding="utf-8")
    return path


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
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Skip smart task filter (allow manual-intervention tasks)",
    )
    parser.add_argument(
        "--no-queue",
        action="store_true",
        help="Do not save individual task files to tasks_queue/",
    )
    args = parser.parse_args()

    if args.platform == "all":
        tasks = discover_all(args.max_tasks)
    else:
        tasks = discover_platform(args.platform, args.max_tasks)

    log.info("discovered %d raw task(s)", len(tasks))

    # 1. Smart task filter — reject manual-intervention tasks
    rejected_count = 0
    if not args.no_filter and tasks:
        f = TaskFilter()
        tasks, rejected = f.filter_many(tasks)
        rejected_count = len(rejected)
        if rejected:
            log.info("filter rejected %d task(s):", rejected_count)
            for r in rejected:
                log.info(
                    "  - %s [%s]: %s",
                    r.get("id", "?"),
                    r.get("platform", "?"),
                    r["_filter"]["reason"],
                )

    # 2. Deduplicate against state
    if not args.no_dedup and tasks:
        state = TaskState(path=args.state_file)
        state.prune()
        before = len(tasks)
        tasks = state.filter_pending(tasks)
        log.info("dedup: %d -> %d task(s)", before, len(tasks))

    # 3. Save each task to tasks_queue/ folder
    if not args.no_queue and tasks:
        for task in tasks:
            save_task_to_queue(task)
        log.info("saved %d task file(s) to %s", len(tasks), TASKS_QUEUE_DIR)

    # 4. Write summary files for the executor + GitHub Issue
    Path("tasks_found.json").write_text(
        json.dumps(tasks, indent=2, default=str), encoding="utf-8"
    )
    Path("tasks_found_count.txt").write_text(str(len(tasks)), encoding="utf-8")
    Path("discovery_log.json").write_text(
        json.dumps(
            {
                "platform": args.platform,
                "total_found": len(tasks),
                "rejected_by_filter": rejected_count,
                "tasks": tasks,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    log.info(
        "final: %d task(s) queued (rejected %d by filter)",
        len(tasks),
        rejected_count,
    )
    return 0 if tasks else 1


if __name__ == "__main__":
    sys.exit(main())
