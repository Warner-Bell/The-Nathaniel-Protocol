#!/usr/bin/env python3
"""source-authority.py - deterministic preToolUse floor under the Source Authority Gate.

=== MODULE MANIFEST (anti-dark-code, dev-protocol Directive 2) ===
WHAT  Reads a Kiro `preToolUse` event (JSON on stdin). Two jobs:
        1) RECORD: when a command reads a live/deployed contract (GraphQL introspection,
           information_schema, a live DB query), stamp a state file.
        2) GATE: when a write would add or change a MODEL CREATE/UPDATE call in a data
           façade, require that such a read happened recently. If not -> exit 2 (BLOCK).
WHY   .kiro/steering/source-authority-gate.md is behavioral, so it is followed
      non-deterministically (Operating Principle 1). On 2026-09-03 the agent guessed a
      deployed AppSync input contract from local migrations, shipped a wrong fix, and
      burned an owner deploy cycle; the KB already held the same lesson twice
      and it still did not fire. This is the structural floor:
      you cannot write a create-input fix without having read the contract.
HOW   Wire as a PreToolUse command hook in .kiro/hooks/safety-floor.json for matchers
      execute_bash / use_aws (record) and fs_write (gate).

MODES (env NATE_SAG):
      "enforce" (default) - block writes with no recent contract read
      "log"               - never block; append would-blocks to the log (bake-in)
      "off"               - allow everything (kill switch, no hook-file edit needed)

SCOPE IS DELIBERATELY NARROW (a floor that over-blocks gets turned off):
      Only fires for writes that touch `models.<X>.create(` / `.update(` inside
      `src/lib/*Api.ts`. Comments, unrelated edits, and every other file are ignored.

FAIL-OPEN: any internal error -> exit 0 (allow) + stderr note. A crashing floor must
      not brick tool use; the steering gate still covers intent.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

MODE = os.environ.get("NATE_SAG", "enforce").strip().lower()

# A contract read is only "fresh" for this long. Long enough to cover a real
# read-then-fix loop, short enough that yesterday's read does not authorise today's guess.
TTL_SECONDS = 2 * 60 * 60

STATE_PATH = os.path.join(
    os.environ.get("TMPDIR", "/tmp"), "nate-sag-contract-reads.json"
)
LOG_PATH = os.path.join(os.environ.get("TMPDIR", "/tmp"), "nate-sag-events.jsonl")

# --- What counts as reading the authority (live/deployed artifact, not local source) ---
CONTRACT_READ_RE = re.compile(
    r"get-introspection-schema"
    r"|get_introspection_schema"
    r"|dump-live-schema"
    r"|information_schema"
    r"|execute-statement"
    r"|execute_statement"
    r"|describe-db-cluster"
    r"|graphql\s+-",  # ad-hoc graphql CLI probe
    re.IGNORECASE,
)

# --- What the gate protects: data-access facades ---
FACADE_PATH_RE = re.compile(r"src/lib/[A-Za-z0-9_]*Api\.ts$")
# The precise failure class: a client model create/update, whose required-field
# contract lives in the DEPLOYED schema and drifts from local migrations.
MODEL_MUTATION_RE = re.compile(r"models\s*\.\s*[A-Za-z0-9_]+\s*\.\s*(create|update)\s*\(")


def _log(record: dict) -> None:
    try:
        record["ts"] = time.time()
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception:
        pass


def _record_contract_read(source: str) -> None:
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as fh:
            json.dump({"last_read": time.time(), "source": source[:300]}, fh)
    except Exception:
        pass


def _seconds_since_contract_read() -> float | None:
    try:
        with open(STATE_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        last = float(data.get("last_read", 0))
        if last <= 0:
            return None
        return time.time() - last
    except Exception:
        return None


def _text_of(tool_input: dict) -> str:
    """All write payload text a gate should inspect."""
    parts = []
    for key in ("file_text", "new_str", "old_str"):
        val = tool_input.get(key)
        if isinstance(val, str):
            parts.append(val)
    return "\n".join(parts)


def main() -> int:
    if MODE == "off":
        return 0

    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    event = json.loads(raw)
    tool_name = (event.get("tool_name") or "").strip()
    tool_input = event.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0

    # ---- 1) RECORD: did this command read a live contract? ----
    if tool_name in ("execute_bash", "use_aws", "aws___call_aws"):
        haystack = " ".join(
            str(tool_input.get(k, ""))
            for k in ("command", "cli_command", "operation_name", "service_name", "parameters")
        )
        if CONTRACT_READ_RE.search(haystack):
            _record_contract_read(haystack)
        return 0

    # ---- 2) GATE: a model create/update edit in a data facade ----
    if tool_name != "fs_write":
        return 0

    path = str(tool_input.get("path") or "")
    if not FACADE_PATH_RE.search(path):
        return 0

    payload = _text_of(tool_input)
    if not MODEL_MUTATION_RE.search(payload):
        return 0

    age = _seconds_since_contract_read()
    if age is not None and age <= TTL_SECONDS:
        return 0  # authority was read recently; proceed

    reason = "no live-contract read recorded" if age is None else f"last read {int(age/60)}m ago (stale)"
    _log({"rule": "SAG-CREATE-CONTRACT", "path": path, "reason": reason, "mode": MODE})

    if MODE == "log":
        return 0

    sys.stderr.write(
        "SAG[SAG-CREATE-CONTRACT]: blocked - editing a model create/update in "
        f"{os.path.basename(path)} with {reason}.\n"
        "The required-field contract for a create/update lives in the DEPLOYED schema, "
        "NOT in local migrations or resource.ts (Amplify marks NOT NULL columns REQUIRED "
        "even when Postgres has a DEFAULT). Read the authority first, e.g.:\n"
        "  API_ID=<id> scripts/dump-live-schema.sh --required Create<Model>Input\n"
        "Then re-apply this edit. Kill switch: NATE_SAG=off\n"
    )
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # fail-open
        sys.stderr.write(f"source-authority.py: internal error, allowing ({exc})\n")
        sys.exit(0)
