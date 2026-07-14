"""Platform adapters for microwork sites."""

from .base import BasePlatform, MicroworkTask
from .sproutgigs import SproutGigsPlatform
from .rewardjoy import RewardJoyPlatform
from .timebucks import TimeBucksPlatform
from .prizerebel import PrizeRebelPlatform
from .cointiply import CointiplyPlatform

__all__ = [
    "BasePlatform",
    "MicroworkTask",
    "SproutGigsPlatform",
    "RewardJoyPlatform",
    "TimeBucksPlatform",
    "PrizeRebelPlatform",
    "CointiplyPlatform",
]
