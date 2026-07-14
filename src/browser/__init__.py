"""Browser abstraction layer."""
from .base_browser import BaseBrowser
from .obscura_browser import ObscuraBrowser
from .playwright_browser import PlaywrightBrowser

__all__ = ["BaseBrowser", "ObscuraBrowser", "PlaywrightBrowser", "get_browser"]


def get_browser(prefer_obscura: bool = True):
    """
    Get best available browser.
    Priority: Obscura (Docker) -> Playwright (fallback)
    """
    import os

    env_browser = os.getenv("BROWSER_TYPE", "auto").lower()

    if env_browser == "obscura":
        obscura = ObscuraBrowser()
        if obscura.is_available():
            return obscura
        raise RuntimeError("Obscura requested but not available on port 9222")

    if env_browser == "playwright":
        playwright = PlaywrightBrowser()
        if playwright.is_available():
            return playwright
        raise RuntimeError("Playwright not available")

    # Auto-detect
    if prefer_obscura:
        obscura = ObscuraBrowser()
        if obscura.is_available():
            print("✅ Using Obscura browser (stealth mode)")
            return obscura
        print("⚠️ Obscura not found, falling back to Playwright")

    playwright = PlaywrightBrowser()
    if playwright.is_available():
        print("✅ Using Playwright browser (fallback)")
        return playwright

    raise RuntimeError(
        "No browser available. "
        "For GitHub Actions, ensure Obscura Docker is running. "
        "For local, install Playwright: pip install playwright && playwright install chromium"
    )
