#!/usr/bin/env python3
"""
Save Session Script - Atomic JSON operations for the Nathaniel Protocol.

Handles all JSON store and index mutations during save. Nate writes an ops file,
this script executes all mechanical operations atomically.

Usage: python3 scripts/save-session.py _save_ops_{session_id}.json
       python3 scripts/save-session.py --dry-run _save_ops_{session_id}.json

Exit codes: 0 = success, 1 = partial (some stores written), 2 = total failure

OPS FILE SCHEMA:
  Required:
    session_id: str              # "session-YYYY-MM-DD-NNN"

  Session index (pick one):
    session_index_entry: {id, date, tags, summary, outcome, outcome_note}
    OR flat: session_tags, session_summary, outcome, outcome_note

  New entries (pick one format):
    new_patterns: [...]          # Flat format (preferred)
    new_knowledge: [...]
    new_reasoning: [...]
    OR new_entries: {patterns: [...], knowledge: [...], reasoning: [...]}

  Access tracking:
    reasoning_access: [str]      # Entry IDs accessed this session

  Memory:
    memory_updates: {
      version_bump: str,
      capture_taxonomy_increments: {category: count, ...}
    }
    active_project_updates: [{name, ...}]
    new_commitments: [{...}]
    resolved_commitments: [str]
    snapshot: {}                 # If present, auto-generates snapshot from store counts

  Options:
    vectorstore_sync: bool       # Default true

  WRONG FORMAT (will warn):
    patterns: {new: [...]}       # Use new_patterns instead
    knowledge: {new: [...]}      # Use new_knowledge instead
    reasoning: {new: [...]}      # Use new_reasoning instead
"""

import json, sys, os, subprocess, datetime, re
from pathlib import Path

try:
    import fcntl
except ImportError:
    print("ERROR: fcntl not available. This script requires POSIX (Linux/macOS/WSL).", file=sys.stderr)
    print("On Windows, run via: wsl python3 scripts/save-session.py <ops_file>", file=sys.stderr)
    sys.exit(2)

# ─── Schema Constants ─────────────────────────────────────────────────────

PATTERN_CATEGORIES = {"preference", "approach", "failure", "process", "procedure", "ai_agent"}
KNOWLEDGE_CATEGORIES = {"technical", "process", "error_solution", "best_practice", "tool_quirk",
                        "reference", "domain_expertise", "architecture", "research", "security", "system"}
REASONING_TYPES = {"deduction", "induction", "analogy", "causal", "meta-process", "insight",
                   "architectural_decision", "failure_analysis"}
REASONING_PROVENANCES = {"stated", "synthesized", "cross_session"}
CONTENT_LIMITS = {"patterns": 400, "knowledge": 600, "reasoning": 700}
REQUIRED_FIELDS = {
    "patterns": {"id", "category", "content", "confidence", "tags"},
    "knowledge": {"id", "category", "content", "confidence", "tags"},
    "reasoning": {"id", "type", "content", "intent", "reuse_signal", "confidence", "tags", "provenance", "derived_from"},
}
ID_PATTERNS = {
    "patterns": re.compile(r'^[a-z_]+_\d+$'),
    "knowledge": re.compile(r'^know-\d+$'),
    "reasoning": re.compile(r'^reason-\d+$'),
}

DRY_RUN = False


# ─── Utilities ────────────────────────────────────────────────────────────

def find_kb_root():
    script_dir = Path(__file__).resolve().parent
    kb_path = script_dir.parent / "Nate's-kb"
    if kb_path.exists():
        return kb_path
    print(f"ERROR: Nate's-kb not found at {kb_path}", file=sys.stderr)
    sys.exit(2)


def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"  WARN: File not found: {path}")
        return None
    except json.JSONDecodeError as e:
        print(f"  ERROR: Invalid JSON in {path}: {e}", file=sys.stderr)
        return None


def save_json(path, data):
    if DRY_RUN:
        print(f"  [DRY-RUN] Would write {path}")
        return True
    tmp = str(path) + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')
        os.replace(tmp, path)
        return True
    except Exception as e:
        print(f"  ERROR: Failed to write {path}: {e}", file=sys.stderr)
        if os.path.exists(tmp):
            os.remove(tmp)
        return False


def get_today():
    return datetime.date.today().isoformat()


