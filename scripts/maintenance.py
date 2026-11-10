#!/usr/bin/env python3
"""
Maintenance Script - Health checks and safe auto-fixes for KB stores.

Modes:
  check: Report issues without fixing
  fix:   Apply safe auto-fixes, report items needing review

Usage: python3 scripts/maintenance.py '{"mode": "check|fix", "scope": "all|patterns|knowledge|reasoning"}'
Exit codes: 0 = clean/fixed, 1 = issues need review, 2 = error
"""

import json, sys, os, re, datetime, time as _time
from pathlib import Path
from collections import Counter

# Intelligence-store ID shapes. A derived_from ref matching one of these SHOULD
# resolve to a live entry; if it doesn't, the source was pruned and the ref is dead.
# Session IDs (session-*) and file-path refs (docs/*.md#anchor) are valid provenance.
INTEL_ID = re.compile(r"^(know-|fail_|pref_|tech_|approach_|reason-|diagnostics_|org_)\d")
PROVENANCE_FILE_SUFFIXES = {".md", ".py", ".ts", ".tsx", ".js", ".txt", ".json", ".yaml", ".yml",
                            ".sh", ".ps1", ".pdf", ".docx", ".xlsx", ".csv", ".ics", ".html"}

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module
save_mod = import_module("save-session")

STORE_NAMES = ("patterns", "knowledge", "reasoning")
JACCARD_THRESHOLD = 0.8


def tokenize(text):
    """Simple whitespace tokenizer for Jaccard similarity."""
    return set(text.lower().split())


def jaccard(a, b):
    """Jaccard token overlap between two strings."""
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def check_store(kb, store_name, fix=False):
    """Run health checks on a store. Returns (auto_fixed, needs_review)."""
    path = kb / "Intelligence" / f"{store_name}.json"
    data = save_mod.load_json(path)
    if data is None:
        return [], [{"type": "missing_store", "detail": f"{store_name}.json not found"}]

    entries = data.get("entries", [])
    index_path = kb / "Intelligence" / f"{store_name}-index.json"
    idx = save_mod.load_json(index_path) or {}

    auto_fixed = []
    needs_review = []
    changed = False
    today = save_mod.get_today()

    for entry in entries:
        eid = entry.get("id", "?")

        # lastAccessed < created
        created = entry.get("created", "")
        accessed = entry.get("lastAccessed", "")
        if created and accessed and accessed < created:
            if fix:
                entry["lastAccessed"] = created
                changed = True
            auto_fixed.append({"id": eid, "type": "lastAccessed_before_created",
                              "detail": f"lastAccessed {accessed} < created {created}"})

        # accessCount < 0
        ac = entry.get("accessCount", 0)
        if ac < 0:
            if fix:
                entry["accessCount"] = 0
                changed = True
            auto_fixed.append({"id": eid, "type": "negative_accessCount", "detail": f"accessCount was {ac}"})

        # Duplicate tags
        tags = entry.get("tags", [])
        if len(tags) != len(set(tags)):
            if fix:
                entry["tags"] = sorted(set(tags))
                changed = True
            auto_fixed.append({"id": eid, "type": "duplicate_tags", "detail": f"had {len(tags)} tags, {len(set(tags))} unique"})

        # Low confidence candidates
        conf = entry.get("confidence", 0.5)
        if conf < 0.3:
            needs_review.append({"id": eid, "type": "low_confidence", "detail": f"confidence {conf}"})

        # Stale candidates (accessCount=0, age > 3 years)
        if ac == 0 and created:
            try:
                age = (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(created)).days
                if age > 1095:
                    needs_review.append({"id": eid, "type": "stale_candidate",
                                        "detail": f"accessCount=0, age={age} days"})
            except ValueError:
                pass

    # Index stats mismatch
    idx_total = idx.get("stats", {}).get("totalEntries", 0)
    actual_total = len(entries)
    if idx_total != actual_total:
        if fix:
            save_mod.rebuild_index(kb, store_name)
        auto_fixed.append({"type": "index_stats_mismatch",
                          "detail": f"index says {idx_total}, store has {actual_total}"})

    # Entry in index but not in store (orphaned index entry)
    entry_ids = {e.get("id") for e in entries}
    idx_ids = set(idx.get("summaries", {}).keys())
    orphaned = idx_ids - entry_ids
    if orphaned:
        if fix:
            save_mod.rebuild_index(kb, store_name)
        auto_fixed.append({"type": "orphaned_index_entries", "detail": f"{len(orphaned)} entries in index but not store"})

    # Near-duplicate detection (Jaccard on content)
    if len(entries) > 1:
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                sim = jaccard(entries[i].get("content", ""), entries[j].get("content", ""))
                if sim >= JACCARD_THRESHOLD:
                    needs_review.append({
                        "type": "near_duplicate",
                        "detail": f"{entries[i]['id']} and {entries[j]['id']} are {sim:.0%} similar"
                    })

    if changed:
        data["lastUpdated"] = today
        save_mod.save_json(path, data)

    return auto_fixed, needs_review


