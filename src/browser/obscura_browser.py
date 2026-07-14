"""
Obscura Browser for GitHub Actions
Connects to Obscura Docker container via CDP
"""
import os
import time
import requests
from typing import Optional, List, Dict, Any
from playwright.sync_api import sync_playwright
from .base_browser import BaseBrowser


class ObscuraBrowser(BaseBrowser):
    """
    Obscura browser wrapper for GitHub Actions
    - Assumes Obscura is already running in Docker
    - Connects via Playwright CDP
    """

    def __init__(self, port: int = 9222):
        self.port = port
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def is_available(self) -> bool:
        """Check if Obscura CDP server is running"""
        try:
            resp = requests.get(
                f"http://127.0.0.1:{self.port}/json/version",
                timeout=5
            )
            return resp.status_code == 200
        except:
            return False

    def start(self, headless: bool = True, stealth: bool = True):
        """Connect to running Obscura instance"""

        # Wait for Obscura to be ready
        for attempt in range(30):
            if self.is_available():
                break
            time.sleep(1)
        else:
            raise RuntimeError(
                f"Obscura not available on port {self.port}. "
                "Make sure Docker container is running: "
                "docker run -d -p 9222:9222 h4ckf0r0day/obscura"
            )

        # Connect Playwright via CDP
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.connect_over_cdp(
            f"http://127.0.0.1:{self.port}"
        )

        # Create context
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        )

        self.page = self.context.new_page()

    def new_page(self):
        return self.context.new_page()

    def goto(self, url: str, timeout: int = 30000):
        self.page.goto(url, timeout=timeout)

    def click(self, selector: str):
        self.page.locator(selector).first.click()

    def fill(self, selector: str, text: str):
        self.page.locator(selector).first.fill(text)

    def screenshot(self, path: str):
        self.page.screenshot(path=path, full_page=True)

    def content(self) -> str:
        return self.page.content()

    def evaluate(self, script: str) -> Any:
        return self.page.evaluate(script)

    def add_cookies(self, cookies: List[Dict]):
        self.context.add_cookies(cookies)

    def close(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
