#!/usr/bin/env python3
"""Reliable em/en-dash lint. Exits 1 if any U+2014 (em dash) or U+2013 (en dash) is found.

Why this exists: em dashes violate a hard style rule but keep slipping into generated files, and a
grep hex-byte check (grep -P '\\xe2\\x80\\x94') gives FALSE PASSES on multi-byte UTF-8 in some
locales (observed 2026-07-21). Unicode codepoint counting in Python is the reliable detector.
Behavioral instruction degrades (know-001); this is the structural enforcement.

Usage:
  python3 scripts/check-no-emdash.py [path ...]     # default: current directory, recursive
Wire into the save flow (optional) to block a save when dashes are present.
"""
import os
import sys
from pathlib import Path

EM, EN = "\u2014", "\u2013"
SKIP = {"__pycache__", ".pytest_cache", ".git", "node_modules", ".venv", "vectorstore"}
BINARY_SUFFIXES = {".gz", ".tar", ".zip", ".png", ".jpg", ".jpeg", ".pdf", ".faiss", ".bin", ".pyc"}


def scan(paths, fix=False):
    hits = []
    roots = [Path(p) for p in paths] or [Path(".")]
    for root in roots:
        if root.is_file():
            files = [root]
        else:
            # Prune SKIP dirs DURING traversal. rglob("*") descends into
            # .venv/.git/__pycache__ and stats every file before the per-file
            # SKIP filter drops it; on a DrvFs/9p mount that is ~15k slow stat
            # calls (~96s) and blows the 30s hook timeout. os.walk lets us prune
            # dirnames in place so those trees are never entered.
            files = []
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in SKIP]
                files.extend(Path(dirpath) / n for n in filenames)
        for f in files:
            if not f.is_file() or any(s in f.parts for s in SKIP) or f.suffix in BINARY_SUFFIXES:
                continue
            try:
                text = f.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            em, en = text.count(EM), text.count(EN)
            if em or en:
                if fix:
                    f.write_text(text.replace(" " + EM + " ", ", ").replace(EM, ", ").replace(EN, "-"))
                hits.append((str(f), em, en))
    return hits


def main(argv):
    fix = "--fix" in argv
    argv = [a for a in argv if a != "--fix"]
    hits = scan(argv or [], fix=fix)
    if not hits:
        print("OK: no em/en dashes found")
        return 0
    verb = "FIXED" if fix else "FAIL"
    print(f"{verb}: prohibited dashes (em U+2014 / en U+2013):")
    for path, em, en in hits:
        print(f"  {path}: em={em} en={en}" + (" -> normalized" if fix else ""))
    # After --fix, files are clean, so a hook that fixes should NOT block; return 0.
    return 0 if fix else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
