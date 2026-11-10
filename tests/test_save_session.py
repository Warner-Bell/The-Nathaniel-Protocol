#!/usr/bin/env python3
"""Tests for save-session.py — covers all 13 spec-required test categories."""

import json, os, sys, tempfile, shutil, unittest
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import importlib
save_mod = importlib.import_module("save-session")


class TestBase(unittest.TestCase):
    """Base with temp KB structure."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.kb = Path(self.tmpdir) / "Nate's-kb"
        (self.kb / "Intelligence").mkdir(parents=True)
        (self.kb / "Memory").mkdir(parents=True)

        # Minimal stores
        for store in ("patterns", "knowledge", "reasoning"):
            self.write_json(self.kb / "Intelligence" / f"{store}.json",
                           {"entries": [], "lastUpdated": "2026-01-01"})
            self.write_json(self.kb / "Intelligence" / f"{store}-index.json",
                           {"stats": {"totalEntries": 0, "activeEntries": 0, "nextId": 1 if store != "patterns" else {}},
                            "byTag": {}, "summaries": {}, "recentIds": []})

        self.write_json(self.kb / "Intelligence" / "cross-references.json",
                       {"_meta": {"last_updated": "2026-01-01"}, "references": {}, "stats": {}})
        self.write_json(self.kb / "Memory" / "session-index.json",
                       {"sessions": [], "recentIds": []})
        self.write_json(self.kb / "Memory" / "memory.json",
                       {"version": "1.0", "lastUpdated": "2026-01-01", "active_projects": []})

        save_mod.DRY_RUN = False

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def write_json(self, path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def read_json(self, path):
        with open(path) as f:
            return json.load(f)

    def make_ops(self, **overrides):
        ops = {"session_id": "session-2026-04-16-001", "schema_version": 1}
        ops.update(overrides)
        return ops


class TestValidation(TestBase):
    """1. Input validation"""

    def test_missing_session_id(self):
        errors = save_mod.validate_ops({})
        self.assertTrue(any("session_id" in e for e in errors))

    def test_invalid_session_id_format(self):
        errors = save_mod.validate_ops({"session_id": "bad-id"})
        self.assertTrue(any("Invalid session_id" in e for e in errors))

    def test_valid_minimal_ops(self):
        errors = save_mod.validate_ops(self.make_ops())
        hard = [e for e in errors if "warning" not in e.lower()]
        self.assertEqual(hard, [])

    def test_invalid_knowledge_category(self):
        ops = self.make_ops(new_knowledge=[{
            "id": "know-1", "category": "INVALID", "content": "test",
            "confidence": 0.8, "tags": ["t"]
        }])
        errors = save_mod.validate_ops(ops)
        self.assertTrue(any("invalid category" in e for e in errors))

    def test_invalid_confidence(self):
        ops = self.make_ops(new_knowledge=[{
            "id": "know-1", "category": "technical", "content": "test",
            "confidence": 1.5, "tags": ["t"]
        }])
        errors = save_mod.validate_ops(ops)
        self.assertTrue(any("confidence" in e for e in errors))

    def test_content_over_limit_is_warning(self):
        ops = self.make_ops(new_patterns=[{
            "id": "pref_1", "category": "preference", "content": "x" * 500,
            "confidence": 0.8, "tags": ["t"]
        }])
        errors = save_mod.validate_ops(ops)
        warnings = [e for e in errors if "warning" in e.lower()]
        self.assertTrue(len(warnings) > 0)

    def test_invalid_id_format(self):
        ops = self.make_ops(new_knowledge=[{
            "id": "bad-format", "category": "technical", "content": "test",
            "confidence": 0.8, "tags": ["t"]
        }])
        errors = save_mod.validate_ops(ops)
        self.assertTrue(any("invalid ID" in e for e in errors))

    def test_tags_must_be_list(self):
        ops = self.make_ops(new_knowledge=[{
            "id": "know-1", "category": "technical", "content": "test",
            "confidence": 0.8, "tags": "not-a-list"
        }])
        errors = save_mod.validate_ops(ops)
        self.assertTrue(any("tags must be a list" in e for e in errors))


class TestIdCollision(TestBase):
    """2. ID collision detection"""

    def test_collision_skips_entry(self):
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        store["entries"].append({"id": "know-1", "category": "technical", "content": "existing",
                                 "confidence": 0.8, "tags": [], "created": "2026-01-01",
                                 "lastAccessed": "2026-01-01", "accessCount": 1})
        self.write_json(self.kb / "Intelligence" / "knowledge.json", store)

        added, ok = save_mod.add_entries(self.kb, "knowledge",
            [{"id": "know-1", "category": "technical", "content": "dupe", "confidence": 0.8, "tags": []}])
        self.assertEqual(added, [])
        self.assertTrue(ok)


class TestAtomicWrites(TestBase):
    """3. Atomic write verification"""

    def test_save_json_atomic(self):
        path = self.kb / "Intelligence" / "test.json"
        save_mod.save_json(path, {"test": True})
        self.assertTrue(path.exists())
        self.assertFalse(Path(str(path) + '.tmp').exists())
        self.assertEqual(self.read_json(path), {"test": True})


class TestIndexRebuild(TestBase):
    """4. Index rebuild correctness"""

    def test_rebuild_knowledge_index(self):
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        store["entries"] = [
            {"id": "know-1", "category": "technical", "content": "first entry",
             "confidence": 0.9, "tags": ["aws", "lambda"], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 1},
            {"id": "know-2", "category": "process", "content": "second entry",
             "confidence": 0.6, "tags": ["workflow"], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ]
        self.write_json(self.kb / "Intelligence" / "knowledge.json", store)

        save_mod.rebuild_index(self.kb, "knowledge")
        idx = self.read_json(self.kb / "Intelligence" / "knowledge-index.json")

        self.assertEqual(idx["stats"]["totalEntries"], 2)
        self.assertEqual(idx["stats"]["nextId"], 3)
        self.assertIn("know-1", idx["summaries"])
        self.assertIn("know-2", idx["summaries"])
        self.assertIn("know-1", idx["byTag"].get("aws", []))
        self.assertIn("know-1", idx["byCategory"].get("technical", []))
        # recentIds must track the store's newest entries, newest first.
        # Regression guard: rebuild previously carried the old index's
        # recentIds forward untouched, so new entries never appeared.
        # Same created date -> append order breaks ties (know-2 appended last).
        self.assertEqual(idx["recentIds"], ["know-2", "know-1"])

    def test_rebuild_patterns_nextid(self):
        store = self.read_json(self.kb / "Intelligence" / "patterns.json")
        store["entries"] = [
            {"id": "pref_5", "category": "preference", "content": "test",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0},
            {"id": "fail_10", "category": "failure", "content": "test",
             "confidence": 0.7, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ]
        self.write_json(self.kb / "Intelligence" / "patterns.json", store)

        save_mod.rebuild_index(self.kb, "patterns")
        idx = self.read_json(self.kb / "Intelligence" / "patterns-index.json")

        self.assertEqual(idx["stats"]["nextId"]["pref"], 6)
        self.assertEqual(idx["stats"]["nextId"]["fail"], 11)


class TestAccessTracking(TestBase):
    """5. Access count updates"""

    def test_access_increments(self):
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        store["entries"].append({"id": "know-1", "category": "technical", "content": "test",
                                 "confidence": 0.8, "tags": [], "created": "2026-01-01",
                                 "lastAccessed": "2026-01-01", "accessCount": 3})
        self.write_json(self.kb / "Intelligence" / "knowledge.json", store)

        save_mod.update_access(self.kb, "knowledge", ["know-1"])
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        entry = store["entries"][0]
        self.assertEqual(entry["accessCount"], 4)
        self.assertEqual(entry["lastAccessed"], save_mod.get_today())


class TestMemoryUpdates(TestBase):
    """6. Memory mutation correctness"""

    def test_top_level_fields(self):
        ops = self.make_ops(memory_updates={"user_address": "Sir"})
        save_mod.update_memory(self.kb, ops)
        mem = self.read_json(self.kb / "Memory" / "memory.json")
        self.assertEqual(mem["user_address"], "Sir")

    def test_domain_expertise_merge(self):
        ops = self.make_ops(memory_updates={"domain_expertise": {"aws": "expert"}})
        save_mod.update_memory(self.kb, ops)
        mem = self.read_json(self.kb / "Memory" / "memory.json")
        self.assertEqual(mem["domain_expertise"]["aws"], "expert")

    def test_snapshot_counts(self):
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        store["entries"] = [{"id": "know-1", "category": "technical", "content": "t",
                             "confidence": 0.8, "tags": [], "created": "2026-01-01",
                             "lastAccessed": "2026-01-01", "accessCount": 0}]
        self.write_json(self.kb / "Intelligence" / "knowledge.json", store)

        ops = self.make_ops(snapshot={"session_id": "session-2026-04-16-001"})
        save_mod.update_memory(self.kb, ops)
        mem = self.read_json(self.kb / "Memory" / "memory.json")
        self.assertEqual(mem["last_session_snapshot"]["knowledge_count"], 1)


class TestSessionIndex(TestBase):
    """7. Session index updates"""

    def test_adds_session(self):
        ops = self.make_ops(session_tags=["test"], session_summary="Test session",
                           outcome="success", outcome_note="All good")
        save_mod.update_session_index(self.kb, ops)
        idx = self.read_json(self.kb / "Memory" / "session-index.json")
        self.assertEqual(len(idx["sessions"]), 1)
        self.assertEqual(idx["sessions"][0]["outcome_note"], "All good")

    def test_no_duplicate(self):
        ops = self.make_ops()
        save_mod.update_session_index(self.kb, ops)
        save_mod.update_session_index(self.kb, ops)
        idx = self.read_json(self.kb / "Memory" / "session-index.json")
        self.assertEqual(len(idx["sessions"]), 1)

    # --- Regression guards for the 2026-08-02 update_session_index fixes ---
    #
    # These behaviors were the CREATE-ONLY bug that blanked a session for 25
    # days and the stats drift of 10 across 6 saves. They had no coverage.

    def _seed_session(self, sid, tags, summary):
        idx = self.read_json(self.kb / "Memory" / "session-index.json")
        idx["sessions"].insert(0, {
            "id": sid, "date": "2026-04-16", "tags": tags,
            "summary": summary, "outcome": "success", "outcome_note": ""
        })
        self.write_json(self.kb / "Memory" / "session-index.json", idx)

    def test_fills_blank_entry_when_content_supplied(self):
        # A blank fingerprint (empty tags + summary) already in the index must
        # be FILLED when a later run supplies content — not left permanently blank.
        sid = "session-2026-04-16-001"
        self._seed_session(sid, [], "")
        ops = self.make_ops(session_tags=["recovered"],
                            session_summary="content arrived on a later run")
        save_mod.update_session_index(self.kb, ops)
        entry = self.read_json(self.kb / "Memory" / "session-index.json")["sessions"][0]
        self.assertEqual(entry["tags"], ["recovered"])
        self.assertEqual(entry["summary"], "content arrived on a later run")

    def test_refuses_overwrite_of_populated_entry(self):
        # A populated entry must NOT be silently overwritten by a colliding
        # session_id — the original content is preserved, the new content dropped.
        sid = "session-2026-04-16-001"
        self._seed_session(sid, ["original"], "original summary")
        ops = self.make_ops(session_tags=["collision"],
                            session_summary="should be discarded")
        save_mod.update_session_index(self.kb, ops)
        entry = self.read_json(self.kb / "Memory" / "session-index.json")["sessions"][0]
        self.assertEqual(entry["summary"], "original summary")
        self.assertEqual(entry["tags"], ["original"])

    def test_stats_totalsessions_maintained_on_insert(self):
        # stats.totalSessions must track the array on the INSERT path (not only
        # on prune), or it drifts silently as sessions accrue.
        ops = self.make_ops(session_tags=["t"], session_summary="s")
        save_mod.update_session_index(self.kb, ops)
        idx = self.read_json(self.kb / "Memory" / "session-index.json")
        self.assertEqual(idx["stats"]["totalSessions"], len(idx["sessions"]))
        self.assertEqual(idx["stats"]["totalSessions"], 1)


class TestSessionIdClaim(TestBase):
    """The session-id collision hole, found live 2026-08-05.

    The entry-id collision guard covers ENTRY ids only. Nothing guarded the SESSION id, so two
    instances auto-numbering from disk both computed the same next-free number. Real
    consequence: id 017 was claimed by two sessions, putting 7 project entries
    under a log about unrelated fixes, plus a blank fingerprint.
    """

    def _mem(self, sessions=None):
        mem = self.kb / "Memory"
        mem.mkdir(parents=True, exist_ok=True)
        (mem / "session-index.json").write_text(
            json.dumps({"sessions": sessions or [], "recentIds": []}))
        return mem

    def test_first_claim_is_001(self):
        self._mem()
        self.assertEqual(save_mod.claim_session_id(self.kb, date="2026-08-05"),
                         "session-2026-08-05-001")

    def test_skips_ids_with_a_log_on_disk(self):
        mem = self._mem()
        (mem / "session-2026-08-05-001.md").write_text("x")
        (mem / "session-2026-08-05-002.md").write_text("x")
        self.assertEqual(save_mod.claim_session_id(self.kb, date="2026-08-05"),
                         "session-2026-08-05-003")

    def test_skips_ids_registered_in_index_with_NO_log(self):
        """The exact 2026-08-05 case: an entries-only save registers an id and never
        writes a log. Scanning only the log directory hands that id straight out."""
        self._mem(sessions=[{"id": "session-2026-08-05-001", "tags": [], "summary": ""}])
        got = save_mod.claim_session_id(self.kb, date="2026-08-05")
        self.assertEqual(got, "session-2026-08-05-002",
                         "index-registered id was reused — this is the live collision")

    def test_claim_creates_the_reservation_file(self):
        self._mem()
        sid = save_mod.claim_session_id(self.kb, date="2026-08-05")
        self.assertTrue((self.kb / "Memory" / f"{sid}.md").exists(),
                        "reservation must be the file itself, or the race reopens")

    def test_sequential_claims_never_repeat(self):
        self._mem()
        ids = [save_mod.claim_session_id(self.kb, date="2026-08-05") for _ in range(5)]
        self.assertEqual(len(set(ids)), 5, f"repeat issued: {ids}")
        self.assertEqual(ids[-1], "session-2026-08-05-005")

    def test_claims_max_plus_one_NOT_lowest_free(self):
        """The bug my own tests could not catch. Every other test here uses contiguous
        ids, so none can tell "lowest free" apart from "next after max". With 013-018
        in use and 001-012 never used, the first implementation handed out 001, which
        misorders the index and misdates the session. Found by RUNNING the flag against
        the real KB, not by the suite."""
        mem = self._mem()
        for n in (13, 14, 15, 16, 17, 18):
            (mem / f"session-2026-08-05-{n:03d}.md").write_text("x")
        got = save_mod.claim_session_id(self.kb, date="2026-08-05")
        self.assertEqual(got, "session-2026-08-05-019",
                         "claimed a low free id instead of max+1")

    def test_gap_from_index_only_ids_also_respected(self):
        """Same gap rule when the high ids exist only in the index (entries-only save)."""
        self._mem(sessions=[{"id": "session-2026-08-05-017", "tags": [], "summary": ""}])
        self.assertEqual(save_mod.claim_session_id(self.kb, date="2026-08-05"),
                         "session-2026-08-05-018")

    def test_concurrent_claims_never_collide(self):
        """The falsifying test. Verified live: the old scan-then-write approach gave
        all 8 workers session-...-001 and lost 7 logs; this must give 8 distinct."""
        from concurrent.futures import ThreadPoolExecutor
        self._mem()
        with ThreadPoolExecutor(max_workers=8) as ex:
            ids = list(ex.map(lambda _: save_mod.claim_session_id(self.kb, date="2026-08-05"),
                              range(8)))
        self.assertEqual(len(set(ids)), 8, f"collision: {sorted(ids)}")
        logs = list((self.kb / "Memory").glob("session-2026-08-05-*.md"))
        self.assertEqual(len(logs), 8, "a reservation was lost")


class TestBlankFingerprintWarning(TestBase):
    """Every blank fingerprint in the index was created silently by the CREATE path
    accepting empty tags AND summary. Four were born on 2026-08-05 alone."""

    def _mem(self):
        mem = self.kb / "Memory"
        mem.mkdir(parents=True, exist_ok=True)
        (mem / "session-index.json").write_text(json.dumps({"sessions": [], "recentIds": []}))
        return mem

    def _capture(self, ops):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            save_mod.update_session_index(self.kb, ops)
        return buf.getvalue()

    def test_blank_creation_warns_loudly(self):
        self._mem()
        out = self._capture({"session_id": "session-2026-08-05-001"})
        self.assertIn("BLANK FINGERPRINT", out,
                      "a blank fingerprint was created with no warning")

    def test_populated_creation_does_not_warn(self):
        """Negative control: the warning must not fire on healthy saves."""
        self._mem()
        out = self._capture({"session_id": "session-2026-08-05-001",
                             "session_index_entry": {"tags": ["t"], "summary": "real work"}})
        self.assertNotIn("BLANK FINGERPRINT", out)

    def test_blank_entry_is_still_written(self):
        """Warning, not refusal: the blank-fill fix means a later save can fill it, and
        refusing would break an entries-only save's registration."""
        self._mem()
        self._capture({"session_id": "session-2026-08-05-001"})
        idx = json.loads((self.kb / "Memory" / "session-index.json").read_text())
        self.assertEqual([s["id"] for s in idx["sessions"]], ["session-2026-08-05-001"])


