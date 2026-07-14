"""
Task deduplication state.

Keeps a small JSON file (``task_state.json``) of every task ID we've
already executed in the last N hours, so we don't waste time / risk
account bans by re-running the same task twice.

The state file is read once at construction and written on every
``mark_done()``. Format:

    {
      "tasks": {
        "<task_id>": {
          "platform": "sproutgigs",
          "completed_at": "2026-07-14T07:23:11Z",
          "status": "dry_run",
          "reward": 0.5
        },
        ...
      },
      "updated_at": "2026-07-14T07:23:11Z"
    }
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional

from src.utils.logger import get_logger

log = get_logger("state")

DEFAULT_STATE_FILE = "task_state.json"
DEFAULT_TTL_HOURS = 24


class TaskState:
    """Persistent record of executed tasks, with TTL-based expiry."""

    def __init__(
        self,
        path: str | Path = DEFAULT_STATE_FILE,
        ttl_hours: int = DEFAULT_TTL_HOURS,
    ):
        self.path = Path(path)
        self.ttl = timedelta(hours=ttl_hours)
        self._data: Dict[str, dict] = self._load()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def _load(self) -> Dict[str, dict]:
        if not self.path.exists():
            return {"tasks": {}}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            log.warning("could not parse %s, starting fresh: %s", self.path, exc)
            return {"tasks": {}}

    def _save(self) -> None:
        self._data["updated_at"] = datetime.now(timezone.utc).isoformat()
        try:
            self.path.write_text(
                json.dumps(self._data, indent=2, default=str), encoding="utf-8"
            )
        except Exception as exc:  # noqa: BLE001
            log.error("could not write state file %s: %s", self.path, exc)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def is_done(self, task_id: str) -> bool:
        """Return True if ``task_id`` was completed within the TTL window."""
        entry = self._data.get("tasks", {}).get(task_id)
        if not entry:
            return False
        try:
            ts = datetime.fromisoformat(entry["completed_at"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            age = datetime.now(timezone.utc) - ts
            if age > self.ttl:
                log.debug("task %s expired (age=%s)", task_id, age)
                return False
            return True
        except Exception:  # noqa: BLE001
            return False

    def mark_done(
        self,
        task_id: str,
        platform: str,
        status: str,
        reward: Optional[float] = None,
    ) -> None:
        """Record that ``task_id`` has been processed."""
        tasks = self._data.setdefault("tasks", {})
        tasks[task_id] = {
            "platform": platform,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "reward": reward,
        }
        self._save()
        log.info("marked %s as %s on %s", task_id, status, platform)

    def filter_pending(self, tasks: list[dict]) -> list[dict]:
        """Return only the tasks that haven't been done within TTL."""
        fresh = []
        skipped = 0
        for t in tasks:
            tid = t.get("id")
            if tid and self.is_done(tid):
                skipped += 1
                continue
            fresh.append(t)
        if skipped:
            log.info("skipped %d already-completed task(s)", skipped)
        return fresh

    def prune(self) -> int:
        """Remove all entries older than TTL. Returns count pruned."""
        now = datetime.now(timezone.utc)
        tasks = self._data.get("tasks", {})
        before = len(tasks)
        kept = {}
        for tid, entry in tasks.items():
            try:
                ts = datetime.fromisoformat(entry["completed_at"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if now - ts <= self.ttl:
                    kept[tid] = entry
            except Exception:  # noqa: BLE001
                # Keep entries we can't parse — safer than dropping
                kept[tid] = entry
        pruned = before - len(kept)
        self._data["tasks"] = kept
        if pruned:
            self._save()
            log.info("pruned %d stale entries from state", pruned)
        return pruned
