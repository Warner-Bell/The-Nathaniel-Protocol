#!/usr/bin/env python3
"""test-skill-router.py - regression suite for the skill-router (both layers).

Layer 1 (HOOK CONTRACT): pipes crafted preToolUse events to skill_router_hook.py and
  asserts exit code (2 = block+redirect, 0 = allow). Positive nudges, negative silence,
  mode behavior (log/off never block), fail-open.
Layer 2 (DECISION QUALITY): imports intent.evaluate and asserts regression floors on the
  labeled corpus (controls must pass; skill precision/recall/F1 and protocol F1 floors).

Run: python3 scripts/hooks/test-skill-router.py   (exit 0 = all pass)
"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "skill_router_hook.py")
ROUTER_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "skill-router"))
# Ledger isolation: point the hook at a throwaway file so test runs never pollute the
# real bake-in ledger (mirrors test-denylist.py's grant-path isolation discipline).
LEDGER_TMP = os.path.join(tempfile.gettempdir(), "skill-router-test.jsonl")


def ev(tool, ti):
    return {"hook_event_name": "preToolUse", "tool_name": tool, "tool_input": ti}


def grep(pattern, path=""):
    return ev("grep", {"pattern": pattern, "path": path})


def glob(pattern, path=""):
    return ev("glob", {"pattern": pattern, "path": path})


def fs_search(pattern, path=""):
    return ev("fs_read", {"operations": [{"mode": "Search", "pattern": pattern, "path": path}]})


def fs_line(path):
    return ev("fs_read", {"operations": [{"mode": "Line", "path": path}]})


# (name, event_or_raw, mode, expected_exit)
HOOK_CASES = [
    # --- POSITIVE: raw discovery reach that a skill covers -> BLOCK+redirect in enforce ---
    ("grep trade-offs ROI -> route-f",  grep("interrogate trade-offs score ROI recommendation", "notes/decision.md"), "enforce", 2),
    ("fs_search options ROI -> route-f", fs_search("explore options trade-offs ROI", "decision.md"), "enforce", 2),

    # --- NEGATIVE: must NOT block (no false positives) ---
    ("routine fs_read Line (journal)",  fs_line("Life/Journal/monthly/2026-09.md"),      "enforce", 0),
    ("gibberish grep",                  grep("asdf qwer zxcv", "foo.txt"),               "enforce", 0),
    ("glob no skill domain",            glob("**/*.py"),                                 "enforce", 0),
    ("routine code grep (TODO)",        grep("TODO", "src/"),                            "enforce", 0),
    ("empty pattern grep",              grep("", ""),                                    "enforce", 0),

    # --- MODE: log and off never block, even on a match ---
    ("log mode never blocks",           grep("console error handler", "staging/app.js"), "log",     0),
    ("off mode never blocks",           grep("console error handler", "staging/app.js"), "off",     0),

    # --- FAIL-OPEN: malformed input allows ---
    ("malformed json fail-open",        "not json at all",                               "enforce", 0),
    ("non-discovery tool ignored",      ev("execute_bash", {"command": "ls -la"}),       "enforce", 0),
]


def run_hook_cases():
    passed = failed = 0
    for name, payload, mode, expected in HOOK_CASES:
        raw = payload if isinstance(payload, str) else json.dumps(payload)
        env = {**os.environ, "NATE_SKILL_ROUTER": mode, "NATE_SKILL_ROUTER_LEDGER": LEDGER_TMP}
        p = subprocess.run([sys.executable, HOOK], input=raw, capture_output=True, text=True, env=env)
        ok = p.returncode == expected
        passed += ok
        failed += not ok
        if not ok:
            print(f"  FAIL [{name}] mode={mode}: expected exit {expected}, got {p.returncode}")
            if p.stderr:
                print(f"        stderr: {p.stderr.strip()[:120]}")
    return passed, failed


# (name, prompt, expect_substring_in_stdout | None for must-stay-silent)
PROMPT_CASES = [
    ("route F request -> route-f",  "route F this before we build: explore options, interrogate the trade-offs, score ROI", "route-f-analysis"),
    ("ROI decision -> route-f",     "analyze whether this is worth building and give me a recommendation with ROI", "route-f-analysis"),
    ("summarize -> protocol",       "summarize this meeting transcript",                "summarization-protocol"),
    ("greeting -> silent",          "good morning!",                                    None),
    ("negated -> silent",           "no need to research this, I already know",         None),
    ("chatter -> silent",           "thanks, that's exactly what I needed",             None),
]


def run_prompt_cases():
    passed = failed = 0
    for name, prompt, expect in PROMPT_CASES:
        raw = json.dumps({"hook_event_name": "userPromptSubmit", "prompt": prompt})
        env = {**os.environ, "NATE_SKILL_ROUTER": "log", "NATE_SKILL_ROUTER_LEDGER": LEDGER_TMP}
        p = subprocess.run([sys.executable, HOOK], input=raw, capture_output=True, text=True, env=env)
        out = p.stdout
        if expect is None:
            ok = "[skill-router]" not in out
        else:
            ok = "[skill-router]" in out and expect in out
        passed += ok
        failed += not ok
        if not ok:
            print(f"  FAIL [{name}]: expected {'silence' if expect is None else expect!r}, got stdout={out.strip()[:120]!r}")
    return passed, failed


def run_decision_floors():
    """Assert the decision function hasn't regressed on the corpus."""
    sys.path.insert(0, ROUTER_DIR)
    import intent as I
    agg, ctl_ok, _ = I.evaluate(True, min_support_skill=2, min_support_proto=1)
    sp, sr, sf = I.prf(*agg["skill"])
    pp, pr, pf = I.prf(*agg["protocol"])
    # regression floors (v3 measured: skills P0.95/R0.80/F1 0.87, protocols F1 0.67; baseline proto F1 0.64)
    checks = [
        ("controls pass",        ctl_ok is True),
        ("skill precision >=0.90", sp >= 0.90),
        ("skill recall    >=0.75", sr >= 0.75),
        ("skill F1        >=0.80", sf >= 0.80),
        ("protocol F1     >=0.64", pf >= 0.64),
    ]
    passed = failed = 0
    for label, ok in checks:
        passed += ok
        failed += not ok
        if not ok:
            print(f"  FAIL [decision] {label}  (skill P{sp:.2f}/R{sr:.2f}/F1{sf:.2f}, proto F1{pf:.2f}, controls={ctl_ok})")
    return passed, failed, (sp, sr, sf, pp, pr, pf, ctl_ok)