class TestVersionBumpGuard(TestBase):
    """version_bump was assigned literally, so passing a
    boolean wrote `"version": true` into memory.json and corrupted the field."""

    def _mem(self, version="4.01"):
        path = self.kb / "Memory" / "memory.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"version": version, "memories": {}}))
        return path

    def test_string_version_used_verbatim(self):
        path = self._mem()
        save_mod.update_memory(self.kb, self.make_ops(memory_updates={"version_bump": "9.99"}))
        self.assertEqual(json.loads(path.read_text())["version"], "9.99")

    def test_boolean_true_increments_instead_of_corrupting(self):
        path = self._mem("4.01")
        save_mod.update_memory(self.kb, self.make_ops(memory_updates={"version_bump": True}))
        v = json.loads(path.read_text())["version"]
        self.assertNotIsInstance(v, bool, "boolean leaked into memory.json version")
        self.assertEqual(v, "4.02", "zero-padded width must be preserved")

    def test_bump_helper_preserves_pad_width(self):
        self.assertEqual(save_mod._bump_version("4.01"), "4.02")
        self.assertEqual(save_mod._bump_version("4.09"), "4.10")
        self.assertEqual(save_mod._bump_version("1.2.9"), "1.2.10")

    def test_bump_helper_tolerates_junk(self):
        self.assertEqual(save_mod._bump_version("no-digits"), "no-digits")
        self.assertTrue(save_mod._bump_version(None))


