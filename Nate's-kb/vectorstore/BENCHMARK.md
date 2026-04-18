# Vectorstore Model Benchmark Protocol

## Purpose

Determine the best embedding model for the KB vectorstore on the current machine. "Best" means: highest semantic accuracy, clean noise rejection, acceptable build time.

## Quick Start

```bash
cd Nate's-kb/vectorstore
python3 kb_benchmark.py
```

This tests all candidate models against 12 queries (10 real, 2 adversarial) across the full KB corpus. Each model runs in a separate subprocess to prevent OOM.

## What It Tests

| Category | Queries | What "pass" means |
|----------|---------|-------------------|
| Vocabulary gap | 3 | Finds conceptually related entries despite no keyword overlap |
| Cross-store | 2 | Retrieves relevant entries from any store |
| Conceptual | 2 | Bridges abstract phrasing to concrete entries |
| Technical | 3 | Exact-match retrieval on specific topics |
| Adversarial | 2 | Scores below 0.35 (noise ceiling) on gibberish |

## Scoring

Models are ranked by:
1. Noise rejection (pass/fail, must score gibberish below 0.35)
2. Total hits (out of 12)
3. Build time (tiebreaker)

A model that scores 10/12 with clean noise beats a model that scores 12/12 but can't distinguish garbage from real queries.

## Options

```bash
# Test all candidates
python3 kb_benchmark.py

# Test specific models
python3 kb_benchmark.py --models bge-small-v1.5 arctic-embed-s

# Test only the currently configured model
python3 kb_benchmark.py --current-only
```

## Candidate Models

| Model | Dims | Size | Notes |
|-------|------|------|-------|
| all-MiniLM-L6-v2 | 384 | 90MB | Current default. Fast, good noise rejection. |
| bge-small-en-v1.5 | 384 | 67MB | Smaller, better semantics, weaker noise rejection. |
| snowflake-arctic-embed-s | 384 | 130MB | Newer, strong conceptual similarity. |
| bge-base-en-v1.5 | 768 | 210MB | Larger dims, needs more RAM. |
| snowflake-arctic-embed-m | 768 | 430MB | Mid-tier, needs 4GB+ free RAM. |
| mxbai-embed-large-v1 | 1024 | 640MB | Top-tier quality, needs 8GB+ free RAM. |

## Memory Requirements

Each model loads into RAM during its benchmark run. If a model OOM-kills, it's skipped and reported as FAILED. This is expected on memory-constrained machines.

Approximate free RAM needed:
- 384-dim models: 2GB+
- 768-dim models: 4GB+
- 1024-dim models: 8GB+

WSL2 users: check `free -h`. If capped low, edit `%UserProfile%\.wslconfig`:
```ini
[wsl2]
memory=8GB
```
Then `wsl --shutdown` and reopen.

## Swapping Models

If the benchmark recommends a different model:

1. Edit `kb_vectorize.py`, change the `MODEL_NAME` constant
2. Run `python3 kb_vectorize.py` to rebuild
3. Run `python3 kb_sync.py` to verify
4. Run `python3 kb_benchmark.py --current-only` to confirm

The query, sync, and server layers are model-agnostic. Only the build step changes.

## Adding Test Queries

Edit the `TESTS` list in `kb_benchmark.py`. Format:
```python
("natural language query", "expected_substring")  # real query
("gibberish input", None)                          # noise query
```

The expected substring is matched against the top result's ID + content preview (case-insensitive).
