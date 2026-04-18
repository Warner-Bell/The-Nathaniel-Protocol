#!/usr/bin/env python3
"""Normalize intelligence store schemas to canonical definitions.

One-time migration script. Normalizes intelligence store entries to canonical schemas.

Usage:
    python3 scripts/normalize-schemas.py [--dry-run]
"""
import json
import sys
import os
import copy
from collections import defaultdict

DRY_RUN = "--dry-run" in sys.argv
KB_DIR = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Nate's-kb", "Intelligence")
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Shared helpers ---

def pick_most_recent_date(*dates):
    """Return the most recent YYYY-MM-DD date from a list, ignoring None/empty."""
    valid = [d[:10] for d in dates if d and isinstance(d, str)]
    return max(valid) if valid else None

def normalize_date(val):
    """Normalize date to YYYY-MM-DD."""
    if not val or not isinstance(val, str):
        return None
    return val[:10]

def merge_into_content(entry, field, limit):
    """Absorb a field's value into content. Returns True if absorbed."""
    val = entry.get(field)
    if not val or not isinstance(val, str):
        return False
    content = entry.get("content", "")
    merged = f"{content} | {val}" if content else val
    if len(merged) <= limit:
        entry["content"] = merged
        return True
    return False  # skip absorption, would exceed limit

# --- Pattern migration ---

PATTERN_ABSORB_FIELDS = ["methodology", "key_insight", "template"]
PATTERN_DROP_FIELDS = {"failureRate", "evidence_count", "prevented_count", "missed_count", "context_scope"}
PATTERN_CONTENT_LIMIT = 400
PATTERN_CATEGORIES = {"preference", "approach", "failure", "process", "procedure", "ai_agent"}

def migrate_pattern(entry, stats):
    e = copy.deepcopy(entry)
    eid = e.get("id", "UNKNOWN")

    # Step 1: content consolidation (pattern vs content — keep longer)
    if "pattern" in e:
        pat = e.pop("pattern")
        if "content" in e:
            if len(pat) > len(e["content"]):
                e["content"] = pat
            stats["pattern_merged"] += 1
        else:
            e["content"] = pat
            stats["pattern_renamed"] += 1

    if "summary" in e and "content" not in e:
        e["content"] = e.pop("summary")
        stats["summary_renamed"] += 1
    elif "summary" in e:
        e.pop("summary")

    if "content" not in e:
        stats["review"].append((eid, "NO CONTENT after all renames — CRITICAL"))
        return None

    # Step 2: date field consolidation
    # Collect all date candidates for created
    created_candidates = [e.get("created"), e.get("first_observed"), e.get("last_updated") if "created" not in e else None]
    # Collect all date candidates for lastAccessed
    la_candidates = [e.get("lastAccessed"), e.get("last_observed"), e.get("lastUpdated"),
                     e.get("last_updated"), e.get("lastOccurred"), e.get("lastModified"), e.get("last_accessed")]

    created_val = normalize_date(e.get("created")) or normalize_date(e.get("first_observed"))
    if not created_val and "last_updated" in e and "created" not in e:
        created_val = normalize_date(e.get("last_updated"))

    la_val = pick_most_recent_date(*[e.get(f) for f in ["lastAccessed", "last_observed", "lastUpdated",
                                                          "last_updated", "lastOccurred", "lastModified", "last_accessed"]])

    # Remove all legacy date fields
    for f in ["first_observed", "last_observed", "lastUpdated", "last_updated", "lastOccurred", "lastModified", "last_accessed"]:
        e.pop(f, None)

    if created_val:
        e["created"] = created_val
    if la_val:
        e["lastAccessed"] = la_val

    # Step 3: count field consolidation (max of all)
    count_vals = [e.get(f, 0) for f in ["accessCount", "access_count", "observation_count", "occurrences"] if f in e]
    ac_val = max(count_vals) if count_vals else 0
    for f in ["access_count", "observation_count", "occurrences"]:
        if f in e:
            e.pop(f)
            stats["count_merged"] += 1
    e["accessCount"] = ac_val

    # Step 4: absorb fields into content
    for field in PATTERN_ABSORB_FIELDS:
        if field in e:
            absorbed = merge_into_content(e, field, PATTERN_CONTENT_LIMIT)
            e.pop(field, None)
            if absorbed:
                stats["absorbed"] += 1
            else:
                stats["absorb_skipped"] += 1

    # context_scope → context
    if "context_scope" in e:
        if "context" not in e:
            e["context"] = e.pop("context_scope")
        else:
            e.pop("context_scope")

    # resolution/correction → prevention
    for f in ["resolution", "correction"]:
        if f in e:
            if "prevention" not in e:
                e["prevention"] = e.pop(f)
            else:
                e.pop(f)

    # Step 5: drop fields
    for f in PATTERN_DROP_FIELDS:
        if f in e:
            e.pop(f)
            stats["dropped"] += 1

    # Step 6: backfill required fields
    if "created" not in e:
        e["created"] = "2026-01-01"
        stats["backfilled"] += 1
    if "lastAccessed" not in e:
        e["lastAccessed"] = e["created"]
        stats["backfilled"] += 1
    if "context" not in e:
        e["_needs_review"] = True
        e["context"] = "needs classification"
        stats["review"].append((eid, "missing context"))
    if "tags" not in e or not e["tags"]:
        e["tags"] = ["untagged"]
        e["_needs_review"] = True
        stats["review"].append((eid, "missing tags"))
    if "confidence" not in e:
        e["confidence"] = 0.5
        stats["backfilled"] += 1

    # Step 7: validate category
    cat = e.get("category", "")
    if cat not in PATTERN_CATEGORIES:
        e["_needs_review"] = True
        stats["review"].append((eid, f"category '{cat}' not in enum"))

    # Step 8: content length flag
    if len(e.get("content", "")) > PATTERN_CONTENT_LIMIT:
        e["_needs_trim"] = True

    return e

# --- Knowledge migration ---

KNOWLEDGE_DROP_FIELDS = {"type"}
KNOWLEDGE_CONTENT_LIMIT = 600
KNOWLEDGE_CATEGORIES = {"technical", "process", "error_solution", "best_practice", "tool_quirk",
                        "reference", "domain_expertise", "architecture", "research", "security",
                        "tool_behavior", "aws_gotcha", "system"}

def migrate_knowledge(entry, stats):
    e = copy.deepcopy(entry)
    eid = e.get("id", "UNKNOWN")

    # Content consolidation
    if "summary" in e:
        if "content" not in e:
            e["content"] = e.pop("summary")
            stats["summary_renamed"] += 1
        else:
            e.pop("summary")  # drop redundant

    if "content" not in e:
        stats["review"].append((eid, "NO CONTENT — CRITICAL"))
        return None

    # Date consolidation
    created_val = normalize_date(e.get("created")) or normalize_date(e.get("timestamp")) or normalize_date(e.get("firstSeen"))
    la_val = pick_most_recent_date(*[e.get(f) for f in ["lastAccessed", "lastUpdated", "last_accessed", "lastSeen", "lastModified"]])

    for f in ["timestamp", "firstSeen", "lastUpdated", "last_accessed", "lastSeen", "lastModified"]:
        e.pop(f, None)

    if created_val:
        e["created"] = created_val
    if la_val:
        e["lastAccessed"] = la_val

    # Count consolidation
    if "access_count" in e:
        e["accessCount"] = e.pop("access_count")
        stats["count_merged"] += 1

    # Drop fields
    for f in KNOWLEDGE_DROP_FIELDS:
        if f in e:
            e.pop(f)
            stats["dropped"] += 1

    # Backfill
    if "created" not in e:
        e["created"] = "2026-01-01"
        stats["backfilled"] += 1
    if "lastAccessed" not in e:
        e["lastAccessed"] = e["created"]
        stats["backfilled"] += 1
    if "accessCount" not in e:
        e["accessCount"] = 0
        stats["backfilled"] += 1
    if "source" not in e:
        e["source"] = "unknown"
        stats["backfilled"] += 1
    if "confidence" not in e:
        e["confidence"] = 0.5
        stats["backfilled"] += 1
    if "tags" not in e or not e["tags"]:
        e["tags"] = ["untagged"]
        e["_needs_review"] = True
        stats["review"].append((eid, "missing tags"))

    # Validate category
    cat = e.get("category", "")
    if not cat or cat not in KNOWLEDGE_CATEGORIES:
        e["_needs_review"] = True
        if not cat:
            e["category"] = "uncategorized"
        stats["review"].append((eid, f"category '{cat}' needs classification"))

    # Content length
    if len(e.get("content", "")) > KNOWLEDGE_CONTENT_LIMIT:
        e["_needs_trim"] = True

    return e

