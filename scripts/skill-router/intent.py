#!/usr/bin/env python3
"""Intent gate for skill/protocol routing — the missing factor.

The six-medium benchmark proved every retrieval medium measures TOPIC, not
INTENT: "mentioned X" scores like "do X", so adversarial negatives (topic-
positive, intent-negative) tank precision. This adds the factor none of them
had: does the signal express intent to INVOKE an action?

Two-factor gate:
  Factor 1 (intent, this file): is this a request/imperative to act, not a
    statement/greeting/negated-action? Pure regex — zero-dependency, hook-viable.
  Factor 2 (target, matcher.py): which skill/protocol (keyword/keyphrase + dominance).
  FIRE only if intent AND a target clears its bar.

Run: python3 intent.py            # eval: keyword-alone vs intent-gated, on the corpus
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(HERE))
import matcher as M

CORPUS = HERE / "corpus.jsonl"

# Common action verbs — imperative-first is a strong request signal.
IMPERATIVE_VERBS = set("""
add analyze assess build check compare compose condense configure create
customize debug deploy design diagnose dig draft edit estimate evaluate explore
figure find fix generate give grade grill harden help implement improve
investigate list look make map migrate pin plan prepare prioritize prove pull
qa recolor refactor refine remember remove research resolve review run save scan
screen set sharpen ship show summarize test transform triage turn update upgrade
verify walk write
clean prune trace look sound answer go strip
""".split())

REQUEST_FRAME = re.compile(
    r"\b(can you|could you|would you|help me|let'?s|please|i want|i need|"
    r"i'?d like|walk me through|give me|show me|map out|break .* into|"
    r"turn .* into|we should|we need to|how do i|how can i|what should i)\b")

# a trailing question that asks for an action/judgment (feasibility, evaluation)
ACTION_QUESTION = re.compile(
    r"\b(can (this|it|we)|does (it|this)|will (it|this)|is (it|this)\b.*\?|"
    r"is it possible|which .* (fits|should)|how (do|can))\b")

NEGATED = re.compile(
    r"\b(no need|do(n'?t| not) (?!know|understand|realize|think)|"
    r"skip (the|this|it)|nah\b|not going to|no thanks)\b")

GREETING_CHATTER = re.compile(
    r"^(hi|hey|hello|good (morning|afternoon|evening)|thanks|thank you|"
    r"cool|ok|okay|nice|great|word|bet|yep|yeah|sure|got it|sounds good)\b")

RHETORICAL = re.compile(r"\b(can you believe|in case you were wondering|just so you know|"
                        r"just so you|by the way)\b")

# Clause boundaries — an imperative verb starting any clause signals a request,
# even when it isn't the first word of the whole signal ("..., screen it for scams").
CLAUSE_SPLIT = re.compile(r"[,;:\u2014]|\s-\s| and | then | but ")
# Tool-reach leads: a tool call IS an action; intent defers to the TARGET factor.
TOOL_LEADS = {"grep", "execute_bash", "fs_read", "fs_write", "glob", "use_aws"}


def intent(signal: str, signal_type=None):
    s = M._norm(signal)
    first = (re.findall(r"[a-z']+", s) or [""])[0]
    # A tool-reach is inherently an action; let the target factor judge relevance
    # (routine fs_read/fs_write get rejected there for lack of a matching target).
    if signal_type == "tool" or first in TOOL_LEADS:
        return True, {"tool_action": True, "intent": True}
    clause_imperative = False
    for clause in CLAUSE_SPLIT.split(s):
        w = re.findall(r"[a-z']+", clause.strip())
        if w and w[0] in IMPERATIVE_VERBS:
            clause_imperative = True
            break
    feats = {
        "imperative_first": first in IMPERATIVE_VERBS,
        "clause_imperative": clause_imperative,
        "request_frame": bool(REQUEST_FRAME.search(s)),
        "action_question": bool(ACTION_QUESTION.search(s)) or (s.endswith("?") and not RHETORICAL.search(s)),
        "negated": bool(NEGATED.search(s)),
        "greeting_chatter": bool(GREETING_CHATTER.search(s)),
        "rhetorical": bool(RHETORICAL.search(s)),
    }
    positive = feats["imperative_first"] or feats["clause_imperative"] or feats["request_frame"] or feats["action_question"]
    blocked = feats["negated"] or feats["greeting_chatter"] or feats["rhetorical"]
    feats["intent"] = positive and not blocked
    return feats["intent"], feats


def prf(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 1.0
    r = tp / (tp + fn) if (tp + fn) else 1.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def _bigrams_desc(text):
    toks = [t for t in re.findall(r"[a-z0-9']+", text.lower()) if t not in M.STOP and len(t) > 2]
    return [f"{a} {b}" for a, b in zip(toks, toks[1:])]


# A token shared by this many targets or more is too common to count as evidence for
# a SKILL fire (e.g. 'build' sits in 7 of 45 targets). Without this, two generic words
# ('start' + 'build') let route-f-analysis fire on "start the build phase". Swept
# 2026-10-27 on the corpus: df<6 raised skill precision 0.87 -> 0.95, controls intact.
COMMON_TOKEN_DF = 6


def _token_df():
    protos, skills = M.load_protocols(), M.load_skills()
    df = {}
    for t in list(protos.values()) + list(skills.values()):
        for tok in t["tokens"]:
            df[tok] = df.get(tok, 0) + 1
    return df


def _support(signal, name):
    """(shared_token_count, phrase_hit_count) between signal and a target.
    For skills, tokens common across many targets don't count toward support."""
    protos = M.load_protocols()
    skills = M.load_skills()
    t = protos.get(name) or skills.get(name)
    if not t:
        return 0, 0
    toks = M._tokens(signal)
    s = M._norm(signal)
    shared = toks & t["tokens"]
    if name not in protos:
        df = _token_df()
        shared = {x for x in shared if df.get(x, 0) < COMMON_TOKEN_DF}
    ntok = len(shared)
    phrases = t["phrases"] if name in protos else _bigrams_desc(skills[name]["desc"])
    nph = sum(1 for p in phrases if p in s)
    return ntok, nph


