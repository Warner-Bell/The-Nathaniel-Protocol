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



def _config_model_name(default="sentence-transformers/all-MiniLM-L6-v2"):
    """Resolve the embedding model from config.json.

    The model name used to be hardcoded here AND in the two sibling scripts. config.json
    carried a decorative `model_name` that nothing read, so a swap in one place would
    silently desync query-time embedding from index-time embedding with no error and
    corrupt retrieval. Single source of truth now.
    """
    try:
        with open(os.path.join(VS_DIR, "config.json")) as f:
            return json.load(f).get("model_name") or default
    except (OSError, json.JSONDecodeError, TypeError):
        return default




def _config_max_tokens(default=256):
    """Tokenizer truncation ceiling, from config.json."""
    try:
        with open(os.path.join(VS_DIR, "config.json")) as f:
            return int(json.load(f).get("max_tokens") or default)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return default


def _apply_max_tokens(model):
    """Raise the tokenizer truncation ceiling on a fastembed model, in place.

    fastembed pins max_length=128 for all-MiniLM-L6-v2 even though the model card
    advertises 256, and it SILENTLY IGNORES a max_length constructor kwarg (verified
    2026-08-05: identical vectors, cosine 1.000000). The only effective route is the
    inner tokenizer. At 128, 1,137 of 2,359 entries (48.2%) were truncated before
    embedding, with no warning and no record.

    Index-time and sync-time must pass through here so a re-embedded entry cannot
    silently diverge from the full build.
    """
    want = _config_max_tokens()
    try:
        tok = model.model.tokenizer
        # Truncation AND padding must move together. fastembed pads to a fixed length and
        # builds input_ids with np.array(); raising truncation alone makes long docs 256
        # tokens while short docs still pad to 128, so the batch is ragged and numpy
        # raises "inhomogeneous shape" inside onnx_embed. A single-document test cannot
        # surface this because one document is never ragged.
        if (tok.truncation or {}).get("max_length") != want:
            tok.enable_truncation(max_length=want)
        if (tok.padding or {}).get("length") != want:
            tok.enable_padding(length=want)
    except Exception as e:
        import warnings
        warnings.warn(f"could not raise tokenizer max_length to {want}: {e}")
    return model


MODEL_NAME = _config_model_name()
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
    model = _apply_max_tokens(TextEmbedding(model_name=MODEL_NAME))
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
        "model": MODEL_NAME.split("/")[-1],
        "model_version": model_version,
        "dimensions": DIMENSIONS,
        "built": now,
        "last_sync": now,
        "entry_count": len(texts),
        "entries": meta_entries,
    }
    with open(os.path.join(VS_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    # Preserve curated config keys this builder does not own.
    #
    # This block used to construct config.json from scratch on every build, which silently
    # ERASED `min_semantic_score` and `_min_semantic_score_calibration`. Those are measured
    # values (calibrated against the 30-query pipeline suite), not build artifacts. The loss
    # was invisible because kb_query.py's fallback default happened to equal the calibrated
    # figure, so behavior survived by coincidence while the provenance was destroyed. Any
    # recalibration would have been wiped by the next rebuild.
    try:
        with open(os.path.join(VS_DIR, "config.json")) as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError):
        config = {}

    config.update({
        "model_name": MODEL_NAME,
        "model_version": model_version,
        "dimensions": DIMENSIONS,
        "fusion_method": "rrf",
        "rrf_k": 60,
        "rrf_weights": {"semantic": 1.0, "keyword": 1.0},
        "score_floor": 0.005,
        "created": config.get("created", now),
        "last_built": now,
        "stores": {
            "patterns": "Intelligence/patterns.json",
            "knowledge": "Intelligence/knowledge.json",
            "reasoning": "Intelligence/reasoning.json",
            "memory": "Memory/memory.json",
        },
    })
    if "min_semantic_score" not in config:
        # Never leave the semantic gate undeclared; kb_query would fall back to its literal.
        config["min_semantic_score"] = 0.36
    if "max_tokens" not in config:
        # Declare the truncation ceiling the build actually used (_apply_max_tokens), so
        # query and sync embed with the same limit and tests/test_truncation.py can check it.
        # fastembed pins all-MiniLM-L6-v2 at 128 tokens and ignores a max_length kwarg;
        # raising this value requires a full re-vectorize.
        config["max_tokens"] = _config_max_tokens()
    with open(os.path.join(VS_DIR, "config.json"), "w") as f:
        json.dump(config, f, indent=2)

    elapsed = time.time() - start
    size_kb = (vectors.nbytes + os.path.getsize(os.path.join(VS_DIR, "metadata.json"))
               + os.path.getsize(os.path.join(VS_DIR, "config.json"))) / 1024

    print(f"Built {len(texts)} entries, {DIMENSIONS} dims, {size_kb:.0f}KB, {elapsed:.1f}s")
    return len(texts), elapsed


if __name__ == "__main__":
    build()
