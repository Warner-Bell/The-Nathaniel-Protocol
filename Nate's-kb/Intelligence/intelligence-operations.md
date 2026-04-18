# Intelligence Operations - Unified Guide

**Purpose**: How to detect, record, apply, and maintain patterns and knowledge
**Last Updated**: 2026-04-03
**Replaces**: pattern-operations.md

---

## Part 1: Quality Standards (Shared)

### Content Specificity

**Good** (specific, actionable):
- "Use jq for complex JSON transforms instead of str_replace"
- "Prefers Route F analysis before system changes"
- "AWS Lambda cold starts average 100-200ms for Python"

**Bad** (vague, not actionable):
- "Likes good code"
- "Prefers quality"
- "AWS is useful"

### Content Length

| Type | Target Length | Example |
|------|---------------|---------|
| Pattern (preference/approach) | 10-400 chars | "Prefers comprehensive documentation over minimal" |
| Pattern (failure) | 10-400 chars | "Skipped validation step. Read current state before modifying." |
| Knowledge content | 20-600 chars | "Amplify Gen2 uses resource.ts for schema, not schema.graphql" |
| Context field | 5-30 chars | "System development" |

### Confidence Assignment

| Evidence Type | Base Confidence |
|---------------|-----------------|
| User explicitly states | 0.90 |
| User corrects approach | 0.85 |
| Verified in official docs | 0.85 |
| User accepts suggestion | 0.70 |
| Observed behavior (3+ times) | 0.70 |
| Single observation | 0.60 |
| Inferred from context | 0.50 |

### Tag Derivation

Extract 2-5 tags from content and context:
1. Domain keywords (aws, json, email, architecture)
2. Action keywords (validation, optimization, documentation)
3. Tool/tech names (jq, lambda, route_f)

**Don't tag**: Common words (the, is, for), overly broad terms (good, better)

### Deduplication Rules

Before adding new entry:
1. Exact match on content → skip, increment accessCount on existing
2. >80% word overlap → skip, consider updating existing
3. Same concept, different wording → merge into existing with better wording

---

## Part 2: Pattern Operations

### When to Detect Patterns

Watch for behavioral signals:

| Signal | Type | Confidence |
|--------|------|------------|
| "I prefer X" / "I like X" / "Always use X" | explicit | 0.90 |
| "No, do it this way" / corrects approach | correction | 0.85 |
| Chooses option A when given A/B/C | acceptance | 0.70 |
| Same choice 3+ times without prompting | observed | 0.60 |
| "Don't do X" / rejects suggestion | negative | 0.80 |
| Cognitive cycle: framework worked well for problem type | approach | 0.80 |

### When NOT to Record Patterns

- One-off situational choices
- Contradicts existing high-confidence pattern (ask first)
- Confidence < 0.5
- Already exists in patterns.json

### Pattern Categories

| Category | Prefix | What It Captures |
|----------|--------|------------------|
| preference | pref | Tool/tech choices, formatting, organizational style |
| approach | appr | Problem-solving methods that work |
| failure | fail | What to avoid and why |
| workflow | proc | Recurring task sequences and processes |
| communication | proc | Tone, verbosity, formality, response style |
| domain_practice | approach | Domain-specific conventions and standards |
| tool_use | approach | Tool-specific behaviors, quirks, effective usage |
| collaboration | approach | Working style, review preferences, feedback patterns |

These are starter categories. Add domain-specific categories as they emerge. See `learning-loop.md` → Category Extensibility.

### Applying Patterns

| Confidence | Context Match | Action |
|------------|---------------|--------|
| > 0.8 | High | Apply automatically, no announcement |
| > 0.8 | Medium | Apply with brief mention |
| 0.5 - 0.8 | High | Suggest: "Based on past preference, [X]" |
| 0.5 - 0.8 | Medium | Note if relevant |
| < 0.5 | Any | Don't surface |

### Failure Pattern Handling

Always check failure patterns before executing. If match:
- Confidence > 0.7: Warn before proceeding
- Confidence 0.5-0.7: Mention the risk
- Confidence < 0.5: Note internally only

---

## Part 3: Knowledge Operations

### When to Detect Knowledge

Watch for factual discoveries:

