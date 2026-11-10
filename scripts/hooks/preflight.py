#!/usr/bin/env python3
"""preflight.py - preToolUse backstop for Cognitive Pre-Flight (locate-intent tool calls).

=== MODULE MANIFEST (anti-dark-code, dev-protocol Directive 2) ===
WHAT  Reads a Kiro `preToolUse` hook event (JSON on stdin). Detects LOCATE-INTENT tool
      calls (glob, grep in files-only mode, bash `find -name`) whose target is on the
      kernel's own enumerated list of locations that "should never require a search tool".
      Exits 2 to BLOCK with a corrective message, or 0 to ALLOW, per tier.
WHY   Cognitive Pre-Flight is behavioral, therefore non-deterministic (Operating Principle 1).
      It failed observably on 2026-09-10 (a repo-wide search the owner killed as a wild
      goose chase) and is a standing failure class.
      Cross-session lesson: when reliability is the goal, relocate the enforcement
      rather than rewording the instruction. This is that relocation for the locate class.
HOW   Wired as a PreToolUse command hook in .kiro/hooks/safety-floor.json for matchers
      glob / grep / execute_bash. Kiro sends {tool_name, tool_input} on stdin.

SCOPE BOUNDARY - READ THIS BEFORE ASSUMING COVERAGE:
      This closes the LOCATE-INTENT class only. It does NOT and cannot close the
      assertion-without-authority class (SAG), because asserting a claim happens while
      emitting text, and there is no tool call for a preToolUse hook to intercept.
      Do not treat this hook as SAG enforcement.

MODES (env NATE_PREFLIGHT):
      "log"     (DEFAULT) - never block; record would-blocks to the audit ledger.
      "enforce"           - exit 2 and block on match, with a corrective stderr message.
      "off"               - allow everything (kill switch, no config edit needed).

TIER HONESTY: in "log" mode the agent does NOT see anything at the moment of the mistake,
      because only the block path writes to stderr (verified against denylist.py's
      contract). Log mode is drift telemetry for later review, NOT live correction. If the
      goal is to change in-session behaviour, "enforce" is the only mode that reaches the
      agent. That is an owner decision, not the hook's.

FAIL-OPEN: any internal error -> exit 0 (allow) + stderr note. A crashing backstop must
      not brick tool use; the behavioural gate still covers intent.
"""
from __future__ import annotations
import sys
import os
import re
import json

MODE = os.environ.get("NATE_PREFLIGHT", "log").strip().lower()

# --- Targets the kernel explicitly says are known locations -------------------
# These live at fixed, documented places (KB Location Map, FILE-STRUCTURE.md). Searching for
# them proves the pre-flight reasoning step was skipped, because the answer is in
# always-loaded context. Add your own fixed-location files here.
KNOWN_TARGET_RE = re.compile(
    r"(-protocol\.md)"                     # protocols -> Nate's-kb/*.md
    r"|(Nathaniel\.md)"                    # kernel -> .kiro/steering/
    r"|(Nate-Protocol\.md)"
    r"|(session-\*|session-\d{4})"         # session logs -> Nate's-kb/Memory/
    r"|((patterns|knowledge|reasoning|memory|cross-references)\.json)"
    r"|((patterns|knowledge|reasoning|memory|session)-index\.json)"
    r"|(learning-loop\.md)"
    r"|(intelligence-operations\.md)"
    r"|(FILE-STRUCTURE\.md)",
    re.IGNORECASE,
)

# bash locate-intent: `find` with a NAME predicate is looking for WHERE something is.
# `find -newermt` / `-type d` alone are inventory/audit, not locate; left alone.
FIND_BY_NAME_RE = re.compile(r"\bfind\b[^|;]*?\s-i?name\b")


def _tool_input(ev):
    ti = ev.get("tool_input", {})
    return ti if isinstance(ti, dict) else {}


def _blob_glob(ti) -> str:
    return " ".join(str(ti.get(k, "")) for k in ("pattern", "path"))


def _blob_grep(ti) -> str:
    # Only files-only mode is locate-intent. Content mode is legitimate content search
    # and MUST NOT fire (explicit requirement of the approved design).
    if str(ti.get("output_mode", "content")).strip() != "files_with_matches":
        return ""
    return " ".join(str(ti.get(k, "")) for k in ("pattern", "include", "path"))


def evaluate(tool_name: str, ti: dict):
    """Return (should_block, rule_id, reason). Empty rule_id means no match."""
    tool = (tool_name or "").strip()

    if tool == "glob":
        blob = _blob_glob(ti)
    elif tool == "grep":
        blob = _blob_grep(ti)
    elif tool == "execute_bash":
        cmd = str(ti.get("command", ""))
        blob = cmd if FIND_BY_NAME_RE.search(cmd) else ""
    else:
        return (False, "", "")

    if not blob.strip():
        return (False, "", "")

    m = KNOWN_TARGET_RE.search(blob)
    if not m:
        return (False, "", "")

    hit = m.group(0)
    reason = (
        f"locate-intent search for '{hit}', which the kernel's Cognitive Pre-Flight lists "
        f"as a known location. Route from the KB Location Map or FILE-STRUCTURE.md instead "
        f"of searching."
    )
    return (MODE == "enforce", "KS-PREFLIGHT-KNOWN", reason)


def main() -> int:
    if MODE == "off":
        return 0
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception as e:
        sys.stderr.write(f"preflight: could not parse hook event ({e}); allowing (fail-open)\n")
        return 0

    try:
        tool_name = str(event.get("tool_name", ""))
        should_block, rid, reason = evaluate(tool_name, _tool_input(event))
    except Exception as e:
        sys.stderr.write(f"preflight: internal error ({e}); allowing (fail-open)\n")
        return 0

    if rid:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from audit_common import write_event, summarize
            write_event(event_type=("blocked" if should_block else "logged"),
                        tool=tool_name, args_summary=summarize(event.get("tool_input", {})),
                        outcome=("blocked" if should_block else "allowed"),
                        rule_id=rid, reason=reason)
        except Exception:
            pass  # telemetry must never affect the decision
        if should_block:
            sys.stderr.write(f"PREFLIGHT[{rid}]: blocked - {reason}\n")
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