def _is_provenance_ref(source_id):
    """True if a cross-ref source is external provenance (file, session, backlog item),
    not an intelligence-store entry ID.

    Tests the PROPERTY (does this name a file or non-entry record?) instead of enumerating
    shapes. The shape list kept growing one false positive at a time: mem-NNN (2026-08-16),
    BL-NNN (2026-10-04), then bare filenames like `build-tenancy.py` (candidate 2026-10-21),
    which have no `/` and were reported "no longer exists" while sitting on disk. Entry IDs
    never carry a file extension, so an extension is a safe file signal. Existence of the
    file on disk stays out of scope here: several valid refs are project-relative paths or
    statute citations that do not resolve from the repo root.
    """
    if "/" in source_id or source_id.startswith(("session-", "BL-")):
        return True
    return Path(source_id.split("#", 1)[0]).suffix.lower() in PROVENANCE_FILE_SUFFIXES


def check_cross_references(kb):
    """Check for orphaned cross-references."""
    xref_path = kb / "Intelligence" / "cross-references.json"
    xref = save_mod.load_json(xref_path)
    if xref is None:
        return []

    # Detect format
    if "references" in xref:
        refs = xref["references"]
    else:
        refs = {k: v for k, v in xref.items() if not k.startswith("_") and isinstance(v, dict)}

    # Collect all existing IDs
    all_ids = set()
    for store_name in STORE_NAMES:
        data = save_mod.load_json(kb / "Intelligence" / f"{store_name}.json")
        if data:
            for e in data.get("entries", []):
                all_ids.add(e.get("id"))
    # Memory entries (mem-NNN) are a valid cross-ref source/target too, but live in
    # Memory/memory.json's "memories" dict, not the Intelligence stores above.
    # Missing this caused a false "Source mem-NNN no longer exists" flag when the
    # entry was real.
    mem_data = save_mod.load_json(kb / "Memory" / "memory.json")
    if mem_data:
        all_ids.update(mem_data.get("memories", {}).keys())

    orphaned = []
    for source_id, info in refs.items():
        # File-path and session refs are legitimate provenance (a reasoning entry can
        # derive_from a source file or a session), NOT intel-store IDs, so they will
        # never appear in all_ids. Mirror check_derived_from and skip them, else they
        # false-positive as "no longer exists". A shape test (path separator / session-
        # prefix) is used instead of INTEL_ID here because cross-ref sources include
        # prefixes (proc_) not in that whitelist; the shape test checks every entry-ID
        # source while ignoring only genuine file/session provenance. Filesystem
        # existence of those source files is out of scope for this check.
        # BL-NNN (external project backlog items) is the same kind of external provenance:
        # an entry deriving from a backlog item otherwise false-flags as "no longer exists".
        is_provenance_ref = _is_provenance_ref(source_id)
        if not is_provenance_ref and source_id not in all_ids:
            orphaned.append({"type": "orphaned_cross_ref", "detail": f"Source {source_id} no longer exists"})
        # Validate referenced_by targets exist too. The source-only check silently
        # missed dead reasoning pointers that the benchmark's
        # cross-reference test flags as broken. Check both directions.
        targets = info.get("referenced_by", []) if isinstance(info, dict) else (info if isinstance(info, list) else [])
        for tgt in targets:
            if tgt not in all_ids:
                orphaned.append({"type": "orphaned_cross_ref", "detail": f"Target {tgt} (referenced by {source_id}) no longer exists"})

    return orphaned


