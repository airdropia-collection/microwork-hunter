"""
Playwright Browser with Cloudflare bypass (via patchright)

Uses `patchright` — a patched fork of Playwright that:
  - Spoofs browser fingerprint to bypass Cloudflare JS challenges
  - Hides automation indicators (Runtime.enable, navigator.webdriver, etc.)
  - Drop-in replacement: same API as playwright

If patchright is not installed, falls back to standard playwright.

Architecture: singleton pattern — a single Playwright/patchright instance
is shared across all platform adapters to avoid the "sync API on sync
scheduler" error.

Why patchright over alternatives?
  - patchright: Playwright fork, minimal code changes, actively maintained
  - nodriver: by ultrafunkamsterdam, no Playwright API (CDP directly)
  - FlareSolverr: separate Docker proxy, more complex setup
  - cloudscraper: Python only, can't click buttons
  - undetected-chromedriver: Selenium-based, slower

patchright is the best free/open-source option for Cloudflare bypass
with full browser automation (clicking, form filling, screenshots).
"""
from __future__ import annotations

from typing import Any, List, Optional

from src.utils.logger import get_logger

from .base_browser import BaseBrowser

log = get_logger("browser.playwright")


def _get_sync_playwright():
    """Try patchright first (Cloudflare bypass), fall back to playwright."""
    try:
        from patchright.sync_api import sync_playwright as _sp
        log.info("using patchright (Cloudflare bypass enabled)")
        return _sp
    except ImportError:
        log.warning(
            "patchright not installed — falling back to standard playwright "
            "(Cloudflare challenges may not be bypassed)"
        )
        from playwright.sync_api import sync_playwright as _sp
        return _sp


class PlaywrightBrowser(BaseBrowser):
    """Standard Playwright browser with shared singleton."""

    # Singleton — shared across all PlaywrightBrowser instances
    _shared_instance: Optional["PlaywrightBrowser._Shared"] = None

    class _Shared:
        """Holds the single Playwright + browser connection."""

        def __init__(self):
            self.playwright = None
            self.browser = None

        def start(self):
            if self.playwright is not None:
                return  # already started
            sp = _get_sync_playwright()
            self.playwright = sp.start()
            args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=args,
            )
            log.info("Chromium instance started (patchright=%s)", "patchright" in str(sp).lower() or "yes")

        def stop(self):
            if self.browser:
                try:
                    self.browser.close()
                except Exception as exc:  # noqa: BLE001
                    log.debug("browser.close() error: %s", exc)
                self.browser = None
            if self.playwright:
                try:
                    self.playwright.stop()
                except Exception as exc:  # noqa: BLE001
                    log.debug("playwright.stop() error: %s", exc)
                self.playwright = None
            log.info("Playwright shared instance stopped")

    def __init__(self):
        self.context = None
        self.page = None

    def is_available(self) -> bool:
        try:
            import playwright  # noqa: F401
            return True
        except ImportError:
            try:
                import patchright  # noqa: F401
                return True
            except ImportError:
                return False

    def start(self, headless: bool = True, stealth: bool = True):
        # Initialise shared singleton
        if PlaywrightBrowser._shared_instance is None:
            PlaywrightBrowser._shared_instance = PlaywrightBrowser._Shared()
        PlaywrightBrowser._shared_instance.start()

        # Create our own context with stealth settings
        self.context = PlaywrightBrowser._shared_instance.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Sec-Ch-Ua": '"Chromium";v="120", "Not_A Brand";v="8"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Linux"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            },
        )

        # Apply stealth: hide navigator.webdriver
        if stealth:
            try:
                self.context.add_init_script(
                    """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    window.chrome = { runtime: {} };
                    """
                )
            except Exception as exc:  # noqa: BLE001
                log.debug("stealth init_script failed: %s", exc)

        self.page = self.context.new_page()

    def new_page(self):
        return self.context.new_page()

    def goto(self, url: str, timeout: int = 30000):
        self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")

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

    def add_cookies(self, cookies: List[dict]):
        # Normalise cookie format (same as ObscuraBrowser)
        normalised = []
        for c in cookies:
            cookie = dict(c)
            ss = cookie.get("sameSite", "")
            if ss not in ("Strict", "Lax", "None"):
                cookie["sameSite"] = "Lax"
            cookie.pop("hostOnly", None)
            cookie.pop("session", None)
            if "expirationDate" in cookie and "expires" not in cookie:
                try:
                    cookie["expires"] = int(float(cookie["expirationDate"]))
                except (TypeError, ValueError):
                    pass
                cookie.pop("expirationDate", None)
            normalised.append(cookie)
        self.context.add_cookies(normalised)

    def close(self):
        """Close this adapter's context only."""
        if self.context:
            try:
                self.context.close()
            except Exception as exc:  # noqa: BLE001
                log.debug("context.close() error: %s", exc)
            self.context = None
            self.page = None

    @classmethod
    def shutdown_shared(cls):
        """Stop the shared Playwright instance. Call once at end of run."""
        if cls._shared_instance is not None:
            cls._shared_instance.stop()
            cls._shared_instance = None
