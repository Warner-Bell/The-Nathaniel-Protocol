---
name: correction-capture
description: Fires only on a [correction-loop] cue injected into context. Steps - retrieve, diagnose, record, then cite or add a directive via scripts/correction-ledger.py.
---

# Correction Capture Skill

Turns each user correction into a recorded diagnosis plus a corrective measure, so the same
mistake gets harder to repeat. The hook (`scripts/hooks/correction_hook.py`) supplies recall;
this skill supplies precision, because only the agent can see the turn being corrected.

**Database**: `Nate's-kb/Intelligence/corrections.jsonl` (raw events from the hook, diagnoses and
doc edits from this skill). The behavioral lesson also lands in `patterns.json` at save, via the
`[CAPTURE:]` marker this skill emits.
**Write path**: `scripts/correction-ledger.py` is the ONLY writer for diagnoses and for the Rules
section of `.kiro/steering/PRIME-DIRECTIVES.md`. Never `fs_write` that section directly.
**Mode**: `Nate's-kb/Intelligence/correction-loop.json`. `log` stages doc edits for user approval;
`enforce` applies them. The skill runs identically in both.

## Triggers

- A `[correction-loop]` cue in context (strong or possible correction).
- Any correction the hook missed, especially fact-phrased ones ("it's the 6-month rule",
  "I wasn't suggesting X"). The kernel Capture self-check row covers these.

## Execution (in order, same turn, before the substantive reply)

### 0. Is it a correction?
For a "possible correction" cue, look at the turn you just gave. If the user is answering a
question you asked ("nope just curious"), it is not one:
`python3 scripts/correction-ledger.py verdict <event_id> false_positive` and reply normally. Stop.

### 1. RETRIEVE before you defend
Run `kb_search` on the correction text and on the subject's domain. Read the user's project
folder research for that subject. If an entry already held the answer, the failure is RETRIEVAL,
not capture. Name the entry id; that fact drives step 4. Do not form a counter-position until
this step is done.

### 2. DIAGNOSE
- **class**: `mistake` (wrong action), `assumption` (unverified premise acted on), `assertion`
  (unsourced claim stated as fact), `behavior` (a recurring tendency), `fact` (a scoped fact was
  wrong; no behavioral lesson beyond the correction cascade).
- **violated_intent**: the user's stated or evident goal the action cut against, in their terms.
- **root_cause**: the mechanism, not the symptom. Which gate should have fired and why it didn't.
- **recurrence_of**: ids of prior patterns or ledger events with the same root cause. Check
  `patterns.json` failure entries and `correction-ledger.py stats`. A RECURRENCE flag in the cue
  means the user already said it repeats; find the prior instance.

### 3. CORRECTIVE MEASURE (pick the rung from evidence, not ambition)
| Situation | Rung | Action |
|---|---|---|
| `fact` class | `entry` | Knowledge entry + Correction Cascade Gate. Never touches the directives doc. |
| First occurrence, an existing directive governs it | `citation` | `cite <rule_no> <evidence_id>` |
| First occurrence, no directive governs it | `rule` | `add-rule` (consolidated, see below) |
| Recurrence of a cited rule | `rule_rewrite` | Sharpen that rule's wording in place (user-visible edit) + cite |
| Third occurrence, or user-flagged recurrence of a rewritten rule | `mechanical` | Propose a hook, test, or denylist rule; text has failed |

The evidence id is the ledger **event id** (`corr-...`). Never cite a planned `fail_NNN`: a planned
id is not reserved, and a concurrent save can consume it for an unrelated entry, leaving the rule
citing the wrong evidence. Cite a `fail_NNN` only
if that pattern is already written in `patterns.json` and names this event in its `evidence`.
If a wrong cite lands anyway, repair it with `recite` (below); `stats` flags it.

**Rule-writing standard** (when `add-rule`): one behavior per rule, phrased as an imperative,
ALL-CAPS title, no em dashes, no user-specific facts (those are knowledge, and the doc has a
template twin). Before adding, re-read the Rules section and ask whether an existing rule covers
it with a sharper word. If yes, it is a citation or a rewrite, not a new rule. The script refuses
new rules past the line cap; that refusal means consolidate.

### 4. RECORD
```
python3 scripts/correction-ledger.py diagnose <event_id> --json '{"verdict":"genuine",
  "class":"...","violated_intent":"...","root_cause":"...","corrective_measure":"...",
  "rung":"...","governing_rule":N,"recurrence_of":[...],"retrieval_miss":"know-NNNN or null",
  "capture_id":"<event_id>"}'
python3 scripts/correction-ledger.py cite N <event_id> --event <event_id>     # or add-rule
```
Then emit the marker so save consolidates it into `patterns.json`, with no planned id in it (save
assigns the id; put the event id in the pattern's `evidence` field):
`[CAPTURE: failure, <what happened> | event: <event_id> | intent violated: <...> | root cause: <...> | measure: <...>]`
(or `correction` for the fact class). If no event id exists (hook missed it), use
`--allow-missing` with a `corr-manual-YYYYMMDD-HHMM` id.

Repair a wrong cite: `recite N <old_id> <new_id> --reason R --event <event_id>` (swaps the cite,
appends a corrected diagnosis). Diagnosis only: `amend-capture <event_id> <new_id> --reason R`.
Before `apply` on a staged cite, run `stats` and clear any citation-audit flag first.

### 5. RESPOND
One line acknowledging the error, then fix the actual thing the user asked about. Report the
measure in one line (`Logged corr-...; cited into Rule 4` or `staged rule 26, apply with ...`).
Do not narrate the skill.

## Anti-Patterns (DO NOT)

- Defend first and retrieve second.
- Write a new rule for a behavior an existing rule already covers.
- Put a scoped fact into the directives doc.
- Mark a correction `false_positive` to avoid the work.
- Edit the Rules section with `fs_write`.
- Apply a staged edit in `log` mode without the user's go.