class TestProactiveOfferHandler(TestBase):
    """No handler existed for offer_history / session_offers_made, so save
    checklist item 4 could not be executed through the script at all."""

    def _mem(self):
        path = self.kb / "Memory" / "memory.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"version": "1.00", "memories": {}}))
        return path

    def test_offer_history_lands_under_proactive_behavior(self):
        path = self._mem()
        offers = [{"type": "research", "accepted": True}]
        save_mod.update_memory(self.kb, self.make_ops(memory_updates={"offer_history": offers}))
        mem = json.loads(path.read_text())
        self.assertIn("proactive_behavior", mem)
        self.assertEqual(mem["proactive_behavior"]["offer_history"], offers)
        self.assertNotIn("offer_history", mem, "must not leak to top level")

    def test_offer_history_appends_rather_than_replaces(self):
        path = self._mem()
        save_mod.update_memory(self.kb, self.make_ops(memory_updates={"offer_history": [{"a": 1}]}))
        save_mod.update_memory(self.kb, self.make_ops(memory_updates={"offer_history": [{"b": 2}]}))
        hist = json.loads(path.read_text())["proactive_behavior"]["offer_history"]
        self.assertEqual(len(hist), 2, "second save overwrote the first")

    def test_session_offers_made_recorded(self):
        path = self._mem()
        save_mod.update_memory(self.kb, self.make_ops(memory_updates={"session_offers_made": 3}))
        mem = json.loads(path.read_text())
        self.assertEqual(mem["proactive_behavior"]["session_offers_made"], 3)
        self.assertNotIn("session_offers_made", mem, "must not leak to top level")


