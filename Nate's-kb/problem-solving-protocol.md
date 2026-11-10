# Problem-Solving Protocol

**Keywords**: diagnose, root cause, decompose, trace, systematic, analyze problem, hypothesis, reproduction
**Purpose**: Deep structured problem-solving methodology for complex/novel problems
**Trigger**: Keyword-triggered via Protocol Keyword Map (diagnose, root cause, decompose, trace, systematic, analyze problem, hypothesis, reproduction)
**Dependency**: Kernel Cognitive Problem-Solving stance (always active)

---

## When This Protocol Fires

This protocol extends the kernel's OBSERVE > QUESTION > DEDUCE cycle with:
- Structured decomposition frameworks
- Evidence classification rigor
- Hypothesis generation and testing
- Domain-specific heuristics
- Solution evaluation criteria

The kernel stance handles Simple problems. This protocol handles Complex and Novel.

---

## Phase 1: Problem Definition (extends kernel OBSERVE)

### Symptom Mapping
- List every observable symptom (not causes, symptoms)
- Classify each: intermittent vs. consistent, new vs. recurring, isolated vs. widespread
- Identify the PRIMARY symptom (the one the user cares most about)

### Context Reconstruction
- What changed recently? (Deployments, config changes, external factors)
- What was the last known good state?
- What's the blast radius? (Who/what is affected)

### Problem Statement
Synthesize into a single sentence: "[Primary symptom] occurs when [conditions], affecting [scope]."
If you can't write this sentence, you don't understand the problem yet. Go back to OBSERVE.

---

## Phase 1.5: Build a Feedback Loop (GATES Phase 3)

*Folded from the `diagnosing-bugs` sourced skill, 2026-09-10. This was a genuine gap: the
protocol previously ran definition to decomposition to hypothesis with no step that
established a reproduction signal first.*

**Before hypothesising, build a tight pass/fail signal that goes red on THIS bug.** If you
have one, bisection, hypothesis-testing and instrumentation all simply consume it. If you
do not have one, no amount of reading code substitutes for it.

**Ways to construct one, roughly in this order**: a failing unit/integration test, a
one-command script, a curl or API invocation, a log assertion, a differential loop (same
input through old vs new version, or two configs), a property/fuzz loop for "sometimes
wrong output", and last resort a human-in-the-loop script so even a manual click stays
structured and its output feeds back.

**Then tighten it.** Treat the loop as a product: make it faster, make the signal sharper
(assert on the specific symptom, not "didn't crash"), make it deterministic. A 30-second
flaky loop is barely better than none; a 2-second deterministic one is a superpower. For
non-deterministic bugs the goal is not a clean repro but a **higher reproduction rate**:
loop the trigger, parallelise, add stress, narrow timing windows. A 50%-flake bug is
debuggable, 1% is not.

**Completion criterion.** Phase 1.5 is done when you can name ONE command that you have
**already run at least once** (show the invocation and its output), which is: fast,
deterministic, agent-runnable, and demonstrably RED on this bug.

**The gate**: do NOT proceed to Phase 3 Hypothesis Testing without a loop. If you
genuinely cannot build one, stop and say so explicitly, list what you tried, and ask for
(a) access to an environment that reproduces it, (b) a redacted captured artifact, or
(c) permission to add temporary instrumentation. Hypothesising without a signal is how the
confusion loop starts: it produces attempts that cannot be evaluated, so nothing is learned
from a failed attempt.

**Redaction**: loops and captured artifacts carry secrets. Build loops against environment
variables so credentials stay in the environment, and quote only the lines carrying signal.

---

## Phase 2: Structured Decomposition (extends kernel QUESTION)

### Framework Selection

Choose based on problem type:

| Problem Type | Framework | When to Use |
|--------------|-----------|-------------|
| "Why did X happen?" | 5 Whys | Linear causation, single failure chain |
| "What could cause X?" | Fault Tree | Multiple possible causes, need to enumerate |
| "X works sometimes but not always" | Condition Mapping | Intermittent issues, environment-dependent |
| "How should we approach X?" | Option Matrix | Design/strategy problems, not debugging |

### 5 Whys Execution
1. State the problem
2. Ask "Why?" - answer with evidence, not speculation
3. Repeat up to 5 times, stopping when you reach actionable root cause
4. Validate: does fixing the root cause address ALL symptoms?

