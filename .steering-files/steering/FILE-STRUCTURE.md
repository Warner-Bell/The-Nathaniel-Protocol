---
inclusion: always
---

# FILE-STRUCTURE.md — Repository Map (steering, always-loaded)

> **RULE — consult before acting.** This map is the filesystem source of truth and is
> in context every turn. Before ANY action that LOCATES a file/directory (or decides
> where to create one), consult this map FIRST. Do NOT reach for find/grep/glob to
> discover where something lives — that is the tool-reach failure.
> grep/find are only for searching *content within* an already-known file. If a path is
> genuinely not in this map, then a search is warranted.
>
> **Auto-maintained** by `scripts/gen-file-structure.py`: on every `fs_write`
> (postToolUse hook), at agent spawn, and on every save. Do not hand-edit the tree.

_Auto-generated. Last updated: 2026-07-15_

## Path Routing Table

| Domain | Root Path | When to Look Here |
|--------|-----------|-------------------|
| AI/KB | Nate's-kb/ | Protocols, intelligence, memory, sessions |
| Config | .kiro/ | Agents, specs, steering, settings, hooks |
| Scripts | scripts/ | Utility scripts, maintenance, setup |

## Directory Tree

```
├── .kiro/
│   └── steering/
├── .steering-files/
│   ├── agents/
│   │   └── analyst/
│   ├── hooks/
│   ├── settings/
│   ├── specs/
│   └── steering/
├── Archive/
├── Brand/
├── Business/
├── Life/
│   ├── Career/
│   ├── Education/
│   ├── Family/
│   ├── Finances/
│   ├── Goals/
│   ├── Health/
│   ├── Home/
│   └── Journal/
├── Nate's-kb/
│   ├── Benchmarks/
│   ├── Intelligence/
│   ├── Memory/
│   │   ├── archive/
│   │   └── cache/
│   ├── patterns/
│   └── vectorstore/
│       └── tests/
├── Projects/
├── docs/
│   └── research/
├── scripts/
└── tests/
```
