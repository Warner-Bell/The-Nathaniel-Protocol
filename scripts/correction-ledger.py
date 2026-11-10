#!/usr/bin/env python3
"""correction-ledger.py - the write path for the correction loop.

=== MODULE MANIFEST ===
WHAT  The ONLY sanctioned writer for (a) diagnosis records in the corrections ledger and
      (b) edits to the Rules section of .kiro/steering/PRIME-DIRECTIVES.md. The
      correction-capture skill calls it; scripts/hooks/correction_hook.py writes the
      raw `event` records it annotates.
WHY   PRIME-DIRECTIVES.md is always-loaded steering, so every line costs context on
      every turn, and two instances (CLI + IDE) can edit it concurrently. Writes go
      through one locked, atomic, size-capped path instead of free-hand fs_write.
      The doc's own history is the constraint: appending a rule per mistake produced
      duplicate "scars" that had to be consolidated. So growth is citation-first:
      a repeat of a covered behavior appends its evidence id to the governing rule; a
      new rule is written only for an uncovered behavior, and never past the line cap.
HOW   Stdlib only. fcntl lock on Intelligence/.corrections.lock. Doc writes are
      tempfile + os.replace. In "log" mode doc edits are STAGED (recorded in the ledger
      with a preview) and applied later with `apply`; in "enforce" they apply at once.

USAGE
  verdict  <event_id> genuine|false_positive         quick label (precision data)
  diagnose <event_id> --json '<obj>' [--allow-missing] full diagnosis record
  cite     <rule_no> <evidence_id> [--event ID]       append evidence to a rule
  add-rule --section S --title T --body B --evidence ID [--event ID]
  rewrite  <rule_no> --title T --body B --evidence ID[,ID] [--event ID]  (keeps prior cites)
  recite   <rule_no> <old_id> <new_id> --reason R [--event ID]  swap a wrong cite in place;
           with --event also amends that event's diagnosis capture_id (append-only)
  amend-capture <event_id> <new_id> --reason R       fix a diagnosis capture_id only
  discard  <stage_id> --reason R                     retire a staged edit unapplied
  apply    <stage_id>                                 apply a staged doc edit
  stats                                               precision, recurrence, top rules,
                                                      citation audit (wrong/unresolved evidence)

EVIDENCE IDS: cite the ledger EVENT id (corr-...), never a planned fail_NNN. A planned id is
not reserved and a concurrent save can consume it.
"""
from __future__ import annotations

import argparse
import datetime
import fcntl
import json
import os
import re
import secrets
import sys
import tempfile

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
INTEL = os.path.join(REPO, "Nate's-kb", "Intelligence")
LEDGER = os.environ.get("NATE_CORRECTION_LEDGER") or os.path.join(INTEL, "corrections.jsonl")
CONFIG = os.environ.get("NATE_CORRECTION_CONFIG") or os.path.join(INTEL, "correction-loop.json")
DOC = os.environ.get("NATE_DIRECTIVES_DOC") or os.path.join(REPO, ".kiro", "steering", "PRIME-DIRECTIVES.md")
PATTERNS = os.environ.get("NATE_PATTERNS_STORE") or os.path.join(INTEL, "patterns.json")
LOCK = LEDGER + ".lock"
PATTERN_ID_RE = re.compile(r"^[a-z_]+_\d+$")
LINE_CAP = int(os.environ.get("NATE_DIRECTIVES_LINE_CAP", "250"))

CLASSES = {"mistake", "assumption", "assertion", "behavior", "fact"}
RUNGS = {"entry", "citation", "rule", "rule_rewrite", "mechanical"}
RULE_RE = re.compile(r"^(\d+)\. \*\*")


# ---------------------------------------------------------------- infrastructure
def mode() -> str:
    env = os.environ.get("NATE_CORRECTION_LOOP", "").strip().lower()
    if env:
        return env
    try:
        with open(CONFIG) as f:
            return str(json.load(f).get("mode", "log")).strip().lower()
    except Exception:
        return "log"


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


