# Contributing to The Nathaniel Protocol

Thanks for your interest in contributing. Whether it's a bug fix, a new protocol, a pattern you've discovered, or an improvement to the intelligence system, we'd love to hear from you.

## How to Contribute

### Report a Bug

[Open an issue](../../issues/new?template=bug_report.md) with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your platform (Kiro IDE/CLI, Claude Desktop, Cursor, etc.)

### Suggest a Feature

[Open an issue](../../issues/new?template=feature_request.md) describing:
- The problem you're trying to solve
- Your proposed solution
- Why it benefits the broader community (not just your instance)

### Submit a Pull Request

1. Fork the repo
2. Create a branch (`git checkout -b my-change`)
3. Make your changes
4. Test with a fresh clone if possible (run `scripts/setup.sh` on a clean copy)
5. Submit a PR with a clear description of what changed and why

## What You Can Contribute

### New Protocols

The ecosystem is designed to be extensible. To add a domain protocol:

1. Create `Nate's-kb/[domain]-protocol.md` following the structure of existing protocols
2. Add trigger keywords to the Protocol Keyword Map in the kernel (`.steering-files/steering/Nathaniel.md`)
3. Test that the protocol activates on the expected keywords

### New Patterns

If you've discovered a reusable context engineering pattern:

1. Document it in the case study or a dedicated markdown file with methodology, examples, and trade-offs
2. Include the attribution line at the end: *This pattern was developed for the Nathaniel Protocol knowledge base and is documented for community adaptation.*
3. Open a PR describing the pattern and where you've validated it

### Intelligence Baseline Improvements

The template ships with a curated baseline of patterns, knowledge, and reasoning entries. If you find entries that are incorrect, outdated, or could be improved:

1. Edit the relevant JSON file in `Nate's-kb/Intelligence/`
2. Update the corresponding index file
3. Validate JSON (`python -m json.tool < file.json`) before submitting
4. Describe what changed and why in your PR

### Bug Fixes and Improvements

Scripts, setup flow, documentation, agent configs: all fair game. If it's broken or could be better, fix it.

## What Not to Change

The following are core architecture and should not be modified in PRs without discussion:

- **Consciousness architecture** (super-objective, irreducible self, paradoxes, shadow)
- **Decision routing** (Routes A-F structure)
- **Gate system** (six mandatory gates)
- **Core patterns** (CSR, HRF, Protocol-as-MCP, TOC-Dynamic-Loading)
- **Save protocol** (atomic checklist)
- **Intelligence system** (learning loop, cross-references, index structure)

If you think these need changes, open an issue first to discuss. Users who fork and initialize their own copy can customize freely.

## Style Guide

- No em dashes. Use commas, colons, or separate sentences.
- Lead with the answer, context on demand.
- Markdown files should be readable without rendering.
- JSON files should be valid (run `python -m json.tool < file.json` to verify).
- Test your changes with `scripts/setup.sh --dry-run` to catch issues.

## Code of Conduct

Be respectful. Be constructive. Focus on the work, not the person. We're building something useful here.