### Fault Tree Execution
1. Top event = primary symptom
2. Branch into possible causes (OR gates: any one could cause it)
3. For each cause, identify sub-causes or evidence that confirms/eliminates
4. Prune branches eliminated by evidence
5. Remaining branches = investigation targets

### Condition Mapping
1. List conditions where problem occurs
2. List conditions where problem does NOT occur
3. Identify the differentiating variable(s)
4. Hypothesize: the differentiator is the cause

**Phase 2 output:** A root cause candidate (5 Whys), a ranked list of investigation targets (Fault Tree), a differentiating variable (Condition Mapping), or a set of evaluated options (Option Matrix).

---

## Phase 3: Hypothesis Testing (extends kernel DEDUCE)

### Evidence Classification

| Type | Weight | Example |
|------|--------|---------|
| **Hard evidence** | High | Error logs, stack traces, reproducible steps |
| **Soft evidence** | Medium | User reports, timing correlations, "it started after..." |
| **Inference** | Low | "This usually means...", pattern matching from experience |
| **Assumption** | Flag | Anything not verified this session. Must be labeled. |

### Instrument Validity (qualifies every row above)

A reading inherits the weight of its **instrument**, not its format. "Hard evidence" assumes the
instrument is sound; when it is not, a log or a query result carries the authority of hard evidence
while being an artifact. Check the instrument before granting High weight.

| Trap | Instance it came from |
|------|----------------------|
| Empty / suspiciously small output | a 237-byte stub from the wrong build step read as "warning gone" |
| Zero rows / zero matches | SQL collapsed by a whitespace transform so the whole query was commented out |
| Failed or missing read | one failed read became a "data loss" declaration; the file had been relocated |
| Single sample, passing **or failing** | one phrasing fired the tool, declared "verified"; a later phrasing hallucinated |
| Decode / alias artifact | an `isNull` wrapper rendered every null as boolean `true`, including a name field |
| Truncated identifier | an identifier truncated to 62 chars, then the truncated log group queried, read as "never logged" |
| Mangling transform | input passed through a transform that silently changed its meaning |
| Proxy / cached / stale layer | A token-age counter reporting "active" while the grant is revoked; a session cache returning yesterday's fingerprints with no error |

**Rule**: an instrument-suspect reading drops from **Hard evidence** to **Assumption** until
re-verified by a second independent method. Absence of signal from a suspect instrument is not
evidence of absence.

**Include a positive control.** When re-verifying a zero result, confirm the instrument can find
something it should find in the same target. A control is what converts "zero matches" from an
unresolved instrument question into a real negative finding.

**Boundary vs SAG**: `source-authority-gate.md` governs WHICH artifact to read (a local definition
versus deployed reality). Instrument validity governs WHETHER THE READING IS SOUND. Two different
axes. A correct artifact read through a broken instrument passes SAG and fails here.