class FileLock:
    """fcntl-based file lock. Context manager."""
    def __init__(self, path, timeout=30):
        self.path = str(path) + '.lock'
        self.timeout = timeout
        self.fd = None

    def __enter__(self):
        self.fd = open(self.path, 'w')
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"  Lock held on {self.path}, waiting up to {self.timeout}s...")
            import time
            start = time.time()
            while time.time() - start < self.timeout:
                try:
                    fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return self
                except BlockingIOError:
                    time.sleep(0.5)
            raise TimeoutError(f"Could not acquire lock on {self.path} within {self.timeout}s")
        return self

    def __exit__(self, *args):
        if self.fd:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            self.fd.close()
            try:
                os.remove(self.path)
            except OSError:
                pass


# ─── Input Validation ─────────────────────────────────────────────────────

def validate_ops(ops):
    """Validate ops file against schema. Returns list of errors."""
    errors = []

    if not isinstance(ops, dict):
        return ["Ops file must be a JSON object"]

    if "session_id" not in ops:
        errors.append("Missing required field: session_id")
    elif not re.match(r'^session-\d{4}-\d{2}-\d{2}-\d{3}$', ops["session_id"]):
        errors.append(f"Invalid session_id format: {ops['session_id']} (expected session-YYYY-MM-DD-NNN)")

    sv = ops.get("schema_version")
    if sv is not None and sv != 1:
        errors.append(f"Unsupported schema_version: {sv}")

    # Detect unrecognized store-like keys (common format mistake)
    recognized_keys = {
        "session_id", "schema_version", "session_index_entry",
        "new_patterns", "new_knowledge", "new_reasoning", "new_entries",
        "access_updates", "reasoning_access",
        "session_tags", "session_summary", "outcome", "outcome_note",
        "memory_updates", "active_project_updates",
        "new_commitments", "resolved_commitments",
        "taxonomy_hits", "snapshot", "cross_session_synthesis_done",
        "vectorstore_sync",
    }
    store_names = {"patterns", "knowledge", "reasoning"}
    for key in ops:
        if key not in recognized_keys and key in store_names:
            nested = ops[key]
            if isinstance(nested, dict) and ("new" in nested or "access" in nested):
                errors.append(
                    f"WARNING: '{key}.new' format not supported. "
                    f"Use 'new_{key}' (flat) or 'new_entries.{key}' (nested). "
                    f"Entries under '{key}' will be SILENTLY SKIPPED."
                )

    # Validate new entries
    for store_name in ("patterns", "knowledge", "reasoning"):
        key = f"new_{store_name}" if f"new_{store_name}" in ops else None
        entries_key = None
        if key:
            entries_key = key
        elif "new_entries" in ops and store_name in ops["new_entries"]:
            entries_key = f"new_entries.{store_name}"

        entries = ops.get(f"new_{store_name}", [])
        if not entries and "new_entries" in ops:
            entries = ops.get("new_entries", {}).get(store_name, [])

        for i, entry in enumerate(entries):
            prefix = f"{store_name}[{i}]"
            errors.extend(validate_entry(entry, store_name, prefix))

    return errors


def validate_entry(entry, store_name, prefix):
    """Validate a single entry against its store schema."""
    errors = []
    required = REQUIRED_FIELDS.get(store_name, set())

    for field in required:
        if field not in entry:
            errors.append(f"{prefix}: missing required field '{field}'")

    eid = entry.get("id", "")
    pattern = ID_PATTERNS.get(store_name)
    if eid and pattern and not pattern.match(eid):
        errors.append(f"{prefix}: invalid ID format '{eid}'")

    conf = entry.get("confidence")
    if conf is not None and (not isinstance(conf, (int, float)) or conf < 0.0 or conf > 1.0):
        errors.append(f"{prefix}: confidence must be float 0.0-1.0, got {conf}")

    tags = entry.get("tags")
    if tags is not None and not isinstance(tags, list):
        errors.append(f"{prefix}: tags must be a list")

    content = entry.get("content", "")
    limit = CONTENT_LIMITS.get(store_name, 999)
    if len(content) > limit:
        errors.append(f"{prefix}: content length {len(content)} exceeds soft limit {limit} (warning)")

    if store_name == "patterns":
        cat = entry.get("category")
        if cat and cat not in PATTERN_CATEGORIES:
            errors.append(f"{prefix}: invalid category '{cat}' (valid: {PATTERN_CATEGORIES})")

    elif store_name == "knowledge":
        cat = entry.get("category")
        if cat and cat not in KNOWLEDGE_CATEGORIES:
            errors.append(f"{prefix}: invalid category '{cat}' (valid: {KNOWLEDGE_CATEGORIES})")

    elif store_name == "reasoning":
        rtype = entry.get("type")
        if rtype and rtype not in REASONING_TYPES:
            errors.append(f"{prefix}: invalid type '{rtype}' (valid: {REASONING_TYPES})")
        prov = entry.get("provenance")
        if prov and prov not in REASONING_PROVENANCES:
            errors.append(f"{prefix}: invalid provenance '{prov}' (valid: {REASONING_PROVENANCES})")
        df = entry.get("derived_from")
        if df is not None and not isinstance(df, list):
            errors.append(f"{prefix}: derived_from must be a list")

    return errors


