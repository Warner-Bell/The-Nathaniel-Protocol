#!/usr/bin/env python3
"""Columbo, OOB, and know-001 tests. Test behavior, not inventory.

Columbo: trace real scenarios end-to-end, verify the BEHAVIOR works
OOB: what happens at boundaries, with bad data, under stress
know-001: leave nothing to chance — every implicit assumption is tested
"""

import json, sys, tempfile, shutil, unittest, os, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from importlib import import_module
save_mod = import_module("save-session")
cascade = import_module("cascade-correction")
removal = import_module("removal-cascade")
maint = import_module("maintenance")


class TestBase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.kb = Path(self.tmpdir) / "Nate's-kb"
        (self.kb / "Intelligence").mkdir(parents=True)
        (self.kb / "Memory").mkdir(parents=True)
        (self.kb / "vectorstore").mkdir(parents=True)

        for store in ("patterns", "knowledge", "reasoning"):
            self.write_json(self.kb / "Intelligence" / f"{store}.json", {"entries": [], "lastUpdated": "2026-01-01"})
            self.write_json(self.kb / "Intelligence" / f"{store}-index.json",
                           {"stats": {"totalEntries": 0, "nextId": 1 if store != "patterns" else {}},
                            "byTag": {}, "summaries": {}, "recentIds": []})

        self.write_json(self.kb / "Intelligence" / "cross-references.json", {})
        self.write_json(self.kb / "Memory" / "session-index.json", {"sessions": [], "recentIds": []})
        self.write_json(self.kb / "Memory" / "memory.json",
                       {"version": "1.0", "lastUpdated": "2026-01-01", "active_projects": [],
                        "commitments": [], "domain_expertise": {}})
        save_mod.DRY_RUN = False

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def write_json(self, path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def read_json(self, path):
        with open(path) as f:
            return json.load(f)

    def seed(self, store, entries):
        self.write_json(self.kb / "Intelligence" / f"{store}.json",
                       {"entries": entries, "lastUpdated": "2026-01-01"})


# ─── COLUMBO: Real Scenario Traces ───────────────────────────────────────

class TestColumbo(TestBase):
    """Trace real user scenarios end-to-end. Does the BEHAVIOR work?"""

    def test_full_save_cycle(self):
        """Scenario: User says 'save'. Nate writes ops, script executes full cycle."""
        ops = {
            "session_id": "session-2026-04-16-001", "schema_version": 1,
            "session_tags": ["test"], "session_summary": "Test session",
            "outcome": "success", "outcome_note": "All good",
            "new_knowledge": [
                {"id": "know-1", "category": "technical", "content": "Lambda cold starts average 100-200ms",
                 "confidence": 0.9, "tags": ["aws", "lambda", "performance"]}
            ],
            "new_reasoning": [
                {"id": "reason-1", "type": "deduction", "content": "Cold starts matter for sync APIs",
                 "intent": "Optimize API latency", "reuse_signal": "Lambda latency optimization",
                 "confidence": 0.85, "tags": ["lambda", "api"], "provenance": "stated",
                 "derived_from": ["know-1"]}
            ],
            "access_updates": {"knowledge": [], "reasoning": [], "patterns": []},
            "memory_updates": {"user_address": "Sir"},
            "snapshot": {"session_id": "session-2026-04-16-001"},
            "vectorstore_sync": False
        }

        # Execute full save
        save_mod.update_session_index(self.kb, ops)
        save_mod.add_entries(self.kb, "knowledge", ops["new_knowledge"])
        save_mod.add_entries(self.kb, "reasoning", ops["new_reasoning"])
        save_mod.rebuild_index(self.kb, "knowledge")
        save_mod.rebuild_index(self.kb, "reasoning")
        save_mod.update_cross_references(self.kb, ops["new_reasoning"])
        save_mod.update_memory(self.kb, ops)

        # Verify: session in index
        sidx = self.read_json(self.kb / "Memory" / "session-index.json")
        self.assertEqual(sidx["sessions"][0]["id"], "session-2026-04-16-001")

        # Verify: entries in stores
        k = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertEqual(len(k["entries"]), 1)
        r = self.read_json(self.kb / "Intelligence" / "reasoning.json")
        self.assertEqual(len(r["entries"]), 1)

        # Verify: indexes accurate
        ki = self.read_json(self.kb / "Intelligence" / "knowledge-index.json")
        self.assertEqual(ki["stats"]["totalEntries"], 1)
        self.assertEqual(ki["stats"]["nextId"], 2)
        self.assertIn("know-1", ki["byTag"]["aws"])

        # Verify: cross-refs created
        xref = self.read_json(self.kb / "Intelligence" / "cross-references.json")
        self.assertIn("reason-1", xref["know-1"]["referenced_by"])

        # Verify: memory updated
        mem = self.read_json(self.kb / "Memory" / "memory.json")
        self.assertEqual(mem["user_address"], "Sir")
        self.assertEqual(mem["last_session_snapshot"]["knowledge_count"], 1)

    def test_correction_then_verify(self):
        """Scenario: User says 'that's wrong, it's actually X'. Full correction cycle."""
        # Setup: stale claim exists in 3 places
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "Lambda timeout is 5 minutes",
             "confidence": 0.9, "tags": ["lambda"], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 5},
            {"id": "know-2", "category": "technical", "content": "Lambda timeout is 5 minutes max",
             "confidence": 0.8, "tags": ["lambda", "limits"], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 2}
        ])
        self.seed("reasoning", [
            {"id": "reason-1", "type": "deduction", "content": "Since Lambda timeout is 5 minutes, batch jobs need Step Functions",
             "intent": "Architecture", "reuse_signal": "Lambda timeout batch",
             "confidence": 0.85, "tags": ["lambda"], "provenance": "stated",
             "derived_from": ["know-1"], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 1}
        ])

        # Scan
        matches, total = cascade.scan_stores(self.kb, ["5 minutes"], ["knowledge", "reasoning"])
        self.assertEqual(total, 3)  # 2 knowledge + 1 reasoning

        # Apply to all
        all_ids = [m["id"] for m in matches]
        cascade.apply_fixes(self.kb, ["5 minutes"], "15 minutes", all_ids, ["knowledge", "reasoning"])

        # Verify: ALL instances corrected
        k = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        for entry in k["entries"]:
            self.assertNotIn("is 5 minutes", entry["content"])
            self.assertIn("15 minutes", entry["content"])

        r = self.read_json(self.kb / "Intelligence" / "reasoning.json")
        self.assertIn("15 minutes", r["entries"][0]["content"])

    def test_dedup_merge_remove_verify(self):
        """Scenario: maintenance finds duplicates, user approves merge+remove."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "S3 versioning enables object recovery and audit trails for compliance",
             "confidence": 0.9, "tags": ["s3", "versioning"], "created": "2026-01-01",
             "lastAccessed": "2026-04-16", "accessCount": 10},
            {"id": "know-2", "category": "technical", "content": "S3 versioning enables object recovery and audit trails for compliance needs",
             "confidence": 0.85, "tags": ["s3", "versioning", "rollback"], "created": "2026-02-01",
             "lastAccessed": "2026-03-01", "accessCount": 3}
        ])
        self.seed("reasoning", [
            {"id": "reason-1", "type": "deduction", "content": "Use versioning for audit trail",
             "intent": "compliance", "reuse_signal": "S3 audit", "confidence": 0.8,
             "tags": ["s3"], "provenance": "stated", "derived_from": ["know-2"],
             "created": "2026-01-01", "lastAccessed": "2026-01-01", "accessCount": 0}
        ])

        # Maintenance finds near-duplicate
        _, review = maint.check_store(self.kb, "knowledge")
        dupes = [r for r in review if r["type"] == "near_duplicate"]
        self.assertTrue(len(dupes) > 0)

        # User approves: keep know-1, merge tags from know-2, remove know-2
        removal.merge_tags(self.kb, {"know-2"}, "know-1")
        removal.remove_entries(self.kb, ["know-2"])
        removal.clean_derived_from(self.kb, ["know-2"])
        save_mod.rebuild_index(self.kb, "knowledge")
        save_mod.rebuild_index(self.kb, "reasoning")

        # Verify: know-1 has merged tags
        k = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertEqual(len(k["entries"]), 1)
        self.assertIn("rollback", k["entries"][0]["tags"])

        # Verify: reasoning derived_from cleaned
        r = self.read_json(self.kb / "Intelligence" / "reasoning.json")
        self.assertEqual(r["entries"][0]["derived_from"], [])

        # Verify: index accurate after removal
        ki = self.read_json(self.kb / "Intelligence" / "knowledge-index.json")
        self.assertEqual(ki["stats"]["totalEntries"], 1)
        self.assertNotIn("know-2", ki["summaries"])

    def test_idempotent_rerun_after_partial_failure(self):
        """Scenario: save crashes mid-way (EXIT:1), user re-runs same ops."""
        entries = [{"id": "know-1", "category": "technical", "content": "test",
                    "confidence": 0.8, "tags": ["t"]}]

        # First run: succeeds
        save_mod.add_entries(self.kb, "knowledge", entries)
        save_mod.rebuild_index(self.kb, "knowledge")

        # Second run: same entries — collision detection, no duplicates
        added, ok = save_mod.add_entries(self.kb, "knowledge", entries)
        self.assertEqual(added, [])  # Skipped
        self.assertTrue(ok)

        k = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertEqual(len(k["entries"]), 1)  # Still 1, not 2


# ─── OOB: Boundary and Stress Tests ──────────────────────────────────────

class TestOOB(TestBase):
    """What happens at boundaries, with bad data, under stress?"""

    def test_unicode_content(self):
        """Unicode in content, tags, and fields."""
        added, ok = save_mod.add_entries(self.kb, "knowledge",
            [{"id": "know-1", "category": "technical",
              "content": "日本語テスト — émojis 🚀 and spëcial chars",
              "confidence": 0.8, "tags": ["ünïcödé", "テスト"]}])
        self.assertTrue(ok)
        save_mod.rebuild_index(self.kb, "knowledge")
        idx = self.read_json(self.kb / "Intelligence" / "knowledge-index.json")
        self.assertIn("ünïcödé", idx["byTag"])

        # Cascade can find unicode
        matches, _ = cascade.scan_stores(self.kb, ["テスト"], ["knowledge"])
        self.assertEqual(len(matches), 1)

    def test_very_long_content(self):
        """Content at and beyond soft limits."""
        long_content = "x" * 1000
        errors = save_mod.validate_ops({
            "session_id": "session-2026-04-16-001",
            "new_knowledge": [{"id": "know-1", "category": "technical",
                               "content": long_content, "confidence": 0.8, "tags": ["t"]}]
        })
        warnings = [e for e in errors if "warning" in e.lower()]
        hard = [e for e in errors if "warning" not in e.lower()]
        self.assertTrue(len(warnings) > 0)  # Soft limit warning
        self.assertEqual(hard, [])  # No hard errors — it's a soft limit

    def test_empty_tags_list(self):
        """Entry with empty tags list — valid, no crash."""
        added, ok = save_mod.add_entries(self.kb, "knowledge",
            [{"id": "know-1", "category": "technical", "content": "no tags",
              "confidence": 0.8, "tags": []}])
        self.assertTrue(ok)
        save_mod.rebuild_index(self.kb, "knowledge")
        idx = self.read_json(self.kb / "Intelligence" / "knowledge-index.json")
        self.assertEqual(idx["byTag"], {})  # No tags indexed

    def test_confidence_boundary_values(self):
        """Confidence at exact boundaries: 0.0, 0.3, 0.5, 0.8, 1.0."""
        for conf in (0.0, 0.3, 0.5, 0.8, 1.0):
            errors = save_mod.validate_ops({
                "session_id": "session-2026-04-16-001",
                "new_knowledge": [{"id": "know-1", "category": "technical",
                                   "content": "t", "confidence": conf, "tags": ["t"]}]
            })
            hard = [e for e in errors if "warning" not in e.lower() and "confidence" in e]
            self.assertEqual(hard, [], f"Failed for confidence={conf}")

    def test_missing_optional_fields(self):
        """Entry with only required fields — defaults applied."""
        added, ok = save_mod.add_entries(self.kb, "knowledge",
            [{"id": "know-1", "category": "technical", "content": "minimal",
              "confidence": 0.8, "tags": ["t"]}])
        k = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        entry = k["entries"][0]
        self.assertIn("created", entry)
        self.assertIn("lastAccessed", entry)
        self.assertEqual(entry["accessCount"], 1)

    def test_corrupt_json_store(self):
        """Store file contains invalid JSON — load_json returns None, no crash."""
        with open(self.kb / "Intelligence" / "knowledge.json", 'w') as f:
            f.write("{invalid json")
        result = save_mod.load_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertIsNone(result)

    def test_missing_store_file(self):
        """Store file doesn't exist — load_json returns None, no crash."""
        os.remove(self.kb / "Intelligence" / "knowledge.json")
        result = save_mod.load_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertIsNone(result)

    def test_concurrent_session_ids(self):
        """Two different session IDs in session-index — both stored."""
        save_mod.update_session_index(self.kb, {"session_id": "session-2026-04-16-001"})
        save_mod.update_session_index(self.kb, {"session_id": "session-2026-04-16-002"})
        idx = self.read_json(self.kb / "Memory" / "session-index.json")
        self.assertEqual(len(idx["sessions"]), 2)
        self.assertEqual(idx["sessions"][0]["id"], "session-2026-04-16-002")  # Most recent first

    def test_removal_of_entry_referenced_in_cross_refs(self):
        """Remove entry that's a key in cross-refs AND in referenced_by of another."""
        self.write_json(self.kb / "Intelligence" / "cross-references.json", {
            "know-1": {"referenced_by": ["reason-1", "reason-2"], "related_to": []},
            "know-2": {"referenced_by": ["reason-1"], "related_to": []}
        })
        self.seed("reasoning", [
            {"id": "reason-1", "type": "deduction", "content": "test",
             "intent": "t", "reuse_signal": "t", "confidence": 0.8, "tags": [],
             "provenance": "stated", "derived_from": ["know-1", "know-2"],
             "created": "2026-01-01", "lastAccessed": "2026-01-01", "accessCount": 0}
        ])

        # Remove know-1 AND reason-1
        removal.clean_cross_references(self.kb, ["know-1", "reason-1"])
        removal.clean_derived_from(self.kb, ["know-1"])

        xref = self.read_json(self.kb / "Intelligence" / "cross-references.json")
        self.assertNotIn("know-1", xref)
        self.assertNotIn("reason-1", xref["know-2"]["referenced_by"])

        r = self.read_json(self.kb / "Intelligence" / "reasoning.json")
        self.assertEqual(r["entries"][0]["derived_from"], ["know-2"])

    def test_cascade_on_empty_stores(self):
        """Scan/apply on completely empty stores — no crash, 0 results."""
        matches, total = cascade.scan_stores(self.kb, ["anything"], ["knowledge", "patterns", "reasoning"])
        self.assertEqual(total, 0)

    def test_maintenance_on_large_store(self):
        """100 entries — maintenance completes without issues."""
        entries = [{"id": f"know-{i}", "category": "technical",
                    "content": f"entry number {i} with unique content {i*7}",
                    "confidence": 0.8, "tags": [f"tag-{i % 5}"],
                    "created": "2026-01-01", "lastAccessed": "2026-04-16", "accessCount": i}
                   for i in range(1, 101)]
        self.seed("knowledge", entries)
        save_mod.rebuild_index(self.kb, "knowledge")

        fixed, review = maint.check_store(self.kb, "knowledge")
        # Should find index mismatch (index was stale) but fix it
        idx = self.read_json(self.kb / "Intelligence" / "knowledge-index.json")
        self.assertEqual(idx["stats"]["totalEntries"], 100)