class Locked:
    def __enter__(self):
        os.makedirs(os.path.dirname(LOCK), exist_ok=True)
        self.f = open(LOCK, "w")
        fcntl.flock(self.f, fcntl.LOCK_EX)
        return self

    def __exit__(self, *a):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()


def read_ledger():
    out = []
    try:
        with open(LEDGER) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return out


def append(rec: dict):
    with open(LEDGER, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def event_exists(eid: str) -> bool:
    return any(r.get("type") == "event" and r.get("id") == eid for r in read_ledger())


def read_doc():
    with open(DOC) as f:
        return f.read().split("\n")


def write_doc(lines):
    d = os.path.dirname(DOC)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".pd-", suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(lines))
    os.replace(tmp, DOC)


def rules_span(lines):
    """(start, end) line indexes of the '## The Rules' section, end exclusive."""
    start = next(i for i, l in enumerate(lines) if l.strip() == "## The Rules")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return start, end


# ---------------------------------------------------------------- doc edit ops (pure)
def op_cite(lines, rule_no: int, evidence: str):
    """Return (new_lines, preview). Appends evidence to rule N's citation group."""
    s, e = rules_span(lines)
    for i in range(s, e):
        m = RULE_RE.match(lines[i])
        if m and int(m.group(1)) == rule_no:
            line = lines[i].rstrip()
            if re.search(rf"(?<![\w-]){re.escape(evidence)}(?![\w-])", line):
                return lines, f"rule {rule_no} already cites {evidence} (no change)"
            cm = re.search(r"\*\(([^()]*)\)\*\s*$", line)
            if cm:
                new = line[:cm.start()] + f"*({cm.group(1)}, {evidence})*"
            else:
                new = line + f" *({evidence})*"
            out = list(lines)
            out[i] = new
            return out, f"rule {rule_no}: ...{new[-110:]}"
    raise ValueError(f"rule {rule_no} not found in the Rules section")


def op_add_rule(lines, section: str, title: str, body: str, evidence: str):
    if len(lines) >= LINE_CAP:
        raise ValueError(
            f"directives doc is {len(lines)} lines (cap {LINE_CAP}). Consolidate an existing "
            f"rule or cite into one instead of adding a new rule.")
    s, e = rules_span(lines)
    nums = [int(RULE_RE.match(l).group(1)) for l in lines[s:e] if RULE_RE.match(l)]
    n = max(nums) + 1 if nums else 1
    hdr = next((i for i in range(s, e)
                if lines[i].startswith("### ") and section.lower() in lines[i].lower()), None)
    if hdr is None:
        raise ValueError(f"section matching '{section}' not found under ## The Rules")
    sec_end = next((i for i in range(hdr + 1, e) if lines[i].startswith("### ")), e)
    last_rule = max((i for i in range(hdr + 1, sec_end) if RULE_RE.match(lines[i])), default=hdr)
    title = title.strip().rstrip(".").upper()
    body = body.strip()
    if "\u2014" in title + body:
        raise ValueError("em dash in rule text; the doc forbids it")
    rule = f"{n}. **{title}.** {body} *({evidence})*"
    out = lines[:last_rule + 1] + ["", rule] + lines[last_rule + 1:]
    return out, f"new rule {n} under '{lines[hdr].strip()}': {rule[:140]}"


def op_rewrite(lines, rule_no: int, title: str, body: str, evidence: str):
    """Replace rule N's title+body in place, keeping its number and EVERY prior citation.
    The rung for a recurrence that a citation alone has not fixed."""
    title = title.strip().rstrip(".").upper()
    body = body.strip()
    if "\u2014" in title + body:
        raise ValueError("em dash in rule text; the doc forbids it")
    s, e = rules_span(lines)
    for i in range(s, e):
        m = RULE_RE.match(lines[i])
        if m and int(m.group(1)) == rule_no:
            cm = re.search(r"\*\(([^()]*)\)\*\s*$", lines[i].rstrip())
            prior = [c.strip() for c in cm.group(1).split(",")] if cm else []
            for ev in [x.strip() for x in evidence.split(",") if x.strip()]:
                if ev not in prior:
                    prior.append(ev)
            cites = f" *({', '.join(prior)})*" if prior else ""
            out = list(lines)
            out[i] = f"{rule_no}. **{title}.** {body}{cites}"
            return out, f"rule {rule_no} rewritten: {out[i][:140]}"
    raise ValueError(f"rule {rule_no} not found in the Rules section")


