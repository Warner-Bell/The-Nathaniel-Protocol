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

  Field updates on existing entries:
    entry_updates: {
      knowledge: [{id: str, set: {field: value}, append_tags: [str]}],
      patterns:  [...],
      reasoning: [...]
    }
    # Primary use is supersession: set superseded_by to the ID of the entry that
    # replaces a stale claim. kb_query then excludes it from retrieval while the
    # record survives for historical recall. Prior values land in _history.

  Memory:
    memory_updates: {
      version_bump: str,
      capture_taxonomy_increments: {category: count, ...}
    }
    active_project_updates: [{name, ...}]
                                 # matched on a NORMALIZED name (case, punctuation and
                                 # parenthetical qualifiers ignored), so a name variant
                                 # updates the existing project instead of appending one
    new_commitments: [{...}]     # an entry with no id gets cmt-YYYY-MM-DD-<slug>
    resolved_commitments: [str]
    commitment_updates: [{id|match: str, set: {field: value}}]
                                 # change fields on an existing commitment (redate, re-own).
                                 # Same matching as resolved_commitments: id, else EXACT text
                                 # of what/deliverable/commitment/task. Ambiguous = refused.
    snapshot: {}                 # If present, auto-generates snapshot from store counts

  Options:
    vectorstore_sync: bool       # Default true

  WRONG FORMAT (will warn):
    patterns: {new: [...]}       # Use new_patterns instead
    knowledge: {new: [...]}      # Use new_knowledge instead
    reasoning: {new: [...]}      # Use new_reasoning instead
    any other unknown top-level key  # warned: it would be silently ignored

  This docstring is the schema contract. A key added to recognized_keys in validate_ops()
  must be documented here too (a missing entry once made a save conclude a capability did
  not exist and hand-patch memory.json).
