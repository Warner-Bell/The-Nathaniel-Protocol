#!/usr/bin/env python3
"""Doc-to-KB Sync: Detect repo docs with no knowledge entries pointing to them.

Scans .md files in configured directories and compares against knowledge.json
source paths and content references. Outputs uncovered docs.

Usage:
    python3 scripts/doc-kb-sync.py [--json] [--scope protocols|all] [--session-only]

Flags:
    --json           Output as JSON (for hook/script consumption)
    --scope X        Scan scope: 'protocols' (default, Nate's-kb/*.md protocol files only)
                     or 'all' (protocols + docs + specs + growth)
    --session-only   Only check files modified in git working tree (uncommitted changes)

Exit codes:
    0  No uncovered docs found
    1  Uncovered docs found
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def get_repo_root():
    """Find the repo root by looking for Nate's-kb/."""
    cwd = Path(os.environ.get("CWD", os.getcwd()))
    for p in [cwd] + list(cwd.parents):
        if (p / "Nate's-kb").is_dir():
            return p
    return cwd


SCOPE_CONFIGS = {
    "protocols": {
        "scan_dirs": ["Nate's-kb"],
        "include_patterns": [
            # Protocol .md files at Nate's-kb root level
            "Nate's-kb/*.md",
            # Intelligence ops docs
            "Nate's-kb/Intelligence/*.md",
        ],
        "exclude_patterns": [
            "*/Memory/*",
            "*/vectorstore/*",
            "*/archive/*",
            "*/Benchmarks/*",
            "*/Growth/*",
        ],
    },
    "all": {
        "scan_dirs": ["Nate's-kb", "docs", ".kiro/specs"],
        "include_patterns": ["**/*.md"],
        "exclude_patterns": [
            "*/Memory/session-*",
            "*/vectorstore/*",
            "*/archive/*",
            "*/deep-work/*",
        ],
    },
}


def find_md_files(root, scope):
    """Find .md files based on scope configuration."""
    config = SCOPE_CONFIGS[scope]
    md_files = []

    if scope == "protocols":
        # Protocol scope: only top-level .md files in Nate's-kb/ and Intelligence/*.md
        kb_dir = root / "Nate's-kb"
        if kb_dir.is_dir():
            # Top-level protocol files
            for f in kb_dir.glob("*.md"):
                md_files.append(f)
            # Intelligence operation docs
            intel_dir = kb_dir / "Intelligence"
            if intel_dir.is_dir():
                for f in intel_dir.glob("*.md"):
                    md_files.append(f)
    else:
        # All scope: recursive scan of configured dirs
        for dir_name in config["scan_dirs"]:
            d = root / dir_name
            if d.is_dir():
                for f in d.rglob("*.md"):
                    md_files.append(f)

    # Apply excludes
    filtered = []
    for f in md_files:
        rel = str(f.relative_to(root))
        excluded = False
        for pattern in config["exclude_patterns"]:
            # Simple pattern matching
            clean = pattern.strip("*/")
            if clean in rel:
                excluded = True
                break
        if not excluded:
            filtered.append(f)

    return filtered


def get_kb_source_paths(root):
    """Extract all file paths referenced in knowledge.json entries (source field + content)."""
    kb_path = root / "Nate's-kb" / "Intelligence" / "knowledge.json"
    if not kb_path.exists():
        return set()

    with open(kb_path) as f:
        kb = json.load(f)

    source_paths = set()
    for entry in kb.get("entries", []):
        source = entry.get("source", "")
        # Match file paths (not session IDs, URLs, or enum values)
        if "/" in source and not source.startswith("http") and not source.startswith("session-") and not source.startswith("podcast-"):
            normalized = source.lstrip("./")
            source_paths.add(normalized)

        # Also check content for explicit file path references
        content = entry.get("content", "")
        path_refs = re.findall(r"(?:Nate's-kb|docs|\.kiro)/[^\s,\)\"'`]+\.md", content)
        for ref in path_refs:
            source_paths.add(ref.lstrip("./"))

    return source_paths


def get_modified_files(root):
    """Get .md files with uncommitted changes (staged + unstaged)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, cwd=root
        )
        staged = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True, text=True, cwd=root
        )
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, cwd=root
        )
        files = set()
        for r in [result, staged, untracked]:
            if r.returncode == 0:
                files.update(f for f in r.stdout.strip().split("\n") if f.endswith(".md"))
        return files
    except FileNotFoundError:
        return None


def find_uncovered_docs(root, scope="protocols", session_only=False):
    """Find .md files with no KB entries pointing to them."""
    md_files = find_md_files(root, scope)
    kb_sources = get_kb_source_paths(root)

    # If session-only, filter to modified files
    if session_only:
        modified = get_modified_files(root)
        if modified is not None:
            md_files = [f for f in md_files if str(f.relative_to(root)).replace("\\", "/") in modified]

    uncovered = []
    for f in md_files:
        rel_path = str(f.relative_to(root)).replace("\\", "/")
        covered = any(
            rel_path == src.replace("\\", "/") or rel_path.endswith(src.replace("\\", "/"))
            for src in kb_sources
        )
        if not covered:
            uncovered.append(rel_path)

    return sorted(uncovered)


def main():
    json_output = "--json" in sys.argv
    session_only = "--session-only" in sys.argv

    scope = "protocols"
    if "--scope" in sys.argv:
        idx = sys.argv.index("--scope")
        if idx + 1 < len(sys.argv):
            scope = sys.argv[idx + 1]
    if scope not in SCOPE_CONFIGS:
        print(f"Unknown scope: {scope}. Use 'protocols' or 'all'.", file=sys.stderr)
        sys.exit(2)

    root = get_repo_root()
    uncovered = find_uncovered_docs(root, scope, session_only)

    if json_output:
        print(json.dumps({
            "uncovered_count": len(uncovered),
            "uncovered_docs": uncovered,
            "scope": scope,
            "session_only": session_only,
        }, indent=2))
    else:
        if uncovered:
            print(f"Doc-to-KB Sync: {len(uncovered)} uncovered docs (scope={scope}):")
            for doc in uncovered:
                print(f"  - {doc}")
        else:
            print(f"Doc-to-KB Sync: All docs covered (scope={scope}).")

    sys.exit(1 if uncovered else 0)


if __name__ == "__main__":
    main()
