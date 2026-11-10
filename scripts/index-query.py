#!/usr/bin/env python3
"""index-query.py - On-demand access to the CSR intelligence indexes.

The patterns/knowledge/reasoning indexes outgrew cold-start context (~290k tokens
on 2026-10-27, mostly `summaries` and `byTag`). Session start now loads only a
compact HEAD per index; summaries and tag lookups are fetched on demand here
(or via kb_search for semantic matches). Same move session-cache.py made for
session-index.json. memory-index.json is small and is still read whole.

Usage (JSON arg, like session-cache.py):
    python3 scripts/index-query.py '{"action":"head"}'
        stats, category/type counts, and the newest N ids with summaries per index
    python3 scripts/index-query.py '{"action":"tag","tags":["lease-terms"],"stores":["knowledge"]}'
        ids + summaries filed under any of the tags (exact, case-insensitive)
    python3 scripts/index-query.py '{"action":"ids","ids":["know-0001","reason-0001"]}'
        summaries (and reasoning intents) for specific ids
    python3 scripts/index-query.py '{"action":"keyword","keyword":"deposit","stores":["knowledge"]}'
        substring match over summaries (+ reasoning intents)
    python3 scripts/index-query.py '{"action":"tags","prefix":"lease","stores":["knowledge"]}'
        list tag names (with counts), optionally filtered by prefix
    python3 scripts/index-query.py '{"action":"signals"}'
        every reasoning entry's reuse_signal as compact "id: signal" lines. Loaded at
        session start so situation-shaped matches ("we figured this out before")
        surface without a query; reasoning is retrieved by situation, not topic.

Optional: "limit" (default 25 for lookups, 10 per index for head).
Exit codes: 0 = ok, 2 = bad input / missing index.
"""

import json
import sys
from pathlib import Path

KB = Path(__file__).resolve().parent.parent / "Nate's-kb"
INDEXES = {
    "patterns": KB / "Intelligence" / "patterns-index.json",
    "knowledge": KB / "Intelligence" / "knowledge-index.json",
    "reasoning": KB / "Intelligence" / "reasoning-index.json",
}
COUNT_SECTIONS = ("byCategory", "byType", "byConfidence", "byProvenance")


def load(store):
    p = INDEXES[store]
    if not p.exists():
        raise FileNotFoundError(str(p))
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def store_of(eid):
    if eid.startswith("know-"):
        return "knowledge"
    if eid.startswith("reason-"):
        return "reasoning"
    return "patterns"


def row(idx, eid):
    r = {"id": eid, "summary": idx.get("summaries", {}).get(eid)}
    intent = idx.get("intents", {}).get(eid) if isinstance(idx.get("intents"), dict) else None
    if intent:
        r["intent"] = intent
    return r


def head(stores, limit):
    out = {}
    for s in stores:
        idx = load(s)
        counts = {sec: {k: len(v) for k, v in idx[sec].items()}
                  for sec in COUNT_SECTIONS if isinstance(idx.get(sec), dict)}
        out[s] = {
            "stats": idx.get("stats", {}),
            "counts": counts,
            "tag_count": len(idx.get("byTag", {})),
            "recent": [row(idx, e) for e in idx.get("recentIds", [])[:limit]],
        }
    return out


def by_tag(stores, tags, limit):
    want = {t.lower() for t in tags}
    hits = []
    for s in stores:
        idx = load(s)
        seen = set()
        for tag, ids in idx.get("byTag", {}).items():
            if tag.lower() in want:
                for e in ids:
                    if e not in seen:
                        seen.add(e)
                        hits.append({"store": s, **row(idx, e)})
    return hits[:limit], len(hits)


def by_ids(ids):
    cache, hits = {}, []
    for e in ids:
        s = store_of(e)
        cache.setdefault(s, load(s))
        r = row(cache[s], e)
        r["store"] = s
        r["found"] = r["summary"] is not None
        hits.append(r)
    return hits


def by_keyword(stores, kw, limit):
    k = kw.lower()
    hits = []
    for s in stores:
        idx = load(s)
        intents = idx.get("intents", {}) if isinstance(idx.get("intents"), dict) else {}
        for e, summ in idx.get("summaries", {}).items():
            text = f"{summ or ''} {intents.get(e, '')}".lower()
            if k in text:
                hits.append({"store": s, **row(idx, e)})
    return hits[:limit], len(hits)


def tag_names(stores, prefix, limit):
    p = (prefix or "").lower()
    out = {}
    for s in stores:
        tags = {t: len(v) for t, v in load(s).get("byTag", {}).items() if t.lower().startswith(p)}
        out[s] = dict(sorted(tags.items(), key=lambda kv: -kv[1])[:limit])
    return out


def signals():
    """Reasoning reuse signals, one compact line each (plain text, not JSON)."""
    idx = load("reasoning")
    lines = [f"{e}: {s}" for e, s in idx.get("summaries", {}).items() if s]
    return lines


def main(argv):
    try:
        params = json.loads(argv[1]) if len(argv) > 1 else {"action": "head"}
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"bad JSON: {e}"}))
        return 2
    action = params.get("action", "head")
    stores = params.get("stores") or list(INDEXES)
    bad = [s for s in stores if s not in INDEXES]
    if bad:
        print(json.dumps({"error": f"unknown store(s): {bad}", "valid": list(INDEXES)}))
        return 2
    try:
        if action == "head":
            res = head(stores, int(params.get("limit", 10)))
        elif action == "tag":
            hits, total = by_tag(stores, params.get("tags") or [], int(params.get("limit", 25)))
            res = {"total": total, "results": hits}
        elif action == "ids":
            res = {"results": by_ids(params.get("ids") or [])}
        elif action == "keyword":
            if not params.get("keyword"):
                print(json.dumps({"error": "keyword required"}))
                return 2
            hits, total = by_keyword(stores, params["keyword"], int(params.get("limit", 25)))
            res = {"total": total, "results": hits}
        elif action == "signals":
            lines = signals()
            print(f"# reasoning reuse signals ({len(lines)}); fetch an entry by id when one matches")
            print("\n".join(lines))
            return 0
        elif action == "tags":
            res = tag_names(stores, params.get("prefix"), int(params.get("limit", 50)))
        else:
            print(json.dumps({"error": f"unknown action: {action}",
                              "valid": ["head", "tag", "ids", "keyword", "tags", "signals"]}))
            return 2
    except FileNotFoundError as e:
        print(json.dumps({"error": f"index missing: {e}"}))
        return 2
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except BrokenPipeError:  # output piped to head etc.; not an error
        sys.stderr.close()
        sys.exit(0)
