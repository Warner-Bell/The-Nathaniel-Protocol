#!/usr/bin/env python3
"""Comprehensive edge case tests for the entire script offload system."""

import json, sys, tempfile, shutil, unittest, os
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

        for store in ("patterns", "knowledge", "reasoning"):
            self.write_json(self.kb / "Intelligence" / f"{store}.json", {"entries": [], "lastUpdated": "2026-01-01"})
            self.write_json(self.kb / "Intelligence" / f"{store}-index.json",
                           {"stats": {"totalEntries": 0, "nextId": 1 if store != "patterns" else {}},
                            "byTag": {}, "summaries": {}, "recentIds": []})

        # Flat cross-references (live KB format)
        self.write_json(self.kb / "Intelligence" / "cross-references.json", {})
        self.write_json(self.kb / "Memory" / "session-index.json", {"sessions": [], "recentIds": []})
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

    def seed(self, store, entries):
        self.write_json(self.kb / "Intelligence" / f"{store}.json",
                       {"entries": entries, "lastUpdated": "2026-01-01"})


# ─── SAVE-SESSION EDGE CASES ─────────────────────────────────────────────

class TestSaveEdgeCases(TestBase):
    def test_empty_ops_file(self):
        """Minimal ops with no entries, no updates — should succeed doing nothing."""
        ops = {"session_id": "session-2026-04-16-001", "schema_version": 1}
        errors = save_mod.validate_ops(ops)
        hard = [e for e in errors if "warning" not in e.lower()]
        self.assertEqual(hard, [])

    def test_empty_stores(self):
        """Adding to completely empty stores."""
        added, ok = save_mod.add_entries(self.kb, "knowledge",
            [{"id": "know-1", "category": "technical", "content": "first ever",
              "confidence": 0.8, "tags": ["first"]}])
        self.assertEqual(added, ["know-1"])
        self.assertTrue(ok)
        save_mod.rebuild_index(self.kb, "knowledge")
        idx = self.read_json(self.kb / "Intelligence" / "knowledge-index.json")
        self.assertEqual(idx["stats"]["totalEntries"], 1)
        self.assertEqual(idx["stats"]["nextId"], 2)

    def test_multiple_entries_same_batch(self):
        """Multiple entries in one ops file."""
        entries = [
            {"id": f"know-{i}", "category": "technical", "content": f"entry {i}",
             "confidence": 0.8, "tags": ["batch"]} for i in range(1, 6)
        ]
        added, ok = save_mod.add_entries(self.kb, "knowledge", entries)
        self.assertEqual(len(added), 5)
        save_mod.rebuild_index(self.kb, "knowledge")
        idx = self.read_json(self.kb / "Intelligence" / "knowledge-index.json")
        self.assertEqual(idx["stats"]["nextId"], 6)

    def test_cross_refs_flat_format(self):
        """Cross-references with flat format (live KB style)."""
        self.write_json(self.kb / "Intelligence" / "cross-references.json", {
            "know-1": {"referenced_by": [], "related_to": []}
        })
        new_r = [{"id": "reason-1", "derived_from": ["know-1"]}]
        save_mod.update_cross_references(self.kb, new_r)
        xref = self.read_json(self.kb / "Intelligence" / "cross-references.json")
        self.assertIn("reason-1", xref["know-1"]["referenced_by"])

    def test_cross_refs_wrapped_format(self):
        """Cross-references with wrapped format (template KB style)."""
        self.write_json(self.kb / "Intelligence" / "cross-references.json", {
            "_meta": {"last_updated": "2026-01-01"},
            "references": {"know-1": {"referenced_by": [], "related_to": []}},
            "stats": {}
        })
        new_r = [{"id": "reason-1", "derived_from": ["know-1"]}]
        save_mod.update_cross_references(self.kb, new_r)
        xref = self.read_json(self.kb / "Intelligence" / "cross-references.json")
        self.assertIn("reason-1", xref["references"]["know-1"]["referenced_by"])

    def test_cross_refs_empty(self):
        """Cross-references on empty file."""
        self.write_json(self.kb / "Intelligence" / "cross-references.json", {})
        new_r = [{"id": "reason-1", "derived_from": ["know-1"]}]
        save_mod.update_cross_references(self.kb, new_r)
        xref = self.read_json(self.kb / "Intelligence" / "cross-references.json")
        self.assertIn("know-1", xref)

    def test_session_id_with_high_sequence(self):
        """Session ID with 3-digit sequence."""
        errors = save_mod.validate_ops({"session_id": "session-2026-04-16-999"})
        hard = [e for e in errors if "warning" not in e.lower()]
        self.assertEqual(hard, [])

    def test_reasoning_defaults(self):
        """Reasoning entries get provenance and derived_from defaults."""
        added, _ = save_mod.add_entries(self.kb, "reasoning",
            [{"id": "reason-1", "type": "deduction", "content": "test",
              "intent": "test", "reuse_signal": "test", "confidence": 0.8, "tags": []}])
        store = self.read_json(self.kb / "Intelligence" / "reasoning.json")
        entry = store["entries"][0]
        self.assertEqual(entry["provenance"], "stated")
        self.assertEqual(entry["derived_from"], [])

    def test_memory_nested_updates(self):
        """Memory updates for domain_expertise merge, not overwrite."""
        mem = self.read_json(self.kb / "Memory" / "memory.json")
        mem["domain_expertise"] = {"aws": "expert"}
        self.write_json(self.kb / "Memory" / "memory.json", mem)

        ops = {"session_id": "session-2026-04-16-001",
               "memory_updates": {"domain_expertise": {"python": "proficient"}}}
        save_mod.update_memory(self.kb, ops)
        mem = self.read_json(self.kb / "Memory" / "memory.json")
        self.assertEqual(mem["domain_expertise"]["aws"], "expert")
        self.assertEqual(mem["domain_expertise"]["python"], "proficient")

    def test_active_project_update_existing(self):
        """Active project update merges into existing, doesn't duplicate."""
        mem = self.read_json(self.kb / "Memory" / "memory.json")
        mem["active_projects"] = [{"name": "Proj1", "status": "active"}]
        self.write_json(self.kb / "Memory" / "memory.json", mem)

        ops = {"session_id": "session-2026-04-16-001",
               "active_project_updates": [{"name": "Proj1", "status": "paused"}]}
        save_mod.update_memory(self.kb, ops)
        mem = self.read_json(self.kb / "Memory" / "memory.json")
        self.assertEqual(len(mem["active_projects"]), 1)
        self.assertEqual(mem["active_projects"][0]["status"], "paused")

    def test_both_ops_formats(self):
        """new_knowledge (flat) and new_entries.knowledge (nested) both work."""
        flat = save_mod.get_entries({"new_knowledge": [{"id": "know-1"}]}, "knowledge")
        nested = save_mod.get_entries({"new_entries": {"knowledge": [{"id": "know-2"}]}}, "knowledge")
        self.assertEqual(flat[0]["id"], "know-1")
        self.assertEqual(nested[0]["id"], "know-2")