def check_missing_cross_refs(kb, fix=False):
    """Cross-references that SHOULD exist but don't (the absence direction).

    check_cross_references validates that what's IN cross-references.json still resolves.
    It has no concept of what's MISSING from it. On 2026-07-25 that blind spot hid 212
    sources declared by reasoning.json derived_from but absent from the cross-ref file,
    behind only 11 flagged stale entries — the flagged set was a sample, not the
    population. Presence-biased validators cannot see never-created data.

    The check is aligned to the WRITER, not to an independent notion of correctness
   : save-session.update_cross_references creates a source entry for every
    derived_from ref except session-* ones, so that is exactly what must exist here.

    The fix is safe because it is purely ADDITIVE: missing sources and back-refs are
    inserted, nothing is removed and related_to is never touched, so no full rebuild
    (which cannot reconstruct related_to) is needed. It delegates to the canonical
    writer over ALL reasoning entries rather than reimplementing the relation.
    Stale-entry REMOVAL stays review-only in check_cross_references."""
    r_path = kb / "Intelligence" / "reasoning.json"
    data = save_mod.load_json(r_path)
    xref = save_mod.load_json(kb / "Intelligence" / "cross-references.json")
    if data is None or xref is None:
        return []

    refs = xref["references"] if "references" in xref else \
        {k: v for k, v in xref.items() if not k.startswith("_") and isinstance(v, dict)}

    # Dangling refs (pointing at pruned intel IDs) are check_derived_from's business.
    # Excluding them here prevents double-reporting one root cause as two issues.
    all_ids = set()
    for store_name in STORE_NAMES:
        d = save_mod.load_json(kb / "Intelligence" / f"{store_name}.json")
        if d:
            for e in d.get("entries", []):
                all_ids.add(e.get("id"))

    missing = []
    for entry in data.get("entries", []):
        rid = entry.get("id", "")
        for source_id in entry.get("derived_from", []) or []:
            if source_id.startswith("session-"):
                continue
            if INTEL_ID.match(source_id) and source_id not in all_ids:
                continue
            info = refs.get(source_id)
            if info is None:
                missing.append({"id": rid, "type": "missing_cross_ref_source",
                                "detail": f"source {source_id} declared by derived_from is absent from cross-references"})
            else:
                targets = info.get("referenced_by", []) if isinstance(info, dict) else info
                if rid not in (targets or []):
                    missing.append({"id": rid, "type": "missing_cross_ref_backref",
                                    "detail": f"source {source_id} exists but does not list {rid} in referenced_by"})

    if fix and missing:
        save_mod.update_cross_references(kb, data.get("entries", []))

    return missing


def check_derived_from(kb, fix=False):
    """Reasoning derived_from refs pointing to intelligence IDs that no longer exist.

    Session IDs (session-*) and file-path refs (docs, .md, #anchors) are legitimate
    provenance and are ignored — only dead intelligence-store pointers are flagged.
    Removing a pointer to a provably nonexistent source is a safe auto-fix. This closes
    the long-standing gap where check_store validated schema but never validated that
    reasoning provenance chains still resolved (dangling refs lingered for months)."""
    path = kb / "Intelligence" / "reasoning.json"
    data = save_mod.load_json(path)
    if data is None:
        return []

    all_ids = set()
    for store_name in STORE_NAMES:
        d = save_mod.load_json(kb / "Intelligence" / f"{store_name}.json")
        if d:
            for e in d.get("entries", []):
                all_ids.add(e.get("id"))

    auto_fixed = []
    changed = False
    for entry in data.get("entries", []):
        derived = entry.get("derived_from", []) or []
        kept = [r for r in derived if not (INTEL_ID.match(r) and r not in all_ids)]
        for r in derived:
            if INTEL_ID.match(r) and r not in all_ids:
                auto_fixed.append({"id": entry.get("id"), "type": "dangling_derived_from",
                                  "detail": f"→ {r} (source pruned)"})
                changed = True
        if fix and len(kept) != len(derived):
            entry["derived_from"] = kept

    if fix and changed:
        data["lastUpdated"] = save_mod.get_today()
        save_mod.save_json(path, data)
        save_mod.rebuild_index(kb, "reasoning")

    return auto_fixed


