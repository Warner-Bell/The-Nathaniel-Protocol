#!/usr/bin/env python3
"""denylist.py - deterministic preToolUse denylist floor beneath the behavioral DAG.

=== MODULE MANIFEST (anti-dark-code, dev-protocol Directive 2) ===
WHAT  Reads a Kiro `preToolUse` hook event (JSON on stdin), evaluates tool_name +
      tool_input against a tiered keystone catalog, and exits 2 to BLOCK (Kiro hard-stops
      the tool) or 0 to ALLOW.
WHY   The Destructive Action Gate is behavioral (Operating Principle 1: non-deterministic).
      This is the structural floor a drifting/compromised agent cannot reason past.
HOW   Wired as a PreToolUse command hook in .kiro/hooks/safety-floor.json for matchers
      execute_bash / read / write / use_aws. Kiro sends {tool_name, tool_input} on stdin.

MODES (env NATE_DENYLIST):
      "enforce" (default) - block on match for enforce-tier rules
      "log"               - never block; record would-blocks to the log (bake-in)
      "off"               - allow everything (kill switch, no hook-file edit needed)

PER-RULE TIER: each rule is "enforce" or "log". Even in global enforce mode, a "log"
      rule only records (used for S3 rules until the bucket allowlist is confirmed).

FAIL-OPEN: any internal error -> exit 0 (allow) + stderr note. A crashing floor must not
      brick tool use; the behavioral DAG still covers intent. Only an explicit rule match
      in an enforce-tier rule under enforce/global mode blocks.
"""
from __future__ import annotations
import sys
import os
import re
import json


MODE = os.environ.get("NATE_DENYLIST", "enforce").strip().lower()

# --- Unambiguous protected secret locations (tight, low false-positive) ---
# The .secrets clause is NAME-based and depth-agnostic by design: any directory named
# .secrets anywhere in the repo is protected. This matches the per-asset .secrets convention
# so a new store is covered the moment it exists.
# DO NOT replace this with specific store paths. Hardcoding the single known store
# is how secret stores end up unguarded when a new one is added;
# a general name clause cannot drift when a store is added or moved.
SECRET_PATH_RE = re.compile(
    r"(\.secrets)"
    r"|(\.ssh/[^/\s]*(id_rsa|id_dsa|id_ecdsa|id_ed25519|_rsa|_ed25519|\.pem))"
    r"|(\.aws/credentials)"
    r"|(\.gnupg)"
    r"|((^|/)tokens/)"
    r"|(\.?git-credentials)"
    r"|(nate-audit\.jsonl)"
    r"|(nate-audit-hmac\.key)"
    r"|(denylist-events\.jsonl)"
)
# bash verbs that read/move/transmit file contents
SECRET_ACCESS_VERB_RE = re.compile(r"(\bcat\b|\bless\b|\bhead\b|\btail\b|\bcp\b|\bmv\b|\btee\b|\bscp\b|\brsync\b|\bsed\b|\bawk\b|\bxxd\b|\bbase64\b|\bdd\b|>|>>)")
ENVCRED_RE = re.compile(r"\b(echo|printenv)\b.*(AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN|AWS_ACCESS_KEY_ID|KIRO_API_KEY)")
IMDS_RE = re.compile(r"169\.254\.169\.254")
S3_WRITE_BASH_RE = re.compile(r"\baws\s+s3\s+(cp|mv|sync)\b")
RMRF_RE = re.compile(r"\brm\s+(-\w*r\w*f\w*|-\w*f\w*r\w*|-rf|-fr)\b")
RMRF_PROTECTED_RE = re.compile(r"(\s/(\s|$))|(\s~(\s|/|$))|(\$HOME)|(\.secrets)|(Nate's-kb)|(\s\*(\s|$))")
S3_ALLOW_PREFIXES = ()  # Add your own bucket-name prefixes. S3 rules are log-tier until you do.
S3_WRITE_OPS = {"putobject", "copyobject", "uploadpart", "putobjectacl", "createmultipartupload"}
# OOB failure-catalog tier (narrow, per Route F). find at absolute root hangs, never legit.
FIND_ROOT_RE = re.compile(r"\bfind\s+/(\s|$)")
# Long-running dev servers/watchers (log-tier only; behavioral refusal is primary; tight to avoid FP on systemctl/docker start / npm run build).
LONGRUN_RE = re.compile(r"(npm run dev|npm start|yarn (dev|start)|pnpm (dev|start)|next dev|vite(\s|$)|nodemon|manage\.py runserver|--watch\b)")
# Gate self-protection (#16 keystone): the agent must not REWRITE its own hook wiring
# (.kiro/agents/*.json) or gate code (denylist/audit_common/audit_log). Reading is fine;
# only writes disarm. Legit gate maintenance = deliberately flip the kill switch
# (NATE_DENYLIST=off), an owner-visible act. This is what stops a drifting/compromised
# agent from silently editing away its own deny+audit floor.
GATE_PATH_RE = re.compile(
    r"(\.kiro/agents/[^/\s]+\.json)"
    r"|(\.kiro/hooks/[^/\s]+\.json)"
    r"|(scripts/hooks/(denylist|audit_common|audit_log|gate_grant|preflight|source-authority)\.py)"
    r"|((^|/)\.nathaniel/gate-grant\.json)"
)
# write verbs only (reads of the gate are allowed; only writes disarm). `rm` counts: deleting
# gate code changes gate state exactly as a write does, and RMRF_RE cannot cover it because
# that rule requires BOTH -r and -f. Found 2026-09-14 when `rm -f scripts/hooks/denylist.py`
# matched no rule at all. Word-bounded on purpose: `npm`, `confirm`, `perms` must not match.
GATE_WRITE_VERB_RE = re.compile(r"(\btee\b|\bsed\b|\bmv\b|\bcp\b|\bdd\b|\brm\b|(?<![0-9&-])>(?!&))")
# Owner grant helper: the agent must never execute it (self-authorisation). A plain string
# match is sufficient and deliberately broad - there is no legitimate reason for the agent
# to reference the helper by name in a shell command.
GRANT_HELPER_RE = re.compile(r"\bnate-grant\b")