class TestWriteVerification(TestBase):
    """add_entries reported success from save_json's return value and never
    re-read the file, so an entry lost to a non-locking concurrent writer was reported
    as added. That is the 'silently no-ops in some runs' behavior."""

    def _store(self, entries=None):
        path = self.kb / "Intelligence" / "knowledge.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"entries": entries or [], "lastUpdated": "2026-01-01"}))
        return path

    def _entry(self, eid="know-1"):
        return {"id": eid, "category": "technical", "content": "c",
                "confidence": 0.8, "tags": ["t"], "source": "session-2026-01-01-001"}

    def test_positive_control_normal_write_succeeds(self):
        self._store()
        added, ok = save_mod.add_entries(self.kb, "knowledge", [self._entry()])
        self.assertTrue(ok)
        self.assertEqual(added, ["know-1"])

    def test_negative_control_clobbered_write_is_reported_as_failure(self):
        """THE BUG. Simulate a non-locking writer clobbering the store during save.

        Patch save_json so it "succeeds" but leaves the file without our entry, exactly
        what a concurrent overwrite produces. Before the fix this returned success.
        """
        path = self._store()
        real_save = save_mod.save_json

        def clobbering_save(p, data):
            # Pretend another process wrote an empty store immediately after us.
            real_save(p, {"entries": [], "lastUpdated": "2026-01-01"})
            return True

        save_mod.save_json = clobbering_save
        try:
            added, ok = save_mod.add_entries(self.kb, "knowledge", [self._entry()])
        finally:
            save_mod.save_json = real_save

        self.assertFalse(ok, "clobbered write must be reported as FAILURE, not success")
        self.assertEqual(added, [], "must not report IDs that are not on disk")
        self.assertEqual(json.loads(path.read_text())["entries"], [])


