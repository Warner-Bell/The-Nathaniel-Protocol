"""Regression tests for kb_query._load_synonyms (synonym-map.json expansion).

Guards two defects found 2026-11-10: a group's key term was never expanded (only the
listed values were), and a term listed in two groups kept only the later group.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import kb_query  # noqa: E402


def _load(tmp_path, monkeypatch, synonyms):
    p = tmp_path / "synonym-map.json"
    p.write_text(json.dumps({"_meta": {}, "synonyms": synonyms}))
    monkeypatch.setattr(kb_query, "SYNONYM_PATH", str(p))
    return kb_query._load_synonyms()


def test_group_key_expands(tmp_path, monkeypatch):
    m = _load(tmp_path, monkeypatch, {"memory": ["recall", "persistence"]})
    assert m["memory"] == ["persistence", "recall"]
    assert "memory" in m["recall"]


def test_term_in_two_groups_gets_union(tmp_path, monkeypatch):
    m = _load(tmp_path, monkeypatch, {"save": ["checkpoint"], "commit": ["checkpoint"]})
    assert set(m["checkpoint"]) == {"save", "commit"}


def test_case_and_self_excluded(tmp_path, monkeypatch):
    m = _load(tmp_path, monkeypatch, {"Kernel": ["kernel", "Steering"]})
    assert m["kernel"] == ["steering"]
    assert "kernel" not in m["kernel"]


def test_missing_file_is_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(kb_query, "SYNONYM_PATH", str(tmp_path / "nope.json"))
    assert kb_query._load_synonyms() == {}


def test_shipped_map_keys_expand():
    """Every group key in the shipped map now expands to at least one term."""
    with open(kb_query.SYNONYM_PATH, encoding="utf-8") as f:
        syn = json.load(f).get("synonyms", {})
    m = kb_query._load_synonyms()
    dead = [k for k, v in syn.items() if v and not m.get(k.lower())]
    assert not dead, dead