def _strong(signal, name, min_support):
    """Keep a fire only if it has a phrase hit OR >= min_support shared tokens."""
    ntok, nph = _support(signal, name)
    return nph > 0 or ntok >= min_support


def evaluate(gate_on_intent: bool, threshold=M.DEFAULT_THRESHOLD, top_k=1, margin=1.0,
             min_support_proto=0, min_support_skill=0):
    rows = [json.loads(l) for l in CORPUS.read_text().splitlines() if l.strip()]
    agg = {"protocol": [0, 0, 0], "skill": [0, 0, 0]}
    ctl_ok = True
    misfires = []
    for row in rows:
        res = M.match(row["signal"], threshold, top_k=top_k, min_margin=margin)
        fired_p, fired_s = set(res["protocols"]), set(res["skills"])
        if gate_on_intent:
            it, _ = intent(row["signal"], row.get("signal_type"))
            if not it:
                fired_p, fired_s = set(), set()
        if min_support_proto:
            fired_p = {n for n in fired_p if _strong(row["signal"], n, min_support_proto)}
        if min_support_skill:
            fired_s = {n for n in fired_s if _strong(row["signal"], n, min_support_skill)}
        if row["source"].startswith("control"):
            exp = set(row.get("expect_protocols", [])) | set(row.get("expect_skills", []))
            got = fired_p | fired_s
            if row["source"] == "control-positive" and not exp.issubset(got):
                ctl_ok = False
            if row["source"] == "control-negative" and got:
                ctl_ok = False
            continue
        for kind, key, fired in (("protocol", "expect_protocols", fired_p),
                                 ("skill", "expect_skills", fired_s)):
            exp = set(row.get(key, []))
            agg[kind][0] += len(exp & fired)
            agg[kind][1] += len(fired - exp)
            agg[kind][2] += len(exp - fired)
            if fired - exp:  # false positive
                misfires.append((row["id"], row["source"], kind, sorted(fired - exp)))
    return agg, ctl_ok, misfires


def main():
    print("="*78)
    print("SOLUTION v1: intent gate x keyword-target  (81-row corpus, top1+dominance)")
    print("="*78)
    for label, gate, kw in [("keyword-alone (baseline)", False, {}),
                            ("INTENT-GATED (v2)", True, {}),
                            ("v3  skill-floor=2, proto-floor=1", True, {"min_support_skill": 2, "min_support_proto": 1}),
                            ("v4  skill-floor=2, proto-floor=2", True, {"min_support_skill": 2, "min_support_proto": 2})]:
        agg, ctl_ok, misfires = evaluate(gate, **kw)
        pp, pr, pf = prf(*agg["protocol"])
        sp, sr, sf = prf(*agg["skill"])
        print(f"\n{label}   controls={'PASS' if ctl_ok else 'FAIL'}")
        print(f"  protocols  P={pp:.2f} R={pr:.2f} F1={pf:.2f}   (tp={agg['protocol'][0]} fp={agg['protocol'][1]} fn={agg['protocol'][2]})")
        print(f"  skills     P={sp:.2f} R={sr:.2f} F1={sf:.2f}   (tp={agg['skill'][0]} fp={agg['skill'][1]} fn={agg['skill'][2]})")
        print(f"  false-fires: {len(misfires)}")

    # show which negatives the intent gate rescued
    print(f"\n{'-'*78}\nINTENT DECISION on the adversarial/negative rows (should all be intent=False):")
    rows = [json.loads(l) for l in CORPUS.read_text().splitlines() if l.strip()]
    wrong = 0
    for row in rows:
        if "negative" not in row["source"]:
            continue
        it, feats = intent(row["signal"], row.get("signal_type"))
        flag = "  <-- LEAK (intent=True on a negative)" if it else ""
        if it: wrong += 1
        print(f"  intent={str(it):5} [{row['source']:26}] {row['signal'][:52]!r}{flag}")
    print(f"\n  negatives misread as intent: {wrong}")

    print(f"\n{'-'*78}\nRECALL KILLERS — positive rows the intent gate BLOCKED (intent=False):")
    miss = 0
    for row in rows:
        exp = set(row.get("expect_protocols", [])) | set(row.get("expect_skills", []))
        if not exp or row["source"].startswith("control"):
            continue
        it, feats = intent(row["signal"], row.get("signal_type"))
        if not it:
            miss += 1
            fired = [k for k, v in feats.items() if v and k != "intent"]
            print(f"  [{row['source']:24}] {row['signal'][:56]!r}  feats={fired or 'NONE'}")
    print(f"\n  true positives blocked by intent gate: {miss}")


if __name__ == "__main__":
    main()
