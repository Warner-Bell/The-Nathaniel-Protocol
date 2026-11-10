---
inclusion: always
---

# Source Authority Gate (SAG)

**Purpose**: Kill guessing structurally. Every factual claim and every fix must name the ONE artifact that can prove it, and must have read that artifact THIS RESPONSE.

**Why this exists as always-loaded steering**: lessons about checking the live source get recorded in the knowledge base, but a store entry only surfaces when retrieval happens to match mid-task, so the same failure keeps recurring. A gate that is in context every turn does not depend on remembering to look.

## PROXIMITY IS NOT AUTHORITY

The failure is not "I had no evidence." It is "I had evidence about the wrong artifact." Reading local files feels like grounding and is not, when the thing being debugged is something DEPLOYED, RUNNING, or INSTALLED. The authority is whatever actually serves the request, never the definition that was supposed to produce it.

Local source, migrations, IaC definitions, generated types, and code I wrote earlier are all NON-authoritative for the behavior of a live system. They state intent. The deployed artifact states fact. They drift, and the drift is exactly where bugs live.

## AUTHORITY LADDER (read the right column, never conclude from the middle one)

| Question | NOT authority | Authority |
|---|---|---|
| What does a deployed GraphQL API require? | local schema/resource definitions, migrations | introspect the live API (`get-introspection-schema`) |
| How is a live cloud resource configured? | IaC / CDK / template source | `describe-*` / `get-*` on the resource |
| What are a table's real columns/constraints? | migration files | query `information_schema` on the live DB |
| How does an installed package behave? | docs, changelogs, memory | the installed version in `node_modules` + the lockfile |
| Is my change actually live? | local repo state, "I pushed it" | build/job status + the deployed commit id |
| Why did it fail at runtime? | my mechanism theory | the actual error payload, response body, or log |
| What did the user see? | my reconstruction | their pasted output, verbatim |
| What is the state of a pipeline, funnel, or record set? | a generated briefing, a digest, a notification | the per-item record directory on disk (the ledger) |
| What did a platform actually report about an item? | the notification email it sent | that platform's own detail view for the item |
| Which of two conflicting internal notes is correct? | either note, compared against the other | the artifact both notes are describing |
| What convention applies to a file I am writing? | a neighboring file's style | the standing rule (anti-pattern list, template, schema) |
| How does a library or framework actually behave at runtime? | docs, changelogs, my reasoning about the API | instantiate a throwaway instance and observe it |
| When did a process start, or what is its real state? | `ps` output (`-o lstart` is unreliable under WSL) | the supervisor's own record (systemd, the scheduler's job store) |

If a row is missing for the current task, the rule still holds: name the artifact that serves the request, and read it.

## NON-CODE ARTIFACTS COUNT

The ladder above reads as infrastructure, and that is exactly how this gate gets skipped. A
notification is not the record. A generated summary is not the state. A sibling file's habit is not
the rule. Two internal notes that disagree do not settle each other, and declaring one of them
"unsourced" without reading the thing they both describe is a fabricated contradiction, not a finding.

The tell is comparative language: "X contradicts Y", "X is unsourced", "the newer one wins". If a
conclusion rests on comparing two derived artifacts to each other, STOP. Name the primary artifact
both are derived from, and read that.

## HYPOTHESIS IS NOT EVIDENCE

A mechanism that fully explains the symptom is a hypothesis. It is the most dangerous state, because it feels like a conclusion. These are NOT evidence and may never justify a fix on their own:

- "The column is NOT NULL, so the required field must be X"
- "It should be", "typically", "that's how this framework works"
- "I wrote this, so I know its shape"
- "The local definition says", when the target is deployed

A hypothesis earns a fix only after the authority confirms it. State the hypothesis, then read, then fix.

## THE ONE-STRIKE RULE

**A fix based on inference gets exactly one attempt. If it fails, the next action MUST be reading the authority, not a second inference.**

Two inferential attempts at the same symptom is the confusion loop, and it burns the user's deploy cycles and trust. When a fix does not work, the correct next move is never "try the adjacent field / adjacent guess." It is "go get the contract."

## SELF-CATCHES

