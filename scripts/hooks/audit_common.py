#!/usr/bin/env python3
"""audit_common.py - shared helpers for the tamper-evident tool-action audit ledger (H1 / steal-list #14).

One append-only JSONL ledger of tool actions: executed events (postToolUse audit_log.py) +
deny/log events (preToolUse denylist.py). HMAC-SHA256 hash-chained: each record signs over the
PREVIOUS record's hash, so altering, inserting, or deleting any past record is detectable via
verify_chain(). args_summary is credential-redacted before write.

Paths (env overridable), both under HOME ~/.kiro (OUTSIDE the repo snapshot scope, so a copied
snapshot carries neither ledger nor key and cannot forge entries elsewhere, satisfies steal-list #20):
  ledger: ~/.kiro/nate-audit.jsonl       (NATE_AUDIT_LOG)
  key:    ~/.kiro/nate-audit-hmac.key    (NATE_AUDIT_KEY)  - 32 random bytes, 0600. Denylist-protected read.

Scope limit (recorded, per Aug-8 #14): this is audit-AFTER-action (forensics), not prevention, there is
no runtime chokepoint to deny at. The preToolUse denylist is the prevention layer; this is the record.

FAIL-OPEN: write_event never raises. If key/HMAC/lock fails, the record is still appended marked
"_unchained": true so no event is lost; verify_chain reports the chain gap.
"""
from __future__ import annotations
import os
import re
import json
import hmac
import hashlib
from datetime import datetime, timezone

try:
    import fcntl  # POSIX advisory locking (WSL/Linux/macOS); absent on native Windows
except Exception:
    fcntl = None

LOG_PATH = os.path.expanduser(os.environ.get("NATE_AUDIT_LOG", "~/.kiro/nate-audit.jsonl"))
KEY_PATH = os.path.expanduser(os.environ.get("NATE_AUDIT_KEY", "~/.kiro/nate-audit-hmac.key"))
_MAX = 500
_KEY_MIN = 32
_GENESIS = "GENESIS"

_REDACT = [
    (re.compile(r"(AKIA|ASIA)[A-Z0-9]{16}"), "<AWS_KEY_ID>"),
    (re.compile(r"-----BEGIN[^-]*PRIVATE KEY-----.*?-----END[^-]*PRIVATE KEY-----", re.S), "<PRIVATE_KEY>"),
    (re.compile(r"\b([A-Za-z0-9_]*(?:SECRET|TOKEN|PASSWORD|API_KEY|ACCESS_KEY)[A-Za-z0-9_]*)\s*[=:]\s*['\"]?[^\s'\"]+", re.I), r"\1=<REDACTED>"),
]


def redact(text: str) -> str:
    for pat, repl in _REDACT:
        text = pat.sub(repl, text)
    return text


def summarize(tool_input) -> str:
    try:
        raw = json.dumps(tool_input, ensure_ascii=False)
    except Exception:
        raw = str(tool_input)
    return redact(raw)[:_MAX]


def _load_or_create_key():
    """Return the HMAC key bytes (>=32) or None. A short/corrupt key returns None (never silently sign with a weak key)."""
    try:
        if os.path.exists(KEY_PATH):
            with open(KEY_PATH, "rb") as f:
                k = f.read()
            return k if len(k) >= _KEY_MIN else None
        d = os.path.dirname(KEY_PATH)
        if d:
            os.makedirs(d, exist_ok=True)
        k = os.urandom(32)
        fd = os.open(KEY_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(fd, k)
        finally:
            os.close(fd)
        return k
    except FileExistsError:  # race: another process created it first
        try:
            with open(KEY_PATH, "rb") as f:
                k = f.read()
            return k if len(k) >= _KEY_MIN else None
        except Exception:
            return None
    except Exception:
        return None


def _payload(rec: dict) -> str:
    """Canonical payload for hashing: the record minus the chain fields, key-sorted."""
    return json.dumps({k: v for k, v in rec.items() if k not in ("prev_hash", "entry_hash")},
                      sort_keys=True, ensure_ascii=False)


def _record_hash(key: bytes, prev_hash: str, payload: str) -> str:
    return hmac.new(key, (prev_hash + payload).encode("utf-8"), hashlib.sha256).hexdigest()


def _last_hash(fh) -> str:
    try:
        fh.seek(0)
        last = None
        for line in fh:
            line = line.strip()
            if line:
                last = line
        if not last:
            return _GENESIS
        return json.loads(last).get("entry_hash", _GENESIS)
    except Exception:
        return _GENESIS


def write_event(**rec) -> None:
    """Append one HMAC-chained ledger record. Never raises; degrades to an unchained append on failure."""
    rec.setdefault("ts", datetime.now(timezone.utc).isoformat())
    try:
        d = os.path.dirname(LOG_PATH)
        if d:
            os.makedirs(d, exist_ok=True)
        key = _load_or_create_key()
        with open(LOG_PATH, "a+", encoding="utf-8") as f:
            if fcntl:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                if key:
                    prev = _last_hash(f)
                    eh = _record_hash(key, prev, _payload(rec))
                    rec["prev_hash"] = prev
                    rec["entry_hash"] = eh
                else:
                    rec["_unchained"] = True
                f.seek(0, os.SEEK_END)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
            finally:
                if fcntl:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception:
        try:  # last resort: never lose the event, never raise
            rec.setdefault("_unchained", True)
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass


def verify_chain(path: str | None = None):
    """Recompute the HMAC chain. Return (ok, first_bad_index_or_None, detail)."""
    path = path or LOG_PATH
    key = _load_or_create_key()
    if not key:
        return (False, None, "no valid HMAC key")
    try:
        with open(path, encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
    except FileNotFoundError:
        return (True, None, "no ledger yet")
    prev = _GENESIS
    for i, ln in enumerate(lines):
        try:
            rec = json.loads(ln)
        except Exception:
            return (False, i, "unparseable record")
        if rec.get("_unchained"):
            return (False, i, "unchained record (chain gap)")
        if rec.get("prev_hash") != prev:
            return (False, i, "prev_hash mismatch (record inserted or deleted)")
        if _record_hash(key, prev, _payload(rec)) != rec.get("entry_hash"):
            return (False, i, "entry_hash mismatch (record altered)")
        prev = rec.get("entry_hash")
    return (True, None, f"{len(lines)} records verified")
