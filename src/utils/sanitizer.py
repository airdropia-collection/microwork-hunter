"""
Secret sanitizer for safe error logging.

Use ``sanitize(obj)`` before passing an exception or any dict to the
logger to ensure cookies, tokens, and PII never end up in CI logs.
"""
from __future__ import annotations

import re
from typing import Any

# Patterns that should never appear in logs
_SECRET_PATTERNS = [
    # GitHub PATs (classic + fine-grained)
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36,255}", re.IGNORECASE),
    re.compile(r"github_pat_[A-Za-z0-9_]{22,255}", re.IGNORECASE),
    # Long hex/base64 tokens (>= 32 chars, looks like a token)
    re.compile(r"\b[A-Za-z0-9+/=_-]{40,}\b"),
    # Email addresses
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    # LTC / BTC addresses (rough)
    re.compile(r"\b(?:ltc|btc|bc1)[a-z0-9]{20,}\b", re.IGNORECASE),
    # Common cookie key names followed by a value
    re.compile(r"(?i)(session|sessid|csrf|auth|token|cookie|password|secret)[\"']?\s*[:=]\s*[\"']?[^\"'\s,}]+"),
]

_REDACTED = "REDACTED"


def sanitize(value: Any, max_len: int = 500) -> Any:
    """
    Recursively redact anything that looks like a secret.

    Truncates long strings to ``max_len`` chars to keep logs readable.
    """
    if isinstance(value, str):
        return _sanitize_str(value, max_len)
    if isinstance(value, dict):
        return {k: sanitize(v, max_len) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        sanitized = [sanitize(v, max_len) for v in value]
        return type(value)(sanitized) if not isinstance(value, set) else set(sanitized)
    if isinstance(value, BaseException):
        return _sanitize_str(str(value), max_len)
    return value


def _sanitize_str(text: str, max_len: int) -> str:
    out = text
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub(_REDACTED, out)
    if len(out) > max_len:
        out = out[:max_len] + f"...<truncated {len(out) - max_len} chars>"
    return out


def is_safe_to_log(text: str) -> bool:
    """Return True if ``text`` contains no detected secret patterns."""
    return not any(p.search(text) for p in _SECRET_PATTERNS)
