# .steering-files

Source of truth for platform configuration. The setup script (`scripts/setup.sh`) copies this directory to `.kiro/` on first run and never overwrites a file that already exists there, so edits in `.kiro/` are local overrides. To take a new release, run `scripts/setup.sh --upgrade`: it backs up `.kiro/` to `.kiro.backup-<timestamp>/`, then overwrites it from here.

## Directory Structure

```
.steering-files/
├── steering/                  # Always-loaded (inclusion: always)
│   ├── Nathaniel.md           # Kernel: identity, voice, anti-patterns, session lifecycle, self-checks
│   ├── ecosystem-operation.md # Kernel: operating principles, gates, Protocol Keyword Map, KB map
│   ├── PRIME-DIRECTIVES.md    # Kernel: compliance directive + Rules (written by scripts/correction-ledger.py)
│   ├── source-authority-gate.md # Kernel: authority ladder, one-strike rule, context-depth rungs
│   ├── tool-inventory.md      # What tools and scripts exist
│   └── FILE-STRUCTURE.md      # Repo map (regenerated into .kiro/steering/ by a hook)
├── agents/
│   ├── analyst.json           # Agent config (name, tools, model, permissions)
│   └── analyst/
│       ├── README.md          # Agent documentation and validation checklist
│       ├── analyst-prompt.md  # Role instructions and research workflow
│       ├── consciousness.md   # Personality extract (shared voice across agents)
│       └── specialization.md  # Research methodology and output standards
├── hooks/
│   ├── file-structure.json    # Kiro CLI v3 workspace hook: refresh FILE-STRUCTURE.md (SessionStart, PostToolUse write)
│   ├── kb-consultation-gate.json  # Kiro CLI v3 workspace hook: per-turn KB reminder (UserPromptSubmit)
│   ├── safety-floor.json      # Kiro CLI v3 workspace hooks: deterministic floor (scripts/hooks/: denylist, source-authority, preflight, audit log)
│   ├── correction-loop.json   # Kiro CLI v3 workspace hook: capture user corrections (UserPromptSubmit)
│   ├── skill-router.json      # Kiro CLI v3 workspace hooks: route requests and raw searches to the covering skill (log mode)
│   ├── email-send-gate.json   # Kiro CLI v3 workspace hook: ask before any email send/reply/forward
│   └── nate-session-gate.kiro.hook  # Kiro IDE version of the same KB reminder
├── skills/
│   ├── correction-capture/SKILL.md  # Runs on a [correction-loop] cue: retrieve, diagnose, record, cite/add rule
│   ├── route-f-analysis/SKILL.md    # Full pre-action analysis for non-trivial decisions
│   └── stop-slop/                   # Third-party (MIT, keep its LICENSE): AI-writing-pattern removal
├── settings/
│   └── mcp.json               # MCP server config (time, fetch, kb-vectorstore)
└── README.md                  # This file
```

## Key Files

| File | What It Does | Edit Frequency |
|------|-------------|----------------|
| `steering/Nathaniel.md` | Defines who the assistant is and how it operates. Loaded every session. | Rarely (customization wizard handles most changes) |
| `steering/ecosystem-operation.md` | The mandatory gates and the Protocol Keyword Map. Add a keyword row here when you add a protocol, then add the same protocol to `scripts/skill-router/routes.json` (`routes_check.py` fails until both agree). | When adding a protocol |
| `steering/PRIME-DIRECTIVES.md` | Compliance rules. The Rules section is written only by `scripts/correction-ledger.py`, never by hand edits from the agent. | Through the correction loop |
| `skills/*/SKILL.md` | Agent skills. The skill router reads each `name` + `description` frontmatter live, so a new skill is routable as soon as setup deploys it. | When adding a skill |
| `agents/analyst.json` | Configures the research agent: tools, write restrictions, and the v3 `permissions` block. No model pin, so it uses your Kiro default (pinned models get retired; check `kiro-cli chat --list-models` before pinning one). | Only to pin a model or add tools |
| `hooks/*.json` | Kiro CLI v3 workspace hooks. They apply to every agent in the workspace, so they are not repeated inside agent configs. Each hook has a kill switch env var (`NATE_DENYLIST`, `NATE_SAG`, `NATE_PREFLIGHT`, `NATE_AUDIT`, `NATE_CORRECTION_LOOP`, `NATE_SKILL_ROUTER`). The denylist blocks the agent from editing `.kiro/hooks/*.json`, so hook changes are yours to make. | When adding a hook |
| `agents/analyst/consciousness.md` | Personality voice shared across all agents. Keeps the analyst sounding like Nate. | Only if you customize the main kernel's voice |
| `agents/analyst/specialization.md` | Research methodology, source evaluation, output templates. | When refining research standards |
| `settings/mcp.json` | MCP servers available to all agents. Ships with time, fetch (via security proxy), and kb-vectorstore. | When adding MCP servers |

## Platform Setup

See the main [README](../README.md#-platform-setup) for instructions on using these files with Kiro, Claude Desktop, Cursor, and other platforms.

## Adding Agents

1. Create `agents/your-agent.json` with name, tools, model, and prompt path
2. Create `agents/your-agent/` directory with prompt and resource files
3. Include `consciousness.md` as a resource to inherit the shared voice
4. Run `scripts/setup.sh` to deploy to `.kiro/`, then `kiro-cli agent validate --path .kiro/agents/your-agent.json`
5. On Kiro CLI v3, `kiro-cli agent upgrade .kiro/agents` converts an older-format config to the universal format (it backs up the original)

See `agents/analyst.json` and `agents/analyst/README.md` as reference implementations.

## Adding Skills

1. Create `skills/your-skill/SKILL.md` with `name:` and `description:` frontmatter. The description is what the skill router matches on, so name the requests it should catch.
2. Run `scripts/setup.sh` (or `--upgrade`) to deploy it to `.kiro/skills/`.
3. Run `python3 scripts/hooks/test-skill-router.py`. To lock in routing, add labeled rows for the new skill to `scripts/skill-router/corpus.jsonl`.
