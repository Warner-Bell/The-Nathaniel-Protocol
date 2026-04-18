# The Nathaniel Protocol - File Structure

**Last Updated**: 2026-04-17

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
├── CONTRIBUTING.md                 # Contribution guidelines
├── CODE_OF_CONDUCT.md              # Community standards
├── Nathaniel-protocol-case-study.md # Context engineering case study
├── CLAUDE.md                       # Claude Code configuration (generated from .steering-files/)
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
│   ├── # Protocols (13 files)
│   ├── customization-protocol.md
│   ├── development-protocol.md
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
│       ├── run-server.sh           # MCP server launcher (handles paths with spaces)
│       └── tests/
│           ├── __init__.py
│           ├── test_build.py
│           ├── test_concat.py
│           ├── test_query.py
│           └── test_sync.py
│
├── .steering-files/                # Platform configuration (portable source of truth)
│   ├── README.md                   # Directory guide and platform setup reference
│   ├── settings/
│   │   └── mcp.json               # MCP server configurations (fetch uses security proxy)
│   ├── steering/
│   │   ├── Nathaniel.md            # Personality kernel (always-loaded)
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
    ├── setup.sh                    # First-run setup (git filters, deps, vectorstore)
    ├── setup-filters.sh            # Git sanitization filter config only
    ├── bootstrap-windows.ps1       # Windows bootstrap (Git, Python, uv, WSL, Ubuntu)
    ├── setup-wsl.ps1               # WSL environment setup (no admin needed)
    ├── teardown.ps1                # Environment teardown (PowerShell)
    ├── run-python.sh               # Python runner (venv-aware)
    ├── save-session.py             # Atomic save: all JSON mutations, index rebuilds, vectorstore sync
    ├── session-cache.py            # Session-local cached KB access (SQLite-backed, FTS5 search)
    ├── cascade-correction.py       # Scan stores for stale claims, apply fixes atomically
    ├── removal-cascade.py          # Delete entries with full cascade (store, indexes, cross-refs)
    ├── maintenance.py              # Health checks + safe auto-fixes
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
| Scripts | `scripts/` | Automation and maintenance |
