"""
SproutGigs Platform Hunter
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from src.config import CONFIG
from src.utils.logger import get_logger
from .base import BasePlatform, MicroworkTask

log = get_logger("platforms.sproutgigs")


class SproutGigsPlatform(BasePlatform):
    """SproutGigs microwork platform"""

    def __init__(self):
        super().__init__(
            name="sproutgigs",
            base_url="https://sproutgigs.com",
            cookies=CONFIG.cookies_sproutgigs
        )

    def discover_tasks(self) -> List[MicroworkTask]:
        """Discover available tasks"""
        self.tasks = []

        try:
            self.page.goto(f"{self.base_url}/micro-jobs", timeout=20000)
            self._human_delay(3, 5)
            # Wait for Cloudflare JS challenge to resolve
            self._wait_for_cloudflare(timeout_sec=15)
            self._log_page_info("sproutgigs_jobs")

            # Extract job cards
            job_cards = self.page.locator(".job-card, [class*='job'], .task-item").all()
            log.info("sproutgigs: found %d job card(s)", len(job_cards))

            for i, card in enumerate(job_cards[:15]):
                try:
                    title = card.locator("h3, .title, [class*='title']").first.inner_text(timeout=3000)
                    reward_text = card.locator(".reward, [class*='price'], [class*='amount']").first.inner_text(timeout=3000)

                    reward_match = re.search(r'[\d.]+', reward_text)
                    reward = float(reward_match.group()) if reward_match else 0.0

                    if reward < CONFIG.MIN_REWARD_USD:
                        continue

                    link = card.locator("a").first.get_attribute("href") or ""
                    if not link.startswith("http"):
                        link = f"{self.base_url}{link}"

                    time_text = card.locator("[class*='time'], .duration").first.inner_text(timeout=2000)
                    time_match = re.search(r'(\d+)', time_text)
                    estimated_time = int(time_match.group()) if time_match else 10

                    if estimated_time > CONFIG.MAX_TASK_TIME_MIN:
                        continue

                    task = MicroworkTask(
                        id=f"sg_{i}_{hash(title) % 10000}",
                        platform="sproutgigs",
                        type="microjob",
                        title=title.strip(),
                        description=f"SproutGigs job - {reward_text}",
                        reward=reward,
                        reward_currency="USD",
                        estimated_time=estimated_time,
                        difficulty="easy",
                        url=link,
                        requirements=["follow_instructions", "screenshot_proof"],
                        tags=["microjob", "quick"]
                    )
                    self.tasks.append(task)

                except Exception as e:
                    continue

            # Also check surveys
            self._discover_surveys()

        except Exception as e:
            print(f"Error discovering SproutGigs: {e}")

        return self.tasks

    def _discover_surveys(self):
        """Discover paid surveys"""
        try:
            self.page.goto(f"{self.base_url}/paid-surveys", timeout=20000)
            self._human_delay(2, 4)

            survey_items = self.page.locator(".survey-item, [class*='survey']").all()

            for i, survey in enumerate(survey_items[:5]):
                try:
                    title = survey.locator("h3, .title").first.inner_text(timeout=3000)
                    reward_text = survey.locator(".reward, [class*='price']").first.inner_text(timeout=3000)

                    reward_match = re.search(r'[\d.]+', reward_text)
                    reward = float(reward_match.group()) if reward_match else 0.0

                    if reward < CONFIG.MIN_REWARD_USD:
                        continue

                    time_text = survey.locator("[class*='time'], .duration").first.inner_text(timeout=2000)
                    time_match = re.search(r'(\d+)', time_text)
                    estimated_time = int(time_match.group()) if time_match else 15

                    task = MicroworkTask(
                        id=f"sg_survey_{i}_{hash(title) % 10000}",
                        platform="sproutgigs",
                        type="survey",
                        title=title.strip(),
                        description=f"Paid survey - {reward_text}",
                        reward=reward,
                        reward_currency="USD",
                        estimated_time=estimated_time,
                        difficulty="easy",
                        url=self.page.url,
                        requirements=["honest_answers", "consistent_responses"],
                        tags=["survey", "paid"]
                    )
                    self.tasks.append(task)

                except:
                    continue

        except Exception as e:
            print(f"Survey discovery error: {e}")

    def execute_task(self, task: MicroworkTask, dry_run: bool = True) -> Dict[str, Any]:
        """Execute a task"""
        result = {
            "task_id": task.id,
            "platform": "sproutgigs",
            "status": "pending",
            "evidence": []
        }

        try:
            self.page.goto(task.url, timeout=20000)
            self._human_delay(3, 6)

            result["evidence"].append(self._take_screenshot(f"{task.id}_before"))

            if dry_run:
                result["status"] = "dry_run"
                result["message"] = "Would complete task and submit proof"
                return result

            # Read instructions
            instructions = self.page.locator(".instructions, [class*='description'], .task-details").first.inner_text(timeout=5000)

            # Use AI to understand task
            from src.utils.ai_helper import get_ai_helper
            ai = get_ai_helper()

            completion = ai.generate(
                prompt=f"Task: {task.title}\nInstructions: {instructions}\n\nGenerate completion steps.",
                system="You are a microwork task completion expert."
            )

            result["status"] = "completed"
            result["completion"] = completion

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        result["evidence"].append(self._take_screenshot(f"{task.id}_after"))
        return result
