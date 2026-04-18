# Ecosystem Benchmark Report

**Date**: 2026-03-21
**Sessions**: 40 (initial), 41 (adversarial interrogation + expansion)
**Memory Version**: 5.8
**Benchmark Runtime**: 2.23 seconds

---

## Session Start Gate

Time to load all 5 indexes from disk: 0.025s

| Index | Bytes | Est. Tokens |
|-------|------:|------------:|
| memory-index.json | 10,535 | 2,633 |
| patterns-index.json | 7,266 | 1,816 |
| knowledge-index.json | 43,327 | 10,831 |
| reasoning-index.json | 17,010 | 4,252 |
| session-index.json | 41,953 | 10,488 |
| **Total** | **120,091** | **30,022** |

Heaviest index: knowledge-index.json (36.1% of total). This scales with tag count (383 unique tags).

---

## Intelligence Stores

### Patterns (169 entries)

| Metric | Value |
|--------|------:|
| File size | 100,294 bytes (97.9 KB) |
| Index size | 7,266 bytes (7.1 KB) |
| Confidence avg | 0.904 |
| Confidence min/max | 0.55 / 1.00 |
| High confidence (>=0.8) | 165 (97.6%) |
| Medium confidence (0.5-0.8) | 4 (2.4%) |
| Low confidence (<0.5) | 0 |
| Entries with evidence_count > 0 | 10 of 169 (5.9%) |

**Categories:**

| Category | Count | % |
|----------|------:|--:|
| failure | 70 | 41.4% |
| preference | 52 | 30.8% |
| approach | 43 | 25.4% |
| ai_agent | 2 | 1.2% |
| process | 2 | 1.2% |

Note: 94.1% of patterns lack evidence_count tracking. This field was introduced after most patterns were created. Not a data quality issue, but a coverage gap for calibration metrics.

### Knowledge (119 entries)

| Metric | Value |
|--------|------:|
| File size | 98,234 bytes (95.9 KB) |
| Index size | 43,327 bytes (42.3 KB) |
| Confidence avg | 0.934 |
| High confidence (>=0.8) | 119 (100.0%) |
| Medium/Low confidence | 0 |
| Unique tags | 383 |

**Top 10 Tags:**

| Tag | Entries |
|-----|-------:|
| kiro | 12 |
| agentcore | 9 |
| vectorstore | 7 |
| architecture | 6 |
| strands-sdk | 6 |
| template | 6 |
| intelligence-system | 6 |
| sdk | 5 |
| python | 5 |
| maintenance | 5 |

Note: 100% high confidence across all 119 knowledge entries. Knowledge captures tend to be factual (verified at capture time), which explains the uniformly high confidence. This is expected behavior, not inflation.

### Reasoning (52 entries)

| Metric | Value |
|--------|------:|
| File size | 56,482 bytes (55.2 KB) |
| Index size | 17,010 bytes (16.6 KB) |
| Confidence avg | 0.874 |

**By Provenance:**

| Provenance | Count | % |
|------------|------:|--:|
| stated | 45 | 86.5% |
| synthesized | 6 | 11.5% |
| recorded | 1 | 1.9% |
| cross_session | 0 | 0.0% |

**By Type:**

| Type | Count | % |
|------|------:|--:|
| deduction | 22 | 42.3% |
| induction | 17 | 32.7% |
| meta-process | 6 | 11.5% |
| causal | 3 | 5.8% |
| insight | 2 | 3.8% |
| connection | 1 | 1.9% |
| unknown | 1 | 1.9% |

Note: Synthesis rate is 11.5%. Cross-session synthesis has never fired despite being eligible (6 sessions since last run, threshold is 3+). The 3c-CROSS step was not executed during saves 004, 005, or 006. The "unknown" type entry should be reclassified.

### Cross-References

| Metric | Value |
|--------|------:|
| File size | 1,171 bytes |
| Entries with links | 11 |
| Structure | Entry ID -> referenced_by/reasoning/patterns mappings |

Note: Cross-references use entry-keyed structure. Only recent entries have cross-reference links. Older entries predate the cross-reference system.

### Synonym Map

| Metric | Value |
|--------|------:|
| File size | 2,976 bytes |
| Entries | 30 |

Supplements vectorstore semantic search for tag normalization during CSR queries.

---

## CSR Efficiency

| Metric | Bytes | Est. Tokens |
|--------|------:|------------:|
| Index-only load (5 indexes) | 120,091 | 30,022 |
| Full store load (4 stores) | 287,740 | 71,935 |
| **Session Start Gate savings** | **167,649** | **41,913 (58.3%)** |

This measures the session start gate cost reduction only. During the session, CSR fetches individual entries by ID (typically 3-5 per task at ~75 tokens each), adding cost back proportional to task complexity.

---

## Vectorstore

| Metric | Value |
|--------|------:|
| Total chunks | 388 |
| Dimensions | 384 |
| Model | sentence-transformers/all-MiniLM-L6-v2 |
| Embedding library | fastembed 0.7.4 |
| Fusion method | RRF (k=60, equal weights) |
| Score floor | 0.005 |
| Vector file | 596,096 bytes (582 KB) |
| Metadata file | 63,604 bytes (62.1 KB) |
| Total size | 659,700 bytes (644 KB) |
| Sample dot-product query time | <0.001s |
| Sync time (no changes) | ~0.1s |
| Vector norms min/max/mean | 1.0000 / 1.0000 / 1.0000 |

