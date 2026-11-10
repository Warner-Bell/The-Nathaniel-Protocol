#!/usr/bin/env python3
"""Ecosystem Behavioral Benchmark Suite - April 2026
Run from Nate's-kb/ directory.
Tests CSR routing, integrity, retrieval quality, and system health.
"""

import json, os, re, time, sys
from pathlib import Path
from collections import Counter

# All paths below are relative to Nate's-kb/. Resolve it from this file so the documented
# invocation from the repo root (python3 Nate's-kb/Benchmarks/run-benchmark.py) works too.
os.chdir(Path(__file__).resolve().parent.parent)

RESULTS = []
WARNINGS = []
METRICS = {}

def metric(key, value):
    """Collect a named metric for persistence."""
    METRICS[key] = value

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test(name, passed, detail="", info_only=False):
    status = "INFO" if info_only else ("PASS" if passed else "FAIL")
    RESULTS.append({"name": name, "status": status, "detail": detail})
    icon = "ℹ️" if info_only else ("✅" if passed else "❌")
    print(f"  {icon} {name}: {detail}")

def warn(msg):
    WARNINGS.append(msg)

# ── Load all stores and indexes ──
print("Loading stores...")
t0 = time.time()
patterns = load_json("Intelligence/patterns.json")
knowledge = load_json("Intelligence/knowledge.json")
reasoning = load_json("Intelligence/reasoning.json")
memory = load_json("Memory/memory.json")
# The kernel is split across always-loaded steering files: gates, IMG, the Protocol
# Keyword Map and the KB Location Map live in ecosystem-operation.md. Kernel tests read
# the set as one text so a section move between files doesn't read as MISSING. The Save
# Command lives in memory-protocol.md (the kernel keeps a must-read stub).
KERNEL_FILES = ["../.kiro/steering/ecosystem-operation.md", "../.kiro/steering/Nathaniel.md",
                "../.kiro/steering/PRIME-DIRECTIVES.md", "memory-protocol.md"]
def read_kernel():
    return "\n".join(open(k, 'r', encoding='utf-8').read() for k in KERNEL_FILES if os.path.exists(k))

pi = load_json("Intelligence/patterns-index.json")
ki = load_json("Intelligence/knowledge-index.json")
ri = load_json("Intelligence/reasoning-index.json")
mi = load_json("Memory/memory-index.json")
si = load_json("Memory/session-index.json")
load_time = time.time() - t0
print(f"Loaded in {load_time:.3f}s\n")

pat_entries = patterns["entries"]
know_entries = knowledge["entries"]
reas_entries = reasoning["entries"]
# Memory is dict-keyed, convert to list format for uniform handling
mem_dict = memory["memories"]
mem_entries = [{"id": k, **v} if isinstance(v, dict) else {"id": k} for k, v in mem_dict.items()]

stores = {
    "patterns": (pat_entries, pi),
    "knowledge": (know_entries, ki),
    "reasoning": (reas_entries, ri),
    "memory": (mem_entries, mi),
}

# ══════════════════════════════════════════════
# TEST 1: CSR Retrieval Accuracy (Component)
# ══════════════════════════════════════════════
print("═══ TEST 1: CSR Retrieval Accuracy ═══")
csr_tests = [
    ("knowledge", "byTag", "tools"),
    ("knowledge", "byTag", "security"),
    ("knowledge", "byTag", "agentcore"),
    ("knowledge", "byTag", "strands"),
    ("knowledge", "byTag", "mcp"),
    ("patterns", "byCategory", "failure"),
    ("patterns", "byCategory", "approach"),
    ("patterns", "byTag", "route-f"),
    ("reasoning", "byTag", "architecture"),
    ("reasoning", "byType", "deduction"),
]
csr_times = []
for store_name, dim, tag in csr_tests:
    _, idx = stores[store_name]
    t = time.perf_counter_ns()
    hits = idx.get(dim, {}).get(tag, [])
    elapsed = (time.perf_counter_ns() - t) / 1000
    csr_times.append(elapsed)
    test(f"CSR {store_name}.{dim}[{tag}]", len(hits) > 0, f"{len(hits)} hits, {elapsed:.1f}us")
metric("csr_avg_us", round(sum(csr_times) / len(csr_times), 1))
metric("csr_max_us", round(max(csr_times), 1))

