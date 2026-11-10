#!/usr/bin/env python3
"""
Lint deliverables (client-facing docs, emails, published content) against the mechanical
rules in Nate's-kb/writing-protocol.md (2.3) plus the Deliverable Hygiene leak sweep.
Internal-reference patterns cover this ecosystem's own markers (KB ids, repo paths, session ids,
credential stores), so internal context cannot leak into a client-facing document.

MECHANICAL RULES ONLY. This tool cannot tell you a draft is compliant.

It sees what a regex can see: banned words, em dashes, date formats,
placeholders, internal references, ING starts, hedges, labor offers.

It is BLIND to the failures that actually reach the customer:
  * a buried lead (the reader's question answered fourth)
  * length mismatched to the ask
  * a reader being taught their own domain
  * a hedged figure whose exact number sits in a file already read
  * an inverted referent that reverses the claim
  * correcting a premise the reader never got wrong
  * re-sending a deliverable whose actionable content did not change

Drafts that pass this linter with zero failures still reach the reader with
those defects. A clean run means the MECHANICS are clean. Run the protocol's Content Quality checklist (writing-protocol.md,
#process) against the draft FIRST and record the verdicts, then run this.

Usage:  python3 lint-deliverables.py FILE [FILE ...]
        python3 lint-deliverables.py --email PATH_TO_CORRESPONDENCE_MD

Emails are linted with the third-person and first-person rules RELAXED: the
protocol's Email Communication section requires a warm first-person greeting,
so "I" and "we" are correct there and wrong in a report.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# --- Non-Negotiable Constraint 2: banned buzzwords ---------------------------
BUZZWORDS = [
    "leverage", "leveraging", "leverages", "seamless", "seamlessly", "robust",
    "elevate", "unlock", "empower", "harness", "delve", "dive in", "dive deep",
    "realm", "landscape", "game-changer", "game changer", "cutting-edge",
    "state-of-the-art", "at the forefront", "in today's world", "in the world of",
    "when it comes to", "it's worth noting", "needless to say", "tapestry",
    "testament to", "foster", "supercharge", "turbocharge", "revolutionize",
]
# "streamline" and figurative "navigate" are banned as filler; flag for review.
SOFT_BUZZ = ["streamline", "streamlined", "navigate", "navigating"]

HEDGES = ["some ", "many ", "a few ", "sometimes", "significant", "significantly",
          "various", "several", "roughly", "approximately", "fairly", "quite",
          "generally", "typically", "usually", "often", "likely", "probably",
          "almost certainly", "appears to", "seems to"]

INTENTION = ["aim to", "aims to", "hope to", "hopes to", "plan to", "plans to",
             "intend to", "intends to", "looking to", "seeking to"]

AI_PREAMBLE = ["here's the", "here is the", "certainly", "i hope this",
               "let me know if", "feel free to", "as requested",
               "per our conversation", "as we discussed", "in this document we"]

# --- Deliverable Hygiene 1: internal references that must never ship ----------
# The workshop, not the product: repo and KB paths, intelligence/memory/commitment ids,
# session ids, credential stores and cards, WSL and Windows drive paths.
INTERNAL = [
    r"Nate's-kb[/\\]", r"\.secrets\b", r"/mnt/[a-z]/", r"\b[A-Z]:\\\\",
    r"\b(know|reason|mem|cmt)-\d", r"\b(fail|pref|approach|proc)_\d+\b",
    r"\bsession-\d{4}-\d{2}-\d{2}-\d{3}\b", r"\bcred-\d{3}\b", r"\bBL-\d+\b",
]

FIRST_PERSON = re.compile(r"(?<![A-Za-z])(I|I'm|I'll|I've|I'd|we|we're|we'll|we've|"
                          r"our|ours|us|me|my|mine)(?![A-Za-z-])")

# Performative deference, banned by Respect the Reader's Expertise.
DEFERENCE = re.compile(
    r"(you'?(ll|d|re)\s+know\s+.{0,30}\bbetter than I\b|better placed than I|"
    r"you'?re the expert|I'?m sure you (already )?know|as you know better)", re.I)

# Reply calibration: EQUIP, DO NOT OPERATE. Never offer to run work
# the reader can self-serve with a tool named in the same message. The ONE legitimate
# exception is remediating our own incomplete or wrong deliverable, which the linter
# cannot detect, so the message names it and the human decides.
LABOR_OFFER = re.compile(
    r"(say the word and I'?ll|if you'?d rather we|we can run (it|that|this)|"
    r"from our side|want me to (run|pull|generate)|I'?ll (run|extend|pull) (it|that|this)|"
    r"happy to (run|pull|generate)|I can (run|pull|generate) (it|that|this) for you|"
    r"we'?d be happy to (run|pull)|leave (it|that) with (me|us))", re.I)

# Reply calibration: no call/meeting offered as a default closer.
# Previously unlinted, which is why it kept recurring.
CALL_OFFER = re.compile(
    r"(happy to (jump|hop|get) on|jump on a (call|quick call)|hop on a call|"
    r"set up a (call|meeting|time)|schedule a (call|meeting)|grab (15|30|a few) minutes|"
    r"walk you through (it|this) live|book (some )?time)", re.I)

# Data and Metrics: scope every claim to what was actually checked.
# Context-dependent, so REVIEW rather than FAIL: sometimes it is genuinely true.
COVERAGE_OVERCLAIM = re.compile(
    r"(the rest of your (footprint|estate|fleet|accounts|environment)|"
    r"(your |the )?(entire|whole) (fleet|estate|footprint|organization|environment)|"
    r"all (of )?your accounts|every account and region|complete coverage|"
    r"across the board|org-wide sweep|full sweep|everywhere)", re.I)

# Prohibited Patterns: ambiguous referents. A bare none/them/those answering a
# negatively phrased question can invert the entire claim.
AMBIG_REFERENT = re.compile(
    r"\b(none|any|all|neither) of (them|those|these)\b", re.I)

ISO_DATE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
CODE_SPAN = re.compile(r"`[^`]*`")
SLASH_DATE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")
ING_START = re.compile(r"(?:^|(?<=[.!?]\s)|(?<=^[-*]\s))([A-Z][a-z]+ing)\b")
# Words that end in -ing but are not gerunds, so they are legal sentence openers.
NOT_GERUNDS = {"everything", "anything", "nothing", "something", "morning", "evening",
               "during", "king", "thing", "ceiling", "building", "spring", "string",
               "sterling", "wing", "ring", "sing", "bring", "swing", "sling"}
PLACEHOLDER = re.compile(r"<[a-z][a-z_-]*>|\{\{[^}]+\}\}|\[TBD\]|XXX", re.I)
EM_DASH = "\u2014"
CONTRASTIVE = re.compile(r"\b(is|are|was|were|be)\s+[^.,;]{2,40},\s+not\s+", re.I)
NOT_JUST = re.compile(r"not just\b.{0,40}\bit'?s\b|isn'?t about\b.{0,40}\bit'?s about\b", re.I)


def strip_code_spans(line: str) -> str:
    """Filenames and identifiers live in backticks; they are not prose."""
    return CODE_SPAN.sub(" ", line)


def in_code_block(lines: list[str]) -> list[bool]:
    """Mark lines inside fenced code blocks so code isn't linted as prose."""
    flags, fence = [], False
    for ln in lines:
        if ln.strip().startswith("```"):
            fence = not fence
            flags.append(True)
            continue
        flags.append(fence)
    return flags