# --- Reasoning migration ---

REASONING_CONTENT_LIMIT = 700
REASONING_TYPES = {"deduction", "induction", "analogy", "causal", "meta-process",
                   "insight", "architectural_decision", "failure_analysis"}

def migrate_reasoning(entry, stats):
    e = copy.deepcopy(entry)
    eid = e.get("id", "UNKNOWN")

    # Content consolidation
    if "summary" in e and "content" not in e:
        e["content"] = e.pop("summary")
        stats["summary_renamed"] += 1
    elif "summary" in e:
        e.pop("summary")

    # Absorb evidence into content
    if "evidence" in e:
        merge_into_content(e, "evidence", REASONING_CONTENT_LIMIT)
        e.pop("evidence", None)

    if "content" not in e:
        stats["review"].append((eid, "NO CONTENT — CRITICAL"))
        return None

    # Source → derived_from migration
    derived = list(e.get("derived_from", []))
    for f in ["source_patterns", "source_knowledge", "sources"]:
        val = e.get(f)
        if isinstance(val, list):
            derived.extend(val)
        e.pop(f, None)

    if "source" in e:
        src = e["source"]
        if not derived and isinstance(src, str) and src:
            derived.append(src)
        e.pop("source")
        stats["source_migrated"] += 1

    e["derived_from"] = list(dict.fromkeys(derived))  # dedup preserving order

    # Date consolidation
    created_val = normalize_date(e.get("created")) or normalize_date(e.get("firstSeen")) or normalize_date(e.get("timestamp"))
    la_val = pick_most_recent_date(*[e.get(f) for f in ["lastAccessed", "lastSeen", "lastUpdated"]])

    for f in ["firstSeen", "lastSeen", "lastUpdated", "timestamp"]:
        e.pop(f, None)

    if created_val:
        e["created"] = created_val
    if la_val:
        e["lastAccessed"] = la_val

    # Backfill
    if "provenance" not in e:
        e["provenance"] = "stated"
        stats["backfilled"] += 1
    if "created" not in e:
        e["created"] = "2026-02-01"
        stats["backfilled"] += 1
    if "lastAccessed" not in e:
        e["lastAccessed"] = e["created"]
        stats["backfilled"] += 1
    if "accessCount" not in e:
        e["accessCount"] = 0
        stats["backfilled"] += 1
    if "tags" not in e or not e["tags"]:
        e["tags"] = ["untagged"]
        e["_needs_review"] = True
        stats["review"].append((eid, "missing tags"))
    if "intent" not in e:
        e["intent"] = "needs classification"
        e["_needs_review"] = True
        stats["review"].append((eid, "missing intent"))
    if "reuse_signal" not in e:
        e["reuse_signal"] = "needs classification"
        e["_needs_review"] = True
        stats["review"].append((eid, "missing reuse_signal"))
    if "confidence" not in e:
        e["confidence"] = 0.5
        stats["backfilled"] += 1

    # Validate type
    t = e.get("type", "")
    if not t or t not in REASONING_TYPES:
        e["_needs_review"] = True
        if not t:
            e["type"] = "insight"
        stats["review"].append((eid, f"type '{t}' needs classification"))

    # Content length
    if len(e.get("content", "")) > REASONING_CONTENT_LIMIT:
        e["_needs_trim"] = True

    return e

