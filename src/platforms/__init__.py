"""Platform adapters for microwork sites."""

from .base import BasePlatform, MicroworkTask
from .sproutgigs import SproutGigsPlatform
from .coinpayu import CoinPayuPlatform
from .timebucks import TimeBucksPlatform
from .prizerebel import PrizeRebelPlatform

__all__ = [
    "BasePlatform",
    "MicroworkTask",
    "SproutGigsPlatform",
    "CoinPayuPlatform",
    "TimeBucksPlatform",
    "PrizeRebelPlatform",
]
