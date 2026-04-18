# Memory Protocol

**Purpose**: Persistent memory system for cross-session recall using file-based storage and behavioral patterns.
**Pattern**: Built on Protocol-as-MCP pattern
**Last Updated**: 2026-04-04

---

## Overview

This protocol enables persistent memory without external dependencies. Uses JSON storage in Memory and behavioral triggers defined here.

**Storage Location**: `Nate's-kb/Memory/memory.json`

**Related Systems**:
- **Intelligence System**: `Nate's-kb/Intelligence/` - patterns, knowledge, and reasoning
- For knowledge retrieval signals, see `Intelligence/intelligence-operations.md` Part 3
- For reasoning retrieval signals, see `Intelligence/intelligence-operations.md` Part 3c

---

## Index Operations (CSR Pattern)

The memory system uses Context Signal Routing for efficient retrieval. Load the lightweight index first, then selectively retrieve relevant memories.

**Index Location**: `Nate's-kb/Memory/memory-index.json`

### Threshold Rule

| memory.json size | INDEX-QUERY | Full Load |
|------------------|-------------|-----------|
| Under 5,000 tokens | Practice (recommended) | Allowed |
| Over 5,000 tokens | **Mandatory** | Not allowed |

**Discipline principle:** Practice INDEX-QUERY even below threshold to build habit. Efficiency allows full load; discipline prefers selective.

### INDEX-QUERY - Retrieve Relevant Memories

**When**: Session start, task context changes, user references past

**Signal-to-Index Mapping**:
| Signal in User Message | Index Query |
|------------------------|-------------|
| Code, build, implement, debug | `byTag["development"]` |
| Email, write, respond, draft | `byTag["communication"]` |
| Process, workflow, approach | `byTag["workflow"]` |
| Test, validate, review | `byTag["quality-control"]` |
| Client, project, account | `byTag["customer-service"]` |
| "Remember when", "last time" | Search `summaries` |
| Route F triggered | `byConfidence["high"]` + `byConfidence["critical"]` |
| Any task | Always include `recentIds` (last 20) |

**How**:
1. Load `memory-index.json` (lightweight, ~400 tokens)
2. Match user signals to index categories
3. Collect memory IDs (max 5, priority: recency > confidence > tag match)
4. Retrieve only those memories from `memory.json`

### INDEX-UPDATE - Sync Index After Memory Changes

**When**: After any STORE, UPDATE, or FORGET operation on a single entry mid-session.

**How**:
1. Update relevant `byTag` arrays
2. Update `byType` array
3. Update `byConfidence` array
4. Update `recentIds` (prepend new ID, slice to 20)
5. Update `summaries` entry
6. Bump `lastUpdated` timestamp
7. Update `stats` counts

### INDEX-REBUILD - Full Index Regeneration

**When**: Save time (recommended), index corrupted, major memory restructuring, version upgrade.

**How**:
1. Read all memories from `memory.json`
2. Build fresh: byTag, byType, byConfidence, summaries, recentIds
3. Set stats counts from actual data
4. Write new `memory-index.json`

**Why rebuild at save time**: Incremental updates drift under context pressure (same issue intelligence system had). Full rebuild is idempotent and self-correcting. At <100 memories, cost is negligible.

### Fallback Behavior

