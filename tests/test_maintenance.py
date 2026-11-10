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


class TestSessionIndexIntegrity(TestBase):
    """Detection guards for the two silent update_session_index() defect classes.

    Two earlier fixes both closed with "STILL OPEN: maintenance.py has zero
    session-index coverage, so blank fingerprints and stats drift remain undetectable
    by the prescribed health check." That gap is why a blank fingerprint hid for 25
    days and a stats counter drifted by 10 across 6+ saves. These lock the detector.
    """

    def _write_index(self, sessions, stats=None):
        path = self.kb / "Memory" / "session-index.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        idx = {"sessions": sessions}
        if stats is not None:
            idx["stats"] = stats
        path.write_text(json.dumps(idx))
        return path

    def _good(self, sid="session-2026-01-01-001"):
        return {"id": sid, "date": "2026-01-01", "tags": ["x"],
                "summary": "did a thing", "outcome": "success"}

    def _blank(self, sid="session-2026-01-02-001"):
        return {"id": sid, "date": "2026-01-02", "tags": [], "summary": "",
                "outcome": "success"}

    def _log(self, sid="session-2026-01-01-001", archived=False):
        d = self.kb / "Memory" / ("archive" if archived else "")
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{sid}.md").write_text("# log\n")

    def test_clean_index_reports_nothing(self):
        self._write_index([self._good()], stats={"totalSessions": 1})
        self._log()
        fixed, review = maint.check_session_index(self.kb, fix=False)
        self.assertEqual(fixed, [])
        self.assertEqual(review, [])

    def test_detects_blank_fingerprint(self):
        self._write_index([self._good(), self._blank()], stats={"totalSessions": 2})
        _fixed, review = maint.check_session_index(self.kb, fix=False)
        blanks = [r for r in review if r["type"] == "blank_fingerprint"]
        self.assertEqual(len(blanks), 1)
        self.assertEqual(blanks[0]["id"], "session-2026-01-02-001")

    def test_blank_fingerprint_is_never_auto_fixed(self):
        """The content is unrecoverable from the index; only the log has it."""
        self._write_index([self._blank()], stats={"totalSessions": 1})
        fixed, review = maint.check_session_index(self.kb, fix=True)
        self.assertFalse([f for f in fixed if f["type"] == "blank_fingerprint"])
        self.assertTrue([r for r in review if r["type"] == "blank_fingerprint"])

    def test_detects_stats_drift(self):
        self._write_index([self._good(), self._blank()], stats={"totalSessions": 99})
        fixed, _review = maint.check_session_index(self.kb, fix=False)
        drift = [f for f in fixed if f["type"] == "stats_drift"]
        self.assertEqual(len(drift), 1)
        self.assertIn("99", drift[0]["detail"])
        self.assertIn("2", drift[0]["detail"])

    def test_stats_drift_is_repaired_in_fix_mode(self):
        path = self._write_index([self._good(), self._blank()], stats={"totalSessions": 99})
        maint.check_session_index(self.kb, fix=True)
        idx = json.loads(path.read_text())
        self.assertEqual(idx["stats"]["totalSessions"], 2)
        # And the repair must actually hold on a re-check.
        fixed, _ = maint.check_session_index(self.kb, fix=False)
        self.assertFalse([f for f in fixed if f["type"] == "stats_drift"])

    def test_missing_stats_block_counts_as_drift(self):
        """An absent stats.totalSessions is the same failure as a wrong one."""
        self._write_index([self._good()])
        fixed, _ = maint.check_session_index(self.kb, fix=False)
        self.assertTrue([f for f in fixed if f["type"] == "stats_drift"])

    def test_detects_populated_row_with_no_log(self):
        """Candidate 2026-10-20: a fingerprint can survive while the narrative is gone."""
        self._write_index([self._good()], stats={"totalSessions": 1})
        _fixed, review = maint.check_session_index(self.kb, fix=False)
        self.assertEqual([r["type"] for r in review], ["session_log_missing"])

    def test_archived_log_counts(self):
        self._write_index([self._good()], stats={"totalSessions": 1})
        self._log(archived=True)
        _fixed, review = maint.check_session_index(self.kb, fix=False)
        self.assertEqual(review, [])

    def test_reconstructed_row_not_reflagged(self):
        row = dict(self._good(), tags=["reconstructed"])
        self._write_index([row], stats={"totalSessions": 1})
        _fixed, review = maint.check_session_index(self.kb, fix=False)
        self.assertEqual(review, [])

    def test_blank_row_reported_once_not_twice(self):
        self._write_index([self._blank()], stats={"totalSessions": 1})
        _fixed, review = maint.check_session_index(self.kb, fix=False)
        self.assertEqual([r["type"] for r in review], ["blank_fingerprint"])

    def test_absent_index_is_not_an_error(self):
        fixed, review = maint.check_session_index(self.kb, fix=False)
        self.assertEqual((fixed, review), ([], []))

class TestCrossRefCheck(TestBase):
    def test_orphaned_cross_ref(self):
        self.write_json(self.kb / "Intelligence" / "cross-references.json", {
            "_meta": {"last_updated": "2026-01-01"},
            "references": {"know-999": {"referenced_by": ["reason-1"], "related_to": []}},
            "stats": {}
        })
        orphaned = maint.check_cross_references(self.kb)
        self.assertTrue(any("know-999" in o["detail"] for o in orphaned))

    def _xref_sources(self, *sources):
        self.write_json(self.kb / "Intelligence" / "cross-references.json", {
            "_meta": {"last_updated": "2026-01-01"},
            "references": {s: {"referenced_by": [], "related_to": []} for s in sources},
            "stats": {}
        })

    def test_bare_filename_is_provenance_not_orphan(self):
        """Candidate 2026-10-21: `build-tenancy.py` has no `/` but is still a file."""
        self._xref_sources("build-tenancy.py", "14-tenancy-buildout-sop.md", "notes.md#anchor")
        self.assertEqual(maint.check_cross_references(self.kb), [])

    def test_existing_provenance_shapes_still_skipped(self):
        self._xref_sources("docs/a.md", "session-2026-01-01-001", "BL-001", "statute 705/4")
        self.assertEqual(maint.check_cross_references(self.kb), [])

    def test_dotless_entry_id_still_checked(self):
        self._xref_sources("proc_999")
        orphaned = maint.check_cross_references(self.kb)
        self.assertTrue(any("proc_999" in o["detail"] for o in orphaned))


class TestSaveSessionGuards(TestBase):
    def test_bare_filename_derived_from_warns_not_errors(self):
        entry = {"id": "reason-1", "type": "inference", "derived_from": ["build-tenancy.py", "docs/x.md"]}
        errs = save_mod.validate_entry(entry, "reasoning", "reasoning[0]")
        bare = [e for e in errs if "bare filename" in e]
        self.assertEqual(len(bare), 1)
        self.assertIn("warning", bare[0].lower())

    def test_fingerprint_check_reads_disk(self):
        path = self.kb / "Memory" / "session-index.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"sessions": [
            {"id": "session-a", "tags": [], "summary": ""},
            {"id": "session-b", "tags": ["x"], "summary": ""},
        ]}))
        self.assertFalse(save_mod._session_fingerprint_populated(self.kb, "session-a"))
        self.assertTrue(save_mod._session_fingerprint_populated(self.kb, "session-b"))
        self.assertFalse(save_mod._session_fingerprint_populated(self.kb, "session-missing"))


if __name__ == "__main__":
    unittest.main()
