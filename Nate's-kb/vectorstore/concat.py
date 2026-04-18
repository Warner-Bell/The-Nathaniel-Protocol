"""Field concatenation with D-2 fallback chains for vectorstore embedding input.

Each store has different field names for the same semantic role. This module
resolves them via fallback chains and produces pipe-delimited text suitable
for embedding, plus a SHA-256 content hash for sync change detection.
"""

import hashlib
from typing import Any

# D-2 fallback chains per store
# Primary text: content (canonical). pattern/summary kept as drift detection fallbacks.
# Context: context | evidence | detail
# Reasoning extras: reuse_signal, intent
FALLBACK_PRIMARY = ("content", "pattern", "summary")
FALLBACK_CONTEXT = ("context", "evidence", "detail")


def _resolve(entry: dict, fields: tuple[str, ...]) -> str:
    """Return first non-empty string from fallback chain."""
    for i, f in enumerate(fields):
        val = entry.get(f)
        if val and isinstance(val, str) and val.strip():
            if i > 0 and fields == FALLBACK_PRIMARY:
                import logging
                logging.warning(f"Drift detected: entry {entry.get('id','?')} using '{f}' instead of 'content'")
            return val.strip()
    return ""


def concatenate_entry(entry: dict, store: str) -> str:
    """Concatenate entry fields per D-2 fallback chains, pipe-delimited.

    Args:
        entry: Single entry dict from any store.
        store: One of 'patterns', 'knowledge', 'reasoning', 'memory'.

    Returns:
        Pipe-delimited concatenated text for embedding.
    """
    primary = _resolve(entry, FALLBACK_PRIMARY)
    context = _resolve(entry, FALLBACK_CONTEXT)

    parts = []
    if primary:
        parts.append(primary)
    if context:
        parts.append(context)

    # Reasoning extras
    if store == "reasoning":
        for field in ("reuse_signal", "intent"):
            val = entry.get(field)
            if val and isinstance(val, str) and val.strip():
                parts.append(val.strip())

    # Tags
    tags = entry.get("tags")
    if isinstance(tags, list):
        tag_str = " ".join(str(t) for t in tags if t)
        if tag_str.strip():
            parts.append(tag_str.strip())

    return " | ".join(parts)


def content_hash(text: str) -> str:
    """SHA-256 hex digest of concatenated text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def iter_store(data: dict, store: str) -> list[tuple[str, dict]]:
    """Yield (id, entry) pairs from a store, handling structural differences.

    Patterns/knowledge/reasoning: data["entries"] is a list, each has "id".
    Memory: data["memories"] is a dict keyed by ID.
    """
    if store == "memory":
        memories = data.get("memories", {})
        return [(mid, m) for mid, m in memories.items()]
    else:
        entries = data.get("entries", [])
        return [(e.get("id", f"unknown_{i}"), e) for i, e in enumerate(entries)]