class TestNestedMemoryGuard(TestBase):
    """Tier-1 fix 2026-09-21. The blind `else: mem[key] = value` catch-all in
    update_memory made two documented failure classes inevitable:

    (a) DATA LOSS. Passing a nested object replaced it wholesale. Live incident
        2026-09-21: supplying the whole `proactive_behavior` dict with 6 new offers
        destroyed 35 historical offers (back to 2026-04-07) and silently changed
        frequency_preference from 'normal' to an invented 'high'. Nothing errored;
        the script printed 'Memory updated'.

    (b) KEY LEAKAGE. Every unrecognised ops key was written straight into
        memory.json, accumulating ~20 junk top-level keys (commitments_add, set,
        todo_list, taxonomy_update...).

    Note the script ALREADY had a correct append handler for offer_history; the
    catch-all is what bypassed it. These tests pin the guard, not the handler."""

    def _mem(self):
        return self.read_json(self.kb / "Memory" / "memory.json")

    def test_nested_dict_is_deep_merged_not_replaced(self):
        self.write_json(self.kb / "Memory" / "memory.json", {
            "version": "1.0",
            "proactive_behavior": {
                "enabled": True,
                "frequency_preference": "normal",
                "offer_history": [{"type": "old", "date": "2026-04-07"}],
            },
        })
        save_mod.update_memory(self.kb, {
            "session_id": "session-2026-09-21-001",
            "memory_updates": {"proactive_behavior": {"session_offers_made": 6}},
        })
        pb = self._mem()["proactive_behavior"]
        self.assertEqual(pb["session_offers_made"], 6, "new key must land")
        self.assertEqual(len(pb["offer_history"]), 1, "existing nested list must survive")
        self.assertEqual(pb["frequency_preference"], "normal",
                         "a field not mentioned in ops must never change")
        self.assertTrue(pb["enabled"])

    def test_shrinking_a_nested_list_is_refused(self):
        """The exact 2026-09-21 incident: 35 offers replaced by 6."""
        old = [{"type": "o%d" % i, "date": "2026-04-07"} for i in range(35)]
        self.write_json(self.kb / "Memory" / "memory.json", {
            "version": "1.0",
            "proactive_behavior": {"offer_history": old, "frequency_preference": "normal"},
        })
        new6 = [{"type": "n%d" % i, "date": "2026-09-21"} for i in range(6)]
        save_mod.update_memory(self.kb, {
            "session_id": "session-2026-09-21-001",
            "memory_updates": {"proactive_behavior": {"offer_history": new6}},
        })
        pb = self._mem()["proactive_behavior"]
        self.assertGreaterEqual(len(pb["offer_history"]), 35,
                                "a shrinking nested list must be refused, not written")

    def test_unknown_top_level_key_is_rejected_not_written(self):
        save_mod.update_memory(self.kb, {
            "session_id": "session-2026-09-21-001",
            "memory_updates": {"commitments_add": [{"x": 1}], "set": "junk",
                               "taxonomy_update": {"a": 1}},
        })
        mem = self._mem()
        for leaked in ("commitments_add", "set", "taxonomy_update"):
            self.assertNotIn(leaked, mem, f"unknown ops key {leaked} must not be written")

    def test_known_scalar_keys_still_work(self):
        """The guard must not break legitimate top-level writes."""
        save_mod.update_memory(self.kb, {
            "session_id": "session-2026-09-21-001",
            "memory_updates": {"last_cross_session_synthesis": "session-2026-09-21-001"},
        })
        self.assertEqual(self._mem()["last_cross_session_synthesis"],
                         "session-2026-09-21-001")

    def test_offer_history_append_handler_unaffected(self):
        """Regression guard: the pre-existing correct path must keep appending."""
        self.write_json(self.kb / "Memory" / "memory.json", {
            "version": "1.0",
            "proactive_behavior": {"offer_history": [{"type": "old", "date": "2026-04-07"}]},
        })
        save_mod.update_memory(self.kb, {
            "session_id": "session-2026-09-21-001",
            "memory_updates": {"offer_history": [{"type": "new", "date": "2026-09-21"}]},
        })
        oh = self._mem()["proactive_behavior"]["offer_history"]
        self.assertEqual(len(oh), 2, "offer_history ops key must still APPEND")


