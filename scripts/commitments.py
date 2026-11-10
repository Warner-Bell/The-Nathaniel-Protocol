#!/usr/bin/env python3
"""commitments.py - read and change memory.json commitments immediately, outside a save.

WHY THIS EXISTS
  Commitments used to close only at save time, through `resolved_commitments`. A commitment
  the user finished mid-day stayed open in memory.json until the next save, so session-start
  scans and any calendar mirror kept surfacing it, and "close the loop immediately" had no
  sanctioned write path.

  Tools also disagreed on what "open" means (`status == "open"` versus "anything not in
  CLOSED_STATUSES"). OPEN / CLOSED_STATUSES / is_open() below are the one definition; new
  tools import them instead of re-deriving.

USAGE
  python3 scripts/commitments.py list [--all] [--to TEXT]
  python3 scripts/commitments.py due [--days 3]        # overdue + due within N days + undated count
  python3 scripts/commitments.py show <id>
  python3 scripts/commitments.py add --what TEXT [--by YYYY-MM-DD] [--to WHO] [--context TEXT]
  python3 scripts/commitments.py close <id> --note TEXT [--status resolved|done|cancelled]
  python3 scripts/commitments.py redate <id> YYYY-MM-DD|none [--note TEXT]
  python3 scripts/commitments.py reopen <id> --note TEXT

SAFETY
  - Writes take the same lock save-session.py uses (Intelligence/stores.lock) and write
    atomically through save-session's save_json, so a concurrent save cannot interleave.
  - Exact id only for every write. Id-less legacy commitments: give them an id through a
    save (`commitment_updates` cannot change ids; `new_commitments` auto-assigns).
  - One rolling backup: Nate's-kb/Memory/memory.json.commitments.bak
  - Every change appends a dated line to the commitment's `note`, and closes carry
    `resolved_by` (maintenance.py flags closed commitments without it).
"""

import argparse
import datetime
import json
import re
import shutil
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
_save = import_module("save-session")

KB = Path(__file__).resolve().parent.parent / "Nate's-kb"
MEM = KB / "Memory" / "memory.json"
LOCK = KB / "Intelligence" / "stores"          # same lock path as save-session.py main()
BACKUP = KB / "Memory" / "memory.json.commitments.bak"

# The one definition. A missing status means open (calendar mirror test asserts this).
OPEN = ("open", None, "")
CLOSED_STATUSES = {"done", "resolved", "complete", "completed", "cancelled", "canceled", "void"}
CLOSE_CHOICES = ("resolved", "done", "cancelled")
TEXT_FIELDS = _save.COMMITMENT_TEXT_FIELDS


def is_open(c):
    """Open = no status, or status "open" (any case). Every other status is not open."""
    if not isinstance(c, dict):
        return False
    st = c.get("status")
    return st in OPEN or str(st).strip().lower() == "open"


def text_of(c):
    return next((str(c.get(f)) for f in TEXT_FIELDS if c.get(f)), "")


def owner_of(c):
    return str(c.get("to") or c.get("who") or c.get("person") or "")


def by_date(c):
    try:
        return datetime.date.fromisoformat(str(c.get("by") or "")[:10])
    except ValueError:
        return None


def load():
    with open(MEM, encoding="utf-8") as f:
        return json.load(f)


def _today():
    return datetime.date.today().isoformat()


def _note(c, text):
    line = f"{_today()}: {text} (commitments.py)"
    c["note"] = f"{c['note']} | {line}" if c.get("note") else line


def _find(mem, cid):
    hits = [c for c in mem.get("commitments", []) if isinstance(c, dict) and c.get("id") == cid]
    if not hits:
        sys.exit(f"ERROR: no commitment with id {cid}")
    if len(hits) > 1:
        sys.exit(f"ERROR: {len(hits)} commitments share id {cid}; fix the store first")
    return hits[0]


def _write(mutate):
    """Load, mutate, back up, write atomically, all under the save lock."""
    with _save.FileLock(LOCK):
        mem = load()
        result = mutate(mem)
        shutil.copy2(MEM, BACKUP)
        mem["lastUpdated"] = _today()
        if not _save.save_json(MEM, mem):
            sys.exit(f"ERROR: write failed; memory.json unchanged (backup at {BACKUP})")
    return result


def _line(c):
    by = str(c.get("by") or "-")[:10]
    return f"{str(c.get('id') or '(no id)'):<44} {str(c.get('status') or 'open'):<9} by {by:<10} {owner_of(c)[:12]:<12} {text_of(c)[:80]}"


