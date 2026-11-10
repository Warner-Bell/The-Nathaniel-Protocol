#!/usr/bin/env python3
"""test-source-authority.py - regression suite for the SAG preToolUse floor.

Verifies the floor blocks the exact 2026-09-03 failure (editing a model create in a
data facade without having read the deployed contract), stays quiet everywhere else,
records contract reads, honours the kill switch and log mode, and fails open.

Run: python3 scripts/hooks/test-source-authority.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source-authority.py")
FACADE = "my-app/src/lib/ordersApi.ts"
CREATE_SNIPPET = "await dataClient.models.SplitParticipant.create({ expense_id: id })"


def run(event: dict, env_extra: dict | None = None, tmpdir: str | None = None) -> int:
    env = dict(os.environ)
    env.pop("NATE_SAG", None)
    if tmpdir:
        env["TMPDIR"] = tmpdir
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode


def fresh_tmp() -> str:
    return tempfile.mkdtemp(prefix="sagtest-")


CASES: list[tuple[str, int, dict, dict, bool]] = []
# (name, expected_exit, event, env, needs_prior_contract_read)

# --- Should BLOCK: the exact failure this floor exists for ---
CASES.append((
    "block: model create edit in facade, no contract read",
    2,
    {"tool_name": "fs_write", "tool_input": {"path": FACADE, "new_str": CREATE_SNIPPET}},
    {},
    False,
))
CASES.append((
    "block: model update edit in facade, no contract read",
    2,
    {"tool_name": "fs_write", "tool_input": {
        "path": "src/lib/preferencesApi.ts",
        "new_str": "await dataClient.models.UserPreference.update({ id })",
    }},
    {},
    False,
))
CASES.append((
    "block: create arrives via file_text (whole-file create)",
    2,
    {"tool_name": "fs_write", "tool_input": {"path": "src/lib/savingsApi.ts", "file_text": CREATE_SNIPPET}},
    {},
    False,
))

# --- Should ALLOW: everything outside the narrow scope ---
CASES.append((
    "allow: facade edit with no model mutation (comment only)",
    0,
    {"tool_name": "fs_write", "tool_input": {"path": FACADE, "new_str": "// clarify the header"}},
    {},
    False,
))
CASES.append((
    "allow: model create outside a facade (component file)",
    0,
    {"tool_name": "fs_write", "tool_input": {"path": "src/pages/SavingsPage.tsx", "new_str": CREATE_SNIPPET}},
    {},
    False,
))
CASES.append((
    "allow: unrelated tool",
    0,
    {"tool_name": "grep", "tool_input": {"pattern": "models.X.create"}},
    {},
    False,
))
CASES.append((
    "allow: reading a file",
    0,
    {"tool_name": "fs_read", "tool_input": {"path": FACADE}},
    {},
    False,
))
CASES.append((
    "allow: empty/garbage input fails open",
    0,
    {},
    {},
    False,
))

# --- Kill switch + log mode ---
CASES.append((
    "kill switch: NATE_SAG=off allows the blocked case",
    0,
    {"tool_name": "fs_write", "tool_input": {"path": FACADE, "new_str": CREATE_SNIPPET}},
    {"NATE_SAG": "off"},
    False,
))
CASES.append((
    "log mode: records but does not block",
    0,
    {"tool_name": "fs_write", "tool_input": {"path": FACADE, "new_str": CREATE_SNIPPET}},
    {"NATE_SAG": "log"},
    False,
))

# --- The unblock path: read the authority, then the same write is allowed ---
CASES.append((
    "allow: same write AFTER a contract read was recorded",
    0,
    {"tool_name": "fs_write", "tool_input": {"path": FACADE, "new_str": CREATE_SNIPPET}},
    {},
    True,
))


def main() -> int:
    failures = 0
    for name, expected, event, env_extra, needs_read in CASES:
        tmp = fresh_tmp()
        if needs_read:
            # Simulate the agent reading the deployed contract first.
            pre = run(
                {"tool_name": "execute_bash",
                 "tool_input": {"command": "API_ID=x scripts/dump-live-schema.sh --required CreateSplitParticipantInput"}},
                tmpdir=tmp,
            )
            if pre != 0:
                print(f"SETUP FAIL ({name}): record step exited {pre}")
                failures += 1
                continue
        got = run(event, env_extra=env_extra, tmpdir=tmp)
        ok = got == expected
        print(f"{'PASS' if ok else 'FAIL'}  [{got}=={expected}]  {name}")
        if not ok:
            failures += 1

    # Explicit check that a contract read is actually recorded
    tmp = fresh_tmp()
    run({"tool_name": "use_aws",
         "tool_input": {"service_name": "appsync", "operation_name": "get-introspection-schema"}},
        tmpdir=tmp)
    state = os.path.join(tmp, "nate-sag-contract-reads.json")
    recorded = os.path.exists(state)
    print(f"{'PASS' if recorded else 'FAIL'}  use_aws introspection call is recorded as a contract read")
    if not recorded:
        failures += 1

    print(f"\n{len(CASES) + 1} checks, {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