class TestDryRunNoFalseVerification(TestBase):
    """--dry-run skips the actual write (save_json returns True without writing),
    so the post-write verification re-reads an unchanged file and reports
    every new entry as missing, citing 'concurrent non-locking writer clobbered the
    store' and 'do NOT hand-write these entries'. Captured SIX times without ever
    being fixed. The alarm risks a future
    session aborting a good save or hand-writing entries that were never lost."""

    def test_dry_run_does_not_report_write_verification_failure(self):
        import io, contextlib
        save_mod.DRY_RUN = True
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                added, ok = save_mod.add_entries(self.kb, "knowledge", [{
                    "id": "know-1", "category": "technical", "content": "x" * 40,
                    "confidence": 0.8, "tags": ["a", "b"], "source": "t",
                }])
            out = buf.getvalue()
            self.assertNotIn("WRITE VERIFICATION FAILED", out,
                             "dry-run must not emit the post-write false alarm")
            self.assertTrue(ok, "dry-run must report success, not failure")
        finally:
            save_mod.DRY_RUN = False

    def test_real_run_still_verifies(self):
        """The guard must not disable verification on a real apply."""
        import io, contextlib
        save_mod.DRY_RUN = False
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            added, ok = save_mod.add_entries(self.kb, "knowledge", [{
                "id": "know-2", "category": "technical", "content": "y" * 40,
                "confidence": 0.8, "tags": ["a", "b"], "source": "t",
            }])
        self.assertTrue(ok)
        self.assertIn("know-2", added)
        landed = self.read_json(self.kb / "Intelligence" / "knowledge.json")["entries"]
        self.assertEqual([e["id"] for e in landed], ["know-2"])


