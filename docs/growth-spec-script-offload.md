# Growth Spec: Script-Offloaded Operations

**Created**: 2026-04-16
**Origin**: Transit test revealed IDE save burning 23.53 credits / 12m15s on mechanical JSON operations. save-session.py reduced this to ~3-5 credits. Pattern applies broadly.

---

## Principle

**Nate does the thinking. Scripts do the JSON plumbing.**

Every time Nate reads a large JSON file to make a mechanical edit (insert entry, update counter, find-replace across stores), that's tokens spent on work Python handles in milliseconds. The LLM context window is for reasoning, not parsing.

This is a separation of concerns applied to cognitive architecture: the LLM reasons about what to capture, scripts execute the mechanical storage operations. Every context engineering pattern in the system (TOC, CSR, HRF, CIS, SRG) and every autonomous system (Pulse, Golden Ethos) depends on stores being accurate and indexes being in sync. Scripts guarantee that mechanically.

---

## Ecosystem Context

### Store Schemas (from validate-schemas.py)

**patterns.json entries:**
- Required: `id` (str), `category` (str), `content` (str), `confidence` (float), `created` (str), `tags` (list), `lastAccessed` (str), `accessCount` (int)
- Optional: `prevention`, `outcome`, `evidence`, `source`, `context`
- Categories: `preference`, `approach`, `failure`, `process`, `procedure`, `ai_agent`
- Content limit: 400 chars

**knowledge.json entries:**
- Required: `id` (str), `category` (str), `content` (str), `confidence` (float), `created` (str), `tags` (list), `lastAccessed` (str), `accessCount` (int)
- Optional: `context`, `source`, `validated`, `validationNote`, `sourceUrl`
- Categories: `technical`, `process`, `error_solution`, `best_practice`, `tool_quirk`, `reference`, `domain_expertise`, `architecture`, `research`, `security`, `system`
- Content limit: 600 chars

**reasoning.json entries:**
- Required: `id` (str), `type` (str), `content` (str), `intent` (str), `reuse_signal` (str), `confidence` (float), `tags` (list), `created` (str), `lastAccessed` (str), `accessCount` (int), `provenance` (str), `derived_from` (list)
- Types: `deduction`, `induction`, `analogy`, `causal`, `meta-process`, `insight`, `architectural_decision`, `failure_analysis`
- Provenances: `stated`, `synthesized`, `cross_session`
- Content limit: 700 chars

**cross-references.json:**
- Keyed by entry ID (e.g., `"know-031"`)
- Value: `{"referenced_by": ["reason-001", "reason-002"]}`

**memory.json top-level keys:**
- `version`, `lastUpdated`, `entities` (list), `domain_expertise` (dict), `anti_preferences` (dict), `active_projects` (list), `commitments` (list), `proactive_behavior`, `last_session_snapshot`, `memories` (list), `intelligence_system`, `pattern_detections`, `confidence_events`, `session_metadata`, `implementation_triggers`
- `user_address`, `name`, `location`, `occupation` are top-level keys (NOT nested under entities)

**session-index.json entries:**
- Fields: `id`, `date`, `tags`, `summary`, `outcome`, `outcome_note`

**memory-index.json:**
- Top keys: `_meta`, `stats` (totalEntries, activeEntries, stale_candidates, nextId), `byTag`, `byType`, `byConfidence` (critical/high/medium/low), `summaries`, `recentIds`
- Entry IDs: `mem-{N}` (e.g., `mem-001`, `mem-067`)
- Types (from memory.json): `preference`, `decision`, `correction`, `learning`, `critical_safety`, `system`

**Index files** (patterns-index, knowledge-index, reasoning-index):
- All contain: `stats` (totalEntries, activeEntries, nextId), `byTag`, `summaries`, `recentIds`
- patterns-index adds: `byCategory`, `byConfidence` (high/medium/low)
- knowledge-index adds: `byCategory`
- reasoning-index adds: `byType`, `byConfidence`, `byProvenance`, `intents`

### ID Format and nextId Workflow

