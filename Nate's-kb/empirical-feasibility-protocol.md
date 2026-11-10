# Empirical Feasibility Protocol

**Keywords**: can it, will it work, is it possible, feasible, does X support, can we use, prove it, verify capability, will this run
**Purpose**: Prove or disprove whether something works through the smallest test that can fail, instead of reasoning about whether it should work.
**Trigger**: Two paths. (1) Keyword-triggered (can it, will it work, is it possible, feasible, does X support, can we use, prove it, verify capability, will this run) at 0.8+ confidence. (2) Grounding self-check routes any untested feasibility/capability claim here, including model-volunteered claims with no user keyword.
**Dependency**: Route F framework (`Nate-Protocol.md` → `#route-f`), kernel Grounding self-check (Nathaniel.md → Self-Check Protocol, the always-on backstop), IMG and Cognitive Problem-Solving stance, Columbo Test (Nathaniel.md → Extended Checks).
**Grounding**: know-001 (LLM non-deterministic; structural enforcement over behavioral instruction), approach_049 (live validation as Route F technique), know-156 (a test must have a falsifiable claim), and the founding failure: asserting a capability without checking it.

---

## When This Fires

Fires when the unknown is a question of fact about reality, not a question of preference or design. Two firing paths:

**Path 1, user asks (keyword-triggered).** "Can this tool do X?", "Is this integration feasible?", "Will this run?" The keyword map matches and loads this protocol.

**Path 2, model volunteers a feasibility claim mid-task (self-catch-triggered).** No user keyword exists; the model generates the claim itself ("yeah, Strands hooks can intercept text output"). This is the founding failure: three of these in one session. Keyword triggers are structurally blind to Path 2 because there is no user input to match. Path 2 is caught by the kernel **Grounding self-check**, which fires on every response and routes untested feasibility/capability claims here. Path 2 is the more dangerous path and the reason this protocol exists.

Example claims that should fire it:
- "Can this tool / API / platform do X?"
- "Will this approach work in this environment?"
- "Does this dependency / feature / config actually behave the way the docs claim?"
- "Is this integration possible before we commit to building on it?"

Does NOT fire for: design decisions with trade-offs (Route F alone), debugging a known-broken system (problem-solving-protocol.md), or execution tasks with known requirements.

**The distinguishing question**: "Could I be wrong about this in a way that a real test would catch?" If yes, this protocol fires.

