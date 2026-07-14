"""
Microwork Hunter Configuration
Reads from environment variables / GitHub Secrets
"""
from __future__ import annotations

import os
import base64
import json
from dataclasses import dataclass
from typing import List, Dict, Optional

from src.utils.logger import get_logger

log = get_logger("config")


@dataclass
class Config:
    # === FREE LLM APIs ===
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-1.5-flash"

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

    # === BROWSER ===
    BROWSER_TYPE: str = os.getenv("BROWSER_TYPE", "obscura")
    OBSCURA_PORT: int = int(os.getenv("OBSCURA_PORT", "9222"))

    # === TASK SETTINGS ===
    MAX_PARALLEL_TASKS: int = int(os.getenv("MAX_PARALLEL_TASKS", "5"))
    MIN_REWARD_USD: float = float(os.getenv("MIN_REWARD_USD", "0.10"))
    MAX_TASK_TIME_MIN: int = int(os.getenv("MAX_TASK_TIME_MIN", "30"))
    DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() == "true"

    # === SOCIAL TASKS (HIGH RISK — disabled by default) ===
    # When true, the task filter will NOT reject FB/IG/TikTok/Twitter/etc.
    # tasks. You must also provide the corresponding COOKIES_FACEBOOK,
    # COOKIES_INSTAGRAM, COOKIES_TIKTOK, COOKIES_TELEGRAM, COOKIES_TWITTER,
    # COOKIES_YOUTUBE, etc. secrets.
    # WARNING: enabling this dramatically increases account-ban risk.
    ENABLE_SOCIAL_TASKS: bool = os.getenv("ENABLE_SOCIAL_TASKS", "false").lower() == "true"

    # === PAYMENT ===
    LTC_ADDRESS: str = os.getenv("LTC_ADDRESS", "")

    # === COOKIES (from GitHub Secrets, base64 encoded) ===
    @property
    def cookies_sproutgigs(self) -> List[Dict]:
        return self._decode_cookies("COOKIES_SPROUTGIGS")

    @property
    def cookies_rewardjoy(self) -> List[Dict]:
        """RewardJoy (formerly CoinPayu) cookies.
        Tries COOKIES_REWARDJOY first, falls back to COOKIES_COINPAYU."""
        cookies = self._decode_cookies("COOKIES_REWARDJOY")
        if not cookies:
            cookies = self._decode_cookies("COOKIES_COINPAYU")
        return cookies

    # Backward-compat alias
    @property
    def cookies_coinpayu(self) -> List[Dict]:
        return self.cookies_rewardjoy

    @property
    def cookies_timebucks(self) -> List[Dict]:
        return self._decode_cookies("COOKIES_TIMEBUCKS")

    @property
    def cookies_prizerebel(self) -> List[Dict]:
        return self._decode_cookies("COOKIES_PRIZEREBEL")

    def _decode_cookies(self, env_var: str) -> List[Dict]:
        """Decode base64 cookies from environment variable"""
        encoded = os.getenv(env_var, "")
        if not encoded:
            # Try reading from file (local dev)
            cookie_file = f"cookies/{env_var.lower().replace('cookies_', '')}_cookies.json"
            if os.path.exists(cookie_file):
                with open(cookie_file) as f:
                    return json.load(f)
            return []

        try:
            decoded = base64.b64decode(encoded).decode('utf-8')
            return json.loads(decoded)
        except Exception as exc:  # noqa: BLE001
            log.error("failed to decode %s: %s", env_var, exc)
            return []

    @property
    def has_gemini(self) -> bool:
        return bool(self.GEMINI_API_KEY)

    @property
    def has_groq(self) -> bool:
        return bool(self.GROQ_API_KEY)

    @property
    def has_any_llm(self) -> bool:
        return self.has_gemini or self.has_groq


# Singleton
CONFIG = Config()
