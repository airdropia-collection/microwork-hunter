"""
Browser Abstraction Layer
Supports: Obscura (primary), Playwright (fallback)
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class BaseBrowser(ABC):
    """Abstract browser interface"""

    @abstractmethod
    def start(self, headless: bool = True, stealth: bool = True):
        pass

    @abstractmethod
    def new_page(self) -> Any:
        pass

    @abstractmethod
    def goto(self, url: str, timeout: int = 30000):
        pass

    @abstractmethod
    def click(self, selector: str):
        pass

    @abstractmethod
    def fill(self, selector: str, text: str):
        pass

    @abstractmethod
    def screenshot(self, path: str):
        pass

    @abstractmethod
    def content(self) -> str:
        pass

    @abstractmethod
    def evaluate(self, script: str) -> Any:
        pass

    @abstractmethod
    def add_cookies(self, cookies: List[Dict]):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass
