#!/usr/bin/env python3
"""PreToolUse gate: every outbound email (send / reply / forward) asks the user first.
WHY
  Email MCP servers (one per mailbox, tool names like email_send or work_email_reply) expose
  send, reply and forward. Outbound email should never leave without the user seeing it,
  and a behavioral rule alone does not enforce that. This gate asks instead of blocking,
  so a send the user wants still goes, one confirmation at a time. With no email MCP
  configured it never matches and does nothing.
WHAT IT MATCHES
  Tool names, or a `tool_id` / `tool_name` argument when tools are invoked through a
  wrapper (deferred tools arrive as `tool_call` with tool_input.tool_id), ending in
  [prefix_]email_send / email_reply / email_forward. Drafts, reads, search, move,
  mark-read and setup pass untouched.

OUTPUT
  Match: exit 0 with {"hookSpecificOutput": {"permissionDecision": "ask", ...}} on stdout,
  so the runtime prompts the user. No match: exit 0, no output.
  Unreadable payload: exit 0, no output (fail open on a gate bug, same convention as the
  denylist floor; the decision applies only to matched email tools, never to everything).

Usage (hook): python3 scripts/email-send-gate.py < payload.json
Self-test:    python3 scripts/email-send-gate.py --self-test
"""
import json
import re
import sys

SEND_RE = re.compile(r"(?:^|[:/_@-])(?:[a-z0-9]+_)?email_(send|reply|forward)$")


def target_tool(payload):
    """The real tool name: the wrapper's tool_id when present, else the tool name."""
    ti = payload.get("tool_input") or {}
    for key in ("tool_id", "tool_name", "name"):
        if isinstance(ti, dict) and isinstance(ti.get(key), str) and ti.get(key):
            return ti[key], ti.get("arguments") or {}
    return str(payload.get("tool_name") or ""), ti


def decide(payload):
    tool, args = target_tool(payload)
    m = SEND_RE.search(tool)
    if not m:
        return None
    to = args.get("to") or args.get("recipients") or args.get("message_id") or "?"
    subj = str(args.get("subject") or "")[:80]
    reason = (f"Outbound email ({m.group(1)}) via {tool}: to {to}"
              + (f", subject \"{subj}\"" if subj else "")
              + ". User approval required for every send (outbound email gate).")
    return {"hookSpecificOutput": {"permissionDecision": "ask", "permissionDecisionReason": reason}}


def _self_test():
    cases = [
        ({"tool_name": "email::email_send", "tool_input": {"to": "a@b.c"}}, True),
        ({"tool_name": "tool_call", "tool_input": {"tool_id": "email-work::work_email_reply", "arguments": {}}}, True),
        ({"tool_name": "@email-home/home_email_forward"}, True),
        ({"tool_name": "tool_call", "tool_input": {"tool_id": "email-work::work_email_create_draft"}}, False),
        ({"tool_name": "email::email_list_unread"}, False),
        ({"tool_name": "tool_call", "tool_input": {"tool_id": "time::get_current_time"}}, False),
        ({"tool_name": "execute_bash", "tool_input": {"command": "echo email_send"}}, False),
    ]
    bad = 0
    for payload, want in cases:
        got = decide(payload) is not None
        bad += got != want
        print(f"  [{'ok' if got == want else 'FAIL'}] {json.dumps(payload)[:90]} -> {'ask' if got else 'pass'}")
    print("PASS" if not bad else f"FAIL ({bad})")
    return 1 if bad else 0


def main():
    if "--self-test" in sys.argv:
        return _self_test()
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    out = decide(payload) if isinstance(payload, dict) else None
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
