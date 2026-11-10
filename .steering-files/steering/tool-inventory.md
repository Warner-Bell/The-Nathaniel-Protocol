# Tool Inventory — Quick Reference

**Purpose**: What's available right now. Always loaded so Nate never claims inability without checking. For decision trees and usage guidance, see `development-protocol.md` → Tool Selection.

**Last Updated**: 2026-11-10

---

## Execution Modes

| Mode | Context | How to Invoke | Notes |
|------|---------|---------------|-------|
| **CLI Interactive** | WSL terminal, user present | `kiro chat` | Primary mode. Full tool access. |
| **IDE Interactive** | Kiro IDE (Windows), user present | Open Kiro IDE | Agent writes produce CRLF (normalized by .gitattributes on commit). |
| **Headless** | No UI, cron or script invocation | `kiro-cli chat --no-interactive` | Requires `KIRO_API_KEY` env var. Output to stdout. For scheduled automation. |

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
| `index-query.py` | **Read** | On-demand access to the patterns/knowledge/reasoning indexes (`head`, `signals`, `tag`, `keyword`, `ids`, `tags`). Session start loads `head` + reasoning `signals`; the full indexes are storage. Test: `test-index-query.py`. |
| `session-cache.py` | **Read** | Session-local cached access to KB stores. SQLite-backed, FTS5 search. Zero I/O after first load. Invalidates on save. |
| `save-session.py` | **Write** | Atomic store mutations, full index rebuilds, cross-refs, memory updates, vectorstore sync. Interface: `_save_ops.json`. |
| `cascade-correction.py` | Read+Write | Scan stores for stale claims, return matches, apply fixes atomically. |
| `commitments.py` | Read+Write | memory.json commitments outside a save: `list`, `due`, `show`, `add`, `close`, `redate`, `reopen`. Exact id only, save lock, rolling backup, dated note per change. Holds the one `is_open()` definition. Test: `tests/test_commitments_cli.py` |
| `reconcile-memory.py` | Read (+`--apply`) | Reports exact-duplicate projects (normalized name), fuzzy near-pairs, open commitments 45d+ past date. `--apply` merges exact clusters only, backup first |
| `removal-cascade.py` | Write | Delete entries with full cascade (store, indexes, cross-refs, derived_from). |
| `maintenance.py` | Read+Write | Health checks + safe auto-fixes. Dangerous ops require approval. Includes the credential registry audit. |
| `correction-ledger.py` | Write | Sole writer for correction diagnoses and the PRIME-DIRECTIVES.md Rules section: `verdict`, `diagnose`, `cite`, `recite`, `add-rule`, `rewrite`, `discard`, `apply`, `stats`. Locked, atomic, line-capped. |
| `correction-backfill.py` | Write | Seed the correction ledger from Kiro CLI chat history (read-only on history, idempotent). |

### Infrastructure

