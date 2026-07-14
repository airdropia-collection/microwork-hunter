"""
Retry decorators built on ``tenacity``.

Wrap any network-call function with ``@retry_network()`` to get
exponential backoff for transient failures.
"""
from __future__ import annotations

from typing import Callable

try:
    from tenacity import (
        RetryError,
        retry,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential_jitter,
    )
except ImportError:  # pragma: no cover
    # tenacity is in requirements.txt but be defensive
    retry = None  # type: ignore
    RetryError = Exception  # type: ignore

from src.utils.logger import get_logger

log = get_logger("retry")


def retry_network(max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 8.0):
    """
    Decorator: retry on ``Exception`` with exponential backoff + jitter.

    Use on:
        - HTTP calls (requests / httpx / aiohttp)
        - Playwright page.goto / click
        - LLM API calls (Gemini / Groq)
    """
    if retry is None:
        # No tenacity — return identity decorator
        def _identity(fn: Callable) -> Callable:
            return fn
        return _identity

    return retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(initial=base_delay, max=max_delay),
        before_sleep=lambda rs: log.warning(
            "%s: attempt %d failed, retrying in %.1fs (%s)",
            rs.fn.__name__ if rs.fn else "?",
            rs.attempt_number,
            rs.outcome_timestamp - rs.previous_state.outcome_timestamp
            if rs.previous_state
            else 0.0,
            rs.outcome.exception() if rs.outcome.failed else "",
        ),
        reraise=True,
    )