# ─── CASCADE-CORRECTION EDGE CASES ───────────────────────────────────────

class TestCascadeEdgeCases(TestBase):
    def test_no_matches(self):
        """Scan with no matches returns empty."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "hello world",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        matches, total = cascade.scan_stores(self.kb, ["NONEXISTENT"], ["knowledge"])
        self.assertEqual(total, 0)
        self.assertEqual(matches, [])

    def test_dedup_per_entry(self):
        """Same entry matching in multiple fields appears once."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "WSL is great",
             "source": "WSL docs", "context": "WSL setup",
             "confidence": 0.8, "tags": ["wsl"], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        matches, total = cascade.scan_stores(self.kb, ["WSL"], ["knowledge"])
        self.assertEqual(total, 1)
        self.assertEqual(len(matches), 1)
        self.assertIn("content", matches[0]["fields"])

    def test_multiple_keywords(self):
        """Multiple keywords — entry matches if ANY keyword hits."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "python is great",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0},
            {"id": "know-2", "category": "technical", "content": "java is fine",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        matches, total = cascade.scan_stores(self.kb, ["python", "java"], ["knowledge"])
        self.assertEqual(total, 2)

    def test_apply_multiple_keywords_replace(self):
        """Apply replaces all keywords with new_value."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "use python3 and pip3",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        applied, _, _ = cascade.apply_fixes(
            self.kb, ["python3", "pip3"], "python/pip", ["know-1"], ["knowledge"])
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertNotIn("python3", store["entries"][0]["content"])
        self.assertNotIn("pip3", store["entries"][0]["content"])

    def test_scan_across_all_stores(self):
        """Scan finds matches across patterns, knowledge, and reasoning."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "target word here",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        self.seed("patterns", [
            {"id": "pref_1", "category": "preference", "content": "target word there",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        matches, total = cascade.scan_stores(self.kb, ["target"], ["knowledge", "patterns"])
        self.assertEqual(total, 2)
        stores_found = {m["store"] for m in matches}
        self.assertEqual(stores_found, {"knowledge", "patterns"})


# ─── REMOVAL-CASCADE EDGE CASES ──────────────────────────────────────────

class TestRemovalEdgeCases(TestBase):
    def test_remove_nonexistent(self):
        """Removing an ID that doesn't exist — graceful, 0 removed."""
        removed, affected = removal.remove_entries(self.kb, ["know-999"])
        self.assertEqual(removed, 0)

    def test_remove_across_stores(self):
        """Remove entries from multiple stores in one call."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "k",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        self.seed("patterns", [
            {"id": "pref_1", "category": "preference", "content": "p",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        removed, affected = removal.remove_entries(self.kb, ["know-1", "pref_1"])
        self.assertEqual(removed, 2)
        self.assertEqual(affected, {"knowledge", "patterns"})

    def test_merge_tags_deduplicates(self):
        """Tag merge doesn't create duplicates in target."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "target",
             "confidence": 0.8, "tags": ["shared", "unique-target"]},
            {"id": "know-2", "category": "technical", "content": "source",
             "confidence": 0.8, "tags": ["shared", "unique-source"]}
        ])
        removal.merge_tags(self.kb, {"know-2"}, "know-1")
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        target = [e for e in store["entries"] if e["id"] == "know-1"][0]
        self.assertEqual(target["tags"].count("shared"), 1)
        self.assertIn("unique-source", target["tags"])

    def test_derived_from_multiple_refs(self):
        """Removing an entry cleans it from multiple reasoning derived_from arrays."""
        self.seed("reasoning", [
            {"id": "reason-1", "type": "deduction", "content": "r1", "intent": "t",
             "reuse_signal": "t", "confidence": 0.8, "tags": [], "provenance": "stated",
             "derived_from": ["know-1", "know-2"], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0},
            {"id": "reason-2", "type": "deduction", "content": "r2", "intent": "t",
             "reuse_signal": "t", "confidence": 0.8, "tags": [], "provenance": "stated",
             "derived_from": ["know-1"], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 0}
        ])
        affected = removal.clean_derived_from(self.kb, ["know-1"])
        self.assertEqual(set(affected), {"reason-1", "reason-2"})
        store = self.read_json(self.kb / "Intelligence" / "reasoning.json")
        self.assertEqual(store["entries"][0]["derived_from"], ["know-2"])
        self.assertEqual(store["entries"][1]["derived_from"], [])

    def test_cross_ref_flat_format(self):
        """Cross-ref cleanup works with flat format."""
        self.write_json(self.kb / "Intelligence" / "cross-references.json", {
            "know-1": {"referenced_by": ["reason-1"], "related_to": []},
            "know-2": {"referenced_by": ["reason-1", "reason-2"], "related_to": []}
        })
        cleaned = removal.clean_cross_references(self.kb, ["know-1", "reason-1"])
        xref = self.read_json(self.kb / "Intelligence" / "cross-references.json")
        self.assertNotIn("know-1", xref)
        self.assertNotIn("reason-1", xref["know-2"]["referenced_by"])
        self.assertIn("reason-2", xref["know-2"]["referenced_by"])

    def test_detect_store_all_pattern_categories(self):
        """All pattern category prefixes detected correctly."""
        for prefix in ("pref_", "approach_", "fail_", "process_", "procedure_", "ai_agent_"):
            self.assertEqual(removal.detect_store(f"{prefix}1"), "patterns", f"Failed for {prefix}")


