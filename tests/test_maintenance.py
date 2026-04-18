#!/usr/bin/env python3
"""Tests for maintenance.py"""

import json, sys, tempfile, shutil, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from importlib import import_module
save_mod = import_module("save-session")
maint = import_module("maintenance")


class TestBase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.kb = Path(self.tmpdir) / "Nate's-kb"
        (self.kb / "Intelligence").mkdir(parents=True)

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


class TestJaccard(TestBase):
    def test_identical(self):
        self.assertAlmostEqual(maint.jaccard("hello world", "hello world"), 1.0)

    def test_no_overlap(self):
        self.assertAlmostEqual(maint.jaccard("hello world", "foo bar"), 0.0)

    def test_partial(self):
        sim = maint.jaccard("hello world foo", "hello world bar")
        self.assertGreater(sim, 0.3)
        self.assertLess(sim, 1.0)


class TestAutoFixes(TestBase):
    def test_fixes_lastAccessed_before_created(self):
        self.write_json(self.kb / "Intelligence" / "knowledge.json", {
            "entries": [{"id": "know-1", "category": "technical", "content": "test",
                        "confidence": 0.8, "tags": [], "created": "2026-04-01",
                        "lastAccessed": "2026-01-01", "accessCount": 0}],
            "lastUpdated": "2026-01-01"
        })
        fixed, _ = maint.check_store(self.kb, "knowledge", fix=True)
        self.assertTrue(any(f["type"] == "lastAccessed_before_created" for f in fixed))
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertEqual(store["entries"][0]["lastAccessed"], "2026-04-01")

    def test_fixes_negative_accessCount(self):
        self.write_json(self.kb / "Intelligence" / "knowledge.json", {
            "entries": [{"id": "know-1", "category": "technical", "content": "test",
                        "confidence": 0.8, "tags": [], "created": "2026-01-01",
                        "lastAccessed": "2026-01-01", "accessCount": -5}],
            "lastUpdated": "2026-01-01"
        })
        fixed, _ = maint.check_store(self.kb, "knowledge", fix=True)
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertEqual(store["entries"][0]["accessCount"], 0)

    def test_deduplicates_tags(self):
        self.write_json(self.kb / "Intelligence" / "knowledge.json", {
            "entries": [{"id": "know-1", "category": "technical", "content": "test",
                        "confidence": 0.8, "tags": ["aws", "aws", "lambda"],
                        "created": "2026-01-01", "lastAccessed": "2026-01-01", "accessCount": 0}],
            "lastUpdated": "2026-01-01"
        })
        fixed, _ = maint.check_store(self.kb, "knowledge", fix=True)
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertEqual(len(store["entries"][0]["tags"]), 2)

    def test_fixes_index_stats_mismatch(self):
        self.write_json(self.kb / "Intelligence" / "knowledge.json", {
            "entries": [{"id": "know-1", "category": "technical", "content": "test",
                        "confidence": 0.8, "tags": [], "created": "2026-01-01",
                        "lastAccessed": "2026-01-01", "accessCount": 0}],
            "lastUpdated": "2026-01-01"
        })
        # Index says 0 but store has 1
        fixed, _ = maint.check_store(self.kb, "knowledge", fix=True)
        self.assertTrue(any(f["type"] == "index_stats_mismatch" for f in fixed))
        idx = self.read_json(self.kb / "Intelligence" / "knowledge-index.json")
        self.assertEqual(idx["stats"]["totalEntries"], 1)


class TestNeedsReview(TestBase):
    def test_low_confidence(self):
        self.write_json(self.kb / "Intelligence" / "knowledge.json", {
            "entries": [{"id": "know-1", "category": "technical", "content": "test",
                        "confidence": 0.2, "tags": [], "created": "2026-01-01",
                        "lastAccessed": "2026-01-01", "accessCount": 0}],
            "lastUpdated": "2026-01-01"
        })
        _, review = maint.check_store(self.kb, "knowledge")
        self.assertTrue(any(r["type"] == "low_confidence" for r in review))

    def test_near_duplicate(self):
        self.write_json(self.kb / "Intelligence" / "knowledge.json", {
            "entries": [
                {"id": "know-1", "category": "technical", "content": "the quick brown fox jumps over the lazy dog today",
                 "confidence": 0.8, "tags": [], "created": "2026-01-01", "lastAccessed": "2026-01-01", "accessCount": 0},
                {"id": "know-2", "category": "technical", "content": "the quick brown fox jumps over the lazy dog now",
                 "confidence": 0.8, "tags": [], "created": "2026-01-01", "lastAccessed": "2026-01-01", "accessCount": 0}
            ], "lastUpdated": "2026-01-01"
        })
        _, review = maint.check_store(self.kb, "knowledge")
        self.assertTrue(any(r["type"] == "near_duplicate" for r in review))


class TestCrossRefCheck(TestBase):
    def test_orphaned_cross_ref(self):
        self.write_json(self.kb / "Intelligence" / "cross-references.json", {
            "_meta": {"last_updated": "2026-01-01"},
            "references": {"know-999": {"referenced_by": ["reason-1"], "related_to": []}},
            "stats": {}
        })
        orphaned = maint.check_cross_references(self.kb)
        self.assertTrue(any("know-999" in o["detail"] for o in orphaned))


if __name__ == "__main__":
    unittest.main()
