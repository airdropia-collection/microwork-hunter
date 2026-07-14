"""
Obscura Browser for GitHub Actions
Connects to Obscura Docker container via CDP.

Architecture note:
    Playwright's sync API does NOT allow multiple ``sync_playwright().start()``
    calls in the same process. If you try, you get:

        "It looks like you are using Playwright Sync API on the sync
         scheduler. We recommend using the Async API instead."

    To support running multiple platform adapters in sequence (SproutGigs,
    RewardJoy, TimeBucks, ...) within the same Hunter run, we share a
    SINGLE Playwright instance + Obscura CDP connection across all
    platforms. Each platform gets its own BrowserContext (with its own
    cookies), but the underlying Playwright driver is started only once.

    The ``_shared_instance`` class attribute holds the singleton.
    ``start()`` creates it on first call, reuses on subsequent calls.
    ``close()`` only closes the context, not the browser. The actual
    Playwright teardown happens via ``shutdown_shared()`` which is called
    by the discover/executor orchestrator after all platforms are done.
"""
from __future__ import annotations

import time
from typing import Any, List, Optional

import requests
from playwright.sync_api import sync_playwright
from src.utils.logger import get_logger

from .base_browser import BaseBrowser

log = get_logger("browser.obscura")


class ObscuraBrowser(BaseBrowser):
    """
    Obscura browser wrapper for GitHub Actions.

    Connects to an already-running Obscura Docker container via Playwright
    CDP. Shares a single Playwright instance across all adapters to avoid
    the "sync API on sync scheduler" error.
    """

    # Singleton — shared across all ObscuraBrowser instances in this process
    _shared_instance: Optional["ObscuraBrowser._Shared"] = None

    class _Shared:
        """Holds the single Playwright + CDP browser connection."""

        def __init__(self, port: int):
            self.port = port
            self.playwright = None
            self.browser = None

        def start(self):
            if self.playwright is not None:
                return  # already started
            # Wait for Obscura to be ready
            for attempt in range(30):
                try:
                    resp = requests.get(
                        f"http://127.0.0.1:{self.port}/json/version",
                        timeout=5,
                    )
                    if resp.status_code == 200:
                        break
                except Exception:  # noqa: BLE001
                    pass
                time.sleep(1)
            else:
                raise RuntimeError(
                    f"Obscura not available on port {self.port}. "
                    "Make sure Docker container is running: "
                    "docker run -d -p 9222:9222 h4ckf0r0day/obscura"
                )

            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.connect_over_cdp(
                f"http://127.0.0.1:{self.port}"
            )
            log.info("Obscura shared Playwright instance started on port %d", self.port)

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
            log.info("Obscura shared Playwright instance stopped")

    def __init__(self, port: int = 9222):
        self.port = port
        self.context = None
        self.page = None

    # ------------------------------------------------------------------ #
    # Availability check
    # ------------------------------------------------------------------ #
    def is_available(self) -> bool:
        """Check if Obscura CDP server is running."""
        try:
            resp = requests.get(
                f"http://127.0.0.1:{self.port}/json/version",
                timeout=5,
            )
            return resp.status_code == 200
        except Exception:  # noqa: BLE001
            return False

    # ------------------------------------------------------------------ #
    # Start / close (per-adapter context, shared browser)
    # ------------------------------------------------------------------ #
    def start(self, headless: bool = True, stealth: bool = True):
        """Connect to running Obscura instance and create a fresh context."""
        # Initialise the shared singleton if needed
        if ObscuraBrowser._shared_instance is None:
            ObscuraBrowser._shared_instance = ObscuraBrowser._Shared(self.port)
        ObscuraBrowser._shared_instance.start()

        # Create our own context (each adapter gets its own cookies)
        self.context = ObscuraBrowser._shared_instance.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
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

    def add_cookies(self, cookies: List[dict]):
        # Playwright requires 'url' or 'domain'+'path' on each cookie.
        # Some cookie exporters omit these — add safe defaults.
        normalised = []
        for c in cookies:
            cookie = dict(c)
            if "domain" not in cookie and "url" not in cookie:
                # Infer domain from the cookie's existing domain field or skip
                pass
            # Ensure sameSite is a valid Playwright enum value
            ss = cookie.get("sameSite", "")
            if ss not in ("Strict", "Lax", "None"):
                cookie["sameSite"] = "Lax"
            # Playwright doesn't accept 'hostOnly' or 'session' keys
            cookie.pop("hostOnly", None)
            cookie.pop("session", None)
            # Convert expirationDate (float, seconds) to expires (int, ms)
            if "expirationDate" in cookie and "expires" not in cookie:
                try:
                    cookie["expires"] = int(float(cookie["expirationDate"]))
                except (TypeError, ValueError):
                    pass
                cookie.pop("expirationDate", None)
            normalised.append(cookie)
        self.context.add_cookies(normalised)

    def close(self):
        """Close this adapter's context only. Does NOT stop Playwright."""
        if self.context:
            try:
                self.context.close()
            except Exception as exc:  # noqa: BLE001
                log.debug("context.close() error: %s", exc)
            self.context = None
            self.page = None

    # ------------------------------------------------------------------ #
    # Class-level teardown — call after ALL adapters are done
    # ------------------------------------------------------------------ #
    @classmethod
    def shutdown_shared(cls):
        """Stop the shared Playwright instance. Call once at end of run."""
        if cls._shared_instance is not None:
            cls._shared_instance.stop()
            cls._shared_instance = None