# ─── KNOW-001: Leave Nothing to Chance ────────────────────────────────────

class TestKnow001(TestBase):
    """Every implicit assumption is a place the LLM will guess wrong."""

    def test_accessCount_defaults_to_1_not_0(self):
        """New entries start at accessCount=1 (they were just created/accessed)."""
        added, _ = save_mod.add_entries(self.kb, "knowledge",
            [{"id": "know-1", "category": "technical", "content": "t",
              "confidence": 0.8, "tags": ["t"]}])
        k = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertEqual(k["entries"][0]["accessCount"], 1)

    def test_index_nextId_survives_rebuild(self):
        """After adding know-50, nextId must be 51 after rebuild."""
        self.seed("knowledge", [
            {"id": "know-50", "category": "technical", "content": "t",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        save_mod.rebuild_index(self.kb, "knowledge")
        idx = self.read_json(self.kb / "Intelligence" / "knowledge-index.json")
        self.assertEqual(idx["stats"]["nextId"], 51)

    def test_pattern_nextId_per_category(self):
        """Pattern nextId is per-category, not global."""
        self.seed("patterns", [
            {"id": "pref_10", "category": "preference", "content": "t",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0},
            {"id": "fail_5", "category": "failure", "content": "t",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        save_mod.rebuild_index(self.kb, "patterns")
        idx = self.read_json(self.kb / "Intelligence" / "patterns-index.json")
        self.assertEqual(idx["stats"]["nextId"]["pref"], 11)
        self.assertEqual(idx["stats"]["nextId"]["fail"], 6)

    def test_reasoning_index_has_intents(self):
        """Reasoning index must populate intents dict."""
        self.seed("reasoning", [
            {"id": "reason-1", "type": "deduction", "content": "test",
             "intent": "Optimize API latency", "reuse_signal": "Lambda latency",
             "confidence": 0.8, "tags": [], "provenance": "stated", "derived_from": [],
             "created": "2026-01-01", "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        save_mod.rebuild_index(self.kb, "reasoning")
        idx = self.read_json(self.kb / "Intelligence" / "reasoning-index.json")
        self.assertEqual(idx["intents"]["reason-1"], "Optimize API latency")

    def test_reasoning_index_has_byProvenance(self):
        """Reasoning index must populate byProvenance."""
        self.seed("reasoning", [
            {"id": "reason-1", "type": "deduction", "content": "t", "intent": "t",
             "reuse_signal": "t", "confidence": 0.8, "tags": [], "provenance": "synthesized",
             "derived_from": [], "created": "2026-01-01", "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        save_mod.rebuild_index(self.kb, "reasoning")
        idx = self.read_json(self.kb / "Intelligence" / "reasoning-index.json")
        self.assertIn("reason-1", idx["byProvenance"]["synthesized"])

    def test_reasoning_summary_uses_reuse_signal(self):
        """Reasoning index summary should use reuse_signal, not content."""
        self.seed("reasoning", [
            {"id": "reason-1", "type": "deduction",
             "content": "Long detailed reasoning about why X leads to Y",
             "intent": "t", "reuse_signal": "X causes Y",
             "confidence": 0.8, "tags": [], "provenance": "stated", "derived_from": [],
             "created": "2026-01-01", "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        save_mod.rebuild_index(self.kb, "reasoning")
        idx = self.read_json(self.kb / "Intelligence" / "reasoning-index.json")
        self.assertEqual(idx["summaries"]["reason-1"], "X causes Y")

    def test_cascade_replace_is_case_insensitive(self):
        """Replacement must find 'Python3' when searching for 'python3'."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "Use Python3 for scripts",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        cascade.apply_fixes(self.kb, ["python3"], "python", ["know-1"], ["knowledge"])
        k = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertNotIn("Python3", k["entries"][0]["content"])
        self.assertIn("python", k["entries"][0]["content"].lower())

    def test_removal_detects_all_pattern_prefixes(self):
        """Every pattern category prefix routes to 'patterns' store."""
        for cat, prefix in [("preference", "pref_"), ("approach", "approach_"),
                            ("failure", "fail_"), ("process", "process_"),
                            ("procedure", "procedure_"), ("ai_agent", "ai_agent_")]:
            self.assertEqual(removal.detect_store(f"{prefix}1"), "patterns",
                           f"{prefix} should route to patterns")

    def test_atomic_write_no_partial_on_crash(self):
        """If write fails, original file is unchanged (no .tmp left behind)."""
        path = self.kb / "Intelligence" / "test.json"
        save_mod.save_json(path, {"original": True})

        # Simulate write to read-only path (will fail)
        bad_path = Path("/proc/nonexistent/test.json")
        result = save_mod.save_json(bad_path, {"corrupted": True})
        self.assertFalse(result)

        # Original unchanged
        data = self.read_json(path)
        self.assertEqual(data, {"original": True})

    def test_session_index_outcome_note_preserved(self):
        """outcome_note field must survive round-trip through session index."""
        ops = {"session_id": "session-2026-04-16-001",
               "outcome": "partial", "outcome_note": "Blocked by IAM permissions"}
        save_mod.update_session_index(self.kb, ops)
        idx = self.read_json(self.kb / "Memory" / "session-index.json")
        self.assertEqual(idx["sessions"][0]["outcome_note"], "Blocked by IAM permissions")

    def test_memory_commitments_resolve(self):
        """Resolving a commitment sets status and date."""
        mem = self.read_json(self.kb / "Memory" / "memory.json")
        mem["commitments"] = [{"id": "c-001", "what": "deliver report", "status": "open"}]
        self.write_json(self.kb / "Memory" / "memory.json", mem)

        ops = {"session_id": "session-2026-04-16-001",
               "resolved_commitments": ["c-001"]}
        save_mod.update_memory(self.kb, ops)
        mem = self.read_json(self.kb / "Memory" / "memory.json")
        self.assertEqual(mem["commitments"][0]["status"], "resolved")
        self.assertIn("resolved_date", mem["commitments"][0])


if __name__ == "__main__":
    unittest.main()
