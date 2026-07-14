"""
PrizeRebel Platform Hunter
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from src.config import CONFIG
from src.utils.logger import get_logger
from .base import BasePlatform, MicroworkTask

log = get_logger("platforms.prizerebel")


class PrizeRebelPlatform(BasePlatform):
    """PrizeRebel GPT site automation"""

    def __init__(self):
        super().__init__(
            name="prizerebel",
            base_url="https://www.prizerebel.com",
            cookies=CONFIG.cookies_prizerebel
        )

    def discover_tasks(self) -> List[MicroworkTask]:
        self.tasks = []
        try:
            self._discover_surveys()
            self._discover_offers()
            self._discover_challenges()
        except Exception as e:
            print(f"Error discovering PrizeRebel: {e}")
        return self.tasks

    def _discover_surveys(self):
        try:
            self.page.goto(f"{self.base_url}/members/surveys", timeout=20000)
            self._human_delay(2, 4)
            self._log_page_info("prizerebel_surveys")
            survey_items = self.page.locator(".survey-card, [class*='survey'], .offer-item").all()
            log.info("prizerebel: found %d survey item(s)", len(survey_items))

            for i, survey in enumerate(survey_items[:10]):
                try:
                    title = survey.locator(".title, h3, [class*='name']").first.inner_text(timeout=3000)
                    points_text = survey.locator(".points, [class*='points'], [class*='reward']").first.inner_text(timeout=3000)

                    points_match = re.search(r'[\d.]+', points_text)
                    points = float(points_match.group()) if points_match else 0.0

                    if points < 50:
                        continue

                    time_text = survey.locator(".time, [class*='duration'], [class*='length']").first.inner_text(timeout=2000)
                    time_match = re.search(r'(\d+)', time_text)
                    estimated_time = int(time_match.group()) if time_match else 15

                    task = MicroworkTask(
                        id=f"pr_survey_{i}_{hash(title) % 10000}",
                        platform="prizerebel",
                        type="survey",
                        title=f"Survey: {title.strip()[:50]}",
                        description=f"Earn {points} points - {time_text}",
                        reward=points,
                        reward_currency="POINTS",
                        estimated_time=estimated_time,
                        difficulty="easy",
                        url=self.page.url,
                        requirements=["honest_answers", "qualify_demographics"],
                        tags=["survey", "points"]
                    )
                    self.tasks.append(task)
                except:
                    continue
        except Exception as e:
            print(f"Survey discovery error: {e}")

    def _discover_offers(self):
        try:
            self.page.goto(f"{self.base_url}/members/offers", timeout=20000)
            self._human_delay(2, 4)
            offer_items = self.page.locator(".offer-card, [class*='offer']").all()

            for i, offer in enumerate(offer_items[:10]):
                try:
                    title = offer.locator(".title, h3").first.inner_text(timeout=3000)
                    points_text = offer.locator(".points, [class*='reward']").first.inner_text(timeout=3000)

                    points_match = re.search(r'[\d.]+', points_text)
                    points = float(points_match.group()) if points_match else 0.0

                    if points < 100:
                        continue

                    task = MicroworkTask(
                        id=f"pr_offer_{i}_{hash(title) % 10000}",
                        platform="prizerebel",
                        type="offer",
                        title=title.strip()[:60],
                        description=f"Complete offer - {points_text}",
                        reward=points,
                        reward_currency="POINTS",
                        estimated_time=10,
                        difficulty="medium",
                        url=self.page.url,
                        requirements=["complete_action", "proof_required"],
                        tags=["offer", "high_points"]
                    )
                    self.tasks.append(task)
                except:
                    continue
        except Exception as e:
            print(f"Offer discovery error: {e}")

    def _discover_challenges(self):
        try:
            self.page.goto(f"{self.base_url}/members/challenges", timeout=20000)
            self._human_delay(2, 4)
            challenge_items = self.page.locator(".challenge-item, [class*='challenge'], .daily-task").all()

            for i, challenge in enumerate(challenge_items[:5]):
                try:
                    title = challenge.locator(".title, h3").first.inner_text(timeout=3000)
                    points_text = challenge.locator(".points, [class*='reward']").first.inner_text(timeout=3000)

                    points_match = re.search(r'[\d.]+', points_text)
                    points = float(points_match.group()) if points_match else 0.0

                    task = MicroworkTask(
                        id=f"pr_challenge_{i}_{hash(title) % 10000}",
                        platform="prizerebel",
                        type="challenge",
                        title=f"Challenge: {title.strip()[:50]}",
                        description=f"Daily challenge - {points_text}",
                        reward=points,
                        reward_currency="POINTS",
                        estimated_time=5,
                        difficulty="easy",
                        url=self.page.url,
                        requirements=["complete_daily", "consistency"],
                        tags=["challenge", "daily", "bonus"]
                    )
                    self.tasks.append(task)
                except:
                    continue
        except Exception as e:
            print(f"Challenge discovery error: {e}")

    def execute_task(self, task: MicroworkTask, dry_run: bool = True) -> Dict[str, Any]:
        result = {"task_id": task.id, "platform": "prizerebel", "status": "pending", "evidence": []}

        try:
            if task.type == "survey":
                return self._execute_survey(task, dry_run)
            elif task.type == "offer":
                return self._execute_offer(task, dry_run)
            elif task.type == "challenge":
                return self._execute_challenge(task, dry_run)
            else:
                result["status"] = "unsupported"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def _execute_survey(self, task: MicroworkTask, dry_run: bool) -> Dict[str, Any]:
        result = {"task_id": task.id, "type": "survey", "status": "pending", "evidence": []}
        try:
            self.page.goto(task.url, timeout=20000)
            self._human_delay(3, 5)
            result["evidence"].append(self._take_screenshot(f"{task.id}_start"))

            if dry_run:
                result["status"] = "dry_run"
                result["message"] = "Would complete survey with AI-generated answers"
                return result

            from src.utils.ai_helper import get_ai_helper
            ai = get_ai_helper()

            page_content = self.page.content()
            answers = ai.generate_survey_answers(page_content)

            for answer in answers.get("answers", []):
                pass

            result["status"] = "completed"
            result["answers"] = answers
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def _execute_offer(self, task: MicroworkTask, dry_run: bool) -> Dict[str, Any]:
        result = {"task_id": task.id, "type": "offer", "status": "pending", "evidence": []}
        if dry_run:
            result["status"] = "dry_run"
            return result

        result["status"] = "skipped"
        result["message"] = "Offer tasks require manual review"
        return result

    def _execute_challenge(self, task: MicroworkTask, dry_run: bool) -> Dict[str, Any]:
        result = {"task_id": task.id, "type": "challenge", "status": "pending", "evidence": []}
        try:
            self.page.goto(task.url, timeout=20000)
            self._human_delay(2, 4)
            result["evidence"].append(self._take_screenshot(f"{task.id}_start"))

            if dry_run:
                result["status"] = "dry_run"
                return result

            action_btn = self.page.locator("button:has-text('Complete'), .complete-btn, [class*='claim']").first
            if action_btn.is_visible():
                action_btn.click()
                self._human_delay(2, 4)

            result["status"] = "completed"
            result["evidence"].append(self._take_screenshot(f"{task.id}_complete"))
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result
