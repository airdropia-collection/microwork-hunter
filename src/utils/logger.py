"""
Centralised logging configuration.

Every module should do:

    import logging
    log = logging.getLogger("microwork.<module>")

instead of using ``print()``. The actual configuration happens once at
import time of this module, controlled by env vars:

    LOG_LEVEL   default INFO  (one of DEBUG | INFO | WARNING | ERROR)
    LOG_FORMAT  default rich  (one of rich | plain | json)
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_FORMAT = os.getenv("LOG_FORMAT", "rich").lower()

# Map string -> numeric level with safe fallback
_LEVEL_NUM = getattr(logging, _LEVEL, logging.INFO)

# Unique logger name for the whole project
ROOT_LOGGER_NAME = "microwork"


class _OneLineFormatter(logging.Formatter):
    """Force every log message onto a single line (great for CI logs)."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        msg = super().format(record)
        return " ".join(msg.splitlines())


def _build_handler() -> logging.Handler:
    """Pick the best available handler for the environment."""
    if _FORMAT == "json":
        # Lightweight JSON formatter — no extra deps
        import json
        import time

        class _JsonFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                payload = {
                    "ts": time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)
                    ),
                    "level": record.levelname,
                    "logger": record.name,
                    "msg": record.getMessage(),
                }
                if record.exc_info:
                    payload["exc"] = self.formatException(record.exc_info)
                return json.dumps(payload, default=str)

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_JsonFormatter())
        return handler

    if _FORMAT == "rich":
        try:
            from rich.logging import RichHandler  # type: ignore

            handler = RichHandler(
                show_time=True,
                show_level=True,
                show_path=False,
                markup=True,
                rich_tracebacks=True,
            )
            return handler
        except ImportError:
            # Fall through to plain
            pass

    # Plain formatter — works everywhere
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        _OneLineFormatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    return handler


def _configure_root() -> logging.Logger:
    root = logging.getLogger(ROOT_LOGGER_NAME)
    if root.handlers:  # already configured
        return root
    root.setLevel(_LEVEL_NUM)
    root.addHandler(_build_handler())
    # Prevent double-printing via root logger
    root.propagate = False
    return root


# Configure on import
_configure_root()


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger under the project root.

    Usage:
        from src.utils.logger import get_logger
        log = get_logger("platforms.sproutgigs")
        log.info("Discovered %d tasks", n)
    """
    if name.startswith(ROOT_LOGGER_NAME + "."):
        return logging.getLogger(name)
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")


def silence_noisy_libs() -> None:
    """Quiet down chatty third-party loggers."""
    for noisy in ("urllib3", "playwright", "asyncio", "chardet", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
