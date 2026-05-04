# Behavioral Control Pipeline

**Purpose**: Standard workflow for governing LLM behaviors that resist instruction-only fixes.

**When to use**: A behavior has failed 2+ times despite being addressed in instructions. The failure is structural (training pressure, context decay, frequency mismatch) not informational (agent didn't know the rule).

---

## The 11-Step Pipeline

### 1. Identify Failure Class

What category of failure is this?
- **Frequency mismatch**: Rule exists but fires too rarely to prevent the behavior (e.g., gate in Pre-Task but behavior happens mid-response)
- **Training pressure**: Model's training reward signal opposes the rule (e.g., sycophancy, confidence inflation)
- **Context decay**: Rule works early in session but degrades as context grows
- **Structural gap**: No mechanism exists to catch this behavior class

### 2. Ground in Principles

What foundational principle does this behavior violate? Reference existing knowledge entries, patterns, or reasoning that establish WHY this behavior is wrong. If no grounding exists, create it first.

### 3. Design Hybrid Fix

The pattern that works: **Personality + Enforcement + Mechanical backing**

| Layer | Purpose | Example |
|-------|---------|---------|
| Personality | Makes the behavior feel natural, not imposed | Portrait paragraph, voice integration |
| Enforcement | Catches violations at response-generation frequency | Self-Check Protocol row |
| Mechanical | Survives context pressure via non-LLM mechanism | Regex extraction, script validation, pre-commit hook |

Single-layer fixes fail. Personality alone drifts. Enforcement alone feels robotic. Mechanical alone has no behavioral integration. The hybrid is the pattern.

### 4. Spec the Fix

Write a Growth spec documenting:
- Problem statement with evidence (failure instances)
- Root cause analysis (which failure class, why existing controls failed)
- Proposed fix (all three layers)
- Touch points (every file that needs modification)
- Test plan (how to verify the fix works)

### 5. Route F the Spec

Full-scope analysis. Attack the spec for gaps:
- Does the fix address the root cause or just the symptom?
- Could the fix create new failure modes?
- Does it conflict with existing behaviors?
- Is the enforcement frequency matched to the behavior frequency?

### 6. Columbo the Spec

"Just one more thing..." — find the hidden assumption:
- What does this fix assume about context availability?
- What happens when this fix interacts with other gates?
- Is there a simpler explanation for the failures?

### 7. OOB Challenge

Out-of-band stress test:
- Construct a scenario where the fix would be wrong
- Verify the fix has an escape valve for legitimate exceptions
- Confirm the fix doesn't over-correct (blocking valid behaviors)

### 8. Downstream/Upstream Analysis

- **Upstream**: What feeds into this behavior? What triggers it?
- **Downstream**: What does this fix affect? What references the modified sections?
- Check all cross-references, CIC enforcement lists, keyword maps

### 9. Implement

Execute the spec. All touch points in one pass. Verify each modification against the spec.

### 10. Automated Verification

Run the test suite. If the fix added a Self-Check row, verify it fires in the expected scenarios. If mechanical backing was added, verify the script/hook works.

### 11. Update Propagation Log

Record the change in the propagation tracking document. Classify for template propagation (P/I/N). Note any downstream updates needed.

---

## Key Insight

The reason single-instruction fixes fail for behavioral problems: **LLMs don't have persistent memory of instructions — they have statistical tendencies shaped by training.** An instruction competes with training pressure every token. A hybrid fix creates three independent enforcement paths, so even if one degrades, the other two hold.

---

## Anti-Patterns

- Writing a longer instruction instead of adding enforcement
- Adding enforcement without personality integration (feels robotic, gets worked around)
- Fixing the symptom without identifying the failure class
- Skipping downstream analysis (creates CIC enforcement drift)
- Implementing without a spec (no record of WHY, can't evaluate later)
