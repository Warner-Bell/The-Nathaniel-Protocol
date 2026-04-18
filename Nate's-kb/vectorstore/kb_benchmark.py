#!/usr/bin/env python3
"""KB Vectorstore Model Benchmark.

Runs the full test suite against candidate embedding models to find the
best option for the current machine. Tests semantic accuracy, noise
rejection, and build performance across the entire corpus.

Usage:
    python3 kb_benchmark.py                  # Run all candidate models
    python3 kb_benchmark.py --models bge-small-en-v1.5 snowflake-arctic-embed-s
    python3 kb_benchmark.py --current-only   # Benchmark current model only

Output: ranked scorecard with hits, noise floor, build time, and recommendation.
"""

import argparse, json, subprocess, sys, textwrap
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
KB_DIR = SCRIPT_DIR.parent

# Models to benchmark (name, short label)
CANDIDATES = [
    ("sentence-transformers/all-MiniLM-L6-v2", "MiniLM-L6-v2"),
    ("BAAI/bge-small-en-v1.5", "bge-small-v1.5"),
    ("snowflake/snowflake-arctic-embed-s", "arctic-embed-s"),
    ("BAAI/bge-base-en-v1.5", "bge-base-v1.5"),
    ("snowflake/snowflake-arctic-embed-m", "arctic-embed-m"),
    ("mixedbread-ai/mxbai-embed-large-v1", "mxbai-large-v1"),
]

# Test suite: (query, expected_substring_in_top_result_or_None_for_noise)
TESTS = [
    ("how to avoid repeating past mistakes", "fail"),
    ("making Nate smarter over time", "intellig"),
    ("what happens when context runs out", "context"),
    ("how does the save process work", "save"),
    ("debugging a broken deployment", "fail"),
    ("trust between human and AI", "honesty"),
    ("when to stop and think before acting", "destruct"),
    ("RRF fusion scoring", "rrf"),
    ("git filter for sanitizing commits", "git"),
    ("Lambda cold start performance", "lambda"),
    ("purple elephant dancing on mars", None),
    ("asdfghjkl qwerty", None),
]

# Noise threshold: scores above this on garbage queries = bad noise rejection
NOISE_CEILING = 0.35


def build_corpus():
    """Load and concatenate all KB entries."""
    sys.path.insert(0, str(SCRIPT_DIR))
    from concat import concatenate_entry

    stores = [
        ("patterns", KB_DIR / "Intelligence/patterns.json", "entries"),
        ("knowledge", KB_DIR / "Intelligence/knowledge.json", "entries"),
        ("reasoning", KB_DIR / "Intelligence/reasoning.json", "entries"),
        ("memory", KB_DIR / "Memory/memory.json", "entities"),
    ]
    texts, ids = [], []
    seen = set()
    for store_name, path, key in stores:
        with open(path) as f:
            data = json.load(f)
        for e in data.get(key, []):
            eid = e.get("id", "")
            if eid in seen:
                continue
            seen.add(eid)
            text = concatenate_entry(e, store_name)
            if text.strip():
                texts.append(text)
                ids.append(eid)
    return texts, ids


def benchmark_model(model_name, texts, ids):
    """Run benchmark in a subprocess to isolate memory."""
    code = textwrap.dedent(f"""\
    import json, sys
    import numpy as np
    import time

    texts = json.loads(sys.stdin.read())["texts"]
    ids = json.loads(open("/tmp/kb_bench_ids.json").read())

    from fastembed import TextEmbedding
    model = TextEmbedding("{model_name}")

    t0 = time.time()
    corpus = np.array(list(model.embed(texts)))
    build_time = time.time() - t0

    tests = json.loads('{json.dumps(TESTS)}')
    results = []
    for query, expected in tests:
        q = np.array(list(model.embed([query]))[0])
        sims = corpus @ q
        top_i = int(np.argmax(sims))
        score = float(sims[top_i])
        tid = ids[top_i]
        ttext = texts[top_i][:80].lower()
        results.append({{"query": query, "expected": expected, "top_id": tid,
                         "score": score, "text_preview": ttext}})

    print(json.dumps({{"build_time": build_time, "dims": int(corpus.shape[1]),
                       "results": results}}))
    """)

    with open("/tmp/kb_bench_ids.json", "w") as f:
        json.dump(ids, f)

    proc = subprocess.run(
        [sys.executable, "-c", code],
        input=json.dumps({"texts": texts}),
        capture_output=True, text=True, timeout=300,
    )
    if proc.returncode != 0:
        return None, proc.stderr.strip().split("\n")[-1] if proc.stderr else "Unknown error"
    return json.loads(proc.stdout), None


