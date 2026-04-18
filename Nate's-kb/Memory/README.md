# Memory Directory

**Purpose**: Session memory, conversation continuity, and context management
**Last Updated**: 2026-04-16

---

## Directory Structure

```
Memory/
├── README.md              # This file
├── memory.json            # Session memory, projects, preferences (grows over time)
├── memory-index.json      # CSR index for efficient memory retrieval
├── session-index.json     # CSR index for session lookup (60-day rolling window)
├── session-archive.json   # Archived session fingerprints (created by first prune cycle)
├── session-*.md           # Individual session logs (full detail)
└── archive/               # Session logs older than 30 days
```

---

## File Purposes

### memory.json
Core memory store containing:
- Memories (preferences, decisions, corrections)
- Active projects with status tracking
- Pattern detections pending consolidation
- Confidence events for calibration
- Proactive behavior offer history
- Domain expertise levels

### memory-index.json (CSR Pattern)
Lightweight routing index for memory retrieval:
- byTag, byType, byConfidence dimensions
- Summaries for quick scanning
- recentIds for recency-based access

### session-index.json (CSR Pattern)
Lightweight session fingerprints for efficient context loading:
- ~50 tokens per session vs ~1,500 for full log
- Tags for signal-based retrieval
- Key outcome for quick context
- 60-day rolling window; older entries archived

### session-archive.json
Fingerprints for sessions older than 30 days. Enables historical recall without loading full logs.

---

## Retention Rules

Per `memory-protocol.md`:
- Session logs: 30-day retention, then archived to `archive/`
- Session index: 60-day window, min keep 10
- Full maintenance: see `maintenance-protocol.md`