# ─── MAINTENANCE EDGE CASES ──────────────────────────────────────────────

class TestMaintenanceEdgeCases(TestBase):
    def test_empty_store(self):
        """Check on empty store — clean, no errors."""
        fixed, review = maint.check_store(self.kb, "knowledge")
        self.assertEqual(fixed, [])
        self.assertEqual(review, [])

    def test_check_mode_doesnt_write(self):
        """Check mode reports but doesn't modify."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "test",
             "confidence": 0.8, "tags": ["dup", "dup"], "created": "2026-04-01",
             "lastAccessed": "2026-01-01", "accessCount": -1}
        ])
        before = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        maint.check_store(self.kb, "knowledge", fix=False)
        after = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertEqual(before, after)

    def test_fix_mode_writes(self):
        """Fix mode actually modifies the store."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "test",
             "confidence": 0.8, "tags": ["dup", "dup"], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": -1}
        ])
        maint.check_store(self.kb, "knowledge", fix=True)
        store = self.read_json(self.kb / "Intelligence" / "knowledge.json")
        self.assertEqual(store["entries"][0]["accessCount"], 0)
        self.assertEqual(len(store["entries"][0]["tags"]), 1)

    def test_jaccard_empty_strings(self):
        """Jaccard on empty strings returns 0."""
        self.assertEqual(maint.jaccard("", ""), 0.0)
        self.assertEqual(maint.jaccard("hello", ""), 0.0)

    def test_orphaned_cross_ref_flat(self):
        """Orphaned cross-ref detection works with flat format."""
        self.write_json(self.kb / "Intelligence" / "cross-references.json", {
            "know-999": {"referenced_by": ["reason-1"], "related_to": []}
        })
        orphaned = maint.check_cross_references(self.kb)
        self.assertTrue(len(orphaned) > 0)

    def test_stale_3year_threshold(self):
        """Stale candidate only flagged after 3 years (1095 days), not 90."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "old but not 3 years",
             "confidence": 0.8, "tags": [], "created": "2024-01-01",
             "lastAccessed": "2024-01-01", "accessCount": 0}
        ])
        _, review = maint.check_store(self.kb, "knowledge")
        stale = [r for r in review if r["type"] == "stale_candidate"]
        self.assertEqual(len(stale), 0)  # ~2.3 years old, not 3

    def test_accessed_entry_never_stale(self):
        """Entry with accessCount > 0 is never flagged stale regardless of age."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "ancient but used",
             "confidence": 0.8, "tags": [], "created": "2020-01-01",
             "lastAccessed": "2026-04-16", "accessCount": 5}
        ])
        _, review = maint.check_store(self.kb, "knowledge")
        stale = [r for r in review if r["type"] == "stale_candidate"]
        self.assertEqual(len(stale), 0)