def op_recite(lines, rule_no: int, old: str, new: str):
    """Swap citation `old` for `new` on rule N, in place. The repair for a cite that points
    at the wrong evidence (a planned capture id another instance consumed).
    No change if the swap is already done; refused if neither id is cited."""
    s, e = rules_span(lines)
    for i in range(s, e):
        m = RULE_RE.match(lines[i])
        if m and int(m.group(1)) == rule_no:
            line = lines[i].rstrip()
            cm = re.search(r"\*\(([^()]*)\)\*\s*$", line)
            cites = [c.strip() for c in cm.group(1).split(",")] if cm else []
            if old not in cites:
                if new in cites:
                    return lines, f"rule {rule_no} already cites {new} and not {old} (no change)"
                raise ValueError(f"rule {rule_no} cites neither {old} nor {new}")
            out_cites = []
            for c in cites:
                c = new if c == old else c
                if c not in out_cites:
                    out_cites.append(c)
            out = list(lines)
            out[i] = line[:cm.start()] + f"*({', '.join(out_cites)})*"
            return out, f"rule {rule_no}: {old} -> {new}: ...{out[i][-110:]}"
    raise ValueError(f"rule {rule_no} not found in the Rules section")


# ---------------------------------------------------------------- commands
def _apply_op(lines, op, p):
    if op == "cite":
        return op_cite(lines, int(p["rule_no"]), p["evidence"])
    if op == "recite":
        return op_recite(lines, int(p["rule_no"]), p["old"], p["new"])
    if op == "rewrite":
        return op_rewrite(lines, int(p["rule_no"]), p["title"], p["body"], p["evidence"])
    return op_add_rule(lines, p["section"], p["title"], p["body"], p["evidence"])


def _doc_edit(kind: str, params: dict, event: str | None):
    with Locked():
        lines = read_doc()
        new, preview = _apply_op(lines, kind, params)
        if new is lines:
            print(preview)
            return 0
        if mode() == "enforce":
            write_doc(new)
            append({"type": "doc_edit", "ts": now(), "op": kind, "params": params,
                    "event_id": event, "applied": True, "preview": preview})
            print(f"APPLIED: {preview}")
        else:
            sid = f"stage-{datetime.datetime.now():%Y%m%d-%H%M%S}-{secrets.token_hex(2)}"
            append({"type": "staged_edit", "id": sid, "ts": now(), "op": kind,
                    "params": params, "event_id": event, "preview": preview})
            print(f"STAGED ({mode()} mode) {sid}: {preview}\n"
                  f"  apply with: python3 scripts/correction-ledger.py apply {sid}")
    return 0


def cmd_verdict(a):
    with Locked():
        if not event_exists(a.event_id) and not a.allow_missing:
            sys.exit(f"no event {a.event_id} in ledger (use --allow-missing for backfill)")
        append({"type": "diagnosis", "ts": now(), "event_id": a.event_id, "verdict": a.verdict})
    print(f"recorded {a.verdict} for {a.event_id}")
    return 0


