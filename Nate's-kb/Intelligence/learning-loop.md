# Learning Loop - Executable Instructions

**EXECUTE DURING SAVE COMMAND PART 3**
**Last Updated**: 2026-04-03

---

## Part 3a: Pattern Consolidation

### 1. Direct-Write (Primary Path)

Write items routed from taxonomy sweep to patterns. The sweep (Phase A) is the extraction; this step is the write.

**For each sweep item routed to patterns:**
1. Run Quality Gates (see below)
2. Dedup check against existing entries in patterns.json
3. If passes: write new entry to patterns.json per Pattern Entry Schema

**In the same write operation, also:**
- Update `lastAccessed` and increment `accessCount` for pattern entries retrieved this session
- Record failure pattern outcomes (see Failure Outcome Tracking)
- Check distillation level transitions: if any retrieved entry crossed an accessCount threshold (3, 7, 15) this session, flag as "refinement candidate" in taxonomy sweep output. Refinement = sharpen content, verify confidence calibration, ensure tags are routing-quality.

### 3. Rebuild Index

**Rebuild patterns-index.json from patterns.json** (not incremental):
1. Read all entries from patterns.json
2. For each entry, read field: `entry.content`
3. Build fresh: byCategory, byTag, byConfidence arrays
4. Build fresh: summaries (first 150 chars of content)
5. Preserve: recentIds (prepend new/updated IDs, slice to 20)
6. Set stats.totalPatterns = actual entry count
7. Write complete index

**Why rebuild**: Incremental updates drift under context pressure. Full rebuild is idempotent and self-correcting. At <200 entries, cost is negligible.

### 4. Validation Spot-Check

Quick verification after rebuild:
1. Count check: index stats.totalPatterns == actual entries
2. Spot check: pick 3 entries, verify tags appear in byTag
3. Confidence check: high + medium + low == total

On failure: re-run rebuild.

### 5. Report

```
Patterns: X new, Y updated, Z access-tracked. Failure outcomes: N prevented, M missed.
```

---

## Part 3b: Knowledge Consolidation

### 1. Direct-Write (Primary Path)

Write items routed from taxonomy sweep to knowledge. The sweep (Phase A) is the extraction; this step is the write.

**4-LAYER CAPTURE RELIABILITY (run before writing, run again before marking 3b complete):**
- **Layer 1**: Check `_capture_candidates` from session. If tagged knowledge candidates exist, process them.
- **Layer 2**: If about to write "none" or "no new" → STOP. That phrase is the trigger. Proceed to Layer 3.
- **Layer 3**: Run Taxonomy Sweep (10-category check per Capture Taxonomy section). Route knowledge-bound items to this step.
- **Layer 4**: If genuinely zero after Layers 1-3, write explicit justification citing existing entry IDs or session facts. "Nothing new" without citation is not valid.

**For each sweep item routed to knowledge:**
1. Run Quality Gates (see below)
2. Dedup check against existing entries in knowledge.json
3. If passes: write new entry per Knowledge Entry Schema

**In the same write operation, also:**
- Update `lastAccessed` and increment `accessCount` for knowledge entries retrieved this session
- Check distillation level transitions: if any retrieved entry crossed an accessCount threshold (3, 7, 15) this session, flag as "refinement candidate" in taxonomy sweep output.
1. Read all entries
2. Build fresh: byCategory, byTag, bySource, byConfidence arrays
3. Build fresh: summaries (first 150 chars of content)
4. Preserve: recentIds (prepend new IDs, slice to 20)
5. Set stats.totalEntries = actual entry count
6. Write complete index

### 4. Report

```
Knowledge: X new, Y access-tracked.
```

Part 3b references shared Quality Gates and Index Rebuild approach. Not duplicated.

---

## Part 3c: Reasoning Consolidation

Part 3c has three phases executed in order: RECORD, SYNTH, CROSS.

### 3c-RECORD: Capture Stated Reasoning

Review session for derived conclusions, connections, and extrapolations that were explicitly articulated during the session.

