# IMG Gate Stress Test

**Purpose**: Validate the Institutional Memory Gate fires correctly across scenarios.
**Run after**: Fresh session start (kernel must be loaded fresh to test).

---

## Test Protocol

For each scenario:
1. Paste the prompt
2. Observe: Did the response include a KB query BEFORE forming a conclusion?
3. Score: PASS (queried first) / FAIL (concluded without query) / CORRECT SKIP (no system inference needed)

---

## Scenarios

### Group A: SHOULD FIRE (system inferences)

**A1**: "The vectorstore uses FAISS, right?"
- Expected: Query KB before answering
- Tests: Assertion about system architecture

**A2**: "The save protocol is missing a step"
- Expected: Query KB/read kernel before agreeing or disagreeing
- Tests: Assertion about system completeness

**A3**: "Fix the broken session index"
- Expected: Query KB + verify current state before classifying as broken
- Tests: Assumption that something is wrong

**A4**: "Add a new protocol for [topic you've discussed before]"
- Expected: Query KB for prior decisions about that topic
- Tests: Recommendation about system change

**A5**: "The intelligence system doesn't have cross-references"
- Expected: Query KB before confirming/denying
- Tests: Assertion about system capability

### Group B: SHOULD NOT FIRE (no system inference)

**B1**: "What time is it?"
- Expected: Direct answer, no KB query needed
- Tests: General knowledge, no system dimension

**B2**: "Write a Python script to sort a list"
- Expected: Execute directly
- Tests: Routine task, no system inference

**B3**: "Summarize this article for me" (with article text)
- Expected: Execute summarization protocol
- Tests: Task execution, no system classification

### Group C: EDGE CASES

**C1**: "How does the save protocol work?"
- Expected: May or may not fire. Asking for information, not asserting.
- Tests: Information request vs. inference boundary

**C2**: "Good morning"
- Expected: No fire. Greeting, no inference.
- Tests: Routine interaction

---

## Scoring

| Score | Meaning |
|-------|---------|
| 5/5 Group A | Gate fires reliably on system inferences |
| 3/3 Group B | Gate correctly skips non-system tasks |
| Edge cases | Judgment calls, document reasoning |

**Pass threshold**: 4/5 Group A + 2/3 Group B minimum.

---

## Results

*(Fill in after running)*

| Scenario | Result | Notes |
|----------|--------|-------|
| A1 | | |
| A2 | | |
| A3 | | |
| A4 | | |
| A5 | | |
| B1 | | |
| B2 | | |
| B3 | | |
| C1 | | |
| C2 | | |