def cmd_diagnose(a):
    d = json.loads(a.json)
    v = d.get("verdict")
    if v not in ("genuine", "false_positive"):
        sys.exit("verdict must be genuine or false_positive")
    if v == "genuine":
        missing = [k for k in ("class", "violated_intent", "root_cause", "corrective_measure", "rung")
                   if not d.get(k)]
        if missing:
            sys.exit(f"genuine diagnosis missing: {missing}")
        if d["class"] not in CLASSES:
            sys.exit(f"class must be one of {sorted(CLASSES)}")
        if d["rung"] not in RUNGS:
            sys.exit(f"rung must be one of {sorted(RUNGS)}")
    with Locked():
        if not event_exists(a.event_id) and not a.allow_missing:
            sys.exit(f"no event {a.event_id} in ledger (use --allow-missing for backfill)")
        append({"type": "diagnosis", "ts": now(), "event_id": a.event_id, **d})
    print(f"diagnosis recorded for {a.event_id} ({v}{', ' + d.get('class', '') if v == 'genuine' else ''})")
    return 0


def cmd_cite(a):
    return _doc_edit("cite", {"rule_no": a.rule_no, "evidence": a.evidence_id}, a.event)


def _amend_capture(event_id: str, new: str, reason: str, old: str | None = None):
    """Append a corrected copy of the event's latest diagnosis with capture_id = new.
    Append-only: stats and audits read the LAST diagnosis per event, so the copy wins."""
    with Locked():
        diag = [r for r in read_ledger() if r.get("type") == "diagnosis" and r.get("event_id") == event_id]
        if not diag:
            sys.exit(f"no diagnosis for {event_id}; nothing to amend")
        last = diag[-1]
        cur = last.get("capture_id")
        if cur == new:
            print(f"{event_id} capture_id already {new} (no change)")
            return 0
        if old and cur not in (old, None):
            sys.exit(f"{event_id} capture_id is {cur}, not {old}; refusing to amend")
        rec = {k: v for k, v in last.items() if k not in ("ts", "amended_from", "amend_reason")}
        rec.update({"ts": now(), "capture_id": new, "amended_from": cur, "amend_reason": reason})
        append(rec)
    print(f"amended {event_id} capture_id {cur} -> {new}")
    return 0


def cmd_recite(a):
    _doc_edit("recite", {"rule_no": a.rule_no, "old": a.old_id, "new": a.new_id,
                         "reason": a.reason}, a.event)
    if a.event:
        return _amend_capture(a.event, a.new_id, a.reason, old=a.old_id)
    return 0


def cmd_amend_capture(a):
    return _amend_capture(a.event_id, a.new_id, a.reason)


def _load_patterns():
    try:
        with open(PATTERNS) as f:
            d = json.load(f)
        ents = d.get("entries", []) if isinstance(d, dict) else d
        return {e["id"]: e for e in ents if isinstance(e, dict) and e.get("id")}
    except (OSError, json.JSONDecodeError):
        return None


def citation_audit(recs, pats):
    """Flags for evidence that points at the wrong thing.
    1. An applied cite whose evidence resolves to nothing (pattern id not in the store, or a
       corr- id with no ledger event or diagnosis).
    2. A diagnosis capture_id whose pattern exists, was created on or after the diagnosis,
       and never names the event: the planned id was consumed by an unrelated entry."""
    flags = []
    events = {r.get("id") for r in recs if r.get("type") == "event"}
    diagnosed = {r.get("event_id") for r in recs if r.get("type") == "diagnosis"}
    edits = [r for r in recs if r.get("type") == "doc_edit" and r.get("applied")]
    swapped = {(int(r["params"]["rule_no"]), r["params"]["old"]) for r in edits if r["op"] == "recite"}
    for r in edits:
        p = r.get("params", {})
        ev = p.get("new") if r["op"] == "recite" else p.get("evidence")
        if r["op"] not in ("cite", "recite") or not ev:
            continue
        if r["op"] == "cite" and (int(p["rule_no"]), ev) in swapped:
            continue
        if PATTERN_ID_RE.match(ev):
            if pats is not None and ev not in pats:
                flags.append(f"rule {p['rule_no']} cites {ev}, not in patterns.json")
        elif re.match(r"^corr-(manual-)?\d{8}-", ev) and ev not in events and ev not in diagnosed:
            flags.append(f"rule {p['rule_no']} cites {ev}, no such ledger event")
    latest = {}
    for r in recs:
        if r.get("type") == "diagnosis":
            latest[r.get("event_id")] = r
    for eid, d in latest.items():
        cid = d.get("capture_id")
        if not cid or not PATTERN_ID_RE.match(cid) or pats is None:
            continue
        ent = pats.get(cid)
        if ent is None:
            flags.append(f"{eid} capture_id {cid} not in patterns.json (unwritten or lost)")
            continue
        if eid in json.dumps(ent):
            continue
        # Older patterns rarely name their event, so absence alone is noise. A consumed id
        # is an UNRELATED entry: word overlap with the diagnosis measured 0.02-0.07 on the
        # real collisions vs 0.19-0.38 on true matches (2026-11-09 real-ledger calibration).
        dw = _words(" ".join(str(d.get(k, "")) for k in ("violated_intent", "root_cause",
                                                           "corrective_measure")))
        pw = _words(f"{ent.get('content', '')} {ent.get('prevention', '')}")
        overlap = len(dw & pw) / max(1, len(dw | pw))
        if overlap < AUDIT_OVERLAP_MIN:
            flags.append(f"{eid} capture_id {cid} looks unrelated to its diagnosis (overlap "
                         f"{overlap:.2f}); likely consumed by another instance, fix with "
                         f"amend-capture/recite")
    return flags