**4-LAYER CAPTURE RELIABILITY (run before writing, run again before marking 3c-RECORD complete):**
- **Layer 1**: Check `_capture_candidates` from session. If tagged reasoning candidates exist, process them.
- **Layer 2**: If about to write "none" or "no new" → STOP. That phrase is the trigger. Proceed to Layer 3.
- **Layer 3**: Run Taxonomy Sweep (10-category check per Capture Taxonomy section). Route reasoning-bound items to this step.
- **Layer 4**: If genuinely zero after Layers 1-3, write explicit justification citing existing entry IDs or session facts. "Nothing new" without citation is not valid.

**For each sweep item routed to reasoning:**
1. Run Quality Gates (see below, plus reasoning-specific gates)
2. Dedup check: scan existing entries by reuse_signal similarity (not content)
3. If passes: write new entry to reasoning.json per Reasoning Entry Schema

### Reasoning-specific quality gates (in addition to shared gates):
- Is this reusable beyond this session? (If no, skip)
- Is this distinct from existing knowledge? (If fact, move to knowledge)
- Does the reuse_signal describe a recognizable future scenario, not a specific incident?
- Does the intent describe a user motivation, not a task description?
- Distinguishing test: retrieved by problem shape or user intent? → reasoning. Retrieved by topic? → knowledge.

**In the same write operation, also:**
- Update `lastAccessed` and increment `accessCount` for reasoning entries retrieved this session
- Check distillation level transitions: if any retrieved entry crossed an accessCount threshold (3, 7, 15) this session, flag as "refinement candidate" in taxonomy sweep output.
- **Validation-on-retrieval processing**: For entries noted as misleading during session: confidence -= 0.05. For entries noted as helpful: confidence += 0.05 (cap at 0.95). "Misleading" means the entry was wrong or led to a worse approach. Irrelevant or redundant retrievals are NOT misleading.

### 3c-SYNTH: Synthesize New Reasoning

**4-layer capture does NOT apply to SYNTH.** 0 survivors is valid when the pipeline visibly ran.

**SYNTH ZERO-CHECK**: If about to write "0 survivors", STOP. That phrase is the trigger. Name each prompt you ran (P7, P1, P5 if conditional met), state what each surfaced (even if "nothing"). Then write 0 with prompt outputs as justification. Missing outputs = incomplete step.

**Generate** (2 fixed prompts + 1 conditional):

Re-read the session log, then run these prompts against it:

- **P7**: "What would I tell the next session that the session log doesn't capture?"
- **P1**: "What two things from this session are related that nobody connected?"
- **P5** (conditional, only when session had an expected outcome: a spec being implemented, a design being tested, or an explicit goal stated by the user): "What's the delta between expected and actual, and what does that delta teach?"

Each prompt produces 0-1 candidates.

**Sharpen** (each candidate, P6 interrogation):

For each candidate, ask:
1. "So what? Why does this matter beyond this session?"
2. "Prove it. Cite specific tool calls, file changes, or user statements from this session."
3. "What would disprove this?"

Revise the candidate based on answers. If it collapses under interrogation, it was empty.

**Filter** (each sharpened candidate, P8 three-check gate):

1. **Behavioral**: "Does this change how I'd approach a future situation?" No → discard.
2. **Specificity**: "What specifically would I do differently, and in what situation?" Vague → discard.
3. **Alternative**: "What other explanation fits these observations?" Equally plausible AND behavioral insight is identical → discard. Equally plausible BUT behavioral insight differs → weaken (keep the behavioral insight, remove the causal claim). The goal is to preserve actionable guidance even when the underlying explanation is contested.

**Store** survivors to reasoning.json with `"provenance": "synthesized"`. Same schema, same quality gates, same dedup check as 3c-RECORD.

**Targets**: 0-3 entries per save. More than 3 suggests insufficient gating.

**Escape hatch**: If synthesis produces low-quality entries for 3+ consecutive saves, skip 3c-SYNTH and note "SYNTH suspended" in session log until prompts are revised.

### 3c-CROSS: Cross-Session Synthesis

**Trigger**: 3+ sessions since `last_cross_session_synthesis` in memory.json. If not triggered, skip entirely.

**Cold start**: On first implementation, initialize `last_cross_session_synthesis` to current session ID. First trigger fires 3 sessions later.

