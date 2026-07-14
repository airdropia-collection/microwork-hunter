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
Two pattern sets are maintained:

1. ``BLOCKLIST`` — phrases that indicate manual intervention is required.
   Matched (case-insensitive) against the task's title, description,
   requirements, and tags. If ANY blocklist pattern matches, the task
   is rejected.

2. ``ALLOWLIST`` — phrases that strongly indicate the task is
   auto-completable. Used for the ``confidence`` score, not for the
   final decision (the absence of blocklist matches is enough).
"""
from __future__ import annotations

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

    def __init__(self):
        # Compile patterns once at construction
        self._block_patterns = [
            re.compile(p, re.IGNORECASE) for p in BLOCKLIST
        ]
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

        # 1. Check blocklist (any match -> reject)
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

        # 2. Score confidence using allowlist
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