# --- Index rebuilders ---

def rebuild_pattern_index(entries):
    idx = {"version": "normalized", "lastUpdated": "", "stats": {"totalEntries": len(entries), "activeEntries": len(entries)},
           "byCategory": defaultdict(list), "byTag": defaultdict(list),
           "byConfidence": {"high": [], "medium": [], "low": []}, "summaries": {}, "recentIds": [],
           "_schema": {"version": "2.0", "fields": {}}}
    for e in entries:
        eid = e["id"]
        idx["byCategory"][e.get("category", "uncategorized")].append(eid)
        for t in e.get("tags", []):
            idx["byTag"][t].append(eid)
        c = e.get("confidence", 0.5)
        bucket = "high" if c >= 0.7 else "medium" if c >= 0.4 else "low"
        idx["byConfidence"][bucket].append(eid)
        idx["summaries"][eid] = e.get("content", "")[:150]
    idx["recentIds"] = sorted([e["id"] for e in entries], key=lambda x: entries[[ee["id"] for ee in entries].index(x)].get("lastAccessed", "") or "", reverse=True)[:20]
    return dict(idx)

def rebuild_knowledge_index(entries):
    idx = {"version": "normalized", "lastUpdated": "", "stats": {"totalEntries": len(entries), "activeEntries": len(entries), "total": len(entries)},
           "byCategory": defaultdict(list), "byTag": defaultdict(list), "bySource": defaultdict(list),
           "byConfidence": {"high": [], "medium": [], "low": []}, "summaries": {}, "recentIds": [],
           "_schema": {"version": "2.0", "fields": {}}}
    for e in entries:
        eid = e["id"]
        idx["byCategory"][e.get("category", "uncategorized")].append(eid)
        for t in e.get("tags", []):
            idx["byTag"][t].append(eid)
        idx["bySource"][e.get("source", "unknown")].append(eid)
        c = e.get("confidence", 0.5)
        bucket = "high" if c >= 0.7 else "medium" if c >= 0.4 else "low"
        idx["byConfidence"][bucket].append(eid)
        idx["summaries"][eid] = e.get("content", "")[:150]
    idx["recentIds"] = sorted([e["id"] for e in entries], key=lambda x: entries[[ee["id"] for ee in entries].index(x)].get("lastAccessed", "") or "", reverse=True)[:20]
    return dict(idx)

def rebuild_reasoning_index(entries):
    idx = {"version": "normalized", "lastUpdated": "", "stats": {"totalEntries": len(entries), "activeEntries": len(entries), "total": len(entries)},
           "byCategory": defaultdict(list), "byTag": defaultdict(list),
           "byConfidence": {"high": [], "medium": [], "low": []},
           "byType": defaultdict(list), "byProvenance": defaultdict(list),
           "summaries": {}, "intents": {}, "recentIds": [],
           "_schema": {"version": "2.0", "fields": {}}}
    for e in entries:
        eid = e["id"]
        for t in e.get("tags", []):
            idx["byTag"][t].append(eid)
        c = e.get("confidence", 0.5)
        bucket = "high" if c >= 0.7 else "medium" if c >= 0.4 else "low"
        idx["byConfidence"][bucket].append(eid)
        idx["byType"][e.get("type", "uncategorized")].append(eid)
        idx["byProvenance"][e.get("provenance", "stated")].append(eid)
        idx["summaries"][eid] = e.get("reuse_signal", "")[:150]
        idx["intents"][eid] = e.get("intent", "")[:150]
    idx["recentIds"] = sorted([e["id"] for e in entries], key=lambda x: entries[[ee["id"] for ee in entries].index(x)].get("lastAccessed", "") or "", reverse=True)[:20]
    return dict(idx)

