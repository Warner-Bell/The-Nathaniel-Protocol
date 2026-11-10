# The Nathaniel Protocol - File Structure

**Last Updated**: 2026-11-10 (v4.0.0)

```
The-Nathaniel-Protocol/
├── .github/                        # GitHub community files
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md           # Bug report template
│   │   └── feature_request.md      # Feature request template
│   └── workflows/
│       └── validate.yml            # CI: JSON validation, setup dry-run, vectorstore tests
├── .gitattributes                  # Git attributes (LF normalization + sanitization filters)
├── .editorconfig                   # Editor config (LF line endings, UTF-8, trim whitespace)
├── .gitignore                      # Exclusion rules
├── CHANGELOG.md                    # Release history (4.0.0: Kiro CLI v3 migration)
├── VERSION                         # Template version (4.0.0)
├── CONTRIBUTING.md                 # Contribution guidelines
├── CODE_OF_CONDUCT.md              # Community standards
├── Nathaniel-protocol-case-study.md # Context engineering case study
├── CLAUDE.md                       # Claude Code configuration (built by setup.sh from the four kernel files)
├── LICENSE                         # MIT License
├── SECURITY.md                     # Vulnerability reporting policy
├── README.md                       # Public-facing project overview
├── POCKET-HQ.md                    # Pocket HQ pattern guide
├── FILE-STRUCTURE.md               # This file
├── setup.bat                       # One-click Windows installer (auto-elevates, chains bootstrap + setup-wsl)
│
├── # Pocket HQ Scaffold (starter workspace directories)
├── Projects/                       # Active project work
├── Business/                       # Business operations
├── Brand/                          # Personal brand, content, social
├── Life/                           # Personal planning (optional)
│   ├── .secrets/                    # (create when needed) credential store: git-ignored, agent-blocked
│   ├── Career/                     # Career progression, resumes, certs
│   ├── Education/                  # Degrees, transcripts, courses
│   ├── Family/                     # Important docs, records
│   ├── Finances/                   # Investments, taxes, budgets
│   ├── Goals/                      # Sprints, weekly ops, aspirations
│   ├── Health/                     # Health records, fitness
│   ├── Home/                       # Property, vehicle, community
│   └── Journal/                    # Reflections, monthly entries
├── Archive/                        # Completed/historical materials
├── docs/                           # Reference documentation
│   └── system-maintenance.md       # System maintenance guide (4-phase)
│
├── Nate's-kb/                      # Core knowledge base system
│   ├── README.md                   # KB overview and navigation
│   ├── QUICKSTART.md               # Quick start cheat sheet
│   ├── CUSTOMIZATION.md            # Personality customization guide
│   ├── CRITICAL-FILE-PROTECTION.md # Protection rules for intelligence files
│   ├── Nate-Protocol.md            # Core decision engine (Routes A-F)
│   ├── Nathaniel-Protocol.webp     # Portrait hero image (README)
│   ├── Nathaniel-Protocol-SC.webp  # Social preview card (upload via GitHub Settings > General > Social preview)
│   ├── lexicon.md                  # Vocabulary and terminology reference
│   │
│   ├── credential-registry.json    # Credential cards: metadata only, never a value (scripts/cred.py)
│   │
│   ├── # Protocols (15 files)
│   ├── anti-slop-protocol.md        # Document integrity audit (every claim proven)
│   ├── customization-protocol.md
│   ├── development-protocol.md
│   ├── empirical-feasibility-protocol.md
│   ├── executive-communication-protocol.md
│   ├── maintenance-protocol.md
│   ├── memory-protocol.md
│   ├── planning-protocol.md
│   ├── proactive-offering-protocol.md
│   ├── problem-solving-protocol.md
│   ├── prompt-enhancement-protocol.md
│   ├── research-protocol.md
│   ├── security-protocol.md
│   ├── summarization-protocol.md
│   ├── writing-protocol.md
│   │
│   ├── Intelligence/               # Learning and knowledge system
│   │   ├── README.md
│   │   ├── intelligence-operations.md
│   │   ├── learning-loop.md
│   │   ├── corrections.jsonl       # Correction loop ledger (hook events + diagnoses)
│   │   ├── correction-loop.json    # Correction loop mode: log | enforce | off
│   │   ├── synonym-map.json        # Enhanced CSR synonym routing
│   │   ├── cross-references.json   # Reverse lookup (curated baseline)
│   │   ├── knowledge.json          # Factual knowledge (curated baseline)
│   │   ├── knowledge-index.json    # Knowledge routing index (curated baseline)
│   │   ├── patterns.json           # Behavioral patterns (curated baseline)
│   │   ├── patterns-index.json     # Pattern routing index (curated baseline)
│   │   ├── reasoning.json          # Derived conclusions (curated baseline)
│   │   └── reasoning-index.json    # Reasoning routing index (curated baseline)
│   │
│   ├── Memory/                     # Session and memory system
│   │   ├── README.md
│   │   ├── memory.json             # Entity memory (starter template)
│   │   ├── memory-index.json       # Memory routing index (starter template)
│   │   ├── session-index.json      # Session fingerprints (starter template)
│   │   ├── context-calibration.json  # Context-depth readings log (Source Authority Gate)
│   │   └── archive/                # Archived session logs
│   │       └── README.md
│   │
│   ├── Benchmarks/                  # Performance and scale metrics
│   │   ├── README.md
│   │   ├── run-benchmark.py        # Automated benchmark runner
│   │   ├── benchmark-metrics.json  # Historical benchmark results
│   │   ├── benchmark-candidates.md
│   │   ├── img-gate-stress-test.md
│   │   ├── ecosystem-benchmark-2026-03-21.md
│   │   ├── behavioral-benchmark-2026-03-21.md
│   │   ├── security-benchmark-2026-03-22.md
│   │   └── save-protocol-benchmark.md
│   └── vectorstore/                # Hybrid semantic search (venv local to this dir, see SETUP.md)
│       ├── SETUP.md                # Venv setup instructions (PEP 668 compatibility)
│       ├── BENCHMARK.md
│       ├── concat.py               # Shared KB concatenation module
│       ├── kb_vectorize.py         # Build vector index from KB
│       ├── kb_query.py             # Hybrid search (CSR + semantic)
│       ├── kb_sync.py              # Sync vectorstore with KB changes
│       ├── kb_server.py            # MCP server for semantic search
│       ├── kb_benchmark.py         # Embedding model benchmarking
│       ├── access_tracking.py      # Retrieval hit counts (feeds pruning decisions)
│       ├── test_dim_guard.py       # Query/index embedding-dimension guard test
│       ├── run-server.sh           # MCP server launcher (handles paths with spaces)
│       └── tests/
│           ├── __init__.py
│           ├── test_build.py
│           ├── test_concat.py
│           ├── test_query.py
│           ├── test_sync.py
│           ├── test_truncation.py  # max-token truncation guard
│           └── test_synonyms.py    # synonym-map expansion
│
├── .steering-files/                # Platform configuration (portable source of truth)
│   ├── README.md                   # Directory guide and platform setup reference
│   ├── settings/
│   │   └── mcp.json               # MCP server configurations (fetch uses security proxy)
│   ├── hooks/                      # Kiro CLI v3 workspace hooks (deployed to .kiro/hooks/)
│   │   ├── safety-floor.json       # denylist, source-authority, pre-flight, audit log
│   │   ├── correction-loop.json    # UserPromptSubmit: capture corrections
│   │   ├── skill-router.json       # UserPromptSubmit + PreToolUse: route to skill/protocol
│   │   ├── file-structure.json     # SessionStart + PostToolUse: refresh the repo map
│   │   ├── kb-consultation-gate.json  # UserPromptSubmit: per-turn KB reminder
│   │   ├── email-send-gate.json    # PreToolUse: ask before any email send/reply/forward
│   │   └── nate-session-gate.kiro.hook  # Kiro IDE twin of the KB reminder
│   ├── skills/                     # Agent skills (deployed to .kiro/skills/)
│   │   ├── correction-capture/SKILL.md  # Diagnose a correction, cite or add a rule
│   │   ├── route-f-analysis/SKILL.md    # Full pre-action analysis for non-trivial decisions
│   │   └── stop-slop/               # Third-party (MIT, Hardik Pandya): AI-writing-pattern removal pass
│   ├── steering/
│   │   ├── Nathaniel.md            # Kernel: identity, voice, sessions, self-checks (always-loaded)
│   │   ├── ecosystem-operation.md  # Kernel: operating gates, keyword map, KB map (always-loaded)
│   │   ├── PRIME-DIRECTIVES.md     # Kernel: compliance directive and Rules (always-loaded)
│   │   ├── source-authority-gate.md  # Kernel: read the artifact that proves a claim (always-loaded)
│   │   ├── FILE-STRUCTURE.md       # Repo map (always-loaded)
│   │   └── tool-inventory.md       # Tool reference (always-loaded)
│   ├── specs/                      # Kiro spec-driven development (empty)
│   └── agents/                     # Specialized sub-agents
│       ├── analyst.json            # Config
│       └── analyst/
│           ├── README.md
│           ├── analyst-prompt.md
│           ├── consciousness.md
│           └── specialization.md
│
└── scripts/                        # Automation and maintenance
    ├── setup.sh                    # First-run setup (git filters, deps, vectorstore); --upgrade refreshes .kiro/
    ├── setup-filters.sh            # Git sanitization filter config only
    ├── bootstrap-windows.ps1       # Windows bootstrap (Git, Python, uv, WSL, Ubuntu)
    ├── setup-wsl.ps1               # WSL environment setup (no admin needed)
    ├── teardown.ps1                # Environment teardown (PowerShell)
    ├── run-python.sh               # Python runner (venv-aware)
    ├── save-session.py             # Atomic save: all JSON mutations, index rebuilds, vectorstore sync
    ├── index-query.py              # On-demand index access (head, signals, tag, keyword, ids)
    ├── session-cache.py            # Session-local cached KB access (SQLite-backed, FTS5 search)
    ├── test-index-query.py         # Tests for index-query.py
    ├── cascade-correction.py       # Scan stores for stale claims, apply fixes atomically
    ├── removal-cascade.py          # Delete entries with full cascade (store, indexes, cross-refs)
    ├── maintenance.py              # Health checks + safe auto-fixes (includes credential registry audit)
    ├── cred.py                     # Credential card resolver + drift audit (never prints a value)
    ├── cred.js                     # Node twin of cred.py for JS scripts
    ├── correction-ledger.py        # Sole writer for correction diagnoses and the PRIME-DIRECTIVES Rules
    ├── correction-backfill.py      # Seed the correction ledger from Kiro CLI chat history
    ├── apply-entry-ops.py          # Apply queued KB entry operations
    ├── doc-kb-sync.py              # Find docs with no knowledge entry pointing at them
    ├── check-no-emdash.py          # Em/en-dash lint
    ├── commitments.py              # Close/redate/add commitments immediately, outside a save
    ├── reconcile-memory.py         # Report (and --apply merge) duplicate projects, stale commitments
    ├── md2pdf.py                   # Markdown to PDF for hand-off deliverables
    ├── md2docx.py / docx-to-md.py  # Markdown to Word and back (python-docx)
    ├── lint-deliverables.py        # Mechanical writing-protocol linter
    ├── email-send-gate.py          # Email send/reply/forward approval gate (hook)
    ├── gen-file-structure.py       # Regenerate the always-loaded repo map
    ├── test-session-cache-fts.py   # FTS5 query sanitizer tests
    ├── hooks/                      # Deterministic floor hooks + their test suites
    │   ├── denylist.py             # Secret paths, credential echo, metadata endpoint, rm -rf, self-disarm
    │   ├── source-authority.py     # Live-contract read required before model create/update edits
    │   ├── preflight.py            # Flags searches for files at documented locations
    │   ├── audit_log.py + audit_common.py  # HMAC-chained audit trail of state changes
    │   ├── gate_grant.py           # Scoped, expiring exceptions to one floor rule
    │   ├── correction_hook.py      # Correction detector (correction loop)
    │   ├── skill_router_hook.py    # Skill/protocol router hook
    │   └── test-*.py               # One regression suite per hook
    ├── skill-router/               # Router engine: matcher.py, intent.py, routes.json, routes_check.py, corpus.jsonl
    ├── reseed.py                   # Golden seed verification and reseeding
    ├── secure-fetch.py             # MCP fetch security proxy (URL filtering)
    ├── full-maintenance.sh         # Unified wrapper: chains Phases 1-3 with flag passthrough
    ├── git-filter-clean.py         # Git clean filter (sanitize on commit)
    ├── git-filter-smudge.py        # Git smudge filter (restore on checkout)
    ├── harden-repo.sh              # Security hardening script
    ├── normalize-schemas.py        # JSON schema normalization
    ├── validate-schemas.py         # JSON schema validation
    ├── pre-commit-kb-validate.sh   # Pre-commit hook for KB validation
    ├── kiro-maintenance.sh         # Kiro CLI maintenance automation
    ├── python-maintenance.sh       # Python environment maintenance
    ├── wsl-compact.ps1             # WSL disk compaction (PowerShell)
    └── wsl-maintenance.sh          # WSL maintenance automation

├── tests/                          # Script test suites
│   ├── test_save_session.py
│   ├── test_save_session_memories.py
│   ├── test_entry_unset.py
│   ├── test_save_session_commitments.py
│   ├── test_commitments_cli.py
│   ├── test_reconcile_memory.py
│   ├── test_doc_converters.py
│   ├── test_lint_deliverables.py
│   ├── test_session_cache.py
│   ├── test_cascade_correction.py
│   ├── test_removal_cascade.py
│   ├── test_maintenance.py
│   ├── test_edge_cases.py
│   └── test_columbo_oob.py
```

## Path Routing Table

| Domain | Root Path | Description |
|--------|-----------|-------------|
| Projects | `Projects/` | Active project work (Pocket HQ scaffold) |
| Business | `Business/` | Business operations (Pocket HQ scaffold) |
| Brand | `Brand/` | Personal brand, content, social (Pocket HQ scaffold) |
| Life | `Life/` | Personal planning (Pocket HQ scaffold, optional) |
| Archive | `Archive/` | Completed/historical materials (Pocket HQ scaffold) |
| Docs | `docs/` | Reference documentation (Pocket HQ scaffold) |
| Knowledge Base | `Nate's-kb/` | All protocols, intelligence, memory |
| Protocols | `Nate's-kb/*.md` | Behavioral and task protocols |
| Intelligence | `Nate's-kb/Intelligence/` | Patterns, knowledge, reasoning stores |
| Memory | `Nate's-kb/Memory/` | Session logs, entity memory |
| Vectorstore | `Nate's-kb/vectorstore/` | Hybrid semantic search (.venv local to vectorstore/) |
| Benchmarks | `Nate's-kb/Benchmarks/` | Performance and scale metrics |
| Kiro Config | `.steering-files/` | Portable Kiro CLI mirror |
| Agents | `.steering-files/agents/` | Sub-agent packages |
| Hooks | `.steering-files/hooks/` | Kiro CLI v3 workspace hooks |
| Skills | `.steering-files/skills/` | Agent skills |
| Credentials | `Nate's-kb/credential-registry.json` | Card registry (values live in git-ignored stores) |
| Scripts | `scripts/` | Automation and maintenance |
