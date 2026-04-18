#!/usr/bin/env python3
"""
Removal Cascade Script - Delete entries with full cascade cleanup.

Handles: store deletion, tag merging, index cleanup, cross-ref cleanup,
derived_from cleanup, full index rebuilds.

Usage: python3 scripts/removal-cascade.py ops.json
Exit codes: 0 = success, 1 = partial, 2 = total failure
"""

import json, sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module
save_mod = import_module("save-session")

STORE_PREFIXES = {
    "know-": "knowledge", "reason-": "reasoning",
    "pref_": "patterns", "approach_": "patterns", "fail_": "patterns",
    "process_": "patterns", "procedure_": "patterns", "ai_agent_": "patterns",
}


def detect_store(entry_id):
    for prefix, store in STORE_PREFIXES.items():
        if entry_id.startswith(prefix):
            return store
    # Fallback: pattern IDs have category_N format
    if "_" in entry_id:
        return "patterns"
    return None


def validate_ops(ops):
    errors = []
    if not isinstance(ops, dict):
        return ["Ops must be a JSON object"]
    remove = ops.get("remove", [])
    if not remove:
        errors.append("remove is required and must be non-empty")
    merge_to = ops.get("merge_tags_to")
    if merge_to and merge_to in remove:
        errors.append(f"merge_tags_to target '{merge_to}' cannot be in the remove list")
    for eid in remove:
        if detect_store(eid) is None:
            errors.append(f"Cannot detect store for ID: {eid}")
    return errors


def merge_tags(kb, remove_ids, target_id):
    """Copy tags from entries being removed to the target entry."""
    target_store = detect_store(target_id)
    if not target_store:
        print(f"  WARN: Cannot detect store for merge target {target_id}")
        return

    path = kb / "Intelligence" / f"{target_store}.json"
    data = save_mod.load_json(path)
    if data is None:
        return

    # Collect tags from entries being removed
    all_tags = set()
    for store_name in ("patterns", "knowledge", "reasoning"):
        spath = kb / "Intelligence" / f"{store_name}.json"
        sdata = save_mod.load_json(spath)
        if sdata is None:
            continue
        for entry in sdata.get("entries", []):
            if entry.get("id") in remove_ids:
                all_tags.update(entry.get("tags", []))

    # Add to target
    for entry in data.get("entries", []):
        if entry.get("id") == target_id:
            existing = set(entry.get("tags", []))
            new_tags = all_tags - existing
            if new_tags:
                entry["tags"] = sorted(existing | all_tags)
                save_mod.save_json(path, data)
                print(f"  ✓ Merged {len(new_tags)} tags to {target_id}")
            return

    print(f"  WARN: Merge target {target_id} not found in {target_store}")


def remove_entries(kb, remove_ids):
    """Remove entries from stores. Returns (removed_count, affected_stores)."""
    id_set = set(remove_ids)
    removed = 0
    affected = set()

    for store_name in ("patterns", "knowledge", "reasoning"):
        path = kb / "Intelligence" / f"{store_name}.json"
        data = save_mod.load_json(path)
        if data is None:
            continue

        before = len(data.get("entries", []))
        data["entries"] = [e for e in data["entries"] if e.get("id") not in id_set]
        after = len(data["entries"])
        delta = before - after

        if delta > 0:
            data["lastUpdated"] = save_mod.get_today()
            save_mod.save_json(path, data)
            removed += delta
            affected.add(store_name)
            print(f"  - {store_name}: {delta} removed")

    return removed, affected


def clean_cross_references(kb, remove_ids):
    """Remove IDs from cross-references (as keys and from referenced_by arrays)."""
    path = kb / "Intelligence" / "cross-references.json"
    xref = save_mod.load_json(path)
    if xref is None:
        return 0

    # Detect format: wrapped (has "references" key) or flat (entry IDs at top level)
    if "references" in xref:
        refs = xref["references"]
        wrapped = True
    else:
        refs = {k: v for k, v in xref.items() if not k.startswith("_")}
        wrapped = False

    cleaned = 0
    id_set = set(remove_ids)

    for eid in list(refs.keys()):
        if eid in id_set:
            del refs[eid]
            cleaned += 1

    for source_id, ref_data in refs.items():
        if isinstance(ref_data, dict):
            rb = ref_data.get("referenced_by", [])
            new_rb = [r for r in rb if r not in id_set]
            if len(new_rb) != len(rb):
                cleaned += len(rb) - len(new_rb)
                ref_data["referenced_by"] = new_rb

    if wrapped:
        xref["references"] = refs
        xref.setdefault("_meta", {})["last_updated"] = save_mod.get_today()
        xref["stats"] = {"total_sources": len(refs),
                         "total_references": sum(len(v.get("referenced_by", [])) for v in refs.values() if isinstance(v, dict))}
    else:
        xref = refs

    save_mod.save_json(path, xref)
    return cleaned


def clean_derived_from(kb, remove_ids):
    """Remove deleted IDs from reasoning derived_from arrays. Returns affected reasoning IDs."""
    path = kb / "Intelligence" / "reasoning.json"
    data = save_mod.load_json(path)
    if data is None:
        return []

    id_set = set(remove_ids)
    affected = []

    for entry in data.get("entries", []):
        df = entry.get("derived_from", [])
        new_df = [d for d in df if d not in id_set]
        if len(new_df) != len(df):
            entry["derived_from"] = new_df
            affected.append(entry["id"])

    if affected:
        data["lastUpdated"] = save_mod.get_today()
        save_mod.save_json(path, data)
        print(f"  ✓ derived_from cleaned in: {affected}")

    return affected


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/removal-cascade.py OPS_FILE")
        sys.exit(2)

    ops = save_mod.load_json(sys.argv[1])
    if ops is None:
        sys.exit(2)

    errors = validate_ops(ops)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    kb = save_mod.find_kb_root()
    remove_ids = ops["remove"]
    merge_to = ops.get("merge_tags_to")

    print(f"═══ Removal Cascade: {len(remove_ids)} entries ═══")

    lock_path = kb / "Intelligence" / "stores"
    try:
        with save_mod.FileLock(lock_path):
            # Merge tags before deletion
            if merge_to:
                print("Tag Merge")
                merge_tags(kb, set(remove_ids), merge_to)
                print()

            # Remove entries
            print("Remove Entries")
            removed, affected = remove_entries(kb, remove_ids)
            print()

            # Clean cross-references
            print("Cross-References")
            xref_cleaned = clean_cross_references(kb, remove_ids)
            print(f"  ✓ {xref_cleaned} refs cleaned")
            print()

            # Clean derived_from
            print("Derived From")
            df_affected = clean_derived_from(kb, remove_ids)
            print()

            # Rebuild all affected indexes (plus reasoning if derived_from changed)
            print("Index Rebuild")
            rebuild_stores = affected | ({"reasoning"} if df_affected else set())
            for store_name in rebuild_stores:
                save_mod.rebuild_index(kb, store_name)
            print()

    except TimeoutError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    result = {
        "removed": removed, "tags_merged_to": merge_to,
        "index_refs_cleaned": xref_cleaned,
        "derived_from_cleaned": len(df_affected),
        "derived_from_affected": df_affected,
        "EXIT": 0
    }
    print("═══ Result ═══")
    print(json.dumps(result, indent=2))

    try:
        os.remove(sys.argv[1])
    except OSError:
        pass


if __name__ == "__main__":
    main()
