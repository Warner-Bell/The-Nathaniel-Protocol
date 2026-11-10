#!/usr/bin/env python3
"""reconcile-memory.py: a cluster with at most one live record is already resolved."""
import importlib.util
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
_spec = importlib.util.spec_from_file_location("reconcile_memory", REPO / "scripts" / "reconcile-memory.py")
rm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rm)


def mem(projects):
    return {"active_projects": projects, "commitments": []}


class TestClusters(unittest.TestCase):
    def test_superseded_twin_is_resolved_not_reported(self):
        _, exact, _, _, resolved = rm.analyze(mem([
            {"name": "project-atlas", "status": "superseded"},
            {"name": "Project Atlas", "status": "active"}]))
        self.assertEqual(exact, {})
        self.assertEqual(resolved, 1)

    def test_two_live_records_still_reported(self):
        _, exact, _, _, resolved = rm.analyze(mem([
            {"name": "project-atlas", "status": "active"},
            {"name": "Project Atlas", "status": "active"},
            {"name": "PROJECT ATLAS", "status": "archived"}]))
        self.assertEqual(list(exact), ["project atlas"])
        self.assertEqual(resolved, 0)

    def test_missing_status_counts_as_live(self):
        _, exact, _, _, _ = rm.analyze(mem([{"name": "A b"}, {"name": "a-b"}]))
        self.assertEqual(list(exact), ["a b"])


if __name__ == "__main__":
    unittest.main()
