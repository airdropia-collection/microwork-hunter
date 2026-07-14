"""Tests for TaskState deduplication logic."""
from src.utils.state import TaskState


def test_empty_state(tmp_path):
    s = TaskState(path=tmp_path / "state.json")
    assert not s.is_done("anything")
    assert s.filter_pending([{"id": "x"}]) == [{"id": "x"}]


def test_mark_done_then_is_done(tmp_path):
    s = TaskState(path=tmp_path / "state.json")
    s.mark_done("t1", "sproutgigs", "dry_run", 0.5)
    assert s.is_done("t1")
    assert not s.is_done("t2")


def test_filter_pending_skips_done(tmp_path):
    s = TaskState(path=tmp_path / "state.json")
    s.mark_done("t1", "sproutgigs", "dry_run")
    tasks = [{"id": "t1"}, {"id": "t2"}, {"id": "t3"}]
    fresh = s.filter_pending(tasks)
    assert fresh == [{"id": "t2"}, {"id": "t3"}]


def test_state_persists_across_instances(tmp_path):
    p = tmp_path / "state.json"
    s1 = TaskState(path=p)
    s1.mark_done("t1", "sproutgigs", "dry_run")
    s2 = TaskState(path=p)
    assert s2.is_done("t1")


def test_prune_removes_old_entries(tmp_path):
    p = tmp_path / "state.json"
    s = TaskState(path=p, ttl_hours=1)
    # Manually inject an old entry
    s._data["tasks"] = {
        "old": {
            "platform": "sproutgigs",
            "completed_at": "2000-01-01T00:00:00+00:00",  # ancient
            "status": "dry_run",
        },
        "new": {
            "platform": "sproutgigs",
            "completed_at": "2099-01-01T00:00:00+00:00",  # future
            "status": "dry_run",
        },
    }
    s._save()
    pruned = s.prune()
    assert pruned == 1
    assert not s.is_done("old")
    assert s.is_done("new")
