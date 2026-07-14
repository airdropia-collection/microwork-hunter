"""
TimeBucks Platform Hunter
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from src.config import CONFIG
from src.utils.logger import get_logger
from .base import BasePlatform, MicroworkTask

log = get_logger("platforms.timebucks")


class TimeBucksPlatform(BasePlatform):
    """TimeBucks task automation"""

    def __init__(self):
        super().__init__(
            name="timebucks",
            base_url="https://timebucks.com",
            cookies=CONFIG.cookies_timebucks
        )

    def discover_tasks(self) -> List[MicroworkTask]:
        self.tasks = []
        try:
            self._discover_videos()
            self._discover_surveys()
            self._discover_content()
        except Exception as e:
            print(f"Error discovering TimeBucks: {e}")
        return self.tasks

    def _discover_videos(self):
        try:
            self.page.goto(f"{self.base_url}/publishers/index.php?pg=earn&tab=videos", timeout=20000)
            self._human_delay(2, 4)
            self._log_page_info("timebucks_videos")
            video_items = self.page.locator(".video-item, [class*='video'], .task-row").all()
            log.info("timebucks: found %d video item(s)", len(video_items))

            for i, video in enumerate(video_items[:10]):
                try:
                    title = video.locator(".title, h3, td:nth-child(2)").first.inner_text(timeout=3000)
                    reward_text = video.locator(".reward, [class*='amount'], td:nth-child(3)").first.inner_text(timeout=3000)

                    reward_match = re.search(r'[\d.]+', reward_text)
                    reward = float(reward_match.group()) if reward_match else 0.0

                    if reward < 0.001:
                        continue

                    task = MicroworkTask(
                        id=f"tb_video_{i}_{hash(title) % 10000}",
                        platform="timebucks",
                        type="video",
                        title=f"Watch: {title.strip()[:50]}",
                        description=f"Watch video - {reward_text}",
                        reward=reward,
                        reward_currency="USD",
                        estimated_time=3,
                        difficulty="easy",
                        url=self.page.url,
                        requirements=["watch_full_video", "stay_active"],
                        tags=["video", "watch", "passive"]
                    )
                    self.tasks.append(task)
                except:
                    continue
        except Exception as e:
            print(f"Video discovery error: {e}")

    def _discover_surveys(self):
        try:
            self.page.goto(f"{self.base_url}/publishers/index.php?pg=earn&tab=surveys", timeout=20000)
            self._human_delay(2, 4)
            survey_items = self.page.locator(".survey-item, [class*='survey'], .task-row").all()

            for i, survey in enumerate(survey_items[:5]):
                try:
                    title = survey.locator(".title, h3, td:nth-child(2)").first.inner_text(timeout=3000)
                    reward_text = survey.locator(".reward, td:nth-child(3)").first.inner_text(timeout=3000)

                    reward_match = re.search(r'[\d.]+', reward_text)
                    reward = float(reward_match.group()) if reward_match else 0.0

                    time_text = survey.locator(".time, td:nth-child(4)").first.inner_text(timeout=2000)
                    time_match = re.search(r'(\d+)', time_text)
                    estimated_time = int(time_match.group()) if time_match else 15

                    task = MicroworkTask(
                        id=f"tb_survey_{i}_{hash(title) % 10000}",
                        platform="timebucks",
                        type="survey",
                        title=f"Survey: {title.strip()[:50]}",
                        description=f"Paid survey - {reward_text}",
                        reward=reward,
                        reward_currency="USD",
                        estimated_time=estimated_time,
                        difficulty="easy",
                        url=self.page.url,
                        requirements=["honest_answers", "complete_all_questions"],
                        tags=["survey", "paid"]
                    )
                    self.tasks.append(task)
                except:
                    continue
        except Exception as e:
            print(f"Survey discovery error: {e}")

    def _discover_content(self):
        try:
            self.page.goto(f"{self.base_url}/publishers/index.php?pg=earn&tab=content", timeout=20000)
            self._human_delay(2, 4)
            content_items = self.page.locator(".content-item, [class*='content'], .task-row").all()

            for i, item in enumerate(content_items[:10]):
                try:
                    title = item.locator(".title, h3, td:nth-child(2)").first.inner_text(timeout=3000)
                    reward_text = item.locator(".reward, td:nth-child(3)").first.inner_text(timeout=3000)

                    reward_match = re.search(r'[\d.]+', reward_text)
                    reward = float(reward_match.group()) if reward_match else 0.0

                    if reward < 0.001:
                        continue

                    task = MicroworkTask(
                        id=f"tb_content_{i}_{hash(title) % 10000}",
                        platform="timebucks",
                        type="content",
                        title=f"Engage: {title.strip()[:50]}",
                        description=f"Content engagement - {reward_text}",
                        reward=reward,
                        reward_currency="USD",
                        estimated_time=2,
                        difficulty="easy",
                        url=self.page.url,
                        requirements=["view_content", "interact"],
                        tags=["content", "engagement"]
                    )
                    self.tasks.append(task)
                except:
                    continue
        except Exception as e:
            print(f"Content discovery error: {e}")

    def execute_task(self, task: MicroworkTask, dry_run: bool = True) -> Dict[str, Any]:
        result = {"task_id": task.id, "platform": "timebucks", "status": "pending", "evidence": []}

        try:
            if task.type == "video":
                return self._execute_video(task, dry_run)
            elif task.type == "survey":
                return self._execute_survey(task, dry_run)
            elif task.type == "content":
                return self._execute_content(task, dry_run)
            else:
                result["status"] = "unsupported"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def _execute_video(self, task: MicroworkTask, dry_run: bool) -> Dict[str, Any]:
        result = {"task_id": task.id, "type": "video", "status": "pending", "evidence": []}
        try:
            self.page.goto(task.url, timeout=20000)
            self._human_delay(2, 4)
            result["evidence"].append(self._take_screenshot(f"{task.id}_start"))

            if dry_run:
                result["status"] = "dry_run"
                result["message"] = "Would watch video for required duration"
                return result

            play_btn = self.page.locator("button:has-text('Play'), .play-btn, video").first
            if play_btn.is_visible():
                play_btn.click()

            self.page.wait_for_timeout(35000)
            result["status"] = "completed"
            result["evidence"].append(self._take_screenshot(f"{task.id}_complete"))
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def _execute_survey(self, task: MicroworkTask, dry_run: bool) -> Dict[str, Any]:
        result = {"task_id": task.id, "type": "survey", "status": "pending", "evidence": []}
        if dry_run:
            result["status"] = "dry_run"
            return result

        result["status"] = "skipped"
        result["message"] = "Survey execution requires AI answer generation"
        return result

    def _execute_content(self, task: MicroworkTask, dry_run: bool) -> Dict[str, Any]:
        result = {"task_id": task.id, "type": "content", "status": "pending", "evidence": []}
        try:
            self.page.goto(task.url, timeout=20000)
            self._human_delay(3, 6)
            result["evidence"].append(self._take_screenshot(f"{task.id}_start"))

            if dry_run:
                result["status"] = "dry_run"
                return result

            self.page.evaluate("window.scrollBy(0, 500)")
            self._human_delay(2, 4)
            self.page.evaluate("window.scrollBy(0, 500)")
            self._human_delay(2, 4)

            buttons = self.page.locator("button, a.btn").all()
            for btn in buttons[:3]:
                try:
                    if btn.is_visible():
                        btn.click()
                        self._human_delay(1, 2)
                except:
                    pass

            result["status"] = "completed"
            result["evidence"].append(self._take_screenshot(f"{task.id}_complete"))
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result
