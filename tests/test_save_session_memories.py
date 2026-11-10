#!/usr/bin/env python3
"""Tests for save-session.py new_memories handling + memory-index rebuild.

Why this exists: two earlier sessions both recorded the
same unclosed gap. save-session.py had NO path to append an entry to memory.json's
`memories` dict. Routing one through `memory_updates` either landed it as a stray
TOP-LEVEL key (the origin of ~15 junk keys) or, after the 2026-09-21
hardening, got REFUSED by the shrink guard because a 1-item list is smaller than the
38-entry dict it would replace. So the only way to record a memory was a hand edit of
memory.json, which the script-first gate prohibits and which caused data loss.

Nothing rebuilt Memory/memory-index.json either: the only writer was
scripts/normalize-memory.py, a one-shot normalizer with hardcoded absolute paths, and
its output shape is already behind the live index (it never writes stats.nextId).

Format authority for these assertions is the LIVE index, not normalize-memory.py.
"""

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

REQUIRED = ("id", "type", "content", "context", "confidence", "tags",
            "created", "lastAccessed", "accessCount")


def memory_entry(mid, **over):
    e = {
        "id": mid,
        "type": "preference",
        "content": f"content for {mid}",
        "context": "unit test",
        "confidence": 0.9,
        "tags": ["testing"],
        "created": "2026-09-22",
        "lastAccessed": "2026-09-22",
        "accessCount": 0,
    }
    e.update(over)
    return e


class MemoryOpsBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.kb = Path(self.tmp) / "Nate's-kb"
        (self.kb / "Memory").mkdir(parents=True)
        (self.kb / "Intelligence").mkdir(parents=True)
        for s in ("patterns", "knowledge", "reasoning"):
            (self.kb / "Intelligence" / f"{s}.json").write_text(
                json.dumps({"entries": []}), encoding="utf-8")
        self.mem_path = self.kb / "Memory" / "memory.json"
        self.idx_path = self.kb / "Memory" / "memory-index.json"
        self.write_mem({
            "version": "1.0",
            "memories": {"mem-001": memory_entry("mem-001", tags=["existing"]),
                         "mem-075": memory_entry("mem-075", tags=["existing"])},
            "active_projects": [],
        })
        save_mod.DRY_RUN = False

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write_mem(self, data):
        self.mem_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def read_mem(self):
        return json.loads(self.mem_path.read_text(encoding="utf-8"))

    def read_idx(self):
        return json.loads(self.idx_path.read_text(encoding="utf-8"))

    def run_ops(self, **ops):
        base = {"session_id": "session-2026-09-22-001"}
        base.update(ops)
        return save_mod.update_memory(self.kb, base)


class TestNewMemories(MemoryOpsBase):

    def test_appends_into_memories_dict_keyed_by_id(self):
        self.run_ops(new_memories=[memory_entry("mem-076", tags=["fresh"])])
        mems = self.read_mem()["memories"]
        self.assertIn("mem-076", mems)
        self.assertEqual(mems["mem-076"]["tags"], ["fresh"])

    def test_never_lands_as_top_level_key(self):
        """The top-level key leakage shape must not reappear."""
        self.run_ops(new_memories=[memory_entry("mem-076")])
        mem = self.read_mem()
        self.assertNotIn("new_memories", mem)

    def test_existing_memories_preserved(self):
        """Appending must not drop or replace what is already there."""
        self.run_ops(new_memories=[memory_entry("mem-076")])
        mems = self.read_mem()["memories"]
        self.assertEqual(len(mems), 3)
        self.assertEqual(mems["mem-001"]["tags"], ["existing"])
        self.assertEqual(mems["mem-075"]["tags"], ["existing"])

    def test_duplicate_id_refused_and_original_untouched(self):
        """ID-collision class: never silently overwrite a live entry."""
        self.run_ops(new_memories=[memory_entry("mem-001", content="CLOBBERED")])
        mems = self.read_mem()["memories"]
        self.assertEqual(mems["mem-001"]["content"], "content for mem-001")
        self.assertEqual(len(mems), 2)

    def test_missing_required_field_refused(self):
        for field in REQUIRED:
            with self.subTest(missing=field):
                bad = memory_entry("mem-076")
                del bad[field]
                self.run_ops(new_memories=[bad])
                self.assertNotIn("mem-076", self.read_mem()["memories"],
                                 f"entry missing '{field}' must be refused")

    def test_invalid_type_refused(self):
        self.run_ops(new_memories=[memory_entry("mem-076", type="not_a_real_type")])
        self.assertNotIn("mem-076", self.read_mem()["memories"])

    def test_valid_types_accepted(self):
        types = ("preference", "decision", "correction", "learning",
                 "critical_safety", "system")
        for i, t in enumerate(types):
            with self.subTest(type=t):
                mid = f"mem-{100 + i}"
                self.run_ops(new_memories=[memory_entry(mid, type=t)])
                self.assertIn(mid, self.read_mem()["memories"])


