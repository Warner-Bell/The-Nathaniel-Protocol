# CRITICAL FILE PROTECTION PROTOCOL

**Purpose**: Prevent accidental destruction of intelligence system and core operational files
**Created**: December 17, 2025
**Updated**: February 13, 2026
**Trigger**: Near-destruction of patterns.md intelligence database

---

## 🚨 CRITICAL FILES - NEVER MODIFY WITHOUT EXPLICIT CONFIRMATION 🚨

### Intelligence System Files (IRREPLACEABLE)
```
/Intelligence/patterns.json        - Behavioral patterns database
/Intelligence/patterns-index.json  - Pattern routing index
/Intelligence/knowledge.json       - Factual knowledge database
/Intelligence/knowledge-index.json - Knowledge routing index
/Intelligence/reasoning.json       - Derived conclusions and connections
/Intelligence/reasoning-index.json - Reasoning routing index
/Intelligence/cross-references.json - Reverse lookup index (derived, rebuildable from reasoning.json)
/Intelligence/synonym-map.json     - CSR synonym expansion map (query-time lookup, maintainable)
/Intelligence/intelligence-operations.md - Unified operations guide
/Intelligence/learning-loop.md     - Consolidation algorithm
```

### Memory System Files (CRITICAL)
```
/Memory/memory.json          - Session memory, projects, preferences
/Memory/memory-index.json    - Memory routing index
/Memory/session-index.json   - Session fingerprints
/Memory/session-*.md         - Session history and continuity
```

### Core System Files (CRITICAL)
```
/.kiro/steering/Nathaniel.md       - Core personality, cognitive stance, and identity
/Nate-Protocol.md                  - Operational framework and decision engine
```

### Vectorstore Source Files (IMPORTANT - logic is git-tracked, artifacts are rebuildable)
```
/vectorstore/concat.py             - Shared field concatenation + hashing
/vectorstore/kb_vectorize.py       - Full vectorstore build
/vectorstore/kb_query.py           - Hybrid search (semantic + keyword + RRF)
/vectorstore/kb_sync.py            - Incremental sync via content hashing
/vectorstore/kb_server.py          - MCP server wrapper
```

### Operational Protocols (IMPORTANT)
```
/development-protocol.md           - Development standards and practices
/writing-protocol.md               - Communication standards
/memory-protocol.md                - Memory operations
```

### Security Scripts (IMPORTANT)
```
/scripts/secure-fetch.py           - MCP fetch proxy (URL filtering at JSON-RPC level)
```

---

## MANDATORY PROTECTION PROCEDURES

### Before ANY File Operation (mv, cp, rm, >)

**STEP 1: STOP AND ASSESS**
```
BEFORE touching ANY file in these directories:
- /Memory/
- /Intelligence/
- /.kiro/steering/
- /Nate's-kb/ (root level protocols)

ASK YOURSELF:
1. What is this file's purpose?
2. Is this part of the intelligence system?
3. Could this break core functionality?
4. Do I have explicit permission to modify this?
```

**STEP 2: READ FIRST, UNDERSTAND SECOND**
```
ALWAYS execute BEFORE any file operation:
fs_read to examine the existing file content
- Understand what the file contains
- Identify if it's system-critical
- Determine if it's user data vs. system data
```

**STEP 3: EXPLICIT CONFIRMATION REQUIRED**
```
FOR CRITICAL FILES - ALWAYS ASK:
"This file appears to be [purpose]. Modifying it could [impact]. 
Confirm you want me to proceed with [specific operation]?"

NEVER assume permission for:
- Overwriting existing files
- Moving files to locations with existing files
- Deleting any file in protected directories
```

---

## FILE OPERATION SAFETY RULES

### Rule 1: Intelligence Files Are SACRED
```
NEVER modify without explicit confirmation:
- patterns.json (behavioral patterns database)
- knowledge.json (factual knowledge database)
- memory.json (session memory and preferences)

THESE FILES REPRESENT ACCUMULATED LEARNING AND CANNOT BE RECREATED
```

### Rule 2: Read Before You Write
```
MANDATORY sequence for file operations:
1. fs_read to examine existing content
2. Understand the file's purpose and importance
3. Ask for explicit confirmation if modifying system files
4. Only then proceed with the operation
```

### Rule 3: Safe Alternatives First
```
PREFER:
- Appending to files over overwriting
- Creating new files over modifying existing
- Asking before any destructive operation

AVOID:
- Blind overwrites (> operator without reading first)
- Moving files without checking destination
- Deleting without explicit user confirmation
```

---

## RECOVERY PROCEDURES

If critical files are damaged:

1. **Check git history** - Old versions may exist
2. **Check session logs** - Recent changes documented
3. **Reconstruct from memory.json** - Pattern detections can rebuild patterns.json
4. **Ask user** - They may have backups or remember key content

---

## CHECKLIST FOR FILE OPERATIONS

Before ANY operation on protected files:

- [ ] Read the file first
- [ ] Understand its purpose
- [ ] Check if it's in a protected directory
- [ ] Ask for explicit confirmation
- [ ] Never overwrite patterns.json (append or ask first)
- [ ] Never overwrite knowledge.json (append or ask first)
- [ ] Never overwrite memory.json without understanding structure
- [ ] Document what you changed in session log

---

*This protocol exists because of a near-catastrophic loss of the intelligence database on December 17, 2025. Learn from this mistake.*
