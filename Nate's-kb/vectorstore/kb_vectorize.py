#!/usr/bin/env python3
"""kb_vectorize.py - Full vectorstore build from all four JSON stores.

Reads patterns.json, knowledge.json, reasoning.json, memory.json.
Embeds all entries via fastembed (all-MiniLM-L6-v2, 384 dims).
Writes vectors.npy, metadata.json, config.json to vectorstore/.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import numpy as np
from fastembed import TextEmbedding

from concat import concatenate_entry, content_hash, iter_store

# Paths relative to Nate's-kb/
KB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VS_DIR = os.path.dirname(os.path.abspath(__file__))

STORES = {
    "patterns": os.path.join(KB_ROOT, "Intelligence", "patterns.json"),
    "knowledge": os.path.join(KB_ROOT, "Intelligence", "knowledge.json"),
    "reasoning": os.path.join(KB_ROOT, "Intelligence", "reasoning.json"),
    "memory": os.path.join(KB_ROOT, "Memory", "memory.json"),
}

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DIMENSIONS = 384


def build():
    """Execute full vectorstore build. Returns (entry_count, elapsed_seconds)."""
    start = time.time()

    # Collect entries from all stores
    texts = []
    meta_entries = []
    seen_ids = {}
    row = 0

    for store_name, path in STORES.items():
        if not os.path.exists(path):
            print(f"Warning: {path} not found, skipping {store_name}", file=sys.stderr)
            continue
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: {path} malformed ({e}), skipping {store_name}", file=sys.stderr)
            continue

        for entry_id, entry in iter_store(data, store_name):
            text = concatenate_entry(entry, store_name)
            if not text.strip():
                continue
            if entry_id in seen_ids:
                print(f"Warning: duplicate ID {entry_id} in {store_name}, using last occurrence", file=sys.stderr)
                # Overwrite previous occurrence
                prev_row = seen_ids[entry_id]
                texts[prev_row] = text
                meta_entries[prev_row]["hash"] = content_hash(text)
                continue
            seen_ids[entry_id] = row
            texts.append(text)
            meta_entries.append({
                "id": entry_id,
                "store": store_name,
                "row": row,
                "hash": content_hash(text),
            })
            row += 1

    if not texts:
        print("Error: No entries to embed.", file=sys.stderr)
        sys.exit(1)

    # Embed
    model = TextEmbedding(model_name=MODEL_NAME)
    vectors = np.array(list(model.embed(texts)), dtype=np.float32)

    # Write artifacts
    os.makedirs(VS_DIR, exist_ok=True)

    np.save(os.path.join(VS_DIR, "vectors.npy"), vectors)

    now = datetime.now(timezone.utc).astimezone().isoformat()
    model_version = getattr(model, "model_version", None)
    if not model_version:
        try:
            import fastembed
            model_version = f"fastembed-{fastembed.__version__}"
        except Exception:
            model_version = "unknown"

    metadata = {
        "model": "all-MiniLM-L6-v2",
        "model_version": model_version,
        "dimensions": DIMENSIONS,
        "built": now,
        "last_sync": now,
        "entry_count": len(texts),
        "entries": meta_entries,
    }
    with open(os.path.join(VS_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    config = {
        "model_name": MODEL_NAME,
        "model_version": model_version,
        "dimensions": DIMENSIONS,
        "fusion_method": "rrf",
        "rrf_k": 60,
        "rrf_weights": {"semantic": 1.0, "keyword": 1.0},
        "score_floor": 0.005,
        "created": now,
        "stores": {
            "patterns": "Intelligence/patterns.json",
            "knowledge": "Intelligence/knowledge.json",
            "reasoning": "Intelligence/reasoning.json",
            "memory": "Memory/memory.json",
        },
    }
    with open(os.path.join(VS_DIR, "config.json"), "w") as f:
        json.dump(config, f, indent=2)

    elapsed = time.time() - start
    size_kb = (vectors.nbytes + os.path.getsize(os.path.join(VS_DIR, "metadata.json"))
               + os.path.getsize(os.path.join(VS_DIR, "config.json"))) / 1024

    print(f"Built {len(texts)} entries, {DIMENSIONS} dims, {size_kb:.0f}KB, {elapsed:.1f}s")
    return len(texts), elapsed


if __name__ == "__main__":
    build()