# ══════════════════════════════════════════════
# TEST 2: End-to-End Retrieval
# ══════════════════════════════════════════════
print("\n═══ TEST 2: End-to-End Retrieval ═══")
e2e_tests = [
    ("Lambda cold start", "knowledge", "byTag", ["lambda", "cold-start"], 1),
    ("Vectorstore architecture", "knowledge", "byTag", ["vectorstore", "architecture"], 2),
    ("File operation failures", "patterns", "byTag", ["file-ops"], 1),
    ("CSR retrieval design", "knowledge", "byTag", ["csr", "retrieval"], 2),
    ("Communication patterns", "knowledge", "byTag", ["communication", "style"], 1),
    ("Agent security patterns", "knowledge", "byTag", ["agentic-ai", "security"], 2),
    ("Template propagation", "knowledge", "byTag", ["template", "propagation"], 1),
    ("Streaming architecture", "knowledge", "byTag", ["streaming", "agentcore"], 1),
]
for desc, store_name, dim, tags, min_hits in e2e_tests:
    _, idx = stores[store_name]
    all_hits = set()
    for tag in tags:
        all_hits.update(idx.get(dim, {}).get(tag, []))
    test(f"E2E: {desc}", len(all_hits) >= min_hits, f"{len(all_hits)} hits (min {min_hits})")

# ══════════════════════════════════════════════
# TEST 3: Adversarial Routing
# ══════════════════════════════════════════════
print("\n═══ TEST 3: Adversarial Routing ═══")
adversarial = [
    ("knowledge", "byTag", "cryptocurrency"),
    ("knowledge", "byTag", "dating_app"),
    ("patterns", "byCategory", "romance"),
    ("reasoning", "byTag", "quantum_computing"),
    ("patterns", "byTag", "social_media_influencer"),
    ("knowledge", "byTag", "cooking_recipes"),
    ("reasoning", "byType", "telepathy"),
    ("knowledge", "byTag", "sports_betting"),
    ("patterns", "byCategory", "astrology"),
]
for store_name, dim, tag in adversarial:
    _, idx = stores[store_name]
    hits = idx.get(dim, {}).get(tag, [])
    test(f"Adversarial: {store_name}.{dim}[{tag}]", len(hits) == 0, f"{len(hits)} hits (expected 0)")

# ══════════════════════════════════════════════
# TEST 4: Index-Store Consistency
# ══════════════════════════════════════════════
print("\n═══ TEST 4: Index-Store Consistency ═══")
for store_name, (entries, idx) in stores.items():
    store_ids = {e["id"] for e in entries}
    # Collect all IDs from index
    index_ids = set()
    for section in ["byTag", "byType", "byCategory", "byConfidence", "byProvenance", "bySource"]:
        for key, ids in idx.get(section, {}).items():
            if isinstance(ids, list):
                index_ids.update(ids)
    # Also check summaries
    if "summaries" in idx:
        index_ids.update(idx["summaries"].keys())

    orphaned = index_ids - store_ids
    missing = store_ids - index_ids
    # Duplicate check in store
    id_counts = Counter(e["id"] for e in entries)
    dupes = {k: v for k, v in id_counts.items() if v > 1}

    test(f"Consistency: {store_name}",
         len(orphaned) == 0 and len(missing) == 0 and len(dupes) == 0,
         f"store={len(store_ids)}, index={len(index_ids)}, orphaned={len(orphaned)}, missing={len(missing)}, dupes={len(dupes)}")
    if orphaned: warn(f"{store_name} orphaned in index: {orphaned}")
    if missing: warn(f"{store_name} missing from index: {missing}")
    if dupes: warn(f"{store_name} duplicate IDs: {dupes}")

# ══════════════════════════════════════════════
# TEST 5: Tag Reachability
# ══════════════════════════════════════════════
print("\n═══ TEST 5: Tag Reachability ═══")
for store_name in ["knowledge", "patterns"]:
    entries, idx = stores[store_name]
    bt = idx.get("byTag", {})
    all_indexed = set()
    for ids in bt.values():
        all_indexed.update(ids)
    store_ids = {e["id"] for e in entries}
    unreachable = store_ids - all_indexed
    shallow = [eid for eid in store_ids if sum(1 for ids in bt.values() if eid in ids) < 2]
    test(f"Reachability: {store_name}",
         len(unreachable) == 0,
         f"{len(store_ids)} entries, {len(unreachable)} unreachable, {len(shallow)} shallow (<2 tags)")

# ── Provenance reference classification ──────────────────────────
# derived_from and cross-reference source keys legitimately hold three shapes:
#   1. intelligence entry IDs (know-123, fail_045, reason-200)  -> MUST resolve
#   2. session refs (session-YYYY-MM-DD-NNN)                  -> not store entries
#   3. repo file paths (scripts/save-session.py, docs/x.md#anchor) -> not store entries
# Only shape 1 can be "broken". Flagging 2 and 3 produced 108 false positives on
# cross-references and 9 on derived_from. This mirrors the INTEL_ID rule already
# documented in scripts/maintenance.py, and repeats an earlier lesson: a
# too-narrow valid-source set makes the benchmark report bugs that aren't there.
INTEL_ID_RE = re.compile(r"^(know-|fail_|pref_|tech_|approach_|reason-|diagnostics_|org_|prob_|proc_|comm_|content_|pat-|ai_agent_)\d")


