# .steering-files

Source of truth for platform configuration. The setup script (`scripts/setup.sh`) copies this directory to `.kiro/` on first run. Edits here propagate on next setup; edits in `.kiro/` are local overrides.

## Directory Structure

```
.steering-files/
├── steering/
│   └── Nathaniel.md          # The kernel. Personality, gates, session protocols.
├── agents/
│   ├── analyst.json           # Agent config (name, tools, model, permissions)
│   └── analyst/
│       ├── README.md          # Agent documentation and validation checklist
│       ├── analyst-prompt.md  # Role instructions and research workflow
│       ├── consciousness.md   # Personality extract (shared voice across agents)
│       └── specialization.md  # Research methodology and output standards
├── settings/
│   └── mcp.json               # MCP server config (time, fetch, kb-vectorstore)
└── README.md                  # This file
```

## Key Files

| File | What It Does | Edit Frequency |
|------|-------------|----------------|
| `steering/Nathaniel.md` | Defines who the assistant is and how it operates. Loaded every session. | Rarely (customization wizard handles most changes) |
| `agents/analyst.json` | Configures the research agent: tools, permissions, model, write restrictions. | Only to change model or add tools |
| `agents/analyst/consciousness.md` | Personality voice shared across all agents. Keeps the analyst sounding like Nate. | Only if you customize the main kernel's voice |
| `agents/analyst/specialization.md` | Research methodology, source evaluation, output templates. | When refining research standards |
| `settings/mcp.json` | MCP servers available to all agents. Ships with time, fetch (via security proxy), and kb-vectorstore. | When adding MCP servers |

## Platform Setup

See the main [README](../README.md#-platform-setup) for instructions on using these files with Kiro, Claude Desktop, Cursor, and other platforms.

## Adding Agents

1. Create `agents/your-agent.json` with name, tools, model, and prompt path
2. Create `agents/your-agent/` directory with prompt and resource files
3. Include `consciousness.md` as a resource to inherit the shared voice
4. Run `scripts/setup.sh` to deploy to `.kiro/`

See `agents/analyst.json` and `agents/analyst/README.md` as reference implementations.