"""

import json
import re as _re, sys, os, subprocess, datetime, re
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
                        "reference", "domain_expertise", "architecture", "research", "security", "system",
                        "tool_behavior", "aws_gotcha", "personal", "financial", "discovery", "negative-knowledge"}
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
        "access_updates", "reasoning_access", "entry_updates",
        "session_tags", "session_summary", "outcome", "outcome_note",
        "memory_updates", "active_project_updates",
        "new_commitments", "resolved_commitments", "memory_remove_keys",
        "new_memories", "commitment_updates",
        "taxonomy_hits", "snapshot", "cross_session_synthesis_done",
        "vectorstore_sync",
        "_acp_candidates",
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
    # Any other unrecognized top-level key is ignored by every writer below, so a claimed
    # capture would vanish while the run still reports success. Underscore keys are
    # comments/metadata by convention and stay quiet.
    for key in ops:
        if key in recognized_keys or key in store_names or str(key).startswith("_"):
            continue
        errors.append(
            f"WARNING: unrecognized ops key '{key}' will be SILENTLY IGNORED. "
            f"See the OPS FILE SCHEMA docstring for the supported keys."
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
        source = entry.get("source", "")
        if not source:
            errors.append(f"{prefix}: missing 'source' field (minimum: session ID)")

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
        elif df:
            # Bare filenames ("build-tenancy.py") are valid provenance but unresolvable:
            # they name no location, and two of them sat as false "no longer exists"
            # flags in maintenance for days (candidate 2026-10-21). Repo-relative paths
            # are the convention 43 of 45 refs already follow. Warn, never abort a save.
            for ref in df:
                if (isinstance(ref, str) and "/" not in ref
                        and not ref.startswith(("session-", "BL-"))
                        and Path(ref.split("#", 1)[0]).suffix):
                    errors.append(f"{prefix}: warning: derived_from '{ref}' is a bare filename; "
                                  f"use a repo-relative path so it resolves")

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


def _bump_version(current):
    """Increment the trailing numeric component, preserving zero-pad width.

    memory.json uses a major.NN form (e.g. 4.01 -> 4.02), not strict semver, so this
    bumps the last run of digits rather than assuming three components.
    """
    s = str(current or "0.00")
    m = _re.match(r"^(.*?)(\d+)$", s)
    if not m:
        return s
    head, num = m.group(1), m.group(2)
    return f"{head}{str(int(num) + 1).zfill(len(num))}"


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
        # POST-WRITE VERIFICATION. Reporting success from save_json's return
        # value alone is how this function "silently no-ops in some runs and succeeds in
        # others": save_json can succeed while the resulting file does not contain the
        # entries, because a non-locking writer (cascade-correction.py, removal-cascade.py,
        # an ad-hoc repair script) can clobber the file between our load and our save.
        # Re-read from disk and prove the IDs landed before claiming success.
        #
        # DRY-RUN EXEMPTION (2026-09-21). save_json returns True under DRY_RUN WITHOUT
        # writing, so this check re-read an unchanged file, found every new entry
        # "missing", and blamed a concurrent clobber that never happened. It also told the
        # reader "do NOT hand-write these entries", inviting either an aborted good save or
        # a pointless manual recovery. That false alarm was captured SIX times without ever
        # being fixed.
        # Verification is only meaningful against a real write.
        if added and not DRY_RUN:
            verify = load_json(path)
            landed = {e.get("id") for e in (verify or {}).get("entries", [])}
            missing = [eid for eid in added if eid not in landed]
            if missing:
                print(f"  ✗ {store_name}: WRITE VERIFICATION FAILED — reported as added but "
                      f"NOT present on disk: {missing}")
                print(f"    Likely a concurrent non-locking writer clobbered the store. "
                      f"Do NOT hand-write these entries until you re-read the file.")
                return [], False
            print(f"  + {store_name}: {len(added)} added {added}")
        elif added:
            print(f"  [DRY-RUN] {store_name}: {len(added)} would be added {added} "
                  f"(write verification skipped, nothing was written)")
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


# Fields an entry_update may mutate. id/created/accessCount are excluded so an
# update can never forge provenance or clobber identity.
MUTABLE_FIELDS = {
    "content", "confidence", "tags", "context", "source", "sourceUrl", "detail",
    "prevention", "outcome", "evidence", "category", "type", "provenance",
    "intent", "reuse_signal", "derived_from", "validated", "validationNote",
    "superseded_by", "superseded_on",
    "_needs_review", "_needs_trim", "_stale_candidate",
}

# Fields an entry_update may never REMOVE via "unset": identity, audit trail, and every
# required field of the store. Anything else (legacy or drifted fields such as trigger,
# related, lastUpdated) can be removed; the removed value is kept in _history.
UNSET_PROTECTED = {"id", "created", "lastAccessed", "accessCount", "_history"}


def _all_intel_ids(kb):
    """Every live entry ID across the three intelligence stores."""
    ids = set()
    for store in ("patterns", "knowledge", "reasoning"):
        data = load_json(kb / "Intelligence" / f"{store}.json")
        if data:
            ids.update(e.get("id") for e in data.get("entries", []))
    return ids


def apply_entry_updates(kb, store_name, updates, valid_ids=None):
    """Mutate fields on existing entries. Returns (updated_count, success).

    Update shape: {"id": "know-0001", "set": {...}, "append_tags": [...], "unset": [...]}

    "unset" removes non-identity, non-required fields (legacy or drifted keys). The
    removed values are recorded in _history like any other change.

    Supersession is the primary use: setting superseded_by marks a claim as
    retired without destroying the record. kb_query excludes superseded entries
    from retrieval, so the stale claim stops competing with its correction while
    remaining available for historical recall.

    Prior values are preserved in the entry's _history list for audit.
    """
    if not updates:
        return 0, True

    path = kb / "Intelligence" / f"{store_name}.json"
    data = load_json(path)
    if data is None:
        return 0, False

    entries = data.get("entries", [])
    by_id = {e.get("id"): e for e in entries}
    today = get_today()
    updated = 0

    for upd in updates:
        eid = upd.get("id")
        entry = by_id.get(eid)
        if entry is None:
            print(f"  MISS: {store_name} {eid} not found, skipping")
            continue

        fields = dict(upd.get("set", {}))

        # Tolerate the flat shape {"id":..., "content":..., "confidence":...} by lifting
        # recognized mutable fields into `set`. Without this the update silently no-ops,
        # because `set` is empty and the "nothing to do" branch below just continues.
        if not fields:
            flat = {k: v for k, v in upd.items()
                    if k in MUTABLE_FIELDS and k not in ("id", "set", "append_tags", "unset")}
            if flat:
                fields = flat
                print(f"  NORMALIZED: {eid} flat fields lifted into 'set' ({', '.join(sorted(flat))})")

        rejected = [k for k in fields if k not in MUTABLE_FIELDS]
        for k in rejected:
            print(f"  REJECT: {eid} field '{k}' is not updatable, skipping field")
            fields.pop(k)

        target = fields.get("superseded_by")
        if target:
            if valid_ids is None:
                valid_ids = _all_intel_ids(kb)
            if target == eid:
                print(f"  REJECT: {eid} cannot supersede itself")
                fields.pop("superseded_by")
            elif target not in valid_ids:
                print(f"  REJECT: {eid} superseded_by '{target}' does not resolve to a live entry")
                fields.pop("superseded_by")
            else:
                fields.setdefault("superseded_on", today)

        append_tags = [t for t in upd.get("append_tags", []) if t not in entry.get("tags", [])]

        protected = UNSET_PROTECTED | REQUIRED_FIELDS.get(store_name, set())
        unset = []
        for k in upd.get("unset", []) or []:
            if k in protected or k in fields:
                print(f"  REJECT: {eid} cannot unset '{k}' (protected or also being set)")
            elif k not in entry:
                print(f"  NOTE: {eid} has no field '{k}' to unset")
            else:
                unset.append(k)

        if not fields and not append_tags and not unset:
            # Fail loud. An update that changes nothing is almost always a malformed ops
            # entry, and silently skipping it makes the save report success while dropping
            # the change (guard-and-continue).
            unknown = [k for k in upd if k not in ("id", "set", "append_tags", "unset")]
            print(f"  WARN: {store_name} {eid} update applies no fields, nothing changed."
                  + (f" Unrecognized keys: {', '.join(sorted(unknown))}."
                     " Mutable fields belong under 'set'." if unknown else ""))
            continue

        before = {k: entry.get(k) for k in list(fields) + unset if k in entry}
        if before:
            entry.setdefault("_history", []).append({"date": today, "was": before})

        entry.update(fields)
        for k in unset:
            entry.pop(k, None)
        if append_tags:
            entry["tags"] = entry.get("tags", []) + append_tags

        changed = sorted(list(fields.keys()) + (["tags"] if append_tags else [])
                         + [f"-{k}" for k in unset])
        print(f"  ~ {eid}: {', '.join(changed)}")
        updated += 1

    if updated == 0:
        return 0, True

    data["entries"] = entries
    data["lastUpdated"] = today

    if save_json(path, data):
        print(f"  ~ {store_name}: {updated} entry field update(s)")
        return updated, True
    return 0, False


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

    idx = {"stats": {}, "byTag": {}, "summaries": {}, "recentIds": []}

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

    # recentIds: newest entries by created date, newest first.
    # Append order breaks ties (new entries are appended, so a higher
    # position in the list is newer). Recomputed every rebuild so the
    # index recency tracks the store instead of freezing at first write.
    ordered = sorted(
        enumerate(entries),
        key=lambda pair: (pair[1].get("created", ""), pair[0]),
    )
    idx["recentIds"] = [e.get("id", "") for _, e in ordered[-20:]][::-1]

    if save_json(index_path, idx):
        print(f"  ✓ {store_name}-index: {total} entries")
        return True
    return False


# ─── Session Index, Memory, Cross-Refs, Vectorstore ──────────────────────

def _session_ids_in_use(kb, date):
    """Every session id already taken for `date`, from BOTH sources.

    The log directory alone is not enough: an entries-only save registers an id in
    the index without ever writing a log (observed 2026-08-05, session-...-017).
    The index alone is not enough either: a log is written at save step 1, before
    the index entry exists at step 2.
    """
    used = set()
    mem = kb / "Memory"
    for p in mem.glob(f"session-{date}-*.md"):
        used.add(p.stem)
    idx = load_json(mem / "session-index.json") or {}
    for s in idx.get("sessions", []):
        sid = s.get("id", "")
        if sid.startswith(f"session-{date}-"):
            used.add(sid)
    return used


def claim_session_id(kb, date=None, max_n=999):
    """Atomically reserve the next free session id for `date`. Returns the id.

    The reservation IS the log file, created with O_EXCL so the filesystem settles
    the race: two processes calling this concurrently cannot receive the same id,
    with or without a lock held. Caller then writes its log content to that path.

    This is the primitive whose absence caused the 2026-08-05 collision: the id was
    chosen minutes before the log was written, leaving a window a concurrent
    instance walked straight into.
    """
    date = date or get_today()
    mem = kb / "Memory"
    mem.mkdir(parents=True, exist_ok=True)
    used = _session_ids_in_use(kb, date)

    # Start at max+1, NOT at the lowest free number. Session ids are chronological, so
    # handing out 001 while 013-018 exist misorders the index and misrepresents when
    # the session happened. Found 2026-08-05 by RUNNING the flag against the real KB:
    # the unit tests all used contiguous ids, so none of them could tell "lowest free"
    # apart from "next after max".
    highest = 0
    prefix = f"session-{date}-"
    for sid in used:
        tail = sid[len(prefix):] if sid.startswith(prefix) else ""
        if tail.isdigit():
            highest = max(highest, int(tail))

    for n in range(highest + 1, max_n + 1):
        sid = f"session-{date}-{n:03d}"
        if sid in used:
            continue
        path = mem / f"{sid}.md"
        try:
            # O_EXCL: fails if another process won the race between our scan and here.
            with open(path, "x", encoding="utf-8") as f:
                f.write(f"# Session {sid}\n")
        except FileExistsError:
            continue
        return sid
    raise RuntimeError(f"no free session id for {date} below {max_n:03d}")


def _session_fingerprint_populated(kb, sid):
    """Re-read session-index.json from disk; True if sid's row has tags or a summary."""
    idx = load_json(kb / "Memory" / "session-index.json") or {}
    row = next((s for s in idx.get("sessions", []) if s.get("id") == sid), None)
    return bool(row and (row.get("tags") or row.get("summary")))