class TestSchemaParity(TestBase):
    """save-session.py (writer) and validate-schemas.py (checker) maintain
    INDEPENDENT schema definitions and drift apart silently. Observed drift was the
    knowledge category enum at 11 vs 13. All four shared enums currently agree, so this
    locks them: change one side and this test names the delta instead of letting a save
    write entries the validator will later reject.
    """

    SHARED_ENUMS = ("KNOWLEDGE_CATEGORIES", "PATTERN_CATEGORIES",
                    "REASONING_TYPES", "REASONING_PROVENANCES")

    def _validator(self):
        import importlib
        try:
            return importlib.import_module("validate-schemas")
        except ModuleNotFoundError:
            self.skipTest("validate-schemas.py not importable")

    def test_shared_enums_agree(self):
        validator = self._validator()
        drift = []
        compared = 0
        for name in self.SHARED_ENUMS:
            w = getattr(save_mod, name, None)
            c = getattr(validator, name, None)
            if w is None or c is None:
                drift.append(f"{name}: missing on {'writer' if w is None else 'checker'}")
                continue
            compared += 1
            if set(w) != set(c):
                drift.append(f"{name}: writer-only={sorted(set(w) - set(c))} "
                             f"checker-only={sorted(set(c) - set(w))}")
        # Guard the instrument: a parity test that compared nothing would pass silently.
        self.assertEqual(compared, len(self.SHARED_ENUMS),
                         f"expected to compare {len(self.SHARED_ENUMS)} enums, compared {compared}")
        self.assertEqual(drift, [], "schema drift — update BOTH scripts: "
                                    + "; ".join(drift))

    def test_parity_check_can_actually_fail(self):
        """Negative control. A parity assertion that cannot fail is worthless."""
        validator = self._validator()
        name = "KNOWLEDGE_CATEGORIES"
        original = list(getattr(validator, name))
        setattr(validator, name, original + ["__injected_drift__"])
        try:
            with self.assertRaises(AssertionError):
                self.test_shared_enums_agree()
        finally:
            setattr(validator, name, original)