def bash_cmd(ti) -> str:
    if isinstance(ti, dict):
        return str(ti.get("command", ""))
    return str(ti or "")


def fs_paths(ti):
    out = []
    if isinstance(ti, dict):
        for op in (ti.get("operations") or []):
            if isinstance(op, dict) and op.get("path"):
                out.append(str(op["path"]))
        if ti.get("path"):
            out.append(str(ti["path"]))
    return out


def _s3_allowlisted(blob: str) -> bool:
    for m in re.finditer(r"s3://([^/\s\"']+)", blob):
        bucket = m.group(1)
        if not any(bucket.startswith(p) for p in S3_ALLOW_PREFIXES):
            return False  # at least one non-allowlisted bucket target
    return True


# Rule = (id, tier, predicate(tool_name, tool_input) -> bool, reason)
RULES = [
    ("KS-SECRET-PATH", "enforce",
     lambda tn, ti: tn in ("fs_read", "fs_write") and any(SECRET_PATH_RE.search(p) for p in fs_paths(ti)),
     "fs tool touching a protected secret path"),
    ("KS-SECRET-BASH", "enforce",
     lambda tn, ti: tn == "execute_bash" and bool(SECRET_PATH_RE.search(bash_cmd(ti))) and bool(SECRET_ACCESS_VERB_RE.search(bash_cmd(ti))),
     "bash read/move/transmit of a protected secret path"),
    ("KS-KEYSTONE", "enforce",
     lambda tn, ti: tn == "fs_write" and any(GATE_PATH_RE.search(p) for p in fs_paths(ti)),
     "fs_write to the agent's own gate wiring/code (self-disarm; set NATE_DENYLIST=off for deliberate gate maintenance)"),
    ("KS-KEYSTONE-BASH", "enforce",
     lambda tn, ti: tn == "execute_bash" and bool(GATE_PATH_RE.search(bash_cmd(ti))) and bool(GATE_WRITE_VERB_RE.search(bash_cmd(ti))),
     "bash write/move to the agent's own gate wiring/code (self-disarm)"),
    ("KS-GRANT-SELF", "enforce",
     lambda tn, ti: tn == "execute_bash" and bool(GRANT_HELPER_RE.search(bash_cmd(ti))),
     "agent attempting to run the owner grant helper (self-authorisation)"),
    ("KS-ENVCRED", "enforce",
     lambda tn, ti: tn == "execute_bash" and bool(ENVCRED_RE.search(bash_cmd(ti))),
     "shell echo/printenv of a credential env var"),
    ("KS-IMDS", "enforce",
     lambda tn, ti: tn == "execute_bash" and bool(IMDS_RE.search(bash_cmd(ti))),
     "access to instance metadata service (169.254.169.254)"),
    ("KS-RMRF", "enforce",
     lambda tn, ti: tn == "execute_bash" and bool(RMRF_RE.search(bash_cmd(ti))) and bool(RMRF_PROTECTED_RE.search(bash_cmd(ti))),
     "rm -rf targeting a protected or overly broad path"),
    ("KS-FIND-ROOT", "enforce",
     lambda tn, ti: tn == "execute_bash" and bool(FIND_ROOT_RE.search(bash_cmd(ti))),
     "find at absolute filesystem root (hangs; never legitimate from the agent)"),
    # S3 exfil rules: LOG tier until the bucket allowlist is confirmed (avoid blocking legit uploads)
    ("KS-S3-BASH", "log",
     lambda tn, ti: tn == "execute_bash" and bool(S3_WRITE_BASH_RE.search(bash_cmd(ti))) and "s3://" in bash_cmd(ti) and not _s3_allowlisted(bash_cmd(ti)),
     "aws s3 write to a non-allowlisted bucket (possible exfil)"),
    ("KS-S3-USEAWS", "log",
     lambda tn, ti: tn == "use_aws" and isinstance(ti, dict) and str(ti.get("service", "")).lower() == "s3"
        and str(ti.get("operation", "")).lower() in S3_WRITE_OPS and not _s3_allowlisted(json.dumps(ti)),
     "use_aws S3 write to a non-allowlisted bucket (possible exfil)"),
    ("KS-LONGRUN", "log",
     lambda tn, ti: tn == "execute_bash" and bool(LONGRUN_RE.search(bash_cmd(ti))),
     "long-running dev server/watcher (behavioral refusal is primary; log-tier observation only)"),
]


