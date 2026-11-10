#!/usr/bin/env python3
"""gate_grant.py - owner-authored, scoped, self-expiring bypass grants for the denylist floor.

=== MODULE MANIFEST (anti-dark-code, dev-protocol Directive 2) ===
WHAT  Reads an owner-authored grant file and answers one question: is rule <ID> currently
      bypassed by an active, valid, unexpired owner grant?
WHY   `NATE_DENYLIST=off` is the only existing owner-auth mechanism and it is too crude:
      all-or-nothing (drops KS-SECRET-PATH along with the keystone rules), requires a
      relaunch, and cannot persist across sessions. The owner asked for a command-password
      bypass instead; a password would live in agent context, the transcript, and
      Memory/recall/conversations.md, and would hand prompt injection a disarm path that
      does not exist today. A file the owner writes and the agent cannot write preserves
      the asymmetry that IS the security property.
HOW   The hook runs as a separate process, so it reads the grant freely. The agent is
      blocked from authoring one by two denylist rules (see PREREQUISITES). Grants are
      scoped to explicit rule IDs, capped at MAX_TTL_HOURS, and fail CLOSED.

FAIL-CLOSED, deliberately inverted vs denylist.py. denylist.py fails OPEN because a
      crashing floor must not brick tool use. A grant reader must do the opposite: any
      malformed, unreadable, unparseable, over-long or expired grant yields NO grant, so
      the floor keeps enforcing. Failing open here would mean a corrupted file silently
      disarms the gate.

PREREQUISITES (owner action, cannot be self-applied - both are gate code):
  1. denylist.py: add GRANT_PATH_RE to the gate-path guard so the agent cannot WRITE the
     grant file (reads stay allowed on purpose: knowing what is authorised is useful and
     leaks nothing - a scope list is not a secret).
  2. denylist.py: add rule KS-GRANT-SELF blocking execute_bash whose command references the
     grant helper or the grant path with any write verb. Without this, the agent can run
     the helper and grant itself, which defeats the entire design.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Owner-authored grant location. Outside the repo, alongside the email token vault
# (~/.nathaniel/ is already the established out-of-repo secret dir per security-protocol.md).
GRANT_PATH = Path(os.environ.get("NATE_GRANT_PATH", Path.home() / ".nathaniel" / "gate-grant.json"))

# Hard ceiling on grant lifetime. Protects against an owner typo (expires: 2099) turning a
# temporary window into a permanent hole. A longer window means re-authoring, which is the
# point: a bypass should be a deliberate, repeated act.
MAX_TTL_HOURS = 24

# Rules a grant may never cover, even if the owner names them explicitly.
# KS-GRANT-SELF guards the grant helper itself: if a grant could bypass it, the agent could
# run the helper and renew its own grant indefinitely, which converts a 24h window into a
# permanent one. That is the one rule whose bypass is self-amplifying, so it is excluded
# structurally rather than by convention.
# Note the corollary: gate_grant.py must itself be added to denylist's GATE_PATH_RE, or the
# agent can simply edit this constant away. See PREREQUISITES.
NEVER_GRANTABLE: frozenset[str] = frozenset({"KS-GRANT-SELF"})


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_expiry(raw) -> datetime | None:
    """Parse an ISO-8601 expiry. Naive timestamps are treated as UTC."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        dt = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def active_grant(now: datetime | None = None, path: Path | None = None) -> dict | None:
    """Return the active grant as a dict, or None.

    None is returned for every failure mode: missing file, unreadable file, bad JSON, wrong
    shape, empty scope, wildcard scope, missing/invalid expiry, already expired, or a TTL
    exceeding MAX_TTL_HOURS. Callers may treat None as "enforce normally".
    """
    now = now or _now()
    path = path or GRANT_PATH

    try:
        if not path.is_file():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None  # fail closed

    if not isinstance(raw, dict):
        return None

    scope = raw.get("scope")
    if not isinstance(scope, list) or not scope:
        return None
    if not all(isinstance(s, str) and s.strip() for s in scope):
        return None
    # No wildcards. A grant must name the rules it bypasses; "everything" is what
    # NATE_DENYLIST=off is for, and that is a deliberate relaunch-scoped act.
    if any(s.strip() in ("*", "ALL", "all") for s in scope):
        return None

    expires = _parse_expiry(raw.get("expires"))
    if expires is None or expires <= now:
        return None
    if expires - now > timedelta(hours=MAX_TTL_HOURS):
        return None  # over-long grant is a typo or an attack, not a window

    reason = raw.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        return None  # an unexplained bypass is not auditable, so it is not a grant

    granted = [s.strip() for s in scope if s.strip() not in NEVER_GRANTABLE]
    if not granted:
        return None

    return {"scope": granted, "expires": expires, "reason": reason.strip()}


def grant_covers(rule_id: str, now: datetime | None = None, path: Path | None = None) -> bool:
    """True if an active owner grant bypasses this specific rule id."""
    if not rule_id:
        return False
    grant = active_grant(now=now, path=path)
    return bool(grant and rule_id in grant["scope"])


def describe() -> str:
    """Human-readable one-liner for audit records and agent-visible status."""
    grant = active_grant()
    if not grant:
        return "no active grant"
    remaining = grant["expires"] - _now()
    mins = max(0, int(remaining.total_seconds() // 60))
    return (
        f"grant active: scope={','.join(grant['scope'])} "
        f"expires_in={mins}m reason={grant['reason']!r}"
    )


if __name__ == "__main__":
    print(describe())
