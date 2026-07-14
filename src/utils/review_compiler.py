"""
Review Compiler.

Reads ``result_*.json`` files produced by the executor and assembles
a single ``review_package.json`` for the GitHub Issue / review bot.
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

from src.utils.logger import get_logger

log = get_logger("review_compiler")


def compile_review_package() -> dict:
    result_files = glob.glob("result_*.json")
    pending: list[dict] = []
    completed: list[dict] = []
    failed: list[dict] = []

    for rf in result_files:
        try:
            result = json.loads(Path(rf).read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            log.warning("could not read %s: %s", rf, exc)
            continue
        status = result.get("status", "unknown")
        if status == "dry_run":
            pending.append(result)
        elif status == "completed":
            completed.append(result)
        elif status == "failed":
            failed.append(result)

    discovered = 0
    try:
        log_data = json.loads(Path("discovery_log.json").read_text(encoding="utf-8"))
        discovered = log_data.get("total_found", 0)
    except Exception:  # noqa: BLE001
        pass

    package = {
        "discovered": discovered,
        "attempted": len(result_files),
        "successful": len(completed),
        "failed": len(failed),
        "pending": pending,
        "completed": completed,
        "failed_tasks": failed,
        "summary": (
            f"{len(pending)} pending, {len(completed)} completed, "
            f"{len(failed)} failed"
        ),
    }

    Path("review_package.json").write_text(
        json.dumps(package, indent=2, default=str), encoding="utf-8"
    )
    log.info("review package: %s", package["summary"])
    return package


if __name__ == "__main__":
    compile_review_package()