**ID formats by store:**
- Knowledge: `know-{N}` where N is sequential integer (e.g., `know-401`)
- Reasoning: `reason-{N}` where N is sequential integer (e.g., `reason-112`)
- Patterns: `{category}_{N}` where category is the enum value (e.g., `fail_129`, `approach_062`, `pref_164`)

**nextId in index stats:**
- Knowledge/Reasoning: single integer (e.g., `"nextId": 401` means next entry is `know-401`)
- Patterns: dict keyed by category (e.g., `"nextId": {"fail": 129, "approach": 62}`)

**Workflow (Nate → script):**
1. Nate reads nextId from the relevant index (or the script reads it internally)
2. Nate assigns IDs to new entries in the ops file using nextId values
3. Script validates no ID collision with existing entries
4. Script writes entries, then rebuilds index with updated nextId (max existing + 1)

**Scripts must NOT trust the ops file's IDs blindly.** Collision check is mandatory: if `know-401` already exists in the store, reject the write. The full index rebuild recalculates nextId from actual max ID in the store, so even if the index was stale, the rebuilt nextId is correct.

**Two ID assignment paths exist:**
- **Script path** (save-session.py, cascade-correction, removal-cascade): Script can auto-assign IDs internally by reading nextId from the store. Nate may provide IDs in the ops file, or omit them and let the script assign. Script always validates regardless.
- **Inline path** (INLINE ENTRY INTEGRITY rule, onboarding captures): Nate writes directly to stores mid-session, bypassing scripts. Nate MUST read nextId from the index before assigning. After writing, Nate MUST update the index stats immediately (per kernel rule).

### Ops File Schema (save-session.py input)

```json
{
  "session_id": "session-YYYY-MM-DD-NNN",
  "schema_version": 1,
  "new_entries": {
    "patterns": [{ ...entry per schema above... }],
    "knowledge": [{ ...entry per schema above... }],
    "reasoning": [{ ...entry per schema above... }]
  },
  "access_updates": {
    "patterns": ["pref_042"],
    "knowledge": ["know-200"],
    "reasoning": ["reason-050"]
  },
  "memory_updates": {
    "user_address": "Name",
    "domain_expertise": {"ai_ml": "expert"}
  },
  "active_project_updates": [
    {"name": "ProjectX", "status": "active", "last_touched": "2026-04-16"}
  ],
  "snapshot": { "session_id": "session-2026-04-16-001" },
  "vectorstore_sync": true,
  "cross_session_synthesis_done": false
}
```

All fields optional except `session_id` and `schema_version`. Omitted sections are skipped.

