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


class TestFileStructureCheck(TestBase):
    """Tests for file_structure_check — stale reference detection."""

    def _init_git(self):
        """Init a git repo in the temp dir so git status works."""
        import subprocess
        root = self.kb.parent
        subprocess.run(["git", "init"], cwd=root, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=root, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init", "--allow-empty"],
                       cwd=root, capture_output=True, env={**os.environ, "GIT_AUTHOR_NAME": "test",
                       "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t"})

    def test_no_changes_returns_empty(self):
        self._init_git()
        alerts = save_mod.file_structure_check(self.kb)
        self.assertEqual(alerts, [])

    def test_detects_new_file(self):
        self._init_git()
        (self.kb.parent / "newfile.txt").write_text("hello")
        alerts = save_mod.file_structure_check(self.kb)
        combined = "\n".join(alerts)
        self.assertIn("New files", combined)
        self.assertIn("newfile.txt", combined)

    def test_detects_deleted_file(self):
        self._init_git()
        # Create and commit a file, then delete it
        import subprocess
        root = self.kb.parent
        (root / "doomed.txt").write_text("bye")
        subprocess.run(["git", "add", "doomed.txt"], cwd=root, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add doomed"], cwd=root, capture_output=True,
                       env={**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t",
                       "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t"})
        os.remove(root / "doomed.txt")
        alerts = save_mod.file_structure_check(self.kb)
        combined = "\n".join(alerts)
        self.assertIn("Deleted files", combined)
        self.assertIn("doomed.txt", combined)

    def test_finds_stale_references_in_knowledge(self):
        self._init_git()
        import subprocess
        root = self.kb.parent
        # Create and commit a file
        (root / "old-protocol.md").write_text("content")
        subprocess.run(["git", "add", "old-protocol.md"], cwd=root, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], cwd=root, capture_output=True,
                       env={**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t",
                       "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t"})
        # Add a knowledge entry referencing it
        self.write_json(self.kb / "Intelligence" / "knowledge.json", {
            "entries": [{"id": "know-001", "content": "See old-protocol.md for details", "source": ""}],
            "lastUpdated": "2026-01-01"
        })
        # Delete the file
        os.remove(root / "old-protocol.md")
        alerts = save_mod.file_structure_check(self.kb)
        combined = "\n".join(alerts)
        self.assertIn("STALE REFERENCES", combined)
        self.assertIn("know-001", combined)
        self.assertIn("old-protocol.md", combined)

    def test_finds_stale_references_in_reasoning(self):
        self._init_git()
        import subprocess
        root = self.kb.parent
        (root / "removed.md").write_text("x")
        subprocess.run(["git", "add", "removed.md"], cwd=root, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], cwd=root, capture_output=True,
                       env={**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t",
                       "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t"})
        self.write_json(self.kb / "Intelligence" / "reasoning.json", {
            "entries": [{"id": "reason-001", "content": "Based on removed.md analysis", "source": ""}],
            "lastUpdated": "2026-01-01"
        })
        os.remove(root / "removed.md")
        alerts = save_mod.file_structure_check(self.kb)
        combined = "\n".join(alerts)
        self.assertIn("STALE REFERENCES", combined)
        self.assertIn("reason-001", combined)

    def test_skips_temp_files(self):
        self._init_git()
        (self.kb.parent / "_save_ops_test.json").write_text("{}")
        alerts = save_mod.file_structure_check(self.kb)
        combined = "\n".join(alerts) if alerts else ""
        self.assertNotIn("_save_ops", combined)

    def test_no_git_returns_empty(self):
        # No git init — should skip gracefully
        alerts = save_mod.file_structure_check(self.kb)
        self.assertEqual(alerts, [])


if __name__ == "__main__":
    unittest.main()
