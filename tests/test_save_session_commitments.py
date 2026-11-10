#!/usr/bin/env python3
"""save-session.py commitment and project-matching behavior:
commitment_updates, commitment auto-id, normalized project matching, unknown-key warning."""

import importlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
save_mod = importlib.import_module("save-session")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.kb = Path(self.tmp) / "Nate's-kb"
        (self.kb / "Memory").mkdir(parents=True)
        (self.kb / "Intelligence").mkdir(parents=True)
        for s in ("patterns", "knowledge", "reasoning"):
            (self.kb / "Intelligence" / f"{s}.json").write_text(json.dumps({"entries": []}))
        self.mem_path = self.kb / "Memory" / "memory.json"
        self.mem_path.write_text(json.dumps({
            "version": "1.0", "memories": {},
            "active_projects": [{"name": "Project Atlas", "status": "active", "next_action": "old"}],
            "commitments": [
                {"id": "cmt-2026-11-01-a", "what": "Ship the build log", "by": "2026-11-14", "status": "open"},
                {"what": "Legacy item with no id", "by": None, "status": "open"},
                {"id": "cmt-2026-11-02-dup1", "what": "Same text", "status": "open"},
                {"id": "cmt-2026-11-02-dup2", "what": "Same text", "status": "open"},
            ],
        }))
        save_mod.DRY_RUN = False

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def mem(self):
        return json.loads(self.mem_path.read_text())

    def run_ops(self, **ops):
        base = {"session_id": "session-2026-11-10-099"}
        base.update(ops)
        return save_mod.update_memory(self.kb, base)

    def commit(self, cid):
        return next(c for c in self.mem()["commitments"] if c.get("id") == cid)


class TestCommitmentUpdates(Base):
    def test_redate_by_id_and_note_records_change(self):
        self.run_ops(commitment_updates=[{"id": "cmt-2026-11-01-a", "set": {"by": "2026-11-21"}}])
        c = self.commit("cmt-2026-11-01-a")
        self.assertEqual(c["by"], "2026-11-21")
        self.assertIn("'2026-11-14' -> '2026-11-21'", c["note"])
        self.assertIn("session-2026-11-10-099", c["note"])

    def test_exact_text_match_works_for_idless(self):
        self.run_ops(commitment_updates=[{"match": "Legacy item with no id", "set": {"by": "2026-12-01"}}])
        c = next(c for c in self.mem()["commitments"] if c.get("what") == "Legacy item with no id")
        self.assertEqual(c["by"], "2026-12-01")

    def test_substring_never_matches(self):
        self.run_ops(commitment_updates=[{"match": "Ship the", "set": {"by": "2027-01-01"}}])
        self.assertEqual(self.commit("cmt-2026-11-01-a")["by"], "2026-11-14")

    def test_ambiguous_refused(self):
        self.run_ops(commitment_updates=[{"match": "Same text", "set": {"by": "2027-01-01"}}])
        self.assertNotIn("by", self.commit("cmt-2026-11-02-dup1"))
        self.assertNotIn("by", self.commit("cmt-2026-11-02-dup2"))

    def test_id_is_never_rewritten(self):
        self.run_ops(commitment_updates=[{"id": "cmt-2026-11-01-a", "set": {"id": "x", "to": "Alex"}}])
        c = self.commit("cmt-2026-11-01-a")
        self.assertEqual(c["to"], "Alex")


class TestCommitmentAutoId(Base):
    def test_new_commitment_without_id_gets_unique_cmt_id(self):
        self.run_ops(new_commitments=[{"what": "Ship the build log", "by": "2026-11-21",
                                       "status": "open", "created": "2026-11-01"},
                                      {"what": "Ship the build log", "status": "open", "created": "2026-11-01"}])
        ids = [c.get("id") for c in self.mem()["commitments"]]
        new = [i for i in ids if i and i.startswith("cmt-2026-11-01-ship-the-build-log")]
        self.assertEqual(len(new), 2)
        self.assertEqual(len(set(new)), 2)

    def test_existing_id_kept(self):
        self.run_ops(new_commitments=[{"id": "cmt-2026-11-10-mine", "what": "x", "status": "open"}])
        self.assertTrue(any(c.get("id") == "cmt-2026-11-10-mine" for c in self.mem()["commitments"]))


class TestProjectMatching(Base):
    def test_variant_name_updates_existing(self):
        self.run_ops(active_project_updates=[{"name": "project-atlas (S2)", "next_action": "new"}])
        ps = self.mem()["active_projects"]
        self.assertEqual(len(ps), 1)
        self.assertEqual(ps[0]["next_action"], "new")
        self.assertEqual(ps[0]["name"], "Project Atlas")  # canonical name kept

    def test_distinct_name_appends(self):
        self.run_ops(active_project_updates=[{"name": "Project Beacon", "status": "active"}])
        self.assertEqual(len(self.mem()["active_projects"]), 2)


class TestUnknownKeyWarning(unittest.TestCase):
    def test_unknown_key_warned_underscore_quiet(self):
        errs = save_mod.validate_ops({"session_id": "session-2026-11-10-099",
                                      "pattern_updates": [], "_comment": "x"})
        warns = [e for e in errs if "unrecognized ops key 'pattern_updates'" in e]
        self.assertEqual(len(warns), 1)
        self.assertFalse(any("_comment" in e for e in errs))
        self.assertTrue(all("warning" in e.lower() for e in warns))


class TestProjectMatchingPrefersLive(Base):
    def test_superseded_twin_never_absorbs_update(self):
        mem = self.mem()
        mem["active_projects"] = [{"name": "project-atlas", "status": "superseded", "next_action": "keep"},
                                  {"name": "Project Atlas", "status": "active", "next_action": "old"}]
        self.mem_path.write_text(json.dumps(mem))
        self.run_ops(active_project_updates=[{"name": "PROJECT ATLAS!", "next_action": "new"}])
        ps = {p["name"]: p for p in self.mem()["active_projects"]}
        self.assertEqual(ps["project-atlas"]["next_action"], "keep")
        self.assertEqual(ps["Project Atlas"]["next_action"], "new")

    def test_exact_name_wins(self):
        mem = self.mem()
        mem["active_projects"] = [{"name": "project-atlas", "status": "superseded", "next_action": "keep"},
                                  {"name": "Project Atlas", "status": "active", "next_action": "old"}]
        self.mem_path.write_text(json.dumps(mem))
        self.run_ops(active_project_updates=[{"name": "project-atlas", "next_action": "hit"}])
        ps = {p["name"]: p for p in self.mem()["active_projects"]}
        self.assertEqual(ps["project-atlas"]["next_action"], "hit")


if __name__ == "__main__":
    unittest.main()
