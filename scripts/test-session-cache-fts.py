#!/usr/bin/env python3
"""test-session-cache-fts.py - regression for the #3 FTS5 query sanitizer.

Unit-tests _sanitize_fts5_query (operators neutralized, recall preserved, safe fallback)
and runs a live control against the real session cache proving that malformed operator
input ("repo OR") now finds the record instead of silently returning zero.
Run: python3 scripts/test-session-cache-fts.py   (exit 0 = all pass)
"""
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "session-cache.py")

spec = importlib.util.spec_from_file_location("session_cache", CACHE)
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

passed = failed = 0
fails = []


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        fails.append(f"  FAIL [{name}]")


# --- unit: sanitizer ---
s = sc._sanitize_fts5_query
check("plain term quoted",        s("repo") == '"repo"')
check("operator neutralized",     s("repo OR") == '"repo"')            # OR dropped (stopword) + quoted
check("multi-term OR-joined",     s("vector store") == '"vector" OR "store"')
check("punct/operator only->None", s("!!! ^ *") is None)              # no word tokens -> LIKE fallback
check("all-stopwords kept raw",   s("and or the") == '"and" OR "or" OR "the"')
check("dangling quote safe",      '"' in s('key"') and s('key"').startswith('"key'))


def live(keyword):
    r = subprocess.run([sys.executable, CACHE, json.dumps({"action": "query", "keyword": keyword, "limit": 3})],
                       capture_output=True, text=True)
    return json.loads(r.stdout).get("total", -1)


# --- live control: the exact malformed case that used to return 0 ---
# Needs at least one saved session whose text contains "repo". A fresh install has none,
# so the positive checks are skipped (not failed) until such a session exists.
if live("repo") >= 1:
    check("live positive 'repo' finds record",   True)
    check("live malformed 'repo OR' now finds",   live("repo OR") >= 1)      # was 0 before the fix (recall loss)
else:
    print("  skip: live 'repo' checks (no saved session mentions 'repo' yet)")
check("live nonsense abstains",               live("zzznosuchtermxyz") == 0)

print(f"session-cache FTS regression: {passed} passed, {failed} failed")
for line in fails:
    print(line)
sys.exit(0 if failed == 0 else 1)