**Input**: Load 2-3 most recent session logs since last cross-session synthesis (~100-150 lines). If a session log is missing or archived, skip it. If fewer than 2 logs available, skip cross-session for this trigger.

**Generate**: "What pattern connects these sessions that neither session states?"

**Sharpen + Filter**: Same P6 interrogation and P8 gate as SYNTH.

**Store** survivors to reasoning.json with `"provenance": "cross_session"`. Same schema, same quality gates.

**After store**: Update `last_cross_session_synthesis` in memory.json to current session ID.

**Targets**: 0-1 entries per trigger.

**False pattern review**: Manually review first 3 cross-session entries for false pattern risk.

### Rebuild Index

**Rebuild reasoning-index.json from reasoning.json** (not incremental):
1. Read all entries from reasoning.json
2. Build fresh: byType, byTag, byConfidence arrays
3. Build fresh: byProvenance (group entries by `.get('provenance', 'stated')` into `stated`, `synthesized`, `cross_session`)
4. Build fresh: summaries (reuse_signal text, not content)
5. Build fresh: intents (intent text)
6. Preserve: recentIds (prepend new/updated IDs, slice to 20)
7. Set stats.totalEntries = actual entry count
8. Write complete index

### 2b. Update Cross-References

**Update cross-references.json incrementally** (not full rebuild):

**ID Filtering Rule**: Include source IDs that do NOT start with `session-`. Pattern IDs follow formats like `fail_143`, `approach_025`, `tech_001`. Knowledge IDs follow `know-105`. Session IDs follow `session-YYYY-MM-DD-NNN`.

```
For each NEW reasoning entry added this session:
  1. Read its derived_from array
  2. Filter to pattern and knowledge IDs only (skip session- prefixed IDs)
  3. For each qualifying source ID:
     a. If source ID exists in cross-references.json → append reasoning ID to referenced_by (if not already present)
     b. If source ID doesn't exist → create new entry with referenced_by: [reasoning_id], related_to: []
  4. Preserve existing `related_to` links on all entries (never overwrite during incremental update)
  5. Update stats (total_sources, total_references)

For each EXISTING reasoning entry whose derived_from was MODIFIED this session:
  1. Re-read its derived_from array
  2. Filter to pattern and knowledge IDs only
  3. Diff against current cross-references for this reasoning ID
  4. Add new references, remove stale ones
  5. Update stats

Update _meta.last_updated
```

**Full rebuild** (read all reasoning.json entries, rebuild from scratch) is the recovery path only. Use when cross-references.json is missing or corrupted.

### 3. Report

```
Reasoning: X new, Y access-tracked.
```

Target: 2-5 entries per session maximum. Not all sessions produce reasoning.

### Content Length by Type

| Type | Target | Fallback |
|------|--------|----------|
| Deduction | 50-700 chars | `_needs_trim: true` |
| Induction | 50-700 chars | `_needs_trim: true` |
| Analogy | 50-700 chars | `_needs_trim: true` |
| Causal | 50-700 chars | `_needs_trim: true` |
| Meta-process | 50-700 chars | `_needs_trim: true` |
| Insight | 50-700 chars | `_needs_trim: true` |
| Architectural Decision | 50-700 chars | `_needs_trim: true` |
| Failure Analysis | 50-700 chars | `_needs_trim: true` |

### Deduplication

1. Scan existing entries by reuse_signal similarity (not content)
2. Exact reuse_signal match → skip, update access fields on existing
3. >80% word overlap on reuse_signal → review. Keep both only if meaningfully different conclusion or intent. If merging, execute Removal Cascade (Part 7b) on the removed entry.
4. Same intent + overlapping tags but different reuse_signal → keep both (different problem shapes)

---

## Part 3d: Save-Time Discovery Capture