# ─── Store Operations ─────────────────────────────────────────────────────

def get_entries(ops, store_name):
    """Get new entries from ops file, supporting both flat and nested formats."""
    entries = ops.get(f"new_{store_name}", [])
    if not entries and "new_entries" in ops:
        entries = ops.get("new_entries", {}).get(store_name, [])
    return entries


def get_access_ids(ops, store_name):
    """Get access update IDs from ops file."""
    return ops.get("access_updates", {}).get(store_name, [])


def add_entries(kb, store_name, new_entries):
    """Add entries to store. Returns (added_ids, success)."""
    if not new_entries:
        return [], True

    path = kb / "Intelligence" / f"{store_name}.json"
    data = load_json(path)
    if data is None:
        return [], False

    entries = data.get("entries", [])
    existing_ids = {e["id"] for e in entries}
    added = []
    today = get_today()

    for entry in new_entries:
        eid = entry["id"]
        if eid in existing_ids:
            print(f"  COLLISION: {eid} already exists, skipping")
            continue

        entry.setdefault("created", today)
        entry.setdefault("lastAccessed", today)
        entry.setdefault("accessCount", 1)
        if store_name == "reasoning":
            entry.setdefault("provenance", "stated")
            entry.setdefault("derived_from", [])

        entries.append(entry)
        added.append(eid)

    data["entries"] = entries
    data["lastUpdated"] = today

    if save_json(path, data):
        if added:
            print(f"  + {store_name}: {len(added)} added {added}")
        return added, True
    return [], False


def update_access(kb, store_name, entry_ids):
    """Update lastAccessed and accessCount for retrieved entries."""
    if not entry_ids:
        return True

    path = kb / "Intelligence" / f"{store_name}.json"
    data = load_json(path)
    if data is None:
        return False

    today = get_today()
    updated = 0
    id_set = set(entry_ids)

    for entry in data.get("entries", []):
        if entry.get("id") in id_set:
            entry["accessCount"] = entry.get("accessCount", 0) + 1
            entry["lastAccessed"] = today
            updated += 1

    if updated > 0 and save_json(path, data):
        print(f"  ~ {store_name}: {updated} access-tracked")
    return True


def get_max_id_num(entries, prefix):
    """Get highest numeric ID for a prefix."""
    max_num = 0
    for e in entries:
        eid = e.get("id", "")
        if prefix in ("know-", "reason-") and eid.startswith(prefix):
            try:
                max_num = max(max_num, int(eid.split("-")[1]))
            except (ValueError, IndexError):
                pass
        elif "_" in eid:
            parts = eid.rsplit("_", 1)
            if len(parts) == 2 and parts[0] == prefix:
                try:
                    max_num = max(max_num, int(parts[1]))
                except ValueError:
                    pass
    return max_num


