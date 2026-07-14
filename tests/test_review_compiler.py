"""Tests for review_compiler."""
import json
from pathlib import Path


def test_compile_review_package(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "result_a.json").write_text(
        json.dumps({"task_id": "a", "status": "dry_run"})
    )
    (tmp_path / "result_b.json").write_text(
        json.dumps({"task_id": "b", "status": "completed"})
    )
    (tmp_path / "result_c.json").write_text(
        json.dumps({"task_id": "c", "status": "failed"})
    )
    (tmp_path / "discovery_log.json").write_text(
        json.dumps({"total_found": 3})
    )

    from src.utils.review_compiler import compile_review_package

    pkg = compile_review_package()
    assert pkg["discovered"] == 3
    assert pkg["attempted"] == 3
    assert pkg["successful"] == 1
    assert pkg["failed"] == 1
    assert len(pkg["pending"]) == 1
    assert pkg["pending"][0]["task_id"] == "a"
    assert (tmp_path / "review_package.json").exists()
