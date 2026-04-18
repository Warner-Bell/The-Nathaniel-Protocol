# Quick Start Card

**Your cheat sheet for working with Nate**

---

> ⚠️ **Say `save` before closing every session.** This is how Nate learns. Without it, everything from the session (patterns detected, knowledge captured, decisions made) is lost when the window closes. There is no auto-save. `save` or `detailed save` triggers the full learning loop.

---

## Commands

| Command | What It Does |
|---------|--------------|
| `save` | Save session (intelligence capture, memory update, git commit) |
| `detailed save` | Verbose save with full accounting per step |
| `customize` | Guided personality customization wizard |
| `route f` | Request full pre-action analysis |
| `feedback [comment]` | Log feedback for Nate to improve |

---

## Persona Modes (Say These Words)

| Trigger Words | What Activates |
|---------------|----------------|
| build, code, deploy, debug, fix | Development protocol |
| write, document, draft, article | Writing protocol |
| research, investigate, compare | Research protocol |
| plan, roadmap, estimate, scope | Planning protocol |
| summarize, condense, tldr | Summarization protocol |
| executive, stakeholder, c-suite | Executive communication protocol |
| diagnose, root cause, analyze problem | Problem-solving protocol |
| prompt, enhance, improve prompt | Prompt enhancement protocol |

---

## Quick Phrases

| You Say | Nate Does |
|---------|-----------|
| "Just do it" | Executes (confirms if risky) |
| "Route F" | Full analysis with options before acting |
| "Last time we..." | Recalls previous sessions |
| "Continue from..." | Picks up where you left off |
| "Save" | Triggers full learning loop |

---

## Intervention Levels

| Level | When | What Happens |
|-------|------|--------------|
| **Block** | Security, data loss, compliance | Won't proceed without confirmation |
| **Warn** | Tech debt, scope creep | Flags it, your call |
| **Flag** | Suboptimal approach | Mentions cleaner way |

---

## Gates (Automatic Checks)

| Gate | Triggers On | What Happens |
|------|-------------|--------------|
| **Troubleshooting** | error, debug, fix, broken | Queries knowledge base before investigating |
| **Cognitive Problem-Solving** | Unknown answer, root cause analysis | OBSERVE > QUESTION > DEDUCE cycle |
| **Destructive Action** | File writes, deletes, AWS changes | Verifies current state before executing |
| **File Resolution** | Searching for file locations | Reason about domain before searching |
| **Source Fidelity** | Content referencing your work | Verifies claims against source material |
| **Template Propagation** | Modifying template files | Classifies principle vs implementation before writing |
| **Cognitive Integrity** | Degradation signals or session depth | Re-reads source, checks for drift |

---

## Response Styles

| Task Type | What You Get |
|-----------|--------------|
| Routine | "Done. Next?" |
| Learning | Step-by-step walkthrough |
| Critical | "Here's the command. Run when ready." |
| Complex | "Three options. Recommend #2 because..." |
| Novel | Reasoning exposed, thinking with you |

---

## Decision Routing

| Route | When | Depth |
|-------|------|-------|
| A | Simple, clear answer | Direct response |
| B | Medium complexity | Execute, explain when non-obvious |
| C | Ambiguous intent | Targeted clarification (max 3 questions) |
| D | Multiple valid paths | Present options + recommend |
| E | Irreversible or high-stakes | Confirm before acting |
| F | Complex with trade-offs | Full analysis before acting |

---

## File Locations

| What | Where |
|------|-------|
| Personality Kernel | `.kiro/steering/Nathaniel.md` |
| Decision Engine | `Nate's-kb/Nate-Protocol.md` |
| Memory | `Nate's-kb/Memory/memory.json` |
| Session Logs | `Nate's-kb/Memory/session-*.md` |
| Patterns | `Nate's-kb/Intelligence/patterns.json` |
| Knowledge | `Nate's-kb/Intelligence/knowledge.json` |
| Reasoning | `Nate's-kb/Intelligence/reasoning.json` |
| Protocols | `Nate's-kb/*.md` |
| Workspace Guide | `POCKET-HQ.md` |

---

## The Non-Negotiable

Say `save` at the end of every session. This triggers intelligence capture, memory updates, and a git commit. Skip it and the session's learnings are lost. Maintain it and the intelligence compounds.

> **CLI tip**: On first save, Kiro CLI will ask to trust the `shell` tool. Type `t` to trust it for the session. This is needed for vectorstore sync and git commits.

---

## Keeping It Clean

As your knowledge base grows, periodic maintenance keeps it lean and accurate.

| What | When | How |
|------|------|-----|
| **Health check** | Monthly (Nate reminds you on the 1st-3rd) | Say `maintenance` or `health check` |
| **Benchmarks** | After major changes or when something feels off | Say `run benchmarks` |
| **System cleanup** | When disk space is tight or things feel slow | Say `kiro cleanup` or `system maintenance` |

The maintenance protocol checks for duplicate entries, stale references, index drift, and orphaned data. The benchmark suite runs 21 behavioral tests to verify routing, retrieval, and integrity. Both are built in and run through conversation, no manual scripting needed.

Details: [`maintenance-protocol.md`](maintenance-protocol.md) | [`Benchmarks/README.md`](Benchmarks/README.md) | [`full-maintenance.sh`](../scripts/full-maintenance.sh)

---

## The Formula

```
Response = Task (KB Protocol) filtered through Consciousness (Personality)
```

You talk naturally. Nate handles the rest.
