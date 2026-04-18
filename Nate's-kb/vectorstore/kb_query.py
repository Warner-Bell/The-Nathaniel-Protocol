#!/usr/bin/env python3
"""kb_query.py - Hybrid semantic + keyword search with RRF fusion.

Importable module and CLI tool. Falls back to keyword-only when vectorstore absent.
Supports structured filters for maintenance queries and pure filter mode.
"""

import argparse
import json
import os
import sys
import warnings
from datetime import datetime, timedelta

import numpy as np

from concat import concatenate_entry, iter_store

KB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VS_DIR = os.path.dirname(os.path.abspath(__file__))

STORE_PATHS = {
    "patterns": os.path.join(KB_ROOT, "Intelligence", "patterns.json"),
    "knowledge": os.path.join(KB_ROOT, "Intelligence", "knowledge.json"),
    "reasoning": os.path.join(KB_ROOT, "Intelligence", "reasoning.json"),
    "memory": os.path.join(KB_ROOT, "Memory", "memory.json"),
}

INDEX_PATHS = {
    "patterns": os.path.join(KB_ROOT, "Intelligence", "patterns-index.json"),
    "knowledge": os.path.join(KB_ROOT, "Intelligence", "knowledge-index.json"),
    "reasoning": os.path.join(KB_ROOT, "Intelligence", "reasoning-index.json"),
}

SYNONYM_PATH = os.path.join(KB_ROOT, "Intelligence", "synonym-map.json")
SAVED_QUERIES_PATH = os.path.join(VS_DIR, "saved-queries.json")


# --- Distillation Levels ---

def distillation_level(entry: dict) -> int:
    """Derive distillation level from accessCount and confidence.

    L4 (canonical): ac >= 15, conf >= 0.85
    L3 (battle-tested): ac >= 7, conf >= 0.8
    L2 (validated): ac >= 3, conf >= 0.7
    L1 (raw): everything else
    """
    ac = entry.get("accessCount", 0)
    conf = entry.get("confidence", 0)
    if ac >= 15 and conf >= 0.85:
        return 4
    if ac >= 7 and conf >= 0.8:
        return 3
    if ac >= 3 and conf >= 0.7:
        return 2
    return 1


LEVEL_NAMES = {1: "raw", 2: "validated", 3: "battle-tested", 4: "canonical"}


# --- Filters ---

def _days_ago(days: int) -> str:
    """Return ISO date string for N days ago."""
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


def apply_filters(entries: list, filters: dict) -> list:
    """Apply structured filters to a list of entry dicts."""
    result = entries
    if filters.get("min_confidence") is not None:
        result = [e for e in result if e.get("confidence", 0) >= filters["min_confidence"]]
    if filters.get("max_confidence") is not None:
        result = [e for e in result if e.get("confidence", 0) <= filters["max_confidence"]]
    if filters.get("tags"):
        result = [e for e in result if all(t in e.get("tags", []) for t in filters["tags"])]
    if filters.get("category"):
        result = [e for e in result if e.get("category") == filters["category"]]
    if filters.get("min_access_count") is not None:
        result = [e for e in result if e.get("accessCount", 0) >= filters["min_access_count"]]
    if filters.get("max_access_count") is not None:
        result = [e for e in result if e.get("accessCount", 0) <= filters["max_access_count"]]
    if filters.get("accessed_since_days") is not None:
        cutoff = _days_ago(filters["accessed_since_days"])
        result = [e for e in result if e.get("lastAccessed", "") >= cutoff]
    if filters.get("not_accessed_since_days") is not None:
        cutoff = _days_ago(filters["not_accessed_since_days"])
        result = [e for e in result if e.get("lastAccessed", "") < cutoff]
    if filters.get("level") is not None:
        result = [e for e in result if distillation_level(e) == filters["level"]]
    return result


def _load_saved_query(name: str) -> dict | None:
    """Load a named saved query from saved-queries.json."""
    data = _load_json(SAVED_QUERIES_PATH)
    if not data or name not in data:
        return None
    return data[name]


