#!/usr/bin/env python3
"""test-correction-loop.py - regression suite for the correction loop.

Layer 1 CLASSIFIER: correction_hook.classify on hand-labeled prompts, including real
        owner phrasings from the 2026-10-12 probe (typos and missing apostrophes kept).
Layer 2 HOOK CONTRACT: pipe events to correction_hook.py; assert exit 0 always,
        cue on stdout only for corrections, ledger written, off mode silent, fail-open.
Layer 3 LEDGER + DOC: correction-ledger.py against a COPY of PRIME-DIRECTIVES.md:
        cite appends, cite is idempotent, add-rule inserts + numbers, line cap refuses,
        log mode stages without touching the doc, apply lands it, em dash refused,
        diagnose validates, unknown event refused.

All writes are isolated to a tempdir via NATE_CORRECTION_* env vars; the real ledger
and the real directives doc are never touched.

Run: python3 scripts/hooks/test-correction-loop.py   (exit 0 = all pass)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
HOOK = os.path.join(HERE, "correction_hook.py")
LEDGER_CLI = os.path.join(REPO, "scripts", "correction-ledger.py")
REAL_DOC = os.path.join(REPO, ".kiro", "steering", "PRIME-DIRECTIVES.md")
if not os.path.exists(REAL_DOC):  # template source, before setup.sh deploys .kiro/
    REAL_DOC = os.path.join(REPO, ".steering-files", "steering", "PRIME-DIRECTIVES.md")

sys.path.insert(0, HERE)
import correction_hook as H  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL {name} {detail}")


# ---------------------------------------------------------------- Layer 1
print("Layer 1: classifier")
STRONG_CASES = [
    "you didnt use the script?",
    "why did you put the summary of right block back?",
    "i told you to give me examples",
    "what are you doing?/ i said go read the sql chat log",
    "that's wrong, it's the 6 month rule",
    "thats not what i asked for",
    "revert that change",
    "undo it",
    "you skipped step 3",
    "why would you delete that",
    "stop doing that",
]
SOFT_CASES = [
    "no proceed i will tell you when to save",
    "nope just curious",          # genuine FP at the hook layer; the model rejects it
    "no, leave it out",
    "wrong file",
]
NONE_CASES = [
    "proceed",
    "ok cool",
    "build the hook",
    "now route f it again correctness completeness etc",       # real: instruction, not complaint
    "run this process again make sure we hit it properly",     # real: instruction, not complaint
    "know what? lets add error handling and git commits for easy roll back",
    "nothing new here, carry on",
    "not now, maybe tomorrow",  # 'not' is not a correction cue
    "i want to review the steering docs",
    "",
]
for p in STRONG_CASES:
    t, m, r = H.classify(p)
    check(f"strong: {p!r}", t == "strong", f"got {t}")
for p in SOFT_CASES:
    t, m, r = H.classify(p)
    check(f"soft: {p!r}", t == "soft", f"got {t}/{m}")
for p in NONE_CASES:
    t, m, r = H.classify(p)
    check(f"none: {p!r}", t == "none", f"got {t}/{m}")

REC = ["why do you keep ignoring them", "you still haven't run the skills",
       "you didnt do it again", "how many times do i have to say it, you skipped it"]
for p in REC:
    t, m, r = H.classify(p)
    check(f"recurrence: {p!r}", r and t != "none", f"got {t}/{r}")
check("no recurrence on plain strong", H.classify("you didnt use the script")[2] is False)

check("strips context wrappers",
      H.user_text("--- CONTEXT ENTRY BEGIN ---\nyou didnt x\n--- CONTEXT ENTRY END ---\n"
                  "--- USER MESSAGE BEGIN ---\nok cool\n--- USER MESSAGE END ---") == "ok cool")

# ---------------------------------------------------------------- Layer 2
print("Layer 2: hook contract")
tmp = tempfile.mkdtemp(prefix="corr-test-")
env = dict(os.environ,
           NATE_CORRECTION_LEDGER=os.path.join(tmp, "corrections.jsonl"),
           NATE_CORRECTION_CONFIG=os.path.join(tmp, "missing.json"),
           NATE_DIRECTIVES_DOC=os.path.join(tmp, "PD.md"),
           NATE_PATTERNS_STORE=os.path.join(tmp, "patterns.json"))
env.pop("NATE_CORRECTION_LOOP", None)


def run_hook(payload, extra=None):
    e = dict(env, **(extra or {}))
    data = payload if isinstance(payload, str) else json.dumps(payload)
    p = subprocess.run([sys.executable, HOOK], input=data, capture_output=True, text=True, env=e, timeout=10)
    return p.returncode, p.stdout, p.stderr


def ledger_lines():
    try:
        return [json.loads(l) for l in open(env["NATE_CORRECTION_LEDGER"]) if l.strip()]
    except FileNotFoundError:
        return []


rc, out, _ = run_hook({"hook_event_name": "userPromptSubmit", "prompt": "you didnt use the script"})
check("strong exits 0", rc == 0)
check("strong cue on stdout", "[correction-loop] Correction detected" in out, out)
check("strong cue names the skill", "correction-capture/SKILL.md" in out)
L = ledger_lines()
check("ledger event written", len(L) == 1 and L[0]["type"] == "event" and L[0]["tier"] == "strong", L)
event_id = L[0]["id"] if L else "missing"

rc, out, _ = run_hook({"hook_event_name": "userPromptSubmit", "prompt": "nope just curious"})
check("soft cue is conditional", rc == 0 and "Possible correction" in out and "false_positive" in out, out)

rc, out, _ = run_hook({"hook_event_name": "userPromptSubmit", "prompt": "build the hook"})
check("non-correction is silent", rc == 0 and out == "", out)
check("non-correction writes nothing", len(ledger_lines()) == 2)

rc, out, _ = run_hook({"hook_event_name": "userPromptSubmit", "prompt": "you keep ignoring the skills again"})
check("recurrence cue", "RECURRENCE" in out, out)

rc, out, _ = run_hook({"prompt": "you didnt"}, {"NATE_CORRECTION_LOOP": "off"})
check("off mode silent", rc == 0 and out == "")
rc, out, err = run_hook("{not json")
check("bad json fails open", rc == 0 and out == "")
rc, out, _ = run_hook({"hook_event_name": "preToolUse", "tool_name": "grep", "tool_input": {"pattern": "you didnt"}})
check("tool events ignored", rc == 0 and out == "")
rc, out, _ = run_hook({"prompt": "revert that"},
                      {"NATE_CORRECTION_LEDGER": "/proc/nope/corrections.jsonl"})
check("ledger failure still cues", rc == 0 and "ledger write FAILED" in out, out)

# ---------------------------------------------------------------- Layer 3
print("Layer 3: ledger + directives doc")
REAL_ORIG = open(REAL_DOC).read()
shutil.copy(REAL_DOC, env["NATE_DIRECTIVES_DOC"])
# A fresh install ships Rules with no citations. Seed rule 4 with two so the
# keep-prior-evidence and rewrite-merge checks exercise a real citation group.
with open(env["NATE_DIRECTIVES_DOC"], encoding="utf-8") as _f:
    _lines = _f.read().split("\n")
for _i, _l in enumerate(_lines):
    if _l.startswith("4. **") and not _l.rstrip().endswith(")*"):
        _lines[_i] = _l.rstrip() + " *(fail_8164, fail_8306)*"
with open(env["NATE_DIRECTIVES_DOC"], "w", encoding="utf-8") as _f:
    _f.write("\n".join(_lines))
orig = open(env["NATE_DIRECTIVES_DOC"]).read()


def cli(*args, mode="enforce", extra=None):
    e = dict(env, NATE_CORRECTION_LOOP=mode, **(extra or {}))
    p = subprocess.run([sys.executable, LEDGER_CLI, *args], capture_output=True, text=True, env=e, timeout=15)
    return p.returncode, p.stdout + p.stderr


def doc():
    return open(env["NATE_DIRECTIVES_DOC"]).read()


def rule_line(n):
    return next(l for l in doc().split("\n") if l.startswith(f"{n}. **"))


rc, out = cli("cite", "4", "fail_9001", "--event", event_id)
check("cite applies in enforce", rc == 0 and "APPLIED" in out, out)
check("cite appended to group", rule_line(4).rstrip().endswith("fail_9001)*"), rule_line(4)[-60:])
check("cite kept prior evidence", "fail_8164" in rule_line(4))
before = doc()
rc, out = cli("cite", "4", "fail_9001")
check("cite is idempotent", rc == 0 and doc() == before and "already cites" in out, out)
rc, out = cli("cite", "4", "fail_900")
check("cite does not false-match a prefix id", ", fail_900)" in rule_line(4) or ", fail_900," in rule_line(4),
      rule_line(4)[-60:])
rc, out = cli("cite", "999", "fail_1")
check("cite unknown rule refused", rc != 0 and "not found" in out, out)

import re as _re
nxt = max(int(m.group(1)) for m in (_re.match(r"^(\d+)\. \*\*", l) for l in doc().split("\n")) if m) + 1
lines_before = doc().count("\n")
rc, out = cli("add-rule", "--section", "Source", "--title", "kb before counter-position",
              "--body", "When the owner corrects a fact, run kb_search before arguing.",
              "--evidence", "fail_9002")
check("add-rule applies", rc == 0 and f"new rule {nxt}" in out, out)
check("add-rule numbered + placed", f"{nxt}. **KB BEFORE COUNTER-POSITION.**" in doc())
ls = doc().split("\n")
inew = next(i for i, l in enumerate(ls) if l.startswith(f"{nxt}. **"))
i4 = next(i for i, l in enumerate(ls) if l.startswith("4. **"))
i5 = next(i for i, l in enumerate(ls) if l.startswith("5. **"))
check("add-rule lands in its section", i4 < inew < i5, (i4, inew, i5))
check("doc grew by 2 lines", doc().count("\n") == lines_before + 2)

rc, out = cli("add-rule", "--section", "Source", "--title", "x", "--body", "a \u2014 b", "--evidence", "e")
check("em dash refused", rc != 0 and "em dash" in out, out)
rc, out = cli("add-rule", "--section", "Nonexistent", "--title", "x", "--body", "y", "--evidence", "e")
check("unknown section refused", rc != 0 and "not found" in out, out)
rc, out = cli("add-rule", "--section", "Source", "--title", "x", "--body", "y", "--evidence", "e",
              extra={"NATE_DIRECTIVES_LINE_CAP": "100"})
check("line cap refuses + says consolidate", rc != 0 and "Consolidate" in out, out)

# log mode stages, does not touch the doc
before = doc()
rc, out = cli("cite", "13", "fail_8649", "--event", event_id, mode="log")
check("log mode stages", rc == 0 and "STAGED" in out, out)
check("log mode leaves doc untouched", doc() == before)
stage_id = out.split("STAGED (log mode) ", 1)[-1].split(":", 1)[0].strip()
rc, out = cli("apply", stage_id, mode="log")
check("apply lands staged edit", rc == 0 and "fail_8649" in rule_line(13), out)
rc, out = cli("apply", stage_id, mode="log")
check("apply is single-use", rc != 0 and "already applied" in out, out)

# diagnose validation
rc, out = cli("diagnose", event_id, "--json", json.dumps({"verdict": "genuine", "class": "behavior"}))
check("diagnose rejects incomplete genuine", rc != 0 and "missing" in out, out)
good = {"verdict": "genuine", "class": "assertion", "violated_intent": "owner's reading is authoritative",
        "root_cause": "IMG skipped", "corrective_measure": "kb_search first", "rung": "citation",
        "governing_rule": 4}
rc, out = cli("diagnose", event_id, "--json", json.dumps(good))
check("diagnose accepts complete", rc == 0, out)
rc, out = cli("diagnose", "corr-nope", "--json", json.dumps(good))
check("diagnose unknown event refused", rc != 0, out)
rc, out = cli("diagnose", "corr-manual-20261012-1000", "--json", json.dumps(good), "--allow-missing")
check("diagnose --allow-missing for misses", rc == 0, out)
bad = dict(good, rung="vibes")
rc, out = cli("diagnose", event_id, "--json", json.dumps(bad))
check("diagnose rejects bad rung", rc != 0, out)
rc, out = cli("verdict", "corr-nope2", "false_positive")
check("verdict unknown event refused", rc != 0, out)

rc, out = cli("stats")
check("stats runs", rc == 0 and "events:" in out and "precision=" in out, out)

# rewrite: in place, number kept, every prior citation preserved, new evidence merged once
n_lines = doc().count("\n")
rc, out = cli("rewrite", "4", "--title", "institutional memory and owner facts",
              "--body", "Check the KB and what the owner already said before asserting.",
              "--evidence", "fail_8700, fail_8164")
r4 = rule_line(4)
check("rewrite applies", rc == 0 and "rewritten" in out, out)
check("rewrite keeps number + new title", r4.startswith("4. **INSTITUTIONAL MEMORY AND OWNER FACTS.**"), r4[:60])
check("rewrite keeps prior cites", all(c in r4 for c in ("fail_8164", "fail_8306", "fail_9001")), r4[-90:])
check("rewrite merges new evidence once", r4.count("fail_8164") == 1 and "fail_8700" in r4, r4[-90:])
check("rewrite adds no lines", doc().count("\n") == n_lines)
rc, out = cli("rewrite", "4", "--title", "x", "--body", "a \u2014 b", "--evidence", "e")
check("rewrite refuses em dash", rc != 0 and "em dash" in out, out)

# discard: retires a stage, apply then refuses it, stats stops counting it pending
rc, out = cli("cite", "3", "fail_8701", mode="log")
sid = out.split("STAGED (log mode) ", 1)[-1].split(":", 1)[0].strip()
rc, out = cli("discard", sid, "--reason", "superseded", mode="log")
check("discard works", rc == 0, out)
rc, out = cli("apply", sid, mode="log")
check("apply refuses discarded", rc != 0 and "discarded" in out, out)
check("discarded stage left doc alone", "fail_8701" not in rule_line(3))
rc, out = cli("stats", mode="log")
check("discarded not pending", sid not in out, out)

# recite + amend-capture + citation audit
mid = "corr-manual-20261109-0800"
diag = dict(good, capture_id="fail_9100")
cli("diagnose", mid, "--json", json.dumps(diag), "--allow-missing")
cli("cite", "6", "fail_9100", "--event", mid)
# a "concurrent save" takes fail_9100 for an unrelated failure; the real one lands as fail_9101
json.dump({"entries": [
    {"id": "fail_9100", "created": "2099-01-01", "content": "unrelated IMAP failure"},
    {"id": "fail_9101", "created": "2099-01-01", "content": "the real one", "evidence": mid}]},
    open(env["NATE_PATTERNS_STORE"], "w"))
rc, out = cli("stats")
check("audit flags consumed capture id", "capture_id fail_9100" in out and "looks unrelated" in out, out)
mid2 = "corr-manual-20261109-0810"
cli("diagnose", mid2, "--json", json.dumps(dict(good, capture_id="fail_9102")), "--allow-missing")
s = json.load(open(env["NATE_PATTERNS_STORE"]))
s["entries"].append({"id": "fail_9102", "created": "2099-01-01",
                     "content": "Skipped the KB search first and argued the owner's reading"})
json.dump(s, open(env["NATE_PATTERNS_STORE"], "w"))
rc, out = cli("stats")
check("audit spares a related entry that never names its event", mid2 not in out, out)
rc, out = cli("recite", "6", "fail_9100", "fail_9101", "--reason", "id consumed", "--event", mid)
r6 = rule_line(6)
check("recite swaps in place", rc == 0 and "fail_9101" in r6 and "fail_9100" not in r6, r6[-80:])
check("recite amends diagnosis", "amended " + mid in out, out)
L = [r for r in ledger_lines() if r.get("type") == "diagnosis" and r.get("event_id") == mid]
check("amend is append-only, latest wins", len(L) == 2 and L[-1]["capture_id"] == "fail_9101"
      and L[-1]["amended_from"] == "fail_9100", L)
rc, out = cli("stats")
check("audit clean after recite", mid not in out and "fail_9100" not in out.split("citation audit")[-1], out)
before = doc()
rc, out = cli("recite", "6", "fail_9100", "fail_9101", "--reason", "again", "--event", mid)
check("recite already-done is a no-op", rc == 0 and doc() == before and "no change" in out, out)
rc, out = cli("recite", "6", "fail_1", "fail_2", "--reason", "x")
check("recite refuses when neither cited", rc != 0 and "cites neither" in out, out)
rc, out = cli("recite", "999", "fail_1", "fail_2", "--reason", "x")
check("recite unknown rule refused", rc != 0 and "not found" in out, out)
rc, out = cli("recite", "6", "fail_910", "fail_2", "--reason", "x")
check("recite does not prefix-match", rc != 0 and "fail_9101" in rule_line(6), out)
cli("cite", "7", "fail_9999")
rc, out = cli("stats")
check("audit flags cite of missing pattern", "cites fail_9999, not in patterns.json" in out, out)
before = doc()
rc, out = cli("cite", "7", "corr-20261109-080000-abcd")
check("cite accepts an event id", rc == 0 and "corr-20261109-080000-abcd)*" in rule_line(7), out)

# isolation: the real doc must be byte-identical to what we copied
check("real doc untouched", open(REAL_DOC).read() == REAL_ORIG)

shutil.rmtree(tmp, ignore_errors=True)
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
