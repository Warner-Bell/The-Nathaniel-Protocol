# Tool Inventory — Quick Reference

**Purpose**: What's available right now. Always loaded so Nate never claims inability without checking. For decision trees and usage guidance, see `development-protocol.md` → Tool Selection.

**Last Updated**: 2026-04-17

---

## Execution Modes

| Mode | Context | How to Invoke | Notes |
|------|---------|---------------|-------|
| **CLI Interactive** | WSL terminal, user present | `kiro chat` | Primary mode. Full tool access. |
| **IDE Interactive** | Kiro IDE (Windows), user present | Open Kiro IDE | Agent writes produce CRLF (normalized by .gitattributes on commit). |
| **Headless** | No UI, Pulse/cron invocation | `kiro-cli chat --agent nate --no-interactive` | Requires `KIRO_API_KEY` env var. Output to stdout. For Pulse automation. |

---

## Python Routing (Battle-Tested)

| Context | Command | Why |
|---------|---------|-----|
| **CLI (WSL)** | `python3` | Native Linux Python. Primary. |
| **IDE (Windows agent)** | `wsl python3 scripts/<name>.py` | Native Windows Python lacks `fcntl` (POSIX locking). Must route through WSL. |
| **Fallback chain** | `python3` → `python` → error | Some systems alias differently. Never use bare `python` first (may hit Windows Store stub that hangs). |
| **Scripts calling Python** | Use `scripts/run-python.sh` | Auto-detects platform, handles fallback. |

---

## Built-in Kiro Tools (Platform-Injected)

These are always available. Platform injects descriptions automatically.

| Tool | What It Does |
|------|-------------|
| `fs_read` | Read files (Line, Directory, Search, Image modes) |
| `fs_write` | Create, edit, append files (str_replace, insert) |
| `execute_bash` | Run shell commands |
| `grep` | Regex text search across files |
| `glob` | Find files by pattern |
| `code` | AST code intelligence (7 ops: search_symbols, lookup_symbols, get_document_symbols, pattern_search, pattern_rewrite, generate_codebase_overview, search_codebase_map) |
| `web_search` | Internet search |
| `web_fetch` | Fetch URL content (selective, truncated, full modes) |
| `use_subagent` | Delegate to specialized subagents |
| `delegate` | Async background agent tasks |
| `session` | Temporary session settings |
| `introspect` | Query Kiro's own features and commands |
| `report_issue` | File GitHub issue with context |

**Platform commands** (not tools, typed in chat):
- `/compact` — Compress context when approaching limits
- `/context` — Monitor context pressure
- `/code init` — Initialize LSP for full code intelligence
- `/plan` (Shift+Tab) — Structured requirements gathering (read-only)
- `/model` — Check current model

---

## Custom Scripts (scripts/)

### Intelligence Operations (Three Primitives)

| Script | Primitive | What It Does |
|--------|-----------|-------------|
| `session-cache.py` | **Read** | Session-local cached access to KB stores. SQLite-backed, FTS5 search. Zero I/O after first load. Invalidates on save. |
| `save-session.py` | **Write** | Atomic store mutations, full index rebuilds, cross-refs, memory updates, vectorstore sync. Interface: `_save_ops.json`. |
| `cascade-correction.py` | Read+Write | Scan stores for stale claims, return matches, apply fixes atomically. |
| `removal-cascade.py` | Write | Delete entries with full cascade (store, indexes, cross-refs, derived_from). |
| `maintenance.py` | Read+Write | Health checks + safe auto-fixes. Dangerous ops require approval. |

### Infrastructure

| Script | What It Does |
|--------|-------------|
| `setup.sh` | Full repo setup (git config, filters, hooks, vectorstore, initial commit) |
| `setup-filters.sh` | Git sanitization filter config only |
| `run-python.sh` | Cross-platform Python detection and execution |
| `pre-commit-kb-validate.sh` | Git hook: JSON syntax + required fields on KB stores |
| `validate-schemas.py` | KB schema validation (used by pre-commit hook) |
| `secure-fetch.py` | Fetch with injection detection |

### Maintenance

| Script | What It Does |
|--------|-------------|
| `full-maintenance.sh` | Complete system maintenance (KB + git + cache) |
| `kiro-maintenance.sh` | Kiro-specific cache and disk cleanup |
| `python-maintenance.sh` | Python/pip/uv cache cleanup |
| `wsl-maintenance.sh` | WSL disk and memory cleanup |
| `wsl-compact.ps1` | Compact WSL virtual disk (PowerShell, run from Windows) |
| `harden-repo.sh` | Git security hardening |

---

## MCP Servers

| Server | Key Tools | What It Does |
|--------|-----------|-------------|
| **kb-vectorstore** | `kb_search`, `kb_sync`, `kb_rebuild` | Local FAISS vectorstore for hybrid semantic search over KB |
| **time** | `get_current_time`, `convert_time` | Timezone-aware time (mandatory for greeting) |
| **fetch** | `fetch` | URL fetching via secure-fetch.py (injection detection) |

Users can add more MCP servers via `.steering-files/settings/mcp.json`. See [Kiro MCP docs](https://docs.kiro.dev) for available servers.

---

## Cross-Platform Gotchas

| Issue | Prevention |
|-------|------------|
| `python3` hangs on Windows | Windows Store stub. Use `wsl python3` from IDE. |
| `fcntl` import error | Script running in native Windows Python. Must use WSL. |
| Apostrophes in paths break bash for-loops | Use `while read` loops, not `for f in`. |
| Symlinks on NTFS silently fail | Use `--copies` for venvs on mounted drives. |
| Three path styles coexist | `/mnt/h/` (WSL), `H:\` (Windows), `/h/` (Git Bash). Pick one per context. |
| inotify broken on /mnt/ DrvFs | File watchers won't work on Windows-mounted drives from WSL. |
| IDE agent writes produce CRLF | .gitattributes normalizes on commit. Don't add CRLF hooks. |
| `str_replace` fails silently on large JSON | Use `execute_bash` + python/jq for files over 400 lines. |
| `fetch` can crash mid-session | Use `execute_bash` + curl as fallback. |