def rebuild_index(kb, store_name):
    """Full index rebuild from store. Idempotent."""
    store_path = kb / "Intelligence" / f"{store_name}.json"
    index_path = kb / "Intelligence" / f"{store_name}-index.json"

    store_data = load_json(store_path)
    if store_data is None:
        return False

    entries = store_data.get("entries", [])
    old_index = load_json(index_path) or {}
    old_recent = old_index.get("recentIds", [])

    idx = {"stats": {}, "byTag": {}, "summaries": {}, "recentIds": old_recent[:20]}

    if store_name == "patterns":
        idx["byCategory"] = {}
        idx["byConfidence"] = {"high": [], "medium": [], "low": []}
    elif store_name == "knowledge":
        idx["byCategory"] = {}
    elif store_name == "reasoning":
        idx["byType"] = {}
        idx["byConfidence"] = {"high": [], "medium": [], "low": []}
        idx["byProvenance"] = {"stated": [], "synthesized": [], "cross_session": []}
        idx["intents"] = {}

    for entry in entries:
        eid = entry.get("id", "")
        confidence = entry.get("confidence", 0.5)

        if store_name == "reasoning":
            idx["summaries"][eid] = entry.get("reuse_signal", entry.get("content", "")[:150])
        else:
            idx["summaries"][eid] = entry.get("content", "")[:150]

        for tag in entry.get("tags", []):
            idx["byTag"].setdefault(tag, []).append(eid)

        if "byConfidence" in idx:
            bucket = "high" if confidence >= 0.8 else "medium" if confidence >= 0.5 else "low"
            idx["byConfidence"][bucket].append(eid)

        if "byCategory" in idx:
            idx["byCategory"].setdefault(entry.get("category", "uncategorized"), []).append(eid)

        if "byType" in idx:
            idx["byType"].setdefault(entry.get("type", "deduction"), []).append(eid)

        if "byProvenance" in idx:
            idx["byProvenance"].setdefault(entry.get("provenance", "stated"), []).append(eid)

        if "intents" in idx and entry.get("intent"):
            idx["intents"][eid] = entry["intent"]

    total = len(entries)
    idx["stats"]["totalEntries"] = total
    idx["stats"]["activeEntries"] = total

    if store_name == "patterns":
        next_ids = {}
        for e in entries:
            eid = e.get("id", "")
            if "_" in eid:
                parts = eid.rsplit("_", 1)
                try:
                    next_ids[parts[0]] = max(next_ids.get(parts[0], 0), int(parts[1]) + 1)
                except ValueError:
                    pass
        idx["stats"]["nextId"] = next_ids
    elif store_name == "knowledge":
        idx["stats"]["nextId"] = get_max_id_num(entries, "know-") + 1
    elif store_name == "reasoning":
        idx["stats"]["nextId"] = get_max_id_num(entries, "reason-") + 1

    if save_json(index_path, idx):
        print(f"  ✓ {store_name}-index: {total} entries")
        return True
    return False


# ─── Session Index, Memory, Cross-Refs, Vectorstore ──────────────────────

def update_session_index(kb, ops):
    path = kb / "Memory" / "session-index.json"
    idx = load_json(path) or {"sessions": [], "recentIds": []}
    sid = ops["session_id"]

    if any(s.get("id") == sid for s in idx.get("sessions", [])):
        print(f"  Session {sid} already in index")
        return True

    # Support both flat keys and nested session_index_entry format
    sie = ops.get("session_index_entry", {})
    idx["sessions"].insert(0, {
        "id": sid, "date": get_today(),
        "tags": sie.get("tags", ops.get("session_tags", [])),
        "summary": sie.get("summary", ops.get("session_summary", "")),
        "outcome": sie.get("outcome", ops.get("outcome", "success")),
        "outcome_note": sie.get("outcome_note", ops.get("outcome_note", ""))
    })
    idx.setdefault("recentIds", []).insert(0, sid)
    idx["recentIds"] = idx["recentIds"][:20]

    if save_json(path, idx):
        print(f"  ✓ Session index: {sid}")
        # Touch sentinel for session-cache invalidation
        sentinel = kb / "Memory" / "cache" / ".invalidated"
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.touch()
        return True
    return False


