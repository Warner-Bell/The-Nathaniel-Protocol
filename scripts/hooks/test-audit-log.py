#!/usr/bin/env python3
"""test-audit-log.py - regression suite for the H1 audit writer (audit_log.py).

Verifies: exit is ALWAYS 0 (observe-only); a well-formed 'executed' record is appended;
credentials are REDACTED in args_summary (G1); NATE_AUDIT=off writes nothing.
Run: python3 scripts/hooks/test-audit-log.py   (exit 0 = all pass)
"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "audit_log.py")


def run_hook(event, mode="on", logpath=None):
    env = dict(os.environ, NATE_AUDIT=mode)
    if logpath:
        env["NATE_AUDIT_LOG"] = logpath
    return subprocess.run([sys.executable, HOOK], input=json.dumps(event),
                          capture_output=True, text=True, env=env)


def ev(tool, ti, resp=None):
    return {"hook_event_name": "postToolUse", "tool_name": tool, "tool_input": ti,
            "tool_response": resp or {"success": True}}


def read_log(p):
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return [json.loads(x) for x in f if x.strip()]


def main():
    passed, failed, fails = 0, 0, []

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            fails.append(f"  FAIL [{name}]")

    tmp = tempfile.mkdtemp()

    # 1. normal executed event -> exit 0 + one well-formed record
    lp = os.path.join(tmp, "a1.jsonl")
    r = run_hook(ev("execute_bash", {"command": "ls -la"}), logpath=lp)
    recs = read_log(lp)
    check("exit 0 on normal", r.returncode == 0)
    check("one record written", len(recs) == 1)
    check("record shape", recs and recs[0].get("event_type") == "executed" and recs[0].get("tool") == "execute_bash" and "ts" in recs[0])

    # 2. failed tool_response -> outcome failed
    lp = os.path.join(tmp, "a2.jsonl")
    r = run_hook(ev("execute_bash", {"command": "false"}, {"success": False}), logpath=lp)
    recs = read_log(lp)
    check("outcome failed", recs and recs[0].get("outcome") == "failed")

    # 3. REDACTION: a literal secret in args must not land in the ledger
    lp = os.path.join(tmp, "a3.jsonl")
    r = run_hook(ev("execute_bash", {"command": "export KIRO_API_KEY=sk-supersecret12345"}), logpath=lp)
    recs = read_log(lp)
    blob = json.dumps(recs)
    check("exit 0 with secret", r.returncode == 0)
    check("secret redacted", "sk-supersecret12345" not in blob)
    check("redaction marker present", "<REDACTED>" in blob or "REDACTED" in blob)

    # 4. NATE_AUDIT=off -> nothing written, exit 0
    lp = os.path.join(tmp, "a4.jsonl")
    r = run_hook(ev("fs_write", {"path": "x.py"}), mode="off", logpath=lp)
    check("off exit 0", r.returncode == 0)
    check("off writes nothing", read_log(lp) == [])

    # 5. malformed event -> exit 0 (fail-open)
    env = dict(os.environ, NATE_AUDIT="on", NATE_AUDIT_LOG=os.path.join(tmp, "a5.jsonl"))
    r = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, env=env)
    check("malformed exit 0", r.returncode == 0)

    print(f"audit-log regression: {passed} passed, {failed} failed")
    for line in fails:
        print(line)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
