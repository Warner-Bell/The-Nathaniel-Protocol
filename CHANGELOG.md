# Changelog

All notable changes to the Nathaniel Protocol template. Versions follow [semantic versioning](https://semver.org/): a major version changes how an install is deployed or upgraded.

## [4.0.0] - 2026-11-10

Moves the template to **Kiro CLI v3** and splits the kernel into four always-loaded steering files. Existing installs must re-deploy `.kiro/`: see [Upgrading from template 3.x](README.md#-upgrading-from-template-3x).

### Breaking changes

- **Kiro CLI 3.0+ required for hooks.** All hooks are standalone workspace hooks in `.kiro/hooks/*.json` (v3 format) and apply to every agent. Agent configs no longer embed hooks. `setup.sh` warns below 3.0 and prints the `kiro-cli agent upgrade` hint.
- **Kernel split.** `Nathaniel.md` keeps identity, voice, anti-patterns, the session lifecycle and the self-checks. The operating principles, every mandatory gate, the Protocol Keyword Map, External Content Security, the KB map and the Recommendation Gate moved to the new `ecosystem-operation.md`. The full Save Command moved into `memory-protocol.md`, and complex-task initialization into `Nate-Protocol.md`.
- **`PRIME-DIRECTIVES.md` rewritten.** The 13 Hard Rules became 27 Rules in five categories (Source & Evidence, Execution & Completion, Output & Scope, Tools & Templates, Interaction & Safety). The Rules section is now written only by `scripts/correction-ledger.py`. Kernel pointers use the new numbers (Rule 11 output, Rule 16 templates, Rule 17 scripts).
- **CLAUDE.md, `.cursorrules`, `.windsurfrules`** must be built from all four kernel files. Copying `Nathaniel.md` alone now drops the gates and rules. `setup.sh` builds CLAUDE.md correctly; the README shows the manual command.
- **`analyst.json`** is in the v3 universal format (`permissions` block, writes scoped to the research folders) and has no model pin, so it uses your Kiro default. The old `claude-opus-4.6` pin pointed at a model Kiro no longer serves.

### Added

- **`setup.sh --upgrade`**: backs up `.kiro/` and `CLAUDE.md` with a timestamp, then overwrites them from `.steering-files/`. Normal runs still never overwrite your copies. Setup also deploys `.steering-files/skills/` and builds the live repo map.
- **Deterministic safety floor** (`scripts/hooks/`, wired in `.kiro/hooks/safety-floor.json`): `denylist.py` (secret paths, credential echo, cloud metadata endpoint, `rm -rf` on protected roots, agent edits to hook wiring), `source-authority.py` (a model create/update edit needs a recent read of the live contract), `preflight.py` (flags searches for files at documented locations), `audit_log.py` + `audit_common.py` (HMAC-chained audit trail), `gate_grant.py` (scoped, expiring exceptions). Each has a kill switch and a test suite.
- **Credential card system**: `scripts/cred.py` + `cred.js` resolve credentials by card id so values never enter agent context; `Nate's-kb/credential-registry.json` ships empty with the schema and one illustrative card; `cred.py audit` runs inside `maintenance.py`; `security-protocol.md` section 2 is the procedure; `.secrets/` folders are git-ignored. Rule 22 makes card-first lookup mandatory.
- **Correction loop**: `scripts/hooks/correction_hook.py` (UserPromptSubmit) detects corrections and logs them to `Nate's-kb/Intelligence/corrections.jsonl`; the `correction-capture` skill diagnoses each one and cites or adds a rule through `scripts/correction-ledger.py`; `scripts/correction-backfill.py` seeds the ledger from Kiro CLI history. Ships in `log` mode (rule edits are staged for your approval) via `Nate's-kb/Intelligence/correction-loop.json`.
- **Skill router**: `scripts/hooks/skill_router_hook.py` + `scripts/skill-router/` (matcher, intent gate, `routes.json`, labeled corpus). Nudges each request toward the covering skill or protocol. Ships in `log` mode; `NATE_SKILL_ROUTER=enforce` makes it block raw searches a skill already covers. `routes_check.py` fails when `routes.json` and the Protocol Keyword Map disagree.
- **Skills**: `.steering-files/skills/correction-capture/` and `route-f-analysis/`.
- **`source-authority-gate.md`** steering: authority ladder, one-strike rule for inferred fixes, context-depth rungs.
- **`empirical-feasibility-protocol.md`** with keyword-map and `Nate-Protocol.md` routing.
- **Self-Check rows**: Instrument, Context-Depth, Materiality, Premise, Defect, Authorship; Extended Check Coverage; Instrument added to the Cognitive Integrity Check lists.
- **Cold start by index head**: `scripts/index-query.py` (`head`, `signals`, `tag`, `keyword`, `ids`, `tags`) replaces loading whole indexes at session start; reasoning reuse signals load at cold start.
- **Protocol content**: problem-solving Phase 1.5 (build a feedback loop) and Instrument Validity, plus `hypothesis` / `reproduction` routing; development Two-Axis Code Review and Code Visibility; writing non-negotiables, deliverable hygiene, leak sweep and related rules; security section 8 (email content security); memory protocol claim-the-ID-first and capture-marker pre-pass; Behavioral Control Pipeline enforcement placement; learning-loop Doc-to-KB sync step.
- **Scripts**: `doc-kb-sync.py`, `check-no-emdash.py`, `apply-entry-ops.py`, `test-session-cache-fts.py`.
- **Vectorstore guards**: max-token truncation and query/index dimension checks in `kb_query`, `kb_sync` and `kb_vectorize`, `access_tracking.py`, and tests (`test_dim_guard.py`, `tests/test_truncation.py`).
- **CI** runs every hook suite, the index-query and FTS tests, `routes_check.py` and `cred.py audit`.
- **Benchmarks**: UAP silence-vs-contradiction behavioral scenarios.
- **`anti-slop-protocol.md`**: document integrity audit (every claim proven against its source; confabulation, stale figures, invented options, misquotes, internal-only leaks), routed by the keyword map, `Nate-Protocol.md` and the skill router. `writing-protocol.md` Gate 0 runs it on consequential external deliverables.
- **Self-Check rows Commensurability** (a figure needs metric, scope and as-of date before it can be called a discrepancy) **and Accounting** (enumerate and read every artifact that governs a mechanism before asserting or recording a plan); the Instrument row gains falsifier-first, pattern-variant and read-to-the-section-boundary clauses.
- **Source Authority Gate**: rung pinning and a context-depth calibration log (`Nate's-kb/Memory/context-calibration.json`, ships empty).
- **Writing protocol 2.3**: Consumable Output Standard, Pre-Delivery Integrity Gate (Gate 0), reader-owned facts, beat leads, more throat-clearing openers, PDF/Word delivery and a mechanical lint step.
- **Development protocol 3.1**: Adaptive Scoping (run first) with a `scope.md` Status block, append-only history docs, three Quality Gate items.
- **Prompt enhancement**: Context Engineering (pick context sources before polishing wording) and a Prompt Quality Score gate.
- **Security protocol**: Full-Tree Verification before any push (sweep every committed blob, gate on a printed total of 0, pin the SHA, avoid the `git grep --cached` false-zero trap).
- **Commitments and memory hygiene**: `scripts/commitments.py` (close, redate, add, reopen commitments immediately, outside a save; one `is_open()` definition), `scripts/reconcile-memory.py` (duplicate projects and stale commitments; `--apply` merges exact clusters only), and a monthly Memory drift step in `maintenance-protocol.md`. `save-session.py` gains a `commitment_updates` op, auto-ids for id-less new commitments, normalized project-name matching that prefers the live record over a superseded twin, and a warning for unknown top-level ops keys.
- **Deliverable tooling**: `scripts/md2pdf.py` (Markdown to PDF via a local Chromium), `md2docx.py` / `docx-to-md.py` (Word round trip; needs `pip install python-docx`), `lint-deliverables.py` (mechanical writing-protocol linter).
- **Email send gate**: `scripts/email-send-gate.py` + `.kiro/hooks/email-send-gate.json` ask before any email send, reply or forward through an email MCP server. Inert until you add one.
- **`stop-slop` skill** (third-party, MIT, Hardik Pandya; LICENSE kept): the style pass the writing and anti-slop protocols point at.

### Changed

- `save-session.py`: session-id claim, memory-index rebuild and validation, guarded deep merge, ops normalization, and a source default for new patterns.
- `maintenance.py`: missing cross-reference, `derived_from`, session-index, commitment-attribution and credential-registry checks. Its cross-reference check found and fixed 18 gaps in the seed KB.
- `session-cache.py`: FTS5 query sanitizer, so raw user text no longer breaks search.
- `validate-schemas.py` now matches the enums `save-session.py` writes: knowledge categories `personal`, `financial`, `discovery` and `negative-knowledge` (hyphen; the old validator demanded `negative_knowledge`, so a normal save could fail the pre-commit check), and pattern `context` is optional, as the writer already treated it. Unused categories (`strategic`, `faq`, `cross_platform`, `system_prompt_engineering`, `writing`) dropped; no seed entry used them.
- Seed indexes regenerated with the current writer: `reasoning-index.json` gains `byConfidence` and reuse-signal summaries, `memory-index.json` gains `_meta` (with its `_schema`) and `byConfidence`, and two stale knowledge summaries now match their entries. These are the shapes a first save would produce anyway.
- `validate-schemas.py` declares the optional fields that carry real data: patterns `provenance`, `validationNote`, `evidence_type`, `kernel_referenced`; knowledge `provenance`, `evidence_type`; reasoning `context`, `source`.
- `save-session.py` entry updates accept `"unset": [field, ...]` to remove legacy or drifted fields through the writer. Identity, audit and required fields are refused; removed values go to `_history`. Seed entries used it to drop duplicate `type` (patterns) and `category` (reasoning) fields.
- Synonym expansion fixed in `kb_query.py`: a synonym group's key term was never expanded (only the listed terms were), so headline words like "memory", "save" and "kernel" got no synonyms at all, and a term listed in two groups kept only the later group. Each term now maps to the union of all its groups. Test: `vectorstore/tests/test_synonyms.py`.
- `tests/` suite brought in line with the current scripts (it had 6-8 failures against the shipped `save-session.py` and `maintenance.py`): 208 pass, including new `test_entry_unset.py` and `test_save_session_memories.py`. CI now runs it.
- `.steering-files/settings/mcp.json`: the fetch server launched with a bare `python`, which does not exist on a stock Ubuntu/WSL install, so the fetch MCP never started there. It now starts through `scripts/run-python.sh`, which finds `python3` or `python` (and skips the Windows Store stub).
- `vectorstore/tests/test_concat.py`: the property test generated field text containing `|`, so its delimiter check failed at random (and every run once the failing example was cached). Generated text now excludes the delimiter and invalid UTF-8.
- `kiro-maintenance.sh`: reports the Kiro CLI 3.x session store (`~/.kiro/sessions`) and never prunes it; `xargs` calls split on newlines only, so paths with spaces are no longer cut apart (previously `rm -rf` missed them while reporting success).
- `gen-file-structure.py` writes the map Kiro loads (`.kiro/steering/FILE-STRUCTURE.md`).
- `Nate-Protocol.md`: removed an unrouted legacy requirements and implementation-plan block.
- Docs updated for all of the above: README, FILE-STRUCTURE, SECURITY, CONTRIBUTING, `.steering-files/README.md`, `tool-inventory.md`, `Nate's-kb/README.md`, `Intelligence/README.md`, QUICKSTART, `docs/system-maintenance.md`.

## [3.4] - 2026-07-15

- Kernel: 14 behavioral additions (Protocol-File-First rule, the four forbidden rationalizations, partial-compliance trap, prescribed output locations, Scope-Fidelity Gate and SCOPE self-check, and more).
- FILE-STRUCTURE.md became an always-loaded steering file kept current by hooks (`gen-file-structure.py`).
- Added `PRIME-DIRECTIVES.md` steering.

## [3.3] - 2026-05-04

- Completion Mandate, Grounding and Completion self-check rows, Active Capture Protocol, User Assertion Primacy, Navigation row and Cognitive Pre-Flight, Behavioral Control Pipeline, save-session cross-reference enforcement.
- Trusted internal invocation exemption and calendar commitment sync.

## [3.2] - 2026-04-17

- First public release: personality kernel with tiered gates, 15 wired protocols, intelligence suite, vectorstore hybrid search, save pipeline, 140-test suite.