# ─── INTEGRATION EDGE CASES ──────────────────────────────────────────────

class TestIntegration(TestBase):
    def test_save_then_cascade_finds_new_entry(self):
        """Entry added by save-session is findable by cascade-correction."""
        save_mod.add_entries(self.kb, "knowledge",
            [{"id": "know-1", "category": "technical", "content": "findable keyword here",
              "confidence": 0.8, "tags": ["findable"]}])
        save_mod.rebuild_index(self.kb, "knowledge")
        matches, total = cascade.scan_stores(self.kb, ["findable"], ["knowledge"])
        self.assertEqual(total, 1)

    def test_save_then_remove_then_maintenance_clean(self):
        """Add entry, remove it, maintenance reports clean."""
        save_mod.add_entries(self.kb, "knowledge",
            [{"id": "know-1", "category": "technical", "content": "temporary",
              "confidence": 0.8, "tags": ["temp"]}])
        save_mod.rebuild_index(self.kb, "knowledge")
        removal.remove_entries(self.kb, ["know-1"])
        save_mod.rebuild_index(self.kb, "knowledge")
        fixed, review = maint.check_store(self.kb, "knowledge")
        self.assertEqual(fixed, [])

    def test_cascade_apply_then_maintenance_clean(self):
        """Correction applied, maintenance finds no issues."""
        self.seed("knowledge", [
            {"id": "know-1", "category": "technical", "content": "old term here",
             "confidence": 0.8, "tags": [], "created": "2026-01-01",
             "lastAccessed": "2026-01-01", "accessCount": 1}
        ])
        cascade.apply_fixes(self.kb, ["old term"], "new term", ["know-1"], ["knowledge"])
        fixed, review = maint.check_store(self.kb, "knowledge")
        issues = [f for f in fixed if f["type"] not in ("index_stats_mismatch",)]
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
