"""Property tests for kb_vectorize.py build output (Properties 2, 3, 4)."""

import json
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from hypothesis import given, settings, assume
from hypothesis import strategies as st


def make_store(entries, store_type="list", prefix="test"):
    """Create a minimal valid store dict."""
    if store_type == "list":
        return {"entries": [{"id": f"{prefix}_{i}", "content": e, "tags": ["test"]} for i, e in enumerate(entries)]}
    else:  # dict (memory)
        return {"memories": {f"{prefix}_{i}": {"content": e, "tags": ["test"], "context": "ctx"} for i, e in enumerate(entries)}}


non_empty = st.text(min_size=3, max_size=100, alphabet=st.characters(whitelist_categories=("L", "N", "Z")))


@given(
    pat_count=st.integers(min_value=0, max_value=5),
    know_count=st.integers(min_value=0, max_value=5),
    reas_count=st.integers(min_value=0, max_value=5),
    mem_count=st.integers(min_value=0, max_value=5),
)
@settings(max_examples=20, deadline=120000)
def test_build_completeness(pat_count, know_count, reas_count, mem_count):
    """Property 2: Build produces complete output for any valid store subset."""
    total = pat_count + know_count + reas_count + mem_count
    assume(total > 0)

    tmpdir = tempfile.mkdtemp()
    try:
        # Create store files
        intel_dir = os.path.join(tmpdir, "Intelligence")
        mem_dir = os.path.join(tmpdir, "Memory")
        vs_dir = os.path.join(tmpdir, "vectorstore")
        os.makedirs(intel_dir)
        os.makedirs(mem_dir)
        os.makedirs(vs_dir)

        stores = {
            "patterns": (os.path.join(intel_dir, "patterns.json"), make_store([f"pattern {i}" for i in range(pat_count)], prefix="pat")),
            "knowledge": (os.path.join(intel_dir, "knowledge.json"), make_store([f"knowledge {i}" for i in range(know_count)], prefix="know")),
            "reasoning": (os.path.join(intel_dir, "reasoning.json"), make_store([f"reasoning {i}" for i in range(reas_count)], prefix="reas")),
            "memory": (os.path.join(mem_dir, "memory.json"), make_store([f"memory {i}" for i in range(mem_count)], "dict", prefix="mem")),
        }
        for path, data in stores.values():
            with open(path, "w") as f:
                json.dump(data, f)

        # Patch paths and run build
        import kb_vectorize as kbv
        orig_kb = kbv.KB_ROOT
        orig_vs = kbv.VS_DIR
        orig_stores = kbv.STORES.copy()
        try:
            kbv.KB_ROOT = tmpdir
            kbv.VS_DIR = vs_dir
            kbv.STORES = {name: path for name, (path, _) in stores.items()}
            count, _ = kbv.build()
        finally:
            kbv.KB_ROOT = orig_kb
            kbv.VS_DIR = orig_vs
            kbv.STORES = orig_stores

        # Verify
        vectors = np.load(os.path.join(vs_dir, "vectors.npy"))
        with open(os.path.join(vs_dir, "metadata.json")) as f:
            meta = json.load(f)
        with open(os.path.join(vs_dir, "config.json")) as f:
            conf = json.load(f)

        assert vectors.shape[0] == total, f"Expected {total} rows, got {vectors.shape[0]}"
        assert meta["entry_count"] == total
        assert len(meta["entries"]) == total

        # Every input ID appears exactly once
        ids = [e["id"] for e in meta["entries"]]
        assert len(ids) == len(set(ids)), "Duplicate IDs in metadata"

        # Config has all required fields
        for field in ["model_name", "model_version", "dimensions", "fusion_method", "rrf_k", "rrf_weights", "score_floor", "created", "stores"]:
            assert field in conf, f"Missing config field: {field}"

    finally:
        shutil.rmtree(tmpdir)


def test_vector_normalization():
    """Property 3: Build output vectors are unit-normalized float32 with correct dimensions."""
    vs_dir = os.path.join(os.path.dirname(__file__), "..")
    vectors_path = os.path.join(vs_dir, "vectors.npy")
    meta_path = os.path.join(vs_dir, "metadata.json")

    if not os.path.exists(vectors_path):
        print("  Skipping (no vectors.npy from live build)")
        return

    vectors = np.load(vectors_path)
    with open(meta_path) as f:
        meta = json.load(f)

    assert vectors.dtype == np.float32, f"Expected float32, got {vectors.dtype}"
    assert vectors.shape == (meta["entry_count"], 384), f"Shape mismatch: {vectors.shape}"

    norms = np.linalg.norm(vectors, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3), f"Not unit-normalized: min={norms.min()}, max={norms.max()}"


def test_metadata_config_structure():
    """Property 4: Build metadata and config contain all required fields."""
    vs_dir = os.path.join(os.path.dirname(__file__), "..")
    meta_path = os.path.join(vs_dir, "metadata.json")
    conf_path = os.path.join(vs_dir, "config.json")

    if not os.path.exists(meta_path):
        print("  Skipping (no metadata.json from live build)")
        return

    with open(meta_path) as f:
        meta = json.load(f)
    with open(conf_path) as f:
        conf = json.load(f)

    # Metadata required fields
    for field in ["model", "model_version", "dimensions", "built", "entry_count", "entries"]:
        assert field in meta, f"Missing metadata field: {field}"

    # Each entry has required fields
    for entry in meta["entries"]:
        for field in ["id", "store", "row", "hash"]:
            assert field in entry, f"Missing entry field: {field}"

    # Config required fields
    for field in ["model_name", "model_version", "dimensions", "fusion_method", "rrf_k", "rrf_weights", "score_floor", "created", "stores"]:
        assert field in conf, f"Missing config field: {field}"

    # Cross-check
    vectors = np.load(os.path.join(os.path.dirname(__file__), "..", "vectors.npy"))
    assert meta["entry_count"] == len(meta["entries"]) == vectors.shape[0]


if __name__ == "__main__":
    test_build_completeness()
    print("✓ Property 2: Build completeness")
    test_vector_normalization()
    print("✓ Property 3: Vector normalization")
    test_metadata_config_structure()
    print("✓ Property 4: Metadata/config structure")
    print("All build property tests passed.")
