# Intelligence System

**Purpose**: Learning, adaptation, cognitive alignment, and knowledge accumulation
**Last Updated**: 2026-04-16
**Version**: 6.0 (GOLDEN seed)
**Pattern**: CSR (Context Signal Routing) for all data stores

---

## Architecture

```
Intelligence/
├── patterns.json              # Behavioral patterns (grows over time)
├── patterns-index.json        # CSR routing index for patterns
├── knowledge.json             # Factual knowledge (grows over time)
├── knowledge-index.json       # CSR routing index for knowledge
├── reasoning.json             # Derived conclusions & connections (grows over time)
├── reasoning-index.json       # CSR routing index for reasoning
├── cross-references.json      # Reverse lookup: pattern/knowledge → reasoning
├── synonym-map.json           # CSR synonym expansion for retrieval quality
├── intelligence-operations.md # Unified operations guide
├── learning-loop.md           # Consolidation + access tracking (save Part 3)
└── README.md                  # This file
```

---

## Documentation Hierarchy

| Type | Location | Purpose |
|------|----------|---------|
| **Operational Docs** | `Intelligence/` | Execution instructions only |

---

## Components

### Data Stores (JSON)
| File | Purpose |
|------|---------|
| `patterns.json` | Behavioral patterns with confidence scores |
| `knowledge.json` | Factual knowledge entries |
| `reasoning.json` | Derived conclusions, connections, analogies |

### Indexes (CSR Pattern)
| File | Dimensions |
|------|------------|
| `patterns-index.json` | byCategory, byTag, byConfidence, recentIds |
| `knowledge-index.json` | byCategory, byTag, bySource, byConfidence, recentIds |
| `reasoning-index.json` | byType, byTag, byConfidence, recentIds |
| `cross-references.json` | pattern_to_reasoning, knowledge_to_reasoning (derived, rebuildable) |
| `synonym-map.json` | Bidirectional synonym expansion for CSR query-time retrieval |

### Operational Docs (Execution Only)
| File | Purpose |
|------|---------|
| `intelligence-operations.md` | Quality standards, detection, application, self-correction |
| `learning-loop.md` | Consolidation, access tracking, quality gates (save Part 3) |

---

## Three Learning Systems

| System | Purpose | Data | Retrieval |
|--------|---------|------|-----------|
| **Patterns** | How to work with user (behavioral) | patterns.json | Via patterns-index.json |
| **Knowledge** | Facts about the world (factual) | knowledge.json | Via knowledge-index.json |
| **Reasoning** | Derived conclusions & connections (analytical) | reasoning.json | Via reasoning-index.json |

---

## How It Works

```
Session Start (via Nathaniel.md Session Start Gate)
    ↓
Load indexes (patterns, knowledge, reasoning, session, memory)
    ↓
During Session
    ↓
Apply patterns, surface knowledge, apply reasoning, detect new learnings
Note accessed entries + failure pattern outcomes (best-effort)
Synonym-aware retrieval via synonym-map.json at query time
    ↓
Save Command (Script-First Gate)
    ↓
Write _save_ops.json with new entries + updates
    ↓
python3 scripts/save-session.py _save_ops.json
    ↓
Script handles ALL store mutations deterministically:
  Part 3a: patterns.json + rebuild index
  Part 3b: knowledge.json + rebuild index
  Part 3c: reasoning.json + rebuild index + cross-references
  Memory, session index, vectorstore sync
    ↓
Fallback: if script fails, manual writes permitted
```

---

## Script Offload System

Store mutations are handled by deterministic Python scripts, not LLM inline edits:

| Script | Purpose |
|--------|---------|
| `scripts/save-session.py` | All save-time store writes (patterns, knowledge, reasoning, memory, indexes) |
| `scripts/cascade-correction.py` | Scan/apply fact corrections across all stores |
| `scripts/removal-cascade.py` | Cascade deletion with tag merge, cross-ref cleanup |
| `scripts/maintenance.py` | Health checks (6 auto-fixes) + review items |
| `scripts/reseed.py` | Validate and rebuild all indexes from stores |

Why scripts: LLM inline JSON edits suffer from omission under load, recall substitution, and format drift (see Section 0 knowledge entries). Scripts execute outside the LLM decision loop and cannot be skipped.

---

## CSR Pattern

All data stores use Context Signal Routing:
1. Load lightweight index (~500 tokens)
2. Match user signals to dimensions (with synonym expansion via synonym-map.json)
3. Retrieve only relevant entries (max 5)
4. Full data loaded on-demand, not eagerly

See `Intelligence/intelligence-operations.md` for full CSR documentation.

---

## If Something Breaks

1. Core personality (Nathaniel.md) works without Intelligence
2. Run `python3 scripts/reseed.py --verify-only` to check integrity
3. Run `python3 scripts/reseed.py` to rebuild all indexes from stores
4. Run `python3 scripts/maintenance.py '{"mode": "check", "scope": "all"}'` for health check
5. If stores corrupted: `git checkout HEAD~1 -- Nate's-kb/Intelligence/` to restore from last save
6. Ask user to confirm key preferences if patterns lost
