# Save Protocol Benchmark

Per-save timing, token estimates, and capture counts.

---

## Session 2026-03-21-004 (First Benchmarked Save)

**Total wall time**: 152.1s (2m 32s)

### Timing Breakdown

| Step | Duration | % of Total |
|------|----------|:----------:|
| Step 1: Session log creation | 46.4s | 30.5% |
| Step 2: Session index update | 7.8s | 5.1% |
| Steps 3a-c: Intelligence capture (plan + write) | 38.2s | 25.1% |
| Step 3d: Vectorstore sync | 8.7s | 5.7% |
| Steps 4-8: Memory update + git commit | 51.0s | 33.5% |

### I/O

| Metric | Value |
|--------|------:|
| Files read | 4 (~47,809 tokens) |
| Files written | 5 (~49,328 tokens) |
| Session log size | 6,073 bytes (~1,518 tokens) |
| Git files committed | 16 |

### Intelligence Captures

| Type | Count | Details |
|------|------:|---------|
| Patterns (new) | 0 | 2 added mid-session (approach_042, approach_043) |
| Knowledge (new) | 1 | know-069 (Ralph Wiggum name collision) |
| Reasoning (new) | 0 | 2 added mid-session (reason-034, reason-035) |
| Vectorstore sync | 5 added | 3.4s sync time |

### Observations

- Session log creation (30.5%) and memory+git (33.5%) dominate. Intelligence capture is 25.1%.
- The 152s total includes LLM thinking time between steps (reading session log for extraction, planning captures, writing entries). Pure file I/O is a fraction of this.
- Vectorstore sync added 5 new chunks (the 4 mid-session intelligence entries + 1 save-time knowledge entry).
- This was a heavy session (benchmarks, kernel changes, template propagation). Lighter sessions should be faster.

---

## Session 2026-03-21-005 (Second Benchmarked Save)

**Total wall time**: 148.3s (2m 28s)

### Timing Breakdown

| Step | Duration | % of Total |
|------|----------|:----------:|
| Step 1: Session log creation | 38.2s | 25.8% |
| Step 2: Session index update | 8.9s | 6.0% |
| Steps 3a-c: Intelligence capture (plan + write) | 48.0s | 32.4% |
| Step 3d: Vectorstore sync | 7.7s | 5.2% |
| Steps 4-8: Memory update + git commit | 45.4s | 30.6% |

### I/O

| Metric | Value |
|--------|------:|
| Files written | 7 |
| Git files committed | 7 |

### Intelligence Captures

| Type | Count | Details |
|------|------:|---------|
| Patterns (new) | 0 | |
| Knowledge (new) | 2 | know-070 (benchmark methodology), know-071 (CSR routing per store) |
| Reasoning (new) | 1 | reason-036 (index compaction, synthesized) |
| Vectorstore sync | 3 added | 2.3s sync time |

### Delta from Previous Save

| Metric | Save 004 | Save 005 | Delta |
|--------|----------|----------|-------|
| Total wall time | 152.1s | 148.3s | -3.8s |
| Session log | 46.4s (30.5%) | 38.2s (25.8%) | -8.2s |
| Intelligence capture | 38.2s (25.1%) | 48.0s (32.4%) | +9.8s |
| Memory+git | 51.0s (33.5%) | 45.4s (30.6%) | -5.6s |
| Intelligence entries | 1 | 3 | +2 |
| Git files | 16 | 7 | -9 |

Intelligence capture took longer despite fewer total entries because this save had 2 knowledge + 1 reasoning (more complex writes) vs. save 004's 1 knowledge entry.

---

*Append future save benchmarks below for trend tracking.*

---

## Session 2026-03-21-007 (Third Benchmarked Save)

**Total wall time**: ~90s (estimated)

### Timing Breakdown

| Step | Duration | % of Total |
|------|----------|:----------:|
| Step 1: Session log creation | ~20s | 22% |
| Step 2: Session index update | ~5s | 6% |
| Steps 3a-c: Intelligence capture (plan + write) | ~25s | 28% |
| Step 3d: Vectorstore sync | 4.2s | 5% |
| Steps 4-8: Memory update + git commit | ~35s | 39% |

### I/O

| Metric | Value |
|--------|------:|
| Files written | 8 |
| Git files committed | 11 |

### Intelligence Captures

| Type | Count | Details |
|------|------:|---------|
| Patterns (new) | 0 | |
| Knowledge (new) | 1 | know-075 (schema evolution in intelligence stores) |
| Reasoning (new) | 0 | |
| Vectorstore sync | 1 added | 4.2s sync time |

### Token Cost

| Metric | Value |
|--------|------:|
| Context at save start | 3,198.6K tokens (95% of 10,000K plan) |
| Context at save end | 3,220.6K tokens |
| **Save operation cost** | **22.0K tokens** |
| % of session total | 0.68% |

### Delta from Previous Saves

| Metric | Save 004 | Save 005 | Save 007 | Trend |
|--------|----------|----------|----------|-------|
| Total wall time | 152.1s | 148.3s | ~90s | Decreasing |
| Intelligence entries | 1 | 3 | 1 | Varies |
| Git files | 16 | 7 | 11 | Varies |
| Token cost | n/a | n/a | 22.0K | First measured |

This is the first save with token cost measurement. The 22.0K represents the floor for a detailed save: session log, index update, 1 intelligence entry, vectorstore sync, memory update, snapshot, prune check, git commit, and detailed output formatting.

---

*Append future save benchmarks below for trend tracking.*
