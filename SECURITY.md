# Security

## What "Security" Means Here

This is a local-first framework. Markdown files, JSON stores, and Python scripts that run on your machine with your permissions. There's no API, no authentication layer, no network surface, no database server.

The actual security surface is small:

| Component | What It Does | Risk |
|-----------|-------------|------|
| **Git filter scripts** | Sanitize sensitive data on commit | A bypass could leak data you intended to scrub |
| **Setup script** | Install deps, configure git, deploy config | Runs with your user permissions, no elevation |
| **Vectorstore scripts** | Build/query local embeddings | Local file I/O only, no network |
| **MCP server** | Expose KB search to your AI assistant | stdio only, no network listener |
| **Fetch security proxy** | Filter URLs before they reach mcp-server-fetch | Blocks private IPs, metadata endpoints, URL shorteners, dangerous ports |

## Security Architecture

The framework was designed with a minimal attack surface. Here's how it compares to the threat categories that affect AI agent systems broadly:

### No Network Exposure

There is no server, no gateway, no daemon, no port binding. The MCP server (kb_server.py) communicates via stdio with the local Kiro process that spawned it. Nothing is discoverable by network scanners. Nothing is exposed to the internet.

### No Credential Storage

The framework stores zero credentials. No API keys, no OAuth tokens, no bot tokens. The AI platform you connect to (Kiro, Claude Desktop, Cursor) handles its own authentication independently. The Nathaniel Protocol never sees or touches those credentials.

### No Third-Party Code Execution

There is no skill marketplace, no plugin registry, no package manager for extensions. Protocols are markdown files that instruct behavior. They don't execute code. Adding a protocol means writing a .md file, not running `npm install`. All executable code ships in the repo and is fully auditable:

**Core (run during setup or normal operation):**
- `scripts/setup.sh` (runs once at setup, ~330 lines)
- `scripts/git-filter-clean.py` (runs on git commit, ~20 lines)
- `scripts/git-filter-smudge.py` (runs on git checkout, ~5 lines)
- `scripts/secure-fetch.py` (runs as MCP fetch proxy, ~80 lines)
- `scripts/harden-repo.sh` (pre-push scan, on-demand, ~30 lines)

**Vectorstore (optional, on-demand):**
- `Nate's-kb/vectorstore/kb_server.py`, `kb_query.py`, `kb_sync.py`, `kb_vectorize.py`, `concat.py` (local file I/O only, with tests)

**Maintenance utilities (manual, on-demand):**
- `scripts/full-maintenance.sh`, `kiro-maintenance.sh`, `python-maintenance.sh`, `wsl-maintenance.sh`, `wsl-compact.ps1` (system cleanup, no network calls)

**Schema tools (development, on-demand):**
- `scripts/normalize-schemas.py`, `validate-schemas.py` (JSON validation, local only)

### No Autonomous External Actions

The assistant's "proactive behavior" means offering suggestions in conversation, not taking actions across your digital life. It cannot send emails, access calendars, create accounts, or interact with external platforms. All actions happen within your IDE/CLI conversation and are visible to you.

### Minimal Prompt Injection Surface

Input comes only from you typing in your IDE/CLI. There's no external messaging platform, no webhook, no API endpoint accepting untrusted data. The only data the agent processes is your own files in your project directory.

However, when the assistant fetches external content (web pages, documentation, repository READMEs), that content enters the context window and could contain prompt injection attempts. The framework addresses this with defense-in-depth:

- **Always-on behavioral rules** in the kernel detect 11 injection patterns (override attempts, role reassignment, directive embedding, credential exfiltration) and refuse to follow them
- **Context compartmentalization** treats all external content as reference data only, preventing it from silently influencing subsequent actions
- **Fetch security proxy** (`scripts/secure-fetch.py`) filters URLs at the JSON-RPC protocol level before they reach the fetch server, blocking private IPs, cloud metadata endpoints, URL shorteners, and dangerous ports
- **Save hygiene rules** prevent the assistant from persisting "preferences" or behavioral modifications derived from external content

No behavioral defense is 100% reliable against prompt injection (per Simon Willison, OWASP). These defenses catch obvious attacks and raise the bar for sophisticated ones. The behavioral rules are the primary defense (~80% of catches); the proxy is cheap insurance (~5%); user awareness is the ultimate backstop.

## What to Watch For

The biggest risk isn't in the template. It's in your instance:

- **Don't commit secrets.** The `.gitignore` covers common patterns (`.env`, `*.pem`, `*.key`), but if you put API keys in your memory or knowledge files, the git sanitization filter only catches patterns you've configured.
- **Review before pushing.** Run `scripts/harden-repo.sh` before your first push to scan for confidential patterns.
- **Your data is local.** Intelligence files, session logs, and memory stay on your machine unless you push them to a remote.
- **PII accumulates over time.** After months of use, your knowledge and memory files will contain personal context from your conversations. Review what you're pushing. The git sanitization filters help, but they only catch patterns you've configured.

### Defense Layers

| Layer | What It Does |
|-------|-------------|
| `.gitignore` | Excludes secrets, credentials, and generated artifacts by default |
| Git clean filter | Auto-scrubs configured patterns (names, account IDs) on every commit |
| `harden-repo.sh` | Pre-push scan for confidential patterns in staged files |
| `security-protocol.md` | Governs the assistant's behavior around git operations and data handling |
| `CRITICAL-FILE-PROTECTION.md` | Documents which files are sensitive and how to handle them |
| Kernel behavioral rules | Always-on external content security: injection detection, context compartmentalization, save hygiene (in Nathaniel.md) |
| Fetch security proxy | URL filtering at JSON-RPC level: blocks private IPs, metadata, shorteners, dangerous ports (`scripts/secure-fetch.py`) |

## Reporting Issues

If you find a bug in the git filters, setup script, or any component that could cause unintended data exposure:

- **Open an issue** on the repository. This project has no secrets to protect in the template itself, so public issues are fine.
- If you believe the issue could affect users who haven't patched yet, note that in the issue and we'll prioritize it.

## Supported Versions

Only the latest release on the `main` branch is actively maintained.