def score_results(data):
    """Score a model's results: hits, noise rejection, overall grade."""
    hits, noise_ok, noise_scores = 0, 0, []
    noise_total, real_total = 0, 0

    for r in data["results"]:
        combined = (r["top_id"] + " " + r["text_preview"]).lower()
        if r["expected"] is None:
            noise_total += 1
            noise_scores.append(r["score"])
            if r["score"] < NOISE_CEILING:
                noise_ok += 1
                hits += 1
        else:
            real_total += 1
            if r["expected"].lower() in combined:
                hits += 1

    noise_pass = noise_ok == noise_total
    avg_noise = sum(noise_scores) / len(noise_scores) if noise_scores else 0
    return {
        "hits": hits,
        "total": len(data["results"]),
        "real_hits": hits - noise_ok,
        "real_total": real_total,
        "noise_pass": noise_pass,
        "noise_ok": noise_ok,
        "noise_total": noise_total,
        "avg_noise": avg_noise,
        "build_time": data["build_time"],
        "dims": data["dims"],
    }


def main():
    parser = argparse.ArgumentParser(description="KB Vectorstore Model Benchmark")
    parser.add_argument("--models", nargs="*", help="Short names of models to test")
    parser.add_argument("--current-only", action="store_true", help="Only test current model")
    args = parser.parse_args()

    # Determine which models to run
    if args.current_only:
        config_path = SCRIPT_DIR / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                cfg = json.load(f)
            current = cfg.get("model", CANDIDATES[0][0])
            models = [(current, current.split("/")[-1])]
        else:
            models = [CANDIDATES[0]]
    elif args.models:
        models = [(n, l) for n, l in CANDIDATES if l in args.models or n.split("/")[-1] in args.models]
        if not models:
            print(f"No matching models. Available: {[l for _, l in CANDIDATES]}")
            sys.exit(1)
    else:
        models = CANDIDATES

    print(f"Building corpus from KB stores...")
    texts, ids = build_corpus()
    print(f"Corpus: {len(texts)} entries\n")

    scoreboard = []

    for model_name, label in models:
        print(f"Testing {label} ({model_name})...")
        data, err = benchmark_model(model_name, texts, ids)
        if data is None:
            print(f"  FAILED: {err}\n")
            continue
        s = score_results(data)
        scoreboard.append((label, model_name, s, data))

        print(f"  Hits: {s['real_hits']}/{s['real_total']} real, {s['noise_ok']}/{s['noise_total']} noise")
        print(f"  Noise floor: {s['avg_noise']:.3f} ({'PASS' if s['noise_pass'] else 'FAIL'} < {NOISE_CEILING})")
        print(f"  Build: {s['build_time']:.1f}s, {s['dims']} dims\n")

    if not scoreboard:
        print("No models completed successfully.")
        sys.exit(1)

    # Rank: noise_pass first, then hits, then build time
    scoreboard.sort(key=lambda x: (-int(x[2]["noise_pass"]), -x[2]["hits"], x[2]["build_time"]))

    print("=" * 70)
    print("RESULTS (ranked)")
    print("=" * 70)
    print(f"{'Rank':<5} {'Model':<20} {'Hits':<8} {'Noise':<8} {'Build':<8} {'Dims':<6}")
    print("-" * 70)
    for i, (label, _, s, _) in enumerate(scoreboard):
        nf = "PASS" if s["noise_pass"] else "FAIL"
        print(f"{i+1:<5} {label:<20} {s['hits']}/{s['total']:<5} {nf:<8} {s['build_time']:.1f}s{'':<4} {s['dims']:<6}")

    winner = scoreboard[0]
    print(f"\nRECOMMENDED: {winner[0]} ({winner[1]})")
    print(f"  {winner[2]['hits']}/{winner[2]['total']} hits, noise {'clean' if winner[2]['noise_pass'] else 'DIRTY'}, {winner[2]['build_time']:.1f}s build")

    # Detail view
    print(f"\n{'='*70}")
    print("DETAIL: Per-query results")
    print(f"{'='*70}")
    for label, _, s, data in scoreboard:
        print(f"\n--- {label} ---")
        for r in data["results"]:
            combined = (r["top_id"] + " " + r["text_preview"]).lower()
            if r["expected"] is None:
                ok = "✅" if r["score"] < NOISE_CEILING else "❌"
            else:
                ok = "✅" if r["expected"].lower() in combined else "⚠️"
            print(f"  {ok} {r['score']:.3f} {r['top_id'][:15]:<15} | {r['query'][:45]}")


if __name__ == "__main__":
    main()
