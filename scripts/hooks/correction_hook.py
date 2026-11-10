#!/usr/bin/env python3
"""correction_hook.py - userPromptSubmit correction loop: detect when the owner corrects
the agent, record it deterministically, and cue the correction-capture skill.

=== MODULE MANIFEST ===
WHAT  Reads a Kiro `userPromptSubmit` hook event (JSON on stdin: {prompt}). Classifies
      the prompt as STRONG (explicit correction phrase), SOFT (leading bare "no/nope/
      wrong/stop"), or NONE, plus a RECURRENCE flag ("again", "keep ignoring", "still
      haven't"). On STRONG or SOFT it appends an event to the corrections ledger and
      injects a non-blocking STDOUT cue (exit 0) telling the agent to run the
      correction-capture skill before replying.
WHY   Capture of owner corrections was purely behavioral ([CAPTURE:] markers), and only
      4 of 385 failure patterns were ever tagged as recurring because nothing measured
      recurrence. Probe 2026-10-12 over 9,423 real prompts: STRONG phrases hit 0.8% at
      ~90% precision; bare "no" hits 2.0% at ~50% (half are answers to yes/no
      questions). Design split (reason recorded in:
      THE HOOK SUPPLIES RECALL, THE MODEL SUPPLIES PRECISION. The hook cannot see the
      previous assistant turn, so SOFT hits get a conditional cue and the
      model, which has the full turn, decides genuine vs false positive.
HOW   Stdlib only, no embeddings, fail-open on any error (never blocks a prompt).
      The ledger is append-only JSONL; this hook writes `event` records only. The
      skill appends `diagnosis` / `staged_edit` records via scripts/correction-ledger.py.

MODES (config Nate's-kb/Intelligence/correction-loop.json {"mode": ...}; env
      NATE_CORRECTION_LOOP overrides):
      "log"     (default) - ledger + cue; the skill STAGES directive-doc edits, owner applies
      "enforce"           - ledger + cue; the skill APPLIES directive-doc edits immediately
      "off"               - do nothing (kill switch)
      The hook behaves identically in log and enforce; the mode only gates doc writes.

Wire as a userPromptSubmit command hook in .kiro/agents/nate.json (owner action:
nate.json is denylist keystone-protected).
"""
from __future__ import annotations

import datetime
import json
import os
import re
import secrets
import sys

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HOOK_DIR, "..", ".."))
INTEL = os.path.join(REPO, "Nate's-kb", "Intelligence")
CONFIG = os.environ.get("NATE_CORRECTION_CONFIG") or os.path.join(INTEL, "correction-loop.json")
LEDGER = os.environ.get("NATE_CORRECTION_LEDGER") or os.path.join(INTEL, "corrections.jsonl")
SKILL_PATH = ".kiro/skills/correction-capture/SKILL.md"

# Explicit correction phrases. Apostrophes optional: the owner types "didnt", "thats".
STRONG = re.compile(
    r"\b("
    r"that'?s (wrong|not (right|correct|true|what i))|"
    r"you('re| are) wrong|(that'?s |this is )?incorrect|"
    r"i (said|told you|asked( you)? (to|for))|"
    r"not what i (asked|meant|wanted|said)|i didn'?t (ask|say|want)|"
    r"why (did|would|are|were) you|"
    r"you (didn'?t|did not|skipped|ignored|missed|forgot|never|still (haven'?t|didn'?t|aren'?t))|"
    r"why do you keep|you keep (ignoring|forgetting|skipping|missing|doing)|"
    r"stop (doing|that|it)|don'?t do that|"
    r"revert|undo (that|it|this|the)|roll (it|that|this) back|put it back"
    r")\b",
    re.I,
)
# Leading bare negation: ~50% precision on its own, so only a conditional cue.
SOFT = re.compile(r"^\s*(no|nope|nah|wrong|stop)\b[\s,.!?]", re.I)
# The owner naming a repeat out loud is the highest-value signal in the corpus.
RECUR = re.compile(
    r"\b(again|keep (doing|ignoring|forgetting|skipping|missing)|"
    r"still (haven'?t|not|didn'?t|isn'?t)|every (single )?time|how many times|"
    r"(same|this) mistake)\b",
    re.I,
)


def mode() -> str:
    env = os.environ.get("NATE_CORRECTION_LOOP", "").strip().lower()
    if env:
        return env
    try:
        with open(CONFIG) as f:
            return str(json.load(f).get("mode", "log")).strip().lower()
    except Exception:
        return "log"


def user_text(prompt: str) -> str:
    """Strip injected CONTEXT ENTRY wrappers if present; classify only what the owner typed."""
    if "USER MESSAGE BEGIN" in prompt:
        prompt = prompt.split("USER MESSAGE BEGIN ---", 1)[-1].split("--- USER MESSAGE END", 1)[0]
    return prompt.strip()


def classify(text: str):
    """Return (tier, matched, recurrence). tier in {'strong','soft','none'}. Pure."""
    m = STRONG.search(text)
    rec = bool(RECUR.search(text))
    if m:
        return "strong", m.group(0), rec
    s = SOFT.search(text)
    if s:
        return "soft", s.group(1), rec
    # A recurrence word ALONE is not a correction: the 2026-10-12 corpus run showed
    # "run this process again" / "route f it again" are instructions, and treating
    # recurrence-alone as SOFT inflated the soft rate 2.0% -> 3.5%. Recurrence only
    # escalates a correction that matched on its own.
    return "none", "", False


def new_id() -> str:
    now = datetime.datetime.now()
    return f"corr-{now:%Y%m%d-%H%M%S}-{secrets.token_hex(2)}"


def record(event_id, tier, matched, rec, text, m) -> bool:
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a") as f:
            f.write(json.dumps({
                "type": "event", "id": event_id,
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "tier": tier, "matched": matched, "recurrence": rec,
                "mode": m, "prompt": text,
            }, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False  # ledger failure must never affect the prompt


def cue(event_id, tier, matched, rec) -> str:
    rec_note = " RECURRENCE signal: the owner says this has happened before; skip to the escalation rung." if rec else ""
    if tier == "strong":
        return (
            f"[correction-loop] Correction detected (event {event_id}, matched '{matched}').{rec_note} "
            f"Before replying, run the correction-capture skill ({SKILL_PATH}). "
            f"Step 1 is retrieval, not defense.\n")
    return (
        f"[correction-loop] Possible correction (event {event_id}, matched '{matched}').{rec_note} "
        f"If this message corrects you rather than answers a question you asked, run the "
        f"correction-capture skill ({SKILL_PATH}) before replying. If it does not, record "
        f"that: python3 scripts/correction-ledger.py verdict {event_id} false_positive\n")


def main() -> int:
    m = mode()
    if m == "off":
        return 0
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception as e:
        sys.stderr.write(f"correction-loop: unparseable hook event ({e}); fail-open\n")
        return 0
    if "tool_name" in event:  # not a prompt event; nothing to do
        return 0
    text = user_text(str(event.get("prompt", "")))
    if not text:
        return 0
    try:
        tier, matched, rec = classify(text)
    except Exception as e:
        sys.stderr.write(f"correction-loop: classify error ({e}); fail-open\n")
        return 0
    if tier == "none":
        return 0
    event_id = new_id()
    if not record(event_id, tier, matched, rec, text, m):
        event_id += " (ledger write FAILED, record manually)"
    sys.stdout.write(cue(event_id, tier, matched, rec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
