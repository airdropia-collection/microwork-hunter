"""
Review Handler

Parses reviewer commands from GitHub Issue comments and dispatches
the corresponding action against the pending tasks stored in
``review_package.json`` (produced by ``src.utils.review_compiler``).

Supported commands (case-insensitive):

    /approve all                       -> submit every pending task
    /approve <task-id> [<task-id>...]  -> submit only listed tasks
    /reject  <task-id> [<reason>]      -> mark task as rejected
    /modify  <task-id> <instructions>  -> request re-execution with notes
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ReviewHandler:
    """Dispatch reviewer commands against pending tasks."""

    def __init__(self, package_path: str | Path = "review_package.json"):
        self.package_path = Path(package_path)
        self.package: Dict[str, Any] = self._load_package()

    # ------------------------------------------------------------------ #
    # Package loading
    # ------------------------------------------------------------------ #
    def _load_package(self) -> Dict[str, Any]:
        if not self.package_path.exists():
            return {
                "discovered": 0,
                "attempted": 0,
                "successful": 0,
                "failed": 0,
                "pending": [],
                "completed": [],
                "failed_tasks": [],
                "summary": "no review package",
            }
        try:
            return json.loads(self.package_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"[review_handler] could not parse package: {exc}")
            return {"pending": [], "completed": [], "failed_tasks": []}

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def process_comment(
        self, comment: str, commenter: str, issue_number: int
    ) -> Dict[str, Any]:
        comment = comment.strip()
        cmd = comment.lower()

        if cmd.startswith("/approve"):
            return self._handle_approve(comment, commenter, issue_number)
        if cmd.startswith("/reject"):
            return self._handle_reject(comment, commenter, issue_number)
        if cmd.startswith("/modify"):
            return self._handle_modify(comment, commenter, issue_number)
        return {
            "status": "ignored",
            "summary": f"Unrecognized command from @{commenter}",
            "action": "noop",
        }

    # ------------------------------------------------------------------ #
    # Command handlers
    # ------------------------------------------------------------------ #
    def _handle_approve(
        self, comment: str, commenter: str, issue_number: int
    ) -> Dict[str, Any]:
        parts = comment.split()
        # parts[0] == "/approve"
        if len(parts) == 2 and parts[1].lower() == "all":
            tasks = self._pending_tasks()
            return {
                "status": "approved",
                "scope": "all",
                "commenter": commenter,
                "issue": issue_number,
                "task_ids": [t.get("task_id") or t.get("id") for t in tasks],
                "tasks": tasks,
                "summary": f"All {len(tasks)} pending task(s) approved by @{commenter}",
                "action": "submit_all",
            }

        task_ids = [p for p in parts[1:] if p]
        if not task_ids:
            return {
                "status": "error",
                "summary": "`/approve` requires `all` or one or more task IDs",
                "action": "noop",
            }
        tasks = [self._find_pending(tid) for tid in task_ids]
        missing = [tid for tid, t in zip(task_ids, tasks) if t is None]
        found = [t for t in tasks if t]
        joined = ", ".join(task_ids)
        summary = f"Approved by @{commenter}: {joined}"
        if missing:
            summary += f" (not found: {', '.join(missing)})"
        return {
            "status": "approved",
            "scope": "specific",
            "commenter": commenter,
            "issue": issue_number,
            "task_ids": task_ids,
            "tasks": found,
            "missing": missing,
            "summary": summary,
            "action": "submit_specific",
        }

    def _handle_reject(
        self, comment: str, commenter: str, issue_number: int
    ) -> Dict[str, Any]:
        parts = comment.split(" ", 2)
        if len(parts) < 2:
            return {
                "status": "error",
                "summary": "`/reject` requires a task ID",
                "action": "noop",
            }
        task_id = parts[1]
        reason = parts[2].strip() if len(parts) > 2 else "No reason provided"
        task = self._find_pending(task_id)
        return {
            "status": "rejected",
            "task_id": task_id,
            "reason": reason,
            "commenter": commenter,
            "issue": issue_number,
            "task": task,
            "summary": f"Rejected {task_id} by @{commenter}: {reason}",
            "action": "reject",
        }

    def _handle_modify(
        self, comment: str, commenter: str, issue_number: int
    ) -> Dict[str, Any]:
        parts = comment.split(" ", 2)
        if len(parts) < 3:
            return {
                "status": "error",
                "summary": "`/modify` requires a task ID and instructions",
                "action": "noop",
            }
        task_id = parts[1]
        instructions = parts[2].strip()
        task = self._find_pending(task_id)
        return {
            "status": "modify",
            "task_id": task_id,
            "instructions": instructions,
            "commenter": commenter,
            "issue": issue_number,
            "task": task,
            "summary": f"Modify {task_id} by @{commenter}: {instructions}",
            "action": "modify",
        }

    # ------------------------------------------------------------------ #
    # Task lookup
    # ------------------------------------------------------------------ #
    def _pending_tasks(self) -> List[Dict[str, Any]]:
        return list(self.package.get("pending", []))

    def _find_pending(self, task_id: str) -> Optional[Dict[str, Any]]:
        for task in self._pending_tasks():
            if task.get("task_id") == task_id or task.get("id") == task_id:
                return task
        return None


# ---------------------------------------------------------------------- #
# CLI
# ---------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description="Process a reviewer comment")
    parser.add_argument("--comment", required=True, help="Raw comment body")
    parser.add_argument("--commenter", required=True, help="GitHub username")
    parser.add_argument("--issue", required=True, type=int, help="Issue number")
    parser.add_argument(
        "--package",
        default="review_package.json",
        help="Path to review_package.json (default: review_package.json)",
    )
    args = parser.parse_args()

    handler = ReviewHandler(package_path=args.package)
    result = handler.process_comment(args.comment, args.commenter, args.issue)

    Path("review_result.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, default=str))

    # Exit 0 for actionable commands, 1 for errors/ignored
    return 0 if result.get("status") in ("approved", "rejected", "modify") else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
