"""Tests for MicroworkTask dataclass."""
from src.platforms.base import MicroworkTask


def test_task_defaults():
    t = MicroworkTask(
        id="x",
        platform="sproutgigs",
        type="microjob",
        title="Test",
        description="d",
        reward=0.5,
        reward_currency="USD",
        estimated_time=5,
        difficulty="easy",
        url="https://example.com",
    )
    assert t.requirements == []
    assert t.tags == []
    assert t.screenshot is None


def test_task_to_dict_roundtrip():
    t = MicroworkTask(
        id="x",
        platform="sproutgigs",
        type="microjob",
        title="Test",
        description="d",
        reward=0.5,
        reward_currency="USD",
        estimated_time=5,
        difficulty="easy",
        url="https://example.com",
        requirements=["a", "b"],
        tags=["t1"],
    )
    d = t.to_dict()
    assert d["id"] == "x"
    assert d["requirements"] == ["a", "b"]
    assert d["tags"] == ["t1"]