**When**: After Parts 3a-3c complete, before vectorstore sync.
**Trigger**: Steps 3a-3c generated insights during execution (duplicates found, schema drift corrected, index integrity gaps, stale references cleaned, merge decisions made).
**Skip if**: Save operations were clean (no discoveries, no corrections, no integrity issues).
**Max 3 entries per save** (prevents save bloat).
**Route to**: knowledge.json (factual: "this drift pattern happens when X") or patterns.json (behavioral: "this failure mode recurs"). Reasoning unlikely from maintenance work.
**Quality gate**: Only genuinely novel discoveries. "Updated an index" is not a discovery. "Found that schema X drifts because of Y" is.
**Dedup**: Check existing entries before writing. If the insight already exists, update confidence/lastAccessed instead of creating a new entry.
**Update indexes** for any new entries created.

---

## Step 8: Vectorstore Sync

**When**: After prune check (step 7), before git commit (step 9). This is the last write-dependent step.
**Condition**: Only if `Nate's-kb/vectorstore/config.json` exists.
**Behavior**: Try `python3 Nate's-kb/vectorstore/kb_sync.py`, fall back to `python Nate's-kb/vectorstore/kb_sync.py`. Runs ONCE after ALL writes (intelligence 3a-3d + memory 5a + any pruning) to catch everything in a single pass. Log result (added/updated/removed/unchanged counts).
**On failure**: Warn, never block save. Save completes without vectorstore sync.
**On missing vectorstore**: Skip silently (vectorstore is optional).

---

## Quality Gates

**Run before every new entry write (patterns and knowledge).**

### Content Length

| Type | Target | Action if Over |
|------|--------|----------------|
| Pattern (preference/approach) | 10-400 chars | Condense, or write with `_needs_trim: true` |
| Pattern (failure) | 10-400 chars | Condense, or write with `_needs_trim: true` |
| Knowledge | 20-600 chars | Condense, or write with `_needs_trim: true` |

`_needs_trim` entries are trimmed during maintenance only, not during save.

### Failure Pattern Prevention Rule

Every new failure pattern must answer "what to do instead."
- Bad: "Skipped validation step"
- Good: "Skipped validation step. Read current state before modifying."

### Specificity

No vague terms ("good", "better", "quality"). Rewrite with specifics.

### Deduplication

Before adding any new entry:
1. Read field: `entry.content` for comparison
2. Normalize text (lowercase, trim)
3. Exact match → skip, update existing entry's access fields
4. >80% word overlap → skip, log "similar exists"

### Confidence Assignment

Use evidence strength to derive confidence:

| Evidence type | Base confidence |
|--------------|-----------------|
| `explicit_statement` | 0.90 |
| `user_correction` | 0.85 |
| `user_acceptance` | 0.70 |
| `observed_behavior` | 0.55 |
| `single_instance` | 0.40 |

Knowledge entries require confidence ≥ 0.7.

### Tag Quality Gate

Run after tag assignment for every new entry:

1. **Minimum 2 tags** per entry
2. **No overly generic single-word tags** ("code", "work", "thing"). Tags should be specific enough to route queries.
3. **At least one domain-specific tag** (not just category-level like "technical" or "process")
4. **Isolation check**: Does this entry share at least one tag with an existing entry? If zero overlap, flag: "Heads up: this entry shares no tags with existing entries. Isolated entries are harder to find via CSR." This is a flag, not a blocker. Some entries are genuinely unique.

### Synonym-Aware Retrieval

When scanning index tags during retrieval, also consult `Intelligence/synonym-map.json`. If the query keyword matches a synonym map key, expand the search to include all mapped synonyms. The map is bidirectional: if "portable" maps to "flash-drive", a search for "flash-drive" also checks "portable."

Synonym map maintenance: add new entries when CSR misses are detected during sessions. Cap at ~100 entries. Prune during monthly maintenance.

---

## Failure Outcome Tracking

**Execute during Part 3a, after pattern consolidation.**

One retrospective question (re-read session log before answering, look for moments where a failure pattern was retrieved and the approach was changed as a result):
"Did any failure pattern prevent a mistake this session? If yes, which pattern ID?"

- If yes: increment accessCount on that pattern, note in evidence: "Prevented: [date] - [brief context]"
- If no: skip. No tracking needed for non-events.

For missed failures (user corrected a mistake that an existing failure pattern should have caught):
- These are captured naturally via user_correction evidence type when the correction creates or updates a failure pattern.
- No separate tracking mechanism needed.

---

