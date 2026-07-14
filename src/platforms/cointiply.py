"""
Cointiply Platform Hunter.

Cointiply is a crypto-reward platform supporting BTC, DOGE, and LTC
payouts. It offers:
  - PTC ads (paid-to-click)
  - Surveys
  - Offerwalls (app installs, sign-ups — filtered out by task_filter)
  - Faucet claims (every hour)
  - Daily challenges

This adapter handles discovery and execution for the auto-completable
task types (PTC ads, surveys, faucet, daily). Offerwalls are filtered
out upstream by ``src.utils.task_filter``.

Payout currency: Cointiply Coins (10000 coins = $1 USD, withdrawable
as BTC/DOGE/LTC).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from src.config import CONFIG
from src.utils.logger import get_logger
from .base import BasePlatform, MicroworkTask

log = get_logger("platforms.cointiply")


class CointiplyPlatform(BasePlatform):
    """Cointiply crypto-reward platform adapter."""

    def __init__(self):
        super().__init__(
            name="cointiply",
            base_url="https://cointiply.com",
            cookies=self._load_cookies(),
        )

    @staticmethod
    def _load_cookies() -> List[Dict]:
        """Load Cointiply cookies from env or local file."""
        # Cointiply is not yet in CONFIG.cookies_* properties — read directly
        import base64
        import json
        import os
        from pathlib import Path

        encoded = os.getenv("COOKIES_COINTIPLY", "")
        if encoded:
            try:
                decoded = base64.b64decode(encoded).decode("utf-8")
                return json.loads(decoded)
            except Exception as exc:  # noqa: BLE001
                log.error("failed to decode COOKIES_COINTIPLY: %s", exc)
                return []
        # Local dev fallback
        cookie_file = Path("cookies/cointiply_cookies.json")
        if cookie_file.exists():
            try:
                return json.loads(cookie_file.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                log.error("failed to read %s: %s", cookie_file, exc)
        return []

    def discover_tasks(self) -> List[MicroworkTask]:
        """Discover available tasks across PTC, surveys, faucet, daily."""
        self.tasks = []
        try:
            self._discover_ptc_ads()
            self._discover_surveys()
            self._discover_faucet()
            self._discover_daily()
        except Exception as exc:  # noqa: BLE001
            log.error("error discovering Cointiply: %s", exc)
        return self.tasks

    # ------------------------------------------------------------------ #
    # Discovery helpers
    # ------------------------------------------------------------------ #
    def _discover_ptc_ads(self):
        """Discover PTC ads on the Cointiply ads page."""
        try:
            self.page.goto(f"{self.base_url}/pages/ptc", timeout=20000)
            self._human_delay(2, 4)
            self._log_page_info("cointiply_ptc")
            ad_items = self.page.locator(
                ".ptc-ad-item, .ad-row, [class*='ptc'], .ad-card"
            ).all()
            log.info("cointiply: found %d PTC ad item(s)", len(ad_items))

            for i, ad in enumerate(ad_items[:15]):
                try:
                    title = ad.locator(
                        ".ad-title, .title, h3, h4"
                    ).first.inner_text(timeout=3000)
                    reward_text = ad.locator(
                        ".reward, [class*='coin'], [class*='amount']"
                    ).first.inner_text(timeout=3000)

                    reward_match = re.search(r"[\d.]+", reward_text)
                    reward = float(reward_match.group()) if reward_match else 0.0
                    if reward < 1:  # less than 1 coin — skip
                        continue

                    duration_text = ad.locator(
                        ".duration, [class*='time'], [class*='seconds']"
                    ).first.inner_text(timeout=2000)
                    duration_match = re.search(r"(\d+)", duration_text)
                    duration_sec = (
                        int(duration_match.group()) if duration_match else 30
                    )

                    link = ad.locator("a").first.get_attribute("href") or ""
                    if link and not link.startswith("http"):
                        link = f"{self.base_url}{link}"

                    task = MicroworkTask(
                        id=f"cp_ptc_{i}_{hash(title) % 10000}",
                        platform="cointiply",
                        type="ptc_ad",
                        title=f"View Ad: {title.strip()[:50]}",
                        description=f"Watch Cointiply ad for {duration_sec}s - Earn {reward} coins",
                        reward=reward,
                        reward_currency="COINS",
                        estimated_time=max(duration_sec // 60, 1),
                        difficulty="easy",
                        url=link or f"{self.base_url}/pages/ptc",
                        requirements=["watch_full_duration", "stay_active"],
                        tags=["ptc", "ad", "crypto", "quick"],
                    )
                    self.tasks.append(task)
                except Exception as exc:  # noqa: BLE001
                    log.debug("ptc item %d skipped: %s", i, exc)
                    continue
        except Exception as exc:  # noqa: BLE001
            log.error("PTC discovery error: %s", exc)

    def _discover_surveys(self):
        """Discover available surveys."""
        try:
            self.page.goto(f"{self.base_url}/pages/surveys", timeout=20000)
            self._human_delay(2, 4)
            survey_items = self.page.locator(
                ".survey-item, [class*='survey'], .survey-card"
            ).all()

            for i, survey in enumerate(survey_items[:5]):
                try:
                    title = survey.locator(
                        ".title, h3, [class*='name']"
                    ).first.inner_text(timeout=3000)
                    reward_text = survey.locator(
                        ".reward, [class*='amount'], [class*='coin']"
                    ).first.inner_text(timeout=3000)
                    reward_match = re.search(r"[\d.]+", reward_text)
                    reward = float(reward_match.group()) if reward_match else 0.0
                    if reward < 100:  # less than 100 coins — skip
                        continue

                    time_text = survey.locator(
                        ".time, [class*='duration']"
                    ).first.inner_text(timeout=2000)
                    time_match = re.search(r"(\d+)", time_text)
                    est_time = int(time_match.group()) if time_match else 15

                    task = MicroworkTask(
                        id=f"cp_survey_{i}_{hash(title) % 10000}",
                        platform="cointiply",
                        type="survey",
                        title=f"Survey: {title.strip()[:50]}",
                        description=f"Cointiply survey - {reward} coins - {time_text}",
                        reward=reward,
                        reward_currency="COINS",
                        estimated_time=est_time,
                        difficulty="easy",
                        url=self.page.url,
                        requirements=["honest_answers", "consistent_profile"],
                        tags=["survey", "paid", "crypto"],
                    )
                    self.tasks.append(task)
                except Exception as exc:  # noqa: BLE001
                    log.debug("survey item %d skipped: %s", i, exc)
                    continue
        except Exception as exc:  # noqa: BLE001
            log.error("survey discovery error: %s", exc)

    def _discover_faucet(self):
        """The Cointiply faucet — claimable every hour."""
        try:
            self.page.goto(f"{self.base_url}/pages/faucet", timeout=20000)
            self._human_delay(2, 4)
            # Check if faucet is claimable (button enabled / countdown done)
            claim_btn = self.page.locator(
                "button:has-text('Roll'), button:has-text('Claim'), "
                "button:has-text('Free Coins'), .faucet-claim"
            ).first
            try:
                is_enabled = claim_btn.is_enabled(timeout=3000)
            except Exception:  # noqa: BLE001
                is_enabled = False

            if is_enabled:
                task = MicroworkTask(
                    id="cp_faucet_hourly",
                    platform="cointiply",
                    type="faucet",
                    title="Hourly Faucet Roll",
                    description="Claim free coins from the Cointiply faucet (every hour)",
                    reward=50,  # average payout ~50 coins
                    reward_currency="COINS",
                    estimated_time=1,
                    difficulty="easy",
                    url=f"{self.base_url}/pages/faucet",
                    requirements=["click_roll_button"],
                    tags=["faucet", "hourly", "free", "crypto"],
                )
                self.tasks.append(task)
        except Exception as exc:  # noqa: BLE001
            log.error("faucet discovery error: %s", exc)

    def _discover_daily(self):
        """Daily login bonus."""
        try:
            self.page.goto(f"{self.base_url}/dashboard", timeout=20000)
            self._human_delay(2, 4)
            daily_btn = self.page.locator(
                "button:has-text('Daily Bonus'), "
                "button:has-text('Daily Reward'), "
                ".daily-bonus, [class*='daily-claim']"
            ).first
            try:
                is_visible = daily_btn.is_visible(timeout=3000)
            except Exception:  # noqa: BLE001
                is_visible = False

            if is_visible:
                task = MicroworkTask(
                    id="cp_daily_bonus",
                    platform="cointiply",
                    type="daily_bonus",
                    title="Daily Login Bonus",
                    description="Claim daily login bonus on Cointiply",
                    reward=100,  # average ~100 coins
                    reward_currency="COINS",
                    estimated_time=1,
                    difficulty="easy",
                    url=f"{self.base_url}/dashboard",
                    requirements=["click_claim_button"],
                    tags=["daily", "bonus", "login", "crypto"],
                )
                self.tasks.append(task)
        except Exception as exc:  # noqa: BLE001
            log.error("daily discovery error: %s", exc)

    # ------------------------------------------------------------------ #
    # Task execution
    # ------------------------------------------------------------------ #
    def execute_task(self, task: MicroworkTask, dry_run: bool = True) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "task_id": task.id,
            "platform": "cointiply",
            "status": "pending",
            "evidence": [],
        }

        try:
            if task.type == "ptc_ad":
                return self._execute_ptc_ad(task, dry_run)
            if task.type == "faucet":
                return self._execute_faucet(task, dry_run)
            if task.type == "daily_bonus":
                return self._execute_daily_bonus(task, dry_run)
            if task.type == "survey":
                return self._execute_survey(task, dry_run)
            result["status"] = "unsupported"
            result["error"] = f"Task type {task.type} not supported"
        except Exception as exc:  # noqa: BLE001
            result["status"] = "failed"
            result["error"] = str(exc)
            log.exception("cointiply task %s failed: %s", task.id, exc)

        return result

    def _execute_ptc_ad(self, task: MicroworkTask, dry_run: bool) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "task_id": task.id,
            "type": "ptc_ad",
            "status": "pending",
            "evidence": [],
        }
        try:
            self.page.goto(task.url, timeout=20000)
            self._human_delay(2, 4)
            result["evidence"].append(self._take_screenshot(f"{task.id}_start"))

            if dry_run:
                result["status"] = "dry_run"
                result["message"] = (
                    f"Would watch Cointiply ad for {task.estimated_time} min"
                )
                return result

            # Click the "View" / "Start" button
            view_btn = self.page.locator(
                "button:has-text('View'), button:has-text('Start'), "
                "button:has-text('Watch'), .view-ad, [class*='start-ad']"
            ).first
            if view_btn.is_visible():
                view_btn.click()
                self._human_delay(1, 2)
                # Wait for required duration
                wait_ms = task.estimated_time * 60 * 1000
                self.page.wait_for_timeout(min(wait_ms, 60000))  # cap at 60s for safety

                # Look for confirmation
                confirm_btn = self.page.locator(
                    "button:has-text('Confirm'), "
                    "button:has-text('Done'), "
                    "button:has-text('Claim'), "
                    ".confirm, [class*='verify']"
                ).first
                if confirm_btn.is_visible(timeout=5000):
                    confirm_btn.click()
                    self._human_delay(1, 2)

                result["status"] = "completed"
                result["message"] = "Ad viewed and confirmed"
            else:
                result["status"] = "failed"
                result["error"] = "View button not found"

            result["evidence"].append(self._take_screenshot(f"{task.id}_complete"))
        except Exception as exc:  # noqa: BLE001
            result["status"] = "failed"
            result["error"] = str(exc)
            log.exception("ptc ad %s failed: %s", task.id, exc)

        return result

    def _execute_faucet(self, task: MicroworkTask, dry_run: bool) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "task_id": task.id,
            "type": "faucet",
            "status": "pending",
            "evidence": [],
        }
        try:
            self.page.goto(task.url, timeout=20000)
            self._human_delay(2, 4)
            result["evidence"].append(self._take_screenshot(f"{task.id}_start"))

            if dry_run:
                result["status"] = "dry_run"
                result["message"] = "Would click faucet roll button"
                return result

            roll_btn = self.page.locator(
                "button:has-text('Roll'), button:has-text('Claim'), "
                "button:has-text('Free Coins'), .faucet-claim"
            ).first
            if roll_btn.is_visible():
                roll_btn.click()
                self._human_delay(3, 5)
                result["status"] = "completed"
                result["message"] = "Faucet rolled"
            else:
                result["status"] = "skipped"
                result["message"] = "Faucet not yet claimable (cooldown)"

            result["evidence"].append(self._take_screenshot(f"{task.id}_complete"))
        except Exception as exc:  # noqa: BLE001
            result["status"] = "failed"
            result["error"] = str(exc)
        return result

    def _execute_daily_bonus(
        self, task: MicroworkTask, dry_run: bool
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "task_id": task.id,
            "type": "daily_bonus",
            "status": "pending",
            "evidence": [],
        }
        try:
            self.page.goto(task.url, timeout=20000)
            self._human_delay(2, 4)
            result["evidence"].append(self._take_screenshot(f"{task.id}_start"))

            if dry_run:
                result["status"] = "dry_run"
                result["message"] = "Would claim daily bonus"
                return result

            claim_btn = self.page.locator(
                "button:has-text('Daily Bonus'), "
                "button:has-text('Daily Reward'), "
                "button:has-text('Claim'), "
                ".daily-bonus, [class*='daily-claim']"
            ).first
            if claim_btn.is_visible():
                claim_btn.click()
                self._human_delay(2, 4)
                result["status"] = "completed"
                result["message"] = "Daily bonus claimed"
            else:
                result["status"] = "skipped"
                result["message"] = "Daily bonus already claimed today"

            result["evidence"].append(self._take_screenshot(f"{task.id}_complete"))
        except Exception as exc:  # noqa: BLE001
            result["status"] = "failed"
            result["error"] = str(exc)
        return result

    def _execute_survey(self, task: MicroworkTask, dry_run: bool) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "task_id": task.id,
            "type": "survey",
            "status": "pending",
            "evidence": [],
        }
        if dry_run:
            result["status"] = "dry_run"
            result["message"] = "Would complete survey with AI-generated answers"
            return result
        # Real survey execution requires AI answer generation — same as
        # other platform adapters. Mark as skipped for now.
        result["status"] = "skipped"
        result["message"] = "Survey execution requires AI answer generation"
        return result