class TestCrossReferences(TestBase):
    """8. Cross-reference updates"""

    def test_adds_refs(self):
        entries = [{"id": "reason-1", "derived_from": ["know-1", "pref_5"]}]
        save_mod.update_cross_references(self.kb, entries)
        xref = self.read_json(self.kb / "Intelligence" / "cross-references.json")
        self.assertIn("reason-1", xref["references"]["know-1"]["referenced_by"])
        self.assertIn("reason-1", xref["references"]["pref_5"]["referenced_by"])

    def test_skips_session_ids(self):
        entries = [{"id": "reason-1", "derived_from": ["session-2026-04-16-001"]}]
        save_mod.update_cross_references(self.kb, entries)
        xref = self.read_json(self.kb / "Intelligence" / "cross-references.json")
        self.assertNotIn("session-2026-04-16-001", xref["references"])


class TestDryRun(TestBase):
    """9. Dry-run mode"""

    def test_no_writes(self):
        save_mod.DRY_RUN = True
        store_before = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        save_mod.add_entries(self.kb, "knowledge",
            [{"id": "know-1", "category": "technical", "content": "test",
              "confidence": 0.8, "tags": ["t"]}])
        store_after = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertEqual(store_before, store_after)


class TestExitCodes(TestBase):
    """10. Exit code differentiation"""

    def test_validate_ops_catches_bad_input(self):
        errors = save_mod.validate_ops({"session_id": "bad"})
        self.assertTrue(len(errors) > 0)


class TestFileLock(TestBase):
    """11. File locking"""

    def test_lock_creates_and_cleans(self):
        lock_path = self.kb / "Intelligence" / "test"
        with save_mod.FileLock(lock_path):
            self.assertTrue(os.path.exists(str(lock_path) + '.lock'))
        # Lock file cleaned up
        self.assertFalse(os.path.exists(str(lock_path) + '.lock'))


class TestOpsFormats(TestBase):
    """12. Both ops file formats (flat and nested)"""

    def test_flat_format(self):
        entries = save_mod.get_entries({"new_knowledge": [{"id": "know-1"}]}, "knowledge")
        self.assertEqual(len(entries), 1)

    def test_nested_format(self):
        entries = save_mod.get_entries(
            {"new_entries": {"knowledge": [{"id": "know-1"}]}}, "knowledge")
        self.assertEqual(len(entries), 1)


class TestDefaults(TestBase):
    """13. Default field application"""

    def test_defaults_applied(self):
        added, _ = save_mod.add_entries(self.kb, "knowledge",
            [{"id": "know-1", "category": "technical", "content": "test",
              "confidence": 0.8, "tags": ["t"]}])
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        entry = store["entries"][0]
        self.assertEqual(entry["accessCount"], 1)
        self.assertEqual(entry["created"], save_mod.get_today())
        self.assertEqual(entry["lastAccessed"], save_mod.get_today())


class TestPatternSourceDefault(TestBase):
    """2026-11-09: normalize_ops defaults a missing pattern source to the session id."""

    def _ops(self, **extra):
        p = {"id": "pref_9001", "category": "preference", "content": "x",
             "confidence": 0.8, "tags": ["t"]}
        p.update(extra)
        return {"session_id": "session-2026-11-09-002", "new_patterns": [p]}

    def test_should_default_pattern_source_to_session_id_when_missing(self):
        ops = self._ops()
        save_mod.normalize_ops(ops, self.kb)
        self.assertEqual(ops["new_patterns"][0]["source"], "session-2026-11-09-002")

    def test_should_keep_explicit_pattern_source_when_present(self):
        ops = self._ops(source="session-2026-11-01-004")
        save_mod.normalize_ops(ops, self.kb)
        self.assertEqual(ops["new_patterns"][0]["source"], "session-2026-11-01-004")

    def test_should_not_write_empty_source_when_session_id_missing(self):
        ops = self._ops()
        ops["session_id"] = ""
        save_mod.normalize_ops(ops, self.kb)
        self.assertNotIn("source", ops["new_patterns"][0])


if __name__ == "__main__":
    unittest.main()
