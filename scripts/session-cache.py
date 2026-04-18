#!/usr/bin/env python3
"""Session cache: SQLite routing cache for session-index.json.

Enables sub-millisecond session queries by tag, date, keyword, and outcome
without loading the full session-index.json into LLM context.

Usage:
    python3 scripts/session-cache.py '{"action": "query", "tags": ["deep-work"]}'
    python3 scripts/session-cache.py '{"action": "query", "date_from": "2026-04-01"}'
    python3 scripts/session-cache.py '{"action": "query", "keyword": "transit test"}'
    python3 scripts/session-cache.py '{"action": "query", "outcome": "blocked"}'
    python3 scripts/session-cache.py '{"action": "rebuild"}'
    python3 scripts/session-cache.py '{"action": "stats"}'

Exit codes: 0=success, 1=rebuilt transparently, 2=fatal error
"""

import json
import os
import sqlite3
import sys
import time
from pathlib import Path


def find_kb_root():
    for p in [Path(__file__).resolve().parent.parent / "Nate's-kb",
              Path.cwd() / "Nate's-kb"]:
        if p.exists():
            return p
    print(json.dumps({"error": "Cannot find Nate's-kb directory"}))
    sys.exit(2)


KB_ROOT = find_kb_root()
INDEX_PATH = KB_ROOT / "Memory" / "session-index.json"
CACHE_DIR = KB_ROOT / "Memory" / "cache"
DB_PATH = CACHE_DIR / "sessions.db"
SENTINEL = CACHE_DIR / ".invalidated"


def load_index():
    with open(INDEX_PATH) as f:
        data = json.load(f)
    return data.get("sessions", [])


def detect_fts5(conn):
    try:
        conn.execute("CREATE VIRTUAL TABLE _fts5_test USING fts5(x)")
        conn.execute("DROP TABLE _fts5_test")
        return True
    except sqlite3.OperationalError:
        return False


