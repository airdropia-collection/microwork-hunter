"""
RewardJoy Platform Hunter.

NOTE: RewardJoy was previously known as CoinPayu. The site was renamed
from coinpayu.com to rewardjoy.com. This adapter has been updated to
use the new domain and platform name.

RewardJoy is a PTC (paid-to-click) and offer platform that pays in
Satoshi (1 satoshi = 0.00000001 BTC). Task types:
  - PTC ads (auto-completable)
  - Offers (usually require app installs / sign-ups — filtered by task_filter)
  - Surveys (auto-completable with AI)

Backward compatibility: reads cookies from ``COOKIES_REWARDJOY`` first,
falls back to the old ``COOKIES_COINPAYU`` secret name if the new one
is not set. This lets existing users transition without re-adding secrets.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from src.config import CONFIG
from src.utils.logger import get_logger
from .base import BasePlatform, MicroworkTask

log = get_logger("platforms.rewardjoy")


class RewardJoyPlatform(BasePlatform):
    """RewardJoy (formerly CoinPayu) PTC and offer platform."""

    def __init__(self):
        super().__init__(
            name="rewardjoy",
            base_url="https://www.rewardjoy.com",
            cookies=self._load_cookies(),
        )

    @staticmethod
    def _load_cookies() -> List[Dict]:
        """Load cookies from COOKIES_REWARDJOY, falling back to COOKIES_COINPAYU."""
        import base64
        import json
        import os
        from pathlib import Path

        # Try new name first
        for env_var in ("COOKIES_REWARDJOY", "COOKIES_COINPAYU"):
            encoded = os.getenv(env_var, "")
            if encoded:
                try:
                    decoded = base64.b64decode(encoded).decode("utf-8")
                    cookies = json.loads(decoded)
                    log.info("loaded cookies from %s", env_var)
                    return cookies
                except Exception as exc:  # noqa: BLE001
                    log.error("failed to decode %s: %s", env_var, exc)

        # Try local file (new name first, then old name)
        for filename in ("rewardjoy_cookies.json", "coinpayu_cookies.json"):
            cookie_file = Path("cookies") / filename
            if cookie_file.exists():
                try:
                    cookies = json.loads(cookie_file.read_text(encoding="utf-8"))
                    log.info("loaded cookies from file %s", cookie_file)
                    return cookies
                except Exception as exc:  # noqa: BLE001
                    log.error("failed to read %s: %s", cookie_file, exc)

        log.warning("no cookies found for RewardJoy (tried COOKIES_REWARDJOY and COOKIES_COINPAYU)")
        return []

    def discover_tasks(self) -> List[MicroworkTask]:
        self.tasks = []
        try:
            self._discover_ptc_ads()
            self._discover_surveys()
        except Exception as exc:  # noqa: BLE001
            log.error("error discovering RewardJoy: %s", exc)
        return self.tasks

    # ------------------------------------------------------------------ #
    # Discovery
    # ------------------------------------------------------------------ #
    def _discover_ptc_ads(self):
        try:
            self.page.goto(f"{self.base_url}/ads", timeout=20000)
            self._human_delay(2, 4)
            self._take_screenshot("ptc_ads_page")
            ad_items = self.page.locator(
                ".ad-item, [class*='ad'], .ptc-item, .ads-item"
            ).all()

            for i, ad in enumerate(ad_items[:20]):
                try:
                    title = ad.locator(
                        ".title, h3, [class*='title']"
                    ).first.inner_text(timeout=3000)
                    reward_text = ad.locator(
                        ".reward, [class*='amount'], [class*='sat']"
                    ).first.inner_text(timeout=3000)

                    reward_match = re.search(r"[\d.]+", reward_text)
                    reward = float(reward_match.group()) if reward_match else 0.0
                    if reward < 1:
                        continue

                    duration_text = ad.locator(
                        ".duration, [class*='time']"
                    ).first.inner_text(timeout=2000)
                    duration_match = re.search(r"(\d+)", duration_text)
                    duration = int(duration_match.group()) if duration_match else 30

                    link = ad.locator("a").first.get_attribute("href") or ""
                    if link and not link.startswith("http"):
                        link = f"{self.base_url}{link}"

                    task = MicroworkTask(
                        id=f"rj_ptc_{i}_{hash(title) % 10000}",
                        platform="rewardjoy",
                        type="ptc_ad",
                        title=f"View Ad: {title.strip()[:50]}",
                        description=f"Watch ad for {duration}s - Earn {reward} satoshi",
                        reward=reward,
                        reward_currency="SATOSHI",
                        estimated_time=max(duration // 60, 1),
                        difficulty="easy",
                        url=link or f"{self.base_url}/ads",
                        requirements=["watch_full_duration", "stay_active"],
                        tags=["ptc", "ad", "quick"],
                    )
                    self.tasks.append(task)
                except Exception as exc:  # noqa: BLE001
                    log.debug("ptc item %d skipped: %s", i, exc)
                    continue
        except Exception as exc:  # noqa: BLE001
            log.error("PTC discovery error: %s", exc)

    def _discover_surveys(self):
        try:
            self.page.goto(f"{self.base_url}/surveys", timeout=20000)
            self._human_delay(2, 4)
            survey_items = self.page.locator(
                ".survey-item, [class*='survey']"
            ).all()

            for i, survey in enumerate(survey_items[:5]):
                try:
                    title = survey.locator(
                        ".title, h3"
                    ).first.inner_text(timeout=3000)
                    reward_text = survey.locator(
                        ".reward, [class*='amount']"
                    ).first.inner_text(timeout=3000)
                    reward_match = re.search(r"[\d.]+", reward_text)
                    reward = float(reward_match.group()) if reward_match else 0.0

                    time_text = survey.locator(
                        ".time, [class*='duration']"
                    ).first.inner_text(timeout=2000)
                    time_match = re.search(r"(\d+)", time_text)
                    estimated_time = int(time_match.group()) if time_match else 15

                    task = MicroworkTask(
                        id=f"rj_survey_{i}_{hash(title) % 10000}",
                        platform="rewardjoy",
                        type="survey",
                        title=f"Survey: {title.strip()[:50]}",
                        description=f"Paid survey - {reward_text}",
                        reward=reward,
                        reward_currency="SATOSHI",
                        estimated_time=estimated_time,
                        difficulty="easy",
                        url=self.page.url,
                        requirements=["honest_answers", "consistent_profile"],
                        tags=["survey", "paid"],
                    )
                    self.tasks.append(task)
                except Exception as exc:  # noqa: BLE001
                    log.debug("survey item %d skipped: %s", i, exc)
                    continue
        except Exception as exc:  # noqa: BLE001
            log.error("survey discovery error: %s", exc)

    # ------------------------------------------------------------------ #
    # Execution
    # ------------------------------------------------------------------ #
    def execute_task(self, task: MicroworkTask, dry_run: bool = True) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "task_id": task.id,
            "platform": "rewardjoy",
            "status": "pending",
            "evidence": [],
        }

        try:
            if task.type == "ptc_ad":
                return self._execute_ptc_ad(task, dry_run)
            if task.type == "survey":
                return self._execute_survey(task, dry_run)
            result["status"] = "unsupported"
            result["error"] = f"Task type {task.type} not supported"
        except Exception as exc:  # noqa: BLE001
            result["status"] = "failed"
            result["error"] = str(exc)
            log.exception("rewardjoy task %s failed: %s", task.id, exc)

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
                    f"Would watch RewardJoy ad for {task.estimated_time} min"
                )
                return result

            view_btn = self.page.locator(
                "button:has-text('View'), button:has-text('Watch'), "
                ".view-ad, [class*='watch']"
            ).first
            if view_btn.is_visible():
                view_btn.click()
                self._human_delay(1, 2)
                # Cap wait at 60s to avoid long CI runs
                wait_ms = min(task.estimated_time * 60 * 1000, 60000)
                self.page.wait_for_timeout(wait_ms)

                confirm_btn = self.page.locator(
                    "button:has-text('Confirm'), .confirm, [class*='verify']"
                ).first
                if confirm_btn.is_visible(timeout=5000):
                    confirm_btn.click()

                result["status"] = "completed"
                result["message"] = "Ad viewed and confirmed"
            else:
                result["status"] = "failed"
                result["error"] = "View button not found"

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

        result["status"] = "skipped"
        result["message"] = "Survey execution requires AI answer generation"
        return result
