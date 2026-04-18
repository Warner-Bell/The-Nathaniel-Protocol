#!/usr/bin/env python3
"""Reseed template intelligence stores from the GOLDEN seed corpus.

Reads the seed data from the requirements doc (or standalone seed files),
validates integrity, and deploys to the Intelligence directory with fresh indexes.

Usage:
    python3 scripts/reseed.py                    # Reseed from current Intelligence/ files
    python3 scripts/reseed.py --from-doc PATH    # Extract seed from requirements doc
    python3 scripts/reseed.py --verify-only      # Verify without writing
"""

import json
import sys
import os
import re
from pathlib import Path
from collections import defaultdict


def find_kb_root():
    """Walk up from script location to find Nate's-kb."""
    p = Path(__file__).resolve().parent.parent
    kb = p / "Nate's-kb"
    if kb.exists():
        return kb
    # Try cwd
    kb = Path.cwd() / "Nate's-kb"
    if kb.exists():
        return kb
    print("ERROR: Cannot find Nate's-kb directory")
    sys.exit(2)


def load_store(path):
    with open(path) as f:
        return json.load(f)


def save_store(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def rebuild_knowledge_index(entries):
    idx = {
        "stats": {"totalEntries": len(entries), "activeEntries": len(entries), "nextId": len(entries) + 1},
        "byTag": defaultdict(list), "byCategory": defaultdict(list),
        "summaries": {}, "recentIds": [e["id"] for e in entries[-20:]]
    }
    for e in entries:
        for t in e.get("tags", []):
            idx["byTag"][t].append(e["id"])
        idx["byCategory"][e.get("category", "unknown")].append(e["id"])
        idx["summaries"][e["id"]] = e["content"][:120]
    idx["byTag"] = dict(idx["byTag"])
    idx["byCategory"] = dict(idx["byCategory"])
    return idx


def rebuild_reasoning_index(entries):
    idx = {
        "stats": {"totalEntries": len(entries), "activeEntries": len(entries), "nextId": len(entries) + 1},
        "byTag": defaultdict(list), "byType": defaultdict(list), "byProvenance": defaultdict(list),
        "summaries": {}, "intents": {}, "recentIds": [e["id"] for e in entries[-20:]]
    }
    for e in entries:
        for t in e.get("tags", []):
            idx["byTag"][t].append(e["id"])
        idx["byType"][e.get("type", "unknown")].append(e["id"])
        idx["byProvenance"][e.get("provenance", "stated")].append(e["id"])
        idx["summaries"][e["id"]] = e["content"][:120]
        idx["intents"][e["id"]] = e.get("intent", "")
    idx["byTag"] = dict(idx["byTag"])
    idx["byType"] = dict(idx["byType"])
    idx["byProvenance"] = dict(idx["byProvenance"])
    return idx


def rebuild_patterns_index(entries):
    next_ids = {}
    for e in entries:
        parts = e["id"].rsplit("_", 1)
        if len(parts) == 2:
            try:
                next_ids[parts[0]] = max(next_ids.get(parts[0], 0), int(parts[1]) + 1)
            except ValueError:
                pass
    idx = {
        "stats": {"totalEntries": len(entries), "activeEntries": len(entries), "nextId": next_ids},
        "byTag": defaultdict(list), "byCategory": defaultdict(list),
        "byConfidence": {"high": [], "medium": [], "low": []},
        "summaries": {}, "recentIds": [e["id"] for e in entries[-20:]]
    }
    for e in entries:
        for t in e.get("tags", []):
            idx["byTag"][t].append(e["id"])
        idx["byCategory"][e.get("category", "unknown")].append(e["id"])
        c = e.get("confidence", 0.5)
        if c >= 0.8:
            idx["byConfidence"]["high"].append(e["id"])
        elif c >= 0.5:
            idx["byConfidence"]["medium"].append(e["id"])
        else:
            idx["byConfidence"]["low"].append(e["id"])
        idx["summaries"][e["id"]] = e.get("content", "")[:120]
    idx["byTag"] = dict(idx["byTag"])
    idx["byCategory"] = dict(idx["byCategory"])
    return idx


def rebuild_cross_references(reasoning_entries, all_ids):
    xrefs = {"_meta": {"lastRebuilt": "2026-04-16"}, "references": {}, "stats": {"totalEntries": 0}}
    for e in reasoning_entries:
        for src_id in e.get("derived_from", []):
            if src_id.startswith("session-") or "/" in src_id:
                continue
            if src_id not in all_ids:
                continue
            if src_id not in xrefs["references"]:
                xrefs["references"][src_id] = {"referenced_by": [], "related_to": []}
            if e["id"] not in xrefs["references"][src_id]["referenced_by"]:
                xrefs["references"][src_id]["referenced_by"].append(e["id"])
    xrefs["stats"]["totalEntries"] = len(xrefs["references"])
    return xrefs


def validate(kb_root):
    """Run full integrity validation. Returns (ok, errors)."""
    intel = kb_root / "Intelligence"
    errors = []

    stores = {}
    for name in ["knowledge", "reasoning", "patterns", "synonym-map", "cross-references"]:
        path = intel / f"{name}.json"
        if not path.exists():
            errors.append(f"Missing: {name}.json")
            continue
        stores[name] = load_store(path)

    if errors:
        return False, errors

    k = stores["knowledge"]["entries"]
    r = stores["reasoning"]["entries"]
    p = stores["patterns"]["entries"]

    # Duplicate IDs
    for name, entries in [("knowledge", k), ("reasoning", r), ("patterns", p)]:
        ids = [e["id"] for e in entries]
        dupes = len(ids) - len(set(ids))
        if dupes:
            errors.append(f"{name}: {dupes} duplicate IDs")

    # Broken derived_from
    all_ids = set(e["id"] for e in k) | set(e["id"] for e in r) | set(e["id"] for e in p)
    for e in r:
        for ref in e.get("derived_from", []):
            if ref and not ref.startswith("session-") and "/" not in ref and ref not in all_ids:
                errors.append(f"{e['id']}: broken derived_from -> {ref}")

    # Zero-tag entries
    for name, entries in [("knowledge", k), ("reasoning", r), ("patterns", p)]:
        for e in entries:
            if not e.get("tags"):
                errors.append(f"{name} {e['id']}: zero tags")

    # PII check (excluding creator attribution)
    pii_terms = ["warner", "gadgetools", "techstar", "jillaman", "cloud nate", "openclaw", "plint", "quicksuite", "kyc"]
    for entries in [k, r, p]:
        for e in entries:
            if e.get("id") == "know-447":
                continue
            text = f"{e.get('content', '')} {e.get('source', '')}".lower()
            for term in pii_terms:
                if term in text:
                    errors.append(f"{e['id']}: PII leak '{term}'")

    return len(errors) == 0, errors


def reseed(kb_root, verify_only=False):
    """Reseed from current Intelligence/ stores."""
    intel = kb_root / "Intelligence"

    print(f"═══ Reseed: {intel} ═══")

    # Load stores
    k = load_store(intel / "knowledge.json")
    r = load_store(intel / "reasoning.json")
    p = load_store(intel / "patterns.json")
    syn = load_store(intel / "synonym-map.json")

    all_ids = set(e["id"] for e in k["entries"]) | set(e["id"] for e in r["entries"]) | set(e["id"] for e in p["entries"])

    print(f"  Knowledge: {len(k['entries'])}")
    print(f"  Reasoning: {len(r['entries'])}")
    print(f"  Patterns:  {len(p['entries'])}")
    print(f"  Synonyms:  {len(syn['synonyms'])}")

    # Validate before writing
    ok, errors = validate(kb_root)
    if not ok:
        print(f"\n  VALIDATION FAILED ({len(errors)} errors):")
        for err in errors[:10]:
            print(f"    {err}")
        if not verify_only:
            print("\n  Aborting reseed. Fix errors first.")
        return False

    if verify_only:
        print("\n  ✅ Validation passed. No writes (--verify-only)")
        return True

    # Rebuild all indexes
    ki = rebuild_knowledge_index(k["entries"])
    ri = rebuild_reasoning_index(r["entries"])
    pi = rebuild_patterns_index(p["entries"])
    xr = rebuild_cross_references(r["entries"], all_ids)

    # Write indexes
    save_store(intel / "knowledge-index.json", ki)
    save_store(intel / "reasoning-index.json", ri)
    save_store(intel / "patterns-index.json", pi)
    save_store(intel / "cross-references.json", xr)

    print(f"\n  Indexes rebuilt:")
    print(f"    knowledge-index: {ki['stats']['totalEntries']}")
    print(f"    reasoning-index: {ri['stats']['totalEntries']}")
    print(f"    patterns-index:  {pi['stats']['totalEntries']}")
    print(f"    cross-references: {xr['stats']['totalEntries']} sources")

    # Final validation
    ok, errors = validate(kb_root)
    if ok:
        print(f"\n  ✅ GOLDEN seed deployed. {len(k['entries'])+len(r['entries'])+len(p['entries'])} entries.")
    else:
        print(f"\n  ⚠️ Post-deploy validation found {len(errors)} issues")
        for err in errors:
            print(f"    {err}")

    return ok


def main():
    verify_only = "--verify-only" in sys.argv

    kb_root = find_kb_root()
    ok = reseed(kb_root, verify_only=verify_only)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
