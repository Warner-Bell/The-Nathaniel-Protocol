"""Access tracking for vectorstore search hits.

Logs search hits to a sidecar file. Flushed to source stores during kb_sync.
Keeps search path read-only for performance.
"""
import json
import os
from datetime import datetime, timezone

VS_DIR = os.path.dirname(os.path.abspath(__file__))
KB_ROOT = os.path.dirname(VS_DIR)
HITS_FILE = os.path.join(VS_DIR, ".access_hits.json")

STORE_PATHS = {
    "patterns": os.path.join(KB_ROOT, "Intelligence", "patterns.json"),
    "knowledge": os.path.join(KB_ROOT, "Intelligence", "knowledge.json"),
    "reasoning": os.path.join(KB_ROOT, "Intelligence", "reasoning.json"),
}


def log_hits(results: list[dict]):
    """Append search hit IDs to sidecar file. Fast, no store reads."""
    if not results:
        return
    hits = {}
    if os.path.exists(HITS_FILE):
        try:
            with open(HITS_FILE) as f:
                hits = json.load(f)
        except (json.JSONDecodeError, OSError):
            hits = {}

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for r in results:
        eid = r.get("id", "")
        store = r.get("store", "")
        if not eid or not store or store == "memory":
            continue
        key = f"{store}:{eid}"
        if key not in hits:
            hits[key] = {"count": 0, "last": ""}
        hits[key]["count"] += 1
        hits[key]["last"] = today

    with open(HITS_FILE, "w") as f:
        json.dump(hits, f)


def flush_hits() -> dict:
    """Apply accumulated hits to source stores. Called during kb_sync.

    Returns summary of updates applied.
    """
    if not os.path.exists(HITS_FILE):
        return {"flushed": 0}

    with open(HITS_FILE) as f:
        hits = json.load(f)

    if not hits:
        return {"flushed": 0}

    # Group by store
    by_store: dict[str, dict[str, dict]] = {}
    for key, data in hits.items():
        store, eid = key.split(":", 1)
        by_store.setdefault(store, {})[eid] = data

    updated = 0
    for store, entries_hits in by_store.items():
        path = STORE_PATHS.get(store)
        if not path or not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        entries = data.get("entries", [])
        modified = False
        for entry in entries:
            eid = entry.get("id", "")
            if eid in entries_hits:
                hit = entries_hits[eid]
                entry["accessCount"] = entry.get("accessCount", 0) + hit["count"]
                entry["lastAccessed"] = hit["last"]
                modified = True
                updated += 1
        if modified:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    # Clear sidecar after flush
    os.remove(HITS_FILE)
    return {"flushed": updated}
