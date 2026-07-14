"""
Smart Task Filter.

Decides whether a discovered microwork task can be **fully automated**
(no manual intervention required from the user) or whether it should be
**rejected** because it requires the user to do something offline
(download an app, verify a phone, sign up on a third-party site, etc.).

The filter is intentionally conservative: when in doubt, REJECT. The
user's explicit instruction was:

    "Sirf wohi task choose/filter karo jis mein user ko manually
     kuch na karna pade."

Usage
-----
    from src.utils.task_filter import TaskFilter, FilterDecision

    f = TaskFilter()
    decision = f.classify(task_dict)
    if decision.allowed:
        ...  # keep task in queue
    else:
        log.info("rejected: %s — reason: %s", task["id"], decision.reason)

Patterns
--------
Three pattern sets are maintained:

1. ``BLOCKLIST`` — phrases that indicate manual intervention is required.
   Matched (case-insensitive) against the task's title, description,
   requirements, and tags. If ANY blocklist pattern matches, the task
   is rejected.

2. ``SOCIAL_BLOCKLIST`` — phrases that indicate the task requires
   interaction with a third-party social platform (Facebook, Instagram,
   TikTok, Telegram, etc.). These are blocked **by default** because:
     - Social platforms have aggressive anti-bot detection
     - Account-ban risk is high
     - Each platform would need its own cookie set
     - TOS violations
   To enable social tasks, set ``ENABLE_SOCIAL_TASKS=true`` in env
   or GitHub Secrets.

3. ``ALLOWLIST`` — phrases that strongly indicate the task is
   auto-completable. Used for the ``confidence`` score, not for the
   final decision (the absence of blocklist matches is enough).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

log = get_logger("filter")


# ---------------------------------------------------------------------- #
# Pattern catalogue
# ---------------------------------------------------------------------- #

# Tasks that REQUIRE the user to do something offline / on a third-party
# site / with personal credentials. These can NEVER be auto-completed.
BLOCKLIST: List[str] = [
    # --- Mobile app install / download ---
    r"\bdownload\s+(and\s+)?install\s+(the\s+)?app\b",
    r"\bdownload\s+(our\s+|the\s+|this\s+)?app\b",
    r"\binstall\s+(our|the|this)\s+app\b",
    r"\bget\s+(the\s+|our\s+)?app\b",
    r"\bmobile\s+app\b",
    r"\bandroid\s+app\b",
    r"\bios\s+app\b",
    r"\bapp\s+store\b",
    r"\bplay\s+store\b",
    r"\bgoogle\s+play\b",
    r"\bapple\s+store\b",
    r"\bapk\s+download\b",

    # --- Phone / SMS verification ---
    r"\bphone\s+number\b",
    r"\bverify\s+(your\s+)?phone\b",
    r"\bsms\s+verification\b",
    r"\bmobile\s+verification\b",
    r"\botp\s+code\b",
    r"\btext\s+message\s+code\b",
    r"\bcell\s+phone\b",
    r"\bwhatsapp\b",

    # --- Email / account sign-up on third-party sites ---
    r"\bsign\s*up\s+(for|on|with)\b",
    r"\bcreate\s+(an?\s+)?account\s+(on|at|for)\b",
    r"\bregister\s+(on|at|for)\b",
    r"\bemail\s+verification\b",
    r"\bverify\s+(your\s+)?email\b",
    r"\bgmail\s+account\b",
    r"\bgoogle\s+account\b",
    r"\bfacebook\s+account\b",
    r"\blinkedin\s+account\b",
    r"\btwitter\s+account\b",
    r"\binstagram\s+account\b",
    r"\btiktok\s+account\b",

    # --- Payment / financial ---
    r"\bcredit\s+card\b",
    r"\bdebit\s+card\b",
    r"\bcard\s+number\b",
    r"\bcvv\b",
    r"\bbank\s+account\b",
    r"\biban\b",
    r"\bpayment\s+method\b",
    r"\benter\s+(your\s+)?payment\b",
    r"\bpurchase\b",
    r"\bpay\s+(for|to)\b",
    r"\bsubscription\b",

    # --- Identity / KYC ---
    r"\bkyc\b",
    r"\bidentity\s+verification\b",
    r"\bid\s+card\b",
    r"\bpassport\b",
    r"\bdriver'?s?\s+licence\b",
    r"\bselfie\b",
    r"\bface\s+verification\b",
    r"\baddress\s+proof\b",
    r"\butility\s+bill\b",
    r"\bnational\s+id\b",
    r"\bssn\b",
    r"\bsocial\s+security\b",

    # --- Address forms ---
    r"\benter\s+(your\s+)?address\b",
    r"\bmailing\s+address\b",
    r"\bpostal\s+code\b",
    r"\bzip\s+code\b",

    # --- Other manual interactions ---
    r"\bmanual\s+(review|approval|action)\b",
    r"\bhuman\s+verification\b",
    r"\bcaptcha\s+(entry|solver|typist)\b",  # we DO allow AI-solvable captchas, but not manual captcha jobs
    r"\brefer\s+(a\s+)?friend\b",
    r"\binvite\s+friends\b",
    r"\bcall\s+(us|the\s+number)\b",
    r"\bvisit\s+(our\s+)?store\b",
    r"\bphysical\s+(visit|location)\b",

    # --- Tag-style keywords (these appear as raw tags in some platforms) ---
    r"\bapp\s+install\b",
    r"\bapp\s+download\b",
    r"\bmanual\s+action\b",
    r"\bsign\s+up\b",  # bare "sign up" tag (catch-all for any sign-up task)
]


# ---------------------------------------------------------------------- #
# Social-media tasks — blocked BY DEFAULT
# ---------------------------------------------------------------------- #
# These tasks require the bot to log in to a third-party social platform
# (Facebook, Instagram, TikTok, Telegram, X/Twitter, YouTube, Reddit, etc.)
# and perform an action (like, share, follow, comment, subscribe).
#
# Why blocked by default?
#   1. Each platform needs its own cookie set (more secrets to manage)
#   2. Social platforms have very aggressive anti-bot detection — accounts
#      get banned fast
#   3. TOS violations — every major social platform forbids automation
#   4. Cookie expiry is fast (hours/days), bot would fail constantly
#   5. Low reward ($0.001-$0.01) vs. high account-ban risk
#
# To enable social tasks (NOT recommended):
#   Set environment variable  ENABLE_SOCIAL_TASKS=true
#   Or add GitHub Secret        ENABLE_SOCIAL_TASKS = true
#
# Even when enabled, you must provide cookies for each platform you want
# to automate via separate secrets:
#   COOKIES_FACEBOOK, COOKIES_INSTAGRAM, COOKIES_TIKTOK,
#   COOKIES_TELEGRAM, COOKIES_TWITTER, COOKIES_YOUTUBE, etc.
SOCIAL_BLOCKLIST: List[str] = [
    # --- Facebook ---
    r"\bfacebook\s+(like|share|comment|post|follow|page|group)\b",
    r"\bfb\s+(like|share|comment|post|follow|page|group)\b",
    r"\blike\s+(our\s+)?facebook\b",
    r"\bshare\s+(on\s+)?facebook\b",
    r"\bfollow\s+(us\s+on\s+)?facebook\b",
    r"\bjoin\s+(our\s+)?facebook\s+group\b",

    # --- Instagram ---
    r"\binstagram\s+(like|follow|comment|post|story|reel)\b",
    r"\binsta\s+(like|follow|comment|post|story|reel)\b",
    r"\blike\s+(our\s+)?instagram\b",
    r"\bfollow\s+(us\s+on\s+)?instagram\b",
    r"\binsta\s+follow\b",

    # --- TikTok ---
    r"\btiktok\s+(like|follow|comment|share|video)\b",
    r"\blike\s+(our\s+)?tiktok\b",
    r"\bfollow\s+(us\s+on\s+)?tiktok\b",
    r"\bwatch\s+(our\s+)?tiktok\b",

    # --- Telegram ---
    r"\btelegram\s+(channel|group|join|subscribe)\b",
    r"\bjoin\s+(our\s+)?telegram\b",
    r"\bsubscribe\s+(to\s+)?telegram\b",

    # --- Twitter / X ---
    r"\btwitter\s+(follow|retweet|like|tweet|post)\b",
    r"\bx\s+(follow|retweet|like|tweet)\b",
    r"\bfollow\s+(us\s+on\s+)?twitter\b",
    r"\bretweet\b",
    r"\btweet\s+(about|us)\b",

    # --- YouTube ---
    r"\byoutube\s+(subscribe|like|comment|watch)\b",
    r"\bsubscribe\s+(to\s+)?(our\s+)?youtube\b",
    r"\blike\s+(our\s+)?youtube\b",
    r"\bwatch\s+(our\s+)?youtube\s+video\b",

    # --- Reddit ---
    r"\breddit\s+(upvote|post|comment|subscribe)\b",
    r"\bupvote\s+(our\s+)?reddit\b",
    r"\bjoin\s+(our\s+)?subreddit\b",

    # --- LinkedIn ---
    r"\blinkedin\s+(connect|follow|like|share)\b",
    r"\bconnect\s+(with\s+us\s+)?on\s+linkedin\b",
    r"\bconnect\s+(on\s+)?linkedin\b",

    # --- Pinterest / Snapchat / Discord ---
    r"\bpinterest\s+(pin|follow|save)\b",
    r"\bsnapchat\s+(add|follow|snap)\b",
    r"\bdiscord\s+(join|server)\b",
    r"\bjoin\s+(our\s+)?discord\b",

    # --- Generic social actions (catch-all) ---
    r"\bsocial\s+media\s+(like|follow|share|comment)\b",
    r"\bsocial\s+share\b",
    r"\bsubscribe\s+(to\s+)?(our\s+)?channel\b",
]


# Tasks that we KNOW we can automate (used for confidence scoring only).
ALLOWLIST: List[str] = [
    r"\bptc\s+ad\b",
    r"\bpaid\s+to\s+click\b",
    r"\bview\s+ad\b",
    r"\bwatch\s+(ad|video)\b",
    r"\bsurvey\b",
    r"\bcontent\s+engagement\b",
    r"\blike\s+(and|&)\s+follow\b",
    r"\bfollow\s+(us|back)\b",
    r"\bdaily\s+(bonus|challenge|claim|reward)\b",
    r"\bfaucet\b",
    r"\bclaim\s+(reward|bonus)\b",
    r"\bscroll\b",
    r"\bvisit\s+(website|site|url|link)\b",
    r"\bread\s+(article|post)\b",
]


# ---------------------------------------------------------------------- #
# Decision dataclass
# ---------------------------------------------------------------------- #

@dataclass
class FilterDecision:
    """Outcome of classifying a single task."""

    allowed: bool
    reason: str
    confidence: float  # 0.0 to 1.0
    matched_block: Optional[str] = None
    matched_allow: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "confidence": round(self.confidence, 3),
            "matched_block": self.matched_block,
            "matched_allow": self.matched_allow,
        }


# ---------------------------------------------------------------------- #
# Filter
# ---------------------------------------------------------------------- #

class TaskFilter:
    """Classify tasks as auto-completable or manual-intervention-required."""

    def __init__(self, enable_social: Optional[bool] = None):
        """
        Args:
            enable_social: Whether to allow social-media tasks.
                If None, reads from env var ``ENABLE_SOCIAL_TASKS``
                (default: false).
        """
        # Resolve the social flag
        if enable_social is None:
            enable_social = os.getenv("ENABLE_SOCIAL_TASKS", "false").lower() == "true"
        self.enable_social = enable_social

        # Compile patterns once at construction
        self._block_patterns = [
            re.compile(p, re.IGNORECASE) for p in BLOCKLIST
        ]
        # Social patterns only active if social tasks are NOT enabled
        if not self.enable_social:
            self._social_patterns = [
                re.compile(p, re.IGNORECASE) for p in SOCIAL_BLOCKLIST
            ]
        else:
            self._social_patterns = []
            log.warning(
                "social tasks ENABLED — bot may attempt FB/IG/TikTok/etc. "
                "actions. Make sure you have provided the corresponding "
                "COOKIES_FACEBOOK / COOKIES_INSTAGRAM / etc. secrets. "
                "Account-ban risk is HIGH."
            )

        self._allow_patterns = [
            re.compile(p, re.IGNORECASE) for p in ALLOWLIST
        ]

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def classify(self, task: Dict[str, Any]) -> FilterDecision:
        """
        Classify a task dict.

        Returns FilterDecision with:
          - allowed=True   if no blocklist pattern matches
          - allowed=False  if any blocklist pattern matches
        """
        text = self._task_to_text(task)

        # 1. Check hard blocklist (any match -> reject)
        for pattern in self._block_patterns:
            m = pattern.search(text)
            if m:
                reason = (
                    f"Blocklisted pattern matched: '{m.group()}' "
                    f"(likely requires manual user action)"
                )
                log.debug("rejected task %s: %s", task.get("id", "?"), reason)
                return FilterDecision(
                    allowed=False,
                    reason=reason,
                    confidence=0.0,
                    matched_block=m.group(),
                )

        # 2. Check social blocklist (only if social tasks are disabled)
        for pattern in self._social_patterns:
            m = pattern.search(text)
            if m:
                reason = (
                    f"Social-media task matched: '{m.group()}' "
                    f"(blocked by default — set ENABLE_SOCIAL_TASKS=true "
                    f"to allow, but account-ban risk is high)"
                )
                log.debug("rejected task %s: %s", task.get("id", "?"), reason)
                return FilterDecision(
                    allowed=False,
                    reason=reason,
                    confidence=0.0,
                    matched_block=m.group(),
                )

        # 3. Score confidence using allowlist
        allow_matches: List[str] = []
        for pattern in self._allow_patterns:
            m = pattern.search(text)
            if m:
                allow_matches.append(m.group())

        # Confidence: 0.5 baseline (no blocklist hit) + bonus per allowlist hit
        confidence = min(0.5 + 0.1 * len(allow_matches), 1.0)
        matched_allow = allow_matches[0] if allow_matches else None

        reason = (
            f"Auto-completable (no manual action required)"
            if allow_matches
            else "No blocklist match — defaulting to allowed (low confidence)"
        )
        return FilterDecision(
            allowed=True,
            reason=reason,
            confidence=confidence,
            matched_allow=matched_allow,
        )

    def filter_many(self, tasks: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Split a list of tasks into (allowed, rejected).

        Each rejected task gets an extra ``_filter`` key with the decision.
        Each allowed task gets an extra ``_filter`` key with confidence.
        """
        allowed: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []
        for task in tasks:
            decision = self.classify(task)
            task_with_meta = {**task, "_filter": decision.to_dict()}
            if decision.allowed:
                allowed.append(task_with_meta)
            else:
                rejected.append(task_with_meta)
        log.info(
            "filter: %d allowed, %d rejected (of %d total)",
            len(allowed),
            len(rejected),
            len(tasks),
        )
        return allowed, rejected

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _task_to_text(task: Dict[str, Any]) -> str:
        """Flatten a task dict into a single searchable text blob.

        Underscores are replaced with spaces so that patterns like
        ``phone number`` also match ``phone_number``.
        """
        parts: List[str] = []
        for key in ("title", "description", "type", "platform"):
            v = task.get(key)
            if v:
                parts.append(str(v))
        for key in ("requirements", "tags"):
            v = task.get(key)
            if isinstance(v, list):
                parts.extend(str(x) for x in v)
            elif v:
                parts.append(str(v))
        text = " | ".join(parts)
        # Normalise: underscores -> spaces, collapse whitespace
        text = re.sub(r"[_\-]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text


# ---------------------------------------------------------------------- #
# Module-level singleton for convenience
# ---------------------------------------------------------------------- #
_default_filter: Optional[TaskFilter] = None


def get_default_filter() -> TaskFilter:
    global _default_filter
    if _default_filter is None:
        _default_filter = TaskFilter()
    return _default_filter