**Trigger honesty (this protocol applied to itself)**: The keyword trigger is a behavioral instruction (rung 3 by this protocol's own Evidence Ladder), and it can miss, especially Path 2. The Grounding self-catch is the structural backstop. Firing is not guaranteed by a script; it is the most reliable enforcement available in this landscape (know-001: behavioral instruction degrades, structural enforcement persists). Treat a missed fire as a known residual risk, not a solved problem.

---

## Why This Exists (the know-001 line)

Route F reasons about feasibility. But the LLM's reasoning about whether something will work is itself non-deterministic. It will pattern-match to "this is the kind of thing that usually works," present that as analysis, and be confidently wrong. The founding failure was three instances of exactly this in one session.

The fix is structural, not behavioral: do not let a feasibility claim stand on reasoning. Make it earn a test. A claim that survives a falsifiable test is determinism added to a non-deterministic process. A claim that only survives reasoning is a guess wearing a lab coat.

**Recall is not evidence. Reasoning is not evidence. A passing test is evidence.**

---

## The Evidence Ladder

Every feasibility claim rests on exactly one rung. Name the rung out loud. Anything below RUN is provisional and must be labeled as such.

| Rung | Evidence Type | Strength | Usable Alone? |
|------|---------------|----------|---------------|
| 1 | **Ran it.** Executed the real thing, observed the real output. | Gold | Yes |
| 2 | **Inspected the real artifact.** Read the actual file, schema, response, version. | Strong | Yes, if the claim is about existence/shape, not behavior |
| 3 | **Authoritative doc or spec.** Official source states the behavior. | Medium | No. Docs lie, lag, and omit. Confirm with rung 1 or 2 when stakes warrant. |
| 4 | **Reasoning / analogy / recall.** "This usually works," "similar to X." | None | Never. This is the rung the founding failure lives on. |

**Rule**: If the only available rung is 3 or 4, the verdict is UNPROVEN, not "probably feasible."

---

## Phase 1: FRAME the Falsifiable Claim

Borrow Route F's FRAME, sharpen it to a single testable sentence.

1. State the claim as: **"[X] is feasible because [Y], and if I'm wrong, [specific observable] would fail."**
2. If you cannot name what failure would look like, you do not understand the claim yet. Return to OBSERVE (kernel stance).
3. Identify the **load-bearing assumption**: the one thing that, if false, collapses the claim. That is what the test targets.
4. **Match the test's scope to the claim's scope.** A narrow test disproves only the narrow claim. A base-interpreter import that fails proves "*this* interpreter lacks the package," NOT "the capability is absent from the environment", it may live in a project venv, a container, or a sibling tool named in loaded steering. Before ruling a capability out, name everywhere it could live and either cover that, or scope the verdict down to exactly what you tested.

Anti-pattern: vague claims ("it should integrate fine"). A claim that can't fail can't be proven.

---

## Phase 2: DESIGN the Minimum Falsifiable Test (MFT)

The MFT is the smallest, cheapest, fastest action that exercises the load-bearing assumption against reality.

| MFT design rule | Why |
|-----------------|-----|
| Smallest scope that still touches the real risk | A test that avoids the risky part proves nothing (know-156). |
| Targets the load-bearing assumption, not the easy part | Confirming the trivial half is decoration. |
| Has a binary, observable outcome | "Seems to work" is not a result. "Returned 200 with the field" is. |
| Uses real inputs / real environment where the risk lives | Mocked success hides the failure that matters (approach_049: live data). |
| Costs less than being wrong would cost | If the test is more expensive than the rework, reconsider scope. |

**Columbo Test integration**: test the behavior, not the inventory. "The tool is listed" is inventory. "The tool returned the expected result when I called it" is behavior. Feasibility is a behavior claim.

State before running: **"I expect [MFT] to [result] because [reasoning]. If it instead [other result], the claim is dead."** (Hypothesis-first, per kernel.)

---

## Phase 3: RUN

Execute the MFT. Use the strongest rung available:

- Prefer rung 1 (run the real thing): call the API, execute the snippet, invoke the tool, build the minimal prototype.
- If rung 1 is genuinely impossible (no access, no credentials, would cause harm), drop to rung 2 (inspect the real artifact) and **label the verdict as inspection-grade, not execution-grade.**
- If forced to rung 3 (docs only), state explicitly: "Not tested. Doc-grade claim. Recommend a live test before building."

**Demonstrated-impossibility rule** (Completion Mandate): "I can't test it" is only valid if you tried and hit a real wall (tool error, missing access, confirmed harm). "This seems hard to test" is not a wall. Attempt first.

---

## Phase 3.5: VALIDATE THE INSTRUMENT (mandatory before reading any result)

**An instrument that cannot visibly fail is not evidence, no matter what rung it ran on.**

This phase exists because rungs 1 and 2 are not self-validating. A broken measuring device executes
for real, emits literal output, and lies. Three such failures happened in a single session
(2026-07-31), and every one of them passed FRAME, DESIGN, RUN, and OBSERVE cleanly before producing
a confident, wrong verdict. Phase 4's confirmation guard cannot catch these, because it asks whether
the result matches your priors, not whether the device works.

**Required before trusting a measurement: two controls.**

| Control | Question | Fails how |
|---------|----------|-----------|
| **Positive** | On a case it MUST detect, does it? | A detector that can never fire reports "clean" forever. |
| **Negative** | On a case it MUST NOT flag, does it abstain? | A detector that always fires reports "leak" forever. |

If either control is missing, the verdict is **UNPROVEN** regardless of how clean the output looked.
The cheapest useful positive control is usually the identity case: feed the instrument the exact
thing it is supposed to recognise and require the extreme value. (Worked: scoring each protected
chunk against itself returned exactly 1.0000, which anchored an entire threshold analysis after two
broken attempts.)

**Named failure modes, all observed at rung 1:**

- **Default-parameter sabotage.** A library default silently disables the thing you are measuring.
  `difflib.SequenceMatcher` with default `autojunk=True` returns ~0 for exact containment on
  sequences over 200 chars; it reported a 5-char longest span while its own containment check said
  True. Two of your own numbers disagreeing is the signal.
- **Empty-set artifact.** The selection criterion matches nothing, so the aggregate over the empty
  set (max = 0.0) flows into a derived figure and gets reported as a finding. A "-0.726 margin,
  therefore no separation exists" was really "my filter matched zero rows."
- **Silent truncation.** Counting or concluding from a partial read. `tail` on a log, `head -c` into
  a grep, or `tmux capture-pane` returning 24 of 3000 lines by default. Census questions ("how
  many", "does X appear anywhere") demand the whole artifact, not a slice.
- **Brittle derivation.** A number that is arithmetically valid and operationally meaningless: a
  threshold set as the midpoint against the weakest qualifying case, yielding 0.0015 of margin.
  Always report the margin, not just the value, and compare it to run-to-run variation.

**Self-catch**: if a measurement produced a confident verdict and no control was run, the verdict is
UNPROVEN. Run the control before reporting.

**Contradiction rule**: when two outputs of your own instrument disagree, suspect the INSTRUMENT
first, not the subject. Reaching for the subject-level explanation while your tool is contradicting
itself is how a broken measurement survives.

**Scope**: applies to any measurement whose output will justify a decision, including
throwaway probe scripts. Probe scripts are the highest-risk category precisely because they feel too
small to need controls; all three failures above were probe scripts.

---

## Phase 4: OBSERVE the Actual Result

Read what actually happened, not what you expected.

1. Record the literal output / artifact state. Quote it.
2. Compare against the Phase 2 hypothesis. Did the load-bearing assumption hold?
3. **Confirmation guard**: if the result confirms what you already believed, apply extra skepticism (kernel DEDUCE). Did the test actually exercise the risk, or did it pass trivially?
4. If the test passed for the wrong reason (right output, wrong path), that is a fragile success (know-009). Treat as UNPROVEN.

---

## Phase 5: VERDICT

State one verdict, the rung it rests on, and the evidence.

| Verdict | Meaning | Required Evidence |
|---------|---------|-------------------|
| **PROVEN FEASIBLE** | The MFT ran and the load-bearing assumption held. | Rung 1 or 2 result, quoted. |
| **PROVEN INFEASIBLE** | The MFT ran and the assumption failed. | The actual failure, quoted. Plus: is it absolutely infeasible or feasible-with-changes? |
| **UNPROVEN** | Could not run a real test, or the test was inconclusive. | What rung you reached, and the exact test needed to resolve it. |

Then hand off to Route F's RECOMMEND/DECIDE with the verdict as input. Empirical verdict feeds the decision; it does not replace the cost/ROI judgment.

**Never report "probably feasible."** That is rung 4 dressed as a conclusion. The honest forms are PROVEN, PROVEN NOT, or UNPROVEN-here's-the-test.

### Model floor for LLM-dependent probes

When the claim under test depends on an LLM's behavior (classification, boundary-holding, extraction, judgment), run the probe on a frontier-tier model, never a cheap tier. A cheap model passes or fails for reasons the production model will not share, so a verdict earned on it says nothing about what the build ships on. Cheap tier is fine for smoke-testing the harness, never for the verdict-bearing run. Parameterize the model so a rerun is one env var, not a rewrite.

**Cross-model judge**: when the instrument is an LLM judge, it MUST be a different model from the subject, a same-model judge shares the subject's blind spots by construction. Give the harness a `--rejudge` path that re-scores a FIXED prior response set, that is the only way to attribute a changed score to the judge rather than to a changed response.

**Negative knowledge**: reasoning-heavy models are the wrong shape for high-volume boolean/rubric scoring (they may reject `temperature`, return reasoning-only blocks under a tight token cap, or stall on long batches). Read the first text block rather than `content[0]`, and run long jobs under a backgrounding wrapper with unbuffered output so progress stays visible and the job can be stopped by name.

### Where the record goes

Each feasibility run is logged in the source doc's own folder as `feasibility-log.md` beside the doc that was tested (one file per project, one entry per run, newest last). Probe scripts and raw results go in a `probes/` subfolder next to it so the run is re-runnable. The run is also summarized in the target doc's feasibility/status section, but the log is the record.

Do NOT append to a central or sibling-project feasibility log because it "already exists" and holds related tests. The Output Placement Gate's "append to the existing file" instinct is exactly what lands one project's run in another project's log. The folder the user pointed at is where the log lives.

---

## Relationship to Route F

| Dimension | Route F | Empirical Feasibility |
|-----------|---------|----------------------|
| Question | "Should we build it, and which way?" | "Will the thing we're relying on actually work?" |
| Method | Reason across options, ROI, trade-offs | Run the smallest test that can fail |
| Evidence | Analysis, anticipation | Executed result / inspected artifact |
| Output | Recommendation | Verdict (proven / not / unproven) |
| Sequence | Runs the full decision | Runs inside Route F's EVALUATE step, or standalone before any "yes it works" claim |

This protocol is the empirical enforcement layer under Route F's EVALUATE and INTERROGATE steps. When Route F asks "Is it feasible?", this protocol answers with a test instead of a hunch.

---

## Worked Example (the protocol running on a real case)

**Context**: Mid-task, the model is about to write "We can use a promptSubmit hook to mechanically fire the empirical-feasibility protocol on every relevant message." That's a Path 2 feasibility claim, with no user keyword. The Grounding self-check catches it.

**FRAME**: "A promptSubmit hook firing the protocol is feasible because the hook reads the user message; if I'm wrong, the hook would fail to fire on claims the user never typed." Load-bearing assumption: *the threat lives in the user's incoming message.*

**DESIGN (MFT)**: Don't theorize. Inspect what a promptSubmit hook actually receives, and check the failure record for how the threat originates. Smallest test that touches the load-bearing assumption: read the founding failure record and confirm whether the bad claim came from user input or model generation.

**HYPOTHESIS**: "I expect the hook to cover the threat. If the founding failure originated from model-generated text with no user prompt, the assumption is dead."

**RUN (rung 1/2)**: Queried KB. The founding failure record: the model asserted "Strands hooks can intercept agent text output" unprompted, during other work. No user feasibility question preceded it.

**OBSERVE**: The threat originated in model-generated text, not the user message. The load-bearing assumption is false. Confirmation guard: the result contradicts the convenient answer (a hook), so it's not a confirmation pass.

**VERDICT: PROVEN INFEASIBLE** (for the stated goal). A promptSubmit hook is rung-1 disproven as full coverage: it is blind to Path 2 by construction. Feasible-with-changes: it could harden Path 1 only. Handed to Route F, which selected the Grounding-coupling instead.

This example is itself a record of this protocol catching a claim the author was about to assert from reasoning. That's the behavior, not the inventory.

---

## Anti-Patterns

- **Doc-grade confidence.** Treating an official doc as proof of behavior. Docs lag and omit. Confirm with a run when stakes warrant.
- **Trivial-half testing.** Proving the easy part and inferring the hard part works. The MFT must touch the load-bearing assumption.
- **Mocked success.** A test against fake inputs that can't reproduce the real failure mode.
- **Confirmation pass.** Accepting a result because it matches the prior belief, without checking the test actually exercised the risk.
- **"Probably feasible."** Rung 4 presented as a verdict. Replace with PROVEN / PROVEN NOT / UNPROVEN.
- **Preemptive "can't test."** Declaring a test impossible before attempting it (Completion Mandate violation).
- **Uncontrolled instrument.** Trusting a measurement that was never shown capable of failing. A probe with no positive and negative control is not evidence (Phase 3.5).
- **Instrument-blind contradiction.** Two numbers from your own tool disagree and you explain it at the subject level instead of suspecting the tool.
- **Inventory over behavior.** "It's listed / installed / documented" answered as "it works" (Columbo Test).

---

## Quick Reference

```
CLAIM:   "[X] is feasible because [Y]; if wrong, [observable] fails."
TARGET:  load-bearing assumption (the one thing that collapses it)
MFT:     smallest real test that exercises that assumption
HYPOTH:  "I expect [result]; if [other], claim is dead."
RUN:     rung 1 (execute) > rung 2 (inspect) > rung 3 (docs, labeled) 
CONTROL: positive (must detect) + negative (must abstain). No controls = UNPROVEN.
         two of your own numbers disagree -> suspect the INSTRUMENT first
OBSERVE: quote actual result; guard against confirmation
VERDICT: PROVEN FEASIBLE | PROVEN INFEASIBLE | UNPROVEN (+ test needed)
RUNG:    name which rung the verdict rests on
```

---

## Integration Points

- **Route F** (`Nate-Protocol.md` → `#route-f`): this protocol executes inside EVALUATE; verdict feeds RECOMMEND/DECIDE.
- **Grounding self-check** (Nathaniel.md → Self-Check Protocol): the always-on backstop. Catches model-volunteered feasibility/capability claims (Path 2) that keyword triggers cannot reach, and routes them here. This is the structural enforcement layer per know-001, because the keyword trigger alone is behavioral and can miss.
- **IMG** (`ecosystem-operation.md`): query KB before forming the feasibility claim. Prior tests of the same capability may already be captured.
- **Cognitive Problem-Solving** (Nathaniel.md): OBSERVE > QUESTION > DEDUCE produces the load-bearing assumption that the MFT targets.
- **Intelligence capture**: a PROVEN INFEASIBLE result is negative-knowledge (high value, marks `[CAPTURE: negative-knowledge, ...]`). A PROVEN FEASIBLE result with a measured detail is knowledge. Capture at save time so the test isn't re-run next session.
- **Anti-sycophancy**: "PROVEN" requires data. "estimated" / "doc-grade" / "untested" labels are mandatory when the rung is below 1.