def _load_all_entries(store_filter: str | None = None) -> list:
    """Load all entries from stores for pure filter mode."""
    entries = []
    stores = [store_filter] if store_filter else ["patterns", "knowledge", "reasoning", "memory"]
    for store_name in stores:
        path = STORE_PATHS.get(store_name)
        if not path:
            continue
        data = _load_json(path)
        if not data:
            continue
        if store_name == "memory":
            for mid, m in data.get("memories", {}).items():
                m["id"] = mid
                m["_store"] = "memory"
                entries.append(m)
        else:
            for e in data.get("entries", []):
                e["_store"] = store_name
                entries.append(e)
    return entries


# --- Formatting ---

def _format_table(results: list) -> str:
    """Format results as a human-readable table."""
    if not results:
        return "No results."
    header = f"{'ID':<16}| {'Store':<10}| {'Lvl':<4}| {'Conf':<5}| {'AC':<4}| {'Tags':<30}| Content"
    sep = "-" * 16 + "|" + "-" * 10 + "|" + "-" * 4 + "|" + "-" * 5 + "|" + "-" * 4 + "|" + "-" * 30 + "|" + "-" * 20
    lines = [header, sep]
    for r in results:
        tags = ", ".join(r.get("tags", [])[:3])
        if len(r.get("tags", [])) > 3:
            tags += "..."
        content = (r.get("content", "") or "")[:40].replace("\n", " ")
        lvl = r.get("level", distillation_level(r))
        lines.append(
            f"{r.get('id', '?'):<16}| {r.get('_store', r.get('store', '?')):<10}| {lvl:<4}| {r.get('confidence', 0):<5.2f}| {r.get('accessCount', 0):<4}| {tags:<30}| {content}"
        )
    return "\n".join(lines)


def _format_ids(results: list) -> str:
    """Format results as newline-separated IDs."""
    return "\n".join(r.get("id", "?") for r in results)


# --- Core ---

def _load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _load_synonyms():
    data = _load_json(SYNONYM_PATH)
    if not data:
        return {}
    syn_map = {}
    for group in data.get("synonyms", {}).values():
        terms = group if isinstance(group, list) else []
        for t in terms:
            syn_map[t.lower()] = [x.lower() for x in terms if x.lower() != t.lower()]
    return syn_map


def _check_consistency():
    """Verify vectorstore artifact consistency. Returns (vectors, metadata, config) or None."""
    vec_path = os.path.join(VS_DIR, "vectors.npy")
    meta_path = os.path.join(VS_DIR, "metadata.json")
    conf_path = os.path.join(VS_DIR, "config.json")

    if not all(os.path.exists(p) for p in [vec_path, meta_path, conf_path]):
        return None

    try:
        vectors = np.load(vec_path)
        meta = _load_json(meta_path)
        conf = _load_json(conf_path)
        if not meta or not conf:
            return None
        if vectors.shape[0] != meta.get("entry_count", -1):
            warnings.warn(f"Vector/metadata row mismatch: {vectors.shape[0]} vs {meta['entry_count']}")
            return None
        if conf.get("model_version") != meta.get("model_version"):
            warnings.warn("Model version mismatch between config and metadata")
            return None
        return vectors, meta, conf
    except Exception as e:
        warnings.warn(f"Vectorstore load error: {e}")
        return None


def _semantic_search(query, vectors, meta, top_n):
    """Embed query, dot product against pre-normalized vectors."""
    from fastembed import TextEmbedding
    model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    query_vec = np.array(list(model.embed([query]))[0], dtype=np.float32)
    scores = vectors @ query_vec
    top_idx = np.argsort(scores)[::-1][:top_n]
    results = []
    for rank, idx in enumerate(top_idx):
        entry = meta["entries"][idx]
        results.append({"id": entry["id"], "store": entry["store"], "score": float(scores[idx]), "rank": rank + 1})
    return results


