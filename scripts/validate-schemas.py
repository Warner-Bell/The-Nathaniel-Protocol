#!/usr/bin/env python3
"""Validate intelligence store schemas against canonical definitions.

Pure deterministic logic. No LLM involvement.
Exit 0 = all entries conform. Non-zero = violations found.

Usage:
    python3 scripts/validate-schemas.py [--quiet]
"""
import json
import sys
import os

QUIET = "--quiet" in sys.argv

KB_DIR = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Nate's-kb", "Intelligence")

# --- Schema Definitions ---

PATTERN_REQUIRED = {"id": str, "category": str, "content": str, "confidence": (int, float),
                    "tags": list, "context": str, "created": str, "lastAccessed": str, "accessCount": (int, float)}
PATTERN_OPTIONAL = {"prevention": str, "outcome": str, "evidence": str, "source": str,
                    "_imported_from": str, "_stale_candidate": bool, "_needs_trim": bool,
                    "_needs_review": bool, "_history": list}
PATTERN_CATEGORIES = {"preference", "approach", "failure", "process", "procedure", "ai_agent"}
PATTERN_LEGACY_CATEGORIES = {"communication", "development", "technical", "tool", "problem_solving",
                             "organization", "presentation", "executive", "content_creation"}
PATTERN_CONTENT_LIMIT = 400

KNOWLEDGE_REQUIRED = {"id": str, "category": str, "content": str, "confidence": (int, float),
                      "tags": list, "source": str, "created": str, "lastAccessed": str, "accessCount": (int, float)}
KNOWLEDGE_OPTIONAL = {"context": str, "validated": bool, "validationNote": str, "sourceUrl": str,
                      "detail": str, "_imported_from": str, "_stale_candidate": bool,
                      "_needs_trim": bool, "_needs_review": bool, "_history": list}
KNOWLEDGE_CATEGORIES = {"technical", "process", "error_solution", "best_practice", "tool_quirk",
                        "reference", "domain_expertise", "architecture", "research", "security",
                        "tool_behavior", "aws_gotcha", "system", "negative_knowledge", "strategic",
                        "faq", "cross_platform", "system_prompt_engineering", "writing"}
KNOWLEDGE_CONTENT_LIMIT = 600

REASONING_REQUIRED = {"id": str, "type": str, "content": str, "intent": str, "reuse_signal": str,
                      "confidence": (int, float), "tags": list, "derived_from": list,
                      "provenance": str, "created": str, "lastAccessed": str, "accessCount": (int, float)}
REASONING_OPTIONAL = {"_imported_from": str, "_stale_candidate": bool, "_needs_trim": bool,
                      "_needs_review": bool, "_history": list}
REASONING_TYPES = {"deduction", "induction", "analogy", "causal", "meta-process",
                   "insight", "architectural_decision", "failure_analysis"}
REASONING_PROVENANCES = {"stated", "synthesized", "cross_session"}
REASONING_CONTENT_LIMIT = 700

LEGACY_FIELDS = {"pattern", "summary", "first_observed", "last_observed", "observation_count",
                 "access_count", "last_accessed", "lastOccurred", "lastModified", "firstSeen",
                 "lastSeen", "timestamp", "last_updated", "occurrences", "failureRate",
                 "evidence_count", "context_scope", "methodology", "key_insight", "template",
                 "resolution", "correction", "prevented_count", "missed_count",
                 "source_patterns", "source_knowledge", "sources"}


