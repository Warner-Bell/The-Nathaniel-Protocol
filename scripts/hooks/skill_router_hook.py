#!/usr/bin/env python3
"""skill_router_hook.py - preToolUse skill-router: nudge the agent from a raw
discovery-tool reach toward the skill that already covers it.

=== MODULE MANIFEST ===
WHAT  Reads a Kiro `preToolUse` hook event (JSON on stdin: {tool_name, tool_input}).
      For a raw discovery reach (grep / glob / fs_read Search), runs the skill-router
      TARGET factor over the tool's args and, if a SKILL fires with support, either
      records the would-nudge (log mode) or blocks+redirects (enforce mode) so the
      agent consults the skill instead of hand-rolling the search.
WHY   A gate that needs the model to REMEMBER a skill is a suggestion, not
      a gate. The matcher was a good decision function that nothing called (lesson:
      wiring the hook is the deliverable). This is the structural firing.
      BOTH firing paths are handled by dispatch on hook_event_name.
      * userPromptSubmit (user-asks): full intent gate + target + kind-floor over the
        prompt; injects a non-blocking STDOUT context nudge (exit 0). Fires skills AND
        protocols (harmless as context). Active in log AND enforce mode.
      * preToolUse (model-volunteers): SKILLS only (P=0.95); on a raw discovery reach
        (grep/glob/fs_read Search) it logs (log mode) or blocks+redirects (enforce, exit 2).
HOW   Modeled exactly on scripts/hooks/denylist.py (the authoritative working hook):
      {tool_name, tool_input} on stdin, exit 2 = block + stderr->LLM, exit 0 = allow,
      fail-open on any error. Scoped to SKILLS only (the solved, P=0.95 half);
      protocols (P=0.68 ceiling) are left to the future userPromptSubmit path.
      Zero heavy deps: keyword matcher + kind-specific support floor, no embeddings.

MODES (env NATE_SKILL_ROUTER):
      "enforce"           - block the raw tool (exit 2) + stderr redirect to the skill
      "log" (default)     - never block; append would-nudges to the ledger (bake-in)
      "off"               - allow everything (kill switch, no config edit)

Wire (when ready) as a preToolUse command hook in .kiro/agents/nate.json for matchers
grep / glob / fs_read. NOT auto-wired - owner enables it.
"""
from __future__ import annotations
import sys
import os
import json
import datetime

MODE = os.environ.get("NATE_SKILL_ROUTER", "log").strip().lower()

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
ROUTER_DIR = os.path.normpath(os.path.join(HOOK_DIR, "..", "skill-router"))
ROUTES_FILE = __import__("pathlib").Path(ROUTER_DIR) / "routes.json"
LEDGER = os.environ.get("NATE_SKILL_ROUTER_LEDGER") or os.path.join(HOOK_DIR, "skill-router-events.jsonl")

DISCOVERY_TOOLS = {"grep", "glob", "fs_read"}
SKILL_FLOOR = 2  # skills need >=2 shared tokens OR a phrase (measured precision floor)


def extract_signal(tool_name: str, ti) -> str:
    """Build a routing signal from a discovery tool's arguments."""
    if not isinstance(ti, dict):
        return ""
    parts = []
    if tool_name == "grep":
        parts = [ti.get("pattern", ""), ti.get("path", ""), ti.get("include", "")]
    elif tool_name == "glob":
        parts = [ti.get("pattern", ""), ti.get("path", "")]
    elif tool_name == "fs_read":
        # only a SEARCH reach counts as raw discovery; plain Line/Directory reads are routine
        for op in (ti.get("operations") or []):
            if isinstance(op, dict) and op.get("mode") == "Search":
                parts += [op.get("pattern", ""), op.get("path", "")]
    return " ".join(str(p) for p in parts if p)


def evaluate(tool_name: str, tool_input):
    """Return (skills_fired:set, signal:str). Pure; importable by the test harness."""
    if tool_name not in DISCOVERY_TOOLS:
        return set(), ""
    signal = extract_signal(tool_name, tool_input)
    if not signal.strip():
        return set(), ""
    sys.path.insert(0, ROUTER_DIR)
    import matcher as M
    import intent as I
    res = M.match(signal, M.DEFAULT_THRESHOLD, top_k=1, min_margin=1.0)
    skills = {n for n in res.get("skills", []) if I._strong(signal, n, SKILL_FLOOR)}
    return skills, signal