# --- Review queue generator ---

def generate_review_queue(all_reviews):
    lines = ["# Migration Review Queue\n", "Generated by normalize-schemas.py. Classify these entries manually.\n"]
    for store, items in all_reviews.items():
        if items:
            lines.append(f"\n## {store}\n")
            for eid, reason in items:
                lines.append(f"- **{eid}**: {reason}")
    return "\n".join(lines) + "\n"

# --- Main ---

def main():
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-05:00")

    stores = [
        ("patterns.json", "patterns-index.json", migrate_pattern, rebuild_pattern_index, "patterns"),
        ("knowledge.json", "knowledge-index.json", migrate_knowledge, rebuild_knowledge_index, "knowledge"),
        ("reasoning.json", "reasoning-index.json", migrate_reasoning, rebuild_reasoning_index, "reasoning"),
    ]

    all_reviews = {}
    total_stats = {"modified": 0, "skipped": 0}

    for data_file, index_file, migrator, indexer, name in stores:
        filepath = os.path.join(KB_DIR, data_file)
        with open(filepath) as f:
            data = json.load(f)

        original_count = len(data["entries"])
        stats = defaultdict(int)
        stats["review"] = []
        migrated = []

        for entry in data["entries"]:
            result = migrator(entry, stats)
            if result is None:
                stats["skipped"] += 1
            else:
                migrated.append(result)

        # Validate: no entries lost
        assert len(migrated) + stats["skipped"] == original_count, \
            f"{name}: entry count mismatch! {len(migrated)}+{stats['skipped']} != {original_count}"

        # Build index
        index = indexer(migrated)
        index["lastUpdated"] = now

        # Write
        norm_path = os.path.join(KB_DIR, data_file.replace(".json", ".normalized.json"))
        norm_idx_path = os.path.join(KB_DIR, index_file.replace(".json", ".normalized.json"))

        if DRY_RUN:
            print(f"\n[DRY RUN] {name}: {original_count} entries → {len(migrated)} migrated, {stats['skipped']} skipped")
        else:
            # Write normalized first
            with open(norm_path, "w") as f:
                json.dump({"version": data.get("version", "1.0"), "lastUpdated": now, "entries": migrated}, f, indent=4, ensure_ascii=False)
            # Validate normalized file
            with open(norm_path) as f:
                check = json.load(f)
            assert len(check["entries"]) == len(migrated), f"{name}: normalized file entry count mismatch"
            assert all("content" in e for e in check["entries"]), f"{name}: normalized file has entries without content"
            # Overwrite original
            os.replace(norm_path, filepath)
            # Write index
            with open(norm_idx_path, "w") as f:
                json.dump(index, f, indent=4, ensure_ascii=False)
            os.replace(norm_idx_path, os.path.join(KB_DIR, index_file))

        all_reviews[name] = stats["review"]
        total_stats["modified"] += len(migrated)
        total_stats["skipped"] += stats["skipped"]

        print(f"\n{'[DRY RUN] ' if DRY_RUN else ''}{name}:")
        print(f"  Entries: {original_count} → {len(migrated)}")
        for k, v in sorted(stats.items()):
            if k == "review":
                print(f"  Needs review: {len(v)}")
            elif isinstance(v, int) and v > 0:
                print(f"  {k}: {v}")

    # Generate review queue
    review_content = generate_review_queue(all_reviews)
    review_path = os.path.join(SCRIPTS_DIR, "migration-review-queue.md")
    if not DRY_RUN:
        with open(review_path, "w") as f:
            f.write(review_content)
        print(f"\nReview queue: {review_path}")

    total_reviews = sum(len(v) for v in all_reviews.values())
    print(f"\n{'[DRY RUN] ' if DRY_RUN else ''}TOTAL: {total_stats['modified']} migrated, {total_stats['skipped']} skipped, {total_reviews} need review")

    if DRY_RUN:
        print("\nDry run complete. No files modified.")


if __name__ == "__main__":
    main()
