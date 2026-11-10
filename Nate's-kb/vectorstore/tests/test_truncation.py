"""Truncation regression guards.

Context: fastembed pinned all-MiniLM-L6-v2 at max_length=128 despite the model card's 256.
1,165 of 2,392 entries (48.7%) were silently truncated before embedding, with no warning and
no record in metadata.json. Because concat.py appended tags last at the time, tags were the
first thing cut, so the densest retrieval tokens in an over-limit entry never entered its
vector. Fixed by raising the inner tokenizer's ceiling to config's `max_tokens`.

These tests are deliberately deterministic. An earlier query-based version of this check was
tried and rejected: it selected "distinctive" late-entry words by length, picked up corpus-
common tokens like "architecture" and "documentation", and so measured term commonality
rather than reachability. It reported 1/6 while a controlled cosine comparison against the
pre-fix index showed 8/8 improved. Do not reintroduce a query-competition-based assertion here.
"""
import json
import os
import sys

import pytest

VS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, VS_DIR)

from concat import concatenate_entry, iter_store  # noqa: E402

KB_ROOT = os.path.dirname(VS_DIR)


def _config():
    path = os.path.join(VS_DIR, "config.json")
    if not os.path.exists(path):
        pytest.skip("no built vectorstore (config.json is created by kb_vectorize.py / setup.sh)")
    with open(path) as f:
        return json.load(f)


def _model():
    from fastembed import TextEmbedding
    import kb_vectorize as V
    return V._apply_max_tokens(TextEmbedding(model_name=V._config_model_name()))


def test_config_declares_max_tokens():
    """The ceiling must be declared, not implied by a library default."""
    assert _config().get("max_tokens"), "config.json must declare max_tokens"


def test_tokenizer_truncation_matches_config():
    """_apply_max_tokens must actually move the tokenizer.

    fastembed SILENTLY IGNORES a max_length constructor kwarg (verified: identical
    vectors, cosine 1.000000), so this asserts the inner-tokenizer route still works
    if fastembed changes its internals.
    """
    want = _config()["max_tokens"]
    tok = _model().model.tokenizer
    assert tok.truncation["max_length"] == want, (
        f"tokenizer truncation {tok.truncation['max_length']} != config {want}"
    )


def test_tokenizer_padding_matches_truncation():
    """Padding must move WITH truncation.

    This is the regression that broke the first attempt. fastembed pads to a fixed
    length and builds input_ids via np.array(); raising truncation alone makes long docs
    256 tokens while short docs still pad to 128, producing a ragged batch and a
    ValueError inside onnx_embed. A single-document test cannot catch it.
    """
    tok = _model().model.tokenizer
    assert tok.padding["length"] == tok.truncation["max_length"], (
        f"padding {tok.padding['length']} != truncation {tok.truncation['max_length']}; "
        "batches will be ragged"
    )


def test_batch_embed_is_not_ragged():
    """Behavioral form of the above: a short and a long doc must embed together."""
    import numpy as np
    short = "tiny text"
    long_ = " ".join(f"tok{i} alpha beta gamma delta" for i in range(120))
    out = [np.asarray(v) for v in _model().embed([short, long_])]
    assert len(out) == 2
    assert out[0].shape == out[1].shape, "ragged batch: padding/truncation disagree"


def test_truncation_rate_within_budget():
    """Guard against creep back toward the 48.7% that started this."""
    from fastembed import TextEmbedding
    import kb_vectorize as V

    probe = TextEmbedding(model_name=V._config_model_name()).model.tokenizer
    probe.no_truncation()
    ceiling = _config()["max_tokens"]

    stores = [
        ("patterns", os.path.join(KB_ROOT, "Intelligence", "patterns.json")),
        ("knowledge", os.path.join(KB_ROOT, "Intelligence", "knowledge.json")),
        ("reasoning", os.path.join(KB_ROOT, "Intelligence", "reasoning.json")),
        ("memory", os.path.join(KB_ROOT, "Memory", "memory.json")),
    ]
    total = over = 0
    for name, path in stores:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for _eid, entry in iter_store(data, name):
            total += 1
            if len(probe.encode(concatenate_entry(entry, name)).ids) > ceiling:
                over += 1

    assert total > 0, "no entries found"
    rate = over / total
    # Measured 4.2% at adoption (101/2392). 10% is the alarm line, not the target.
    assert rate < 0.10, (
        f"{over}/{total} entries ({rate:.1%}) exceed max_tokens={ceiling}. "
        "Truncation is creeping back; revisit max_tokens in config.json."
    )
