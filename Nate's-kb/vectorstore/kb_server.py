#!/usr/bin/env python3
"""kb_server.py - MCP stdio server exposing vectorstore operations.

Tools: kb_search, kb_sync, kb_rebuild.
Model loads once on startup, reused across invocations.
"""

import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("kb-vectorstore")


@mcp.tool()
def kb_search(query: str = "", top_k: int = 5, store: str | None = None,
              min_confidence: float | None = None, max_confidence: float | None = None,
              tag: str | None = None, category: str | None = None,
              min_access_count: int | None = None, not_accessed_since_days: int | None = None,
              level: int | None = None, saved: str | None = None) -> str:
    """Search the KB using hybrid semantic + keyword search with RRF fusion.

    Args:
        query: Search string. If empty with filters, runs pure filter mode.
        top_k: Max results (default 5).
        store: Optional filter: patterns, knowledge, reasoning, or memory.
        min_confidence: Filter entries with confidence >= value.
        max_confidence: Filter entries with confidence <= value.
        tag: Filter entries containing this tag.
        category: Filter entries in this category.
        min_access_count: Filter entries with accessCount >= value.
        not_accessed_since_days: Filter entries NOT accessed in N days.
        level: Filter by derived distillation level (1-4).
        saved: Run a named saved query from saved-queries.json.
    """
    from kb_query import search, _load_saved_query

    filters = {}
    if saved:
        sq = _load_saved_query(saved)
        if sq:
            filters = dict(sq.get("filters", {}))

    if min_confidence is not None:
        filters["min_confidence"] = min_confidence
    if max_confidence is not None:
        filters["max_confidence"] = max_confidence
    if tag is not None:
        filters["tags"] = [tag]
    if category is not None:
        filters["category"] = category
    if min_access_count is not None:
        filters["min_access_count"] = min_access_count
    if not_accessed_since_days is not None:
        filters["not_accessed_since_days"] = not_accessed_since_days
    if level is not None:
        filters["level"] = level

    results = search(query or None, top_k=top_k, store=store or None, filters=filters or None)
    return json.dumps(results, indent=2)


@mcp.tool()
def kb_sync() -> str:
    """Incrementally sync vectorstore after intelligence updates.

    Re-embeds only changed entries. Atomic writes.
    """
    from kb_sync import sync
    result = sync()
    return json.dumps(result, indent=2)


@mcp.tool()
def kb_rebuild() -> str:
    """Full vectorstore rebuild from all JSON stores.

    Use when sync reports issues or after major changes.
    """
    from kb_vectorize import build
    count, elapsed = build()
    return json.dumps({"entries": count, "elapsed": round(elapsed, 1)})


if __name__ == "__main__":
    mcp.run(transport="stdio")