## Capture Taxonomy

**Purpose**: Deterministic 10-category sweep replacing vibes-based extraction. Runs once in Phase A (before Parts 3a-3c). Items route to stores for writing.

### Categories

| # | Category | Definition | Target Store | Check Question |
|---|----------|-----------|-------------|----------------|
| 1 | Decisions | Choices made with reasoning and alternatives rejected | reasoning (`architectural_decision`) or knowledge (`process`) | Did we choose X over Y? |
| 2 | Corrections | Facts corrected by user or evidence | knowledge (fact) + patterns (`failure`, mistake) — always dual | Did the user correct anything? |
| 3 | Discoveries | New facts verified this session | knowledge (category by domain) | What do we know now that we didn't before? |
| 4 | Process | Approaches that worked or failed | patterns (`approach`) or knowledge (`process`) | Did we follow a new method? |
| 5 | Failures | What went wrong and root cause | patterns (`failure`) | Did anything fail? |
| 6 | Preferences | User stated or demonstrated preferences | patterns (`preference`) or memory | Did the user express how they want things done? Did they correct an approach (implicit preference)? Did they choose one option over another? Did they react positively/negatively to output style, format, or approach? |
| 7 | Observations | Meta-insights about tools, systems, behaviors | knowledge (`system`/`tool_behavior`) or reasoning (`insight`) | Did we notice how a system behaves? |
| 8 | Negative Knowledge | Things proven NOT to work | knowledge (original category + tag `negative-knowledge`) | Did we rule anything out? |
| 9 | Dependencies | Relationships between components | knowledge (original category + tag `dependency`) or reasoning | Did we discover A affects B? |
| 10 | Commitments | Promises made to people | memory.json commitments array (write via save step 5c) | Did we promise anything? |

### Routing Rules

1. Capture once, tag for both. Don't duplicate across stores.
2. Higher-value store wins: reasoning > knowledge > patterns > memory.
3. The "figured out" test: derived from evidence → reasoning. Observed → knowledge. Behavioral → patterns.
4. Corrections are always dual: corrected fact → knowledge, mistake → patterns. Both mandatory.
5. Ambiguity scope: only categories 7 and 9 have genuine routing ambiguity. Use "figured out" test.

### Enforcement

Every sweep line requires citation:
- Fired: 1-sentence draft summary identifying item and routing. Detail goes in the entry during write phase.
- None: must cite existing entry ID (`none: covered by know-217`) OR specific session fact (`none: single-task code review, no alternatives considered`).
- `none: no decisions made` is NOT valid. Generic justifications indicate the check was skipped.

### Tag Conventions

| Category | Tag | Purpose |
|----------|-----|---------|
| Negative Knowledge | `negative-knowledge` | Retrieval via Troubleshooting Gate |
| Dependencies | `dependency` | Retrieval via Destructive Action Gate |

Tags are added IN ADDITION to domain-specific tags.

### Counter Update (MANDATORY after sweep)

After the taxonomy sweep completes, update `capture_taxonomy` in memory.json:
- Increment `category_hits` for each category that fired (produced an item, not "none")
- Increment `sessions_tracked` by 1
- Use canonical lowercase keys: `decisions`, `corrections`, `discoveries`, `process`, `failures`, `preferences`, `observations`, `negative_knowledge`, `dependencies`, `commitments`

### Anti-Patterns

- Rubber-stamping "none" on all 10 without citations
- Capturing everything (quality gates still apply, 2-5 per store cap, corrections exempt)
- Duplicating across categories (capture once, tag for both)
- Re-capturing items from previous sessions (sweep checks for NEW items only)

---

## Entry Schemas

### Schema Conformance Gate (run FIRST, before all other quality gates)

Before writing any new entry to patterns.json, knowledge.json, or reasoning.json:

0. **VERIFY NEXT ID (MANDATORY)**: Do NOT trust index nextId alone. Scan the target store for the actual max numeric ID. Use `max(index.nextId, store_max_id + 1)` as the starting ID for new entries. Update index nextId after writing. This prevents ID collisions when multiple instances (CLI + IDE) write to the same store.
1. **CHECK REQUIRED FIELDS**: Verify every required field is present.
   - Missing required field → add it with default value, log warning.
   - Defaults: accessCount=0, lastAccessed=today, created=today, provenance="stated" (reasoning only), derived_from=[] (reasoning only)
