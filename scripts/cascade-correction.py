#!/usr/bin/env python3
"""
Cascade Correction Script - Find and fix stale claims across all stores.

Two modes:
  scan:  Find entries matching keywords, return matches for review
  apply: Apply approved fixes (literal find-replace)

Usage:
  python3 scripts/cascade-correction.py ops.json

Exit codes: 0 = success, 1 = partial, 2 = total failure
"""

import json, sys, os, re
from pathlib import Path

try:
    import fcntl
except ImportError:
    print("ERROR: fcntl not available. Run via: wsl python3 scripts/cascade-correction.py <ops_file>", file=sys.stderr)
    sys.exit(2)

# Reuse utilities from save-session
sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module
save_mod = import_module("save-session")

SEARCH_FIELDS = ("content", "source", "context", "tags")
STORE_NAMES = ("patterns", "knowledge", "reasoning")


def validate_ops(ops):
    errors = []
    if not isinstance(ops, dict):
        return ["Ops must be a JSON object"]
    if "old_keywords" not in ops or not ops["old_keywords"]:
        errors.append("old_keywords is required and must be non-empty")
    elif not isinstance(ops["old_keywords"], list):
        errors.append("old_keywords must be a list of strings")
    if "mode" not in ops:
        errors.append("mode is required (scan or apply)")
    elif ops["mode"] not in ("scan", "apply"):
        errors.append(f"Invalid mode: {ops['mode']} (must be scan or apply)")
    if ops.get("mode") == "apply":
        if "new_value" not in ops:
            errors.append("new_value is required for apply mode")
        if "approved_ids" not in ops or not ops["approved_ids"]:
            errors.append("approved_ids is required for apply mode")
    return errors


def scan_stores(kb, keywords, stores, limit=10):
    """Scan stores for entries matching any keyword. Returns matches."""
    matches = []
    total = 0
    seen_ids = set()

    for store_name in stores:
        if store_name not in STORE_NAMES:
            continue
        path = kb / "Intelligence" / f"{store_name}.json"
        data = save_mod.load_json(path)
        if data is None:
            continue

        for entry in data.get("entries", []):
            eid = entry.get("id", "")
            matched_fields = []

            for field in SEARCH_FIELDS:
                value = entry.get(field, "")
                if isinstance(value, list):
                    value_str = " ".join(str(v) for v in value)
                else:
                    value_str = str(value)

                for kw in keywords:
                    if kw.lower() in value_str.lower():
                        matched_fields.append(field if not isinstance(entry.get(field), list) else "tags")
                        break

            if matched_fields:
                total += 1
                entry_key = f"{store_name}:{eid}"
                if entry_key not in seen_ids and len(matches) < limit:
                    seen_ids.add(entry_key)
                    # Build snippet from first matched field
                    first_field = matched_fields[0]
                    value = entry.get(first_field, "")
                    if isinstance(value, list):
                        value_str = " ".join(str(v) for v in value)
                    else:
                        value_str = str(value)
                    idx = value_str.lower().find(keywords[0].lower())
                    start = max(0, idx - 40)
                    end = min(len(value_str), idx + len(keywords[0]) + 40)
                    snippet = value_str[start:end]
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(value_str):
                        snippet = snippet + "..."

                    matches.append({
                        "id": eid,
                        "store": store_name,
                        "fields": matched_fields,
                        "snippet": snippet,
                    })
    return matches, total


def apply_fixes(kb, keywords, new_value, approved_ids, stores):
    """Apply literal find-replace for approved entries."""
    applied = 0
    skipped = 0
    affected_stores = set()
    id_set = set(approved_ids)

    for store_name in stores:
        if store_name not in STORE_NAMES:
            continue
        path = kb / "Intelligence" / f"{store_name}.json"
        data = save_mod.load_json(path)
        if data is None:
            continue

        changed = False
        for entry in data.get("entries", []):
            if entry.get("id") not in id_set:
                continue

            entry_changed = False
            for field in SEARCH_FIELDS:
                value = entry.get(field)
                if value is None:
                    continue

                if isinstance(value, list):
                    new_list = []
                    for item in value:
                        new_item = item
                        for kw in keywords:
                            if kw.lower() in str(new_item).lower():
                                new_item = re.sub(re.escape(kw), new_value, str(new_item), flags=re.IGNORECASE)
                                entry_changed = True
                        new_list.append(new_item)
                    entry[field] = new_list
                else:
                    for kw in keywords:
                        if kw.lower() in value.lower():
                            entry[field] = re.sub(re.escape(kw), new_value, value, flags=re.IGNORECASE)
                            value = entry[field]
                            entry_changed = True

            if entry_changed:
                entry["lastAccessed"] = save_mod.get_today()
                applied += 1
                changed = True
                affected_stores.add(store_name)
            else:
                skipped += 1

        if changed:
            data["lastUpdated"] = save_mod.get_today()
            save_mod.save_json(path, data)

    # Rebuild indexes for affected stores
    for store_name in affected_stores:
        save_mod.rebuild_index(kb, store_name)

    return applied, skipped, list(affected_stores)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/cascade-correction.py OPS_FILE")
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
    keywords = ops["old_keywords"]
    stores = ops.get("stores", list(STORE_NAMES))
    mode = ops["mode"]

    lock_path = kb / "Intelligence" / "stores"
    try:
        with save_mod.FileLock(lock_path):
            if mode == "scan":
                limit = ops.get("limit", 10)
                matches, total = scan_stores(kb, keywords, stores, limit)
                result = {"matches": matches, "count": len(matches), "total": total, "EXIT": 0}
                print(json.dumps(result, indent=2))

            elif mode == "apply":
                new_value = ops["new_value"]
                approved = ops["approved_ids"]
                applied, skipped, rebuilt = apply_fixes(kb, keywords, new_value, approved, stores)
                result = {
                    "applied": applied, "skipped": skipped,
                    "indexes_rebuilt": rebuilt,
                    "succeeded": rebuilt, "failed": [],
                    "EXIT": 0
                }
                print(json.dumps(result, indent=2))
                # Clean up ops file on success
                try:
                    os.remove(sys.argv[1])
                except OSError:
                    pass

    except TimeoutError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