def update_session_index(kb, ops):
    path = kb / "Memory" / "session-index.json"
    idx = load_json(path) or {"sessions": [], "recentIds": []}
    sid = ops["session_id"]

    if any(s.get("id") == sid for s in idx.get("sessions", [])):
        # Fix 2026-08-02: this used to early-return unconditionally, making the
        # function CREATE-ONLY. Any ops run carrying session_id without a
        # session_index_entry wrote a permanently blank fingerprint that no later
        # save could fill (it blanked for 25 days), and a
        # run whose session_id collided with an already-saved session silently
        # DISCARDED real content. Now: fill a blank entry when content is
        # supplied, refuse to overwrite a populated one.
        existing = next(s for s in idx["sessions"] if s.get("id") == sid)
        sie = ops.get("session_index_entry", {})
        new_tags = sie.get("tags", ops.get("session_tags", []))
        new_summary = sie.get("summary", ops.get("session_summary", ""))
        existing_is_blank = not existing.get("summary") and not existing.get("tags")

        if existing_is_blank and (new_tags or new_summary):
            existing["tags"] = new_tags
            existing["summary"] = new_summary
            existing["outcome"] = sie.get("outcome", ops.get("outcome", "success"))
            existing["outcome_note"] = sie.get("outcome_note", ops.get("outcome_note", ""))
            if save_json(path, idx):
                print(f"  ✓ Session index: {sid} (filled a blank entry)")
                sentinel = kb / "Memory" / "cache" / ".invalidated"
                sentinel.parent.mkdir(parents=True, exist_ok=True)
                sentinel.touch()
                return True
            return False

        if (new_tags or new_summary) and not existing_is_blank:
            print(f"  ! Session {sid} already in index WITH content; refusing to "
                  f"overwrite. Supplied entry DISCARDED — check for a session_id collision.")
            return True

        print(f"  Session {sid} already in index")
        return True

    # Support both flat keys and nested session_index_entry format
    sie = ops.get("session_index_entry", {})
    _new_tags = sie.get("tags", ops.get("session_tags", []))
    _new_summary = sie.get("summary", ops.get("session_summary", ""))
    if not _new_tags and not _new_summary:
        # Every blank fingerprint in the index was born here, silently. A blank entry
        # is invisible to session-cache search and to cold-start continuity, and it
        # lets a concurrent instance's id look "taken but empty" (2026-08-05: four
        # blanks in one day). A later save CAN fill it, so
        # this is a loud warning rather than a refusal.
        print(f"  ! BLANK FINGERPRINT: registering {sid} with no tags and no summary.")
        print(f"    It will not appear in session-cache search until filled. Pass a")
        print(f"    session_index_entry, or re-save with one. Detected by")
        print(f"    scripts/maintenance.py check_session_index().")
    idx["sessions"].insert(0, {
        "id": sid, "date": get_today(),
        "tags": sie.get("tags", ops.get("session_tags", [])),
        "summary": sie.get("summary", ops.get("session_summary", "")),
        "outcome": sie.get("outcome", ops.get("outcome", "success" if (_new_tags or _new_summary) else "pending")),
        "outcome_note": sie.get("outcome_note", ops.get("outcome_note", ""))
    })
    idx.setdefault("recentIds", []).insert(0, sid)
    idx["recentIds"] = idx["recentIds"][:20]

    # Fix 2026-08-02: stats.totalSessions was never maintained on insert, so it
    # sat at 133 while the array grew to 143 (drift of 10 across 6 sessions).
    # Only the prune path (line ~942) touched it, which almost never runs.
    idx.setdefault("stats", {})["totalSessions"] = len(idx["sessions"])
    idx["lastUpdated"] = get_today()

    if save_json(path, idx):
        print(f"  ✓ Session index: {sid}")
        # Touch sentinel for session-cache invalidation
        sentinel = kb / "Memory" / "cache" / ".invalidated"
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.touch()
        return True
    return False


def _canon_category(cat):
    """Normalize a taxonomy category to canonical lowercase_underscore form.

    Callers sometimes pass the kernel's Title-Case display names
    ("Negative Knowledge", "Decisions"). Without this, those fork the
    counters into duplicate mis-cased buckets. Normalize on write.
    """
    return str(cat).strip().lower().replace(" ", "_")


# Known-good TOP-LEVEL keys in memory.json. This is NOT the whole schema:
# memory-protocol.md documents only a few fields, so a hand-written allowlist would
# keep rejecting legitimate keys (user_address was caught that way in testing). The
# check in update_memory therefore accepts a key that is EITHER on this list OR
# already established in memory.json. That blocks the real failure mode, a novel ops
# key materialising as a top-level field, which is how memory.json accumulated ~20
# junk keys such as commitments_add, set, todo_list and taxonomy_update,
# without breaking any field that currently works.
# Ops-only keys with their own branches above (version_bump,
# capture_taxonomy_increments, offer_history, session_offers_made) deliberately do
# NOT appear here.
MEMORY_TOP_LEVEL_KEYS = {
    "version", "lastUpdated", "user_address", "last_session_snapshot",
    "intelligence_system", "proactive_behavior", "active_projects", "commitments",
    "implementation_triggers", "memories", "pattern_detections", "confidence_events",
    "session_metadata", "projects_archive", "domain_expertise", "anti_preferences",
    "entities", "instance_identity", "capture_taxonomy",
    "last_cross_session_synthesis", "behavioral_profile", "ideas_backlog",
}