def evaluate(tool_name: str, tool_input) -> tuple[bool, str, str]:
    """Return (should_block, rule_id, reason). Pure; no I/O. Used by the harness too."""
    for rid, tier, pred, reason in RULES:
        try:
            if pred(tool_name, tool_input):
                # a "log"-tier rule never blocks; an "enforce" rule blocks only in enforce mode
                should_block = (tier == "enforce" and MODE == "enforce")
                return should_block, rid, reason
        except Exception:
            continue  # a broken rule must not brick tool use
    return False, "", ""


def main() -> int:
    if MODE == "off":
        return 0
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception as e:
        sys.stderr.write(f"denylist: could not parse hook event ({e}); allowing (fail-open)\n")
        return 0
    tool_name = str(event.get("tool_name", ""))
    tool_input = event.get("tool_input", {})
    should_block, rid, reason = evaluate(tool_name, tool_input)

    # Owner grant check, deliberately at the edge and not inside evaluate() (which is pure
    # and harness-tested). ANY failure here - missing module, unreadable grant, bad JSON -
    # leaves should_block untouched, i.e. fail CLOSED. This is the opposite of this file's
    # global fail-open posture, and intentionally so: a corrupted grant must not disarm.
    grant_note = ""
    if should_block and rid:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from gate_grant import grant_covers, describe
            if grant_covers(rid):
                should_block = False
                grant_note = f" [owner grant: {describe()}]"
        except Exception:
            pass  # keep enforcing

    if rid:  # a rule matched (blocked, log-tier, or owner-granted) -> record to the ledger
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from audit_common import write_event, summarize
            write_event(event_type=("blocked" if should_block
                                    else ("granted" if grant_note else "logged")),
                        tool=tool_name, args_summary=summarize(tool_input),
                        outcome=("blocked" if should_block else "allowed"),
                        rule_id=rid, reason=reason + grant_note)
        except Exception:
            pass  # logging must never affect the block decision
        if should_block:
            sys.stderr.write(f"DENYLIST[{rid}]: blocked - {reason}\n")
            return 2
        if grant_note:
            sys.stderr.write(f"DENYLIST[{rid}]: allowed by owner grant -{grant_note}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
