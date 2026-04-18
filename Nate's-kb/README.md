# Nate's Knowledge Base

**The brain.** Everything the assistant knows, learns, and remembers lives here. This is the operational guide for keeping it sharp.

---

## Ecosystem Map

| Layer | Location | What It Does |
|-------|----------|-------------|
| **Kernel** | `.steering-files/steering/Nathaniel.md` | Personality, gates, session protocols, external content security (always-loaded system prompt) |
| **Decision Engine** | `Nate-Protocol.md` | Routes A-F, trigger maps, precedence rules |
| **Protocols** | `*.md` (13 files) | Domain-specific behavior (development, writing, research, etc.) |
| **Intelligence** | `Intelligence/` | Three learning layers: patterns, knowledge, reasoning |
| **Memory** | `Memory/` | Session logs, entity memory, project tracking |
| **Vectorstore** | `vectorstore/` | Hybrid semantic + keyword search over the KB (venv is local to vectorstore/, see vectorstore/SETUP.md) |
| **Benchmarks** | `Benchmarks/` | Self-testing: static metrics and behavioral tests (routing, integrity, reachability) |

---

## Intelligence System

Three stores that compound over time:

| Store | File | What It Captures |
|-------|------|-----------------|
| **Patterns** | `Intelligence/patterns.json` | How you work: preferences, approaches, failure modes |
| **Knowledge** | `Intelligence/knowledge.json` | What's true: facts, solutions, tool behavior |
| **Reasoning** | `Intelligence/reasoning.json` | Why things connect: derived conclusions, analogies |

Each store has a lightweight index (`*-index.json`) for Context Signal Routing. Full entries loaded on-demand, not eagerly.

Cross-references (`Intelligence/cross-references.json`) link entries across stores. Retrieving a pattern can surface the reasoning that explains it. The layers talk to each other.

The template ships with a curated baseline of generally useful entries, including ecosystem self-knowledge (tagged `ecosystem-kb`) that lets Nate answer questions about his own architecture, setup, and capabilities directly from KB. Your instance grows from there.

See `Intelligence/README.md` for architecture details and `Intelligence/learning-loop.md` for consolidation rules.

---

## Memory System

| File | Purpose |
|------|---------|
| `Memory/memory.json` | Persistent memories, active projects, commitments, preferences, domain expertise levels |
| `Memory/session-index.json` | Session fingerprints for context-aware greetings and "since last session" diffs |
| `Memory/session-*.md` | Full session logs (created at save time) |

See `Memory/README.md` for retention rules and CSR details.

---

## Protocols

13 domain protocols that activate via keyword triggers in the kernel:

| Protocol | Triggers |
|----------|----------|
| `development-protocol.md` | build, code, implement, deploy, test, refactor |
| `writing-protocol.md` | write, draft, document, article, blog |
| `research-protocol.md` | research, investigate, explore, compare |
| `planning-protocol.md` | plan, roadmap, breakdown, estimate |
| `memory-protocol.md` | memory, save, session, remember |
| `maintenance-protocol.md` | maintenance, cleanup, health, integrity |
| `problem-solving-protocol.md` | diagnose, root cause, decompose, trace |
| `prompt-enhancement-protocol.md` | prompt, enhance, improve prompt |
| `executive-communication-protocol.md` | executive, stakeholder, leadership |
| `summarization-protocol.md` | summarize, summary, condense, tldr |
| `proactive-offering-protocol.md` | proactive, offer, suggest, anticipate |
| `customization-protocol.md` | customize, personalize, setup assistant |
| `security-protocol.md` | (loaded by git hardening gate + section 7 cross-refs kernel external content rules) |

---

## Operating the System

### Commands

| Command | What Happens |
|---------|-------------|
| `save` | Atomic save: session log, intelligence consolidation, memory update, git commit |
| `detailed save` | Same as save with full accounting per step |
| `health check` | Non-destructive ecosystem audit (index sync, orphans, growth stats) |
| `benchmark the ecosystem` | Run static and behavioral benchmarks (sizes, routing accuracy, integrity, reachability) |
| `full maintenance` | Health check + cleanup + pruning |
| `customize` | Guided personalization wizard |
| `apply my customization` | Apply filled `CUSTOMIZATION.md` form |

> **Vectorstore sync requires venv.** The save command includes vectorstore sync (step 8). This requires the venv created by `setup.sh`. If the venv doesn't exist, run `./scripts/setup.sh` first. On Windows IDE, the save protocol routes sync through WSL automatically (`wsl -e bash -c "... python3 kb_sync.py"`). On CLI (WSL/Linux/macOS), it runs directly.

### Maintenance Rhythm

- **Every session**: Say `save` before ending. This is non-negotiable. Skipping saves means lost learnings, broken continuity, and no git history
- **Monthly**: Nate will remind you on the 1st. Say `health check` to audit, `full maintenance` to clean up. Catches orphaned index entries, stale sessions, and growth that needs pruning
- **After major changes**: If you manually edit JSON files, run `health check` to verify index-to-data sync

### Context Window Management