def update_memory(kb, ops):
    path = kb / "Memory" / "memory.json"
    mem = load_json(path)
    if mem is None:
        return False

    today = get_today()
    changed = False

    for key, value in ops.get("memory_updates", {}).items():
        if key == "version_bump":
            mem["version"] = value
        elif key == "capture_taxonomy_increments":
            pass  # Handled by taxonomy_hits section below
        elif key == "domain_expertise" and isinstance(value, dict):
            mem.setdefault("domain_expertise", {}).update(value)
        elif key == "anti_preferences" and isinstance(value, dict):
            mem.setdefault("anti_preferences", {}).update(value)
        elif key == "last_session_snapshot" and isinstance(value, dict):
            mem["last_session_snapshot"] = value
        else:
            mem[key] = value
        changed = True

    for update in ops.get("active_project_updates", []):
        projects = mem.setdefault("active_projects", [])
        existing = next((p for p in projects if p.get("name") == update.get("name")), None)
        if existing:
            existing.update(update)
        else:
            projects.append(update)
        changed = True

    for c in ops.get("new_commitments", []):
        mem.setdefault("commitments", []).append(c)
        changed = True
    for cid in ops.get("resolved_commitments", []):
        for c in mem.get("commitments", []):
            if c.get("id") == cid:
                c["status"] = "resolved"
                c["resolved_date"] = today
                changed = True

    snapshot = ops.get("snapshot", {})
    if snapshot:
        stores = {}
        for s in ("patterns", "knowledge", "reasoning"):
            d = load_json(kb / "Intelligence" / f"{s}.json")
            stores[s] = len(d.get("entries", [])) if d else 0
        mem["last_session_snapshot"] = {
            "session_id": ops["session_id"],
            "memory_version": mem.get("version", "unknown"),
            "patterns_count": stores["patterns"],
            "knowledge_count": stores["knowledge"],
            "reasoning_count": stores["reasoning"],
            "active_projects": len([p for p in mem.get("active_projects", [])
                                    if isinstance(p, dict) and p.get("status") == "active"]),
            "timestamp": datetime.datetime.now().isoformat()
        }
        changed = True

    hits = ops.get("taxonomy_hits", {})
    # Also support list format from memory_updates.capture_taxonomy_increments
    cti = ops.get("memory_updates", {}).get("capture_taxonomy_increments", [])
    if cti and not hits:
        hits = {cat: 1 for cat in cti} if isinstance(cti, list) else cti
    if hits:
        ct = mem.setdefault("capture_taxonomy", {"sessions_tracked": 0, "category_hits": {}})
        ct["sessions_tracked"] = ct.get("sessions_tracked", 0) + 1
        for cat, count in hits.items():
            ct["category_hits"][cat] = ct["category_hits"].get(cat, 0) + count
        changed = True

    if ops.get("cross_session_synthesis_done"):
        mem["last_cross_session_synthesis"] = ops["session_id"]
        changed = True

    if changed:
        mem["lastUpdated"] = today
        if save_json(path, mem):
            print(f"  ✓ Memory updated")
            return True
    return True


def update_cross_references(kb, new_reasoning):
    if not new_reasoning:
        return
    path = kb / "Intelligence" / "cross-references.json"
    xref = load_json(path) or {}

    # Detect format: wrapped (has "references" key) or flat (entry IDs at top level)
    if "references" in xref:
        refs = xref["references"]
        wrapped = True
    else:
        refs = xref
        wrapped = False

    added = 0
    for entry in new_reasoning:
        rid = entry.get("id", "")
        for source_id in entry.get("derived_from", []):
            if source_id.startswith("session-"):
                continue
            refs.setdefault(source_id, {"referenced_by": [], "related_to": []})
            if rid not in refs[source_id]["referenced_by"]:
                refs[source_id]["referenced_by"].append(rid)
                added += 1

    if wrapped:
        xref["references"] = refs
        xref.setdefault("_meta", {})["last_updated"] = get_today()
        xref["stats"] = {"total_sources": len(refs),
                         "total_references": sum(len(v.get("referenced_by", [])) for v in refs.values() if isinstance(v, dict))}
    # flat format: refs IS xref, already mutated

    if save_json(path, xref) and added:
        print(f"  ✓ Cross-refs: {added} added")