def cmd_list(a):
    rows = [c for c in load().get("commitments", []) if isinstance(c, dict) and (a.all or is_open(c))]
    if a.to:
        rows = [c for c in rows if a.to.lower() in owner_of(c).lower()]
    rows.sort(key=lambda c: (by_date(c) or datetime.date.max, str(c.get("id") or "")))
    for c in rows:
        print(_line(c))
    print(f"\n{len(rows)} {'commitments' if a.all else 'open'}")


def cmd_due(a):
    today = datetime.date.today()
    opens = [c for c in load().get("commitments", []) if is_open(c)]
    overdue = [c for c in opens if by_date(c) and by_date(c) < today]
    soon = [c for c in opens if by_date(c) and today <= by_date(c) <= today + datetime.timedelta(days=a.days)]
    undated = [c for c in opens if not by_date(c)]
    for title, rows in (("OVERDUE", overdue), (f"DUE WITHIN {a.days}d", soon)):
        print(f"-- {title}: {len(rows)} --")
        for c in sorted(rows, key=by_date):
            print("  " + _line(c))
    print(f"-- UNDATED: {len(undated)} --")
    print(f"\nopen={len(opens)} overdue={len(overdue)} due_{a.days}d={len(soon)} undated={len(undated)}")


def cmd_show(a):
    print(json.dumps(_find(load(), a.id), indent=2, ensure_ascii=False))


def cmd_add(a):
    if a.by:
        datetime.date.fromisoformat(a.by)

    def m(mem):
        cs = mem.setdefault("commitments", [])
        c = {"what": a.what, "by": a.by, "status": "open", "created": _today(), "source": "commitments.py"}
        if a.to:
            c["to"] = a.to
        if a.context:
            c["context"] = a.context
        c["id"] = _save._new_commitment_id(c, cs, _today())
        cs.append(c)
        return c
    c = _write(m)
    print(f"added {c['id']}")


def _transition(cid, status, note):
    def m(mem):
        c = _find(mem, cid)
        prev = c.get("status") or "open"
        if status in CLOSE_CHOICES and not is_open(c):
            sys.exit(f"ERROR: {cid} is already {prev}; reopen it first if this is intended")
        if status == "open" and is_open(c):
            sys.exit(f"ERROR: {cid} is already open")
        c["status"] = status
        if status in CLOSE_CHOICES:
            c["resolved_date"] = _today()
            c["resolved_by"] = "commitments.py"
        else:
            c.pop("resolved_date", None)
            c.pop("resolved_by", None)
        _note(c, f"{prev} -> {status}: {note}")
        return c
    c = _write(m)
    print(f"{cid}: {c['status']}  ({note})")


def cmd_close(a):
    _transition(a.id, a.status, a.note)


def cmd_reopen(a):
    _transition(a.id, "open", a.note)


def cmd_redate(a):
    new = None if a.date.lower() == "none" else a.date
    if new is not None:
        datetime.date.fromisoformat(new)

    def m(mem):
        c = _find(mem, a.id)
        old = c.get("by")
        c["by"] = new
        _note(c, f"redated {old} -> {new}" + (f": {a.note}" if a.note else ""))
        return c
    _write(m)
    print(f"{a.id}: by {new}")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.add_argument("--all", action="store_true"); s.add_argument("--to"); s.set_defaults(f=cmd_list)
    s = sub.add_parser("due"); s.add_argument("--days", type=int, default=3); s.set_defaults(f=cmd_due)
    s = sub.add_parser("show"); s.add_argument("id"); s.set_defaults(f=cmd_show)
    s = sub.add_parser("add"); s.add_argument("--what", required=True); s.add_argument("--by")
    s.add_argument("--to"); s.add_argument("--context"); s.set_defaults(f=cmd_add)
    s = sub.add_parser("close"); s.add_argument("id"); s.add_argument("--status", choices=CLOSE_CHOICES, default="resolved")
    s.add_argument("--note", required=True); s.set_defaults(f=cmd_close)
    s = sub.add_parser("redate"); s.add_argument("id"); s.add_argument("date"); s.add_argument("--note"); s.set_defaults(f=cmd_redate)
    s = sub.add_parser("reopen"); s.add_argument("id"); s.add_argument("--note", required=True); s.set_defaults(f=cmd_reopen)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