AUDIT_OVERLAP_MIN = 0.12


def _words(s: str) -> set:
    return set(re.findall(r"[a-z]{4,}", s.lower()))


def cmd_add_rule(a):
    return _doc_edit("add-rule", {"section": a.section, "title": a.title, "body": a.body,
                                  "evidence": a.evidence}, a.event)


def cmd_rewrite(a):
    return _doc_edit("rewrite", {"rule_no": a.rule_no, "title": a.title, "body": a.body,
                                 "evidence": a.evidence}, a.event)


def cmd_discard(a):
    with Locked():
        recs = read_ledger()
        if not any(r.get("type") == "staged_edit" and r.get("id") == a.stage_id for r in recs):
            sys.exit(f"no staged edit {a.stage_id}")
        if any(r.get("stage_id") == a.stage_id and r.get("type") in ("doc_edit", "staged_discard")
               for r in recs):
            sys.exit(f"{a.stage_id} already applied or discarded")
        append({"type": "staged_discard", "ts": now(), "stage_id": a.stage_id, "reason": a.reason})
    print(f"discarded {a.stage_id}: {a.reason}")
    return 0


def cmd_apply(a):
    with Locked():
        recs = read_ledger()
        st = next((r for r in recs if r.get("type") == "staged_edit" and r.get("id") == a.stage_id), None)
        if not st:
            sys.exit(f"no staged edit {a.stage_id}")
        if any(r.get("type") == "doc_edit" and r.get("stage_id") == a.stage_id for r in recs):
            sys.exit(f"{a.stage_id} already applied")
        if any(r.get("type") == "staged_discard" and r.get("stage_id") == a.stage_id for r in recs):
            sys.exit(f"{a.stage_id} was discarded")
        lines = read_doc()
        p = st["params"]
        new, preview = _apply_op(lines, st["op"], p)
        if new is not lines:
            write_doc(new)
        append({"type": "doc_edit", "ts": now(), "op": st["op"], "params": p,
                "event_id": st.get("event_id"), "stage_id": a.stage_id,
                "applied": new is not lines, "preview": preview})
    print(f"APPLIED {a.stage_id}: {preview}")
    return 0