def rebuild():
    """Rebuild cache from session-index.json. Atomic."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    sessions = load_index()

    tmp_db = str(DB_PATH) + ".tmp"
    if os.path.exists(tmp_db):
        os.remove(tmp_db)

    conn = sqlite3.connect(tmp_db)
    conn.execute("PRAGMA journal_mode=WAL")

    conn.execute("""CREATE TABLE sessions (
        id TEXT PRIMARY KEY, date TEXT NOT NULL, tags TEXT NOT NULL,
        summary TEXT NOT NULL, outcome TEXT NOT NULL, outcome_note TEXT)""")
    conn.execute("CREATE INDEX idx_date ON sessions(date)")
    conn.execute("CREATE INDEX idx_outcome ON sessions(outcome)")

    has_fts5 = detect_fts5(conn)
    if has_fts5:
        conn.execute("CREATE VIRTUAL TABLE sessions_fts USING fts5(id, summary)")

    for s in sessions:
        tags_json = json.dumps(s.get("tags", []))
        conn.execute("INSERT OR REPLACE INTO sessions VALUES (?,?,?,?,?,?)",
                     (s["id"], s["date"], tags_json, s.get("summary", ""),
                      s.get("outcome", ""), s.get("outcome_note", "")))
        if has_fts5:
            conn.execute("INSERT INTO sessions_fts(id, summary) VALUES (?, ?)",
                         (s["id"], s.get("summary", "")))

    # Store metadata
    conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO meta VALUES ('has_fts5', ?)", (str(has_fts5),))
    conn.execute("INSERT INTO meta VALUES ('rebuilt_at', ?)", (time.strftime("%Y-%m-%dT%H:%M:%S"),))
    conn.execute("INSERT INTO meta VALUES ('session_count', ?)", (str(len(sessions)),))

    conn.commit()
    conn.close()

    os.replace(tmp_db, str(DB_PATH))

    # Delete sentinel AFTER replace (C5 fix: ordering matters for crash safety)
    if SENTINEL.exists():
        SENTINEL.unlink()
    # Re-check for TOCTOU race (concurrent save)
    if SENTINEL.exists():
        return rebuild()

    return has_fts5


def ensure_cache():
    """Ensure cache exists and is fresh. Returns (conn, has_fts5, was_rebuilt)."""
    was_rebuilt = False

    if SENTINEL.exists() or not DB_PATH.exists():
        rebuild()
        was_rebuilt = True

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        # Verify tables exist
        conn.execute("SELECT 1 FROM sessions LIMIT 1")
    except (sqlite3.DatabaseError, sqlite3.OperationalError):
        # Corrupt cache — rebuild
        if DB_PATH.exists():
            DB_PATH.unlink()
        rebuild()
        was_rebuilt = True
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row

    # Read FTS5 flag
    try:
        row = conn.execute("SELECT value FROM meta WHERE key='has_fts5'").fetchone()
        has_fts5 = row[0] == "True" if row else False
    except sqlite3.OperationalError:
        has_fts5 = False

    return conn, has_fts5, was_rebuilt


def query(conn, has_fts5, params):
    """Execute query with combined filters."""
    conditions = []
    query_params = []

    # Tag filter: JSON array membership (not FTS5 — hyphenated tags)
    tags = params.get("tags")
    if tags and isinstance(tags, list) and len(tags) > 0:
        tag_clauses = []
        for tag in tags:
            if tag:  # skip empty strings
                tag_clauses.append("tags LIKE ?")
                query_params.append(f'%"{tag}"%')
        if tag_clauses:
            conditions.append(f"({' OR '.join(tag_clauses)})")

    # Date range
    date_from = params.get("date_from")
    if date_from:
        conditions.append("date >= ?")
        query_params.append(date_from)

    date_to = params.get("date_to")
    if date_to:
        conditions.append("date <= ?")
        query_params.append(date_to)

    # Outcome filter
    outcome = params.get("outcome")
    if outcome:
        conditions.append("outcome = ?")
        query_params.append(outcome)

    # Keyword filter
    keyword = params.get("keyword")
    fts_session_ids = None
    if keyword and keyword.strip():
        if has_fts5:
            try:
                fts_rows = conn.execute(
                    "SELECT id FROM sessions_fts WHERE sessions_fts MATCH ?",
                    (keyword,)).fetchall()
                fts_session_ids = {r[0] for r in fts_rows}
            except sqlite3.OperationalError:
                conditions.append("summary LIKE ? COLLATE NOCASE")
                query_params.append(f"%{keyword}%")
        else:
            conditions.append("summary LIKE ? COLLATE NOCASE")
            query_params.append(f"%{keyword}%")

    # Build SQL
    sql = "SELECT * FROM sessions"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY date DESC"

    limit = params.get("limit", 10)
    sql += f" LIMIT {int(limit)}"

    rows = conn.execute(sql, query_params).fetchall()

    # Apply FTS5 filter if we got ID matches
    if fts_session_ids is not None:
        rows = [r for r in rows if r["id"] in fts_session_ids]

    results = []
    for r in rows:
        results.append({
            "id": r["id"], "date": r["date"],
            "tags": json.loads(r["tags"]),
            "summary": r["summary"], "outcome": r["outcome"],
            "outcome_note": r["outcome_note"]
        })

    return results


def stats(conn):
    """Return cache statistics."""
    total = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

    date_range = conn.execute(
        "SELECT MIN(date), MAX(date) FROM sessions").fetchone()

    outcomes = {}
    for row in conn.execute(
            "SELECT outcome, COUNT(*) FROM sessions GROUP BY outcome"):
        outcomes[row[0]] = row[1]

    rebuilt_at = None
    try:
        row = conn.execute("SELECT value FROM meta WHERE key='rebuilt_at'").fetchone()
        if row:
            rebuilt_at = row[0]
    except sqlite3.OperationalError:
        pass

    cache_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0

    return {
        "total_sessions": total,
        "date_range": [date_range[0], date_range[1]] if date_range[0] else [],
        "outcomes": outcomes,
        "cache_file": str(DB_PATH),
        "cache_size_bytes": cache_size,
        "last_rebuild": rebuilt_at
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: session-cache.py '{\"action\": \"query\", ...}'"}))
        sys.exit(2)

    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(2)

    action = params.get("action")
    if not action:
        print(json.dumps({"error": "Missing 'action' parameter"}))
        sys.exit(2)

    if action == "rebuild":
        if not INDEX_PATH.exists():
            print(json.dumps({"error": f"session-index.json not found at {INDEX_PATH}"}))
            sys.exit(2)
        rebuild()
        print(json.dumps({"status": "rebuilt", "cache": str(DB_PATH)}))
        sys.exit(0)

    if action == "stats":
        conn, has_fts5, was_rebuilt = ensure_cache()
        result = stats(conn)
        result["from_rebuild"] = was_rebuilt
        conn.close()
        print(json.dumps(result))
        sys.exit(1 if was_rebuilt else 0)

    if action == "query":
        conn, has_fts5, was_rebuilt = ensure_cache()
        results = query(conn, has_fts5, params)
        conn.close()
        output = {
            "results": results,
            "total": len(results),
            "from_rebuild": was_rebuilt
        }
        print(json.dumps(output))
        sys.exit(1 if was_rebuilt else 0)

    print(json.dumps({"error": f"Unknown action: {action}"}))
    sys.exit(2)


if __name__ == "__main__":
    main()