If `memory-index.json` missing or corrupted:
1. Log warning (don't fail)
2. Load full `memory.json` (legacy behavior)
3. Rebuild index when convenient

---

## Memory Operations

### STORE - Save to Memory

**When to store:**
- User states a preference ("I prefer X over Y")
- Key decision made ("We decided to use X")
- Project state changes ("Project X is now in phase Y")
- Correction given ("Actually, it's X not Y")
- Pattern observed (repeated behavior worth noting)

**How to store:**
```json
{
  "id": "mem-NNN",
  "type": "preference|decision|correction|learning|critical_safety|system",
  "content": "The actual memory (10-300 chars)",
  "context": "Why this matters (5-100 chars)",
  "created": "YYYY-MM-DD",
  "lastAccessed": "YYYY-MM-DD",
  "accessCount": 0,
  "confidence": 0.9,
  "tags": ["relevant", "tags"]
}
```

**Confidence values**: numeric 0.0-1.0. Use: 1.0 (critical_safety only), 0.9 (explicitly stated), 0.7 (inferred), 0.5 (uncertain).

### RECALL - Retrieve from Memory

**When to recall:**
- Session start (check recent/relevant memories) - **ALWAYS FIRST**
- User references past ("last time", "remember when", "we discussed")
- Topic matches stored memory tags
- Making a decision that past context would inform

**Priority**: Index first, then selective memory retrieval, session logs last.

**How to recall (Index-First Flow)**:
1. Load `memory-index.json` (if not already loaded)
2. Match user signals to index categories (see INDEX-QUERY)
3. Collect relevant memory IDs (max 5)
4. Retrieve only those memories from `memory.json`
5. Pull session logs only if deeper narrative context needed
6. Surface naturally in response, don't announce "checking memory"

**Fallback**: If index unavailable, load full `memory.json` (legacy behavior)

### SEARCH - Find Specific Memories

**When to search:**
- User asks about past decisions
- Need context for current task
- Verifying a preference before acting

**How to search:**
- By type: "What preferences do I have stored?"
- By tag: "What do I know about Project X?"
- By date: "What did we decide last week?"

### UPDATE - Modify Existing Memory

**When to update:**
- User corrects a stored memory
- Confidence changes based on new info
- Project state evolves
- Preference changes

**How to update:**
- Find existing memory by id or content match
- Update relevant fields
- Bump `lastAccessed` date

### FORGET - Remove from Memory

**When to forget:**
- User explicitly asks ("forget that", "delete that memory")
- Memory becomes obsolete (project completed, preference changed)
- Confidence drops to zero

**How to forget:**
- Remove entry from `memory.json`
- Or mark as `"archived": true` if might be useful later
- **If removing intelligence entries** (patterns, knowledge, reasoning): Execute Removal Cascade (intelligence-operations.md Part 7b)

---

## Memory Schema

### memory.json Sections

| Section | Purpose |
|---------|---------|
| `intelligence_system` | Learning state and session tracking |
| `proactive_behavior` | Offer history and preferences |
| `active_projects` | Project tracking with status, next actions |
| `implementation_triggers` | Feature triggers with thresholds |
| `memories` | Core memories (preferences, decisions, learnings, critical_safety) |
| `pattern_detections` | Session pattern observations pending consolidation |
| `confidence_events` | Prediction accuracy tracking |
| `domain_expertise` | User expertise levels by domain (expert/proficient/intermediate/learning) |
| `anti_preferences` | Explicit things to avoid - softer than critical_safety |
| `session_metadata` | Current session stats |

### Memory Entry Schema

```json
{
  "version": "4.0",
  "lastUpdated": "2026-04-04",
  "memories": {
    "mem-001": {
      "id": "mem-001",
      "type": "preference",
      "content": "Prefers TypeScript over JavaScript",
      "context": "Stated during dev discussion",
      "created": "2025-12-12",
      "lastAccessed": "2026-04-04",
      "accessCount": 3,
      "confidence": 0.9,
      "tags": ["development", "language", "typescript"]
    }
  }
}
```

Note: `memories` is a dict keyed by ID, not an array. All CSR lookup paths assume dict access.

### Memory Types

| Type | Description | Example |
|------|-------------|---------|
| `preference` | User likes/dislikes | "Prefers direct communication" |
| `decision` | Choice made | "Decided to use S3 for storage" |
| `correction` | Fixed misunderstanding | "Customer name is X not Y" |
| `learning` | Discovered fact or technique | "API rate limits reset at midnight UTC" |
| `critical_safety` | Must-not-violate rules | "NEVER modify intelligence files without reading first" |
| `system` | System configuration or state | "KB vectorstore uses titan-embed-text-v2" |

### Confidence Levels

| Value | Meaning | When to Use |
|-------|---------|-------------|
| 1.0 | Critical, must-not-violate | `critical_safety` type only |
| 0.9 | Explicitly stated, recently confirmed | Direct user statement |
| 0.7 | Inferred or moderately certain | Observed pattern, not explicitly stated |
| 0.5 | Uncertain or very old | Needs validation |

**Decay**: Entries with `accessCount == 0` and `created > 180 days` decay by 0.05/month (floor: 0.7). Applied during monthly maintenance.

### Session Index Schema

```json
{
  "id": "session-YYYY-MM-DD-NNN",
  "date": "YYYY-MM-DD",
  "tags": ["topic-1", "topic-2"],
  "summary": "What happened this session (20-500 chars)",
  "outcome": "success|partial|blocked",
  "outcome_note": "Brief explanation (10-150 chars)"
}
```

Optional fields: `key_decisions`, `files_modified`, `memories_recalled` (memory IDs retrieved during session).

---

## Behavioral Triggers

### Session Start
1. Read `memory.json`
2. Check for memories accessed in last 7 days
3. Note any relevant to likely tasks (based on day/time patterns)
4. Hold in context, surface when relevant

### During Session
- **User states preference** → STORE as preference
- **Decision made** → STORE as decision
- **"Remember that..."** → STORE with high confidence
- **"Last time we..."** → RECALL and respond
- **"Forget about..."** → FORGET specified memory
- **Correction given** → UPDATE or STORE as correction

### Session End (save)
- Review session for storable memories
- Update `lastAccessed` for any recalled memories
- Add new memories identified during session
- **Update `last_session_snapshot`** with current state (see below)

### Snapshot Update (Part of Save)
On every save, update `last_session_snapshot` in memory.json:
```json
"last_session_snapshot": {
    "session_id": "<current-session-id>",
    "memory_version": "<memory.json version>",
    "patterns_count": <count from patterns-index.json>,
    "knowledge_count": <count from knowledge-index.json>,
    "active_projects": <count of status=active in active_projects>,
    "timestamp": "<save timestamp>"
}
```
This enables session diff on next start.

---

## Integration Points

### With Nathaniel.md
Add to Session Protocols:
- Check memory.json on session start
- Surface relevant memories naturally

### With patterns.json
- patterns.json = aggregated learnings (general)
- memory.json = specific facts and decisions (granular)
- They complement, not duplicate

### Pattern Consolidation

**When**: During save command, Part 3 (Consolidate patterns)

**Spec**: See `Intelligence/learning-loop.md` for the consolidation algorithm.

**Process**:
1. Review `pattern_detections` in memory.json
2. Check patterns.json for similar existing patterns
3. Update existing or add new based on evidence
4. Mark detections as consolidated

### With Session Logs
- Session logs = full narrative history
- memory.json = extracted, searchable facts
- save command updates both

---

## Anti-Patterns

- ❌ Announcing "checking memory" (just do it)
- ❌ Storing everything (be selective)
- ❌ Forgetting without confirmation for high-confidence items
- ❌ Letting memory.json grow unbounded (archive old items)
- ❌ Duplicating what's in patterns.json

---

## Validation

### Conformance Gate (Write-Time)

Before writing any new memory entry to memory.json:

1. **CHECK REQUIRED FIELDS**: id, type, content, context, confidence, tags, created, lastAccessed, accessCount.
   - Missing required field → add with default (accessCount=0, lastAccessed=today, created=today)
2. **CHECK CONFIDENCE**: Must be numeric 0.0-1.0.
   - String detected → convert: critical=1.0, high=0.9, medium=0.7, low=0.5
3. **CHECK TYPE**: Must be in enum: preference, decision, correction, learning, critical_safety, system.
   - Unknown type → flag `_needs_review: true`
4. **CHECK ID**: Must match dict key. Must follow `mem-NNN` format.

Before writing any new session-index entry:

1. **CHECK REQUIRED FIELDS**: id, date, tags, summary, outcome, outcome_note.
2. **CHECK ID FORMAT**: Must match `session-YYYY-MM-DD-NNN`.
3. **CHECK OUTCOME**: Must be success, partial, or blocked.
4. **NO DEPRECATED FIELDS**: focus, topics, duration_minutes, file.

### On STORE
- Verify required fields present: id, type, content, confidence, tags
- Check for duplicate content before creating new memory
- Validate memory.json structure after write

### On RECALL
- If memory.json fails to parse, flag error and proceed without memory
- Log missing required fields on any memory encountered

### On Session Start
- Verify memory.json parses as valid JSON
- Check version field exists
- Flag memories with missing required fields (don't fail, just note)

### Trigger Examples

For clarity, these phrases indicate specific operations:

| Trigger Phrase | Operation |
|----------------|-----------|
| "I prefer...", "I like...", "Always use...", "Never use..." | STORE preference |
| "Let's go with...", "We decided...", "The plan is..." | STORE decision |
| "Remember that...", "Don't forget..." | STORE with high confidence |
| "Last time we...", "Remember when...", "What did we decide about..." | RECALL |
| "Forget about...", "Delete that...", "Never mind that..." | FORGET |
| "Actually it's...", "I was wrong about...", "Correction:..." | UPDATE or STORE correction |

---

## Pruning Operations

Pruning prevents unbounded growth while preserving valuable context. Content is archived; metadata is destroyed.

### Retention Rules

| Data | Retention | Min Keep | Action |
|------|-----------|----------|--------|
| Session index entries | 60 days | 10 | Destroy |
| Session log files | 30 days | 10 | Archive to Memory/archive/ |
| Pattern detections (consolidated=true) | 30 days | 5 | Destroy |
| Confidence events | 30 days | 5 | Destroy |
| Offer history | 60 days | 10 | Destroy |
| Completed projects | 14 days post-completion | 0 | Archive to projects_archive in memory.json |
| Resolved commitments | 30 days post-resolution | 0 | Destroy |
| Cancelled commitments | 14 days post-cancellation | 0 | Destroy |
| Open commitments | Never auto-prune | N/A | User resolves or cancels |

**Principle:** Archive *content* (logs, projects). Destroy *metadata* (index entries, events, detections).

### PRUNE-CHECK

**When**: Save command Part 7

**How**:
1. Count items in each data store
2. Check oldest item age against retention
3. If (count > min_keep) AND (oldest > retention) → flag for pruning
4. Return list of stores needing pruning
5. If none flagged → skip PRUNE-EXECUTE

### PRUNE-EXECUTE

**When**: PRUNE-CHECK returns non-empty list

**How**:
1. **Session logs**: Move files older than 30 days to `Memory/archive/`, remove corresponding entries from session-index.json
2. **Completed projects**: Move to `projects_archive` array in memory.json
3. **Pattern detections**: Delete entries where `consolidated=true` AND older than 30 days
4. **Confidence events**: Delete entries older than 30 days (keep min 5 most recent)
5. **Offer history**: Delete entries older than 60 days (keep min 10 most recent)
6. Update `stats` and `lastUpdated` in affected files
7. Note pruning action in session log

### PRUNE-MANUAL

**Trigger**: "prune", "cleanup", "archive old sessions"

**How**: Run PRUNE-CHECK with min_keep set to 0 (force full evaluation against retention only)

**For full ecosystem maintenance** (beyond memory pruning): See `maintenance-protocol.md` for integrity checks, growth management, orphan detection, and coordinated cleanup across all data stores.

---

## Maintenance

### Monthly Review
- Archive memories older than 90 days with no access
- Consolidate similar memories
- Update confidence based on access patterns
- Confidence decay: entries with `accessCount == 0` and `created > 180 days`, reduce confidence by 0.05 (floor: 0.7), flag as `_stale_candidate`

### Size Limits
- Active memories: ~100 max
- Archive when exceeds
- Keep memory.json under 2,000 lines

---

## Recovery

**memory.json corrupted** (parse error):
1. Check for syntax errors (missing commas, brackets)
2. Restore from git history if available
3. Manually reconstruct from recent session logs
4. Re-validate after repair

**Memory not being recalled**:
1. Verify memory exists in memory.json
2. Check tags match expected triggers
3. Confirm confidence level isn't below 0.5
4. Check lastAccessed - may have been archived

**Duplicate memories created**:
1. Search memory.json for similar content
2. Merge duplicates, keep higher confidence
3. Update validation to catch future duplicates

**AI not following protocol**:
1. Re-read memory-protocol.md at session start
2. Explicitly reference protocol when storing/recalling
3. Add validation checks to catch drift

**Data loss prevention**:
- memory.json is git-tracked - commit regularly
- /save command checkpoints state
- Session logs provide reconstruction path

---

*Memory is persistence. Persistence is continuity. Continuity is trust.*

*The Retention & Pruning pattern was developed for the Nathaniel Protocol knowledge base and is documented for community adaptation.*