**Nate's responsibility when writing the ops file:**
1. Read nextId from the relevant index BEFORE assigning IDs (do not guess or recall)
2. Use exact field names from the store schemas above (not synonyms, not camelCase variants)
3. Use only enum values listed above for category/type/provenance (script rejects others)
4. Include `created`, `lastAccessed` (today's date as YYYY-MM-DD), and `accessCount: 1` on all new entries
5. Include `tags` as a list of strings (not comma-separated, not a single string)
6. Include `derived_from` as a list of entry IDs on reasoning entries (empty list `[]` if none)
7. Include `provenance` on reasoning entries: `"stated"` for direct captures, `"synthesized"` for SYNTH phase, `"cross_session"` for cross-session synthesis
8. `confidence` is a float between 0.0 and 1.0 (not a percentage, not an integer)
9. Session ID format: `session-YYYY-MM-DD-NNN` where NNN is zero-padded sequence (e.g., `session-2026-04-16-001`)
10. Date format everywhere: `YYYY-MM-DD` (ISO 8601 date only, no time component in store entries)

---

## Completed

### save-session.py
- **Problem**: Save protocol required 40+ tool calls to mutate 3 stores + 3 indexes + memory + cross-refs
- **Solution**: Nate writes `_save_ops.json`, script handles all mutations atomically with full index rebuilds
- **Impact**: ~23 credits to ~3-5 credits per save. Zero index drift.
- **Gap analysis** (must be hardened before building new scripts):
  - ✅ Atomic writes (os.replace via tmp file)
  - ✅ Basic try/except on JSON load/write
  - ❌ No input validation (schema check on ops file before mutations)
  - ❌ No dry-run mode
  - ❌ No exit code differentiation (1 = partial, 2 = total failure)
  - ❌ No ID collision detection
  - ❌ No file locking for concurrent access
  - ❌ No test suite

---

## Planned Scripts

### 1. cascade-correction.py
**Priority**: High
**Trigger**: Correction Cascade Gate (user corrects a fact)
**Problem**: Nate greps all 3 stores + indexes + cross-refs for stale claim. On 600+ knowledge entries, that's multiple large file reads just to find matches.
**Solution**: Script takes keywords and new value, scans all stores, returns matches with entry IDs and context. Nate reviews matches, approves, script applies fixes + rebuilds indexes.
**Input schema:**
```json
{
  "schema_version": 1,
  "old_keywords": ["python3", "venv"],
  "new_value": "python (not python3) with system venv",
  "stores": ["knowledge", "patterns", "reasoning"],
  "mode": "scan|apply",
  "approved_ids": ["know-229", "know-314"]
}
```
- `old_keywords` (required): list of strings to search for in content/source/context/tags fields
- `new_value` (required for apply mode): literal replacement text. Script performs find-replace of each old_keyword with new_value in matched fields. For complex rewrites, Nate edits the ops file per-match before calling apply mode.
- `stores` (optional, default all three): which stores to scan
- `mode` (required): `"scan"` returns matches for review, `"apply"` executes approved fixes
- `approved_ids` (required for apply mode): list of entry IDs Nate approved after scan
- `limit` (optional, default 10): max matches returned in scan mode. Total count always reported.

**Output (scan mode):** `{"matches": [{"id": "know-229", "store": "knowledge", "field": "content", "snippet": "...context around match...", "proposed_fix": "..."}], "count": 5, "total": 50, "EXIT": 0}`
**Output (apply mode):** `{"applied": 3, "skipped": 0, "indexes_rebuilt": ["knowledge", "reasoning"], "succeeded": ["knowledge"], "failed": [], "EXIT": 0}`

**Workflow**:
1. Nate writes input JSON with `mode: "scan"` and keywords from the stale claim
2. Script scans all specified stores for content/source/context/tags fields containing ANY keyword
3. Script returns matches with surrounding context (not full entries) for Nate to review
4. Nate reviews matches, writes second input JSON with `mode: "apply"` and `approved_ids`
5. Script applies approved fixes, rebuilds all affected indexes, updates cross-references
6. Script prints `EXIT:0` on success
**Token savings**: Eliminates 3-6 large file reads per correction cascade.

### 2. removal-cascade.py
**Priority**: High
**Trigger**: Removal Cascade Gate (delete/merge/dedup entries)
**Problem**: Removing an entry requires: delete from store, remove from ALL index sections (byTag, byCategory, byConfidence, summaries, recentIds), remove from cross-references (keyed by entry ID, plus referenced_by arrays), scan reasoning derived_from arrays, update stats. Manual execution is error-prone.
**Solution**: Script takes list of entry IDs to remove, handles full cascade atomically, rebuilds indexes.
**Input schema:**
```json
{
  "schema_version": 1,
  "remove": ["know-314"],
  "merge_tags_to": "know-206"
}
```
- `remove` (required): list of entry IDs to delete. Can span multiple stores (script detects store from ID prefix).
- `merge_tags_to` (optional): entry ID that receives tags from removed entries before deletion. **Must NOT be in the remove list.** Script rejects if target is being removed.

**Output:** `{"removed": 1, "tags_merged_to": "know-206", "index_refs_cleaned": 14, "cross_refs_cleaned": 3, "derived_from_cleaned": 0, "EXIT": 0}`
**Workflow**:
1. Nate writes input JSON with entry IDs to remove
2. If `merge_tags_to` is set: script copies tags from removed entries to the target entry before deletion
3. Script deletes entries from their stores
4. Script removes IDs from ALL index sections: byTag, byCategory, byConfidence, byType, byProvenance, summaries, recentIds, intents
5. Script removes IDs from cross-references.json (both as top-level keys AND from referenced_by arrays)
6. Script scans reasoning.json derived_from arrays and removes deleted IDs from them. Logs which reasoning entries were affected for Nate to review provenance chain integrity.
7. Script rebuilds all affected indexes (full rebuild)
8. Script prints summary of what was cleaned and `EXIT:0`
**Edge cases**:
- Removing an ID that doesn't exist: warn, skip, continue (not an error)
- merge_tags_to target doesn't exist: error, abort, `EXIT:2`
- Removing all entries from a store: valid, results in empty store with valid schema
**Token savings**: Eliminates the most error-prone manual operation in the system.

### 3. session-cache.py
**Priority**: Medium
**Trigger**: Session Start Gate
**Problem**: 5 index files loaded every session = 5 file reads. Indexes don't change mid-session (only at save time). Re-reading them after context compaction wastes tokens on identical content.
**Approach**: SQLite routing cache. NOT summarization. Indexes loaded once into tables, queried by tag/category/confidence. Same CSR pattern, faster I/O.
**Key constraint**: Nate must be able to reach any entry. The cache optimizes the routing step (tag → ID mapping), not the content retrieval step.

**SQLite tables:**

| Table | Source | Columns |
|-------|--------|---------|
| knowledge | knowledge-index.json | id, summary, tags (comma-sep), category, confidence |
| patterns | patterns-index.json | id, summary, tags, category, confidence |
| reasoning | reasoning-index.json | id, summary, tags, type, confidence, provenance, intent, reuse_signal |
| memory | memory-index.json | id, tags, type |
| sessions | session-index.json | id, date, tags, summary, outcome, outcome_note |

**Location**: `Nate's-kb/cache/session-cache.db` (derived artifact, never committed to git)
**Sentinel**: `Nate's-kb/cache/.invalidated` (touched by inline writes, checked before queries)
**Lifecycle**: Build on session start (reads from store JSON files, not indexes — indexes may be stale after inline writes) → query mid-session → invalidate on save → rebuild next query
**Query interface** (how Nate interacts with the cache):

Nate queries the cache via execute_bash with shell-escaped JSON arg. The script accepts a query JSON and returns matching IDs:
```bash
python3 scripts/session-cache.py query '{"store": "knowledge", "tags": ["save-protocol"], "category": "process"}'
# Returns: [{"id": "know-398", "summary": "save-session.py usage..."}, ...]

python3 scripts/session-cache.py query '{"store": "reasoning", "confidence_min": 0.8, "type": "architectural_decision"}'
# Returns: [{"id": "reason-175", "summary": "Full rebuild over incremental..."}, ...]
```

**Query parameters** (all optional, combined with AND):
- `store` (required): `"knowledge"`, `"patterns"`, `"reasoning"`, `"memory"`, `"sessions"`
- `tags`: list of strings, matches entries containing ANY tag (OR within tags)
- `category` / `type`: exact match against enum value
- `confidence_min`: float, entries >= this value
- `provenance`: exact match (`"stated"`, `"synthesized"`, `"cross_session"`)
- `intent_contains`: substring match against reasoning intent field
- `limit`: max results (default 20)

Internally the script translates these to SQL against the SQLite cache. Nate never writes SQL directly.
**What the cache does NOT store**: full entry content, source fields, cross-references. Those stay in JSON files.
**Research validation**: SQLite is the industry consensus for local AI agent structured caching (sparkco.ai evaluation, memweave project, Oracle developer blog — all independently converged on SQLite for zero-dependency, single-file, sub-ms query, ACID-compliant local caching).

### 4. maintenance.py
**Priority**: Medium
**Trigger**: `maintenance` keyword or monthly cadence
**Problem**: Health checks require reading all stores to check integrity, find stale entries, detect duplicates, verify tag coverage.
**Solution**: Script runs health checks AND applies safe fixes. Returns report. Dangerous operations still require Nate's approval.
**Input**: `{"mode": "check|fix", "scope": "all|patterns|knowledge|reasoning"}`
**Output**: `{"issues_found": 12, "auto_fixed": 8, "needs_review": 4, "details": [...]}`
**Safe auto-fixes** (applied in `fix` mode without approval):
- lastAccessed dates older than created dates → set lastAccessed = created
- accessCount < 0 → set to 0
- Duplicate tags within an entry → deduplicate
- Index stats.totalEntries doesn't match actual count → rebuild index
- Entry in store but missing from index summaries → rebuild index
- Entry in index but missing from store → remove from index (rebuild)
**Requires Nate's approval** (reported but not auto-fixed):
- Entries with accessCount = 0 and age > 90 days (prune candidates)
- Near-duplicate entries (>80% content overlap, measured by Jaccard token overlap on content field)
- Entries with confidence < 0.3 (low-value candidates)
- Orphaned cross-references (source entry deleted but cross-ref remains)

### 5. Vectorstore graceful degradation
**Priority**: Low
**Trigger**: KB search when vectorstore is unavailable
**Resolution**: Extend existing vectorstore MCP server (kb_server.py) to fall back to keyword + tag matching when the vector index is missing or corrupted. Same interface, degraded mode. No new script needed.

---

## Implementation Order

0. **save-session.py hardening** — Reference implementation. Patterns established here carry to all subsequent scripts.
1. **cascade-correction.py** — High per-occurrence token cost, high error risk (missed refs = poisoned KB).
2. **removal-cascade.py** — Most error-prone manual operation, causes benchmark failures when done wrong.
3. **session-cache.py** — Saves tokens every session, compounds over time.
4. **maintenance.py** — Monthly use but high token cost when it runs.
5. **Vectorstore degradation** — Folded into existing server. Not a separate build.

---

## Design Principles

- Scripts are tools, not replacements for reasoning. Nate decides WHAT to do. Scripts do HOW.
- All scripts are idempotent. Running twice produces the same result.
- All scripts validate input before writing. Malformed ops files abort, don't corrupt.
- All scripts use atomic writes (write to .tmp, then os.replace).
- Index rebuilds are always full rebuilds, never incremental. Drift is eliminated structurally.
- Scripts clean up after themselves (temp files, ops files).
- Scripts work cross-platform: find their own KB root, handle path separators, find the right Python/venv.
- Ops files include `"schema_version": 1`. Scripts validate version and reject unknown versions.
- Ops file cleanup: script deletes ops file on success (exit 0). On EXIT:1 (partial), script preserves ops file for debugging — Nate deletes after manual completion. Nate deletes on manual fallback (EXIT:2).
- Script timeout: 60s default. If exceeded, Nate kills process and falls back to manual.
- Exit code communication: scripts print `EXIT:0`, `EXIT:1`, or `EXIT:2` as final stdout line. Nate parses text output, not process exit code (PowerShell/IDE may not reliably return exit codes).
- File locking: mandatory for all store writes. `fcntl.flock` on POSIX (covers WSL on Windows). Native Windows Python execution is not a supported path for store writes. Concurrent IDE + CLI saves must not corrupt stores.
- Cache invalidation on inline writes: any direct store write outside save-session.py touches a sentinel file (`cache/.invalidated`). session-cache checks sentinel before queries.
- New entries must conform to store schemas (see Ecosystem Context). Scripts validate category/type/provenance against enum values before writing.
- Ops file naming: `_save_ops_{session_id}.json` to prevent concurrent overwrites when IDE and CLI save simultaneously.
- Scripts are coupled to the 3-store architecture (patterns, knowledge, reasoning). Adding a 4th store requires updating all scripts. Scripts warn on exceed but still write (matching validate-schemas.py behavior which flags as INFO, not ERROR). The warning surfaces in script output so Nate can revise if needed.

---

## Deployment Protocol

Every script deployment requires three artifacts. Behavioral instructions alone degrade under context pressure — the same structural-vs-behavioral principle from SRG.

### Required Artifacts Per Script

| Artifact | Purpose | Location |
|----------|---------|----------|
| **Gate** | Mandatory checkpoint before the manual approach | Kernel (Nathaniel.md) — in the existing gate for the operation |
| **Knowledge entries** | CLI usage, input/output schema, platform quirks | knowledge.json |
| **Fallback clause** | If script fails, manual is permitted but failure is logged | Inside the gate definition |

### Gate Placement Map

| Script | Gate Location | Fires Before |
|--------|-------------|--------------|
| save-session.py | Save Phase B (Script-First Gate) | Any JSON store write |
| cascade-correction.py | Correction Cascade Gate | Manual grep + fix loop |
| removal-cascade.py | Removal Cascade Gate | Manual delete + index cleanup |
| session-cache.py | Session Start Gate (step 2) | Loading 5 index files |
| maintenance.py | Maintenance protocol trigger | Full-store reads for health checks |

### Gate Template

```
SCRIPT CHECK (before manual execution):
IF scripts/<script-name>.py exists:
  1. Prepare input per script's expected schema
  2. Call: python3 scripts/<script-name>.py <args>
  3. Manual execution of this operation is PROHIBITED when the script exists
  4. FALLBACK: If script fails, manual execution is permitted. Log the failure.
IF scripts/<script-name>.py does NOT exist:
  - Proceed with manual execution (standard behavior)
```

### Deployment Checklist (per script)

```
[ ] Script built and tested (dry run + live run)
[ ] Gate added/updated in kernel (both .steering-files and .kiro copies)
[ ] Knowledge entries added to template KB (conforming to schema enums)
[ ] Schema validation passes (0 errors, 0 warnings)
[ ] Benchmarks updated if new testable behavior added
[ ] Committed to template repo
```

---

## Error Handling Standards

Every script is a critical path component. If a script corrupts a store or silently drops data, the entire intelligence layer is compromised.

### Requirements

**1. Atomic writes or no writes**
- All store mutations use write-to-tmp then `os.replace()` pattern
- If any step fails mid-execution, no partial writes reach the store
- On failure: original files remain untouched, error reported to stdout

**2. Input validation**
- Validate ops file schema before any mutations (required fields, types, ID formats)
- Validate entry fields against store schemas (category/type/provenance enums, content length limits)
- Reject malformed input with clear error message naming the specific field
- Validate entry IDs don't collide with existing entries before writing

**3. Graceful degradation**
- Missing store files: create empty store with valid schema, warn, continue
- Missing index files: rebuild from store, warn, continue
- Missing vectorstore: skip sync step, warn, never block
- Corrupt JSON: refuse to write, report corruption, preserve original file

**4. Exit codes**
- 0: success (all operations completed)
- 1: partial success (some operations completed, others failed — report which)
- 2: total failure (no operations completed, stores untouched)
- Final stdout line: `EXIT:0`, `EXIT:1`, or `EXIT:2` (text-parseable)

**5. Logging**
- Every mutation logged to stdout: what changed, entry IDs, counts
- Errors logged to stderr with enough context to reproduce
- Dry-run mode (`--dry-run`) that reports what would change without writing

**6. File locking**
- Acquire exclusive lock before any store write
- Release on completion or failure
- Second concurrent call waits (with timeout) or fails clean

---

## Testing Standards

Applies to ALL scripts including save-session.py.

### Per-Script Test Suite (pytest, `tests/` directory)

| Test Category | What It Covers |
|--------------|----------------|
| Happy path | Normal operation with valid input, verify output matches expected |
| Empty input | No entries, no updates — exits 0, changes nothing |
| Malformed input | Bad JSON, missing fields, wrong types — exits 2, stores untouched |
| Schema violation | Invalid category/type/provenance enum — rejects with clear error |
| ID collision | New entry ID already exists — rejects with clear error |
| Large store | 500+ entries — performance under 5s, no memory issues |
| Corrupt store | Invalid JSON in target — refuses to write, preserves original |
| Missing files | Store/index doesn't exist — creates or rebuilds as appropriate |
| Concurrent access | Two script calls on same store — second waits or fails clean |
| Dry run | `--dry-run` — reports changes, writes nothing, exits 0 |
| Index integrity | After write: stats match actual count, all IDs in summaries |
| Cross-platform | Runs on Linux (direct) and Windows (WSL) with same results |
| Rollback on failure | Inject failure mid-write — original files preserved |

### session-cache.py Additional Tests

| Test Category | What It Covers |
|--------------|----------------|
| Cache build | SQLite DB built from 5 index files, all entries queryable |
| Cache invalidation | After save, cache marked stale, next query triggers rebuild |
| Cache miss fallback | DB missing or corrupt — falls back to file reads, no error |
| Query accuracy | Tag/category/confidence queries return same IDs as direct index search |
| Compaction survival | Cache persists on disk, queryable after simulated context reset |
| Rebuild idempotency | Building cache twice produces identical DB |
| Sentinel invalidation | Inline write touches sentinel → next query rebuilds cache |

### Integration Tests

| Test | What It Validates |
|------|------------------|
| Full save cycle | ops file → save-session.py → indexes rebuilt → vectorstore synced → git clean |
| Correction cascade | Stale fact → cascade-correction.py finds all refs → all updated → indexes rebuilt |
| Removal cascade | Entry deleted → removal-cascade.py cleans indexes, cross-refs, derived_from → no orphans |
| Cache → save → cache | Query cache → save new entries → cache invalidated → rebuild → new entries queryable |
| Maintenance report | maintenance.py finds planted issues → reports → auto-fixes safe ones → report accurate |
| Fallback path | Script deliberately broken → Nate detects failure → falls back to manual → save completes |

### Infrastructure

- Tests use fixture stores (small, known-state JSON files conforming to schemas above), not live KB
- Each test creates temp directory, runs script, asserts output, cleans up
- CI-compatible: `pytest tests/` exits 0 or reports failures
- Coverage target: 90%+ line coverage per script
- Existing benchmark suite (`scripts/run-benchmarks.py`) must still pass after any script run

---

## Success Metrics

| Metric | Before | Target |
|--------|--------|--------|
| Save credits | ~23 | ~3-5 |
| Save time | ~12 min | ~2 min |
| Correction cascade credits | ~10 | ~2-3 |
| Removal cascade error rate | ~30% (index drift) | 0% |
| Session start file reads | 5 | 1 (cached) |
| Monthly maintenance credits | ~15 | ~3-5 |

---

## Research Validation

### Industry Patterns

**Programmatic Tool Calling** — Production agent reduced from 76K tokens / 56 tool calls to 30K tokens / 5-12 calls by offloading sequential data operations to Python scripts. "The agent's job isn't to have a conversation — it's to decompose a task, select the right execution strategy, and assemble results." This is our pattern: Nate decomposes (taxonomy sweep), scripts execute (JSON mutations), Nate assembles (git commit + confirmation). [mejba.me]

**Token Cost Optimization Consensus** — Industry converges on: offload mechanical work to scripts (40-60% savings), context curation (avoid full file loads), batch operations (one script call vs 40+ tool calls). [veduis.com, fast.io]

**SQLite for Local Agent Caching** — Three independent sources (sparkco.ai, memweave/TDS, Oracle dev blog) converged on SQLite as the optimal choice for local AI agent structured caching: zero dependencies, single file, sub-ms queries, ACID, ships with Python.

**Atomic Writes** — `os.replace()` is atomic on POSIX and Windows (NTFS). Standard Python ecosystem approach. No external dependency needed.

**TOON Format** — Evaluated and rejected for ops files. Reduces JSON overhead 30-60% but adds parser complexity. Our ops files are small (~500 tokens). Not worth it.

---

## Adversarial Findings

**Gate position is load-bearing.** The Script-First Gate works because it's the first thing in Phase B. If future kernel edits push it down, the LLM may start writing before seeing the gate. The gate's position must be preserved.

**Fallback is the expensive path.** If scripts fail frequently, we're back to 23-credit saves. Script reliability is the entire value proposition. Testing standards are the mitigation.

**Concurrent IDE + CLI saves.** Both instances share the same stores. File locking is a mandatory design requirement, not just a test requirement.

**Cache staleness after inline entries.** The INLINE ENTRY INTEGRITY rule writes directly to stores mid-session, bypassing save-session.py. The session-cache won't know about these entries until next rebuild. Sentinel file invalidation addresses this.

**Script-kernel version drift.** Template ships script v1. User customizes kernel. We ship script v2 with new gate language. Mitigation: add version check when template ships v2 of any script.

---

## Future Audit

This is not a closed list. As the KB grows, audit for:
- Any operation where Nate reads a file just to count, search, or transform (not to reason about)
- Any operation requiring 5+ sequential tool calls on the same file
- Any operation with a >20% error rate when done manually
- Any operation that recurs monthly or more frequently

When a new candidate is identified, evaluate: token cost, error risk, frequency, and whether a gate already exists for the manual version.
