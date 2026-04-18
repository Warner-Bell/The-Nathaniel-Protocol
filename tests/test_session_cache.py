"""Tests for session-cache.py"""
import json
import os
import sqlite3
import sys
from pathlib import Path

import pytest

# Import the module directly
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import importlib
sc_path = Path(__file__).parent.parent / "scripts" / "session-cache.py"
spec = importlib.util.spec_from_file_location("session_cache", str(sc_path))
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

SAMPLE_INDEX = {
    "_meta": {"description": "test"},
    "sessions": [
        {"id": "s-001", "date": "2026-04-16", "tags": ["golden-seed", "template"],
         "summary": "Built GOLDEN seed corpus", "outcome": "success", "outcome_note": "783 entries"},
        {"id": "s-002", "date": "2026-04-15", "tags": ["my-project", "deep-work"],
         "summary": "Deep work on project spec", "outcome": "success", "outcome_note": "Spec complete"},
        {"id": "s-003", "date": "2026-04-14", "tags": ["transit-test", "bug-fix"],
         "summary": "Transit test with bug fixes", "outcome": "partial", "outcome_note": "E2E pending"},
        {"id": "s-004", "date": "2026-04-13", "tags": ["my-project", "route-f"],
         "summary": "Route F on project spec", "outcome": "success", "outcome_note": "Fixed"},
        {"id": "s-005", "date": "2026-04-12", "tags": ["template", "review"],
         "summary": "Template final review and cleanup", "outcome": "blocked", "outcome_note": "Permissions"},
    ],
    "_schema": {"version": "1.0"}, "recentIds": ["s-001"]
}


@pytest.fixture
def env(tmp_path):
    """Set up temp KB and patch module paths."""
    kb = tmp_path / "Nate's-kb"
    mem = kb / "Memory"
    mem.mkdir(parents=True)
    with open(mem / "session-index.json", "w") as f:
        json.dump(SAMPLE_INDEX, f)
    # Patch module-level paths
    sc.KB_ROOT = kb
    sc.INDEX_PATH = mem / "session-index.json"
    sc.CACHE_DIR = mem / "cache"
    sc.DB_PATH = mem / "cache" / "sessions.db"
    sc.SENTINEL = mem / "cache" / ".invalidated"
    return tmp_path


def test_rebuild_from_index(env):
    sc.rebuild()
    assert sc.DB_PATH.exists()
    conn = sqlite3.connect(str(sc.DB_PATH))
    count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    conn.close()
    assert count == 5


def test_stats_output(env):
    sc.rebuild()
    conn, has_fts5, _ = sc.ensure_cache()
    result = sc.stats(conn)
    conn.close()
    assert result["total_sessions"] == 5
    assert result["outcomes"]["success"] == 3
    assert result["outcomes"]["partial"] == 1
    assert result["outcomes"]["blocked"] == 1
    assert result["date_range"] == ["2026-04-12", "2026-04-16"]


def test_query_by_tag(env):
    sc.rebuild()
    conn, has_fts5, _ = sc.ensure_cache()
    results = sc.query(conn, has_fts5, {"tags": ["my-project"]})
    conn.close()
    assert len(results) == 2
    ids = {r["id"] for r in results}
    assert ids == {"s-002", "s-004"}


def test_query_by_multiple_tags(env):
    sc.rebuild()
    conn, has_fts5, _ = sc.ensure_cache()
    results = sc.query(conn, has_fts5, {"tags": ["golden-seed", "transit-test"]})
    conn.close()
    assert len(results) == 2  # OR logic


def test_query_by_date_range(env):
    sc.rebuild()
    conn, has_fts5, _ = sc.ensure_cache()
    results = sc.query(conn, has_fts5, {"date_from": "2026-04-15", "date_to": "2026-04-16"})
    conn.close()
    assert len(results) == 2
    for r in results:
        assert r["date"] >= "2026-04-15"


def test_query_by_keyword(env):
    sc.rebuild()
    conn, has_fts5, _ = sc.ensure_cache()
    results = sc.query(conn, has_fts5, {"keyword": "GOLDEN seed"})
    conn.close()
    assert len(results) >= 1
    assert any("GOLDEN" in r["summary"] for r in results)


def test_query_by_outcome(env):
    sc.rebuild()
    conn, has_fts5, _ = sc.ensure_cache()
    results = sc.query(conn, has_fts5, {"outcome": "partial"})
    conn.close()
    assert len(results) == 1
    assert results[0]["outcome"] == "partial"


def test_combined_filters(env):
    sc.rebuild()
    conn, has_fts5, _ = sc.ensure_cache()
    results = sc.query(conn, has_fts5, {"tags": ["my-project"], "outcome": "success"})
    conn.close()
    assert len(results) == 2
    for r in results:
        assert r["outcome"] == "success"
        assert "my-project" in r["tags"]


def test_limit(env):
    sc.rebuild()
    conn, has_fts5, _ = sc.ensure_cache()
    results = sc.query(conn, has_fts5, {"limit": 2})
    conn.close()
    assert len(results) <= 2


def test_sentinel_triggers_rebuild(env):
    sc.rebuild()
    sc.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    sc.SENTINEL.touch()
    conn, has_fts5, was_rebuilt = sc.ensure_cache()
    conn.close()
    assert was_rebuilt is True
    assert not sc.SENTINEL.exists()


def test_sentinel_deleted_after_rebuild(env):
    sc.rebuild()
    assert not sc.SENTINEL.exists()


def test_missing_cache_auto_rebuild(env):
    # Don't rebuild — cache doesn't exist
    conn, has_fts5, was_rebuilt = sc.ensure_cache()
    count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    conn.close()
    assert was_rebuilt is True
    assert count == 5


def test_corrupt_cache_recovery(env):
    sc.rebuild()
    with open(sc.DB_PATH, "w") as f:
        f.write("corrupt")
    conn, has_fts5, was_rebuilt = sc.ensure_cache()
    count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    conn.close()
    assert was_rebuilt is True
    assert count == 5


def test_empty_index(env):
    with open(sc.INDEX_PATH, "w") as f:
        json.dump({"sessions": []}, f)
    sc.rebuild()
    conn, has_fts5, _ = sc.ensure_cache()
    result = sc.stats(conn)
    conn.close()
    assert result["total_sessions"] == 0


def test_empty_keyword_treated_as_absent(env):
    sc.rebuild()
    conn, has_fts5, _ = sc.ensure_cache()
    results = sc.query(conn, has_fts5, {"keyword": "", "limit": 10})
    conn.close()
    assert len(results) == 5  # All sessions returned


def test_sort_order_date_desc(env):
    sc.rebuild()
    conn, has_fts5, _ = sc.ensure_cache()
    results = sc.query(conn, has_fts5, {"limit": 10})
    conn.close()
    dates = [r["date"] for r in results]
    assert dates == sorted(dates, reverse=True)


def test_duplicate_ids_handled(env):
    """Duplicate session IDs should be handled via INSERT OR REPLACE."""
    idx = SAMPLE_INDEX.copy()
    idx["sessions"] = list(SAMPLE_INDEX["sessions"]) + [
        {"id": "s-001", "date": "2026-04-16", "tags": ["dupe"],
         "summary": "Duplicate entry", "outcome": "success", "outcome_note": "dupe"}
    ]
    with open(sc.INDEX_PATH, "w") as f:
        json.dump(idx, f)
    sc.rebuild()
    conn = sqlite3.connect(str(sc.DB_PATH))
    count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    conn.close()
    assert count == 5  # Dupe replaced, not added
