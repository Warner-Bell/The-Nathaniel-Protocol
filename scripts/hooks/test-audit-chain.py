#!/usr/bin/env python3
"""test-audit-chain.py - rung-1 control for the HMAC audit chain (audit_common, steal-list #14).

Positive control: a clean chain verifies. Negative controls: an altered record and a deleted
record are both caught. Mirrors the Aug-8 feasibility proof (clean verifies True, tampered True).
Run: python3 scripts/hooks/test-audit-chain.py   (exit 0 = all pass)
"""
import os
import sys
import json
import tempfile
import importlib

sys.path.insert(0, os.path.dirname(__file__))


def main():
    tmp = tempfile.mkdtemp()
    led = os.path.join(tmp, "led.jsonl")
    key = os.path.join(tmp, "k.key")
    os.environ["NATE_AUDIT_LOG"] = led
    os.environ["NATE_AUDIT_KEY"] = key
    import audit_common
    importlib.reload(audit_common)  # pick up the temp paths (module-level at import)

    p = f = 0
    fails = []

    def ck(name, cond):
        nonlocal p, f
        if cond:
            p += 1
        else:
            f += 1
            fails.append("  FAIL " + name)

    audit_common.write_event(event_type="executed", tool="execute_bash", args_summary="ls -la", outcome="completed")
    audit_common.write_event(event_type="blocked", tool="execute_bash", args_summary="cat Life/.secrets/x", outcome="blocked", rule_id="KS-SECRET-BASH")
    audit_common.write_event(event_type="executed", tool="fs_write", args_summary="Development/x.py", outcome="completed")

    ok, idx, detail = audit_common.verify_chain()
    ck("clean chain verifies (positive control)", ok)
    ck("3 records counted", "3 records" in detail)
    ck("key created >=32B", os.path.exists(key) and os.path.getsize(key) >= 32)

    # negative control 1: alter record index 1
    lines = open(led).read().splitlines()
    rec = json.loads(lines[1]); rec["args_summary"] = "TAMPERED"; lines[1] = json.dumps(rec)
    open(led, "w").write("\n".join(lines) + "\n")
    ok2, idx2, _ = audit_common.verify_chain()
    ck("alteration caught at idx 1 (negative control)", (not ok2) and idx2 == 1)

    # negative control 2: delete a record
    lines2 = open(led).read().splitlines(); del lines2[1]
    open(led, "w").write("\n".join(lines2) + "\n")
    ok3, _, _ = audit_common.verify_chain()
    ck("deletion caught (negative control)", not ok3)

    print(f"audit-chain: {p} passed, {f} failed")
    for x in fails:
        print(x)
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
