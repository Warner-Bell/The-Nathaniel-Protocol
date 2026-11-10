#!/usr/bin/env python3
"""Tests for scripts/index-query.py against the live indexes (read-only).

Run: python3 scripts/test-index-query.py
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "index-query.py"
KB = SCRIPT.parent.parent / "Nate's-kb"
fails = 0


def run(params):
    r = subprocess.run([sys.executable, str(SCRIPT), json.dumps(params)], capture_output=True, text=True)
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else {})


def check(name, cond, detail=""):
    global fails
    print(f"  {'PASS' if cond else 'FAIL'} {name} {detail}")
    fails += 0 if cond else 1


kidx = json.load(open(KB / "Intelligence" / "knowledge-index.json", encoding="utf-8"))
ridx = json.load(open(KB / "Intelligence" / "reasoning-index.json", encoding="utf-8"))

# head: every index present, small, newest ids match recentIds
rc, h = run({"action": "head"})
check("head exits 0", rc == 0)
check("head covers 3 stores", set(h) == {"patterns", "knowledge", "reasoning"})
size_tok = len(json.dumps(h)) // 4
check("head is compact (<15k tok)", size_tok < 15000, f"(~{size_tok} tok)")
check("head recent = recentIds order", [r["id"] for r in h["knowledge"]["recent"]] == kidx["recentIds"][:10])
check("head counts match index", h["knowledge"]["counts"]["byCategory"] ==
      {k: len(v) for k, v in kidx["byCategory"].items()})

# tag: pick a real tag and confirm exact membership
tag, ids = next((t, v) for t, v in kidx["byTag"].items() if 3 <= len(v) <= 20)
rc, t = run({"action": "tag", "tags": [tag.upper()], "stores": ["knowledge"], "limit": 100})
check("tag is case-insensitive + complete", rc == 0 and {r["id"] for r in t["results"]} == set(ids), f"({tag})")
check("tag total reported", t.get("total") == len(set(ids)))

# ids: mixed stores, unknown id flagged not found
rid = ridx["recentIds"][0]
rc, i = run({"action": "ids", "ids": [kidx["recentIds"][0], rid, "know-9999999"]})
res = {r["id"]: r for r in i["results"]}
check("ids resolves knowledge", res[kidx["recentIds"][0]]["found"])
check("ids resolves reasoning + intent", res[rid]["found"] and ("intent" in res[rid]) == (rid in ridx.get("intents", {})))
check("ids flags missing", res["know-9999999"]["found"] is False)

# keyword: substring of a real summary must find that entry
eid, summ = next((e, s) for e, s in kidx["summaries"].items() if s and len(s) > 40)
needle = summ[10:30]
rc, k = run({"action": "keyword", "keyword": needle, "stores": ["knowledge"], "limit": 500})
check("keyword finds source entry", rc == 0 and eid in {r["id"] for r in k["results"]})

# signals: one line per reasoning summary, plain text, compact
r = subprocess.run([sys.executable, str(SCRIPT), json.dumps({"action": "signals"})], capture_output=True, text=True)
lines = [l for l in r.stdout.splitlines() if l and not l.startswith("#")]
want = {e for e, s in ridx["summaries"].items() if s}
check("signals exits 0", r.returncode == 0)
check("signals covers every reasoning entry", {l.split(": ", 1)[0] for l in lines} == want, f"({len(lines)}/{len(want)})")
sig_tok = len(r.stdout) // 4
check("signals compact (<= summaries section)", sig_tok <= len(json.dumps(ridx["summaries"])) // 4 + 50, f"(~{sig_tok} tok)")

# errors
check("unknown action -> 2", run({"action": "nope"})[0] == 2)
check("unknown store -> 2", run({"action": "head", "stores": ["bogus"]})[0] == 2)
check("keyword without value -> 2", run({"action": "keyword"})[0] == 2)

print(f"\n{'ALL PASS' if not fails else f'{fails} FAILED'}")
sys.exit(1 if fails else 0)
