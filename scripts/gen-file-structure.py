#!/usr/bin/env python3
"""Canonical generator for the repository map.

Writes .kiro/steering/FILE-STRUCTURE.md (steering => always loaded into context).
Single source of truth, called by:
  - Kiro agent JSON hooks: postToolUse(fs_write) + agentSpawn (auto-update on file actions / session start)
  - scripts/save-session.py (save step 5d)
  - manual runs: python3 scripts/gen-file-structure.py

Resolves repo root from its own location, so it is cwd-independent (hooks run from arbitrary cwd).

CUSTOMIZATION: Edit the ROUTING table below to match your repository's domain structure.
The directory tree is generated automatically. Run once after cloning to initialize.
"""
import os
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / ".steering-files" / "steering" / "FILE-STRUCTURE.md"
EXCLUDE = {'.git', 'node_modules', '__pycache__', 'cdk.out', '.venv', '.aws-sam',
           '.hypothesis', '.pytest_cache', '*.egg-info'}

HEADER = """---
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

"""

# ROUTING TABLE — edit these rows to match your repository's domain structure.
# Format: ("Domain Label", "Root Path/", "Description of what lives here")
# The path is relative to the repo root. Used to build the routing table in the map.
ROUTING = [
    ("AI/KB", "Nate's-kb/", "Protocols, intelligence, memory, sessions"),
    ("Config", ".kiro/", "Agents, specs, steering, settings, hooks"),
    ("Scripts", "scripts/", "Utility scripts, maintenance, setup"),
    # Add your own domains here, for example:
    # ("Projects", "projects/", "Code projects and specs"),
    # ("Docs", "docs/", "Documentation and reference"),
    # ("Data", "data/", "Data files and datasets"),
]


def tree(path, prefix='', depth=0, max_depth=2):
    if depth > max_depth:
        return []
    lines = []
    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        return lines
    dirs = [e for e in entries if os.path.isdir(os.path.join(path, e))
            and e not in EXCLUDE and not e.startswith('.git')]
    for i, d in enumerate(dirs):
        connector = '└── ' if i == len(dirs) - 1 else '├── '
        lines.append(f'{prefix}{connector}{d}/')
        extension = '    ' if i == len(dirs) - 1 else '│   '
        lines.extend(tree(os.path.join(path, d), prefix + extension, depth + 1, max_depth))
    return lines


def generate():
    lines = tree(str(REPO_ROOT), max_depth=2)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(HEADER)
        f.write(f"_Auto-generated. Last updated: {date.today()}_\n\n")
        f.write("## Path Routing Table\n\n| Domain | Root Path | When to Look Here |\n")
        f.write("|--------|-----------|-------------------|\n")
        for domain, p, desc in ROUTING:
            f.write(f"| {domain} | {p} | {desc} |\n")
        f.write("\n## Directory Tree\n\n```\n")
        f.write('\n'.join(lines))
        f.write("\n```\n")
    return len(lines)


if __name__ == "__main__":
    n = generate()
    print(f"FILE-STRUCTURE.md regenerated -> {OUT} ({n} entries)")
