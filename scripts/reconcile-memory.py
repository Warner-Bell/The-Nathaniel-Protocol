#!/usr/bin/env python3
"""Reconcile memory.json: report duplicate active_projects and long-stale open commitments.

WHY THIS EXISTS
  save-session.py matched active_project_updates by EXACT name until 2026-11-10, so a name
  variant appended a second project instead of updating the first, leaving exact duplicate
  pairs and near-pairs ("Project X" / "Project X-aws") in memory.json.
  Matching is normalized now, which stops NEW duplicates; this script finds the old ones.

MODES
  (default)   report only, writes nothing
  --apply     merge EXACT normalized-name clusters (keep the richest entry, union
              related_files), backing up memory.json first. Fuzzy pairs are never merged.

Commitments are never changed here. Close them with
  python3 scripts/commitments.py close <id> --note "..."
"""

import datetime
import difflib
import json
import re
import shutil
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commitments import is_open, LOCK, MEM, text_of  # the one definition of "open"
_save = import_module("save-session")

STALE_DAYS = 45
FUZZY_RATIO = 0.82
INACTIVE_PROJECT = {"superseded", "archived", "retired", "done", "complete", "completed"}


def norm(s):
    return _save._norm_project_name(s)


def richness(p):
    """Higher = keep: field count, next_action length, then recency."""
    score = len(p) * 10 + len(str(p.get("next_action", "")))
    lt = str(p.get("last_touched", ""))
    if re.match(r"\d{4}-\d{2}-\d{2}", lt):
        score += int(lt[:10].replace("-", ""))
    return score


def analyze(mem):
    projects = mem.get("active_projects", [])
    items = list(projects.values()) if isinstance(projects, dict) else list(projects)
    clusters = {}
    for p in items:
        if isinstance(p, dict):
            clusters.setdefault(norm(p.get("name")), []).append(p)
    exact_all = {k: v for k, v in clusters.items() if k and len(v) > 1}
    # A cluster where at most one record is live is already resolved by hand (the extras were
    # marked superseded/archived/done on purpose and kept as history). Not a duplicate to act
    # on, so it is neither reported nor merged.
    live = lambda p: str(p.get("status", "")).strip().lower() not in INACTIVE_PROJECT
    exact = {k: v for k, v in exact_all.items() if sum(1 for p in v if live(p)) > 1}
    resolved = len(exact_all) - len(exact)
    keys = [k for k in clusters if k]
    fuzzy = sorted(((round(difflib.SequenceMatcher(None, a, b).ratio(), 2), a, b)
                    for i, a in enumerate(keys) for b in keys[i + 1:]
                    if difflib.SequenceMatcher(None, a, b).ratio() >= FUZZY_RATIO), reverse=True)
    today = datetime.date.today()
    stale = []
    for c in mem.get("commitments", []):
        if not is_open(c):
            continue
        by = str(c.get("by") or "")[:10]
        if re.match(r"\d{4}-\d{2}-\d{2}$", by):
            age = (today - datetime.date.fromisoformat(by)).days
            if age > STALE_DAYS:
                stale.append((by, c.get("id") or "(no id)", text_of(c)[:80]))
    return items, exact, fuzzy, sorted(stale), resolved


def main():
    apply = "--apply" in sys.argv
    mem = json.loads(MEM.read_text(encoding="utf-8"))
    items, exact, fuzzy, stale, resolved = analyze(mem)

    print(f"=== memory.json reconcile ({'APPLY' if apply else 'REPORT'}) ===")
    print(f"projects: {len(items)} | open commitments: {sum(1 for c in mem.get('commitments', []) if is_open(c))}\n")
    print(f"-- Exact-duplicate project clusters (normalized name): {len(exact)} --"
          + (f"  ({resolved} more already resolved: one live record, the rest superseded/archived/done)" if resolved else ""))
    for k, v in exact.items():
        keep = max(v, key=richness)
        print(f"  [{k}] {len(v)} entries -> keep '{keep.get('name')}' (touched {keep.get('last_touched', '?')}, "
              f"status {keep.get('status', '?')}); drop {[(p.get('name'), p.get('status')) for p in v if p is not keep]}")
    print(f"\n-- Fuzzy near-duplicate pairs (REVIEW only, never merged): {len(fuzzy)} --")
    for r, a, b in fuzzy:
        print(f"  {r}  '{a}'  ~  '{b}'")
    print(f"\n-- Open commitments more than {STALE_DAYS}d past their date: {len(stale)} --")
    for by, cid, text in stale:
        print(f"  {by} | {cid} | {text}")

    if not apply:
        print("\n(report only; --apply merges exact clusters. Close commitments with scripts/commitments.py)")
        return
    if not exact:
        print("\nNothing to merge.")
        return

    with _save.FileLock(LOCK):
        mem = json.loads(MEM.read_text(encoding="utf-8"))
        items, exact, _, _, _ = analyze(mem)
        bak = f"{MEM}.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"
        shutil.copy2(MEM, bak)
        projects = mem["active_projects"]
        merged = 0
        for v in exact.values():
            keep = max(v, key=richness)
            files = sorted({f for p in v for f in (p.get("related_files") or [])})
            if files:
                keep["related_files"] = files
            for p in v:
                if p is keep:
                    continue
                if isinstance(projects, dict):
                    for k in [k for k, val in projects.items() if val is p]:
                        del projects[k]
                else:
                    projects.remove(p)
                merged += 1
        if not _save.save_json(MEM, mem):
            sys.exit(f"ERROR: write failed; memory.json unchanged (backup {bak})")
    print(f"\nBackup: {bak}\nProjects merged (dropped): {merged}")


if __name__ == "__main__":
    main()
