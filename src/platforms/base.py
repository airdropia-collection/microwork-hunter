"""
Base Platform Class
Common functionality for all microwork platforms
"""
import json
import time
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class MicroworkTask:
    """Represents a discovered microwork task"""
    id: str
    platform: str
    type: str
    title: str
    description: str
    reward: float
    reward_currency: str
    estimated_time: int
    difficulty: str
    url: str
    requirements: List[str] = None
    tags: List[str] = None
    screenshot: Optional[str] = None

    def __post_init__(self):
        if self.requirements is None:
            self.requirements = []
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BasePlatform(ABC):
    """Base class for all microwork platforms"""

    def __init__(self, name: str, base_url: str, cookies: List[Dict]):
        self.name = name
        self.base_url = base_url
        self.cookies = cookies
        self.tasks: List[MicroworkTask] = []
        self.evidence_dir = Path("evidence") / name
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.browser = None
        self.page = None

    def _human_delay(self, min_sec: float = 2.0, max_sec: float = 8.0):
        """Random delay to appear human"""
        time.sleep(random.uniform(min_sec, max_sec))

    def _take_screenshot(self, name: str) -> str:
        """Take screenshot for evidence"""
        if self.page:
            path = self.evidence_dir / f"{name}.png"
            self.page.screenshot(path=str(path), full_page=True)
            return str(path)
        return None

    def start_browser(self):
        """Start browser with cookies"""
        from src.browser import get_browser

        self.browser = get_browser()
        self.browser.start()

        # Add cookies
        if self.cookies:
            self.browser.add_cookies(self.cookies)

        self.page = self.browser.page

    def close_browser(self):
        """Close browser"""
        if self.browser:
            self.browser.close()

    @abstractmethod
    def discover_tasks(self) -> List[MicroworkTask]:
        pass

    @abstractmethod
    def execute_task(self, task: MicroworkTask, dry_run: bool = True) -> Dict[str, Any]:
        pass

    def __enter__(self):
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_browser()