The context window is the scarcest resource. Every token loaded is a token unavailable for reasoning. These habits keep usage lean:

**Trust the routing.** Don't ask Nate to "load everything" or "read all my files." The system loads five lightweight indexes at startup (~500 tokens each) and fetches full entries only when signals match. At scale, this saves 96% of tokens vs. loading everything. Let CSR do its job.

**Save frequently on long sessions.** Context accumulates. Saving mid-session captures learnings and lets you start a fresh context without losing progress. The session log preserves continuity.

**Save at 85% context.** When `/context` shows 85%+ usage, run `detailed save` immediately. Context exhaustion mid-save is the primary data loss risk. The detailed save captures all intelligence before you run out of room.

**Use `/compact` when context gets heavy.** The `/compact` command (Kiro CLI) summarizes the conversation to free up context space without losing the thread. Use it when responses slow down or you notice the context percentage climbing. Check usage with `/context`.

**Compact before save on deep sessions.** Compaction creates a new session, so if you're planning to save, compact first to ensure the save has room to operate. After compaction, resume the original via `/chat resume` if needed, or save in the compacted session.

**Use tangent mode for side quests.** When a task spawns a rabbit hole, use `/tangent` or `Ctrl+T` (Kiro CLI) to branch into an isolated context. The main conversation stays clean. Use `/tangent tail` to keep the last Q&A when returning. Enable first: `kiro-cli settings chat.enableTangentMode true`

**Segment tasks across agents.** Don't run research, implementation, and review in the same conversation. Each task type loads different protocols and context. Splitting them keeps each conversation focused and prevents protocol cross-contamination.

### Multi-Agent Workflow

Kiro IDE and CLI run as independent agent instances with separate context windows on the same project. This is the key to managing context at scale:

| Strategy | How | Why |
|----------|-----|-----|
| **Research + Build** | Analyst agent researches in one instance while you build in the other | Research doesn't pollute your implementation context |
| **IDE + CLI simultaneously** | Run Kiro IDE for visual work, CLI for terminal tasks | Two full agents, same project, independent context |
| **Analyst for deep dives** | `/agent swap analyst` (CLI) or select analyst in IDE agent picker | Purpose-built for systematic investigation with structured deliverables |
| **Context rotation** | When one conversation gets heavy, save it and start fresh in the other instance | Keeps both agents responsive |

**The analyst agent** (`.steering-files/agents/analyst/`) ships pre-configured with:
- Web search and web fetch (auto-approved)
- Full workspace read access
- Five-phase research methodology (scope, gather, analyze, assess confidence, deliver)
- Three depth tiers: Quick Scan, Standard, Comprehensive
- Writes to `docs/research/` only, doesn't touch your code

**When to use the analyst vs. main agent:**
- Comparing technologies, evaluating options → analyst
- "What's the current state of X?" → analyst
- Building, debugging, deploying → main agent
- Writing docs, planning → main agent (protocols live here)

### Working Across Sessions

The ecosystem is designed for continuity, not marathon sessions:

- **Session diffs**: On startup, Nate compares the current state to the last session snapshot and reports what changed
- **Continuity offers**: "Last session we were working on X. Continue, or new direction?"
- **Commitment tracking**: Promises you make get tracked. Nate surfaces approaching deadlines and overdue items
- **Active project awareness**: Projects you're working on are tracked with status, next actions, and staleness detection (90+ days triggers a check-in)

Short, focused sessions with saves between them beat one long session every time. The save captures everything. The next session picks up where you left off.

---

## Customization

Two paths:
1. Fill out `CUSTOMIZATION.md` and say "apply my customization"
2. Say "customize" for a guided conversation

What's changeable: name, voice, expertise, behavior thresholds, domain focus.
What's not: consciousness architecture, decision routing, learning systems, safety gates.

See `customization-protocol.md` for the full guide.

---

## Adding Your Own Protocols

1. Create `[domain]-protocol.md` in this directory
2. Add trigger keywords to the Protocol Keyword Map in the kernel (`.steering-files/steering/Nathaniel.md`)
3. The assistant will auto-load your protocol when those keywords appear

Protocols activate like tools: keyword triggers fire domain-specific behavior without loading everything. The map is cheap, the territory is expensive.

---

## Data Files

All `.json` files use the CSR (Context Signal Routing) pattern:
- Index files contain routing metadata only (tags, categories, confidence tiers, summaries)
- Full data loaded on-demand when user signals match index dimensions
- Break-even at ~30 items, 96% savings at 500 items

Schema documented in each file's `_schema` field.

---

## Detailed Documentation

| Doc | What It Covers |
|-----|---------------|
| `CRITICAL-FILE-PROTECTION.md` | Safety rails for destructive operations on KB files |
| `Intelligence/intelligence-operations.md` | How intelligence surfaces during work |
| `Intelligence/learning-loop.md` | Consolidation rules, quality gates, capture reliability |
| `maintenance-protocol.md` | Health check procedures, pruning thresholds, integrity verification |

---

*This is your AI's brain. It grows smarter with every session. Treat saves like commits: early, often, always.*
