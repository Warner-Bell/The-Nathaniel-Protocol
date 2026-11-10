#!/usr/bin/env python3
"""audit_log.py - postToolUse audit writer (H1).

Appends one 'executed' record per state-changing tool call to the shared ledger
(audit_common). Observe-only: ALWAYS exits 0 (postToolUse cannot block; fail-open).
Wired in .kiro/hooks/safety-floor.json for matchers execute_bash / fs_write / use_aws (reads excluded:
high volume, low forensic value). Modes: env NATE_AUDIT on (default) / off.
"""
from __future__ import annotations
import sys
import os
import json

# scripts/hooks is on sys.path[0] when run as `python3 scripts/hooks/audit_log.py`
try:
    from audit_common import write_event, summarize
except Exception:
    write_event = None  # fail-open: no ledger write, tool still runs


def main() -> int:
    if os.environ.get("NATE_AUDIT", "on").strip().lower() == "off" or write_event is None:
        return 0
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0
    try:
        tool = str(event.get("tool_name", ""))
        tool_input = event.get("tool_input", {})
        resp = event.get("tool_response", {})
        outcome = "completed" if (not isinstance(resp, dict) or resp.get("success", True)) else "failed"
        write_event(event_type="executed", tool=tool, args_summary=summarize(tool_input), outcome=outcome)
    except Exception:
        pass  # observe-only: never affect tool execution
    return 0


if __name__ == "__main__":
    sys.exit(main())