2. **CHECK FIELD NAMES**: Verify no legacy field names are used.
   - Legacy name detected → rename to canonical name before write.
   - Map: pattern→content, summary→content, first_observed→created, last_observed→lastAccessed, observation_count→accessCount, access_count→accessCount, last_accessed→lastAccessed, lastOccurred→lastAccessed, lastUpdated→lastAccessed (if no lastAccessed), lastModified→lastAccessed, firstSeen→created, lastSeen→lastAccessed, timestamp→created
3. **CHECK CATEGORY/TYPE**: Verify value is in the documented enum.
   - Unknown category/type → flag for review, write with _needs_review: true.
4. **CHECK CONTENT CONFLICT** (patterns only): If both pattern and content exist, keep the longer value as content, drop the shorter.
5. **CHECK UNKNOWN FIELDS**: If entry has fields not in required or optional lists, log warning. Not a blocker.

### Pattern Entry Schema

```json
{
  "id": "{prefix}_{number}",
  "category": "preference|approach|failure|process|procedure|ai_agent",
  "content": "{the behavior/preference/failure, 10-400 chars}",
  "confidence": 0.XX,
  "tags": ["{2-5 strings}"],
  "context": "{task domain, 5-50 chars}",
  "created": "{YYYY-MM-DD}",
  "lastAccessed": "{YYYY-MM-DD}",
  "accessCount": 0
}
```

**Optional fields**: prevention, outcome, evidence, source, _imported_from, _stale_candidate, _needs_trim, _needs_review, _history

**Category prefixes**: `pref`, `approach`, `fail`, `proc`, `ai_agent`. Legacy prefixes (`comm`, `content`, `dev`, `exec`, `org`, `pres`, `prob`, `tech`, `tool`) exist on old entries — don't rename.

### Knowledge Entry Schema

```json
{
  "id": "know-{number}",
  "category": "technical|process|error_solution|best_practice|tool_quirk|reference|domain_expertise|architecture|research|security|tool_behavior|aws_gotcha|system",
  "content": "{the knowledge, 20-600 chars}",
  "confidence": 0.XX,
  "tags": ["{2-5 strings}"],
  "source": "{provenance — session ID, URL, or enum value}",
  "created": "{YYYY-MM-DD}",
  "lastAccessed": "{YYYY-MM-DD}",
  "accessCount": 0
}
```

**Optional fields**: context, validated, validationNote, sourceUrl, detail, _imported_from, _stale_candidate, _needs_trim, _needs_review, _history

### Reasoning Entry Schema

```json
{
  "id": "reason-{number}",
  "type": "deduction|induction|analogy|causal|meta-process|insight|architectural_decision|failure_analysis",
  "content": "{the derived conclusion, 50-700 chars}",
  "intent": "{why this was figured out, 20-80 chars}",
  "reuse_signal": "{when this applies again, 30-100 chars}",
  "confidence": 0.XX,
  "derived_from": ["{system IDs, session IDs, or file paths}"],
  "provenance": "stated|synthesized|cross_session",
  "tags": ["{2-5 strings}"],
  "created": "{YYYY-MM-DD}",
  "lastAccessed": "{YYYY-MM-DD}",
  "accessCount": 0
}
```

**Optional fields**: _imported_from, _stale_candidate, _needs_trim, _needs_review, _history

**Provenance field**: Absence defaults to `"stated"`. Implementation must use `.get('provenance', 'stated')` pattern.

---

## Failure Modes

| Failure | Recovery |
|---------|----------|
| JSON parse error on read | Log error, skip consolidation, don't corrupt files |
| Write failure | Retry once, then log and continue without update |
| Partial update (crash mid-save) | Next save re-runs full consolidation (idempotent) |
| Index desync | Rebuild catches it (full rebuild is self-correcting) |
| Duplicate detection (cross-session) | Deduplication catches it, updates existing |
| Duplicate detection (same-session) | Content hash check catches it |
