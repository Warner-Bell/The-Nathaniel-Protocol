#!/usr/bin/env python3
"""test-gate-grant.py - regression suite for gate_grant.py.

Every case asserts the FAIL-CLOSED contract: anything other than a well-formed, in-scope,
unexpired, reasoned, TTL-capped grant must yield no bypass. A false positive here silently
disarms the denylist floor, so the negative cases matter more than the positive one.

Run: python3 scripts/hooks/test-gate-grant.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_grant  # noqa: E402

NOW = datetime(2026, 9, 14, 15, 0, 0, tzinfo=timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat()


def write_grant(tmpdir: Path, payload, raw_text: str | None = None) -> Path:
    p = tmpdir / "gate-grant.json"
    p.write_text(raw_text if raw_text is not None else json.dumps(payload), encoding="utf-8")
    return p


# (name, payload_or_None, raw_text_or_None, rule_id, expect_covered)
CASES = [
    # --- the one positive case ---
    ("valid grant covers its named rule",
     {"scope": ["KS-SECRET-PATH"], "expires": iso(NOW + timedelta(hours=2)), "reason": "vault reorg"},
     None, "KS-SECRET-PATH", True),

    # --- scoping: a grant must not leak to rules it did not name ---
    ("valid grant does NOT cover an unnamed rule",
     {"scope": ["KS-SECRET-PATH"], "expires": iso(NOW + timedelta(hours=2)), "reason": "vault reorg"},
     None, "KS-KEYSTONE", False),
    ("multi-rule scope covers each named rule",
     {"scope": ["KS-SECRET-PATH", "KS-KEYSTONE"], "expires": iso(NOW + timedelta(hours=1)), "reason": "gate maintenance"},
     None, "KS-KEYSTONE", True),

    # --- expiry ---
    ("expired grant does not cover",
     {"scope": ["KS-SECRET-PATH"], "expires": iso(NOW - timedelta(minutes=1)), "reason": "stale window"},
     None, "KS-SECRET-PATH", False),
    ("expiry exactly now does not cover (boundary)",
     {"scope": ["KS-SECRET-PATH"], "expires": iso(NOW), "reason": "boundary"},
     None, "KS-SECRET-PATH", False),
    ("TTL beyond MAX_TTL_HOURS is rejected",
     {"scope": ["KS-SECRET-PATH"], "expires": iso(NOW + timedelta(hours=gate_grant.MAX_TTL_HOURS + 1)), "reason": "too long"},
     None, "KS-SECRET-PATH", False),
    ("far-future typo (2099) is rejected",
     {"scope": ["KS-SECRET-PATH"], "expires": "2099-01-01T00:00:00+00:00", "reason": "typo"},
     None, "KS-SECRET-PATH", False),
    ("naive timestamp is treated as UTC and still works",
     {"scope": ["KS-SECRET-PATH"], "expires": (NOW + timedelta(hours=1)).replace(tzinfo=None).isoformat(), "reason": "naive ts"},
     None, "KS-SECRET-PATH", True),
    ("missing expires is rejected",
     {"scope": ["KS-SECRET-PATH"], "reason": "no expiry"},
     None, "KS-SECRET-PATH", False),
    ("unparseable expires is rejected",
     {"scope": ["KS-SECRET-PATH"], "expires": "next tuesday", "reason": "bad ts"},
     None, "KS-SECRET-PATH", False),

    # --- wildcards: "everything" is what NATE_DENYLIST=off is for ---
    ("wildcard scope * is rejected",
     {"scope": ["*"], "expires": iso(NOW + timedelta(hours=1)), "reason": "everything"},
     None, "KS-SECRET-PATH", False),
    ("wildcard scope ALL is rejected",
     {"scope": ["ALL"], "expires": iso(NOW + timedelta(hours=1)), "reason": "everything"},
     None, "KS-KEYSTONE", False),

    # --- shape ---
    ("empty scope is rejected",
     {"scope": [], "expires": iso(NOW + timedelta(hours=1)), "reason": "empty"},
     None, "KS-SECRET-PATH", False),
    ("scope as a bare string is rejected",
     {"scope": "KS-SECRET-PATH", "expires": iso(NOW + timedelta(hours=1)), "reason": "wrong type"},
     None, "KS-SECRET-PATH", False),
    ("non-string scope member is rejected",
     {"scope": ["KS-SECRET-PATH", 42], "expires": iso(NOW + timedelta(hours=1)), "reason": "mixed types"},
     None, "KS-SECRET-PATH", False),
    ("top-level list instead of object is rejected",
     ["KS-SECRET-PATH"],
     None, "KS-SECRET-PATH", False),

    # --- accountability: an unexplained bypass is not auditable ---
    ("missing reason is rejected",
     {"scope": ["KS-SECRET-PATH"], "expires": iso(NOW + timedelta(hours=1))},
     None, "KS-SECRET-PATH", False),
    ("blank reason is rejected",
     {"scope": ["KS-SECRET-PATH"], "expires": iso(NOW + timedelta(hours=1)), "reason": "   "},
     None, "KS-SECRET-PATH", False),

    # --- corruption must never open the gate ---
    ("malformed JSON is rejected (fail closed)",
     None, "{this is not json", "KS-SECRET-PATH", False),
    ("empty file is rejected",
     None, "", "KS-SECRET-PATH", False),

    # --- caller hygiene ---
    ("empty rule id never matches",
     {"scope": ["KS-SECRET-PATH"], "expires": iso(NOW + timedelta(hours=1)), "reason": "ok"},
     None, "", False),

    # --- NEVER_GRANTABLE: the self-amplifying rule cannot be bypassed even if named ---
    ("KS-GRANT-SELF cannot be granted even when explicitly named",
     {"scope": ["KS-GRANT-SELF"], "expires": iso(NOW + timedelta(hours=1)), "reason": "self-renew attempt"},
     None, "KS-GRANT-SELF", False),
    ("a scope of ONLY KS-GRANT-SELF yields no grant at all",
     {"scope": ["KS-GRANT-SELF"], "expires": iso(NOW + timedelta(hours=1)), "reason": "self-renew attempt"},
     None, "KS-SECRET-PATH", False),
    ("KS-GRANT-SELF is stripped but a co-named legitimate rule still works",
     {"scope": ["KS-GRANT-SELF", "KS-SECRET-PATH"], "expires": iso(NOW + timedelta(hours=1)), "reason": "mixed scope"},
     None, "KS-SECRET-PATH", True),
    ("...and the stripped rule is still not covered in that mixed grant",
     {"scope": ["KS-GRANT-SELF", "KS-SECRET-PATH"], "expires": iso(NOW + timedelta(hours=1)), "reason": "mixed scope"},
     None, "KS-GRANT-SELF", False),
]


def main() -> int:
    passed = failed = 0

    for name, payload, raw, rule_id, expect in CASES:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            path = write_grant(tmp, payload, raw)
            got = gate_grant.grant_covers(rule_id, now=NOW, path=path)
        ok = got == expect
        passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)
        print(f"  {'PASS' if ok else 'FAIL'}  {name}"
              + ("" if ok else f"   (expected {expect}, got {got})"))

    # missing file: the common case, must be a clean no-grant
    with tempfile.TemporaryDirectory() as td:
        missing = Path(td) / "does-not-exist.json"
        got = gate_grant.grant_covers("KS-SECRET-PATH", now=NOW, path=missing)
        ok = got is False
        passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)
        print(f"  {'PASS' if ok else 'FAIL'}  missing grant file is a clean no-grant")

    # a directory where the file should be: unreadable, must fail closed
    with tempfile.TemporaryDirectory() as td:
        as_dir = Path(td) / "gate-grant.json"
        as_dir.mkdir()
        got = gate_grant.grant_covers("KS-SECRET-PATH", now=NOW, path=as_dir)
        ok = got is False
        passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)
        print(f"  {'PASS' if ok else 'FAIL'}  unreadable path (dir) fails closed")

    print(f"\ngate-grant regression: {passed} passed, {failed} failed  ({passed + failed} cases)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