def file_structure_check(kb):
    """Detect new/deleted/moved files via git and scan stores for stale path references."""
    repo_root = kb.parent
    alerts = []

    # Get git status for new/deleted/renamed files
    try:
        result = subprocess.run(
            ["git", "status", "--short"], capture_output=True, text=True, cwd=repo_root
        )
        if result.returncode != 0:
            print("  Skip: git status failed")
            return alerts
    except FileNotFoundError:
        print("  Skip: git not found")
        return alerts

    deleted_paths = []
    renamed_paths = []  # (old, new) tuples
    new_paths = []

    for line in result.stdout.strip().splitlines():
        if len(line) < 3:
            continue
        # Git status format: XY PATH or XY -> PATH for renames
        # Split on first whitespace after status columns
        parts = line.lstrip().split(None, 1)
        if len(parts) < 2:
            continue
        status = parts[0]
        path = parts[1].strip()
        # Skip temp files, build artifacts, ops files
        if any(path.startswith(p) for p in ("node_modules/", ".aws-sam/", "__pycache__/")):
            continue
        if path.startswith("_save_ops") or path.endswith(".pyc"):
            continue

        if "D" in status and "?" not in status:
            deleted_paths.append(path)
        elif "R" in status:
            if " -> " in path:
                old, new = path.split(" -> ", 1)
                renamed_paths.append((old.strip(), new.strip()))
        elif status in ("A", "?", "??"):
            new_paths.append(path)

    # Scan stores for references to deleted/renamed-from paths
    stale_refs = []
    check_paths = deleted_paths + [old for old, _ in renamed_paths]

    if check_paths:
        for store_name in ("knowledge", "reasoning"):
            store_path = kb / "Intelligence" / f"{store_name}.json"
            if not store_path.exists():
                continue
            try:
                data = json.loads(store_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            entries = data.get("entries", [])
            for entry in entries:
                content = entry.get("content", "") + " " + entry.get("source", "")
                for cp in check_paths:
                    if cp in content:
                        stale_refs.append({"entry": entry["id"], "store": store_name, "path": cp})

    # Build output
    if new_paths:
        alerts.append(f"  New files ({len(new_paths)}):")
        for p in new_paths[:10]:
            alerts.append(f"    + {p}")
        if len(new_paths) > 10:
            alerts.append(f"    ... and {len(new_paths) - 10} more")

    if deleted_paths:
        alerts.append(f"  Deleted files ({len(deleted_paths)}):")
        for p in deleted_paths[:10]:
            alerts.append(f"    - {p}")

    if renamed_paths:
        alerts.append(f"  Renamed files ({len(renamed_paths)}):")
        for old, new in renamed_paths[:10]:
            alerts.append(f"    {old} → {new}")

    if stale_refs:
        alerts.append(f"  ⚠ STALE REFERENCES ({len(stale_refs)}):")
        for ref in stale_refs:
            alerts.append(f"    {ref['entry']} ({ref['store']}): references \"{ref['path']}\"")

    if alerts:
        alerts.insert(0, "  Action needed: review FILE-STRUCTURE.md" +
                      (f", fix {len(stale_refs)} stale reference(s)" if stale_refs else ""))

    return alerts


def prune_check(kb):
    """Intelligence stores grow indefinitely — CSR indexes keep query cost constant.
    No size caps. Stale entries (accessCount=0, age > 3 years) flagged by maintenance.py."""
    for store in ("patterns", "knowledge", "reasoning"):
        data = load_json(kb / "Intelligence" / f"{store}.json")
        if data:
            print(f"  ✓ {store}: {len(data.get('entries', []))} entries (no cap)")


def vectorstore_sync(kb):
    config = kb / "vectorstore" / "config.json"
    if not config.exists():
        print("  - Vectorstore not configured")
        return True
    sync_script = kb / "vectorstore" / "kb_sync.py"
    if not sync_script.exists():
        print("  - kb_sync.py not found")
        return True
    if DRY_RUN:
        print("  [DRY-RUN] Would sync vectorstore")
        return True

    venv_py = kb / "vectorstore" / ".venv" / "bin" / "python3"
    cmd = str(venv_py) if venv_py.exists() else "python3"
    try:
        result = subprocess.run([cmd, str(sync_script)], cwd=str(kb),
                                capture_output=True, text=True, timeout=120)
        for line in result.stdout.strip().split('\n'):
            if 'Synced:' in line or 'Built' in line:
                print(f"  ✓ {line.strip()}")
                return True
        if result.returncode == 0:
            print("  ✓ Vectorstore synced")
            return True
        print(f"  ⚠ Sync failed: {result.stderr[:200]}")
        return False
    except subprocess.TimeoutExpired:
        print("  ⚠ Sync timed out (120s)")
        return False
    except FileNotFoundError:
        print(f"  ⚠ Python not found: {cmd}")
        return False


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    global DRY_RUN

    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]
    DRY_RUN = '--dry-run' in flags

    if not args:
        print("Usage: python3 scripts/save-session.py [--dry-run] OPS_FILE")
        sys.exit(2)

    ops_file = args[0]
    ops = load_json(ops_file)
    if ops is None:
        print(f"ERROR: Could not load {ops_file}", file=sys.stderr)
        sys.exit(2)

    # Validate
    errors = validate_ops(ops)
    hard_errors = [e for e in errors if "warning" not in e.lower()]
    warnings = [e for e in errors if "warning" in e.lower()]

    for w in warnings:
        print(f"  WARN: {w}")
    if hard_errors:
        for e in hard_errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        print(f"\nValidation failed: {len(hard_errors)} error(s). Aborting.", file=sys.stderr)
        sys.exit(2)

    session_id = ops["session_id"]
    kb = find_kb_root()
    succeeded = []
    failed = []

    if DRY_RUN:
        print(f"═══ DRY RUN: {session_id} ═══")
    else:
        print(f"═══ Save: {session_id} ═══")
    print(f"  KB: {kb}")
    print()

    # Acquire lock on intelligence directory
    lock_path = kb / "Intelligence" / "stores"
    try:
        with FileLock(lock_path):
            # Session index
            print("Session Index")
            if update_session_index(kb, ops):
                succeeded.append("session_index")
            else:
                failed.append("session_index")
            print()

            # Intelligence stores
            for store_name in ("patterns", "knowledge", "reasoning"):
                print(f"{store_name.title()}")
                new = get_entries(ops, store_name)
                access = get_access_ids(ops, store_name)

                added, ok = add_entries(kb, store_name, new)
                if not ok:
                    failed.append(store_name)
                    print()
                    continue

                update_access(kb, store_name, access)
                rebuild_index(kb, store_name)
                succeeded.append(store_name)
                print()

            # Cross-references
            new_r = get_entries(ops, "reasoning")
            if new_r:
                print("Cross-References")
                update_cross_references(kb, new_r)
                print()

            # Memory
            print("Memory")
            if update_memory(kb, ops):
                succeeded.append("memory")
            else:
                failed.append("memory")
            print()

    except TimeoutError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    # Mandatory step enforcement: 3c-CROSS check
    print("Mandatory Step Check")
    mem_path = kb / "Memory" / "memory.json"
    sess_idx_path = kb / "Memory" / "session-index.json"
    mem_data = load_json(mem_path)
    sess_idx = load_json(sess_idx_path)
    if mem_data and sess_idx:
        last_cross = mem_data.get("last_cross_session_synthesis", "")
        sessions = sess_idx.get("sessions", [])
        sessions_since = 0
        for s in sessions:
            if s.get("id") == last_cross:
                break
            sessions_since += 1
        cross_done = ops.get("cross_session_synthesis_done", False)
        has_cross_reasoning = any(
            e.get("provenance") == "cross_session"
            for e in get_entries(ops, "reasoning")
        )
        if sessions_since >= 3 and not cross_done and not has_cross_reasoning:
            print(f"  ⚠ 3c-CROSS is DUE ({sessions_since} sessions since last). Not found in this save.")
            print(f"    Last cross-session synthesis: {last_cross or 'never'}")
            print(f"    This is a mandatory step. Run it before closing the session.")
        else:
            print(f"  ✓ 3c-CROSS: {'done this save' if (cross_done or has_cross_reasoning) else f'not due ({sessions_since} sessions since last)'}")
    else:
        print("  ✓ 3c-CROSS: skipped (memory or session-index not loaded)")
    print()

    # Outside lock: prune + vectorstore
    print("Prune Check")
    prune_check(kb)
    print()

    if ops.get("vectorstore_sync", True):
        print("Vectorstore")
        vectorstore_sync(kb)
        print()

    # File structure check
    print("File Structure Check")
    fs_alerts = file_structure_check(kb)
    if fs_alerts:
        for line in fs_alerts:
            print(line)
    else:
        print("  No new/deleted/moved files detected")
    print()

    # Summary
    print("═══ Result ═══")
    print(f"  Succeeded: {succeeded}")
    if failed:
        print(f"  Failed: {failed}")

    # Exit code and ops file cleanup
    if failed and succeeded:
        print(f"\nEXIT:1 (partial). Ops file preserved for retry.")
        sys.exit(1)
    elif failed:
        print(f"\nEXIT:2 (total failure). Ops file preserved.")
        sys.exit(2)
    else:
        if not DRY_RUN:
            try:
                os.remove(ops_file)
            except OSError:
                pass
        print(f"\nEXIT:0. Done.")
        sys.exit(0)


if __name__ == "__main__":
    main()