def _deep_merge_guarded(existing: dict, incoming: dict, path: str) -> list:
    """Recursively merge `incoming` into `existing` IN PLACE, refusing data loss.

    Returns a list of human-readable refusals (empty list means a clean merge).

    Two rules, both written after live data loss on 2026-09-21,
    when passing a whole nested object through memory_updates destroyed 35 historical
    proactive offers and silently changed a user preference, with no error raised:

      1. A nested dict is MERGED, never replaced, so a sibling key the caller did not
         mention cannot silently change or disappear.
      2. A collection is never allowed to SHRINK. Replacing a 35-item list with a
         6-item one is refused rather than written, because the caller almost
         certainly meant to append and the intent is unrecoverable afterwards.

    Refusing is the right default here: a save that silently loses records is far
    worse than a save that loudly declines one field.
    """
    refusals = []
    for k, v in incoming.items():
        cur = existing.get(k)
        sub = f"{path}.{k}"
        if isinstance(cur, dict) and isinstance(v, dict):
            refusals.extend(_deep_merge_guarded(cur, v, sub))
        elif isinstance(cur, (list, dict)) and isinstance(v, (list, dict)) and len(v) < len(cur):
            refusals.append(f"{sub} would shrink {len(cur)} -> {len(v)}")
        else:
            existing[k] = v
    return refusals


# ─── Memory index ─────────────────────────────────────────────────────────

# Authority for both constants is the LIVE Memory/memory-index.json `_meta._schema`,
# NOT scripts/normalize-memory.py, whose one-shot output is already behind the live
# file (it never writes stats.nextId).
MEMORY_TYPE_ENUM = {"preference", "decision", "correction", "learning",
                    "critical_safety", "system"}
MEMORY_REQUIRED_FIELDS = ("id", "type", "content", "context", "confidence",
                          "tags", "created", "lastAccessed", "accessCount")


def _memory_confidence_bucket(conf):
    """Live contract: critical=1.0, high>=0.8, medium=0.5-0.79, low<0.5."""
    try:
        c = float(conf)
    except (TypeError, ValueError):
        c = 0.7
    if c >= 1.0:
        return "critical"
    if c >= 0.8:
        return "high"
    if c >= 0.5:
        return "medium"
    return "low"


def _normalize_memories(mem):
    """Return the memories container as a dict keyed by id.

    Live shape is a dict (mem-001, mem-002...). A list is tolerated because other
    KB stores use that shape and the schema has drifted before (pat-366).
    """
    memories = mem.get("memories") or {}
    if isinstance(memories, list):
        return {m.get("id"): m for m in memories
                if isinstance(m, dict) and m.get("id")}
    return memories if isinstance(memories, dict) else {}


def _memory_recent_ids(memories, limit=26):
    """Most-recently-accessed ids, newest first, with a DETERMINISTIC tiebreak.

    lastAccessed is frequently a bare date, so ties are common (three entries share
    2026-09-15 in the live store). Sorting on that field alone leaves the order at the
    mercy of dict insertion order, which makes the rebuild non-reproducible and turns
    every save into a spurious diff. Tiebreak on the numeric id, highest first.
    """
    def key(item):
        mid, m = item
        la = (m.get("lastAccessed") or "") if isinstance(m, dict) else ""
        tail = str(mid).rsplit("-", 1)[-1]
        return (la, int(tail) if tail.isdigit() else -1)

    ordered = sorted(memories.items(), key=key, reverse=True)
    return [mid for mid, _ in ordered][:limit]


def rebuild_memory_index(kb, mem):
    """Rebuild Memory/memory-index.json from memory.json's `memories` dict.

    NOTHING rebuilt this index before. The only writer was normalize-memory.py, a
    one-shot normalizer with hardcoded absolute paths, so every memory change since
    left the index behind. That matters more than a normal index: the Session Start
    Gate loads memory-index at cold start and fetches entries by ID from it (CSR),
    so a stale index makes a real memory INVISIBLE rather than merely miscounted.

    Summaries are preserved where they already exist. The live file carries a mix of
    150-char and 200-char truncations plus some hand-authored longer ones, so
    regenerating all of them would churn 17 entries for no gain.
    """
    path = kb / "Memory" / "memory-index.json"
    memories = _normalize_memories(mem)
    prior = load_json(path) or {}
    prior_summaries = prior.get("summaries") or {}

    by_tag, by_type = {}, {}
    by_conf = {"critical": [], "high": [], "medium": [], "low": []}
    summaries = {}
    for mid, m in memories.items():
        if not isinstance(m, dict):
            continue
        for t in (m.get("tags") or []):
            by_tag.setdefault(t, []).append(mid)
        by_type.setdefault(m.get("type", "unknown"), []).append(mid)
        by_conf[_memory_confidence_bucket(m.get("confidence", 0.7))].append(mid)
        summaries[mid] = prior_summaries.get(mid) or (m.get("content") or "")[:200]

    # nextId is max numeric id + 1, NOT len(memories). Ids are sparse because entries
    # get pruned: the live index reads nextId 76 against 38 entries. Deriving it from
    # the count would hand out an id that already exists.
    nums = [int(str(mid).rsplit("-", 1)[-1]) for mid in memories
            if str(mid).rsplit("-", 1)[-1].isdigit()]
    next_id = (max(nums) + 1) if nums else 1

    meta = prior.get("_meta") or {
        "description": "Memory index using CSR pattern",
        "pattern": "Context Signal Routing (CSR)",
        "usage": ("Load this index always. Load specific memories from memory.json "
                  "by ID when signals match."),
        "version": "1.0",
    }
    meta["last_updated"] = datetime.datetime.now().isoformat()
    meta.setdefault("_schema", {
        "required": list(MEMORY_REQUIRED_FIELDS),
        "confidence": ("numeric 0.0-1.0 (critical=1.0, high>=0.8, "
                       "medium=0.5-0.79, low<0.5)"),
        "type_enum": sorted(MEMORY_TYPE_ENUM),
    })

    idx = {
        "_meta": meta,
        "stats": {
            "totalEntries": len(memories),
            "activeEntries": len([m for m in memories.values()
                                  if isinstance(m, dict) and not m.get("archived")]),
            "stale_candidates": len([m for m in memories.values()
                                     if isinstance(m, dict)
                                     and m.get("_stale_candidate")]),
            "nextId": next_id,
        },
        "byTag": by_tag,
        "byType": by_type,
        "byConfidence": by_conf,
        "summaries": summaries,
        "recentIds": _memory_recent_ids(memories),
    }
    if save_json(path, idx):
        print(f"  ✓ memory-index rebuilt ({len(memories)} entries, "
              f"nextId {next_id})")
        return True
    return False


