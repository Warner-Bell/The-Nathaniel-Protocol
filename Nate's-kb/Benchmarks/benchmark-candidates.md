# Benchmark Candidates

Measurable metrics across the Nathaniel Protocol ecosystem, tiered by collection readiness.

---

## Tier 1: Measurable Now

These can be collected during normal operation with no changes.

### Save Protocol

| Metric | How Measured | Baseline (Session 39) |
|--------|-------------|----------------------|
| Wall time (total) | Timestamp start/end of save | 148.3s |
| Wall time per step | Timestamp each of 9 steps | See save-protocol-benchmark.md |
| Files read during save | Count tool calls | 4 (~47,809 tokens) |
| Files written during save | Count tool calls | 5 (~49,328 tokens) |
| Bytes written | Sum file deltas | ~197 KB |
| Estimated tokens (read) | Bytes read / 4 | ~47,809 |
| Estimated tokens (written) | Bytes written / 4 | ~49,328 |
| Patterns captured | Count new + updated | 0 at save (2 mid-session) |
| Knowledge captured | Count new + updated | 1 |
| Reasoning captured | Count new + updated | 0 at save (2 mid-session) |
| Total intelligence captures | Sum of above | 5 (session total) |
| Vectorstore sync time | kb_sync.py output | 3.4s |
| Vectorstore sync delta | added/updated/removed | 5 added |
| Git files committed | git status output | 16 |
| Session log size | File size after creation | 6,073 bytes (~1,518 tokens) |

### Session Start Gate

| Metric | How Measured | Baseline |
|--------|-------------|----------|
| Indexes loaded | Count (should be 5) | 5 |
| Total index token cost | Sum of 5 index file sizes / 4 | ~30,022 tokens |
| memory-index.json | File size / 4 | ~2,633 tokens |
| patterns-index.json | File size / 4 | ~1,816 tokens |
| knowledge-index.json | File size / 4 | ~10,831 tokens |
| reasoning-index.json | File size / 4 | ~4,252 tokens |
| session-index.json | File size / 4 | ~10,488 tokens |

### Intelligence Stores

| Metric | How Measured | Baseline |
|--------|-------------|----------|
| Pattern count | patterns.json entries length | 169 |
| Pattern categories | byCategory in patterns-index.json | failure: 70, preference: 52, approach: 43, ai_agent: 2, process: 2 |
| Knowledge count | knowledge.json entries length | 119 |
| Knowledge unique tags | byTag keys in knowledge-index.json | 383 |
| Reasoning count | reasoning.json entries length | 52 |
| Reasoning type breakdown | byType in reasoning-index.json | deduction: 22, induction: 17, meta-process: 6, causal: 3, insight: 2, connection: 1, unknown: 1 |
| Total intelligence entries | Sum | 340 |
| Pattern confidence avg | Mean of all confidence values | 0.90 |
| Pattern confidence distribution | High/Med/Low buckets | 165 / 4 / 0 |
| Reasoning provenance breakdown | stated/synthesized/cross_session/recorded | 45 / 6 / 0 / 1 |
| Cross-reference links | pattern->reasoning + knowledge->reasoning | Measurable from cross-references.json |
| Synonym map entries | synonym-map.json length | 2 |
| Store file sizes | os.path.getsize | patterns: 97.9 KB, knowledge: 95.9 KB, reasoning: 55.2 KB |

### CSR Efficiency

| Metric | How Measured | Baseline |
|--------|-------------|----------|
| Index-only load cost | Sum of 5 index sizes | ~30,022 tokens |
| Full store load cost | Sum of 4 full store sizes | ~71,935 tokens |
| Session Start Gate savings | 1 - (index / full) | 58.3% |
| Entries per CSR fetch | Count entries loaded per task | Varies (target: 3-5) |

Note: CSR savings represent the Session Start Gate cost reduction (loading indexes instead of full stores). During the session, targeted fetches by ID add cost back. Total session savings depend on how many entries are fetched.

### Vectorstore

| Metric | How Measured | Baseline |
|--------|-------------|----------|
| Total chunks | vectors.npy shape[0] | 388 |
| Dimensions | vectors.npy shape[1] | 384 |
| Vector file size | os.path.getsize | 577 KB |
| Metadata file size | os.path.getsize | 61.6 KB |
| Sync time | kb_sync.py output | ~0.1s (no changes), ~3.4s (with additions) |
| Model | config.json | all-MiniLM-L6-v2 |

### Memory System