def _keyword_search(query, top_n):
    """Tag + summary match with synonym expansion."""
    syn_map = _load_synonyms()
    tokens = query.lower().split()
    expanded = set(tokens)
    for t in tokens:
        expanded.update(syn_map.get(t, []))
    total_terms = len(tokens) if tokens else 1

    candidates = {}

    # Search index files (patterns, knowledge, reasoning)
    for store_name, idx_path in INDEX_PATHS.items():
        data = _load_json(idx_path)
        if not data:
            continue
        by_tag = data.get("byTag", {})
        for term in expanded:
            for tag, ids in by_tag.items():
                if term in tag.lower():
                    for eid in ids:
                        key = (eid, store_name)
                        candidates[key] = candidates.get(key, 0) + 1.0 / total_terms

        summaries = data.get("summaries", {})
        for eid, summary in summaries.items():
            if not isinstance(summary, str):
                continue
            summary_lower = summary.lower()
            for term in expanded:
                if term in summary_lower:
                    key = (eid, store_name)
                    candidates[key] = candidates.get(key, 0) + 0.5 / total_terms

    # Memory: search tags and content directly
    mem_data = _load_json(STORE_PATHS.get("memory", ""))
    if mem_data:
        for mid, m in mem_data.get("memories", {}).items():
            tags = [t.lower() for t in m.get("tags", []) if isinstance(t, str)]
            content = (m.get("content", "") or "").lower()
            for term in expanded:
                if any(term in tag for tag in tags):
                    key = (mid, "memory")
                    candidates[key] = candidates.get(key, 0) + 1.0 / total_terms
                if term in content:
                    key = (mid, "memory")
                    candidates[key] = candidates.get(key, 0) + 0.5 / total_terms

    ranked = sorted(candidates.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [{"id": k[0], "store": k[1], "score": v, "rank": i + 1} for i, (k, v) in enumerate(ranked)]


def _rrf_fuse(semantic_results, keyword_results, k, weights, score_floor, store_filter):
    """RRF fusion: score = sum(weight_i / (k + rank_i)) per path."""
    w_sem = weights.get("semantic", 1.0)
    w_key = weights.get("keyword", 1.0)

    scores = {}
    sem_ranks = {}
    key_ranks = {}

    for r in semantic_results:
        uid = (r["id"], r["store"])
        if store_filter and r["store"] != store_filter:
            continue
        scores[uid] = scores.get(uid, 0) + w_sem / (k + r["rank"])
        sem_ranks[uid] = r["rank"]

    for r in keyword_results:
        uid = (r["id"], r["store"])
        if store_filter and r["store"] != store_filter:
            continue
        scores[uid] = scores.get(uid, 0) + w_key / (k + r["rank"])
        key_ranks[uid] = r["rank"]

    # Apply score floor
    scores = {uid: s for uid, s in scores.items() if s >= score_floor}

    # Sort by score, tiebreak by distillation level (higher wins)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [
        {
            "id": uid[0],
            "store": uid[1],
            "score": round(s, 6),
            "semantic_rank": sem_ranks.get(uid),
            "keyword_rank": key_ranks.get(uid),
        }
        for uid, s in ranked
    ]


def _populate_content(results, top_k):
    """Load source JSON and populate content + level fields."""
    results = results[:top_k]
    if not results:
        return results

    store_data = {}
    for r in results:
        sn = r["store"]
        if sn not in store_data:
            store_data[sn] = _load_json(STORE_PATHS.get(sn, ""))

    for r in results:
        data = store_data.get(r["store"])
        if not data:
            r["content"] = ""
            r["level"] = 1
            continue
        if r["store"] == "memory":
            entry = data.get("memories", {}).get(r["id"], {})
        else:
            entry = next((e for e in data.get("entries", []) if e.get("id") == r["id"]), {})
        r["content"] = concatenate_entry(entry, r["store"])
        r["level"] = distillation_level(entry)

    return results