def check_session_index(kb, fix=False):
    """Blank-fingerprint and stats-drift checks for Memory/session-index.json.

    This file had ZERO coverage here, which is precisely why two silent integrity
    defects in save-session.py's update_session_index() went undetected in production:

      - A blank fingerprint (id present, tags and summary empty) made
        invisible to session-cache search and cold-start
        continuity for 25 DAYS while a full 5.6KB log sat beside it.
      - stats.totalSessions was never maintained on the insert path, so it read 133
        while the sessions array held 143, a drift of 10 across at least 6 saves.

    Both are now fixed in the writer AND guarded by tests, but a writer fix cannot
    detect pre-existing corruption or a future regression from another code path
    (or a concurrent instance). This is the detection half.

    Returns (fixed, review) matching the other checks. stats drift is auto-fixable
    because the sessions array is authoritative. Blank fingerprints are NOT: the
    content is gone and only the session log can restore it, so they go to review.
    """
    path = kb / "Memory" / "session-index.json"
    idx = save_mod.load_json(path)
    if idx is None:
        return [], []

    fixed, review = [], []
    sessions = idx.get("sessions", [])
    if not isinstance(sessions, list):
        return [], [{"type": "session_index_malformed", "id": "",
                     "detail": "sessions is not a list"}]

    # --- Blank fingerprints (NOT auto-fixable: the content is unrecoverable here) ---
    # Grace period: a save in progress registers session_id BEFORE its index content, so a
    # concurrent instance mid-save legitimately looks blank. Flagging that on every run
    # would make this check cry wolf about healthy behavior, which is how a detector gets
    # ignored. Judge by the log's age: an in-flight save just wrote its log; an abandoned
    # blank has an old one.
    GRACE_SECONDS = 600
    now = _time.time()
    for s in sessions:
        if not isinstance(s, dict):
            continue
        sid = s.get("id", "?")
        if not s.get("summary") and not s.get("tags"):
            log = kb / "Memory" / f"{sid}.md"
            if log.exists():
                age = now - log.stat().st_mtime
                if age < GRACE_SECONDS:
                    review.append({"type": "blank_fingerprint_in_flight", "id": sid,
                                   "detail": f"blank but log written {int(age)}s ago — "
                                             f"likely a save in progress, re-check shortly"})
                    continue
                hint = (f"log exists ({log.stat().st_size}B, {int(age // 3600)}h old), "
                        f"re-save with a session_index_entry to fill it")
            else:
                hint = "no session log found either"
            review.append({"type": "blank_fingerprint", "id": sid,
                           "detail": f"empty tags AND summary — invisible to "
                                     f"session-cache search; {hint}"})

    # --- Index row with no session log anywhere  ---
    # The blank check above only notices a missing log incidentally. A row can carry a full
    # fingerprint while its narrative is gone, which is institutional-memory loss. Logs move
    # to Memory/archive/ after the rolling window, so both locations count. A row explicitly
    # tagged `reconstructed` has had its loss acknowledged and is not re-flagged.
    archive_dir = kb / "Memory" / "archive"
    for s in sessions:
        if not isinstance(s, dict) or "reconstructed" in (s.get("tags") or []):
            continue
        sid = s.get("id", "")
        if not sid.startswith("session-") or (not s.get("summary") and not s.get("tags")):
            continue  # blank rows are already reported above
        if not (kb / "Memory" / f"{sid}.md").exists() and not (archive_dir / f"{sid}.md").exists():
            review.append({"type": "session_log_missing", "id": sid,
                           "detail": "index row has no session log in Memory/ or Memory/archive/; "
                                     "recover from Memory/recall/ or tag the row `reconstructed`"})

    # --- stats.totalSessions drift (auto-fixable: the array is authoritative) ---
    declared = idx.get("stats", {}).get("totalSessions")
    actual = len(sessions)
    if declared != actual:
        detail = f"stats.totalSessions={declared} but sessions array holds {actual}"
        if fix:
            idx.setdefault("stats", {})["totalSessions"] = actual
            idx["stats"]["lastUpdated"] = save_mod.get_today()
            save_mod.save_json(path, idx)
        fixed.append({"type": "stats_drift", "id": "", "detail": detail})

    return fixed, review


ATTRIBUTION_ENFORCED_FROM = "2026-09-22"