| Metric | How Measured | Baseline |
|--------|-------------|----------|
| Total memories | memory.json memories length | 48 |
| Active projects | Count status=active | 5 |
| Session count | session-index.json sessions length | 41 |
| Archived sessions | session-archive.json length | 0 |
| Session log avg size | Mean of session-*.md sizes | ~4,127 bytes (~1,031 tokens) |
| Session outcomes | success/partial/blocked counts | 40 / 1 / 0 |
| Proactive offers logged | offer_history length | 1 |

### Ecosystem Scale

| Metric | How Measured | Baseline |
|--------|-------------|----------|
| Total KB size | Walk Nate's-kb/ | 7.4 MB |
| Kernel size | Nathaniel.md file size | 113 KB (~28,813 tokens), 2,344 lines |
| Total ecosystem | KB + kernel | 7.5 MB |
| Protocol count | Count *.md protocol files | 14 |
| Protocol total size | Sum protocol file sizes | 237 KB (~60,778 tokens) |
| Pattern documentation files | Count patterns/*.md | N/A (patterns documented in case study) |
| Domain expertise entries | memory.json domain_expertise | 9 |
| Steering files | Count .steering-files/ | 8 files |

---

## Tier 2: Measurable with Minor Additions

These need small changes to how data is tracked but no new infrastructure.

### Protocol Activation

| Metric | What's Needed | Value |
|--------|---------------|-------|
| Protocol trigger frequency | Log which protocols load per session during save | Which protocols fire most |
| Protocol load cost per trigger | File size of each protocol | Already known, need frequency |
| Gate fire rate | Count gate activations per session | How often each of 5 gates fires |
| Gate false positive rate | Track gate fires that didn't prevent an actual issue | Requires judgment call |

### Intelligence Quality

| Metric | What's Needed | Value |
|--------|---------------|-------|
| Confidence drift over time | Track avg confidence per save | Is the system getting more or less confident? |
| Knowledge coverage by domain | Count entries per tag over time | Which domains are well-covered vs. sparse? |
| Reasoning synthesis rate | Track synthesized vs. stated per save | Is synthesis producing value? |
| Dedup hit rate | Count dedup catches during save | How often does new intelligence duplicate existing? |
| Access tracking (hot entries) | lastAccessed field analysis | Which entries get used most? |

### Proactive Behavior

| Metric | What's Needed | Value |
|--------|---------------|-------|
| Offer accept rate by type | More offer_history entries (need more sessions) | Which offer types land? |
| Offers per session | Track in save | Staying under max 3? |
| Offer maturity stage | Assess against 4-stage model | Where is the system in its proactive evolution? |

### Session Efficiency

| Metric | What's Needed | Value |
|--------|---------------|-------|
| Tokens per task type | Estimate by task complexity | Which tasks are token-expensive? |
| Context switches per session | Count topic changes | How fragmented are sessions? |
| Files touched per session | Count unique files read/written | Session scope indicator |

---

## Tier 3: Future / Aspirational

These would require new tooling or external measurement.

| Metric | What's Needed | Value |
|--------|---------------|-------|
| Actual token usage per save | API-level token counter | True cost, not estimate |
| Actual token usage per session | API-level token counter | True session cost |
| Response latency | Timestamp request/response pairs | How fast is Nate? |
| Pattern prediction accuracy | Track predictions vs. outcomes systematically | Is confidence calibration working? |
| User satisfaction score | Explicit feedback mechanism | Quality signal |
| Cross-session learning transfer | Track when session N's learning helps session N+X | Compounding value measurement |
| Multi-user pattern isolation | Multiple users on same system | Enterprise readiness |
| Cold start vs. warm start time | Compare first message to mid-session | Init overhead |

### Security (Defense-in-Depth)

| Metric | How to Measure | Target |
|--------|---------------|--------|
| Proxy URL filtering accuracy | Run test suite against BLOCKED patterns | 100% (0 FP, 0 FN) |
| Behavioral trigger catch rate | Test malicious content against triggers | >85% catch, <15% FP |
| Behavioral trigger false positive rate | Test legitimate content against triggers | <15% |
| Pattern count | Count regex patterns in BLOCKED list | Track growth |
| Trigger count | Count detection triggers in kernel | Track growth |

Note: Security benchmarks are in `security-benchmark-2026-03-22.md`. Proxy: 44/44 (100%, 0 FP). Triggers: 7/7 catch (100%), 0/9 FP (0%). Triggers are natural language (LLM-interpreted), not regex.

---

## Tier 4: Adversarial Interrogation Findings

Identified via adversarial interrogation of the benchmark suite itself (session 2026-03-21-006). Tests whether the benchmarks are testing the right things.

### Missing Coverage

| ID | Finding | Test Type | Priority |
|----|---------|-----------|----------|
| M1 | No dedicated reasoning retrieval behavioral test. Reasoning routes via reuse_signals/intents, not tags. Only tested as secondary store in Test 2. | Mechanical | High |
| M2 | No synonym map effectiveness test. 30 entries exist but no test verifies they improve retrieval. Inventory without behavior. | Mechanical | High |
| M3 | No HRF hybrid retrieval test. All retrieval tests are CSR-only. Don't know if HRF surfaces results CSR misses (the whole point of having it). | Mechanical | High |
| M4 | No save protocol correctness test. Timing/IO measured but not whether 4-layer capture system actually caught everything. | Observational | Medium |
| M5 | No proactive offering behavioral test. 11 trigger types, confidence thresholds, max-3 guardrail, but only metric is "1 offer logged." | Observational | Medium |
| M6 | No cross-session continuity test. Session index integrity checked (file existence) but not whether context actually carries forward. | Observational | Medium |

### Misconfigured Tests

| ID | Finding | Fix Type | Priority |
|----|---------|----------|----------|
| C1 | Test 10 (Memory Retrieval): Concluded "data sparsity, not routing failure" without verifying. Projects with multiple sessions and docs showing 0 memories needs investigation. | Retest with data | High |
| C2 | Test 12 (Confidence Calibration): Measures distribution shape, not calibration accuracy. 0.9 confidence should mean 90% correct. We measure compression, not correctness. | Redesign | Medium |
| C3 | Test 8 (Gate Coverage): Checks documentation, not behavior. Gates documented with triggers but no test that they actually fire during operation. | Add behavioral layer | High |

### False Confidence

| ID | Finding | Fix Type | Priority |
|----|---------|----------|----------|
| F1 | 100% tag reachability hides tag quality. Entry reachable via "runtime" but invisible for the likely query "eol" or "migration." Reachability ≠ findability. | Add quality test | Medium |
| F2 | 58.4% CSR savings is start-gate only. Session-long fetches add cost back. Reporting best-case without full picture. | Track full session | Low |
| F3 | 97.5% session success rate is self-assessed. No external validation. Missed items marked "success" are invisible. | Methodology note | Low |

### Methodology Gaps

| ID | Finding | Fix Type | Priority |
|----|---------|----------|----------|
| G1 | No regression tracking. Can't detect degradation between runs. A test that passes today and fails tomorrow is invisible. | Build comparison | Medium |
| G2 | No negative behavioral tests for protocols. Positive routing tested but not whether non-matching keywords correctly don't trigger. | Add negative tests | Medium |
| G3 | Growth rate projections assume linear growth. Intelligence capture rates likely change as system matures (diminishing returns, increasing dedup). | Methodology note | Low |

### Resolution Status

| ID | Status | Resolved In |
|----|--------|-------------|
| M1 | ✅ Added | behavioral-benchmark Test 14 |
| M2 | ✅ Added | behavioral-benchmark Test 15 |
| M3 | ✅ Added | behavioral-benchmark Test 16 |
| M4 | 📋 Tracked | Observational, test during live saves |
| M5 | 📋 Tracked | Observational, test during live sessions |
| M6 | 📋 Tracked | Observational, test during live sessions |
| C1 | ✅ Fixed | behavioral-benchmark Test 10 (reinvestigated) |
| C2 | ✅ Fixed | behavioral-benchmark Test 12 (renamed + methodology note) |
| C3 | 📋 Tracked | Observational, requires live gate firing observation |
| F1 | ✅ Added | behavioral-benchmark Test 17 |
| F2 | 📋 Tracked | Requires session-level token accounting |
| F3 | ✅ Fixed | behavioral-benchmark methodology section updated |
| G1 | 📋 Tracked | Future: automated regression comparison |
| G2 | ✅ Added | behavioral-benchmark Test 18 |
| G3 | ✅ Fixed | ecosystem-benchmark growth section updated |

---

## When to Re-Run

| Trigger | What |
|---------|------|
| Major milestone | Full ecosystem snapshot (all Tier 1 metrics) |
| Post-fix verification | Behavioral tests for the affected area |
| Periodic health check | Behavioral benchmark suite |
| Post-interrogation | Re-run after adding new tests from adversarial findings |

---

*First benchmarked save completed in session 39. See save-protocol-benchmark.md for results.*
*First adversarial interrogation completed session 2026-03-21-006. 15 findings, 8 resolved mechanically, 7 tracked for observational testing.*
*Full re-run with 3-pass consistency validation completed session 41. All stale numbers updated. All 3 passes identical.*
*Hardened re-run: expanded to 21 tests (T19 Schema Integrity, T20 ID Sequence, T21 Index Meta Accuracy). All existing tests expanded with additional signals and secondary assertions. 3-pass hardened validation: all identical. 17 PASS, 2 PARTIAL, 0 FAIL, 2 INFO.*