def run_routes_coverage():
    """Enforce kernel <-> routes.json protocol COVERAGE (not keyword curation).
    routes_check.py exits 1 if the kernel gains/loses a routable protocol that
    routes.json doesn't reflect. Keyword drift stays advisory (no --strict)."""
    checker = os.path.join(ROUTER_DIR, "routes_check.py")
    p = subprocess.run([sys.executable, checker], capture_output=True, text=True)
    ok = p.returncode == 0
    if not ok:
        for line in p.stdout.splitlines():
            if "MISSING" in line or "EXTRA" in line:
                print(f"  FAIL [routes-coverage] {line.strip()}")
    return int(ok), int(not ok)


def main():
    print("=== Layer 0: ROUTES COVERAGE (kernel <-> routes.json) ===")
    rp, rf = run_routes_coverage()
    print(f"  {rp} passed, {rf} failed")
    print("=== Layer 1: HOOK CONTRACT (preToolUse) ===")
    hp, hf = run_hook_cases()
    print(f"  {hp} passed, {hf} failed")
    print("=== Layer 1b: PROMPT NUDGE (userPromptSubmit) ===")
    pp_, pf_ = run_prompt_cases()
    print(f"  {pp_} passed, {pf_} failed")
    print("=== Layer 2: DECISION QUALITY (labeled corpus) ===")
    dp, df, stats = run_decision_floors()
    sp, sr, sf, pp, pr, pf, ctl = stats
    print(f"  skills P{sp:.2f}/R{sr:.2f}/F1{sf:.2f}  protocols P{pp:.2f}/R{pr:.2f}/F1{pf:.2f}  controls={'PASS' if ctl else 'FAIL'}")
    print(f"  {dp} passed, {df} failed")
    total_fail = rf + hf + pf_ + df
    print(f"\n{'ALL PASS' if total_fail == 0 else str(total_fail) + ' FAILED'}  ({rp+hp+pp_+dp} checks passed)")
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