def _validate_memory_entry(entry, existing):
    """Return a refusal reason, or None if the entry is safe to append."""
    if not isinstance(entry, dict):
        return "not an object"
    mid = entry.get("id")
    missing = [f for f in MEMORY_REQUIRED_FIELDS if f not in entry]
    if missing:
        return f"missing required field(s): {', '.join(missing)}"
    if entry.get("type") not in MEMORY_TYPE_ENUM:
        return (f"type '{entry.get('type')}' not in "
                f"{sorted(MEMORY_TYPE_ENUM)}")
    if mid in existing:
        return f"id '{mid}' already exists"
    return None


def _norm_project_name(s):
    """Normalized project-name key: lowercase, parenthetical qualifiers and punctuation
    dropped, whitespace collapsed. Exact-name matching appended a new project for every
    name variant (two entries for the same project under slightly different names)."""
    s = (s or "").lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


COMMITMENT_TEXT_FIELDS = ("what", "deliverable", "commitment", "task")


def _match_commitments(commitments, token):
    """Commitments a token identifies: exact id first, else EXACT text on any text field.
    Never substring (a prefix must not hit a longer commitment)."""
    hits = [c for c in commitments if isinstance(c, dict) and c.get("id") == token]
    if not hits:
        hits = [c for c in commitments if isinstance(c, dict)
                and any(c.get(f) == token for f in COMMITMENT_TEXT_FIELDS)]
    return hits


def _new_commitment_id(commitment, existing, today):
    """cmt-YYYY-MM-DD-<slug> from the commitment text, unique against existing ids."""
    text = next((str(commitment.get(f)) for f in COMMITMENT_TEXT_FIELDS if commitment.get(f)), "item")
    words = re.findall(r"[a-z0-9]+", text.lower())
    slug = "-".join(w for w in words if len(w) > 2)[:32].strip("-") or "item"
    base = f"cmt-{commitment.get('created') or today}-{slug}"
    taken = {c.get("id") for c in existing if isinstance(c, dict)}
    cid, n = base, 2
    while cid in taken:
        cid, n = f"{base}-{n}", n + 1
    return cid


