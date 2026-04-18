#!/usr/bin/env python3
"""Tests for cascade-correction.py"""

import json, sys, tempfile, shutil, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from importlib import import_module
save_mod = import_module("save-session")
cascade = import_module("cascade-correction")


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

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def write_json(self, path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def read_json(self, path):
        with open(path) as f:
            return json.load(f)

    def seed_knowledge(self, entries):
        self.write_json(self.kb / "Intelligence" / "knowledge.json",
                       {"entries": entries, "lastUpdated": "2026-01-01"})


class TestValidation(TestBase):
    def test_missing_keywords(self):
        self.assertTrue(len(cascade.validate_ops({"mode": "scan"})) > 0)

    def test_missing_mode(self):
        self.assertTrue(len(cascade.validate_ops({"old_keywords": ["x"]})) > 0)

    def test_apply_needs_new_value(self):
        errors = cascade.validate_ops({"old_keywords": ["x"], "mode": "apply", "approved_ids": ["know-1"]})
        self.assertTrue(any("new_value" in e for e in errors))

    def test_valid_scan(self):
        self.assertEqual(cascade.validate_ops({"old_keywords": ["x"], "mode": "scan"}), [])


class TestScan(TestBase):
    def test_finds_in_content(self):
        self.seed_knowledge([
            {"id": "know-1", "category": "technical", "content": "Use python3 for scripts",
             "confidence": 0.8, "tags": ["python"], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 1}
        ])
        matches, total = cascade.scan_stores(self.kb, ["python3"], ["knowledge"])
        self.assertEqual(total, 1)
        self.assertEqual(matches[0]["id"], "know-1")

    def test_finds_in_tags(self):
        self.seed_knowledge([
            {"id": "know-1", "category": "technical", "content": "Some content",
             "confidence": 0.8, "tags": ["old-tag"], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 1}
        ])
        matches, total = cascade.scan_stores(self.kb, ["old-tag"], ["knowledge"])
        self.assertEqual(total, 1)

    def test_case_insensitive(self):
        self.seed_knowledge([
            {"id": "know-1", "category": "technical", "content": "Use PYTHON3",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 1}
        ])
        matches, total = cascade.scan_stores(self.kb, ["python3"], ["knowledge"])
        self.assertEqual(total, 1)

    def test_limit_respected(self):
        entries = [{"id": f"know-{i}", "category": "technical", "content": f"python3 entry {i}",
                    "confidence": 0.8, "tags": [], "created": "2026-01-01",
                    "lastAccessed": "2026-01-01", "accessCount": 0} for i in range(20)]
        self.seed_knowledge(entries)
        matches, total = cascade.scan_stores(self.kb, ["python3"], ["knowledge"], limit=5)
        self.assertEqual(len(matches), 5)
        self.assertEqual(total, 20)


class TestApply(TestBase):
    def test_replaces_in_content(self):
        self.seed_knowledge([
            {"id": "know-1", "category": "technical", "content": "Use python3 for scripts",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 1}
        ])
        applied, _, _ = cascade.apply_fixes(self.kb, ["python3"], "python", ["know-1"], ["knowledge"])
        self.assertEqual(applied, 1)
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertIn("python", store["entries"][0]["content"])
        self.assertNotIn("python3", store["entries"][0]["content"])

    def test_replaces_in_tags(self):
        self.seed_knowledge([
            {"id": "know-1", "category": "technical", "content": "test",
             "confidence": 0.8, "tags": ["old-term"], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 1}
        ])
        applied, _, _ = cascade.apply_fixes(self.kb, ["old-term"], "new-term", ["know-1"], ["knowledge"])
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertIn("new-term", store["entries"][0]["tags"])

    def test_skips_unapproved(self):
        self.seed_knowledge([
            {"id": "know-1", "category": "technical", "content": "python3 here",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 1},
            {"id": "know-2", "category": "technical", "content": "python3 there",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 1}
        ])
        applied, skipped, _ = cascade.apply_fixes(self.kb, ["python3"], "python", ["know-1"], ["knowledge"])
        self.assertEqual(applied, 1)
        self.assertEqual(skipped, 0)  # know-2 not in approved, not counted as skipped

    def test_rebuilds_index(self):
        self.seed_knowledge([
            {"id": "know-1", "category": "technical", "content": "python3",
             "confidence": 0.8, "tags": ["python3"], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 1}
        ])
        _, _, rebuilt = cascade.apply_fixes(self.kb, ["python3"], "python", ["know-1"], ["knowledge"])
        self.assertIn("knowledge", rebuilt)
        idx = self.read_json(self.kb / "Intelligence" / "knowledge-index.json")
        self.assertIn("python", idx["byTag"])


if __name__ == "__main__":
    unittest.main()
