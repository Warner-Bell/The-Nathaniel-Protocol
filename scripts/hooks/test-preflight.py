#!/usr/bin/env python3
"""test-preflight.py - regression suite for scripts/hooks/preflight.py.

Mirrors test-denylist.py: feeds synthetic preToolUse events and asserts the exit code.
The critical cases are the NEGATIVES: a backstop that fires on legitimate content search
is worse than no backstop, because it trains the owner to disable it.

Run: python3 scripts/hooks/test-preflight.py
"""
import json
import os
import subprocess
import sys

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preflight.py")

# (label, mode, tool_name, tool_input, expected_exit)
CASES = [
    # --- POSITIVES: locate-intent for a kernel-known location, enforce tier ---
    ("glob for a protocol file", "enforce", "glob",
     {"pattern": "**/*-protocol.md"}, 2),
    ("glob for the kernel", "enforce", "glob",
     {"pattern": "**/Nathaniel.md"}, 2),
    ("glob for session logs", "enforce", "glob",
     {"pattern": "Nate's-kb/Memory/session-*.md"}, 2),
    ("glob for a store", "enforce", "glob",
     {"pattern": "**/knowledge.json"}, 2),
    ("glob for an index", "enforce", "glob",
     {"pattern": "**/patterns-index.json"}, 2),
    ("bash find -name for a store", "enforce", "execute_bash",
     {"command": "find . -name memory.json"}, 2),
    ("bash find -iname for a protocol", "enforce", "execute_bash",
     {"command": "find . -maxdepth 4 -iname '*-protocol.md'"}, 2),
    ("grep files-only for a store", "enforce", "grep",
     {"pattern": "confidence", "include": "knowledge.json",
      "output_mode": "files_with_matches"}, 2),

    # --- NEGATIVES: must NOT fire ---
    ("grep CONTENT mode in a store (legit content search)", "enforce", "grep",
     {"pattern": "project-tag", "include": "knowledge.json"}, 0),
    ("grep content mode explicit", "enforce", "grep",
     {"pattern": "deposit", "include": "*.md", "output_mode": "content"}, 0),
    ("glob for an unknown//genuinely-unmapped target", "enforce", "glob",
     {"pattern": "**/some-vendor-export-*.csv"}, 0),
    ("bash find WITHOUT a name predicate (inventory)", "enforce", "execute_bash",
     {"command": "find scripts -type d -newermt '-20 minutes'"}, 0),
    ("bash unrelated command", "enforce", "execute_bash",
     {"command": "ls -la .action-items/"}, 0),
    ("unrelated tool", "enforce", "fs_read",
     {"operations": [{"mode": "Line", "path": "Nate's-kb/Nathaniel.md"}]}, 0),
    ("reading a known file by path is fine, not a search", "enforce", "fs_read",
     {"path": "Nate's-kb/Intelligence/knowledge.json"}, 0),

    # --- TIER behaviour ---
    ("log tier never blocks (default)", "log", "glob",
     {"pattern": "**/*-protocol.md"}, 0),
    ("off kill switch", "off", "glob",
     {"pattern": "**/*-protocol.md"}, 0),

    # --- FAIL-OPEN ---
    ("empty event", "enforce", "", {}, 0),
]


def run(mode, tool_name, tool_input):
    env = dict(os.environ)
    env["NATE_PREFLIGHT"] = mode
    payload = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    p = subprocess.run([sys.executable, HOOK], input=payload, text=True,
                       capture_output=True, env=env)
    return p.returncode, (p.stderr or "").strip()


def main():
    passed = failed = 0
    for label, mode, tool, ti, want in CASES:
        got, err = run(mode, tool, ti)
        ok = got == want
        if ok:
            passed += 1
            print(f"  PASS  [{mode:7s}] {label}")
        else:
            failed += 1
            print(f"  FAIL  [{mode:7s}] {label}: expected exit {want}, got {got}")
            if err:
                print(f"        stderr: {err}")

    # malformed stdin must fail open
    env = dict(os.environ); env["NATE_PREFLIGHT"] = "enforce"
    p = subprocess.run([sys.executable, HOOK], input="{not json", text=True,
                       capture_output=True, env=env)
    if p.returncode == 0:
        passed += 1; print("  PASS  [enforce] malformed stdin fails open")
    else:
        failed += 1; print(f"  FAIL  [enforce] malformed stdin: expected 0, got {p.returncode}")

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