def search(query=None, top_k=5, store=None, filters=None):
    """Hybrid search with optional structured filters.

    Args:
        query: Search string. If None/empty with filters, runs pure filter mode.
        top_k: Max results to return.
        store: Optional store filter ('patterns', 'knowledge', 'reasoning', 'memory').
        filters: Optional dict of structured filters.

    Returns:
        List of dicts with id, store, score, semantic_rank, keyword_rank, content, level.
    """
    # Pure filter mode: no query, just filters
    if (not query or not query.strip()) and filters:
        entries = _load_all_entries(store)
        filtered = apply_filters(entries, filters)
        filtered.sort(key=lambda e: e.get("confidence", 0), reverse=True)
        results = []
        for e in filtered[:top_k]:
            results.append({
                "id": e.get("id", "?"),
                "store": e.get("_store", "?"),
                "score": e.get("confidence", 0),
                "semantic_rank": None,
                "keyword_rank": None,
                "content": concatenate_entry(e, e.get("_store", "")),
                "level": distillation_level(e),
                **{k: v for k, v in e.items() if k in ("tags", "confidence", "accessCount", "lastAccessed", "category")},
            })
        return results

    if not query or not query.strip():
        return []

    vs = _check_consistency()

    k = 60
    weights = {"semantic": 1.0, "keyword": 1.0}
    score_floor = 0.005

    conf_path = os.path.join(VS_DIR, "config.json")
    conf = _load_json(conf_path)
    if conf:
        k = conf.get("rrf_k", k)
        weights = conf.get("rrf_weights", weights)
        score_floor = conf.get("score_floor", score_floor)

    top_n = top_k * 3

    semantic_results = []
    if vs:
        vectors, meta, _ = vs
        semantic_results = _semantic_search(query, vectors, meta, top_n)

    keyword_results = _keyword_search(query, top_n)

    if not semantic_results and not keyword_results:
        return []

    fused = _rrf_fuse(semantic_results, keyword_results, k, weights, score_floor, store)
    results = _populate_content(fused, top_k)

    # Apply post-search filters if provided
    if filters:
        store_data = {}
        filtered = []
        for r in results:
            sn = r["store"]
            if sn not in store_data:
                store_data[sn] = _load_json(STORE_PATHS.get(sn, ""))
            data = store_data.get(sn)
            if not data:
                continue
            if sn == "memory":
                entry = data.get("memories", {}).get(r["id"], {})
            else:
                entry = next((e for e in data.get("entries", []) if e.get("id") == r["id"]), {})
            if apply_filters([entry], filters):
                # Carry useful fields from entry to result
                for field in ("tags", "confidence", "accessCount", "lastAccessed", "category"):
                    if field in entry and field not in r:
                        r[field] = entry[field]
                filtered.append(r)
        results = filtered

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KB hybrid search with structured filters")
    parser.add_argument("query", nargs="?", default="", help="Search query (optional if using --saved or filters)")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--store", choices=["patterns", "knowledge", "reasoning", "memory"], default=None)
    parser.add_argument("--min-confidence", type=float, default=None)
    parser.add_argument("--max-confidence", type=float, default=None)
    parser.add_argument("--tag", action="append", dest="tags", default=None, help="Filter by tag (repeatable, AND logic)")
    parser.add_argument("--category", default=None)
    parser.add_argument("--accessed-since", type=int, default=None, metavar="DAYS")
    parser.add_argument("--not-accessed-since", type=int, default=None, metavar="DAYS")
    parser.add_argument("--min-access-count", type=int, default=None)
    parser.add_argument("--max-access-count", type=int, default=None)
    parser.add_argument("--level", type=int, choices=[1, 2, 3, 4], default=None, help="Distillation level")
    parser.add_argument("--format", choices=["json", "table", "ids"], default="json", dest="output_format")
    parser.add_argument("--saved", default=None, help="Run a named saved query")
    args = parser.parse_args()

    # Build filters from args + saved query
    filters = {}
    if args.saved:
        sq = _load_saved_query(args.saved)
        if sq:
            filters = dict(sq.get("filters", {}))
            if not args.output_format or args.output_format == "json":
                args.output_format = sq.get("format", "json")
        else:
            print(f"Unknown saved query: {args.saved}", file=sys.stderr)
            sys.exit(1)

    # CLI flags override saved query
    if args.min_confidence is not None:
        filters["min_confidence"] = args.min_confidence
    if args.max_confidence is not None:
        filters["max_confidence"] = args.max_confidence
    if args.tags:
        filters["tags"] = args.tags
    if args.category:
        filters["category"] = args.category
    if args.accessed_since is not None:
        filters["accessed_since_days"] = args.accessed_since
    if args.not_accessed_since is not None:
        filters["not_accessed_since_days"] = args.not_accessed_since
    if args.min_access_count is not None:
        filters["min_access_count"] = args.min_access_count
    if args.max_access_count is not None:
        filters["max_access_count"] = args.max_access_count
    if args.level is not None:
        filters["level"] = args.level

    results = search(args.query or None, top_k=args.top_k, store=args.store, filters=filters or None)

    if args.output_format == "table":
        print(_format_table(results))
    elif args.output_format == "ids":
        print(_format_ids(results))
    else:
        print(json.dumps(results, indent=2))