def check_commitment_attribution(kb, fix=False):
    """Flag closed commitments that carry no attribution for the closure.

    This is the detection half of the commitment-clobber class. A commitment was flipped
    to done-without-being-done THREE times, restored three times, and clobbered again
    each time. The recorded mitigation was mirroring it into Life/calendar.ics as a
    "clobber-proof store", but that mirror CANNOT catch it: VTODOs bearing
    X-NATE-SOURCE:commitments are a GENERATED view of memory.json (see
    scripts/sync-commitments-calendar.py, whose own docstring names memory.json
    canonical), so a clobber deletes the VTODO on the next sync rather than being
    contradicted by it.

    What a silent flip DOES leave behind is a closure with no provenance. Legitimate
    resolutions go through save-session's resolved_commitments, which stamps
    resolved_date and resolved_by. A status changed by any other route has neither.
    Never auto-fixed: only a human knows whether the work actually happened.

    Scoped so it stays a tripwire instead of a standing complaint. Commitments closed
    before resolved_by was stamped automatically are skipped, because flagging those on
    every run buries the one case that matters (a signal that always fires carries no
    information). Two rules:
      - A closure with NO date at all is flagged in every era. That is the actual
        silent-flip signature, since a clobber sets status and nothing else.
      - A missing resolved_by is only flagged from ATTRIBUTION_ENFORCED_FROM onward,
        the date save-session began stamping it.
    """
    review = []
    path = kb / "Memory" / "memory.json"
    mem = save_mod.load_json(path)
    if not mem:
        return [], [{"type": "memory_unreadable", "id": "",
                     "detail": f"could not read {path}"}]

    closed = {"done", "resolved", "complete", "completed",
              "cancelled", "canceled", "void"}
    commitments = mem.get("commitments") or []
    if not isinstance(commitments, list):
        return [], [{"type": "commitments_malformed", "id": "",
                     "detail": f"expected list, got {type(commitments).__name__}"}]

    for c in commitments:
        if not isinstance(c, dict):
            continue
        if str(c.get("status", "open")).lower() not in closed:
            continue
        label = (c.get("id") or c.get("what") or c.get("deliverable")
                 or c.get("commitment") or c.get("task") or "?")
        when = c.get("resolved_date") or c.get("resolved")
        gaps = []
        if not when:
            gaps.append("resolved_date")
        if not c.get("resolved_by") and str(when or "") >= ATTRIBUTION_ENFORCED_FROM:
            gaps.append("resolved_by")
        if gaps:
            review.append({
                "type": "commitment_closed_without_attribution",
                "id": str(label)[:70],
                "detail": (f"status={c.get('status')} but missing {', '.join(gaps)} "
                           f"— a closure with no provenance is the silent-flip "
                           f"silent-flip signature; confirm the work happened")})
    return [], review


