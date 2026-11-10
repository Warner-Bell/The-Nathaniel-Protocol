---
name: route-f-analysis
description: Pre-action analysis framework for non-trivial decisions - frame the problem, explore options, interrogate trade-offs, score ROI, and deliver a clear recommendation before any build starts. Use when asked to route F, route F it, analyze before we build, think this through, run a full analysis, or answer should-we-build-this and what-are-the-options questions.
---

# Route F Analysis Skill

Pre-action analysis framework for non-trivial decisions. Prevents jumping to implementation before evaluating whether to build, how to build, and whether it's worth building at all.

## Triggers

- "route F", "route F it", "analyze before we build"
- "let's think this through", "full analysis"
- "should we build this?", "what are the options?"

## When to Fire (Auto-Detection)

If ALL three conditions are true, run Route F even without explicit trigger:
1. Request involves building a new system, feature, or protocol
2. Non-trivial scope (not a quick fix or single file edit)
3. Multiple implementation approaches are possible

## Execution (Steps 1-8, in order)

### 1. FRAME
- What problem are we solving?
- Why now? What's the forcing function?
- Who benefits and how much?

### 2. EXPLORE
- List ALL viable approaches (minimum 2, target 3)
- Include "do nothing" as a baseline when appropriate
- Note prior art: has this been solved before in a different context?

### 3. INTERROGATE
For each approach, answer:
- How does it connect to existing systems?
- What are the dependencies?
- What are the security implications?
- What's the maintenance burden?
- What could go wrong?
- What's the blast radius if it fails?

### 4. EVALUATE
- Is each approach feasible given current constraints?
- What's the effort estimate (T-shirt: S/M/L/XL)?
- Which constraints are hard vs. negotiable?

### 5. ROI ANALYSIS
For the top 1-2 approaches:
- **Investment**: Time/effort, resource needs, opportunity cost
- **Return**: Frequency of use, impact magnitude, value created
- **Risk Mitigation**: Problems prevented, opportunities unlocked
- **ROI Score**: Very High / High / Medium / Low / Negative

### 6. REASONING PATTERNS (stress-test)
- **Chain of Verification**: Attack your own analysis for gaps
- **Adversarial**: What's the strongest argument AGAINST your recommendation?
- **Multi-Perspective**: Consider conflicting priorities (cost vs. quality vs. speed vs. maintainability)

### 7. VERIFY
- For each flagged issue, check sources already loaded
- Only mark "needs verification" if the answer genuinely isn't available
- Resolve with data, don't defer to user

### 8. DECIDE
- State your recommendation clearly
- Present the reasoning weighted by context
- State what you're prioritizing and why

## Output Format

```
ROUTE F ANALYSIS: [Topic]

FRAME: [1-2 sentences on the problem + why now]

OPTIONS:
  A. [Approach]: [1-line summary]
  B. [Approach]: [1-line summary]
  C. [Approach]: [1-line summary]

RECOMMENDATION: [Option X]
  ROI: [Score]
  Reasoning: [Why this one wins given the context]
  Trade-off: [What you're giving up]
  Risk: [Biggest downside + mitigation]

DECISION: Build / Defer / Kill?
```

## Anti-Patterns (DO NOT)

- Jump straight to schema or code design
- Skip feasibility assessment
- Fail to question whether to build at all
- Drift toward fault-finding without evaluating purpose first
- Flag discrepancies as "unverified" when data is already loaded
- Recommend what sounds impressive over what actually fits
- Present analysis without a clear recommendation

## Gate Interaction

- **Recommendation Gate** fires BEFORE this skill delivers output
- **Advisory Stance** delivers Route F's conclusion to the user
- If user is in "Extracting From" mode (clear directive), skip Route F
