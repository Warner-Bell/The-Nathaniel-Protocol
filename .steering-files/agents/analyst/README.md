# Analyst

Deep research specialist that investigates topics, evaluates sources, synthesizes findings, and delivers structured research outputs with analyst-grade rigor.

## What It Does

Analyst conducts systematic research across technical, market, competitive, and strategic domains. It follows a five-phase methodology (scope, gather, analyze, assess confidence, deliver) and produces structured deliverables with explicit confidence ratings, source attribution, and gap identification.

The agent decomposes complex topics into independent research dimensions, investigates each to appropriate depth, and synthesizes across dimensions only at the end. This prevents shallow coverage and ensures balanced analysis.

Three depth tiers: Quick Scan (surface-level, 2-3 sources), Standard (findings + recommendation, 5-8 sources), Comprehensive (full multi-dimensional analysis, 10+ sources).

## Tools and Permissions

- **Read**: Full workspace read access (any file for context)
- **Write**: Restricted to `docs/research/**` only
- **Web Search**: Enabled, auto-approved
- **Web Fetch**: Enabled, auto-approved
- **Knowledge**: Enabled for knowledge base queries
- **Grep/Glob**: Enabled for workspace file discovery
- **Shell**: Not available
- **No file modifications** outside the research output directory

## Resources Loaded

- `consciousness.md`: Personality and voice (always in context)
- `specialization.md`: Research methodology, analytical frameworks, source evaluation criteria, output standards (always in context)

## Borrowed Expertise

- **Research Protocol** (Nate's KB): Five-phase research methodology, source hierarchy, credibility scoring, confidence assessment framework, output structure templates, research type classifications, anti-patterns
- **AI Research Agent Patterns** (web research): Iterative deepening strategy, dimension decomposition, verification and citation binding, critique loops, controlled aggregation, adaptive depth based on uncertainty, planner-executor orchestration patterns
- **Deep Research Engineering** (GoDaddy case study): Three-phase pipeline (planning, iterative exploration, synthesis), configurable stopping criteria (depth level, breadth per level, follow-up strategy), schema-driven decomposition, LLM-as-judge evaluation methodology

## Usage Examples

- "Research the current state of serverless container options on AWS"
- "Compare Datadog vs New Relic vs Grafana Cloud for our observability stack"
- "Deep dive into FedRAMP authorization process for SaaS vendors"
- "What are the trends in government cloud adoption for 2026?"

## Validation Checklist

- [ ] Agent loads with `analyst` name and welcome message appears
- [ ] Web search returns results when asked to research a topic
- [ ] Research output file is written to `docs/research/` with correct naming convention
- [ ] Output includes confidence rating, source attribution, and gaps section
- [ ] Agent refuses to write files outside `docs/research/`

## Maintenance Notes

- Update `specialization.md` if research methodology or output format standards change
- Update `consciousness.md` if personality/voice evolves
- Model set to `claude-opus-4.6` for deep reasoning. Adjust if cost is a concern
- `includeMcpJson: true` means workspace MCP servers (web search, fetch) are inherited automatically