def validate_entry(entry, required, optional, category_or_type_key, valid_values, content_limit, store_name):
    """Validate a single entry. Returns list of (severity, message) tuples."""
    issues = []
    eid = entry.get("id", "UNKNOWN")

    # Check required fields
    for field, expected_type in required.items():
        if field not in entry:
            issues.append(("ERROR", f"{eid}: missing required field '{field}'"))
        elif not isinstance(entry[field], expected_type):
            issues.append(("ERROR", f"{eid}: '{field}' should be {expected_type}, got {type(entry[field]).__name__}"))

    # Check optional field types
    for field, expected_type in optional.items():
        if field in entry and not isinstance(entry[field], expected_type):
            issues.append(("WARN", f"{eid}: optional '{field}' should be {expected_type}, got {type(entry[field]).__name__}"))

    # Check category/type enum
    val = entry.get(category_or_type_key, "")
    if val and val not in valid_values:
        if store_name == "patterns" and val in PATTERN_LEGACY_CATEGORIES:
            issues.append(("WARN", f"{eid}: legacy category '{val}' (not in canonical enum)"))
        else:
            issues.append(("WARN", f"{eid}: '{category_or_type_key}' value '{val}' not in enum"))

    # Check provenance (reasoning only)
    if store_name == "reasoning" and "provenance" in entry:
        if entry["provenance"] not in REASONING_PROVENANCES:
            issues.append(("WARN", f"{eid}: provenance '{entry['provenance']}' not in enum"))

    # Check content length
    content = entry.get("content", "")
    if isinstance(content, str) and len(content) > content_limit:
        issues.append(("INFO", f"{eid}: content {len(content)} chars exceeds {content_limit} target"))

    # Check legacy fields
    all_known = set(required) | set(optional)
    for field in entry:
        if field in LEGACY_FIELDS:
            issues.append(("ERROR", f"{eid}: legacy field '{field}' should have been migrated"))
        elif field not in all_known:
            issues.append(("INFO", f"{eid}: unknown field '{field}'"))

    return issues


def validate_store(filepath, required, optional, cat_key, valid_values, content_limit, store_name):
    """Validate an entire store file."""
    if not os.path.exists(filepath):
        return [("ERROR", f"{filepath} not found")]

    with open(filepath) as f:
        data = json.load(f)

    entries = data.get("entries", [])
    all_issues = []
    for entry in entries:
        all_issues.extend(validate_entry(entry, required, optional, cat_key, valid_values, content_limit, store_name))
    return all_issues


def main():
    total = {"ERROR": 0, "WARN": 0, "INFO": 0}
    all_issues = []

    stores = [
        ("patterns.json", PATTERN_REQUIRED, PATTERN_OPTIONAL, "category", PATTERN_CATEGORIES, PATTERN_CONTENT_LIMIT, "patterns"),
        ("knowledge.json", KNOWLEDGE_REQUIRED, KNOWLEDGE_OPTIONAL, "category", KNOWLEDGE_CATEGORIES, KNOWLEDGE_CONTENT_LIMIT, "knowledge"),
        ("reasoning.json", REASONING_REQUIRED, REASONING_OPTIONAL, "type", REASONING_TYPES, REASONING_CONTENT_LIMIT, "reasoning"),
    ]

    for filename, req, opt, cat_key, valid, limit, name in stores:
        filepath = os.path.join(KB_DIR, filename)
        issues = validate_store(filepath, req, opt, cat_key, valid, limit, name)
        all_issues.extend([(name, sev, msg) for sev, msg in issues])
        for sev, _ in issues:
            total[sev] += 1

        if not QUIET:
            entry_count = 0
            if os.path.exists(filepath):
                with open(filepath) as f:
                    entry_count = len(json.load(f).get("entries", []))
            errs = sum(1 for s, _ in issues if s == "ERROR")
            warns = sum(1 for s, _ in issues if s == "WARN")
            print(f"{name}: {entry_count} entries, {errs} errors, {warns} warnings")

    if not QUIET:
        print(f"\nTotal: {total['ERROR']} errors, {total['WARN']} warnings, {total['INFO']} info")
        if total["ERROR"] > 0:
            print("\nERRORS:")
            for store, sev, msg in all_issues:
                if sev == "ERROR":
                    print(f"  [{store}] {msg}")
        if total["WARN"] > 0:
            print("\nWARNINGS:")
            for store, sev, msg in all_issues:
                if sev == "WARN":
                    print(f"  [{store}] {msg}")

    sys.exit(0 if total["ERROR"] == 0 else 1)


if __name__ == "__main__":
    main()
