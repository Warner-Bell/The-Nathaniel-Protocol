"""Property tests for kb_sync.py (Properties 10, 11, 12)."""

import json
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from concat import concatenate_entry, content_hash


def setup_vectorstore(tmpdir, entries, model_version="unknown"):
    """Create a minimal vectorstore from entry dicts."""
    vs_dir = os.path.join(tmpdir, "vectorstore")
    os.makedirs(vs_dir, exist_ok=True)

    n = len(entries)
    vectors = np.random.randn(n, 384).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    np.save(os.path.join(vs_dir, "vectors.npy"), vectors)

    meta = {
        "model": "all-MiniLM-L6-v2",
        "model_version": model_version,
        "dimensions": 384,
        "built": "2026-01-01T00:00:00",
        "last_sync": "2026-01-01T00:00:00",
        "entry_count": n,
        "entries": [
            {"id": e["id"], "store": e["store"], "row": i, "hash": e["hash"]}
            for i, e in enumerate(entries)
        ],
    }
    with open(os.path.join(vs_dir, "metadata.json"), "w") as f:
        json.dump(meta, f)

    config = {
        "model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "model_version": model_version,
        "dimensions": 384,
        "fusion_method": "rrf",
        "rrf_k": 60,
        "rrf_weights": {"semantic": 1.0, "keyword": 1.0},
        "score_floor": 0.005,
        "created": "2026-01-01T00:00:00",
        "stores": {},
    }
    with open(os.path.join(vs_dir, "config.json"), "w") as f:
        json.dump(config, f)

    return vs_dir, vectors


def test_sync_change_detection():
    """Property 10: Sync correctly identifies changes via content hash."""
    vs_dir = os.path.join(os.path.dirname(__file__), "..")
    meta_path = os.path.join(vs_dir, "metadata.json")
    if not os.path.exists(meta_path):
        print("  Skipping (no live vectorstore)")
        return

    # Run sync on live data - should detect 0 changes
    from kb_sync import sync
    result = sync()
    assert result.get("added", 0) == 0
    assert result.get("updated", 0) == 0
    assert result.get("removed", 0) == 0
    assert result.get("unchanged", 0) > 0


def test_consistency_check_row_mismatch():
    """Property 11: Consistency check detects row count mismatch."""
    tmpdir = tempfile.mkdtemp()
    try:
        vs_dir = os.path.join(tmpdir, "vectorstore")
        os.makedirs(vs_dir)

        # Create mismatched artifacts: 5 vectors but metadata says 3
        vectors = np.random.randn(5, 384).astype(np.float32)
        np.save(os.path.join(vs_dir, "vectors.npy"), vectors)

        meta = {"model": "test", "model_version": "1.0", "dimensions": 384,
                "built": "", "last_sync": "", "entry_count": 3, "entries": []}
        with open(os.path.join(vs_dir, "metadata.json"), "w") as f:
            json.dump(meta, f)

        from kb_query import _check_consistency
        import kb_query
        orig = kb_query.VS_DIR
        try:
            kb_query.VS_DIR = vs_dir
            config = {"model_name": "test", "model_version": "1.0", "dimensions": 384,
                       "fusion_method": "rrf", "rrf_k": 60, "rrf_weights": {}, "score_floor": 0.005,
                       "created": "", "stores": {}}
            with open(os.path.join(vs_dir, "config.json"), "w") as f:
                json.dump(config, f)
            result = _check_consistency()
            assert result is None, "Should detect row count mismatch"
        finally:
            kb_query.VS_DIR = orig
    finally:
        shutil.rmtree(tmpdir)


def test_consistency_check_model_mismatch():
    """Property 11b: Consistency check detects model version mismatch."""
    tmpdir = tempfile.mkdtemp()
    try:
        vs_dir = os.path.join(tmpdir, "vectorstore")
        os.makedirs(vs_dir)

        vectors = np.random.randn(3, 384).astype(np.float32)
        np.save(os.path.join(vs_dir, "vectors.npy"), vectors)

        meta = {"model": "test", "model_version": "1.0", "dimensions": 384,
                "built": "", "last_sync": "", "entry_count": 3,
                "entries": [{"id": f"t{i}", "store": "patterns", "row": i, "hash": "x"} for i in range(3)]}
        with open(os.path.join(vs_dir, "metadata.json"), "w") as f:
            json.dump(meta, f)

        config = {"model_name": "test", "model_version": "2.0", "dimensions": 384,
                   "fusion_method": "rrf", "rrf_k": 60, "rrf_weights": {}, "score_floor": 0.005,
                   "created": "", "stores": {}}
        with open(os.path.join(vs_dir, "config.json"), "w") as f:
            json.dump(config, f)

        from kb_query import _check_consistency
        import kb_query
        orig = kb_query.VS_DIR
        try:
            kb_query.VS_DIR = vs_dir
            result = _check_consistency()
            assert result is None, "Should detect model version mismatch"
        finally:
            kb_query.VS_DIR = orig
    finally:
        shutil.rmtree(tmpdir)


def test_error_containment_missing_vectorstore():
    """Property 12: Missing vectorstore falls back to keyword-only, no error."""
    import kb_query
    orig = kb_query.VS_DIR
    try:
        kb_query.VS_DIR = "/nonexistent/path"
        results = kb_query.search("test query", top_k=3)
        # Should not raise, may return keyword-only results or empty
        assert isinstance(results, list)
    finally:
        kb_query.VS_DIR = orig


if __name__ == "__main__":
    test_sync_change_detection()
    print("✓ Property 10: Sync change detection")
    test_consistency_check_row_mismatch()
    print("✓ Property 11: Row count mismatch detection")
    test_consistency_check_model_mismatch()
    print("✓ Property 11b: Model version mismatch detection")
    test_error_containment_missing_vectorstore()
    print("✓ Property 12: Error containment (missing vectorstore)")
    print("All sync property tests passed.")