class TestMemoryIndexRebuild(MemoryOpsBase):

    def test_index_written_on_memory_change(self):
        self.run_ops(new_memories=[memory_entry("mem-076")])
        self.assertTrue(self.idx_path.exists(), "memory-index.json must be rebuilt")

    def test_index_shape_matches_live_contract(self):
        self.run_ops(new_memories=[memory_entry("mem-076")])
        idx = self.read_idx()
        for key in ("_meta", "stats", "byTag", "byType", "byConfidence",
                    "summaries", "recentIds"):
            self.assertIn(key, idx)
        for bucket in ("critical", "high", "medium", "low"):
            self.assertIn(bucket, idx["byConfidence"])

    def test_stats_counts_entries(self):
        self.run_ops(new_memories=[memory_entry("mem-076")])
        stats = self.read_idx()["stats"]
        self.assertEqual(stats["totalEntries"], 3)
        self.assertEqual(stats["activeEntries"], 3)

    def test_nextid_derives_from_max_id_not_count(self):
        """Live index reads nextId=76 against 38 entries because ids are sparse.

        Deriving nextId from the count would hand out an id that already exists.
        """
        self.run_ops(new_memories=[memory_entry("mem-076")])
        self.assertEqual(self.read_idx()["stats"]["nextId"], 77)

    def test_tag_type_confidence_routing(self):
        self.run_ops(new_memories=[
            memory_entry("mem-076", tags=["alpha", "beta"], type="decision",
                         confidence=1.0),
            memory_entry("mem-077", tags=["alpha"], type="learning",
                         confidence=0.4),
        ])
        idx = self.read_idx()
        self.assertCountEqual(idx["byTag"]["alpha"], ["mem-076", "mem-077"])
        self.assertEqual(idx["byTag"]["beta"], ["mem-076"])
        self.assertIn("mem-076", idx["byType"]["decision"])
        self.assertIn("mem-076", idx["byConfidence"]["critical"])
        self.assertIn("mem-077", idx["byConfidence"]["low"])

    def test_summaries_present_for_every_entry(self):
        self.run_ops(new_memories=[memory_entry("mem-076")])
        idx = self.read_idx()
        self.assertEqual(set(idx["summaries"]), set(self.read_mem()["memories"]))

    def test_index_rebuilt_even_when_only_other_memory_fields_change(self):
        """A commitment resolve also has to leave the index consistent."""
        mem = self.read_mem()
        mem["commitments"] = [{"what": "x", "status": "open"}]
        self.write_mem(mem)
        self.run_ops(resolved_commitments=["x"])
        self.assertTrue(self.idx_path.exists())
        self.assertEqual(self.read_idx()["stats"]["totalEntries"], 2)

    def test_recent_ids_deterministic_on_tied_lastaccessed(self):
        """Ties must break on numeric id, not dict insertion order.

        lastAccessed is often a bare date, so ties are the common case (three live
        entries share 2026-09-15). Without a tiebreak the rebuild is not reproducible
        and every save produces a spurious recentIds diff.
        """
        self.run_ops(new_memories=[
            memory_entry("mem-076", lastAccessed="2026-09-15"),
            memory_entry("mem-077", lastAccessed="2026-09-15"),
            memory_entry("mem-078", lastAccessed="2026-09-01"),
        ])
        first_run = self.read_idx()["recentIds"]
        # Contract: lastAccessed descending, then numeric id descending.
        # Fixture mem-001 and mem-075 both sit at 2026-09-22 (the later date), so they
        # lead; mem-077/076 tie at 09-15 and break on id; mem-078 is oldest.
        self.assertEqual(first_run,
                         ["mem-075", "mem-001", "mem-077", "mem-076", "mem-078"])

        # Rebuilding from the same data must give the identical list.
        save_mod.rebuild_memory_index(self.kb, self.read_mem())
        self.assertEqual(self.read_idx()["recentIds"], first_run)

    def test_existing_summaries_preserved_not_regenerated(self):
        """A hand-authored or differently-truncated summary must survive a rebuild.

        The live index carries a mix of 150-char and 200-char truncations plus longer
        hand-written ones. Regenerating all of them would churn 17 entries for no gain.
        """
        save_mod.rebuild_memory_index(self.kb, self.read_mem())
        idx = self.read_idx()
        idx["summaries"]["mem-001"] = "HAND WRITTEN SUMMARY"
        self.idx_path.write_text(json.dumps(idx), encoding="utf-8")

        self.run_ops(new_memories=[memory_entry("mem-076")])
        self.assertEqual(self.read_idx()["summaries"]["mem-001"],
                         "HAND WRITTEN SUMMARY")


if __name__ == "__main__":
    unittest.main()