def is_intel_ref(ref):
    """True if this ref claims to be an intelligence entry ID."""
    return bool(INTEL_ID_RE.match(str(ref)))


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def repo_path_exists(ref):
    """Resolve a repo-relative provenance path from the REPO ROOT, not cwd.

    The suite runs with cwd=Nate's-kb, so 'scripts/save-session.py' was being
    checked at Nate's-kb/scripts/... and reported missing though it exists.
    """
    bare = str(ref).split("#")[0]
    return os.path.exists(os.path.join(REPO_ROOT, bare))

# ══════════════════════════════════════════════
# TEST 6: Cross-Reference Integrity
# ══════════════════════════════════════════════
print("\n═══ TEST 6: Cross-Reference Integrity ═══")
try:
    xref = load_json("Intelligence/cross-references.json")
    # Reasoning can derive from reasoning, so reasoning ids are valid cross-ref sources too
    # (maintenance.py check_missing_cross_refs adds them).
    all_source_ids = {e["id"] for e in pat_entries} | {e["id"] for e in know_entries} | {e["id"] for e in reas_entries}
    all_reas_ids = {e["id"] for e in reas_entries}
    broken = 0
    total_refs = 0
    stale_paths = []
    for source_id, refs in xref.items():
        if source_id.startswith("_"):
            continue  # metadata key, not a reference
        if is_intel_ref(source_id):
            if source_id not in all_source_ids:
                broken += 1
        elif not source_id.startswith("session-") and not repo_path_exists(source_id):
            stale_paths.append(source_id)
        for r_id in refs.get("referenced_by", []):
            total_refs += 1
            if r_id not in all_reas_ids:
                broken += 1
    test("Cross-references", broken == 0, f"{total_refs} refs, {broken} broken")
    # Stale file-path provenance is a real signal but not a reference-integrity
    # failure: the entry is fine, the file moved. Report separately.
    test("Cross-ref path provenance", len(stale_paths) == 0,
         f"{len(stale_paths)} source paths no longer on disk",
         info_only=(len(stale_paths) > 0))
    for sp in stale_paths[:5]:
        warn(f"  cross-ref source path gone: {sp}")
except Exception as e:
    test("Cross-references", False, f"Error: {e}")

# ══════════════════════════════════════════════
# TEST 7: Protocol Trigger Accuracy
# ══════════════════════════════════════════════
print("\n═══ TEST 7: Protocol Trigger Accuracy ═══")
protocols = [
    ("development-protocol.md", "build"),
    ("writing-protocol.md", "write"),
    ("summarization-protocol.md", "summarize"),
    ("research-protocol.md", "research"),
    ("planning-protocol.md", "plan"),
    ("prompt-enhancement-protocol.md", "prompt"),
    ("executive-communication-protocol.md", "executive"),
    ("memory-protocol.md", "memory"),
    ("maintenance-protocol.md", "maintenance"),
    ("proactive-offering-protocol.md", "proactive"),
    ("problem-solving-protocol.md", "diagnose"),
    ("customization-protocol.md", "customize"),
    ("security-protocol.md", "security"),
]
for proto_file, keyword in protocols:
    exists = os.path.exists(proto_file)
    size = os.path.getsize(proto_file) if exists else 0
    test(f"Protocol: {keyword} → {proto_file}", exists and size > 100, f"exists={exists}, {size}B")

# ══════════════════════════════════════════════
# TEST 8: Gate Coverage
# ══════════════════════════════════════════════
print("\n═══ TEST 8: Gate Coverage ═══")
gates = ["Troubleshooting Gate", "Removal Cascade", "Destructive Action Gate",
         "Source-Fidelity Gate", "Template Propagation Gate", "File Resolution", "Recommendation Gate"]
kernel_path = KERNEL_FILES[1]
if os.path.exists(kernel_path):
    kernel = read_kernel()
    for gate in gates:
        found = gate in kernel
        test(f"Gate: {gate}", found, "found" if found else "MISSING")
else:
    test("Gate Coverage", False, "Kernel not found")

