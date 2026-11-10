#!/usr/bin/env python3
"""Tests for the `unset` op in save-session.apply_entry_updates (added 2026-11-10).

unset removes legacy/drifted fields through the prescribed writer, records the removed
value in _history, and refuses identity, audit and required fields.
"""
import importlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
save_mod = importlib.import_module("save-session")


class UnsetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="unset-test-"))
        (self.tmp / "Intelligence").mkdir()
        self.entry = {"id": "fail_001", "category": "failure", "content": "c", "confidence": 0.9,
                      "tags": ["t"], "created": "2026-01-01", "lastAccessed": "2026-01-01",
                      "accessCount": 1, "trigger": "when X", "related": ["fail_002"]}
        (self.tmp / "Intelligence" / "patterns.json").write_text(
            json.dumps({"version": "1.0", "entries": [self.entry]}))
        save_mod.DRY_RUN = False

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _entry(self):
        return json.loads((self.tmp / "Intelligence" / "patterns.json").read_text())["entries"][0]

    def test_set_and_unset_together(self):
        n, ok = save_mod.apply_entry_updates(self.tmp, "patterns", [
            {"id": "fail_001", "set": {"context": "when X"}, "unset": ["trigger"]}])
        self.assertTrue(ok)
        self.assertEqual(n, 1)
        e = self._entry()
        self.assertEqual(e["context"], "when X")
        self.assertNotIn("trigger", e)
        self.assertEqual(e["_history"][-1]["was"], {"trigger": "when X"})

    def test_unset_alone_counts_as_change(self):
        n, _ = save_mod.apply_entry_updates(self.tmp, "patterns", [{"id": "fail_001", "unset": ["related"]}])
        self.assertEqual(n, 1)
        self.assertNotIn("related", self._entry())

    def test_protected_and_required_refused(self):
        n, _ = save_mod.apply_entry_updates(self.tmp, "patterns", [
            {"id": "fail_001", "unset": ["id", "created", "content", "tags", "_history"]}])
        self.assertEqual(n, 0)
        e = self._entry()
        for k in ("id", "created", "content", "tags"):
            self.assertIn(k, e)

    def test_missing_field_is_noop(self):
        n, _ = save_mod.apply_entry_updates(self.tmp, "patterns", [{"id": "fail_001", "unset": ["nope"]}])
        self.assertEqual(n, 0)

    def test_cannot_set_and_unset_same_field(self):
        n, _ = save_mod.apply_entry_updates(self.tmp, "patterns", [
            {"id": "fail_001", "set": {"context": "x"}, "unset": ["context"]}])
        self.assertEqual(n, 1)
        self.assertEqual(self._entry()["context"], "x")


if __name__ == "__main__":
    unittest.main()
