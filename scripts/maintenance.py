#!/usr/bin/env python3
"""
Maintenance Script - Health checks and safe auto-fixes for KB stores.

Modes:
  check: Report issues without fixing
  fix:   Apply safe auto-fixes, report items needing review

Usage: python3 scripts/maintenance.py '{"mode": "check|fix", "scope": "all|patterns|knowledge|reasoning"}'
Exit codes: 0 = clean/fixed, 1 = issues need review, 2 = error
"""

import json, sys, os, datetime
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module
save_mod = import_module("save-session")

STORE_NAMES = ("patterns", "knowledge", "reasoning")
JACCARD_THRESHOLD = 0.8


def tokenize(text):
    """Simple whitespace tokenizer for Jaccard similarity."""
    return set(text.lower().split())


def jaccard(a, b):
    """Jaccard token overlap between two strings."""
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def check_store(kb, store_name, fix=False):
    """Run health checks on a store. Returns (auto_fixed, needs_review)."""
    path = kb / "Intelligence" / f"{store_name}.json"
    data = save_mod.load_json(path)
    if data is None:
        return [], [{"type": "missing_store", "detail": f"{store_name}.json not found"}]

    entries = data.get("entries", [])
    index_path = kb / "Intelligence" / f"{store_name}-index.json"
    idx = save_mod.load_json(index_path) or {}

    auto_fixed = []
    needs_review = []
    changed = False
    today = save_mod.get_today()

    for entry in entries:
        eid = entry.get("id", "?")

        # lastAccessed < created
        created = entry.get("created", "")
        accessed = entry.get("lastAccessed", "")
        if created and accessed and accessed < created:
            if fix:
                entry["lastAccessed"] = created
                changed = True
            auto_fixed.append({"id": eid, "type": "lastAccessed_before_created",
                              "detail": f"lastAccessed {accessed} < created {created}"})

        # accessCount < 0
        ac = entry.get("accessCount", 0)
        if ac < 0:
            if fix:
                entry["accessCount"] = 0
                changed = True
            auto_fixed.append({"id": eid, "type": "negative_accessCount", "detail": f"accessCount was {ac}"})

        # Duplicate tags
        tags = entry.get("tags", [])
        if len(tags) != len(set(tags)):
            if fix:
                entry["tags"] = sorted(set(tags))
                changed = True
            auto_fixed.append({"id": eid, "type": "duplicate_tags", "detail": f"had {len(tags)} tags, {len(set(tags))} unique"})

        # Low confidence candidates
        conf = entry.get("confidence", 0.5)
        if conf < 0.3:
            needs_review.append({"id": eid, "type": "low_confidence", "detail": f"confidence {conf}"})

        # Stale candidates (accessCount=0, age > 3 years)
        if ac == 0 and created:
            try:
                age = (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(created)).days
                if age > 1095:
                    needs_review.append({"id": eid, "type": "stale_candidate",
                                        "detail": f"accessCount=0, age={age} days"})
            except ValueError:
                pass

    # Index stats mismatch
    idx_total = idx.get("stats", {}).get("totalEntries", 0)
    actual_total = len(entries)
    if idx_total != actual_total:
        if fix:
            save_mod.rebuild_index(kb, store_name)
        auto_fixed.append({"type": "index_stats_mismatch",
                          "detail": f"index says {idx_total}, store has {actual_total}"})

    # Entry in index but not in store (orphaned index entry)
    entry_ids = {e.get("id") for e in entries}
    idx_ids = set(idx.get("summaries", {}).keys())
    orphaned = idx_ids - entry_ids
    if orphaned:
        if fix:
            save_mod.rebuild_index(kb, store_name)
        auto_fixed.append({"type": "orphaned_index_entries", "detail": f"{len(orphaned)} entries in index but not store"})

    # Near-duplicate detection (Jaccard on content)
    if len(entries) > 1:
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                sim = jaccard(entries[i].get("content", ""), entries[j].get("content", ""))
                if sim >= JACCARD_THRESHOLD:
                    needs_review.append({
                        "type": "near_duplicate",
                        "detail": f"{entries[i]['id']} and {entries[j]['id']} are {sim:.0%} similar"
                    })

    if changed:
        data["lastUpdated"] = today
        save_mod.save_json(path, data)

    return auto_fixed, needs_review


def check_cross_references(kb):
    """Check for orphaned cross-references."""
    xref_path = kb / "Intelligence" / "cross-references.json"
    xref = save_mod.load_json(xref_path)
    if xref is None:
        return []

    # Detect format
    if "references" in xref:
        refs = xref["references"]
    else:
        refs = {k: v for k, v in xref.items() if not k.startswith("_") and isinstance(v, dict)}

    # Collect all existing IDs
    all_ids = set()
    for store_name in STORE_NAMES:
        data = save_mod.load_json(kb / "Intelligence" / f"{store_name}.json")
        if data:
            for e in data.get("entries", []):
                all_ids.add(e.get("id"))

    orphaned = []
    for source_id in refs:
        if source_id not in all_ids:
            orphaned.append({"type": "orphaned_cross_ref", "detail": f"Source {source_id} no longer exists"})

    return orphaned


def main():
    if len(sys.argv) < 2:
        print('Usage: python3 scripts/maintenance.py \'{"mode": "check|fix", "scope": "all"}\'')
        sys.exit(2)

    ops = json.loads(sys.argv[1])
    mode = ops.get("mode", "check")
    scope = ops.get("scope", "all")
    fix = mode == "fix"

    kb = save_mod.find_kb_root()
    stores = list(STORE_NAMES) if scope == "all" else [scope]

    total_fixed = []
    total_review = []

    print(f"═══ Maintenance {'Fix' if fix else 'Check'} ═══")
    print()

    for store_name in stores:
        if store_name not in STORE_NAMES:
            continue
        print(f"{store_name.title()}")
        fixed, review = check_store(kb, store_name, fix=fix)
        total_fixed.extend(fixed)
        total_review.extend(review)
        if fixed:
            for f in fixed:
                print(f"  {'FIXED' if fix else 'FIXABLE'}: {f['type']} — {f.get('id', '')} {f['detail']}")
        if review:
            for r in review:
                print(f"  REVIEW: {r['type']} — {r.get('id', '')} {r['detail']}")
        if not fixed and not review:
            print("  ✓ Clean")
        print()

    # Cross-reference check
    if scope == "all":
        print("Cross-References")
        orphaned = check_cross_references(kb)
        total_review.extend(orphaned)
        if orphaned:
            for o in orphaned:
                print(f"  REVIEW: {o['detail']}")
        else:
            print("  ✓ Clean")
        print()

    result = {"issues_found": len(total_fixed) + len(total_review),
              "auto_fixed": len(total_fixed) if fix else 0,
              "needs_review": len(total_review),
              "details": {"fixed": total_fixed, "review": total_review}}

    print("═══ Summary ═══")
    print(json.dumps({k: v for k, v in result.items() if k != "details"}, indent=2))

    sys.exit(1 if total_review else 0)


if __name__ == "__main__":
    main()
