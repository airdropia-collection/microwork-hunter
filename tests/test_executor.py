"""Tests for the TaskExecutor payload coercion logic (no browser needed)."""
import json
from pathlib import Path
from unittest.mock import patch

from src.workers.executor import _coerce_to_task_list, TaskExecutor


def test_coerce_single_dict():
    payload = {"id": "x", "platform": "sproutgigs"}
    out = _coerce_to_task_list(payload)
    assert out == [payload]


def test_coerce_list():
    payload = [{"id": "x"}, {"id": "y"}]
    out = _coerce_to_task_list(payload)
    assert out == payload


def test_coerce_dict_with_tasks_key():
    payload = {"tasks": [{"id": "x"}], "meta": "ok"}
    out = _coerce_to_task_list(payload)
    assert out == [{"id": "x"}]


def test_coerce_invalid_type():
    try:
        _coerce_to_task_list("not a dict")
    except TypeError:
        return
    assert False, "expected TypeError"


def test_executor_unknown_platform():
    ex = TaskExecutor(dry_run=True)
    res = ex.execute_task({"id": "x", "platform": "unknown_platform"})
    assert res["status"] == "error"
    assert "Unknown platform" in res["error"]


def test_executor_many_persists_results(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ex = TaskExecutor(dry_run=True)
    fake_tasks = [
        {"id": "t1", "platform": "sproutgigs", "type": "x"},
        {"id": "t2", "platform": "coinpayu", "type": "ptc_ad"},
    ]
    with patch.object(TaskExecutor, "execute_task") as mock_exec:
        mock_exec.side_effect = lambda t: {"task_id": t["id"], "status": "dry_run"}
        results = ex.execute_many(fake_tasks)
    assert len(results) == 2
    assert (tmp_path / "result_t1.json").exists()
    assert (tmp_path / "result_t2.json").exists()
