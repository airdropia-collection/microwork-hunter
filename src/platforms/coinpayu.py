
"""
CoinPayu Platform Hunter
"""
import re
from typing import List, Dict, Any
from src.config import CONFIG
from .base import BasePlatform, MicroworkTask


class CoinPayuPlatform(BasePlatform):
    """CoinPayu PTC and offer platform"""

    def __init__(self):
        super().__init__(
            name="coinpayu",
            base_url="https://www.coinpayu.com",
            cookies=CONFIG.cookies_coinpayu
        )

    def discover_tasks(self) -> List[MicroworkTask]:
        self.tasks = []
        try:
            self._discover_ptc_ads()
            self._discover_offers()
            self._discover_surveys()
        except Exception as e:
            print(f"Error discovering CoinPayu: {e}")
        return self.tasks

    def _discover_ptc_ads(self):
        try:
            self.page.goto(f"{self.base_url}/ads", timeout=20000)
            self._human_delay(2, 4)
            ad_items = self.page.locator(".ad-item, [class*='ad'], .ptc-item").all()

            for i, ad in enumerate(ad_items[:20]):
                try:
                    title = ad.locator(".title, h3, [class*='title']").first.inner_text(timeout=3000)
                    reward_text = ad.locator(".reward, [class*='amount'], [class*='sat']").first.inner_text(timeout=3000)

                    reward_match = re.search(r'[\d.]+', reward_text)
                    reward = float(reward_match.group()) if reward_match else 0.0

                    if reward < 1:
                        continue

                    duration_text = ad.locator(".duration, [class*='time']").first.inner_text(timeout=2000)
                    duration_match = re.search(r'(\d+)', duration_text)
                    duration = int(duration_match.group()) if duration_match else 30

                    link = ad.locator("a").first.get_attribute("href") or ""

                    task = MicroworkTask(
                        id=f"cp_ptc_{i}_{hash(title) % 10000}",
                        platform="coinpayu",
                        type="ptc_ad",
                        title=f"View Ad: {title.strip()[:50]}",
                        description=f"Watch ad for {duration}s - Earn {reward} satoshi",
                        reward=reward,
                        reward_currency="SATOSHI",
                        estimated_time=max(duration // 60, 1),
                        difficulty="easy",
                        url=link if link.startswith("http") else f"{self.base_url}{link}",
                        requirements=["watch_full_duration", "stay_active"],
                        tags=["ptc", "ad", "quick"]
                    )
                    self.tasks.append(task)
                except:
                    continue
        except Exception as e:
            print(f"PTC discovery error: {e}")

    def _discover_offers(self):
        try:
            self.page.goto(f"{self.base_url}/offers", timeout=20000)
            self._human_delay(2, 4)
            offer_items = self.page.locator(".offer-item, [class*='offer']").all()

            for i, offer in enumerate(offer_items[:10]):
                try:
                    title = offer.locator(".title, h3").first.inner_text(timeout=3000)
                    reward_text = offer.locator(".reward, [class*='amount']").first.inner_text(timeout=3000)

                    reward_match = re.search(r'[\d.]+', reward_text)
                    reward = float(reward_match.group()) if reward_match else 0.0

                    if reward < 100:
                        continue

                    task = MicroworkTask(
                        id=f"cp_offer_{i}_{hash(title) % 10000}",
                        platform="coinpayu",
                        type="offer",
                        title=title.strip()[:60],
                        description=f"Complete offer - {reward_text}",
                        reward=reward,
                        reward_currency="SATOSHI",
                        estimated_time=10,
                        difficulty="medium",
                        url=self.page.url,
                        requirements=["complete_action", "proof_screenshot"],
                        tags=["offer", "high_pay"]
                    )
                    self.tasks.append(task)
                except:
                    continue
        except Exception as e:
            print(f"Offer discovery error: {e}")

    def _discover_surveys(self):
        try:
            self.page.goto(f"{self.base_url}/surveys", timeout=20000)
            self._human_delay(2, 4)
            survey_items = self.page.locator(".survey-item, [class*='survey']").all()

            for i, survey in enumerate(survey_items[:5]):
                try:
                    title = survey.locator(".title, h3").first.inner_text(timeout=3000)
                    reward_text = survey.locator(".reward, [class*='amount']").first.inner_text(timeout=3000)

                    reward_match = re.search(r'[\d.]+', reward_text)
                    reward = float(reward_match.group()) if reward_match else 0.0

                    time_text = survey.locator(".time, [class*='duration']").first.inner_text(timeout=2000)
                    time_match = re.search(r'(\d+)', time_text)
                    estimated_time = int(time_match.group()) if time_match else 15

                    task = MicroworkTask(
                        id=f"cp_survey_{i}_{hash(title) % 10000}",
                        platform="coinpayu",
                        type="survey",
                        title=f"Survey: {title.strip()[:50]}",
                        description=f"Paid survey - {reward_text}",
                        reward=reward,
                        reward_currency="SATOSHI",
                        estimated_time=estimated_time,
                        difficulty="easy",
                        url=self.page.url,
                        requirements=["honest_answers", "consistent_profile"],
                        tags=["survey", "paid"]
                    )
                    self.tasks.append(task)
                except:
                    continue
        except Exception as e:
            print(f"Survey discovery error: {e}")

    def execute_task(self, task: MicroworkTask, dry_run: bool = True) -> Dict[str, Any]:
        result = {"task_id": task.id, "platform": "coinpayu", "status": "pending", "evidence": []}

        try:
            if task.type == "ptc_ad":
                return self._execute_ptc_ad(task, dry_run)
            elif task.type == "survey":
                return self._execute_survey(task, dry_run)
            elif task.type == "offer":
                return self._execute_offer(task, dry_run)
            else:
                result["status"] = "unsupported"
                result["error"] = f"Task type {task.type} not supported"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def _execute_ptc_ad(self, task: MicroworkTask, dry_run: bool) -> Dict[str, Any]:
        result = {"task_id": task.id, "type": "ptc_ad", "status": "pending", "evidence": []}
        try:
            self.page.goto(task.url, timeout=20000)
            self._human_delay(2, 4)
            result["evidence"].append(self._take_screenshot(f"{task.id}_start"))

            if dry_run:
                result["status"] = "dry_run"
                result["message"] = f"Would watch ad for {task.estimated_time} minutes"
                return result

            view_btn = self.page.locator("button:has-text('View'), button:has-text('Watch'), .view-ad, [class*='watch']").first
            if view_btn.is_visible():
                view_btn.click()
                self._human_delay(1, 2)
                self.page.wait_for_timeout(task.estimated_time * 60 * 1000)

                confirm_btn = self.page.locator("button:has-text('Confirm'), .confirm, [class*='verify']").first
                if confirm_btn.is_visible():
                    confirm_btn.click()

                result["status"] = "completed"
                result["message"] = "Ad viewed and confirmed"
            else:
                result["status"] = "failed"
                result["error"] = "View button not found"

            result["evidence"].append(self._take_screenshot(f"{task.id}_complete"))
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def _execute_survey(self, task: MicroworkTask, dry_run: bool) -> Dict[str, Any]:
        result = {"task_id": task.id, "type": "survey", "status": "pending", "evidence": []}
        if dry_run:
            result["status"] = "dry_run"
            result["message"] = "Would complete survey with AI-generated answers"
            return result

        result["status"] = "skipped"
        result["message"] = "Survey execution requires AI answer generation"
        return result

    def _execute_offer(self, task: MicroworkTask, dry_run: bool) -> Dict[str, Any]:
        result = {"task_id": task.id, "type": "offer", "status": "pending", "evidence": []}
        if dry_run:
            result["status"] = "dry_run"
            result["message"] = "Would complete offer task"
            return result

        result["status"] = "skipped"
        result["message"] = "Offer tasks require manual review"
        return result