def update_memory(kb, ops):
    path = kb / "Memory" / "memory.json"
    mem = load_json(path)
    if mem is None:
        return False

    today = get_today()
    changed = False

    for key, value in ops.get("memory_updates", {}).items():
        if key == "version_bump":
            # this used to assign the value literally, so
            # version_bump: true set memory.json's version to the boolean True and
            # corrupted the field. A string is authoritative; anything else truthy
            # means "increment for me".
            if isinstance(value, str) and value.strip():
                mem["version"] = value.strip()
            elif value:
                mem["version"] = _bump_version(mem.get("version"))
                print(f"  version: auto-incremented to {mem['version']} "
                      f"(non-string version_bump)")
        elif key == "capture_taxonomy_increments":
            pass  # Handled by taxonomy_hits section below
        elif key == "domain_expertise" and isinstance(value, dict):
            mem.setdefault("domain_expertise", {}).update(value)
        elif key == "anti_preferences" and isinstance(value, dict):
            mem.setdefault("anti_preferences", {}).update(value)
        elif key == "last_session_snapshot" and isinstance(value, dict):
            mem["last_session_snapshot"] = value
        elif key in ("offer_history", "session_offers_made"):
            # no handler existed, so save checklist item 4 (consolidate
            # proactive offers) could not be executed through the script at all and
            # required a manual memory edit. These belong under proactive_behavior,
            # not at the top level, which is why the catch-all was the wrong home.
            pb = mem.setdefault("proactive_behavior", {})
            if key == "offer_history":
                if isinstance(value, list):
                    pb.setdefault("offer_history", []).extend(value)
                else:
                    pb.setdefault("offer_history", []).append(value)
            else:
                pb["session_offers_made"] = value
        else:
            # Replaces the old blind `mem[key] = value`, which caused BOTH documented
            # failure classes: wholesale replacement of nested objects (35 offers and a
            # user preference destroyed silently) and ops-key leakage into memory.json.
            if key not in MEMORY_TOP_LEVEL_KEYS and key not in mem:
                print(f"  ✗ memory_updates: unknown NEW key '{key}' REJECTED, not written "
                      f". Route it through its own handler, or add it to "
                      f"MEMORY_TOP_LEVEL_KEYS if it is a real memory field.")
                continue
            cur = mem.get(key)
            if isinstance(cur, dict) and isinstance(value, dict):
                refusals = _deep_merge_guarded(cur, value, key)
                for r in refusals:
                    print(f"  ✗ memory_updates: {r}, REFUSED. "
                          f"Read current value, merge, then pass the merged whole.")
            elif isinstance(cur, (list, dict)) and isinstance(value, (list, dict)) \
                    and len(value) < len(cur):
                print(f"  ✗ memory_updates: '{key}' would shrink {len(cur)} -> "
                      f"{len(value)}, REFUSED. Read-merge-write instead.")
                continue
            else:
                mem[key] = value
        changed = True

    for update in ops.get("active_project_updates", []):
        projects = mem.setdefault("active_projects", {})
        # Handle both dict-of-dicts (current) and list (legacy) formats
        target = _norm_project_name(update.get("name"))
        if isinstance(projects, list):
            cands = [p for p in projects if isinstance(p, dict)
                     and _norm_project_name(p.get("name")) == target]
            # Exact name first, then a live entry: a superseded/archived twin must never
            # absorb the update (a superseded "project-x" can sit beside a live "Project X").
            existing = (next((p for p in cands if p.get("name") == update.get("name")), None)
                        or next((p for p in cands if str(p.get("status", "")).lower()
                                 not in ("superseded", "archived", "retired", "done", "complete")), None)
                        or (cands[0] if cands else None))
            if existing:
                if existing.get("name") != update.get("name"):
                    print(f"  ~ project '{update.get('name')}' matched existing "
                          f"'{existing.get('name')}' (normalized name)")
                existing.update({k: v for k, v in update.items() if k != "name"})
            else:
                projects.append(update)
        else:
            # Dict-of-dicts format: key is project name
            name = update.get("name", "")
            key = next((k for k in projects if _norm_project_name(k) == target), name)
            if key in projects:
                projects[key].update({k: v for k, v in update.items() if k != "name"})
            else:
                projects[name] = {k: v for k, v in update.items() if k != "name"}
        changed = True

    for c in ops.get("new_commitments", []):
        existing_commits = mem.setdefault("commitments", [])
        if isinstance(c, dict) and not c.get("id"):
            c["id"] = _new_commitment_id(c, existing_commits, today)
            print(f"  + commitment id assigned: {c['id']}")
        existing_commits.append(c)
        changed = True

    # there was NO path to append a memory entry. Routing one
    # through memory_updates either leaked it as a stray top-level key or,
    # after the 2026-09-21 hardening, tripped the shrink guard because a 1-item list is
    # smaller than the dict it would replace. So recording a memory required a hand edit
    # of memory.json, which the script-first gate prohibits and which caused data loss.
    new_memories = ops.get("new_memories") or []
    if new_memories:
        memories = _normalize_memories(mem)
        for entry in new_memories:
            reason = _validate_memory_entry(entry, memories)
            if reason:
                mid = entry.get("id") if isinstance(entry, dict) else "?"
                print(f"  ✗ new_memories: '{mid}' REFUSED, {reason}")
                continue
            memories[entry["id"]] = entry
            print(f"  + memory {entry['id']} ({entry['type']})")
            changed = True
        mem["memories"] = memories

    # Commitments written before the id convention carry no 'id' at all, and pat-366
    # schema drift put the text under 'what', 'deliverable' OR 'commitment' depending on
    # which session wrote it. Matching on id alone left every one of those PERMANENTLY
    # unresolvable through the sanctioned path, and the only way out was a hand edit of
    # memory.json, which the script-first gate prohibits. Found 2026-09-22 while closing
    # a real commitment.
    #
    # Match on id first, then fall back to EXACT text on any of the three text fields.
    # Never substring: a prefix must not resolve a longer commitment. An ambiguous token
    # resolves NOTHING rather than several, because silently closing extra commitments is
    # the class of quiet data damage.
    for upd in ops.get("commitment_updates", []):
        token = (upd or {}).get("id") or (upd or {}).get("match")
        fields = dict((upd or {}).get("set") or {})
        fields.pop("id", None)  # ids are stable keys; never rewritten here
        if not token or not fields:
            print(f"  ✗ commitment_updates: needs 'id' (or 'match') and a non-empty 'set', skipped: {upd}")
            continue
        matches = _match_commitments(mem.get("commitments", []), token)
        if len(matches) != 1:
            why = "matches no commitment" if not matches else f"matches {len(matches)} commitments (ambiguous)"
            print(f"  ✗ commitment_updates: '{str(token)[:60]}' {why}, REFUSED")
            continue
        c = matches[0]
        before = {k: c.get(k) for k in fields}
        c.update(fields)
        note = f"{today}: updated by {ops.get('session_id') or 'unattributed'}: " + \
            ", ".join(f"{k} {before[k]!r} -> {fields[k]!r}" for k in fields)
        c["note"] = f"{c['note']} | {note}" if c.get("note") else note
        print(f"  ✓ commitment_updates: {c.get('id') or str(token)[:40]} ({', '.join(fields)})")
        changed = True

    for cid in ops.get("resolved_commitments", []):
        commitments = mem.get("commitments", [])
        matches = _match_commitments(commitments, cid)
        if len(matches) > 1:
            print(f"  ✗ resolved_commitments: '{str(cid)[:60]}' matches "
                  f"{len(matches)} commitments, REFUSED as ambiguous. "
                  f"Add an 'id' to the target to disambiguate.")
            continue
        if not matches:
            print(f"  ✗ resolved_commitments: no commitment matches "
                  f"'{str(cid)[:60]}', skipped")
            continue
        matches[0]["status"] = "resolved"
        matches[0]["resolved_date"] = today
        # Attribution is the real clobber guard. A calendar VTODO mirror
        # might look like protection against a commitment flipped to done-without-being
        # -done, but it cannot: VTODOs carrying X-NATE-SOURCE are a
        # GENERATED view of memory.json, so a clobber deletes the VTODO on the next sync
        # instead of being caught by it. What IS detectable is an unattributed closure.
        # Stamp the resolving session here; maintenance.py flags any closed commitment
        # missing this field, which is the signature a silent flip leaves behind.
        matches[0].setdefault("resolved_by", ops.get("session_id") or "unattributed")
        changed = True

    # One-time / repeatable cleanup of ops-key LEAKAGE. The old blind
    # catch-all wrote every unrecognised memory_updates key straight into memory.json,
    # so it accumulated ~19 junk top-level keys (commitments_add, set, todo_list,
    # taxonomy_update, active_project_touches...). The guard above stops NEW leaks, but
    # the script had no way to clean the existing ones, which is why they survived for
    # months. Removing them is now a first-class operation instead of a hand edit.
    # SAFETY: verify the data reached its proper home before removing a data-bearing
    # key. A 2026-09-21 audit found an orphaned Google Maps commitment in a leaked
    # `new_commitments` key that had NEVER been applied to commitments[].
    for key in ops.get("memory_remove_keys", []):
        if key in MEMORY_TOP_LEVEL_KEYS:
            print(f"  ✗ memory_remove_keys: refusing to remove '{key}', it is a known "
                  f"memory field, not ops leakage")
            continue
        if key in mem:
            mem.pop(key)
            print(f"  - memory: removed leaked ops key '{key}'")
            changed = True
        else:
            print(f"  · memory_remove_keys: '{key}' not present, nothing to do")

    # this only ran when an explicit 'snapshot' op was passed, so save
    # step 6 (update last_session_snapshot) was silently skipped on most saves. It is
    # mandatory, cheap, and derivable, so it now always runs.
    if ops.get("session_id"):
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
            "active_projects": len([p for p in (mem.get("active_projects", {}).values()
                                    if isinstance(mem.get("active_projects"), dict)
                                    else mem.get("active_projects", []))
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
        # Convert legacy list format to dict if needed
        if isinstance(ct.get("category_hits"), list):
            ct["category_hits"] = {}
        ch = ct.setdefault("category_hits", {})
        for cat, count in hits.items():
            key = _canon_category(cat)
            ch[key] = ch.get(key, 0) + count
        changed = True

    if ops.get("cross_session_synthesis_done") or ops.get("memory_updates", {}).get("last_cross_session_synthesis"):
        mem["last_cross_session_synthesis"] = ops["session_id"]
        changed = True

    if changed:
        mem["lastUpdated"] = today
        if save_json(path, mem):
            print(f"  ✓ Memory updated")
            rebuild_memory_index(kb, mem)
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


def regenerate_file_structure(repo_root):
    """Regenerate the steering FILE-STRUCTURE.md via the canonical generator.

    The map now lives at .kiro/steering/FILE-STRUCTURE.md (steering => always in
    context). scripts/gen-file-structure.py is the single source of truth (also
    invoked by nate.json postToolUse/agentSpawn hooks). Delegating here avoids
    format divergence and the old behavior of writing a stale copy at repo root.
    """
    import subprocess
    gen = repo_root / "scripts" / "gen-file-structure.py"
    try:
        r = subprocess.run([sys.executable, str(gen)], capture_output=True,
                           text=True, timeout=30)
        msg = (r.stdout or "").strip() or "FILE-STRUCTURE.md regenerated"
        if r.returncode == 0:
            print(f"  ✓ {msg}")
        else:
            print(f"  WARN: FILE-STRUCTURE.md regen exit {r.returncode}: {(r.stderr or '').strip()}")
    except Exception as e:
        print(f"  WARN: FILE-STRUCTURE.md regen failed: {e}")


def _session_date(session_id):
    """Parse the date out of a session ID/filename. Returns date or None.

    Uses the ID's embedded date rather than file mtime: these files get copied
    between machines and instances, and mtime does not survive that. The ID is
    the authoritative timestamp.
    """
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(session_id))
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def prune_sessions(kb):
    """Enforce the session retention rules from memory-protocol.md.

    Rules (memory-protocol.md -> Retention Rules):
      - Session log files: 30 days, min keep 10, ARCHIVE to Memory/archive/
      - Session index entries: 60 days, min keep 10, remove from live index

    Index entries are moved to Memory/session-archive.json rather than destroyed.
    memory-protocol says "destroy metadata", but maintenance-protocol already
    budgets a session-archive.json, and moving costs nothing while keeping
    historical recall possible. The live index stays small either way, which is
    the actual goal.

    This existed only as documentation until 2026-07-25. prune_check reported
    intelligence-store counts and performed no retention work, so 234 logs sat
    past the 30-day window with 2 archived, and the session index carried 222
    entries past the 60-day window (~44k startup tokens of dead weight).
    """
    mem = kb / "Memory"
    archive_dir = mem / "archive"
    today = datetime.date.today()
    log_cutoff = today - datetime.timedelta(days=30)
    idx_cutoff = today - datetime.timedelta(days=60)
    MIN_KEEP = 10

    # --- Session log files ---
    logs = sorted(mem.glob("session-*.md"))
    dated = [(p, _session_date(p.name)) for p in logs]
    undated = [p for p, d in dated if d is None]
    dated = sorted([(p, d) for p, d in dated if d is not None], key=lambda x: x[1])

    to_archive = [p for p, d in dated if d < log_cutoff]
    # Never archive below the min-keep floor of most-recent logs
    keepable = len(dated) - MIN_KEEP
    if keepable < 0:
        keepable = 0
    to_archive = to_archive[:keepable]

    archived = 0
    if to_archive:
        if DRY_RUN:
            print(f"  [DRY-RUN] Would archive {len(to_archive)} session logs to Memory/archive/")
        else:
            archive_dir.mkdir(parents=True, exist_ok=True)
            for p in to_archive:
                dest = archive_dir / p.name
                if dest.exists():
                    p.unlink()  # already archived, drop the duplicate
                else:
                    p.rename(dest)
                archived += 1
            print(f"  ✓ sessions: archived {archived} logs older than 30d "
                  f"({len(dated) - archived} active)")
    else:
        print(f"  ✓ sessions: {len(dated)} logs, none past 30d retention")
    if undated:
        print(f"  ! sessions: {len(undated)} logs with unparseable dates, left in place")

    # --- Session index entries ---
    idx_path = mem / "session-index.json"
    idx = load_json(idx_path)
    if idx is None:
        return archived, 0

    sessions = idx.get("sessions", [])
    dated_idx = []
    for s in sessions:
        d = _session_date(s.get("date") or s.get("id") or "")
        dated_idx.append((s, d))

    old = [s for s, d in dated_idx if d is not None and d < idx_cutoff]
    keepable_idx = len(sessions) - MIN_KEEP
    if keepable_idx < 0:
        keepable_idx = 0
    old = old[:keepable_idx]
    old_ids = {id(s) for s in old}

    if not old:
        print(f"  ✓ session-index: {len(sessions)} entries, none past 60d retention")
        return archived, 0

    if DRY_RUN:
        print(f"  [DRY-RUN] Would move {len(old)} session-index entries to session-archive.json")
        return archived, len(old)

    arch_path = mem / "session-archive.json"
    arch = load_json(arch_path) or {"_meta": {
        "description": "Session index entries aged out of the 60-day live window",
        "source": "save-session.py prune_sessions",
    }, "sessions": []}
    existing = {s.get("id") for s in arch.get("sessions", [])}
    arch["sessions"] = arch.get("sessions", []) + [s for s in old if s.get("id") not in existing]
    arch["sessions"].sort(key=lambda s: s.get("date") or s.get("id") or "")
    arch["lastUpdated"] = get_today()

    idx["sessions"] = [s for s in sessions if id(s) not in old_ids]
    if "stats" in idx and isinstance(idx["stats"], dict):
        idx["stats"]["totalSessions"] = len(idx["sessions"])
        idx["stats"]["archivedSessions"] = len(arch["sessions"])
    idx["lastUpdated"] = get_today()

    if save_json(arch_path, arch) and save_json(idx_path, idx):
        print(f"  ✓ session-index: moved {len(old)} entries past 60d to session-archive.json "
              f"({len(idx['sessions'])} live)")
        return archived, len(old)
    print("  ✗ session-index: write failed, live index unchanged")
    return archived, 0


def prune_check(kb):
    """Intelligence stores grow indefinitely — CSR indexes keep query cost constant.
    No size caps. Stale entries (accessCount=0, age > 3 years) flagged by maintenance.py.

    Session data DOES have retention rules (memory-protocol.md) and they are
    enforced here by prune_sessions().
    """
    for store in ("patterns", "knowledge", "reasoning"):
        data = load_json(kb / "Intelligence" / f"{store}.json")
        if data:
            print(f"  ✓ {store}: {len(data.get('entries', []))} entries (no cap)")
    prune_sessions(kb)


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


# ─── ACP Marker Extraction ────────────────────────────────────────────────

ACP_REGEX = re.compile(
    r'\[CAPTURE:\s*(decision|correction|discovery|process|failure|preference|'
    r'observation|negative-knowledge|dependency|commitment|other)\s*[—–-]\s*(.+?)\]'
)

def extract_acp_markers(kb, session_id):
    """Extract [CAPTURE: ...] markers from session log. Returns list of dicts."""
    log_path = kb / "Memory" / f"{session_id}.md"
    if not log_path.exists():
        return []
    try:
        text = log_path.read_text(encoding="utf-8")
    except Exception:
        return []
    seen = set()
    markers = []
    for m in ACP_REGEX.finditer(text):
        category, content = m.group(1).strip(), m.group(2).strip()
        key = (category, content)
        if key not in seen:
            seen.add(key)
            markers.append({"category": category, "content": content})
    return markers


# ─── Pre-flight Normalization ─────────────────────────────────

def _id_prefix(eid):
    """Return the ID prefix for auto-bump: 'know-', 'reason-', or '<cat>_' (e.g. 'fail_')."""
    if re.match(r'^know-\d+$', eid):
        return 'know-'
    if re.match(r'^reason-\d+$', eid):
        return 'reason-'
    m = re.match(r'^([a-z_]+)_\d+$', eid)
    if m:
        return m.group(1) + '_'
    return None


def _max_num_for_prefix(ids, prefix):
    mx = 0
    for eid in ids:
        if not eid or not eid.startswith(prefix):
            continue
        tail = eid[len(prefix):] if not prefix.endswith('-') else eid.split('-', 1)[1]
        try:
            mx = max(mx, int(tail))
        except (ValueError, IndexError):
            pass
    return mx


def normalize_ops(ops, kb):
    """Auto-fix common ops mismatches BEFORE validation, so a save doesn't need multiple
    retry passes. Returns a list of human-readable normalization notes. Non-destructive to
    intent: only defaults missing provenance fields and reassigns colliding IDs."""
    notes = []
    if not isinstance(ops, dict):
        return notes

    # 1. taxonomy_hits list -> {cat: 1} dict (list crashes update_memory's .items())
    th = ops.get("taxonomy_hits")
    if isinstance(th, list):
        ops["taxonomy_hits"] = {c: 1 for c in th}
        notes.append(f"taxonomy_hits: list->dict ({len(th)} categories)")

    sid = ops.get("session_id", "")

    for store in ("patterns", "knowledge", "reasoning"):
        entries = ops.get(f"new_{store}")
        if not entries and "new_entries" in ops:
            entries = ops.get("new_entries", {}).get(store)
        if not entries:
            continue

        data = load_json(kb / "Intelligence" / f"{store}.json") or {}
        existing = {e.get("id") for e in data.get("entries", []) if e.get("id")}
        assigned = set()
        remap = {}

        for e in entries:
            if not isinstance(e, dict):
                continue
            # field defaults that would otherwise hard-abort validation
            if store == "knowledge" and not e.get("source"):
                e["source"] = sid
                notes.append(f"{e.get('id', '?')}: source defaulted to {sid}")
            # Patterns had no source default and no validation, so most patterns ended up
            # with no source and the quality audit could not attribute them to a session.
            if store == "patterns" and not e.get("source") and sid:
                e["source"] = sid
                notes.append(f"{e.get('id', '?')}: source defaulted to {sid}")
            if store == "reasoning":
                if not e.get("provenance"):
                    e["provenance"] = "stated"
                    notes.append(f"{e.get('id', '?')}: provenance defaulted to stated")
                if e.get("derived_from") is None:
                    e["derived_from"] = []

            # ID auto-bump on collision (with store OR earlier entries in this batch)
            old = e.get("id", "")
            pfx = _id_prefix(old)
            if pfx and (old in existing or old in assigned):
                new = f"{pfx}{_max_num_for_prefix(existing | assigned, pfx) + 1}"
                e["id"] = new
                remap[old] = new
                notes.append(f"{old}->{new} (ID collision auto-bumped)")
                old = new
            if old:
                assigned.add(old)

        # remap derived_from refs that pointed at a bumped id within this same batch
        if store == "reasoning" and remap:
            for e in entries:
                df = e.get("derived_from")
                if isinstance(df, list):
                    e["derived_from"] = [remap.get(x, x) for x in df]

    return notes


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    global DRY_RUN

    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]
    DRY_RUN = '--dry-run' in flags

    # Claim-only mode: reserve the next session id atomically and print it. Wired into
    # save step 1 so the id is never hand-picked. See claim_session_id().
    if '--claim-session-id' in flags:
        print(claim_session_id(find_kb_root()))
        return

    if not args:
        print("Usage: python3 scripts/save-session.py [--dry-run] OPS_FILE")
        print("       python3 scripts/save-session.py --claim-session-id")
        sys.exit(2)

    ops_file = args[0]
    ops = load_json(ops_file)
    if ops is None:
        print(f"ERROR: Could not load {ops_file}", file=sys.stderr)
        sys.exit(2)

    # Pre-flight normalization (auto-fix common mismatches before validation)
    _pf_kb = find_kb_root()
    _norm = normalize_ops(ops, _pf_kb)
    if _norm:
        print("Pre-flight normalization")
        for _n in _norm:
            print(f"  ~ {_n}")
        print()

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

    # ACP marker extraction
    markers = extract_acp_markers(kb, session_id)
    if markers:
        valid = [m for m in markers if m["category"] in ACP_REGEX.pattern]
        ops["_acp_candidates"] = markers
        print(f"ACP: extracted {len(markers)} candidates from session log")
    
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
                # Mechanical post-save check (candidate 2026-10-20, replaces the behavioral
                # proc_186 step that failed on: re-read the row we
                # just wrote. A blank fingerprint is invisible to cold-start continuity, so
                # it must not end in EXIT:0. Ops file is preserved for a re-save to fill it.
                if not DRY_RUN and not _session_fingerprint_populated(kb, ops["session_id"]):
                    print(f"  ! FINGERPRINT CHECK FAILED: {ops['session_id']} has no tags and no summary "
                          f"on disk. Re-save with a session_index_entry.")
                    failed.append("session_fingerprint")
            else:
                failed.append("session_index")
            print()

            # Intelligence stores
            _valid_ids = None
            if ops.get("entry_updates"):
                _valid_ids = _all_intel_ids(kb)
                # Entries created in this same save are valid supersession targets
                for _s in ("patterns", "knowledge", "reasoning"):
                    _valid_ids.update(e.get("id") for e in get_entries(ops, _s) if e.get("id"))
            for store_name in ("patterns", "knowledge", "reasoning"):
                print(f"{store_name.title()}")
                new = get_entries(ops, store_name)
                access = get_access_ids(ops, store_name)
                updates = ops.get("entry_updates", {}).get(store_name, [])

                added, ok = add_entries(kb, store_name, new)
                if not ok:
                    failed.append(store_name)
                    print()
                    continue

                update_access(kb, store_name, access)
                if updates:
                    # New entries in this save are valid supersession targets too
                    if added and _valid_ids is not None:
                        _valid_ids.update(added)
                    _, upd_ok = apply_entry_updates(kb, store_name, updates, _valid_ids)
                    if not upd_ok:
                        failed.append(f"{store_name}_updates")
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
        # Count sessions since last cross-session synthesis
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

    # File structure regen (git-independent)
    print("File Structure")
    regenerate_file_structure(kb.parent)
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
