"""
Cookie Validator.

Quickly checks whether the configured cookies for each platform are
still valid by visiting the platform URL and looking for a
login-indicator string in the resulting URL or page content.

Run as:
    python -m src.utils.cookie_validator --platform all

Exits 0 if at least one platform validates, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.utils.logger import get_logger

log = get_logger("cookie_validator")


class CookieValidator:
    PLATFORMS = {
        "sproutgigs": {
            "url": "https://sproutgigs.com",
            "login_indicator": "dashboard",
        },
        "rewardjoy": {
            "url": "https://www.rewardjoy.com",
            "login_indicator": "dashboard",
        },
        "timebucks": {
            "url": "https://timebucks.com",
            "login_indicator": "dashboard",
        },
        "prizerebel": {
            "url": "https://www.prizerebel.com",
            "login_indicator": "members",
        },
        "cointiply": {
            "url": "https://cointiply.com",
            "login_indicator": "dashboard",
        },
    }

    def validate_all(self) -> dict:
        results = {}
        for name, config in self.PLATFORMS.items():
            results[name] = self._validate(name, config)
        return results

    def _validate(self, name: str, config: dict) -> dict:
        result = {"platform": name, "valid": False, "error": None}
        try:
            from src.browser import get_browser  # local import — heavy

            browser = get_browser()
            browser.start()
            try:
                browser.goto(config["url"], timeout=15000)
                current_url = browser.page.url if hasattr(browser, "page") else ""
                content = browser.content() if hasattr(browser, "content") else ""
                result["current_url"] = current_url
                indicator = config["login_indicator"].lower()
                result["valid"] = indicator in current_url.lower() or indicator in content.lower()
                log.info(
                    "cookie check %s: valid=%s url=%s",
                    name,
                    result["valid"],
                    current_url,
                )
            finally:
                browser.close()
        except Exception as exc:  # noqa: BLE001
            result["error"] = str(exc)
            log.error("cookie check %s failed: %s", name, exc)
        return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", default="all")
    args = parser.parse_args()

    validator = CookieValidator()
    if args.platform == "all":
        results = validator.validate_all()
    else:
        cfg = validator.PLATFORMS[args.platform]
        results = {args.platform: validator._validate(args.platform, cfg)}

    Path("cookies_valid.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )

    ready = sum(1 for r in results.values() if r["valid"])
    Path("platforms_ready.txt").write_text(str(ready), encoding="utf-8")

    log.info("validated: %d/%d platforms ready", ready, len(results))
    return 0 if ready > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