Stores indexed: patterns, knowledge, reasoning, memory.

---

## Memory System

| Metric | Value |
|--------|------:|
| Memories | 48 |
| memory.json | 32,804 bytes (32.0 KB) |
| memory-index.json | 10,535 bytes (10.3 KB) |
| Active projects | 5 of 6 (1 complete) |
| Commitments | 0 open |
| Domain expertise areas | 9 |
| Anti-preferences | 0 |
| Proactive offers logged | 1 |
| Memory version | 5.8 |

### Sessions

| Metric | Value |
|--------|------:|
| Total sessions | 41 |
| Outcomes | 40 success, 1 partial |
| Success rate | 97.6% |
| Archived sessions | 0 |
| Session logs on disk | 41 |
| Avg log size | 4,127 bytes (~1,031 tokens) |
| Min/Max log size | 1,130 / 10,198 bytes |
| Total log storage | 169,223 bytes (165 KB) |
| Session index size | 41,953 bytes (41.0 KB) |

---

## Ecosystem Scale

| Component | Bytes | KB | Est. Tokens |
|-----------|------:|---:|------------:|
| Kernel (Nathaniel.md) | 115,253 | 112 | 28,813 |
| Nate-Protocol.md | 100,662 | 98 | 25,165 |
| 14 domain protocols | 243,114 | 237 | 60,778 |
| All KB .md files (141 files) | 1,686,324 | 1,647 | 421,581 |
| Intelligence stores (3 JSON) | 255,010 | 249 | 63,752 |
| Intelligence indexes (3 JSON) | 67,603 | 66 | 16,900 |
| Memory system (all files) | 256,395 | 250 | 64,098 |
| Vectorstore | 659,700 | 644 | n/a (binary) |
| Session logs (41 files) | 169,223 | 165 | 42,305 |
| Pattern docs (6 files) | varies | - | - |
| **KB directory total** | **7,786,199** | **7,604** | - |
| **Full ecosystem (KB + kernel)** | **7,901,452** | **7,716** | - |

| Stat | Value |
|------|------:|
| Total files in KB | 223 |
| Total ecosystem size | 7.5 MB |
| Kernel lines | 2,344 |
| Nate-Protocol lines | 1,907 |

---

## Growth Rates (over 41 sessions)

| Metric | Per Session |
|--------|------------:|
| Patterns | 4.1 |
| Knowledge | 2.9 |
| Reasoning | 1.3 |
| **Total intelligence** | **8.3** |
| Memories | 1.2 |

Note: These are averages over the full 41-session history. Actual capture rates likely follow a curve, not a line: early sessions produce more novel patterns/knowledge, while mature sessions increasingly hit dedup. Linear extrapolation below is a rough guide, not a prediction.

At current average rates (will likely slow):
- Session 50: ~415 intelligence entries (~75 more)
- Session 100: ~831 intelligence entries (~491 more)
- Vectorstore chunks scale proportionally

---

## Save Protocol

First benchmarked save completed in session 39. See `save-protocol-benchmark.md` for per-step timing, I/O metrics, and capture counts.

---

## Observations

1. **CSR savings improved significantly**: Index compaction during session 39 index rebuilds reduced total index load from ~45K tokens to ~30K tokens. CSR savings at 58.3%. The indexes carry less redundant structure after rebuild.

2. **Knowledge index is the heaviest** (42.3 KB, 36.1% of total index load). This scales with tag count (383 unique tags). As knowledge grows, the index may need tag consolidation.

3. **Pattern evidence_count gap**: 94.1% of patterns lack evidence tracking. This was introduced after most patterns were created. Backfilling would improve calibration metrics but isn't blocking.

4. **Cross-references are sparse**: Only 11 entries have links. The system is recent and links are only created during save when reasoning entries cite sources. Coverage will grow naturally.

5. **Synthesis rate at 11.5%**: Cross-session synthesis has been eligible since session 38 (6 sessions since last run) but has not been executed. Expected to fire on next save.

6. **100% high-confidence knowledge**: All 119 entries are >= 0.8. This is expected (knowledge captures are factual, verified at capture time) but means confidence isn't differentiating within the knowledge store.

7. **Failure patterns dominate**: 41.4% of patterns are failure modes. This reflects the ecosystem's emphasis on negative context engineering. Healthy distribution for a system that prioritizes failure prevention.

8. **Duplicate knowledge entries found and removed**: 2 duplicate IDs (know-107, know-108) were discovered during session 39 via the Columbo Test (behavioral testing). Knowledge count corrected from 116 to 114. Now at 119 after 5 new entries (know-068 through know-074, minus 2 removed dupes).

---

*Benchmarks captured against live system at optimal conditions. Reference documentation for the Nathaniel Protocol ecosystem.*

*These numbers reflect a mature instance (41 sessions, 340 intelligence entries). A fresh template clone starts empty. These benchmarks show what a healthy, populated system looks like at scale, serving as a target reference, not a starting state.*
