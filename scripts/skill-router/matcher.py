#!/usr/bin/env python3
"""Skill / Protocol matcher — v1 keyword strategy (IDF-weighted token overlap
+ explicit-phrase substring bonus).

This is BOTH the component under test (measured by eval.py) and the eventual
backend a hook would call. Keep it dependency-free and fast so it can run inside
a preToolUse/userPromptSubmit hook without adding latency.

Single source of truth:
  - Skills:   parsed live from .kiro/skills/**/SKILL.md frontmatter (name+description).
  - Protocols: keyword map in routes.json (transcribed from the kernel).

Strategy rationale: keyword matching is the deterministic floor.
IDF weighting gives distinctive words (lease, console, prototype) more pull than
common ones (code, review, use), so the verdict on keyword matching is fair rather
than a strawman. Where it still misses (paraphrases with zero shared tokens) is the
empirical spec for whether a semantic v2 is needed.

Usage:
  echo '{"signal_type":"prompt","signal":"..."}' | python3 matcher.py
  python3 matcher.py --signal "QA the staging site" [--threshold 1.5] [--json]
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]  # scripts/skill-router/ -> repo root
ROUTES = HERE / "routes.json"
SKILLS_DIR = REPO / ".kiro" / "skills"
if not SKILLS_DIR.exists():  # template source, before setup.sh deploys .kiro/
    SKILLS_DIR = REPO / ".steering-files" / "skills"

DEFAULT_THRESHOLD = 1.5

# Boilerplate that carries no routing signal. Kept deliberately small; over-stopping
# would hand the matcher an unfair advantage on the negatives.
STOP = set("""
a an the this that these those to of in on for with and or but if then else
is are was were be been being do does did done has have had will would can could
should may might must i you he she it we they me him her us them my your our their
your yours it's its as at by from into over under out up down off about not no yes
just only also more most very much many any some all each every into per via
use used using when where what which who whom whose how why whether want wants
wanting need needs help helps let lets me my get gets got give gives given
thing things stuff something someone before after first once ready right now
""".split())

WORD = re.compile(r"[a-z0-9][a-z0-9\-']*")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _stem(tok: str) -> str:
    for suf in ("ing", "ers", "er", "ed", "es", "s"):
        if len(tok) > len(suf) + 2 and tok.endswith(suf):
            return tok[: -len(suf)]
    return tok


def _tokens(text: str) -> set:
    out = set()
    for m in WORD.findall(_norm(text)):
        # Quoted terms ('red-green-refactor') keep a trailing quote/hyphen from WORD;
        # strip it so they match the same term in a signal (2026-10-27 fix).
        m = m.strip("'-")
        if m in STOP or len(m) < 2:
            continue
        out.add(_stem(m))
    return out


def load_protocols() -> dict:
    data = json.loads(ROUTES.read_text(encoding="utf-8"))
    protos = {}
    for name, triggers in data["protocols"].items():
        phrases = [t.lower() for t in triggers if " " in t]
        toks = set()
        for t in triggers:
            toks |= _tokens(t)
        protos[name] = {"phrases": phrases, "tokens": toks}
    return protos


def _frontmatter(path: Path) -> dict:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    if not txt.startswith("---"):
        return {}
    end = txt.find("---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in txt[3:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip().lower()] = v.strip().strip("'\"")
    return fm


def load_skills() -> dict:
    skills = {}
    for p in SKILLS_DIR.rglob("SKILL.md"):
        fm = _frontmatter(p)
        name = fm.get("name")
        desc = fm.get("description", "")
        if not name:
            continue
        skills[name] = {"phrases": [], "tokens": _tokens(desc), "desc": desc}
    return skills


def build_idf(targets: dict) -> dict:
    """Document frequency across all targets' token bags -> idf."""
    n = len(targets) or 1
    df = {}
    for t in targets.values():
        for tok in t["tokens"]:
            df[tok] = df.get(tok, 0) + 1
    return {tok: math.log((n + 1) / (c + 0.5)) + 0.1 for tok, c in df.items()}


def _score(sig_norm: str, sig_toks: set, target: dict, idf: dict) -> float:
    score = 0.0
    for ph in target.get("phrases", []):
        if ph in sig_norm:
            score += 2.0  # explicit multi-word trigger present verbatim
    shared = sig_toks & target["tokens"]
    for tok in shared:
        score += idf.get(tok, 0.6)
    return round(score, 3)


def match(signal: str, threshold: float = DEFAULT_THRESHOLD,
          top_k=None, min_margin: float = 0.0):
    protos = load_protocols()
    skills = load_skills()
    idf = build_idf({**protos, **skills})
    sig_norm = _norm(signal)
    sig_toks = _tokens(signal)

    proto_scores = {n: _score(sig_norm, sig_toks, t, idf) for n, t in protos.items()}
    skill_scores = {n: _score(sig_norm, sig_toks, t, idf) for n, t in skills.items()}

    def shape(scores):
        fired = sorted([(n, s) for n, s in scores.items() if s >= threshold],
                       key=lambda x: -x[1])
        if top_k is None:
            return fired
        # dominance gate: if the top candidate doesn't beat the runner-up by
        # min_margin, the signal is too ambiguous to fire — abstain.
        if fired and len(fired) >= 2 and (fired[0][1] - fired[1][1]) < min_margin:
            return []
        return fired[:top_k]

    fired_p = shape(proto_scores)
    fired_s = shape(skill_scores)
    return {
        "protocols": [n for n, _ in fired_p],
        "skills": [n for n, _ in fired_s],
        "proto_scores": dict(fired_p),
        "skill_scores": dict(fired_s),
        "threshold": threshold,
    }


def _read_signal(args) -> str:
    if args.signal:
        return args.signal
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            try:
                obj = json.loads(raw)
                # accept hook-event shapes too
                if "prompt" in obj:
                    return obj["prompt"]
                if "tool_name" in obj:
                    ti = obj.get("tool_input", "")
                    return f"{obj['tool_name']} {json.dumps(ti) if not isinstance(ti, str) else ti}"
                return obj.get("signal", "")
            except json.JSONDecodeError:
                return raw
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--signal")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    sig = _read_signal(args)
    if not sig:
        print("no signal provided", file=sys.stderr)
        sys.exit(1)
    res = match(sig, args.threshold)
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        p = ", ".join(res["protocols"]) or "(none)"
        s = ", ".join(res["skills"]) or "(none)"
        print(f"protocols: {p}\nskills:    {s}")


if __name__ == "__main__":
    main()
