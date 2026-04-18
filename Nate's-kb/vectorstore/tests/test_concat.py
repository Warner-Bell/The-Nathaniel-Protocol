"""Property tests for field concatenation (D-2 fallback chains)."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from concat import concatenate_entry, content_hash, _resolve, FALLBACK_PRIMARY, FALLBACK_CONTEXT

non_empty_text = st.text(min_size=1, max_size=200).filter(lambda s: s.strip())
stores = st.sampled_from(["patterns", "knowledge", "reasoning", "memory"])


def entry_strategy():
    """Generate random entries with varying field name combinations."""
    return st.fixed_dictionaries({}, optional={
        "content": non_empty_text,
        "pattern": non_empty_text,
        "summary": non_empty_text,
        "context": non_empty_text,
        "evidence": non_empty_text,
        "detail": non_empty_text,
        "reuse_signal": non_empty_text,
        "intent": non_empty_text,
        "tags": st.lists(st.text(min_size=1, max_size=30), max_size=10),
    })


@given(entry=entry_strategy(), store=stores)
@settings(max_examples=100)
def test_fallback_chain_resolves_any_variant(entry, store):
    """Property 1: Fallback chain resolves any field name variant."""
    has_primary = any(
        entry.get(f) and isinstance(entry.get(f), str) and entry.get(f).strip()
        for f in FALLBACK_PRIMARY
    )
    result = concatenate_entry(entry, store)

    if has_primary:
        assert len(result) > 0, "Non-empty primary field should produce non-empty output"
        assert "|" not in result or " | " in result, "Pipes should be space-delimited"
    else:
        # No primary field: result may be empty or just context/tags
        pass

    # Pipe-delimited structure
    if " | " in result:
        parts = result.split(" | ")
        assert all(p.strip() for p in parts), "No empty segments between pipes"


@given(entry=entry_strategy(), store=stores)
@settings(max_examples=100)
def test_content_hash_deterministic(entry, store):
    """Content hash is deterministic for same input."""
    text = concatenate_entry(entry, store)
    assert content_hash(text) == content_hash(text)
    assert len(content_hash(text)) == 64  # SHA-256 hex


@given(entry=entry_strategy())
@settings(max_examples=50)
def test_reasoning_extras_included(entry):
    """Reasoning store includes reuse_signal and intent when present."""
    result = concatenate_entry(entry, "reasoning")
    if entry.get("reuse_signal") and entry["reuse_signal"].strip():
        assert entry["reuse_signal"].strip() in result
    if entry.get("intent") and entry["intent"].strip():
        assert entry["intent"].strip() in result


@given(entry=entry_strategy())
@settings(max_examples=50)
def test_non_reasoning_excludes_extras(entry):
    """Non-reasoning stores don't add reuse_signal/intent as separate pipe segments."""
    for store in ["patterns", "knowledge", "memory"]:
        result_parts = concatenate_entry(entry, store).split(" | ")
        reasoning_result_parts = concatenate_entry(entry, "reasoning").split(" | ")
        # Non-reasoning should have fewer or equal segments than reasoning
        # (reasoning adds reuse_signal and intent as extra segments)
        assert len(result_parts) <= len(reasoning_result_parts)


if __name__ == "__main__":
    test_fallback_chain_resolves_any_variant()
    print("✓ Property 1: Fallback chain")
    test_content_hash_deterministic()
    print("✓ Hash determinism")
    test_reasoning_extras_included()
    print("✓ Reasoning extras")
    test_non_reasoning_excludes_extras()
    print("✓ Non-reasoning exclusion")
    print("All concat property tests passed.")