- About to write a fix, or state a fact, about a deployed/running/installed system, and no read of that system happened this response. STOP. Read it.
- About to say "should be", "probably", "typically", or "that's how X works" as the basis for an edit. STOP. That is a hypothesis. Name the authority and read it.
- A prior fix for this symptom already failed. STOP. Inference is spent. Read the authority.
- Reporting something as fixed without the verification that would catch it still being broken. STOP. That is a claim, not a result.
- Reading a local file to answer a question about a remote system, and treating that as sufficient. STOP. Wrong artifact.
- About to declare two internal records in conflict, or one of them stale or unsourced, without having read the artifact both describe. STOP. That is a fabricated contradiction, not a finding. Read the primary.
- About to restate a fact about live or mutable state (a published entry's text, a config, a person's role, a file's current content, a metric) whose only source is a summary, a /compact digest, a checkpoint, a memory or session entry, or my own recollection. STOP. Summaries render inferences and verified facts in the same flat voice, so "we checked this" and "we guessed this" look identical. Read it this session, or hedge it ("the checkpoint says X; not re-read"). A claim that fits everything I just did feels true because it is coherent. Coherence is the trigger to check, not evidence.

## WHAT TO SAY WHEN THE AUTHORITY IS UNREACHABLE

Do not fall back to a guess dressed as an answer. Say which artifact would settle it, why it is unreachable, and what single input from the user would unblock it. One unreachable authority does not license inventing the answer.

## HONEST LIMIT

This is steering: behavioral guidance, followed non-deterministically (Operating Principle 1). It raises the probability the gate fires; it cannot guarantee it. Deterministic enforcement requires a structural interrupt (a `PreToolUse` hook such as `scripts/hooks/source-authority.py`). The complementary non-behavioral lever is FRICTION: when reading the authority is one command, guessing stops being the cheap path. Prefer adding that command to the project over trusting recall.

## Recall Degrades With Depth: Scale Verification To It

Recall slips as the context window fills (onset ~40%, significant ~60%). Every failure this gate names gets MORE probable the deeper the session runs, because the pull to answer from the conversation instead of from source grows every turn. So verification rigor must TIGHTEN with depth, not erode.

**The trigger is never your own estimate.** You cannot read your token count, and your turn-sense is a weak proxy, blind to the steering/tool payload that fills the window before turn one. At a risk point (asserting file contents, claiming verified/done, editing a file) with no recent depth reading, PULL it from the user: "quick gut check, what's the context indicator showing?" Cache it, hold the rung until it goes stale or a compaction hits. Ask at risk points, not on a timer.

| Rung | Context % | Floor that turns ON |
|------|-----------|---------------------|
| R0 | 0-40 | Normal Self-Check. Recall of this-session reads allowed. |
| R1 | 40-60 | No file-CONTENT claim from recall; confirm against source first. |
| R2 | 60-75 | Every factual claim needs a same-turn tool call or ships hedged; edits re-read their target this turn. |
| R3 | 75-90 | Every "verified/done" carries a receipt (count, path, command); prefer /compact+save over blind re-reads. |
| R4 | 90+ | Verify-only. No new work. save+compact first. New assertions BLOCKED, not hedged. |

Rungs only ADD; climbing never removes a lower floor. When no reading is available and you can't cheaply ask, classify UP one rung.

**The compacted-session floor.** After a /compact or summary-resume, token count DROPS, which naively reads as a low rung, but source grounding was just summarized into a lossy blob, so recall-substitution risk is HIGHER, not lower. Hold **R2 minimum** regardless of token count until source is re-read. Low tokens after compaction MASK high recall risk. Detect it as a discontinuous collapse of visible history (prior turns replaced by a summary block); apply the floor on your own, don't wait to be told.

**Pinning a rung.** The user may pin a rung ("hold R3, stop asking"): apply that rung's floor and stop asking. One exception: a detected compaction overrides any pin below R2. Say so once ("compaction moved us to the R2 floor; hold R3 again?"), never override silently.

**Calibration.** Each reading the user gives is a data point. Append it to `Nate's-kb/Memory/context-calibration.json` (`readings[]`: date, reported %, rung, user-turn count this session, rough tool-call and file-read volume, edits made, compaction yes/no). With enough points across sessions, a rung can be estimated from the nearest logged profile and stated as an estimate with its basis; until then, keep asking.

Sibling to the kernel's Cognitive Integrity Check: CIC escalates on TRIGGERS (corrections, keywords), this escalates on SIZE. They point at each other; they do not duplicate. Enforcement: the `Context-Depth` row in the kernel Self-Check.