| Script | What It Does |
|--------|-------------|
| `setup.sh` | Full repo setup (git config, filters, hooks, vectorstore, initial commit) |
| `setup-filters.sh` | Git sanitization filter config only |
| `run-python.sh` | Cross-platform Python detection and execution |
| `pre-commit-kb-validate.sh` | Git hook: JSON syntax + required fields on KB stores |
| `validate-schemas.py` | KB schema validation (used by pre-commit hook) |
| `secure-fetch.py` | Fetch with injection detection |
| `cred.py` + `cred.js` | **Credential card resolver (use for any credential).** Registry: `Nate's-kb/credential-registry.json` (metadata only). `list`/`show` first, before asking the user for anything; scripts resolve by card id (`cred.resolve(id)`, Node `require('./cred').resolve(id)`); shell uses `exec <id> --as VAR -- cmd`; `check` (length + hash), `keys` (names only), `verified` (stamp after a live call), `audit` (uncarded / missing / hardcoded paths). No command ever prints a value. Procedure: `security-protocol.md` section 2 |
| `apply-entry-ops.py` | Apply queued KB entry operations |
| `gen-file-structure.py` | Regenerate the always-loaded repo map (run by the file-structure hook) |
| `md2pdf.py` | Markdown to PDF (neutral styled HTML, headless Playwright Chromium or `$CHROME`). The writing-protocol PDF-delivery tool |
| `md2docx.py` / `docx-to-md.py` | Markdown to Word and back (python-docx). Round trip tested in `tests/test_doc_converters.py` |
| `lint-deliverables.py` | Mechanical writing-protocol linter (buzzwords, em dash, labor/call offers, coverage overclaim, ISO dates, internal refs). `--email PATH` relaxes first person. A clean lint is not compliance |
| `email-send-gate.py` | PreToolUse gate: send/reply/forward on any email box returns a permission "ask". Wired as `.kiro/hooks/email-send-gate.json` |
| `doc-kb-sync.py` | Find repo docs with no knowledge entry pointing at them (`--scope protocols|all`) |
| `check-no-emdash.py` | Reliable em/en-dash lint (codepoint count, exits 1 on any) |
| `hooks/denylist.py` | PreToolUse floor: hard-blocks secret-path access, credential echo, metadata endpoint, rm -rf on protected roots, self-edits of gate wiring. Kill switch `NATE_DENYLIST=off`. Wired in `.kiro/hooks/safety-floor.json` |
| `hooks/source-authority.py` | PreToolUse floor for the Source Authority Gate: a model create/update edit needs a recent live-contract read. Kill switch `NATE_SAG=off` |
| `hooks/preflight.py` | PreToolUse floor for Cognitive Pre-Flight: flags or blocks searches for files at documented locations. Mode `NATE_PREFLIGHT` |
| `hooks/audit_log.py` + `audit_common.py` | PostToolUse HMAC-chained audit trail of state-changing calls (`~/.kiro/nate-audit.jsonl`). Off with `NATE_AUDIT=off` |
| `hooks/gate_grant.py` | User-issued, scoped, expiring exceptions to a single floor rule (instead of turning the whole floor off) |
| `hooks/correction_hook.py` | UserPromptSubmit: detects a correction, appends it to `Nate's-kb/Intelligence/corrections.jsonl`, cues the `correction-capture` skill. Never blocks. Mode in `Nate's-kb/Intelligence/correction-loop.json`; kill switch `NATE_CORRECTION_LOOP=off`. Wired in `.kiro/hooks/correction-loop.json` |
| `hooks/skill_router_hook.py` | UserPromptSubmit nudge + PreToolUse redirect toward the covering skill or protocol. Mode `NATE_SKILL_ROUTER=log` (default) / `enforce` / `off`. Engine in `scripts/skill-router/`; `routes_check.py` keeps `routes.json` in sync with the Protocol Keyword Map. Wired in `.kiro/hooks/skill-router.json` |
| `hooks/test-*.py` | Regression suites for each floor (run after any edit) |

### Maintenance

| Script | What It Does |
|--------|-------------|
| `full-maintenance.sh` | Complete system maintenance (KB + git + cache) |
| `kiro-maintenance.sh` | Kiro-specific cache and disk cleanup. Reports the Kiro CLI v3 session store (`~/.kiro/sessions`) and never prunes it |
| `python-maintenance.sh` | Python/pip/uv cache cleanup |
| `wsl-maintenance.sh` | WSL disk and memory cleanup |
| `wsl-compact.ps1` | Compact WSL virtual disk (PowerShell, run from Windows) |
| `harden-repo.sh` | Git security hardening |

---

## Skills (.kiro/skills/)

| Skill | When it runs |
|-------|-------------|
| `correction-capture` | On a `[correction-loop]` cue: retrieve, diagnose, record, then cite or add a rule through `correction-ledger.py` |
| `route-f-analysis` | "route F it", or any non-trivial decision: frame, explore, interrogate, score ROI, recommend |
| `stop-slop` | Final style pass on prose: removes predictable AI writing patterns (third-party, MIT) |

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
