#!/usr/bin/env python3
"""Apply new_knowledge + entry_updates outside a session save.

Imports save-session.py and calls its own write functions so the
locking, ID-collision guard, and index rebuilds are the prescribed script's, not
hand-rolled. Used for correction/supersession work that shouldn't fabricate a
session index entry.

Usage: python3 scripts/apply-entry-ops.py OPS_FILE [--dry-run]
"""

import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
save_mod = import_module("save-session")

STORES = ("patterns", "knowledge", "reasoning")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("Usage: python3 scripts/apply-entry-ops.py OPS_FILE [--dry-run]")
        sys.exit(2)

    save_mod.DRY_RUN = "--dry-run" in sys.argv[1:]

    ops = save_mod.load_json(args[0])
    if ops is None:
        print(f"ERROR: could not load {args[0]}", file=sys.stderr)
        sys.exit(2)

    kb = save_mod.find_kb_root()
    print(f"KB: {kb}")
    if save_mod.DRY_RUN:
        print("=== DRY RUN ===")

    valid_ids = save_mod._all_intel_ids(kb)
    for s in STORES:
        valid_ids.update(e.get("id") for e in save_mod.get_entries(ops, s) if e.get("id"))

    failed = []
    lock_path = kb / "Intelligence" / "stores"
    with save_mod.FileLock(lock_path):
        for store in STORES:
            new = save_mod.get_entries(ops, store)
            updates = ops.get("entry_updates", {}).get(store, [])
            if not new and not updates:
                continue
            print(f"\n{store.title()}")

            added, ok = save_mod.add_entries(kb, store, new)
            if not ok:
                failed.append(store)
                continue

            if updates:
                _, upd_ok = save_mod.apply_entry_updates(kb, store, updates, valid_ids)
                if not upd_ok:
                    failed.append(f"{store}_updates")

            save_mod.rebuild_index(kb, store)

        new_r = save_mod.get_entries(ops, "reasoning")
        if new_r:
            print("\nCross-References")
            save_mod.update_cross_references(kb, new_r)

    print()
    if failed:
        print(f"PARTIAL: failed on {failed}")
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