def evaluate_prompt(prompt: str):
    """Return (protocols:set, skills:set) for a user prompt (userPromptSubmit path).
    Uses the full intent gate (built for prompts) + kind-specific support floor. Pure."""
    if not prompt.strip():
        return set(), set()
    sys.path.insert(0, ROUTER_DIR)
    import matcher as M
    import intent as I
    it, _ = I.intent(prompt)
    if not it:
        return set(), set()
    res = M.match(prompt, M.DEFAULT_THRESHOLD, top_k=1, min_margin=1.0)
    protos = {n for n in res.get("protocols", []) if I._strong(prompt, n, 1)}
    skills = {n for n in res.get("skills", []) if I._strong(prompt, n, SKILL_FLOOR)}
    return protos, skills


def _log(tool_name, signal, skills, action):
    try:
        with open(LEDGER, "a") as f:
            f.write(json.dumps({
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "tool": tool_name, "signal": signal,  # full, untruncated: permanent historical corpus for matcher tuning / corpus expansion (owner decision 2026-09-20)
                "skills": sorted(skills), "action": action, "mode": MODE,
            }) + "\n")
    except Exception:
        pass  # logging must never affect the decision


def main() -> int:
    if MODE == "off":
        return 0
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception as e:
        sys.stderr.write(f"skill-router: could not parse hook event ({e}); allowing (fail-open)\n")
        return 0

    name = str(event.get("hook_event_name", ""))
    is_prompt = name == "userPromptSubmit" or ("prompt" in event and "tool_name" not in event)

    # --- userPromptSubmit: the user-asks path (non-blocking STDOUT context nudge) ---
    if is_prompt:
        try:
            protos, skills = evaluate_prompt(str(event.get("prompt", "")))
        except Exception as e:
            sys.stderr.write(f"skill-router: prompt eval error ({e}); no nudge (fail-open)\n")
            return 0
        if not (protos or skills):
            return 0
        _log("userPromptSubmit", str(event.get("prompt", "")), protos | skills, "nudge")
        # Inject on STDOUT (exit 0 -> added to context). Active in both log and enforce
        # modes: it never blocks, so there is no reason to withhold the hint.
        bits = []
        if skills:
            bits.append(f"skills: {sorted(skills)}")
        if protos:
            bits.append(f"protocols: {sorted(protos)}")
        sys.stdout.write(
            f"[skill-router] This request maps to {{{', '.join(bits)}}}. Consult the "
            f"relevant skill (.kiro/skills/) or protocol (Nate's-kb/) before proceeding.\n")
        # Required reads (routes.json "required_reads"): records the agent has repeatedly failed to
        # read before acting on this protocol. Printed as an instruction, never blocking.
        try:
            reads = json.loads(ROUTES_FILE.read_text(encoding="utf-8")).get("required_reads", {})
            for p in sorted(protos):
                files = reads.get(p) or []
                if files:
                    sys.stdout.write(f"[skill-router] Before acting on {p}, read: " + "; ".join(files) + "\n")
        except Exception as e:
            sys.stderr.write(f"skill-router: required_reads unavailable ({e})\n")
        return 0

    # --- preToolUse: the model-volunteers path (block/redirect on a raw discovery reach) ---
    try:
        tool_name = str(event.get("tool_name", ""))
        tool_input = event.get("tool_input", {})
        skills, signal = evaluate(tool_name, tool_input)
    except Exception as e:
        sys.stderr.write(f"skill-router: internal error ({e}); allowing (fail-open)\n")
        return 0

    if not skills:
        return 0

    if MODE == "enforce":
        _log(tool_name, signal, skills, "blocked")
        names = ", ".join(sorted(skills))
        sys.stderr.write(
            f"SKILL-ROUTER: you're reaching for {tool_name}, but the '{names}' skill "
            f"covers this. Consult .kiro/skills/ for '{names}' first, then proceed if it "
            f"doesn't fit.\n")
        return 2

    # log mode (default): observe, never block
    _log(tool_name, signal, skills, "would-nudge")
    return 0


if __name__ == "__main__":
    sys.exit(main())