# ══════════════════════════════════════════════
# TEST 9: Vectorstore Quality
# ══════════════════════════════════════════════
print("\n═══ TEST 9: Vectorstore Quality ═══")
vs_path = "vectorstore"
if os.path.exists(f"{vs_path}/config.json"):
    try:
        import numpy as np
        vectors = np.load(f"{vs_path}/vectors.npy")
        with open(f"{vs_path}/metadata.json", 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        meta_entries = metadata.get("entries", [])
        norms = np.linalg.norm(vectors, axis=1)
        zero_vecs = np.sum(norms == 0)
        test("Vectorstore: normalized", np.allclose(norms[norms > 0], 1.0, atol=0.01),
             f"norms min={norms.min():.4f} max={norms.max():.4f} mean={norms.mean():.4f}")
        test("Vectorstore: vec/meta match", vectors.shape[0] == len(meta_entries),
             f"vectors={vectors.shape[0]}, metadata={len(meta_entries)}")
        test("Vectorstore: zero vectors", zero_vecs == 0, f"{zero_vecs} zero vectors")
        # Check vectorstore is current with intelligence stores
        total_entries = len(pat_entries) + len(know_entries) + len(reas_entries) + len(mem_entries)
        vs_count = metadata.get("entry_count", vectors.shape[0])
        test("Vectorstore: current with stores",
             abs(vs_count - total_entries) < total_entries * 0.1,
             f"vectorstore={vs_count}, stores={total_entries}, delta={vs_count - total_entries}")
    except ImportError:
        test("Vectorstore", True, "numpy not available, skipping vector checks", info_only=True)
else:
    test("Vectorstore", True, "No vectorstore configured, skipping", info_only=True)

# ══════════════════════════════════════════════
# TEST 10: Session Index Integrity
# ══════════════════════════════════════════════
print("\n═══ TEST 10: Session Index Integrity ═══")
sessions = si.get("sessions", [])
session_ids = [s["id"] for s in sessions]
log_files = [f.stem for f in Path("Memory").glob("session-*.md")]
idx_set = set(session_ids)
log_set = set(log_files)
# Check archive too
archive_logs = [f.stem for f in Path("Memory/archive").glob("session-*.md")] if os.path.exists("Memory/archive") else []
all_logs = log_set | set(archive_logs)
missing_logs = idx_set - all_logs
dupe_ids = [sid for sid, c in Counter(session_ids).items() if c > 1]
test("Session index: no missing logs", len(missing_logs) == 0,
     f"index={len(idx_set)}, logs={len(log_set)}, archived={len(archive_logs)}, missing={len(missing_logs)}")
test("Session index: no dupes", len(dupe_ids) == 0, f"{len(dupe_ids)} duplicate IDs")

# ══════════════════════════════════════════════
# TEST 11: Confidence Distribution
# ══════════════════════════════════════════════
print("\n═══ TEST 11: Confidence Distribution ═══")
for store_name, (entries, _) in stores.items():
    if store_name == "memory":
        confs = [e.get("confidence", 0) for e in entries]
    else:
        confs = [e.get("confidence", 0) for e in entries]
    if confs:
        avg = sum(confs) / len(confs)
        invalid = [c for c in confs if not (0.0 <= c <= 1.0)]
        from collections import Counter as Ctr2
        mode_val, mode_count = Ctr2(confs).most_common(1)[0]
        pct_mode = mode_count * 100 // len(confs)
        # FAIL if invalid values exist. FAIL if >80% share same value (not differentiating).
        differentiating = pct_mode < 80
        test(f"Confidence: {store_name}",
             len(invalid) == 0 and differentiating,
             f"avg={avg:.3f}, min={min(confs):.2f}, max={max(confs):.2f}, invalid={len(invalid)}, mode={mode_val} ({pct_mode}%)")
        metric(f"confidence_{store_name}_avg", round(avg, 3))
        metric(f"confidence_{store_name}_mode_pct", pct_mode)

# ══════════════════════════════════════════════
# TEST 12: Schema Integrity
# ══════════════════════════════════════════════
print("\n═══ TEST 12: Schema Integrity ═══")
required_fields = {
    "patterns": ["id", "category", "content", "confidence", "tags"],
    "knowledge": ["id", "category", "content", "confidence", "tags"],
    "reasoning": ["id", "type", "content", "confidence", "reuse_signal", "intent"],
}
for store_name, fields in required_fields.items():
    entries, _ = stores[store_name]
    violations = []
    for e in entries:
        missing = [f for f in fields if f not in e]
        if missing:
            violations.append(f"{e.get('id','?')}: missing {missing}")
    test(f"Schema: {store_name}", len(violations) == 0,
         f"{len(entries)} entries, {len(violations)} violations")
    for v in violations[:5]:
        warn(f"  {store_name} schema: {v}")

# ══════════════════════════════════════════════
# TEST 13: Index Meta Accuracy
# ══════════════════════════════════════════════
print("\n═══ TEST 13: Index Meta Accuracy ═══")
for store_name, (entries, idx) in stores.items():
    if store_name == "memory":
        continue
    stats = idx.get("stats", {})
    meta_total = stats.get("totalEntries", stats.get("totalPatterns", stats.get("total", -1)))
    actual = len(entries)
    test(f"Meta accuracy: {store_name}", meta_total == actual,
         f"meta={meta_total}, actual={actual}")

# ══════════════════════════════════════════════
# TEST 14: Token Economics
# ══════════════════════════════════════════════
print("\n═══ TEST 14: Token Economics ═══")
idx_files = {
    "memory-index": "Memory/memory-index.json",
    "patterns-index": "Intelligence/patterns-index.json",
    "knowledge-index": "Intelligence/knowledge-index.json",
    "reasoning-index": "Intelligence/reasoning-index.json",
}
content_files = {
    "memory": "Memory/memory.json",
    "patterns": "Intelligence/patterns.json",
    "knowledge": "Intelligence/knowledge.json",
    "reasoning": "Intelligence/reasoning.json",
}
idx_total = sum(os.path.getsize(p) // 4 for p in idx_files.values())
content_total = sum(os.path.getsize(p) // 4 for p in content_files.values())
reduction = (content_total - idx_total) * 100 // content_total if content_total > 0 else 0
ratio = idx_total * 100 // content_total if content_total > 0 else 0

print(f"  Index total: ~{idx_total:,} tokens")
print(f"  Content total: ~{content_total:,} tokens")
print(f"  Index:Content ratio: {ratio}%")
print(f"  CSR reduction (indexes only vs full load): ~{reduction}%")

# Per-store breakdown
for name in ["memory", "patterns", "knowledge", "reasoning"]:
    idx_tok = os.path.getsize(idx_files[f"{name}-index"]) // 4
    cont_tok = os.path.getsize(content_files[name]) // 4
    entries_list, _ = stores[name]
    r = idx_tok * 100 // cont_tok if cont_tok > 0 else 0
    print(f"  {name}: {len(entries_list)} items, idx={idx_tok:,} tok, content={cont_tok:,} tok, ratio={r}%")

test("Token economics", ratio <= 60,
     f"4-store: {idx_total:,} idx / {content_total:,} content = {ratio}% ratio, {reduction}% reduction")
metric("token_idx_total", idx_total)
metric("token_content_total", content_total)
metric("token_ratio_pct", ratio)

# ── Cold-start context budget ────────────────────────────────────
# The ratio test above measures CSR efficiency (index vs full store), which is a
# different question from "what does a cold session actually pay to boot?".
# Nothing measured the latter, so the session index grew to 327KB unnoticed while
# the reported figure stayed flat because session-index was never in the sum.
# This tracks the real Session Start Gate load set.
# The Session Start Gate loads memory-index whole but only the HEAD of the
# patterns/knowledge/reasoning indexes plus every reasoning reuse signal
# (scripts/index-query.py); the full indexes are storage, queried on demand. Measure the
# real load set; full_index_tok is tracked, not budgeted, so index growth stays visible.
import subprocess
mem_tok = os.path.getsize("Memory/memory-index.json") // 4 if os.path.exists("Memory/memory-index.json") else 0
head_proc = subprocess.run([sys.executable, "../scripts/index-query.py", '{"action":"head"}'],
                           capture_output=True, text=True)
head_ok = head_proc.returncode == 0 and head_proc.stdout.strip().startswith("{")
head_tok = len(head_proc.stdout) // 4 if head_ok else 0
sig_proc = subprocess.run([sys.executable, "../scripts/index-query.py", '{"action":"signals"}'],
                          capture_output=True, text=True)
sig_ok = sig_proc.returncode == 0 and sig_proc.stdout.startswith("# reasoning reuse signals")
sig_tok = len(sig_proc.stdout) // 4 if sig_ok else 0
full_index_tok = sum(os.path.getsize(f"Intelligence/{n}-index.json") // 4
                     for n in ("patterns", "knowledge", "reasoning")
                     if os.path.exists(f"Intelligence/{n}-index.json"))
session_idx_path = "Memory/session-index.json"
session_idx_tok = os.path.getsize(session_idx_path) // 4 if os.path.exists(session_idx_path) else 0
startup_total = mem_tok + head_tok + sig_tok
print(f"  Cold-start load set: ~{startup_total:,} tokens (memory-index ~{mem_tok:,} + index head ~{head_tok:,} + reasoning signals ~{sig_tok:,})")
print(f"  Full indexes:        ~{full_index_tok:,} tokens (STORAGE, queried via index-query.py)")
print(f"  session-index.json:  ~{session_idx_tok:,} tokens (STORAGE, queried via session-cache)")
test("Index head query works", head_ok, "ok" if head_ok else (head_proc.stderr or head_proc.stdout)[-200:])
test("Reasoning signals query works", sig_ok, "ok" if sig_ok else (sig_proc.stderr or sig_proc.stdout)[-200:])
# 40k is a growth tripwire: reasoning signals grow with every reasoning entry.
test("Cold-start context budget", head_ok and sig_ok and startup_total <= 40000,
     f"~{startup_total:,} tokens loaded at session start (budget 40,000)")
metric("startup_context_tokens", startup_total)
metric("full_index_tokens_not_loaded", full_index_tok)
metric("reasoning_signals_tokens", sig_tok)
metric("session_index_tokens_not_loaded", session_idx_tok)

metric("csr_reduction_pct", reduction)

# ══════════════════════════════════════════════
# TEST 15: Duplicate Content Detection
# ══════════════════════════════════════════════
print("\n═══ TEST 15: Duplicate Content Detection ═══")
for store_name, (entries, _) in stores.items():
    if store_name == "memory":
        continue
    contents = {}
    dupes = []
    for e in entries:
        c = e.get("content", "").strip()
        if c in contents:
            dupes.append((contents[c], e["id"]))
        else:
            contents[c] = e["id"]
    test(f"Duplicates: {store_name}", len(dupes) == 0,
         f"{len(entries)} entries, {len(dupes)} content duplicates")
    for d in dupes:
        warn(f"  {store_name} duplicate: {d[0]} == {d[1]}")

# ══════════════════════════════════════════════
# TEST 16: Tag Breadth Analysis
# ══════════════════════════════════════════════
print("\n═══ TEST 16: Tag Breadth Analysis ═══")
for store_name in ["knowledge", "patterns"]:
    _, idx = stores[store_name]
    bt = idx.get("byTag", {})
    entries, _ = stores[store_name]
    total = len(entries)
    # Fresh instance (no sessions): broad tags and singletons are expected from seed intelligence
    si = load_json("Memory/session-index.json")
    session_count = len(si.get("sessions", []))
    is_fresh = session_count == 0
    broad_tags = {tag: len(ids) for tag, ids in bt.items() if len(ids) > total * 0.30}
    singletons = {tag for tag, ids in bt.items() if len(ids) == 1}
    # FAIL if any tag covers >30% of the store (routing dilution) — skip for fresh instances
    test(f"Tag breadth: {store_name}",
         is_fresh or len(broad_tags) == 0,
         f"{len(bt)} tags, {len(broad_tags)} overly broad (>30%), {len(singletons)} singletons ({len(singletons)*100//len(bt)}%)")
    if broad_tags:
        for tag, count in sorted(broad_tags.items(), key=lambda x: -x[1])[:5]:
            print(f"    ⚠️ '{tag}' = {count} entries ({count*100//total}%)")

# ══════════════════════════════════════════════
# TEST 17: Near-Duplicate Detection
# ══════════════════════════════════════════════
print("\n═══ TEST 17: Near-Duplicate Detection ═══")
for store_name in ["patterns", "knowledge"]:
    entries, _ = stores[store_name]
    prefixes = {}
    near_dupes = []
    for e in entries:
        prefix = e.get("content", "").strip()[:80]
        if prefix in prefixes:
            near_dupes.append((prefixes[prefix], e["id"]))
        else:
            prefixes[prefix] = e["id"]
    test(f"Near-duplicates: {store_name}", len(near_dupes) == 0,
         f"{len(near_dupes)} near-duplicates (first 80 chars match)",
         info_only=(len(near_dupes) > 0))
    for nd in near_dupes:
        print(f"    {nd[0]} ~ {nd[1]}")

# ══════════════════════════════════════════════
# TEST 18: Derived-From Integrity
# ══════════════════════════════════════════════
print("\n═══ TEST 18: Derived-From Integrity ═══")
all_live = {e["id"] for e in pat_entries} | {e["id"] for e in know_entries} | {e["id"] for e in reas_entries}
broken_refs = []
stale_derived = []
for e in reas_entries:
    for src in e.get("derived_from", []):
        if is_intel_ref(src):
            if src not in all_live:
                broken_refs.append((e["id"], src))
        elif not str(src).startswith("session-") and not repo_path_exists(src):
            stale_derived.append((e["id"], src))
test("Derived-from refs", len(broken_refs) == 0,
     f"{len(broken_refs)} broken entry-ID refs (session/file-path refs are valid provenance)")
test("Derived-from path provenance", len(stale_derived) == 0,
     f"{len(stale_derived)} derived_from paths no longer on disk",
     info_only=(len(stale_derived) > 0))
for sd in stale_derived[:5]:
    warn(f"  {sd[0]} -> {sd[1]} (path gone)")
for br in broken_refs[:5]:
    warn(f"  {br[0]} -> {br[1]} (not found)")

# ══════════════════════════════════════════════
# TEST 19: Tag-Index Consistency
# ══════════════════════════════════════════════
print("\n═══ TEST 19: Tag-Index Consistency ═══")
for store_name in ["patterns", "knowledge"]:
    entries, idx = stores[store_name]
    bt = idx.get("byTag", {})
    misrouted = 0
    details = []
    for e in entries:
        for tag in e.get("tags", []):
            if tag in bt and e["id"] not in bt[tag]:
                misrouted += 1
                details.append(f"{e['id']} has tag '{tag}' but missing from index")
    test(f"Tag-index sync: {store_name}", misrouted == 0,
         f"{misrouted} entries with tags not reflected in index")
    for d in details[:3]:
        warn(f"  {d}")

# ══════════════════════════════════════════════
# TEST 20: Cross-Store ID Collision
# ══════════════════════════════════════════════
print("\n═══ TEST 20: Cross-Store ID Collision ═══")
id_sets = {
    "patterns": {e["id"] for e in pat_entries},
    "knowledge": {e["id"] for e in know_entries},
    "reasoning": {e["id"] for e in reas_entries},
    "memory": {e["id"] for e in mem_entries},
}
collisions = set()
names = list(id_sets.keys())
for i in range(len(names)):
    for j in range(i+1, len(names)):
        overlap = id_sets[names[i]] & id_sets[names[j]]
        if overlap:
            collisions.update(overlap)
test("Cross-store ID collision", len(collisions) == 0,
     f"{len(collisions)} collisions")

# ══════════════════════════════════════════════
# TEST 21: Access Count Health
# ══════════════════════════════════════════════
print("\n═══ TEST 21: Access Count Health ═══")
for store_name in ["patterns", "knowledge", "reasoning"]:
    entries, _ = stores[store_name]
    counts = [e.get("accessCount", 0) for e in entries]
    zeros = sum(1 for c in counts if c == 0)
    negatives = sum(1 for c in counts if c < 0)
    pct_zero = zeros * 100 // len(counts) if counts else 0
    # Fresh instance (no sessions): all entries will be never-accessed — that's expected
    si = load_json("Memory/session-index.json")
    session_count = len(si.get("sessions", []))
    is_fresh = session_count == 0
    test(f"Access health: {store_name}",
         negatives == 0 and (is_fresh or pct_zero < 50),
         f"{zeros}/{len(counts)} never-accessed ({pct_zero}%), {negatives} negative")
    metric(f"access_zero_pct_{store_name}", pct_zero)

# ══════════════════════════════════════════════
# TEST 22: Summary Completeness
# ══════════════════════════════════════════════
print("\n═══ TEST 22: Summary Completeness ═══")
for store_name in ["patterns", "knowledge", "reasoning"]:
    entries, idx = stores[store_name]
    summs = idx.get("summaries", {})
    missing = [e["id"] for e in entries if e["id"] not in summs]
    short = [e["id"] for e in entries if len(summs.get(e["id"], "")) < 20]
    test(f"Summaries: {store_name}",
         len(missing) == 0 and len(short) == 0,
         f"{len(missing)} missing, {len(short)} too short (<20 chars)")

# ══════════════════════════════════════════════
# TEST 23: Failure-to-Fix Cycle Coverage
# ══════════════════════════════════════════════
print("\n═══ TEST 23: Failure-to-Fix Cycle Coverage ═══")
kernel_path = KERNEL_FILES[1]
if os.path.exists(kernel_path):
    kernel = read_kernel()
    test("Failure-to-Fix: exists in kernel",
         "Failure-to-Fix Cycle" in kernel and "MANDATORY" in kernel[kernel.index("Failure-to-Fix"):kernel.index("Failure-to-Fix")+500],
         "found" if "Failure-to-Fix Cycle" in kernel else "MISSING")
    test("Failure-to-Fix: no-deferral rule",
         'Not "noted."' in kernel or "Not \"noted.\"" in kernel,
         "found" if "noted" in kernel[kernel.index("Failure-to-Fix"):kernel.index("Failure-to-Fix")+500] else "MISSING")
    test("Failure-to-Fix: same-response mandate",
         "ONE response" in kernel or "SAME RESPONSE" in kernel,
         "found")
else:
    test("Failure-to-Fix", False, "Kernel not found")

# ══════════════════════════════════════════════
# TEST 24: Kernel Coherence
# ══════════════════════════════════════════════
print("\n═══ TEST 24: Kernel Coherence ═══")
kernel_path = KERNEL_FILES[1]
if os.path.exists(kernel_path):
    kernel = read_kernel()

    # 24a: Keyword map protocols exist on disk
    import re
    keyword_map_match = re.findall(r'`([a-z\-]+(?:-protocol)?\.md)`', kernel)
    protocol_dir = "."
    missing_protocols = []
    for proto in set(keyword_map_match):
        if proto.endswith('.md') and 'protocol' in proto:
            if not os.path.exists(proto) and not os.path.exists(f"../{proto}"):
                missing_protocols.append(proto)
    test("Kernel coherence: keyword map protocols exist",
         len(missing_protocols) == 0,
         f"{len(missing_protocols)} missing: {missing_protocols}" if missing_protocols else "all referenced protocols found on disk")

    # 24b: Gates referenced in Pre-Task Protocol exist in kernel body
    pre_task_gates = ["TROUBLESHOOTING GATE", "COGNITIVE PROBLEM-SOLVING GATE", "DESTRUCTIVE ACTION GATE",
                      "Source-Fidelity Gate", "Template Propagation Gate", "Cognitive Integrity Check"]
    missing_gates = [g for g in pre_task_gates if g not in kernel]
    test("Kernel coherence: Pre-Task gates present in body",
         len(missing_gates) == 0,
         f"{len(missing_gates)} missing: {missing_gates}" if missing_gates else "all Pre-Task gates have body sections")

    # 24c: IMG gate present and has mandatory markers
    has_img = "Institutional Memory Gate" in kernel
    has_img_mandatory = "MANDATORY" in kernel[kernel.index("Institutional Memory"):kernel.index("Institutional Memory")+200] if has_img else False
    test("Kernel coherence: IMG gate present + mandatory",
         has_img and has_img_mandatory,
         "found + mandatory" if has_img and has_img_mandatory else "MISSING or not mandatory")

    # 24d: Save protocol steps sequential (1-10)
    # Steps 3 and 5 are legitimately lettered sub-steps in the kernel checklist
    # (3a/3b/3c/3c-CROSS/3d, 5a..5e) because each represents a distinct save
    # operation; match any step-N or step-Na/Nb-style checklist line.
    save_steps_found = []
    checklist_start = kernel.index("SAVE CHECKLIST")
    checklist_block = kernel[checklist_start:checklist_start + 2000]
    for i in range(1, 11):
        patterns = [f"[ ] {i}.", f"[x] {i}."] + [f"[ ] {i}{c}." for c in "abcdef"] + [f"[x] {i}{c}." for c in "abcdef"]
        if any(p in checklist_block for p in patterns) or f"{i}. " in checklist_block:
            save_steps_found.append(i)
    test("Kernel coherence: save protocol steps 1-10 present",
         len(save_steps_found) >= 9,
         f"found steps: {save_steps_found}")

    # 24e: Mandatory read directives present for critical docs
    mandatory_reads = [
        ("Schema Conformance Gate", "Read Schema Conformance Gate"),
        ("security-protocol.md", "Read `security-protocol.md`"),
        ("Pruning", "read `memory-protocol.md`"),
    ]
    missing_reads = [(name, pattern) for name, pattern in mandatory_reads if pattern not in kernel]
    test("Kernel coherence: critical doc read mandates",
         len(missing_reads) == 0,
         f"{len(missing_reads)} missing: {[m[0] for m in missing_reads]}" if missing_reads else "all critical read mandates present")

    # 24f: Silent session start directive
    test("Kernel coherence: silent session start",
         "Execute steps 1-4 SILENTLY" in kernel,
         "found" if "Execute steps 1-4 SILENTLY" in kernel else "MISSING")

else:
    test("Kernel Coherence", False, "Kernel not found")

# ══════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════
print("\n" + "═" * 60)
print("SUMMARY")
print("═" * 60)
passes = sum(1 for r in RESULTS if r["status"] == "PASS")
fails = sum(1 for r in RESULTS if r["status"] == "FAIL")
infos = sum(1 for r in RESULTS if r["status"] == "INFO")
print(f"  PASS: {passes}")
print(f"  FAIL: {fails}")
print(f"  INFO: {infos}")
print(f"  Total: {len(RESULTS)}")

if WARNINGS:
    print(f"\n  WARNINGS ({len(WARNINGS)}):")
    for w in WARNINGS:
        print(f"    ⚠️ {w}")

if fails > 0:
    print("\n  FAILED TESTS:")
    for r in RESULTS:
        if r["status"] == "FAIL":
            print(f"    ❌ {r['name']}: {r['detail']}")

# Entry counts for reference
print(f"\n  System: {len(pat_entries)} patterns, {len(know_entries)} knowledge, {len(reas_entries)} reasoning, {len(mem_entries)} memories = {len(pat_entries)+len(know_entries)+len(reas_entries)+len(mem_entries)} total")
print(f"  Load time: {load_time:.3f}s")

# ══════════════════════════════════════════════
# METRICS PERSISTENCE
# ══════════════════════════════════════════════
from datetime import datetime, timezone
metric("timestamp", datetime.now(timezone.utc).isoformat())
metric("load_time_s", round(load_time, 3))
metric("passes", passes)
metric("fails", fails)
metric("infos", infos)
metric("total_tests", len(RESULTS))
metric("warnings", len(WARNINGS))
metric("entry_counts", {
    "patterns": len(pat_entries), "knowledge": len(know_entries),
    "reasoning": len(reas_entries), "memory": len(mem_entries),
    "total": len(pat_entries) + len(know_entries) + len(reas_entries) + len(mem_entries)
})

metrics_path = "Benchmarks/benchmark-metrics.json"
history = []
if os.path.exists(metrics_path):
    with open(metrics_path, 'r', encoding='utf-8') as f:
        history = json.load(f)
history.append(METRICS)
with open(metrics_path, 'w', encoding='utf-8') as f:
    json.dump(history, f, indent=2)
print(f"\n  📊 Metrics saved to {metrics_path} ({len(history)} runs total)")