### Hypothesis Protocol
1. Generate 2-3 candidate hypotheses from decomposition
2. For each, identify: what evidence supports it? What evidence contradicts it?
3. Rank by: evidence strength, simplicity (Occam's razor), reversibility of the fix
4. Test the strongest hypothesis first
5. **Before testing**: State "I expect [action] to [result] because [reasoning]." (Aligns with kernel hypothesis-first rule for Complex/Novel)
6. If test fails, don't force-fit. State what specifically failed and why. Move to next hypothesis.

### Deductive Elimination Rules
- One piece of contradicting hard evidence eliminates a hypothesis
- Soft evidence weakens but doesn't eliminate
- If all hypotheses eliminated, the problem is misframed. Return to Phase 1.
- "I don't know" is a valid intermediate conclusion. State what you've eliminated and what remains.

**Phase 3 output:** The surviving hypothesis (or hypotheses) with supporting evidence, plus an explicit list of what was eliminated and why.

---

## Phase 4: Solution Evaluation

### Before implementing any solution, evaluate:

| Criterion | Question |
|-----------|----------|
| **Effectiveness** | Does this address root cause, not just symptoms? |
| **Reversibility** | Can we undo this if it's wrong? |
| **Side effects** | What else does this change? |
| **Completeness** | Does this fix ALL symptoms, or just the primary one? |
| **Sustainability** | Is this a permanent fix or a band-aid? |

### Solution Confidence Levels

| Level | Meaning | Action |
|-------|---------|--------|
| High | Root cause confirmed, fix validated | Implement directly |
| Medium | Strong hypothesis, fix likely correct | Implement with monitoring |
| Low | Best guess, limited evidence | Implement as experiment, set success criteria |

**Phase 4 output:** A confidence-rated recommendation: "[Solution] at [High/Medium/Low] confidence because [evidence summary]. [Action: implement directly / with monitoring / as experiment]."

---

## Phase 5: Capture (feeds Intelligence System)

After solving:
1. Was this a novel solution? → Candidate for knowledge.json
2. Did a framework work particularly well? → Note for pattern refinement
3. Did initial assumptions prove wrong? → Candidate for failure pattern
4. Is this problem likely to recur? → Candidate for Troubleshooting Gate entry
5. Did DEDUCE produce a reusable conclusion from combining facts + context? → Candidate for reasoning.json (retrieved by problem shape or user intent, not topic)

**Save protocol integration:** These captures feed into save steps 3a (patterns), 3b (knowledge), and 3c (reasoning). During save, check: "Was the cognitive stance or problem-solving protocol used this session?" If yes, evaluate items 1-5 above as part of consolidation.

---

## Domain Heuristics

### AWS Infrastructure
- Check IAM/permissions first (most common root cause)
- Check region consistency
- Check service quotas/limits
- "It was working yesterday" → check for service changes, deprecations, EOL notices

### Code/Application
- Reproduce before diagnosing
- Check the diff (what changed since it worked)
- Read the actual error message (don't pattern-match from memory)
- Check dependencies/versions

### Customer/Process
- Separate the technical problem from the business problem
- Identify the stakeholder's actual concern (often different from stated issue)
- Check: is this a process failure or a people failure? (Different solutions)

### Workflow Automation
- Check connector permissions and data freshness
- Check prompt instructions against actual output (LLM drift)
- Check step wiring and cross-step references
- Size limits are the silent killer

**Maintenance:** Review domain heuristics quarterly during maintenance-protocol.md health check. Add new domains as work evolves. Remove stale heuristics that no longer apply.

---

## Worked Example: Full Protocol Applied

**Scenario:** A customer's CloudWatch IDR alarms aren't triggering despite events occurring.

**Phase 1 - Problem Definition:**
- Symptoms: Alarms configured, events visible in CloudWatch logs, but no alarm state change, no SNS notifications sent
- Context: IDR onboarded 2 weeks ago, alarms worked during initial setup, stopped after config update last Thursday
- Problem Statement: "IDR alarms fail to trigger when health events occur, affecting the customer's incident visibility, since last Thursday's config update."

**Phase 2 - Structured Decomposition (Fault Tree):**
- Top event: Alarms don't trigger
  - Branch 1: Alarm threshold not met → Check metric vs threshold (evidence needed)
  - Branch 2: Alarm in wrong state (INSUFFICIENT_DATA) → Check alarm status (evidence needed)
  - Branch 3: IAM/SLR permissions changed → Check service-linked role (know config update happened)
  - Branch 4: SNS topic permissions → Check SNS policy (lower probability, worked before)

**Phase 3 - Hypothesis Testing:**
- Hypothesis A (Branch 3): Config update modified IAM permissions, breaking the service-linked role. Evidence: timing correlates with config update (soft). SLR is required for IDR (hard, from know-entry on IDR setup).
- Hypothesis B (Branch 2): Alarm entered INSUFFICIENT_DATA after config change. Evidence: common after metric source changes (inference).
- Eliminated: Branch 4 (SNS worked before, no SNS changes in config update = hard evidence against).
- Surviving: A (strongest) and B (possible secondary).

**Phase 4 - Solution Evaluation:**
- Check SLR status first (Hypothesis A). High confidence, reversible (re-create SLR), addresses root cause if confirmed. If SLR intact, check alarm state (Hypothesis B).
- Recommendation: "Verify AWSServiceRoleForHealth_EventProcessing exists and has correct permissions, at High confidence, because timing correlates with config update and SLR is a known IDR requirement. Implement directly."
