#!/usr/bin/env python3
"""kb_sync.py - Incremental vectorstore sync. Re-embeds only changed entries.

Compares SHA-256 content hashes against metadata.json to detect changes.
Atomic writes via temp files + os.replace().
"""

import json
import os
import sys
import time
import warnings

import numpy as np

from concat import concatenate_entry, content_hash, iter_store

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


def _load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def sync():
    """Incremental sync. Returns dict with counts and elapsed time."""
    start = time.time()

    meta_path = os.path.join(VS_DIR, "metadata.json")
    vec_path = os.path.join(VS_DIR, "vectors.npy")
    conf_path = os.path.join(VS_DIR, "config.json")

    # If vectorstore missing or model mismatch, delegate to full build
    if not all(os.path.exists(p) for p in [meta_path, vec_path, conf_path]):
        print("Vectorstore not found, running full build...", file=sys.stderr)
        from kb_vectorize import build
        build()
        return {"action": "full_build", "reason": "missing_artifacts"}

    meta = _load_json(meta_path)
    conf = _load_json(conf_path)
    if not meta or not conf:
        from kb_vectorize import build
        build()
        return {"action": "full_build", "reason": "malformed_metadata"}

    vectors = np.load(vec_path)
    if vectors.shape[0] != meta.get("entry_count", -1):
        from kb_vectorize import build
        build()
        return {"action": "full_build", "reason": "row_count_mismatch"}

    # Build current state from JSON stores
    current = {}  # id -> (store, text, hash)
    for store_name, path in STORES.items():
        if not os.path.exists(path):
            continue
        data = _load_json(path)
        if not data:
            continue
        for entry_id, entry in iter_store(data, store_name):
            text = concatenate_entry(entry, store_name)
            if not text.strip():
                continue
            current[entry_id] = (store_name, text, content_hash(text))

    # Build previous state from metadata
    previous = {}  # id -> (store, row, hash)
    for e in meta.get("entries", []):
        previous[e["id"]] = (e["store"], e["row"], e["hash"])

    # Classify changes
    added = {eid for eid in current if eid not in previous}
    removed = {eid for eid in previous if eid not in current}
    updated = {eid for eid in current if eid in previous and current[eid][2] != previous[eid][2]}
    unchanged = {eid for eid in current if eid in previous and current[eid][2] == previous[eid][2]}

    if not added and not updated and not removed:
        elapsed = time.time() - start
        # Still flush access hits even when vectors unchanged
        access_result = {"flushed": 0}
        try:
            import importlib.util
            at_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "access_tracking.py")
            spec = importlib.util.spec_from_file_location("access_tracking", at_path)
            at_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(at_mod)
            access_result = at_mod.flush_hits()
            if access_result["flushed"] > 0:
                print(f"Access tracking: flushed {access_result['flushed']} hits to stores")
        except Exception as e:
            print(f"Access tracking flush failed (non-blocking): {e}", file=sys.stderr)
        print(f"Synced: 0 added, 0 updated, 0 removed, {len(unchanged)} unchanged, {elapsed:.1f}s")
        return {"added": 0, "updated": 0, "removed": 0, "unchanged": len(unchanged), "access_flushed": access_result["flushed"], "elapsed": elapsed}

    # Re-embed changed/new entries
    to_embed = list(added | updated)
    new_vectors = {}
    if to_embed:
        from fastembed import TextEmbedding
        model = _apply_max_tokens(TextEmbedding(model_name=MODEL_NAME))
        texts = [current[eid][1] for eid in to_embed]
        embedded = list(model.embed(texts))
        for eid, vec in zip(to_embed, embedded):
            new_vectors[eid] = np.array(vec, dtype=np.float32)

    # Rebuild array: unchanged keep old vectors, updated/added get new ones
    new_entries = []
    new_vecs = []
    row = 0

    # Unchanged entries: preserve original vectors
    for eid in unchanged:
        store, old_row, old_hash = previous[eid]
        new_vecs.append(vectors[old_row])
        new_entries.append({"id": eid, "store": store, "row": row, "hash": old_hash})
        row += 1

    # Updated entries: new vectors
    for eid in updated:
        store = current[eid][0]
        new_vecs.append(new_vectors[eid])
        new_entries.append({"id": eid, "store": store, "row": row, "hash": current[eid][2]})
        row += 1

    # Added entries: new vectors
    for eid in added:
        store = current[eid][0]
        new_vecs.append(new_vectors[eid])
        new_entries.append({"id": eid, "store": store, "row": row, "hash": current[eid][2]})
        row += 1

    # Atomic write
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).astimezone().isoformat()

    new_vec_array = np.stack(new_vecs)
    tmp_vec = os.path.join(VS_DIR, "vectors.tmp.npy")
    tmp_meta = os.path.join(VS_DIR, "metadata.tmp.json")

    np.save(tmp_vec, new_vec_array)

    meta["entry_count"] = len(new_entries)
    meta["entries"] = new_entries
    meta["last_sync"] = now
    with open(tmp_meta, "w") as f:
        json.dump(meta, f, indent=2)

    os.replace(tmp_vec, vec_path)
    os.replace(tmp_meta, meta_path)

    elapsed = time.time() - start
    print(f"Synced: {len(added)} added, {len(updated)} updated, {len(removed)} removed, {len(unchanged)} unchanged, {elapsed:.1f}s")

    # Flush accumulated access tracking hits to source stores
    access_result = {"flushed": 0}
    try:
        import importlib.util
        at_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "access_tracking.py")
        spec = importlib.util.spec_from_file_location("access_tracking", at_path)
        at_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(at_mod)
        access_result = at_mod.flush_hits()
        if access_result["flushed"] > 0:
            print(f"Access tracking: flushed {access_result['flushed']} hits to stores")
    except Exception as e:
        print(f"Access tracking flush failed (non-blocking): {e}", file=sys.stderr)

    return {"added": len(added), "updated": len(updated), "removed": len(removed), "unchanged": len(unchanged), "access_flushed": access_result["flushed"], "elapsed": elapsed}


if __name__ == "__main__":
    sync()
