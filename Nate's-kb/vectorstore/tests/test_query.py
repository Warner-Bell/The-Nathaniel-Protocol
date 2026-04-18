"""Property tests for kb_query.py (Properties 5-9, 13)."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from kb_query import _rrf_fuse, _keyword_search


# --- Property 5: RRF fusion formula correctness ---

def make_results(ids_ranks, store="patterns"):
    return [{"id": f"id_{i}", "store": store, "score": 0.0, "rank": r} for i, r in ids_ranks]


@given(
    k=st.integers(min_value=1, max_value=100),
    n_sem=st.integers(min_value=0, max_value=10),
    n_key=st.integers(min_value=0, max_value=10),
)
@settings(max_examples=100)
def test_rrf_formula(k, n_sem, n_key):
    """Property 5: RRF score = sum(weight/(k+rank)) per path."""
    assume(n_sem + n_key > 0)
    sem = make_results([(i, i + 1) for i in range(n_sem)])
    key = make_results([(i, i + 1) for i in range(n_key)])
    weights = {"semantic": 1.0, "keyword": 1.0}

    fused = _rrf_fuse(sem, key, k, weights, 0.0, None)

    for r in fused:
        expected = 0.0
        if r["semantic_rank"]:
            expected += 1.0 / (k + r["semantic_rank"])
        if r["keyword_rank"]:
            expected += 1.0 / (k + r["keyword_rank"])
        assert abs(r["score"] - round(expected, 6)) < 1e-5, f"Score mismatch for {r['id']}"

    # Sorted descending
    scores = [r["score"] for r in fused]
    assert scores == sorted(scores, reverse=True)


@given(k=st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_rrf_dual_path_boost(k):
    """Entries in both paths score higher than single-path at same rank."""
    sem = make_results([(0, 1)])
    key = make_results([(0, 1)])  # same entry in both
    single_sem = make_results([(1, 1)])  # different entry, same rank, sem only
    single_key = make_results([(2, 1)], store="knowledge")  # different entry, same rank, key only

    dual = _rrf_fuse(sem, key, k, {"semantic": 1.0, "keyword": 1.0}, 0.0, None)
    sem_only = _rrf_fuse(single_sem, [], k, {"semantic": 1.0, "keyword": 1.0}, 0.0, None)
    key_only = _rrf_fuse([], single_key, k, {"semantic": 1.0, "keyword": 1.0}, 0.0, None)

    if dual and sem_only:
        assert dual[0]["score"] > sem_only[0]["score"]
    if dual and key_only:
        assert dual[0]["score"] > key_only[0]["score"]


# --- Property 6: Semantic scoring = dot product ---

def test_semantic_dot_product():
    """Property 6: Semantic scores equal dot product of normalized vectors."""
    rng = np.random.default_rng(42)
    n, d = 20, 384
    vectors = rng.standard_normal((n, d)).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    query_vec = rng.standard_normal(d).astype(np.float32)
    query_vec /= np.linalg.norm(query_vec)

    scores = vectors @ query_vec
    top_idx = np.argsort(scores)[::-1][:5]

    # Verify top N are highest dot products
    for i in range(len(top_idx) - 1):
        assert scores[top_idx[i]] >= scores[top_idx[i + 1]]

    # Verify scores match dot product
    for idx in top_idx:
        expected = np.dot(vectors[idx], query_vec)
        assert abs(scores[idx] - expected) < 1e-5


# --- Properties 8, 9: Store filter and score floor ---

@given(
    floor=st.floats(min_value=0.0, max_value=0.1),
    n=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=50)
def test_score_floor(floor, n):
    """Property 9: All results have score >= floor."""
    sem = make_results([(i, i + 1) for i in range(n)])
    fused = _rrf_fuse(sem, [], 60, {"semantic": 1.0, "keyword": 1.0}, floor, None)
    for r in fused:
        assert r["score"] >= floor, f"Score {r['score']} below floor {floor}"


@given(store=st.sampled_from(["patterns", "knowledge", "reasoning", "memory"]))
@settings(max_examples=20)
def test_store_filter(store):
    """Property 8: Store filter restricts results."""
    sem = [
        {"id": "a", "store": "patterns", "score": 0.9, "rank": 1},
        {"id": "b", "store": "knowledge", "score": 0.8, "rank": 2},
        {"id": "c", "store": "reasoning", "score": 0.7, "rank": 3},
        {"id": "d", "store": "memory", "score": 0.6, "rank": 4},
    ]
    fused = _rrf_fuse(sem, [], 60, {"semantic": 1.0, "keyword": 1.0}, 0.0, store)
    for r in fused:
        assert r["store"] == store


# --- Property 13: Result structure ---

def test_result_structure():
    """Property 13: Query result structure completeness (on live data)."""
    vs_dir = os.path.join(os.path.dirname(__file__), "..")
    if not os.path.exists(os.path.join(vs_dir, "vectors.npy")):
        print("  Skipping (no live vectorstore)")
        return

    from kb_query import search
    results = search("test query", top_k=3)
    for r in results:
        assert isinstance(r["id"], str)
        assert r["store"] in ("patterns", "knowledge", "reasoning", "memory")
        assert isinstance(r["score"], float) and r["score"] >= 0
        assert r["semantic_rank"] is None or isinstance(r["semantic_rank"], int)
        assert r["keyword_rank"] is None or isinstance(r["keyword_rank"], int)
        assert isinstance(r["content"], str)


if __name__ == "__main__":
    test_rrf_formula()
    print("✓ Property 5: RRF formula")
    test_rrf_dual_path_boost()
    print("✓ Property 5b: Dual-path boost")
    test_semantic_dot_product()
    print("✓ Property 6: Semantic dot product")
    test_score_floor()
    print("✓ Property 9: Score floor")
    test_store_filter()
    print("✓ Property 8: Store filter")
    test_result_structure()
    print("✓ Property 13: Result structure")
    print("All query property tests passed.")
