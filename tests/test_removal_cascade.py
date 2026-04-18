#!/usr/bin/env python3
"""Tests for removal-cascade.py"""

import json, sys, tempfile, shutil, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from importlib import import_module
save_mod = import_module("save-session")
removal = import_module("removal-cascade")


class TestBase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.kb = Path(self.tmpdir) / "Nate's-kb"
        (self.kb / "Intelligence").mkdir(parents=True)
        (self.kb / "Memory").mkdir(parents=True)

        for store in ("patterns", "knowledge", "reasoning"):
            self.write_json(self.kb / "Intelligence" / f"{store}.json", {"entries": [], "lastUpdated": "2026-01-01"})
            self.write_json(self.kb / "Intelligence" / f"{store}-index.json",
                           {"stats": {"totalEntries": 0, "nextId": 1 if store != "patterns" else {}},
                            "byTag": {}, "summaries": {}, "recentIds": []})

        self.write_json(self.kb / "Intelligence" / "cross-references.json",
                       {"_meta": {"last_updated": "2026-01-01"}, "references": {}, "stats": {}})

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def write_json(self, path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def read_json(self, path):
        with open(path) as f:
            return json.load(f)


class TestValidation(TestBase):
    def test_empty_remove(self):
        self.assertTrue(len(removal.validate_ops({"remove": []})) > 0)

    def test_merge_target_in_remove(self):
        errors = removal.validate_ops({"remove": ["know-1"], "merge_tags_to": "know-1"})
        self.assertTrue(any("cannot be in the remove list" in e for e in errors))

    def test_valid(self):
        self.assertEqual(removal.validate_ops({"remove": ["know-1"]}), [])


class TestDetectStore(TestBase):
    def test_knowledge(self):
        self.assertEqual(removal.detect_store("know-123"), "knowledge")

    def test_reasoning(self):
        self.assertEqual(removal.detect_store("reason-45"), "reasoning")

    def test_pattern(self):
        self.assertEqual(removal.detect_store("pref_10"), "patterns")
        self.assertEqual(removal.detect_store("fail_5"), "patterns")


class TestRemoval(TestBase):
    def test_removes_entry(self):
        self.write_json(self.kb / "Intelligence" / "knowledge.json", {
            "entries": [
                {"id": "know-1", "category": "technical", "content": "keep", "confidence": 0.8, "tags": []},
                {"id": "know-2", "category": "technical", "content": "remove", "confidence": 0.8, "tags": []}
            ], "lastUpdated": "2026-01-01"
        })
        removed, affected = removal.remove_entries(self.kb, ["know-2"])
        self.assertEqual(removed, 1)
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertEqual(len(store["entries"]), 1)
        self.assertEqual(store["entries"][0]["id"], "know-1")


class TestTagMerge(TestBase):
    def test_merges_tags(self):
        self.write_json(self.kb / "Intelligence" / "knowledge.json", {
            "entries": [
                {"id": "know-1", "category": "technical", "content": "target", "confidence": 0.8, "tags": ["existing"]},
                {"id": "know-2", "category": "technical", "content": "source", "confidence": 0.8, "tags": ["new-tag", "existing"]}
            ], "lastUpdated": "2026-01-01"
        })
        removal.merge_tags(self.kb, {"know-2"}, "know-1")
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        target = [e for e in store["entries"] if e["id"] == "know-1"][0]
        self.assertIn("new-tag", target["tags"])
        self.assertIn("existing", target["tags"])


class TestCrossRefCleanup(TestBase):
    def test_removes_keys_and_refs(self):
        self.write_json(self.kb / "Intelligence" / "cross-references.json", {
            "_meta": {"last_updated": "2026-01-01"},
            "references": {
                "know-1": {"referenced_by": ["reason-1", "reason-2"], "related_to": []},
                "know-2": {"referenced_by": ["reason-1"], "related_to": []}
            },
            "stats": {}
        })
        cleaned = removal.clean_cross_references(self.kb, ["know-2", "reason-1"])
        xref = self.read_json(self.kb / "Intelligence" / "cross-references.json")
        self.assertNotIn("know-2", xref["references"])
        self.assertNotIn("reason-1", xref["references"]["know-1"]["referenced_by"])
        self.assertIn("reason-2", xref["references"]["know-1"]["referenced_by"])


class TestDerivedFromCleanup(TestBase):
    def test_cleans_derived_from(self):
        self.write_json(self.kb / "Intelligence" / "reasoning.json", {
            "entries": [
                {"id": "reason-1", "type": "deduction", "content": "test", "intent": "test",
                 "reuse_signal": "test", "confidence": 0.8, "tags": [], "provenance": "stated",
                 "derived_from": ["know-1", "know-2"], "created": "2026-01-01",
                 "lastAccessed": "2026-01-01", "accessCount": 0}
            ], "lastUpdated": "2026-01-01"
        })
        affected = removal.clean_derived_from(self.kb, ["know-2"])
        self.assertEqual(affected, ["reason-1"])
        store = self.read_json(self.kb / "Intelligence" / "reasoning.json")
        self.assertEqual(store["entries"][0]["derived_from"], ["know-1"])


if __name__ == "__main__":
    unittest.main()
