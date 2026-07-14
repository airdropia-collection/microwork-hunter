"""
Task Execution Engine.

Reads ``tasks_found.json`` (a list of task dicts, as produced by
``src.hunters.discover``) and runs each task through the matching
platform adapter. Results are written as ``result_<task_id>.json``
files so that ``src.utils.review_compiler`` can pick them up.

After each task, ``TaskState.mark_done()`` is called so the next
discovery run skips it.
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
from src.utils.logger import get_logger
from src.utils.state import TaskState

log = get_logger("executor")

PLATFORM_MAP = {
    "sproutgigs": SproutGigsPlatform,
    "coinpayu": CoinPayuPlatform,
    "timebucks": TimeBucksPlatform,
    "prizerebel": PrizeRebelPlatform,
}


def _coerce_to_task_list(payload: Union[Dict, List]) -> List[Dict[str, Any]]:
    """Accept either a single task dict or a list of task dicts."""
    if isinstance(payload, dict):
        if "tasks" in payload and isinstance(payload["tasks"], list):
            return payload["tasks"]
        return [payload]
    if isinstance(payload, list):
        return payload
    raise TypeError(f"Unsupported task payload type: {type(payload).__name__}")


class TaskExecutor:
    """Run discovered tasks against their platform adapters."""

    def __init__(
        self,
        dry_run: bool = True,
        state: TaskState | None = None,
    ):
        self.dry_run = dry_run
        self.state = state

    def execute_task(self, task_json: Dict[str, Any]) -> Dict[str, Any]:
        platform_name = task_json.get("platform")
        task_id = task_json.get("id", "unknown")

        log.info("running: %s - %s", platform_name, task_id)

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
                result = platform.execute_task(task, dry_run=self.dry_run)
                # Record in dedup state
                if self.state and result.get("status") in (
                    "completed",
                    "dry_run",
                    "skipped",
                ):
                    self.state.mark_done(
                        task_id,
                        platform_name or "unknown",
                        result["status"],
                        task_json.get("reward"),
                    )
                return result
        except Exception as exc:  # noqa: BLE001
            log.exception("task %s failed: %s", task_id, exc)
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

            result_file = f"result_{task.get('id', 'unknown')}.json"
            try:
                Path(result_file).write_text(
                    json.dumps(result, indent=2, default=str), encoding="utf-8"
                )
                log.debug("saved %s", result_file)
            except Exception as exc:  # noqa: BLE001
                log.error("failed to write %s: %s", result_file, exc)
        return results

    def execute_from_file(self, task_path: str) -> List[Dict[str, Any]]:
        payload = json.loads(Path(task_path).read_text(encoding="utf-8"))
        tasks = _coerce_to_task_list(payload)
        log.info("loaded %d task(s) from %s", len(tasks), task_path)
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
    parser.add_argument(
        "--state-file",
        default="task_state.json",
        help="Path to dedup state file (default: task_state.json)",
    )
    parser.add_argument(
        "--no-state",
        action="store_true",
        help="Do not record task completions in state file",
    )
    args = parser.parse_args()

    state = None if args.no_state else TaskState(path=args.state_file)
    executor = TaskExecutor(dry_run=args.dry_run, state=state)
    results = executor.execute_from_file(args.task)

    ok = sum(
        1 for r in results if r.get("status") in ("completed", "dry_run")
    )
    log.info("%d/%d task(s) OK", ok, len(results))
    return 0 if ok == len(results) and results else (1 if not results else 2)


if __name__ == "__main__":
    sys.exit(main())
