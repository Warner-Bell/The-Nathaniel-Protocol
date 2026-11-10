#!/usr/bin/env python3
"""scripts/commitments.py against a temp memory.json (never the live store)."""
import importlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
cm = importlib.import_module("commitments")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "Intelligence").mkdir()
        (self.tmp / "Memory").mkdir()
        self.mem = self.tmp / "Memory" / "memory.json"
        self.mem.write_text(json.dumps({"commitments": [
            {"id": "cmt-2026-11-01-a", "what": "Ship it", "by": "2026-11-14", "status": "open"},
            {"id": "cmt-2026-11-01-b", "what": "Done thing", "status": "done"},
            {"what": "No status, no id"},
        ]}))
        self._saved = (cm.MEM, cm.LOCK, cm.BACKUP)
        cm.MEM, cm.LOCK, cm.BACKUP = self.mem, self.tmp / "Intelligence" / "stores", self.tmp / "Memory" / "bak"

    def tearDown(self):
        cm.MEM, cm.LOCK, cm.BACKUP = self._saved
        shutil.rmtree(self.tmp)

    def get(self, cid):
        return next(c for c in json.loads(self.mem.read_text())["commitments"] if c.get("id") == cid)


class TestIsOpen(Base):
    def test_definition(self):
        cs = json.loads(self.mem.read_text())["commitments"]
        self.assertEqual([cm.is_open(c) for c in cs], [True, False, True])
        self.assertFalse(cm.is_open({"status": "parked"}))


class TestWrites(Base):
    def test_close_stamps_and_notes(self):
        cm.cmd_close(SimpleNamespace(id="cmt-2026-11-01-a", status="resolved", note="shipped"))
        c = self.get("cmt-2026-11-01-a")
        self.assertEqual(c["status"], "resolved")
        self.assertEqual(c["resolved_by"], "commitments.py")
        self.assertIn("open -> resolved: shipped", c["note"])
        self.assertTrue(cm.BACKUP.exists())

    def test_close_twice_refused(self):
        with self.assertRaises(SystemExit):
            cm.cmd_close(SimpleNamespace(id="cmt-2026-11-01-b", status="done", note="x"))

    def test_redate_and_clear(self):
        cm.cmd_redate(SimpleNamespace(id="cmt-2026-11-01-a", date="2026-11-21", note="moved"))
        self.assertEqual(self.get("cmt-2026-11-01-a")["by"], "2026-11-21")
        cm.cmd_redate(SimpleNamespace(id="cmt-2026-11-01-a", date="none", note=None))
        self.assertIsNone(self.get("cmt-2026-11-01-a")["by"])

    def test_reopen(self):
        cm.cmd_reopen(SimpleNamespace(id="cmt-2026-11-01-b", note="not actually done"))
        c = self.get("cmt-2026-11-01-b")
        self.assertEqual(c["status"], "open")
        self.assertNotIn("resolved_date", c)

    def test_add_assigns_unique_id(self):
        for _ in range(2):
            cm.cmd_add(SimpleNamespace(what="Call the plumber", by=None, to="Alex", context=None))
        ids = [c.get("id") for c in json.loads(self.mem.read_text())["commitments"]]
        new = [i for i in ids if i and "call-the-plumber" in i]
        self.assertEqual(len(set(new)), 2)

    def test_unknown_id_exits(self):
        with self.assertRaises(SystemExit):
            cm.cmd_close(SimpleNamespace(id="nope", status="resolved", note="x"))


if __name__ == "__main__":
    unittest.main()
