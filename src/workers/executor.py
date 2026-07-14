"""
Task Execution Engine

Reads ``tasks_found.json`` (a list of task dicts, as produced by
``src.hunters.discover``) and runs each task through the matching
platform adapter. Results are written as ``result_<task_id>.json``
files so that ``src.utils.review_compiler`` can pick them up.

Usage
-----
    python -m src.workers.executor --task tasks_found.json --dry-run true
    python -m src.workers.executor --task result_pending.json --dry-run false
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

from src.platforms.sproutgigs import SproutGigsPlatform
from src.platforms.coinpayu import CoinPayuPlatform
from src.platforms.timebucks import TimeBucksPlatform
from src.platforms.prizerebel import PrizeRebelPlatform
from src.platforms.base import MicroworkTask


PLATFORM_MAP = {
    "sproutgigs": SproutGigsPlatform,
    "coinpayu": CoinPayuPlatform,
    "timebucks": TimeBucksPlatform,
    "prizerebel": PrizeRebelPlatform,
}


def _coerce_to_task_list(payload: Union[Dict, List]) -> List[Dict[str, Any]]:
    """Accept either a single task dict or a list of task dicts."""
    if isinstance(payload, dict):
        # Be permissive: a dict that *contains* a list under "tasks"
        if "tasks" in payload and isinstance(payload["tasks"], list):
            return payload["tasks"]
        return [payload]
    if isinstance(payload, list):
        return payload
    raise TypeError(f"Unsupported task payload type: {type(payload).__name__}")


class TaskExecutor:
    """Run discovered tasks against their platform adapters."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def execute_task(self, task_json: Dict[str, Any]) -> Dict[str, Any]:
        platform_name = task_json.get("platform")
        task_id = task_json.get("id", "unknown")

        print(f"[executor] running: {platform_name} - {task_id}")

        platform_class = PLATFORM_MAP.get(platform_name)
        if not platform_class:
            return {
                "task_id": task_id,
                "platform": platform_name,
                "status": "error",
                "error": f"Unknown platform: {platform_name}",
            }

        try:
            with platform_class() as platform:
                task = MicroworkTask(**task_json)
                return platform.execute_task(task, dry_run=self.dry_run)
        except Exception as exc:  # noqa: BLE001
            return {
                "task_id": task_id,
                "platform": platform_name,
                "status": "failed",
                "error": str(exc),
            }

    def execute_many(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for task in tasks:
            result = self.execute_task(task)
            results.append(result)

            # Persist per-task result so review_compiler can find it
            result_file = f"result_{task.get('id', 'unknown')}.json"
            try:
                Path(result_file).write_text(
                    json.dumps(result, indent=2, default=str), encoding="utf-8"
                )
                print(f"[executor] saved {result_file}")
            except Exception as exc:  # noqa: BLE001
                print(f"[executor] failed to write {result_file}: {exc}")
        return results

    def execute_from_file(self, task_path: str) -> List[Dict[str, Any]]:
        payload = json.loads(Path(task_path).read_text(encoding="utf-8"))
        tasks = _coerce_to_task_list(payload)
        print(f"[executor] loaded {len(tasks)} task(s) from {task_path}")
        return self.execute_many(tasks)


# ---------------------------------------------------------------------- #
# CLI
# ---------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description="Execute microwork tasks")
    parser.add_argument(
        "--task",
        required=True,
        help="Path to JSON file with a single task dict or a list of tasks",
    )
    parser.add_argument(
        "--dry-run",
        type=lambda x: str(x).lower() == "true",
        default=True,
        help="true=dry-run (default), false=real submission",
    )
    args = parser.parse_args()

    executor = TaskExecutor(dry_run=args.dry_run)
    results = executor.execute_from_file(args.task)

    ok = sum(
        1
        for r in results
        if r.get("status") in ("completed", "dry_run")
    )
    print(f"\n[executor] {ok}/{len(results)} task(s) OK")

    return 0 if ok == len(results) and results else (1 if not results else 2)


if __name__ == "__main__":
    sys.exit(main())