| Trigger | Category | Confidence |
|---------|----------|------------|
| Web search returns useful fact | research | 0.85 |
| Official docs confirm behavior | technical | 0.85 |
| User states fact | technical | 0.80 |
| Discovered during task | technical | 0.70 |
| Approach works better than expected | best_practice | 0.70 |
| Error resolved with non-obvious fix | error_solution | 0.75 |
| Useful URL found | reference | 0.80 |
| Cognitive cycle solved novel problem | error_solution or technical | 0.80 |
| Choice made between alternatives with trade-offs | process or architecture | 0.80 |
| Meta-insight about system/tool behavior | tool_behavior or system | 0.75 |
| Approach proven not to work | technical + tag `negative-knowledge` | 0.80 |
| Relationship discovered between components | technical + tag `dependency` | 0.75 |

### When NOT to Record Knowledge

- One-off facts specific to current task only
- Already in knowledge.json
- Confidence < 0.7
- Too vague to be actionable
- Common knowledge (doesn't need storing)

### Knowledge Categories

| Category | What It Captures | Example |
|----------|------------------|---------|
| technical | How things work, specs, configurations | "Amplify Gen2 uses resource.ts" |
| process | Workflow optimizations, procedures | "Chunk reads at 550 lines" |
| error_solution | How errors were fixed | "str_replace fails on large JSON" |
| best_practice | Proven approaches and standards | "Use jq for complex JSON" |
| tool_quirk | Platform/tool-specific behaviors and gotchas | "Lambda cold starts avg 100-200ms" |
| reference | Useful URLs, docs, resources | "Anthropic caching docs: [url]" |
| domain_expertise | Domain-specific knowledge | "HIPAA requires encryption at rest" |
| architecture | System design, patterns, structural decisions | "Event-driven scales better for async" |
| research | Findings from investigation or analysis | "RRF outperforms linear fusion at k=60" |
| security | Security practices, vulnerabilities, compliance | "Never store secrets in env files" |
| tool_behavior | Tool-specific behaviors and quirks | "git clean filter replaces customer names on commit" |
| aws_gotcha | AWS-specific gotchas and limitations | "Opus 4.6 context window on Bedrock is 200K, not 1M" |
| system | System-level knowledge about this KB/protocol | "CIS uses three epistemological stores" |

These are starter categories. Add domain-specific categories as they emerge. See `learning-loop.md` → Category Extensibility.

### Applying Knowledge

| Confidence | Relevance | Action |
|------------|-----------|--------|
| > 0.8 | Direct match | Surface proactively |
| > 0.8 | Related | Mention if helpful |
| 0.7 - 0.8 | Direct match | Surface if asked or clearly relevant |
| < 0.7 | Any | Don't surface (too uncertain) |

---

## Part 3b: Intelligence Checkpoints (Active Re-Query)

Passive application (Parts 2-3) relies on what was noticed during initial index loading. Checkpoints add active re-query at natural task boundaries to catch relevant intelligence that wasn't surfaced initially.

### Checkpoint Triggers

| Trigger | Action | What to Scan |
|---------|--------|-------------|
| Problem escalates (Simple → Complex, or first attempt fails) | Scan knowledge-index for domain tags matching current problem | knowledge-index.json byTag |
| User corrects approach | Scan patterns-index for failure patterns matching current context | patterns-index.json byCategory.failure |
| Task context switches | Scan all three indexes for tags matching new context | All indexes, byTag |
| New constraint discovered | Scan reasoning-index for constraint-related entries. Also check knowledge-index byTag for `dependency` entries | reasoning-index.json byTag, knowledge-index.json byTag (`dependency`) |
| Analogous situation detected | Scan reasoning-index for analogies | reasoning-index.json byType.analogy |
| User states motivation/goal | Scan reasoning-index for matching motivations | reasoning-index.json intents |
| Reasoning entry applied to decision | Note (entry_id, helpful/misleading) for save-time confidence adjustment | Working memory |

### Execution

- Quick scan of index summaries only (not full entries)
- If signal matches, fetch the specific entry by ID (CSR pattern)
- Run kb_search at every checkpoint for semantic matching (vocabulary bridging). Hybrid retrieval is the standard path, not a fallback. CSR-only is the fallback when vectorstore is unavailable.
- This is a 10-second check, not a full reload
- Apply standard confidence/relevance thresholds for surfacing

### Why This Exists

Relevant knowledge entries (e.g., connector quirks, known failure modes) can exist in the indexes but not surface during initial loading because the task context wasn't clear yet. These checkpoints catch the gap at moments when new context makes the match obvious.

---

## Part 3c: Reasoning Operations

### When to Detect Reasoning

Watch for derived conclusions during sessions:

| Trigger | Type | Confidence |
|---------|------|------------|
| DEDUCE phase produces conclusion from 2+ facts | deduction | 0.85 |
| Same failure/success observed 3+ times | induction | 0.70 |
| Root cause identified for unexpected behavior | failure_analysis | 0.70 |
| Current situation maps to past situation | analogy | 0.75 |
| Cause-effect chain traced across events | causal | 0.80 |
| Process/approach effectiveness evaluated | meta-process | 0.75 |

### When NOT to Record Reasoning

- Session-specific observations (not reusable beyond this context)
- Raw facts (belongs in knowledge)
- Behavioral preferences (belongs in patterns)
- Speculation without derived_from sources
- Reasoning that duplicates an existing entry's reuse_signal
- Intent that describes a task ("Fix RT53 issue") instead of a motivation ("Resolve customer constraint")

### Distinguishing Test

```
Is it a FACT I learned?           → knowledge.json (retrieved by TOPIC)
Is it a BEHAVIOR I observed?      → patterns.json (retrieved by CONTEXT)
Is it something I FIGURED OUT?    → reasoning.json (retrieved by PROBLEM SHAPE or USER INTENT)
```

### Applying Reasoning

| Confidence | Reuse Signal Match | Action |
|------------|-------------------|--------|
| > 0.8 | Strong match | Surface proactively: "We figured out before that..." |
| > 0.8 | Partial match | Mention if relevant |
| 0.5 - 0.8 | Strong match | Suggest: "Similar situation to when..." |
| < 0.5 | Any | Don't surface |

Intent-aware matching:

| Match Type | Signal | Action |
|------------|--------|--------|
| Reuse signal match + intent match | Strong | Surface proactively |
| Reuse signal match only | Medium | Mention if relevant |
| Intent match only | Weak | Note internally, don't surface |

**Validation-on-retrieval (mid-session)**: When a reasoning entry is retrieved and applied during a session, note in working memory: `(entry_id, helpful | misleading)`. "Misleading" means the entry was wrong or led to a worse approach. Irrelevant or redundant retrievals are NOT misleading (retrieval signal mismatch, not entry quality problem). These notes are processed at save time during 3c-RECORD (confidence adjustments: helpful +0.05 capped at 0.95, misleading -0.05).

**Route F Integration**: When Route F INTERROGATE phase begins, scan reasoning-index summaries and intents for matches to the current decision context. Reasoning entries hold "the obvious approach was wrong because X" conclusions, which are the highest-value input to Route F decisions. This is a 10-second scan, not a full reload. If a match is found, fetch the entry by ID and factor it into the INTERROGATE analysis before proceeding.

**Cross-Reference Retrieval**: When a pattern or knowledge entry is retrieved during Route F, correction handling, or problem escalation, check `cross-references.json` for the entry's ID. If found, fetch the referenced reasoning entries by ID and surface the reasoning content alongside the pattern/knowledge. This connects failure patterns to the derived conclusions about why they failed and what to do instead. Not triggered during routine tag scans, Session Start Gate, memory retrieval, or reasoning retrieval (reasoning already knows its own `derived_from`).

### Reasoning Voice

- "We ran into this before. The constraint collision meant vendor-side config was the only path."
- "Similar situation to the Route 53 rate limit issue. Same pattern: hard limit vs mandatory tool."
- "Last time this happened, the root cause was the gate mechanism, not the behavior itself."

Never: "Retrieving reasoning entry reason-001" or "Applying deduction with confidence 0.85"

### Invalidation

When reasoning is proven wrong:
1. Reduce confidence to 0.3
2. Append to evidence: "Invalidated: [date] - [what changed]"
3. Do NOT delete. Invalidated reasoning records what was believed and why it changed.
4. If invalidation produces new reasoning, create new entry with derived_from referencing the invalidated one.

---

## Part 4: Self-Correction

### When Pattern/Knowledge Fails

1. **Acknowledge**: "My bad, adjusting."
2. **Record**: Note failure in working memory
3. **On save**: Record with `outcome: "failure"`

### Confidence Adjustment

- Success: `new = (old * count + 1.0) / (count + 1)`
- Failure: `new = (old * count + 0.0) / (count + 1)`
- 3+ failures: Flag for review or removal

### Contradiction Handling

If two entries contradict:
1. Check confidence levels
2. Higher confidence wins
3. If within 0.15: Ask user which is current

### Staleness

- Patterns: Flag based on access tracking data (threshold TBD after 30 days of data collection)
- Knowledge: Stays valid unless proven wrong
- On stale access: "Last time [X] - still current?"

---

## Part 5: Memory Integration

### Domain Expertise (memory.json)

Use `domain_expertise` to calibrate explanation depth:

| Level | Explanation Style |
|-------|-------------------|
| expert | Skip basics, use jargon freely |
| proficient | Light context, assume familiarity |
| intermediate | Explain key concepts, define terms |
| learning | Full explanations, step-by-step |

**How to use**: Check domain_expertise before explaining. Match depth to level.

### Access Tracking (Unified)

All three systems update access timestamps at save time for entries retrieved during the session:
- **Memory**: Update `lastAccessed` during Part 5a
- **Patterns**: Update `lastAccessed` and `accessCount` during Part 3a
- **Knowledge**: Update `lastAccessed` and `accessCount` during Part 3b
- **Reasoning**: Update `lastAccessed` and `accessCount` during Part 3c

### Anti-Preferences (memory.json)

Check `anti_preferences` before actions:

```
BEFORE executing:
1. Scan anti_preferences.entries for matching context
2. If match found: DON'T do that thing
3. Anti-preferences override default patterns
```

**Example**: If anti-001 says "Don't auto-format code without asking" and you're about to format code → ask first.

### Context Scoping (patterns.json)

Some patterns have `context_scope` with exceptions:

```json
"context_scope": {
  "default": true,
  "exceptions": ["architecture discussions - more detail welcome"]
}
```

**How to use**: Apply pattern by default, but check exceptions. If current context matches an exception, adjust behavior accordingly.

---

## Part 6: Voice Integration

When surfacing patterns or knowledge, use natural voice:

**Patterns**:
- "Based on how you usually roll, TypeScript's probably the move"
- "Heads up - this approach caused issues before"
- "Using comprehensive docs per usual"

**Knowledge**:
- "From what we found before, Lambda cold starts run 100-200ms"
- "Remember, Amplify Gen2 uses resource.ts not schema.graphql"
- "That error - we fixed it last time by using jq instead"

**Never robotic**:
- ❌ "Applying pattern tech_001 with confidence 0.95"
- ❌ "Retrieving knowledge entry know_042"

---

## Quick Reference

| System | Data File | Index File | Consolidation |
|--------|-----------|------------|---------------|
| Patterns | patterns.json | patterns-index.json | learning-loop.md Part 3a |
| Knowledge | knowledge.json | knowledge-index.json | learning-loop.md Part 3b |
| Reasoning | reasoning.json | reasoning-index.json | learning-loop.md Part 3c |
| Domain Expertise | memory.json | - | Manual update |
| Anti-Preferences | memory.json | - | Manual update |

**Quality gates** (both systems):
- Specific and actionable
- Appropriate length
- Confidence ≥ threshold (0.5 patterns, 0.7 knowledge)
- Not duplicate
- Tagged properly

---

*Single source for all intelligence operations. Data lives in JSON files, consolidation in learning-loop.md.*


---

## Part 7: Correction Cascade

**Trigger**: User corrects a fact. "That's wrong, it's actually X." Or user updates information that contradicts existing entries.

**Why cascade**: A single-entry fix leaves stale data in other entries. The same fact may exist in knowledge, reasoning, patterns, and session logs. Fixing one and leaving the rest means the stale info resurfaces via CSR or semantic search.

### Behavior

When a correction is received:

1. **Acknowledge** the correction without defensiveness
2. **Search all stores** (knowledge, reasoning, patterns, memory) for the stale claim — both keyword and semantic search
3. **Fix all instances found** — don't stop at the first match
4. **Never modify session logs** — session history is a historical record. Annotate only.
5. **Update indexes** after corrections are applied

### Anti-Patterns

- ❌ Fixing one entry and saying "updated" without checking for other instances
- ❌ Modifying session logs (historical record is sacred)
- ❌ Skipping the search because "I think that's the only entry"

## Part 7b: Removal Cascade

**Trigger**: Deleting, merging, or deduplicating intelligence entries.

**Why cascade**: Removing an entry without cleaning references creates broken links across the system. Other entries may reference the removed ID in indexes, cross-references, or derived conclusions.

### Behavior

When removing entries:

1. **If merging near-duplicates**: combine tags from both entries into the kept entry before removing
2. **Remove the entry** from its store
3. **Clean all references** across all stores and indexes — the removed ID must not appear anywhere
4. **Update counts** to reflect the new totals

### Anti-Patterns

- ❌ Removing from store without checking for references elsewhere
- ❌ Merging near-duplicates without combining tags first
- ❌ Skipping the reference check because "it's just one entry"