def cmd_stats(a):
    recs = read_ledger()
    events = {r["id"]: r for r in recs if r.get("type") == "event"}
    diag = {}
    for r in recs:
        if r.get("type") == "diagnosis":
            diag[r["event_id"]] = r  # last write wins
    print(f"mode: {mode()} | events: {len(events)} | diagnosed: {len(diag)}")
    for tier in ("strong", "soft"):
        ids = [i for i, e in events.items() if e.get("tier") == tier]
        lab = [diag[i]["verdict"] for i in ids if i in diag]
        g = lab.count("genuine")
        prec = f"{g / len(lab):.0%}" if lab else "n/a"
        print(f"  {tier:6s} events={len(ids):3d} labeled={len(lab):3d} precision={prec}")
    rec = sum(1 for e in events.values() if e.get("recurrence"))
    print(f"  recurrence-flagged events: {rec}")
    gen = [d for d in diag.values() if d.get("verdict") == "genuine"]
    by_class = {}
    for d in gen:
        by_class[d.get("class")] = by_class.get(d.get("class"), 0) + 1
    print(f"  genuine by class: {by_class or '{}'}")
    edits = [r for r in recs if r.get("type") == "doc_edit" and r.get("applied")]
    staged = [r for r in recs if r.get("type") == "staged_edit"]
    applied_stages = {r.get("stage_id") for r in edits}
    applied_stages |= {r.get("stage_id") for r in recs if r.get("type") == "staged_discard"}
    pend = [s["id"] for s in staged if s["id"] not in applied_stages]
    cites = {}
    for r in edits:
        if r["op"] == "cite":
            k = r["params"]["rule_no"]
            cites[k] = cites.get(k, 0) + 1
    print(f"  doc edits applied: {len(edits)} | staged pending: {len(pend)} {pend[:5]}")
    if cites:
        print(f"  most-cited rules: {sorted(cites.items(), key=lambda x: -x[1])[:5]}")
    undiag = [i for i in events if i not in diag]
    print(f"  undiagnosed events: {len(undiag)} {undiag[-5:]}")
    pats = _load_patterns()
    flags = citation_audit(recs, pats)
    note = "" if pats is not None else " (patterns.json unreadable, store checks skipped)"
    print(f"  citation audit: {len(flags)} flag(s){note}")
    for f in flags:
        print(f"    ! {f}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    v = sp.add_parser("verdict"); v.add_argument("event_id"); v.add_argument("verdict", choices=["genuine", "false_positive"])
    v.add_argument("--allow-missing", action="store_true"); v.set_defaults(fn=cmd_verdict)
    d = sp.add_parser("diagnose"); d.add_argument("event_id"); d.add_argument("--json", required=True)
    d.add_argument("--allow-missing", action="store_true"); d.set_defaults(fn=cmd_diagnose)
    c = sp.add_parser("cite"); c.add_argument("rule_no", type=int); c.add_argument("evidence_id")
    c.add_argument("--event"); c.set_defaults(fn=cmd_cite)
    r = sp.add_parser("add-rule")
    for k in ("--section", "--title", "--body", "--evidence"):
        r.add_argument(k, required=True)
    r.add_argument("--event"); r.set_defaults(fn=cmd_add_rule)
    w = sp.add_parser("rewrite"); w.add_argument("rule_no", type=int)
    for k in ("--title", "--body", "--evidence"):
        w.add_argument(k, required=True)
    w.add_argument("--event"); w.set_defaults(fn=cmd_rewrite)
    rc = sp.add_parser("recite"); rc.add_argument("rule_no", type=int)
    rc.add_argument("old_id"); rc.add_argument("new_id"); rc.add_argument("--reason", required=True)
    rc.add_argument("--event"); rc.set_defaults(fn=cmd_recite)
    am = sp.add_parser("amend-capture"); am.add_argument("event_id"); am.add_argument("new_id")
    am.add_argument("--reason", required=True); am.set_defaults(fn=cmd_amend_capture)
    x = sp.add_parser("discard"); x.add_argument("stage_id"); x.add_argument("--reason", required=True)
    x.set_defaults(fn=cmd_discard)
    p = sp.add_parser("apply"); p.add_argument("stage_id"); p.set_defaults(fn=cmd_apply)
    s = sp.add_parser("stats"); s.set_defaults(fn=cmd_stats)
    a = ap.parse_args()
    try:
        return a.fn(a)
    except ValueError as e:
        sys.exit(f"refused: {e}")


if __name__ == "__main__":
    sys.exit(main())
