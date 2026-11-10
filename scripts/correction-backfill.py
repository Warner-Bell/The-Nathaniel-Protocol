#!/usr/bin/env python3
"""correction-backfill.py - seed the corrections ledger from Kiro CLI history.

=== MODULE MANIFEST ===
WHAT  Reads ~/.local/share/kiro-cli/data.sqlite3 (read-only), runs the SHIPPED
      correction_hook.classify over every owner prompt for this repo, and for each
      STRONG-tier hit writes a ledger `event` (source=backfill) carrying the owner's
      prompt AND the assistant turn it was correcting. Soft hits are skipped: at ~50%
      precision they would bury the real signal without the turn context to judge them.
WHY   The live hook only sees corrections from the day it is wired. Backfilling the
      historical strong hits gives the correction-capture skill real recurrence counts
      on day one, so the top repeat offenders can be ranked now instead of in weeks.
HOW   Idempotent: event ids are derived from a hash of (conversation_id, turn index),
      so a re-run skips rows already in the ledger. Tool-output rows that the CLI
      history stores as prompts ({"exit_status"..., "I will run...") are filtered.

USAGE  python3 scripts/correction-backfill.py [--dry-run]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sqlite3
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(REPO, "scripts", "hooks"))
import correction_hook as H  # noqa: E402

DB = os.path.expanduser("~/.local/share/kiro-cli/data.sqlite3")
SESSIONS_DIR = os.path.expanduser("~/.kiro/sessions")
TOOL_OUTPUT_PREFIXES = ('{"exit_status"', "I will run the following", "[{\"line_number\"")


def prompt_text(entry) -> str:
    c = entry.get("user", {}).get("content", {})
    t = c.get("Prompt", {}).get("prompt", "") if isinstance(c, dict) else ""
    return H.user_text(t) if t else ""


def assistant_text(entry) -> str:
    a = entry.get("assistant") or {}
    if not isinstance(a, dict):
        return str(a)
    for kind in ("Response", "ToolUse"):
        x = a.get(kind)
        if isinstance(x, dict) and x.get("content"):
            return str(x["content"])
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    existing = set()
    try:
        with open(H.LEDGER) as f:
            for line in f:
                try:
                    existing.add(json.loads(line).get("id"))
                except json.JSONDecodeError:
                    pass
    except FileNotFoundError:
        pass

    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = db.execute(
        "SELECT conversation_id, value, updated_at FROM conversations_v2 WHERE key = ? "
        "ORDER BY updated_at ASC", (REPO,))
    new, skipped, scanned = [], 0, 0

    def consider(conv_id, turn, text, prev, updated_ms):
        nonlocal skipped, scanned
        if not text or len(text) >= 4000 or text.startswith(TOOL_OUTPUT_PREFIXES):
            return
        scanned += 1
        tier, matched, rec = H.classify(text)
        if tier != "strong":
            return
        eid = "corr-bf-" + hashlib.sha1(f"{conv_id}:{turn}".encode()).hexdigest()[:10]
        if eid in existing:
            skipped += 1
            return
        existing.add(eid)
        new.append({
            "type": "event", "id": eid, "source": "backfill",
            "conversation_id": conv_id, "turn": turn, "conv_updated_ms": updated_ms,
            "tier": tier, "matched": matched, "recurrence": rec, "mode": "backfill",
            "prompt": text, "corrected_turn": prev[-1500:],
        })

    for conv_id, value, updated_at in rows:
        try:
            hist = json.loads(value).get("history", [])
        except json.JSONDecodeError:
            continue
        for i, entry in enumerate(hist):
            prev = assistant_text(hist[i - 1]) if i > 0 else ""
            consider(conv_id, i, prompt_text(entry), prev, updated_at)
    db.close()

    # Kiro CLI 3.x (~2026-11-04 onward) stopped writing conversations_v2; sessions live in
    # ~/.kiro/sessions/<hash>/sess_<uuid>/{session.json,messages.jsonl}. Read-only scan;
    # turn = line index in messages.jsonl, so ids stay stable as a session grows.
    for sj in sorted(glob.glob(os.path.join(SESSIONS_DIR, "*", "sess_*", "session.json"))):
        try:
            with open(sj) as f:
                meta = json.load(f)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            continue
        paths = {os.path.normpath(p) for p in (meta.get("workspacePaths") or []) + (meta.get("rootPaths") or [])}
        if REPO not in paths:
            continue
        msgs = os.path.join(os.path.dirname(sj), "messages.jsonl")
        if not os.path.exists(msgs):
            continue
        sess_id = meta.get("id") or os.path.basename(os.path.dirname(sj))
        last_say = ""
        with open(msgs) as f:
            for i, line in enumerate(f):
                try:
                    m = json.loads(line)
                except json.JSONDecodeError:
                    continue
                pl = m.get("payload", {})
                t = pl.get("type")
                if t == "assistant" and pl.get("operationType") != "Reasoning":
                    c = pl.get("content")
                    if isinstance(c, str) and c.strip():
                        last_say = c
                elif t == "user":
                    c = pl.get("content")
                    text = H.user_text(c) if isinstance(c, str) and c else ""
                    consider(sess_id, i, text, last_say, m.get("timestamp"))
    print(f"scanned {scanned} owner prompts | strong hits new: {len(new)} | already in ledger: {skipped}")
    if a.dry_run or not new:
        return 0
    os.makedirs(os.path.dirname(H.LEDGER), exist_ok=True)
    with open(H.LEDGER, "a") as f:
        for r in new:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(new)} backfill events to {H.LEDGER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
