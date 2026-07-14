"""
Startup configuration validation.

Run as:
    python -m src.utils.health

Exits 0 if everything looks good, 1 if any required piece is missing.
The Hunter workflow calls this before discovery so that misconfigured
runs fail fast with a clear message instead of mid-way through.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.config import CONFIG
from src.utils.logger import get_logger

log = get_logger("health")


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""
    severity: str = "error"  # error | warning | info


def _check_llm_keys() -> Check:
    if CONFIG.has_gemini:
        return Check("llm_keys", True, "Gemini API key present", "info")
    if CONFIG.has_groq:
        return Check(
            "llm_keys",
            True,
            "Groq API key present (Gemini missing — survey quality may be lower)",
            "warning",
        )
    return Check(
        "llm_keys",
        False,
        "Neither GEMINI_API_KEY nor GROQ_API_KEY set — AI features disabled",
        "error",
    )


def _check_browser() -> Check:
    browser_type = os.getenv("BROWSER_TYPE", "auto").lower()
    if browser_type == "obscura":
        port = CONFIG.OBSCURA_PORT
        # Quick TCP probe
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            sock.connect(("127.0.0.1", port))
            sock.close()
            return Check("browser", True, f"Obscura reachable on port {port}", "info")
        except OSError as exc:
            return Check(
                "browser",
                False,
                f"Obscura not reachable on port {port}: {exc}",
                "error",
            )
    if browser_type in ("playwright", "auto"):
        try:
            import playwright  # type: ignore  # noqa: F401

            return Check(
                "browser",
                True,
                "Playwright available (will use as fallback or primary)",
                "info",
            )
        except ImportError:
            return Check(
                "browser",
                False,
                "Playwright not installed — install with `pip install playwright && playwright install chromium`",
                "error",
            )
    return Check("browser", False, f"Unknown BROWSER_TYPE={browser_type!r}", "error")


def _check_cookie(platform: str) -> Check:
    import os
    from pathlib import Path

    # Try CONFIG.cookies_<platform> first (works for sproutgigs/coinpayu/etc.)
    cookies = getattr(CONFIG, f"cookies_{platform}", None)
    if cookies is None:
        # Cointiply and other platforms not yet on CONFIG — check env directly
        env_var = f"COOKIES_{platform.upper()}"
        if os.getenv(env_var):
            cookies = [{"_source": "env"}]  # truthy placeholder
        elif Path(f"cookies/{platform}_cookies.json").exists():
            cookies = [{"_source": "file"}]
        else:
            cookies = []
    if cookies:
        return Check(
            f"cookies_{platform}",
            True,
            f"{len(cookies)} cookie(s) loaded for {platform}",
            "info",
        )
    # Try file path
    cookie_file = Path(f"cookies/{platform}_cookies.json")
    if cookie_file.exists():
        return Check(
            f"cookies_{platform}",
            True,
            f"Cookie file found at {cookie_file} (not yet loaded)",
            "warning",
        )
    return Check(
        f"cookies_{platform}",
        False,
        f"No cookies for {platform} — set COOKIES_{platform.upper()} secret",
        "warning",  # warning, not error — bot can still run for other platforms
    )


def run_all_checks() -> List[Check]:
    checks: List[Check] = []
    checks.append(_check_llm_keys())
    checks.append(_check_browser())
    for platform in ("sproutgigs", "coinpayu", "timebucks", "prizerebel", "cointiply"):
        checks.append(_check_cookie(platform))
    return checks


def print_report(checks: List[Check]) -> int:
    """Pretty-print the report. Returns exit code (0 ok, 1 has errors)."""
    has_error = False
    has_warning = False

    print("\n" + "=" * 60)
    print("  🩺 Microwork Hunter — Health Check")
    print("=" * 60)

    for c in checks:
        emoji = {
            "error": "❌",
            "warning": "⚠️ ",
            "info": "✅",
        }[c.severity]
        print(f"  {emoji} {c.name:25} {c.detail}")
        if c.severity == "error" and not c.ok:
            has_error = True
        if c.severity == "warning":
            has_warning = True

    print("=" * 60)
    if has_error:
        print("  ❌ ERRORS — bot may not run correctly. Fix and re-run.")
        code = 1
    elif has_warning:
        print("  ⚠️  WARNINGS — bot will run with degraded functionality.")
        code = 0
    else:
        print("  ✅ All checks passed — ready to hunt!")
        code = 0

    print("=" * 60 + "\n")
    return code


def main() -> int:
    log.info("Running health checks...")
    checks = run_all_checks()
    return print_report(checks)


if __name__ == "__main__":
    sys.exit(main())
