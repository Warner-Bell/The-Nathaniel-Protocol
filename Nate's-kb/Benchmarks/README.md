# Benchmarks

Performance, scale, and behavioral metrics for the Nathaniel Protocol ecosystem.

## Contents

| File | What It Tracks |
|------|----------------|
| `benchmark-candidates.md` | Full catalog of measurable metrics, tiered by readiness. Includes Tier 4 adversarial interrogation findings. |
| `ecosystem-benchmark-2026-03-21.md` | Ecosystem scale snapshot: store sizes, CSR efficiency, vectorstore, memory system, growth rates |
| `behavioral-benchmark-2026-03-21.md` | 23 behavioral tests: routing accuracy, integrity, retrieval effectiveness, tag quality, adversarial resistance, schema integrity, duplicate detection |
| `security-benchmark-2026-03-22.md` | Defense-in-depth: proxy URL filtering (44 tests), behavioral trigger detection (16 tests), defense hierarchy validation |
| `save-protocol-benchmark.md` | Per-save timing, token estimates, capture counts |

## How Benchmarks Are Collected

Benchmarks are captured against the live system operating at optimal conditions. The reports document what a mature, healthy Nathaniel Protocol ecosystem looks like: its scale, its behavioral accuracy, and its operational characteristics. These serve as reference documentation, not a continuous monitoring system.

A fresh template clone starts with empty stores. These benchmarks show the target state of a populated, healthy instance after sustained use.

## Test Suite (23 tests)

| # | Test | Type | What It Proves |
|---|------|------|----------------|
| 1 | CSR Retrieval Accuracy | Component | Index lookup mechanics work |
| 2 | End-to-End Retrieval | E2E | Full CSR pipeline surfaces relevant entries for real queries |
| 3 | Adversarial CSR Routing | Adversarial | Off-domain signals return zero hits |
| 4 | Index-Store Consistency | Integrity | No orphans, ghosts, or duplicates |
| 5 | Tag Reachability | Coverage | Every entry findable via at least one tag |
| 6 | Cross-Reference Integrity | Integrity | All reasoning chain references valid |
| 7 | Protocol Trigger Accuracy | Routing | Every keyword maps to an existing protocol |
| 8 | Gate Coverage | Documentation | All 7 gates documented with triggers |
| 9 | Vectorstore Quality | Integrity | Vectors normalized, self-consistent, corruption-free |
| 10 | Memory Retrieval Simulation | E2E | Active projects can reach relevant memories |
| 11 | Session Index Integrity | Integrity | 1:1 index-to-file correspondence |
| 12 | Confidence Distribution | Quality | Scores distributed enough for prioritization |
| 13 | Kernel & Anti-Pattern Coverage | Documentation | All sections non-empty, all categories present |
| 14 | Reasoning Retrieval via Reuse Signals | E2E | Reasoning entries findable via native routing (not tags) |
| 15 | Synonym Map Effectiveness | Behavioral | Synonym expansion finds entries direct lookup misses |
| 16 | HRF Hybrid Retrieval | E2E | Semantic search bridges vocabulary gaps CSR can't |
| 17 | Tag Quality Audit | Quality | Tags match likely query terms, not just exist |
| 18 | Negative Protocol Routing | Adversarial | Non-matching keywords don't trigger protocols |
| 19 | Schema Integrity | Integrity | Every entry has required fields for its store type |
| 20 | ID Sequence Integrity | Integrity | IDs are sequential with documented gaps only |
| 21 | Index Meta Accuracy | Integrity | _meta.total matches actual entry counts |
| 22 | Proxy URL Filtering | Security | Blocked URLs rejected, legitimate URLs pass, zero false positives |
| 23 | Behavioral Trigger Detection | Security | Injection patterns caught in external content, low false positive rate |

## Baseline Snapshot (Development Instance, Session 41)

*These numbers reflect the development instance at a point in time. The template ships with a curated subset. Run `python3 Nate's-kb/Benchmarks/run-benchmark.py` to generate current metrics for your instance.*

| Metric | Value |
|--------|-------|
| Total ecosystem size | ~7.5 MB |
| Kernel | 2,344 lines, ~28,813 tokens |
| Intelligence entries | 340 (169 patterns, 119 knowledge, 52 reasoning) |
| Vectorstore | 388 chunks, 384 dimensions |
| Sessions | 41 (40 success, 1 partial) |
| Memories | 48 |
| Active projects | 5 of 6 |
| Protocols | 14 domain protocols |
| CSR savings (start gate) | 58.3% vs. full store load |
| Behavioral tests | 23 (13 original + 5 adversarial interrogation + 3 hardened + 2 security) |

## History

| Date | Event |
|------|-------|
| Session 39 | First benchmarked save (save-protocol-benchmark.md) |
| Session 40 | First behavioral benchmark (13 tests). Research-informed methodology (Ragas, Fowler, Hamel). |
| Session 41 | Adversarial interrogation of benchmark suite. 15 findings. 5 new tests added (14-18). Test 10 reinvestigated. Test 12 renamed. All stale numbers updated. 3-pass consistency validation: all identical. Hardened re-run: expanded to 21 tests (added T19 Schema Integrity, T20 ID Sequence, T21 Index Meta Accuracy). Doubled adversarial signals. 3-pass hardened validation: all identical. 17 PASS, 2 PARTIAL, 0 FAIL, 2 INFO. |
