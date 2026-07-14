"""Tests for the ReviewHandler command parser."""
import json
from pathlib import Path

from src.workers.review_handler import ReviewHandler


def _write_package(tmp_path: Path, pending):
    pkg = {
        "discovered": len(pending),
        "attempted": len(pending),
        "successful": 0,
        "failed": 0,
        "pending": pending,
        "completed": [],
        "failed_tasks": [],
        "summary": "test",
    }
    p = tmp_path / "review_package.json"
    p.write_text(json.dumps(pkg), encoding="utf-8")
    return p


def test_approve_all(tmp_path):
    pending = [
        {"task_id": "sg_1", "platform": "sproutgigs", "reward": 0.5},
        {"task_id": "cp_1", "platform": "coinpayu", "reward": 100},
    ]
    pkg = _write_package(tmp_path, pending)
    h = ReviewHandler(package_path=pkg)
    res = h.process_comment("/approve all", "alice", 42)
    assert res["status"] == "approved"
    assert res["scope"] == "all"
    assert res["action"] == "submit_all"
    assert len(res["tasks"]) == 2
    assert "alice" in res["summary"]


def test_approve_specific(tmp_path):
    pending = [
        {"task_id": "sg_1", "platform": "sproutgigs"},
        {"task_id": "cp_1", "platform": "coinpayu"},
    ]
    pkg = _write_package(tmp_path, pending)
    h = ReviewHandler(package_path=pkg)
    res = h.process_comment("/approve sg_1", "bob", 7)
    assert res["status"] == "approved"
    assert res["scope"] == "specific"
    assert res["task_ids"] == ["sg_1"]
    assert len(res["tasks"]) == 1


def test_approve_specific_missing(tmp_path):
    pending = [{"task_id": "sg_1", "platform": "sproutgigs"}]
    pkg = _write_package(tmp_path, pending)
    h = ReviewHandler(package_path=pkg)
    res = h.process_comment("/approve sg_1 nope_99", "bob", 7)
    assert res["status"] == "approved"
    assert res["missing"] == ["nope_99"]
    assert len(res["tasks"]) == 1


def test_reject_with_reason(tmp_path):
    pending = [{"task_id": "sg_1", "platform": "sproutgigs"}]
    pkg = _write_package(tmp_path, pending)
    h = ReviewHandler(package_path=pkg)
    res = h.process_comment("/reject sg_1 looks spammy", "carol", 9)
    assert res["status"] == "rejected"
    assert res["task_id"] == "sg_1"
    assert res["reason"] == "looks spammy"
    assert res["action"] == "reject"


def test_reject_no_reason(tmp_path):
    pending = [{"task_id": "sg_1", "platform": "sproutgigs"}]
    pkg = _write_package(tmp_path, pending)
    h = ReviewHandler(package_path=pkg)
    res = h.process_comment("/reject sg_1", "carol", 9)
    assert res["reason"] == "No reason provided"


def test_modify_requires_instructions(tmp_path):
    pending = [{"task_id": "sg_1", "platform": "sproutgigs"}]
    pkg = _write_package(tmp_path, pending)
    h = ReviewHandler(package_path=pkg)
    res = h.process_comment("/modify sg_1", "carol", 9)
    assert res["status"] == "error"


def test_modify_ok(tmp_path):
    pending = [{"task_id": "sg_1", "platform": "sproutgigs"}]
    pkg = _write_package(tmp_path, pending)
    h = ReviewHandler(package_path=pkg)
    res = h.process_comment("/modify sg_1 use persona X", "carol", 9)
    assert res["status"] == "modify"
    assert res["instructions"] == "use persona X"


def test_unknown_command(tmp_path):
    pkg = _write_package(tmp_path, [])
    h = ReviewHandler(package_path=pkg)
    res = h.process_comment("hello there", "dave", 1)
    assert res["status"] == "ignored"
    assert res["action"] == "noop"


def test_case_insensitive(tmp_path):
    pending = [{"task_id": "sg_1", "platform": "sproutgigs"}]
    pkg = _write_package(tmp_path, pending)
    h = ReviewHandler(package_path=pkg)
    res = h.process_comment("/APPROVE ALL", "alice", 1)
    assert res["status"] == "approved"
    assert res["scope"] == "all"


def test_missing_package(tmp_path):
    """If review_package.json does not exist, handler still returns sane results."""
    h = ReviewHandler(package_path=tmp_path / "does_not_exist.json")
    res = h.process_comment("/approve all", "alice", 1)
    assert res["status"] == "approved"
    assert res["tasks"] == []
