"""
Playwright Browser (Fallback)
Standard Playwright with Chromium
"""
from typing import Optional, List, Dict, Any
from playwright.sync_api import sync_playwright
from .base_browser import BaseBrowser


class PlaywrightBrowser(BaseBrowser):
    """Standard Playwright browser (fallback when Obscura unavailable)"""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def is_available(self) -> bool:
        try:
            import playwright
            return True
        except ImportError:
            return False

    def start(self, headless: bool = True, stealth: bool = True):
        self.playwright = sync_playwright().start()

        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
        ]

        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=args
        )

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
