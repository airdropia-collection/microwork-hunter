"""
Earnings Tracker.

Aggregates per-task result files into a persistent ``earnings.json``
so we can see total earnings across all platforms and currencies.
"""
from __future__ import annotations

import argparse
import glob
import json
from datetime import datetime, timezone
from pathlib import Path

from src.utils.logger import get_logger

log = get_logger("earnings")


class EarningsTracker:
    def __init__(self, data_file: str | Path = "earnings.json"):
        self.data_file = Path(data_file)
        self.data: dict = self._load()

    def _load(self) -> dict:
        if self.data_file.exists():
            try:
                return json.loads(self.data_file.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                log.warning("could not parse %s, starting fresh: %s", self.data_file, exc)
        return {
            "total_earnings_usd": 0.0,
            "total_earnings_satoshi": 0,
            "total_earnings_points": 0,
            "platforms": {},
            "history": [],
        }

    def update(self) -> None:
        for result_file in glob.glob("result_*.json"):
            try:
                result = json.loads(Path(result_file).read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                log.warning("could not read %s: %s", result_file, exc)
                continue
            if result.get("status") not in ("completed", "dry_run"):
                continue

            platform = result.get("platform", "unknown")
            platform_entry = self.data["platforms"].setdefault(
                platform,
                {
                    "tasks_completed": 0,
                    "total_earned": 0.0,
                    "currency": "USD",
                },
            )
            platform_entry["tasks_completed"] += 1
            # We don't have ground-truth payout yet — increment by task.reward
            # (real payout confirmation happens later via platform dashboard)
            reward = result.get("reward") or 0
            try:
                platform_entry["total_earned"] += float(reward)
            except (TypeError, ValueError):
                pass

            # Update global counters by currency
            currency = result.get("reward_currency") or platform_entry.get("currency", "USD")
            if currency == "USD":
                try:
                    self.data["total_earnings_usd"] += float(reward)
                except (TypeError, ValueError):
                    pass
            elif currency == "SATOSHI":
                try:
                    self.data["total_earnings_satoshi"] += int(float(reward))
                except (TypeError, ValueError):
                    pass
            elif currency == "POINTS":
                try:
                    self.data["total_earnings_points"] += int(float(reward))
                except (TypeError, ValueError):
                    pass

        self.data["history"].append(
            {
                "date": datetime.now(timezone.utc).isoformat(),
                "total_earnings_usd": self.data["total_earnings_usd"],
                "total_earnings_satoshi": self.data["total_earnings_satoshi"],
                "total_earnings_points": self.data["total_earnings_points"],
                "platforms": json.loads(json.dumps(self.data["platforms"])),
            }
        )

        self.data_file.write_text(
            json.dumps(self.data, indent=2, default=str), encoding="utf-8"
        )
        log.info(
            "earnings updated: $%.2f USD, %d sat, %d pts",
            self.data["total_earnings_usd"],
            self.data["total_earnings_satoshi"],
            self.data["total_earnings_points"],
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()

    tracker = EarningsTracker()
    if args.update:
        tracker.update()

    print(f"Total USD    : ${tracker.data['total_earnings_usd']:.2f}")
    print(f"Total Satoshi: {tracker.data['total_earnings_satoshi']}")
    print(f"Total Points : {tracker.data['total_earnings_points']}")
    for platform, data in tracker.data["platforms"].items():
        print(f"  {platform}: {data['tasks_completed']} tasks | {data['total_earned']} {data['currency']}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