def lint(path: str, is_email: bool) -> list[tuple[str, int, str]]:
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")
    code = in_code_block(lines)
    is_csv = path.lower().endswith(".csv")
    out: list[tuple[str, int, str]] = []

    def add(sev, n, msg):
        out.append((sev, n, msg))

    header = lines[0] if lines else ""
    for n, raw in enumerate(lines, 1):
        if code[n - 1]:
            continue
        line = raw
        prose = strip_code_spans(raw)
        low = line.lower()

        if EM_DASH in line:
            add("FAIL", n, "em dash (Constraint 2)")
        if NOT_JUST.search(line):
            add("FAIL", n, "AI-cliche 'not just X, it's Y' (Constraint 1)")
        if DEFERENCE.search(line):
            add("FAIL", n, "performative deference (Respect the Reader's Expertise)")
        m = LABOR_OFFER.search(prose)
        if m:
            add("FAIL", n, f"self-service labor offer {m.group(0)!r} (EQUIP, DO NOT "
                           "OPERATE). Only legitimate when remediating OUR OWN incomplete "
                           "deliverable, otherwise give the tool, not the labor")
        m = CALL_OFFER.search(prose)
        if m:
            add("FAIL", n, f"call/meeting offered as a closer {m.group(0)!r}. "
                           "Offer a call ONLY when the user said to, or when the topic "
                           "genuinely cannot be resolved in writing")
        m = COVERAGE_OVERCLAIM.search(prose)
        if m:
            add("REVIEW", n, f"coverage claim {m.group(0)!r}, confirm it matches what was "
                             "ACTUALLY checked and name the scope if it does not")
        m = AMBIG_REFERENT.search(prose)
        if m:
            add("REVIEW", n, f"ambiguous referent {m.group(0)!r}, name the noun and the "
                             "condition. Answering a negative question, this can invert "
                             "the claim")
        for w in BUZZWORDS:
            if re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", low):
                add("FAIL", n, f"banned buzzword {w!r} (Constraint 2)")
        for w in SOFT_BUZZ:
            if re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", low):
                add("REVIEW", n, f"filler-risk word {w!r}, confirm it carries meaning")
        for pat in INTERNAL:
            m = re.search(pat, line, re.I)
            if m:
                add("FAIL", n, f"internal reference {m.group(0)!r} (Deliverable Hygiene 1)")
        for w in AI_PREAMBLE:
            # "certainly" must not fire on "almost certainly", which is a hedge not a preamble
            if w == "certainly" and re.search(r"almost certainly", low):
                continue
            if w in low:
                add("FAIL", n, f"AI output artifact {w!r} (Deliverable Hygiene 3)")
        m = PLACEHOLDER.search(line)
        if m and not is_csv:
            add("FAIL", n, f"unresolved placeholder {m.group(0)!r} in a shipped doc")
        if SLASH_DATE.search(line):
            add("FAIL", n, "slash date format, protocol requires Month Day, Year")

        if not is_csv:
            if ISO_DATE.search(prose) and not line.strip().startswith("|"):
                add("FAIL", n, "ISO date in prose, protocol requires Month Day, Year")
            m = ING_START.search(line)
            if m and m.group(1).lower() not in NOT_GERUNDS:
                add("FAIL", n, f"ING word at sentence start {m.group(1)!r}")
            if CONTRASTIVE.search(line):
                add("REVIEW", n, "contrastive 'X, not Y', confirm the foil is load-bearing")
            for w in INTENTION:
                if w in low:
                    add("FAIL", n, f"intention verb {w!r}, state the commitment with a date")
            for w in HEDGES:
                if w in low:
                    add("REVIEW", n, f"hedge word {w.strip()!r}, replace with a number if possible")
            if re.search(r"\bwill\b", low) and not re.search(
                    r"(January|February|March|April|May|June|July|August|September|"
                    r"October|November|December)", line):
                add("REVIEW", n, "'will' without a date on the same line")
            if not is_email and FIRST_PERSON.search(prose):
                add("FAIL", n, "first person in a report (Third Person Only)")
            if re.search(r"(?<![A-Z])&(?![a-z]*;)", line):
                add("REVIEW", n, "ampersand, avoid unless part of a proper name")

    if is_csv:
        cells = "\n".join(lines)
        if re.search(r"\*\*|^#{1,6}\s|```", cells, re.M):
            add("FAIL", 0, "markdown syntax inside CSV cells (Deliverable Hygiene 3)")
        vals = re.findall(r"\b(YES|NO|Yes|No|yes|no)\b", cells)
        forms = {v for v in vals}
        if len({v.lower() for v in forms}) and len(forms) > 2:
            add("FAIL", 0, f"inconsistent boolean casing across cells: {sorted(forms)}")
    else:
        body = "\n".join(l for i, l in enumerate(lines) if not code[i])
        if not is_email:
            if not re.search(r"(?i)\b(purpose|this report|outcome)\b", body[:1200]):
                add("FAIL", 0, "no purpose/outcome statement in the opening "
                               "(Required Elements: every document states its outcome)")
            if not re.search(r"(?i)(next step|recommended action|what to do|action requir)", body):
                add("FAIL", 0, "no next-steps/action section (Required Elements: "
                               "concerns need Action, Owner, Path, Date)")
        if header.startswith("#") and ISO_DATE.search(header):
            add("FAIL", 1, "ISO date in the document title")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--email", action="append", default=[],
                    help="path to treat as an email body (first person allowed)")
    a = ap.parse_args()

    targets = [(f, False) for f in a.files] + [(f, True) for f in a.email]
    total_fail = total_review = 0
    for path, is_email in targets:
        if not os.path.exists(path):
            print(f"!! missing {path}")
            continue
        res = lint(path, is_email)
        fails = [r for r in res if r[0] == "FAIL"]
        revs = [r for r in res if r[0] == "REVIEW"]
        total_fail += len(fails)
        total_review += len(revs)
        tag = "EMAIL" if is_email else "DOC  "
        print(f"\n=== {tag} {os.path.basename(path)}: {len(fails)} FAIL, {len(revs)} REVIEW")
        seen = set()
        for sev, n, msg in res:
            key = (sev, msg)
            if key in seen:
                continue
            seen.add(key)
            count = sum(1 for s, _, m in res if (s, m) == key)
            loc = f"L{n}" + (f" (+{count-1} more)" if count > 1 else "")
            print(f"  {sev:<6} {loc:<16} {msg}")
    print(f"\nTOTAL: {total_fail} FAIL, {total_review} REVIEW")
    print("\n" + "=" * 72)
    print("MECHANICAL CHECKS ONLY. A clean run is NOT a compliant draft.")
    print("This tool cannot see: a buried lead, length vs the ask, explaining the")
    print("reader their own domain, a hedged figure whose number is already on disk,")
    print("an inverted referent, or a re-send whose content did not change.")
    print("Run the Content Quality checklist (writing-protocol.md #process) against")
    print("the draft and RECORD the verdicts. An unrecorded pass reads as a skipped one.")
    print("=" * 72)
    return 1 if total_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