def main():
    if len(sys.argv) < 2:
        print('Usage: python3 scripts/maintenance.py \'{"mode": "check|fix", "scope": "all"}\'')
        sys.exit(2)

    ops = json.loads(sys.argv[1])
    mode = ops.get("mode", "check")
    scope = ops.get("scope", "all")
    fix = mode == "fix"

    kb = save_mod.find_kb_root()
    stores = list(STORE_NAMES) if scope == "all" else [scope]

    total_fixed = []
    total_review = []

    print(f"═══ Maintenance {'Fix' if fix else 'Check'} ═══")
    print()

    for store_name in stores:
        if store_name not in STORE_NAMES:
            continue
        print(f"{store_name.title()}")
        fixed, review = check_store(kb, store_name, fix=fix)
        total_fixed.extend(fixed)
        total_review.extend(review)
        if fixed:
            for f in fixed:
                print(f"  {'FIXED' if fix else 'FIXABLE'}: {f['type']} — {f.get('id', '')} {f['detail']}")
        if review:
            for r in review:
                print(f"  REVIEW: {r['type']} — {r.get('id', '')} {r['detail']}")
        if not fixed and not review:
            print("  ✓ Clean")
        print()

    # Cross-reference check
    if scope == "all":
        print("Cross-References")
        orphaned = check_cross_references(kb)
        total_review.extend(orphaned)
        if orphaned:
            for o in orphaned:
                print(f"  REVIEW: {o['detail']}")
        else:
            print("  ✓ Clean")
        print()

        # Session-index integrity (blank fingerprints + stats drift).
        # Added 2026-08-05: this was the detection gap that let two silent
        # update_session_index() defects live in production.
        print("Session Index")
        si_fixed, si_review = check_session_index(kb, fix=fix)
        total_fixed.extend(si_fixed)
        total_review.extend(si_review)
        if si_fixed:
            for f in si_fixed:
                print(f"  {'FIXED' if fix else 'FIXABLE'}: {f['type']} — {f['detail']}")
        if si_review:
            for r in si_review:
                print(f"  REVIEW: {r['type']} — {r.get('id', '')} {r['detail']}")
        if not si_fixed and not si_review:
            print("  ✓ Clean")
        print()

        # Commitment closure attribution. Detection half of the silent-flip
        # class: the calendar VTODO "mirror" cannot catch a clobber because those
        # VTODOs are a generated view of memory.json, but an unattributed closure is
        # a durable signature. Never auto-fixed; only a human knows if the work
        # actually happened.
        print("Commitment Attribution")
        _, ca_review = check_commitment_attribution(kb, fix=fix)
        total_review.extend(ca_review)
        if ca_review:
            for r in ca_review:
                print(f"  REVIEW: {r['type']} — {r.get('id', '')} {r['detail']}")
        else:
            print("  ✓ Clean")
        print()

        # Credential card registry drift (security-protocol.md section 2). Values are never
        # read here: cred.audit enumerates filenames and card metadata only. Uncarded files,
        # card files that vanished, and scripts naming a store path directly are REVIEW items;
        # verification age is informational.
        print("Credential Registry")
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import cred
            ca = cred.audit()
            cr_review = ([{"type": "uncarded_credential", "detail": p} for p in ca["uncarded"]]
                         + [{"type": "card_file_missing", "detail": m} for m in ca["missing"]]
                         + [{"type": "unknown_secrets_store", "detail": s} for s in ca["unknown_stores"]]
                         + [{"type": "hardcoded_store_path", "detail": p} for p in ca["hardcoded_consumers"]])
            total_review.extend(cr_review)
            for r in cr_review[:15]:
                print(f"  REVIEW: {r['type']} — {r['detail']}")
            if len(cr_review) > 15:
                print(f"  ... and {len(cr_review) - 15} more ({len(cr_review)} total)")
            print(f"  INFO: {ca['cards']} cards, {len(ca['pending'])} pending, "
                  f"{len(ca['never_verified'])} never live-verified, {len(ca['stale_verification'])} stale")
            if not cr_review:
                print("  ✓ Clean")
        except Exception as e:  # registry problems must surface, not crash the whole run
            total_review.append({"type": "credential_audit_failed", "detail": f"{type(e).__name__}: {e}"})
            print(f"  REVIEW: credential_audit_failed — {type(e).__name__}: {e}")
        print()

        # Derived-from provenance check (reasoning entries pointing to pruned intel IDs)
        print("Derived-From Provenance")
        dangling = check_derived_from(kb, fix=fix)
        total_fixed.extend(dangling)
        if dangling:
            for d in dangling:
                print(f"  {'FIXED' if fix else 'FIXABLE'}: {d['type']} — {d.get('id', '')} {d['detail']}")
        else:
            print("  ✓ Clean")
        print()

        # Cross-reference coverage: refs that SHOULD exist but don't. Additive fix, so
        # these are FIXABLE rather than REVIEW. Output is capped because a real gap can
        # run to hundreds of lines (212 on 2026-07-25) and would bury the rest.
        print("Cross-Ref Coverage")
        gaps = check_missing_cross_refs(kb, fix=fix)
        total_fixed.extend(gaps)
        if gaps:
            for g in gaps[:10]:
                print(f"  {'FIXED' if fix else 'FIXABLE'}: {g['type']} — {g.get('id', '')} {g['detail']}")
            if len(gaps) > 10:
                print(f"  ... and {len(gaps) - 10} more ({len(gaps)} total)")
        else:
            print("  ✓ Clean")
        print()

    result = {"issues_found": len(total_fixed) + len(total_review),
              "auto_fixed": len(total_fixed) if fix else 0,
              "needs_review": len(total_review),
              "details": {"fixed": total_fixed, "review": total_review}}

    print("═══ Summary ═══")
    print(json.dumps({k: v for k, v in result.items() if k != "details"}, indent=2))

    sys.exit(1 if total_review else 0)


if __name__ == "__main__":
    main()
