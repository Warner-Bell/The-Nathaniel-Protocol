# Writing Protocol

**Keywords**: write, writing, document, memo, report, email, update, brief, draft, edit, review-doc, 6-pager, narrative, thread, slack, letter, correspondence, communication, message, compose
**Purpose**: Writing standards for all written deliverables
**Last Updated**: 2026-11-10
**Version**: 2.3 (Consumable Output Standard, Gate 0 Pre-Delivery Integrity wired to anti-slop-protocol.md, do not recite facts the reader owns, lead each beat with its substance, more throat-clearing openers)

---

## Section Routing (TOC-Dynamic-Loading)

**Load only the section(s) matching task keywords. Fallback to full load if ambiguous.**

| Keywords | Anchor | Lines | Description |
|----------|--------|-------|-------------|
| standards, voice, tone, audience, concise | #standards | ~105 | Basic writing standards and voice |
| format, typography, headers, lists, tables | #formatting | ~70 | Formatting and typography rules |
| 6-pager, narrative, email, memo, template, brief | #documents | ~390 | Document types and templates |
| process, draft, edit, review, checklist | #process | ~120 | Writing process and quality checks |
| quick, reference, rules | #reference | ~22 | Quick reference card |
| consumable, readable, report, findings, hand-off, deliverable doc | #consumable | ~35 | Consumable Output Standard: the required readable shape for any deliverable |
| clean, deliverable, artifact, noise, meta, hygiene, strip, notes, caveat | #hygiene | ~45 | Keeping meta, notes, caveats, and scaffolding out of the finished deliverable |

**Multi-section triggers**:
- "write email" → #documents only
- "format 6-pager" → #documents + #formatting
- "review draft" → #process + #standards

**Fallback**: Load full document if no keywords match or request spans 3+ sections.

---

## Integration Notes

### With Decision Engine
- Triggered during Phase 2 (KB Consultation) when writing keywords detected
- Applies to all written output: documents, emails, reports, summaries, briefs
- Takes precedence over casual communication style for formal deliverables

### With Other KB Documents
- For meeting summaries: Use summarization-protocol.md for structure, this doc for prose style
- For customer deliverables: Use relevant domain protocol for content, this doc for writing quality
- For technical documentation: Use development-protocol.md for technical accuracy, this doc for clarity
- For a final anti-slop editing pass: Use the `stop-slop` skill (`.kiro/skills/stop-slop/`), a scored slop-removal lens (curated banned phrases, structural cliches, active-voice rules) that complements this protocol. This protocol governs the craft upstream; stop-slop is the finishing pass.
- For document integrity (every claim proven, confabulation, stale figures, invented options, misquotes): `anti-slop-protocol.md`. The Pre-Delivery Integrity Gate (Gate 0 in #process) runs it in full for consequential, external, client-facing, published, or leadership deliverables. stop-slop checks style; anti-slop checks truth. On conflict, this protocol and the kernel Anti-Patterns win.

### Personality Integration
- All outputs filtered through Nathaniel.md personality kernel
- Maintain Nate's cultural voice and communication style
- See: Nathaniel.md for voice, values, and behavioral patterns

---

## Core Principles

### The Writing Philosophy

1. **Narrative over bullets**: Full sentences force complete thinking. Bullet points hide sloppy logic.
2. **Clarity is kindness**: Readers should never re-read a sentence to understand it.
3. **Data proves impact**: Claims without metrics are opinions.
4. **Respect reader time**: Every word must earn its place.
5. **Outcome-driven**: Every document has a purpose (inform, decide, align).

---

## Non-Negotiable Constraints

These override style preferences and apply to EVERY written deliverable, including speaker notes, drafts, and any content the user will publish, send, or present. A violation here is a correctness failure, not a stylistic one.

### 1. No AI-cliché constructions, buzzwords, or em dashes

Per kernel Anti-Patterns (always loaded): the "not just X, it's Y" family, the corporate-buzzword list (leverage, seamless, robust, elevate, unlock, delve, and the rest), and em dashes are already banned repo-wide. They apply here too. State the thing directly.

### 2. No unverified or confabulated content

Every factual claim, capability, number, name, date, or subject-matter assertion must trace to a verified source: the project spec or requirements doc, official docs, prep material, or something confirmed this session. If it is not verified, it does not go in the deliverable.
- Do not invent capabilities, integrations, metrics, or features.
- Do not upgrade "in preview" to "GA," "customers report up to" to "delivers," or "estimated" to "measured."
- If a claim cannot be verified, omit it or flag it explicitly for the user to confirm. Never paper over a gap with plausible-sounding filler.
- The operational form of this constraint is `anti-slop-protocol.md`. Run it in full for any consequential, external, client-facing, published, or leadership deliverable, and on any request to check, audit, fact-check, or slop-check a document. See Gate 0 in #process.

### 3. No shortcuts under context pressure

Do the full due diligence every time: read the source, verify the claim, write it properly. A long session, heavy context, or a large task is never a reason to write from recall, skip a source read, abbreviate the work, or lower quality. If the work is large, do the work.

### 4. The user is the sole arbiter of context depth

The user decides how deep the context runs and when compaction happens. Never self-abbreviate, self-summarize, silently reduce scope, or invoke "context is getting heavy" as a reason to cut corners. If compaction or a fresh session seems warranted, surface it as a recommendation and let the user decide. The call is theirs.

---

<!-- #consumable -->
## Consumable Output Standard (MANDATORY for deliverables)

Any document meant to be read or sent (report, findings, brief, summary, analysis, hand-off note, review) must be consumable: a reader who is not deep in the specifics should be able to follow it. Apply all seven:

1. **Lead with a plain "short version."** State the bottom line and the headline takeaways in everyday language before any detail, table, or evidence. A reader who stops after the first screen still gets the point.
2. **Define the terms up front.** Give a short glossary for any jargon or acronym the reader needs, and expand every acronym on first use.
3. **Explain with a concrete example.** Every technical or abstract point gets one plain, specific example that shows why it matters. A point the reader cannot picture is not consumable yet.
4. **Narrative over data dumps.** Tell what happened, what was learned, what resulted. Lead with the anchor or best result, and compress noisy, broken, or heavily caveated detail into brief narrative instead of dropping every run, table, or dataset into the body.
5. **Evidence to an appendix.** Exact references, line-level proof, and full datasets go at the back for readers who want them. The body must read cleanly without it.
6. **Balance.** For feedback, review, or test-result docs, include a short "what worked well," not only the problems.
7. **Plain language.** Short sentences, one idea each, name a thing before referring to it. The expertise rules in #standards still hold: do not explain an expert reader their own domain.

**Two halves of a good deliverable.** This standard governs STRUCTURE (is it clear?). Gate 0 in #process governs TRUTH (is it correct?). Deliverable Hygiene below governs NOISE (is anything in it that does not belong?). A deliverable passes all three.

**Person.** First person is correct for a personal note to a colleague or client, the same relaxation granted to speaker notes and replies. Third person stays the default for formal reports.

**Delivery.** When the deliverable will be handed to someone outside the chat, also produce a clean, readable PDF with `python3 scripts/md2pdf.py SOURCE.md OUT.pdf "Title"` (Word: `scripts/md2docx.py`) and give the path. Keep the editable source beside it.

<!-- #hygiene -->
## Deliverable Hygiene (No Noise, No Artifacts)

A deliverable contains only what belongs in the finished product. Working notes, reasoning, caveats, review flags, and process scaffolding live elsewhere, the chat reply, a companion review doc, or the session log, never baked into the artifact the user will use, send, sign, or publish.

**The test before delivering:** if the user handed this to a third party as-is, would anything read as a note to themselves, a message from the assistant, or drafting scaffolding rather than part of the product? If yes, strip it.

### Strip from every deliverable
- **Assistant voice / conversational text.** The artifact does not talk to the requester. No "here's what I did," no "let me know if," no addressing the user inside the artifact.
- **Notes to the requester.** No "(Owner to complete)", "(confirm with X)", "TODO", or instructions aimed at the person the deliverable is for. Genuine fill-in fields a third party completes (blank name, date, amount) are not notes and stay.
- **Review / flag tags.** No inline "[ATTORNEY]", "[REVIEW]", "[TBD]" markers. If something needs review, say so in the accompanying message or a separate doc, not in the artifact.
- **Rationale and design commentary.** No "why I chose this" tables, no "design decisions baked in" preambles. The artifact states what it is, not how it was built.
- **Caveat / draft disclaimers.** No "this is a draft," "not final," "verify before relying" embedded in the body. A disclaimer the deliverable's own domain requires, such as a contract's governing-law or not-legal-advice clause the user asked for, is content, not meta, and stays.
- **Provenance / meta footers.** No "prepared by [assistant] on [date] after X review" trailers, no citations of the internal research that produced it, no changelogs addressed to the user.
- **Structure notes.** No "this section covers," no meta-labels explaining the document's own layout.
- **Unrequested summaries and preambles.** Do not open with a recap of the request or close with a summary of what was produced, unless the deliverable's format calls for it.

### Where the stripped material goes
- Caveats, open questions, review items: the chat reply, or a separate companion doc clearly distinct from the artifact.
- Reasoning and provenance: the session log and intelligence capture.
- Status (draft vs final): filename or file location, not a banner inside the document.

### Scope
Applies to every deliverable: legal documents, letters, emails to send, published content, code files, configs, reports handed to others. When the user asks for "the doc," "the deliverable," or to "clean it up," default to zero meta and put any caveats in the chat beside it.

### Live documents state only the present
A live operating document (disclosure packet, lease, procedure, checklist, listing, status tracker) describes the current state, never the history of how it reached that state. When a requirement moves from unmet to met, **delete the old entry and state the requirement as met, or omit it entirely if being met makes it a non-issue.** Do not narrate the transition. A reader opening the document for the first time needs the current requirement and how to act on it, not the changelog of its authorship.

Strip from live docs:
- **Status-change narration.** No "RESOLVED 2026-08-15," "REMEDY DECIDED," "was a blocker," "previously unmet, now met," "corrected, an earlier note said X." If it is true now, state it now; if it is no longer an issue, delete it.
- **Dated working annotations.** No "confirmed 2026-08-02," "updated 2026-08-13," "added [date]" tags on facts. Operational dates that are content (a statute's effective date, a deadline, an event date) stay; annotations recording when a line was verified do not.
- **Internal references.** No session IDs, memory/knowledge/pattern IDs (know-###, pref_###, session-###), or "see session notes." Those point at the workshop, not the product.
- **Resolved-question scaffolding.** Once a question is answered, the answer is the content. Drop the "open question / determination / RESOLVED" framing and keep the resolved fact.

Where it goes: the transition history, the resolved blockers, the dated verifications, and the reasoning all live in the session log and intelligence capture, not in the operating document.

### Client-Facing Artifacts: Leak Sweep (MANDATORY before send)

Complementary to the strip rules above. Documents authored in-session inherit conversation voice and internal context. Before ANY client-facing deliverable (doc, spreadsheet, deck, email attachment) ships, sweep EVERY cell and line for these three leak classes:

**1. Internal information**
- ❌ Internal program, tool, or codename references
- ❌ Internal repo or file paths (`Nate's-kb/`, `C:\`, workspace paths, `/mnt/`)
- ❌ Internal process references (session logs, memory IDs, agendas, tickets, chat channels)
- ✅ Public-facing equivalents only

**2. Conversation-voice leakage (assistant-to-user dialogue frozen into the doc)**
- ❌ "your [X] email to [person]": second person addressing the author, not the reader
- ❌ "my proposed call", "my logic": first-person advisory voice in a shared artifact
- ❌ "per our conversation", "as we discussed", "as requested"
- ✅ Depersonalize: state the fact, not the exchange that produced it
- **The test**: who is the READER? If the doc reads as if addressed to the user instead of the client, the conversation leaked in.

**3. AI output artifacts**
- ❌ Markdown syntax in non-markdown formats (`**bold**`, `##`, code fences in spreadsheet cells)
- ❌ Preamble/closer phrases: "Here's the...", "Certainly", "I hope this", "Let me know if", "Feel free to"
- ❌ Model or assistant references of any kind

**Sweep execution**: enumerate the FULL population (every sheet, every cell; every line), not a spot-check. Template boilerplate that legitimately says "you/your" (e.g., a vendor questionnaire's own instructions) is exempt; anything authored this side of the template is not.

---

<!-- #standards -->
## Basic Writing Standards

### Voice and Perspective

**Active Voice Required**
- ✅ "The team completed the migration"
- ❌ "The migration was completed by the team"

**Third Person Only**
- ✅ "The engineering team identified three risks"
- ❌ "We identified three risks"
- ❌ "I found the issue"
- Use proper nouns, team names, or role titles instead of first person (I, we, our, us)

### Audience Calibration

| Audience | Approach |
|----------|----------|
| Line Manager | Detailed, tactical, include execution specifics |
| Senior Leadership (L8+) | Strategic context, business impact, avoid technical jargon |
| Technical Peers | Precise terminology, implementation details acceptable |
| Customer-Facing | Plain language, outcome-focused, no internal acronyms |

**Rule**: Senior audiences need MORE context about why, LESS detail about how.

### Respect the Reader's Expertise

Write to the reader you have, not a novice. For capable and senior readers (architects, senior engineers, specialists, experienced clients), assume competence and never explain their own domain back to them.

- **Do not teach the reader their own craft.** State a distinction in their vocabulary instead of defining the concept. "The cert date bounds domain control, not IP tenure" respects an architect; "a certificate is misleading because it proves control of the domain, not the address" lectures one.
- **Do not spell out an implication the reader reaches in one step.** Telling an experienced operator "one record is housekeeping, several is an inventory question" explains what they already know.
- **Do not recite facts the reader owns.** Their own launch date, that a system is theirs, what their team built: none of it is news to them. Lead with your read on it (the significance, the outside view, the non-obvious synthesis), not the fact they already hold.
- **Do not append an unrequested how-to.** A capable reader asked a question, not for a runbook of their own tools. Give the answer plus the genuinely non-obvious insight; offer the step-by-step only if they ask. Over-delivery reads as condescension.
- **No performative deference.** Cut "you're better placed than I am" and similar. State the fact and stop; hollow deference is as off-key as talking down.

**The test**: would a peer of equal expertise find this respectful or patronizing? When in doubt with an expert audience, assume they know it.

### Conciseness

- Cover fewer topics deeply rather than many topics thinly
- Question every word: "Does this add value?"
- If a sentence works without a word, remove the word
- Target: Say it in half the words, then cut again

### Cut Meta-Padding

Strip two padding patterns on every edit pass:

- **Contrastive filler ("X, not Y").** When the foil adds nothing, drop it and state the thing directly. "The reason is forensic" beats "the reason is forensic, not operational." Keep the contrast only when the reader would otherwise assume the wrong thing, where it is load-bearing rather than padding.
- **Value-hedging and throat-clearing.** Cut openers that question the worth of your own content, merely announce you are about to speak, or justify the structure before delivering it: "If it's useful, here's...", "One thing worth knowing...", "The question I'd want answered is...", "Let me walk you through...", "Let me start by...", "There's more than one thing going on here, and they're separate...". If a point earns its place, state it plainly; if it needs an apology to justify being there, cut it.

### Plain Language

- ✅ "Start" not "Initiate"
- ✅ "Use" not "Utilize"
- ✅ "Help" not "Facilitate"
- ✅ "End" not "Terminate"
- ✅ "Show" not "Demonstrate"

Complex terminology is acceptable only when precision requires it.

### Required Elements

**Misses/Lowlights/Concerns/Risks MUST include:**
1. Action: What will be done
2. Owner: Who is responsible (by title, not name)
3. Path to Green: How it gets resolved
4. Date: When the next step occurs

**"Will" statements MUST include a date:**
- ✅ "The team will complete testing by January 15"
- ❌ "The team will complete testing soon"

**Every document MUST state its outcome:**
- Purpose: Inform, Request Decision, Align, or Escalate
- State this explicitly in the opening

### Data and Metrics

**Show impact, not tasks:**
- ❌ "Completed 47 support tickets"
- ✅ "Reduced average resolution time by 23%, improving customer satisfaction scores from 4.1 to 4.6"

**Support claims with data:**
- ❌ "Performance improved significantly"
- ✅ "Latency decreased from 450ms to 120ms (73% improvement)"

**Never hedge a figure a source already read states exactly.** A hedge is honest only when the number is genuinely unknown. If the exact figure is sitting in data already pulled this session, look it up rather than approximating it. The correction is never "hedge more carefully," it is "the number was on disk."
- ❌ "roughly half the accounts sit there"
- ✅ "16 of the 22 accounts, in two of the six regions"
- **Self-catch**: before writing *roughly*, *approximately*, *about*, *most*, or *a majority*, ask whether any artifact already open would state it precisely.

**Scope every claim to what was actually checked, not to what it feels like you covered.** Coverage language drifts toward totality on its own. "Across the rest of the footprint" reads as complete when several segments were never read; naming the three actually checked costs the same words and is true. Derived or estimated figures stay out of client-facing prose entirely when a verified count makes the same point.

### Prohibited Patterns

**ING Words at Sentence Start**
- ❌ "Finding that the results were positive..."
- ✅ "The analysis found positive results..."
- Use sparingly within sentences

**Hedge Words (Weasel Words)**
| Avoid | Replace With |
|-------|--------------|
| some | specific number or percentage |
| many | specific count |
| few | exact quantity |
| sometimes | frequency (e.g., "in 3 of 10 cases") |
| significant | measurable impact |
| great/good/bad | specific metrics |

**Words of Intention**
- ❌ "aim to", "hope to", "plan to", "intend to"
- ✅ State the commitment: "will [action] by [date]"

**Ambiguous Referents**

Every pronoun, and every bare *none*, *them*, *those*, *it*, or *that*, must have exactly one possible antecedent. This matters most when answering a **negatively phrased question**, where a loose referent can invert the entire claim.

- ❌ "Which roles do NOT have these permissions?" → "very likely none of them"
- ✅ "very likely none of the roles are missing those four permissions"

The first parses equally as *none of them have the permissions*, the opposite of the intended answer, on the single most load-bearing sentence in the reply. **Self-catch**: after writing any sentence containing *none*, *them*, or *those*, re-read it assuming the reader inverts it. If that reading is coherent, name the noun and name the condition.

### Naming Conventions

**Use formal names and titles:**
- ✅ "VP of Engineering" not "John Smith"
- ✅ "Engineering Team" not "the eng folks"
- ✅ "Enterprise Support" not "ES team"

**Exception**: Customer names in customer-specific documents

### FAQs and Appendices

- Include based on anticipated questions
- Avoid "kitchen sink" approach
- Appendices support the narrative, not replace it
- Reference appendices in main text

---

<!-- #formatting -->
## Formatting Standards

### Typography

| Element | Standard |
|---------|----------|
| Document text | 10 pt Calibri |
| Email text | 10 pt Ember |
| Page numbers | 9 pt, "Page 1 of X" format |
| Margins | Minimum 0.75" left/right |
| Line numbers | Required for review documents |

### Numbers

| Type | Format | Example |
|------|--------|---------|
| 1-9 | Spelled out | one, two, three |
| 10+ | Numerals | 10, 25, 100 |
| Comparisons | Numerals for both | "8 to 13 people" |
| Large numbers | Numeral + suffix | "3MM", "1.2B" |
| Percentages | Numeral + % | "23%" |

### Dates

**Format**: Month Day, Year
- ✅ "December 12, 2025"
- ✅ "December 12" (if single year context)
- ❌ "12/12/25"
- ❌ "Dec. 12, 2025" (unless consistently abbreviated throughout)

**Year inclusion**: Only required when multiple years referenced in paragraph

### Acronyms

**First occurrence**: Spell out with acronym in parentheses
- "Project Manager (PM)"
- "Strategic Support Plan (SSP)"

**Subsequent occurrences**: Acronym only
- "The lead completed the security review"

### Punctuation

**Oxford Comma**: Required
- ✅ "compute, storage, and networking"
- ❌ "compute, storage and networking"

**Ampersand (&)**: Avoid unless part of proper name
- ✅ "Security and Compliance"
- ✅ "AT&T" (proper name)
- ❌ "Security & Compliance"

### Document Length

- **Maximum**: Six pages (excluding appendix)
- **Appendix**: No hard limit, but respect reader time
- **Executive summaries**: One page maximum

### Consistency Rule

Even when unsure of a convention, maintain consistency throughout:
- Capitalization patterns
- Acronym usage
- Date formats
- Structure and tone
- Formatting choices

---

<!-- #documents -->
## Document Types

### Narrative Document (6-Pager)

**Title Format**: [Title for your narrative] -[Date]

**Structure:**

#### 1. Purpose (Required)
State what you need to happen and why it matters. If requesting a decision, state it up front.

**Format**: 2-3 sentences maximum
**Example**: "This document presents a recommendation to reallocate X resources from Project X to Project Y. The proposal will result in Z profit over five years. Leadership approval is requested to implement the reallocation before end of Q3."

#### 2. Background
Share context and data behind the topic. Include information that supports the purpose and helps readers understand the problem/opportunity.

**Tips**:
- Put extra context in appendix if only some readers need it
- Can merge with Problem/Opportunity section if appropriate
- Focus on what supports the purpose statement

#### 3. Problem/Opportunity (Critical Section)
This is the most important section. All discussions, solutions, and arguments rely on correctly identifying the customer problem/opportunity.

**Requirements**:
- Describe the customer problem and/or opportunity
- Include data, details, and evidence supporting the purpose
- Explain why readers should care
- Use sub-headings to divide parts of the problem if needed

**Rule**: Demonstrate customer obsession. Data is evidence for the argument.

#### 4. Recommendation
Define the solution(s) to the problem. Write out the proposed initiative, strategy, or solution with supporting evidence.

**Requirements**:
- If decision needed, clearly state what is needed
- Only include content that helps stakeholders decide
- Include full data sources in appendix
- Use data to make arguments specific
- Highlight the best recommendation and why (with supporting data)

**Multiple recommendations**: Acceptable, but identify the preferred option with rationale.

**Note**: Documents without recommendations are rare unless specifically requested by leadership.

#### 5. Next Steps
State what is recommended and what decisions are needed.

**Include**:
- What needs to happen next and when
- Who is involved/affected
- How to move forward
- Missing data and plan to gather it

**Rule**: The bigger the ask, the more supporting data required.

#### 6. Summary (Optional)
For 5-6 page documents, recap main data points and what readers should do.

**Use when**: Document is long or problem/solutions are complex.
**Purpose**: Help readers transition into discussion.

#### 7. FAQs (Optional)
Address questions and objections raised during stakeholder feedback.

**Format**:
```
FAQ1: [Question]?
[Answer with supporting data]

FAQ2: [Question]?
[Answer with supporting data]
```

**Tip**: Questions asked during feedback will likely be asked again. Prepare data-backed answers.

#### 8. Appendices
Supporting evidence and reference material directly relevant to the narrative.

**Rules**:
- Support the narrative and purpose only
- Do not sneak in content that did not fit in the narrative
- Include complete data sets when specific data points used in body
- Label consistently: Appendix A, B, C or Appendix 1, 2, 3

**Format**:
```
Appendix A: [Title]
[Supporting evidence]

Appendix B: [Title]
[Reference material]
```

---

### Narrative Document Rules

- **Narrative prose**: Full sentences, not bullets (bullets hide sloppy thinking)
- **Maximum 6 pages**: Appendix is separate and does not count
- **Silent reading**: Documents read silently at meeting start (20-25 minutes)
- **Data-driven**: Every claim supported with evidence
- **Customer obsession**: Problem/Opportunity section demonstrates understanding of customer needs

### Status Update

**Structure:**
1. **Summary**: One paragraph, key outcomes
2. **Highlights**: What went well (with metrics)
3. **Lowlights**: What needs attention (with action/owner/date)
4. **Risks**: Potential issues (with mitigation)
5. **Next Period Focus**: Priorities ahead

**Rules:**
- Outcome-focused, not task lists
- Every lowlight has a path to green
- Metrics prove progress

### Decision Document

**Structure:**
1. **Decision Required**: Clear statement of what needs deciding
2. **Background**: Context for the decision
3. **Options**: 2-4 alternatives with tradeoffs
4. **Recommendation**: Preferred option with rationale
5. **Impact**: What changes based on decision
6. **Timeline**: When decision needed, implementation dates

**Rules:**
- State recommendation clearly
- Present options fairly
- Include dissenting views if relevant

### Speaker Notes (Conversational Talk Tracks)

Speaker notes are spoken talk tracks, not prose documents. They are the one deliverable where the third-person and active-only rules are relaxed: notes are first-person, addressed to the room, in the presenter's natural speaking voice.

**Voice (the presenter's speaking style is the reference standard):**
- First person, conversational, spoken cadence. Contractions welcome ("you've," "I'll," "let's").
- Short paragraphs, one beat each. Natural connective openers are fine here ("So," "And," "Now") because that is how people actually talk.
- Warm and direct. Sound like a person walking the room through it, not a script reciting facts.
- Do not cram every slide fact into the note. Say the beat that matters, in plain words, and move.
- Address the audience directly ("you," "your setup"); name people in the room where it personalizes.
- **Lead each beat with its substance, not an announcement of it.** A one-word connective ("So," "Now") is fine; a preamble that describes the tour or justifies the structure is not, even in notes: no "Let me walk you through...", "Let me start by...". If two efforts must be kept separate, signal it at the second one, not as an opening preamble.

**Still binding on speaker notes:**
- All Non-Negotiable Constraints above (no AI clichés or buzzwords, no unverified or confabulated claims, no context-pressure shortcuts, user owns context depth).
- Accuracy to source. Use the exact capability language from the spec or official docs, not a loose paraphrase.
- Honest framing stays intact: "in preview," "customers report up to," "the credit is an offset," and any read-only or scope boundaries.

**Reference example (first-person intro, the presenter's own phrasing):**
> Thanks. I'm [name]. I work on [product], and [colleague] brought me in to walk you through the new features.
>
> You've seen [product] before, during the public preview, when it was limited to [scope]. Since then the capability set has expanded well past that.
>
> There were a few use cases you were interested in seeing. So today I'll share what's live now and demo some of it through the lens of your use cases.
>
> So let's get started.

---

### Email Communication

**Structure:**
1. **Greeting**: Warm, human opening (not optional)
2. **Subject Line**: Action required + topic + deadline (if applicable)
3. **Context**: Brief background with personal touch
4. **Details**: Supporting information
5. **Ask**: Clear request or next step

**Rules:**
- One email = one topic
- Action items bolded or bulleted
- Respect inbox: could this be shorter?
- **Warmth is required, not optional**: Every email should feel like it's from a person, not a process. Start with a genuine greeting. Ask how they're doing. Reference shared history when relevant.
- BLUF (Bottom Line Up Front) applies to the business content, but comes AFTER the human greeting
- Cold, transactional emails damage relationships. Efficiency without warmth reads as indifference.
- **Cutting scope does not license cutting warmth.** When a draft is trimmed for scope creep or length, the greeting, the empathy line, and the human close are NOT the padding being removed. They are the smallest part of the word count and the first thing an aggressive edit deletes. Trim the unasked-for content; keep the person.

**Reply calibration (peer / technical threads)**

For a working reply into an active multi-recipient thread with a technical peer or client:

- **Address the room, not just the sender.** When the thread has multiple recipients, open "Hi [name] and team," not just the person who wrote last. Everyone on it is reading.
- **Thanks is one line.** Acknowledge, then go straight to substance. Cut the editorializing follow-on ("this is exactly what we needed", "great to hear", "this is huge"). The thanks carries the warmth; the sentence after it is filler.
- **One acknowledgment, maximum.** Keep a single earned "good catch"; cut softer second validations and anything that restates what the recipient already knows (their own setup, their own config). Piling on praise reads as filler, not warmth.
- **Hedge a finding you have not independently confirmed.** A finding that came from your own analysis rather than the recipient's confirmation is surfaced as "looks to be" or "worth checking", never asserted as fact. Reserve flat assertions for what is verified. Extends Non-Negotiable Constraint 2: an unverified claim is hedged, not stated, even when you believe it is right.
- **Do NOT offer a call, meeting, or live walkthrough as a default closer.** An unprompted "happy to jump on a call" is a commitment that may have to be walked back, and it reads as filler when the email already answered the question. Close on the substance, or on a next step that is genuinely yours to take ("I'm re-confirming that and will come back to you"). **Offer a call ONLY when the user has said to, or when the topic genuinely cannot be resolved in writing** (live troubleshooting, a walkthrough of something interactive). Warmth stays required; it comes from the greeting and the tone, not from offering time.
- **EQUIP, DO NOT OPERATE. Never offer to run work the reader can self-serve with a tool named in the same email.** Banned closers of the shape "Say the word and I'll run it" or "If you'd rather we pull that from our side, we can." Both create a reader-dependent commitment while undercutting the self-serve path the same email just handed over. The answer to "can you pull X for us" is the tool plus "you can pull this any time," NOT "I'll run it."
  - **The line is new labor versus already-held analysis.** Offering to hand over analysis already done is FINE ("I can tell you which segments have the gap"). A generic close is FINE. Offering to execute a fresh pull, scan, audit, or report is NOT.
  - **The one exception: remediating OUR OWN incomplete or wrong deliverable.** If we shipped something partial, fixing it is an obligation, not self-serve work, and this rule must not be used to leave a bad artifact standing. State the correction, own it, and deliver the fix.
- **The lead of a reply is THEIR ask, not your status update.** Burying the reader's actual question behind unrequested progress notes is "burying the lead," and it happens most easily when their message opened with thanks for prior work. Mirror the substance, not the courtesy order: answer the question first, put the status note after it.
- **Before correcting a premise, test whether the malformation is in their words or in YOUR reading.** A senior reader's question that looks badly scoped usually is not. Anchoring on your own first-pass reading and then building a reply around correcting them is the same failure as inheriting anyone else's wrong frame. Re-read their sentence for the charitable parse before you write a correction.
- **Do not re-send a deliverable whose actionable content has not changed, and prefer confirming an absence over claiming a finding.** If a re-run produces the same actionable set, a fresh attachment signals a change that does not exist and invites "so what changed?" Say what was re-checked and that nothing moved. Reframing from *finding something* to *confirming an absence* is both true and the stronger message. Check the delta before writing the verb.
- **Answer everything the reader actually asked, in as few words as possible, and nothing they did not ask.** The trim target is NOT "answer only the literal question." Count the asks in their message, including the ones phrased as statements of need ("I need a backup plan" is an ask) and the hypotheses they float. Answer each, once, briefly. Cutting for scope creep must not delete a reader's own stated need.
- **Do not name third-party individuals to a client when the artifact alone carries the point.** Reference the mailbox, account, or role rather than the person behind it. The address is a fact about the account; naming the human points the client at a third party. **Refinement: the rule governs INTRODUCING a third party, not echoing one the client already raised.** When the client names the person themselves, or sends screenshots of that person's console, the name is already in the thread and using it is plain speech, not exposure. Test: who put the name in the thread first?
- **Do not write a defensive clause into a client email to pre-empt a risk you invented.** The failure shape: imagine a way the client could misread or misact, then insert a warning against it, then defend the insertion as judgment. It is unrequested content in someone else's message. Two tells: the clause **rehashes or re-argues a previous email** (the client did not ask for a correction narrative), or it **restates what a quoted source says one line later** in weaker words. If a cited source or doc quote already carries the point, the clause is padding. Cut it and let the source speak.

**Subject Line Patterns**:
| Type | Pattern | Example |
|------|---------|---------|
| Action Required | [ACTION] Topic - Deadline | [ACTION] Budget approval needed - Dec 15 |
| FYI | [FYI] Topic | [FYI] Q4 metrics published |
| Decision | [DECISION] Topic - Deadline | [DECISION] Vendor selection - EOD Friday |
| Urgent | [URGENT] Topic | [URGENT] Production incident |
| Follow-up | [FOLLOW-UP] Topic | [FOLLOW-UP] Migration timeline |

**Tone Calibration by Situation**:

| Situation | Tone | Key Phrases |
|-----------|------|-------------|
| Good News | Confident, celebratory | "Pleased to share", "Successfully completed" |
| Bad News | Direct, solution-focused | "Encountered an issue", "Working to resolve" |
| Request | Clear, respectful | "Would appreciate", "Please provide by" |
| Escalation | Factual, urgent | "Requires immediate attention", "Escalating due to" |
| Follow-up | Polite, persistent | "Following up on", "Checking status of" |
| Thank You | Genuine, specific | "Thank you for [specific action]" |
| Re-engagement | Warm, inviting, value-focused | "Hope you're doing well", "Wanted to check in", "I'm always available" |

**Re-engagement Email Guidelines**:

Re-engagement emails to low-touch customers require a different approach than standard business emails. The goal is relationship building, not task completion.

**Key Principles:**
- **Lead with warmth, not BLUF**: Start with a genuine greeting and ask how they're doing
- **Reference shared history**: Mention specific past work to show you remember them
- **Demonstrate value without pressure**: Remind them of entitlements/services available
- **Make engagement easy**: Offer low-commitment next steps ("30 minutes, no formal agenda")
- **Personal touch matters**: These emails should feel like they're from a person, not a process

**Anti-patterns for re-engagement:**
- ❌ Too short and transactional (feels like a form letter)
- ❌ Jumping straight to business without greeting
- ❌ Generic "let me know if you need anything" without specifics
- ❌ Pressure tactics or guilt about low engagement
- ❌ Missing the human element

**Email Templates**:

**Status Update**:
```
Subject: [FYI] [Project] Status Update - [Date]

[One sentence summary of overall status]

Highlights:
- [Achievement 1]
- [Achievement 2]

Concerns:
- [Issue] - [Owner] addressing by [date]

Next Steps:
- [Action 1] - [Date]
- [Action 2] - [Date]
```

**Request for Action**:
```
Subject: [ACTION] [Request] - [Deadline]

[BLUF: What you need and by when]

Context:
[2-3 sentences of background]

Request:
[Specific ask with clear deliverable]

Timeline:
[When you need it and why]

[Thank you / available for questions]
```

**Escalation**:
```
Subject: [URGENT] [Issue] - Escalation

Issue: [One sentence description]
Impact: [Who/what is affected]
Current Status: [What's happening now]
Ask: [What you need from recipient]
Timeline: [Urgency level]

[Available to discuss immediately]
```

**Follow-up**:
```
Subject: [FOLLOW-UP] [Original Topic]

Following up on [original request/conversation] from [date].

[Brief reminder of context]

Current status: [What you know]
Ask: [What you still need]

[Appreciate the update / available to discuss]
```

**Re-engagement / Low-Touch Customer Check-in**:

WHAT GOOD LOOKS LIKE:
```
Subject: Year-End Check-in - 2026 Planning

Hi [Name],

Hope you're doing well and things are winding down smoothly as the year closes out. Wanted to check in and see how everything is going on your end.

Our last collaboration focused on [specific past work - e.g., Cloud Intelligence Dashboards and the broader tagging strategy for cost allocation]. Both have potential to [specific value - e.g., improve visibility into your savings plans and reserved instance utilization]. I'd enjoy picking that back up, or if there are other areas where you could use a sounding board or extra hands, I'm happy to jump in.

I'm always available if you need to talk through a challenge or want a second set of eyes on something.

As a reminder, your Enterprise Support entitlements include:
- **Well-Architected Reviews** - Deep-dive assessments of your workloads against AWS best practices
- **Infrastructure Event Management (IEM)** - Dedicated support for launches, migrations, or high-traffic events
- **Operational Reviews** - Analysis of your operational health and recommendations
- **Trusted Advisor Priority** - Proactive recommendations for cost, security, performance, and fault tolerance
- **Training Credits** - AWS Skill Builder and certification prep resources

These are included in what you're already paying for. If any of these would be useful, I can help coordinate.

[Month] might be a good time to grab 30 minutes and see what's on the roadmap for [year]. No formal agenda needed, just a chance to sync up and identify where we can add value.

Happy holidays to you and the team. Reach out anytime if something comes up.

Best,
[Your name]
```

**Email Anti-Patterns**:
- ❌ Burying the ask at the end
- ❌ Multiple unrelated topics in one email
- ❌ Wall of text without structure
- ❌ Vague subject lines ("Quick question", "Update")
- ❌ Passive-aggressive tone
- ❌ Reply-all when unnecessary

**Technical Options / Decision Request Email**:

Use when presenting technical options to a customer and requesting a decision. Balances warmth with structured information.

WHAT GOOD LOOKS LIKE:
```
Subject: [Topic] Options + Action Items

Hi [Names],

Hope you're doing well and [seasonal/contextual greeting].

Following up on [recent discussion/meeting]. [Collaborator] and I synced on this and wanted to lay out your options before [deadline/event] so you can decide how to proceed.

## Your Options

### Option A: [Recommended Option Name] (Recommended)

[One sentence description of what this option involves.]

| Factor | Details |
|--------|---------|
| Cost | [Specific numbers] |
| Setup | [Time/effort estimate] |
| Maintenance | [Ongoing requirements] |
| Complexity | [Low/Medium/High] |

[Additional context explaining why this works or what it doesn't replace.]

### Option B: [Alternative Option Name]

[One sentence description.]

| Factor | Details |
|--------|---------|
| Cost | [Specific numbers] |
| Setup | [Time/effort estimate] |
| Maintenance | [Ongoing requirements] |
| Complexity | [Low/Medium/High] |

[Flow or technical details if relevant.]

[Note about attached documentation if applicable.]

### Option C: [Fallback/Status Quo]

[Brief description of doing nothing and what's lost.]

## Our Recommendation

**Option A** is [rationale]. [Supporting details.]

Option B makes sense if [specific condition], but [tradeoff].

## What We Need

1. **[Item 1]** - [Why you need it and what it helps with]
2. **[Item 2]** - [Context]

## If You Want to Get Started Before [Date]

[Resource link or guidance]

[Low-pressure statement about timing flexibility.]

Let me know if you want to schedule a quick call before [date] to [action], or if you'd rather wait.

[Holiday/seasonal closing]. Reach out anytime if something comes up.

---

[Signature]

---

**References**: 
- [Link 1]
- [Link 2]

**Attachments**:
- [Attachment description]
```

**Key Principles for Technical Options Emails:**
- **Warm opening + seasonal awareness**: Acknowledge holidays, end of quarter, etc.
- **Clear structure with headers**: Options, Recommendation, What We Need, Next Steps
- **Tables for comparison**: Easy scanning of tradeoffs
- **Explicit recommendation with rationale**: Don't make them guess your opinion
- **Specific asks**: What you need from them, numbered
- **Low-pressure close**: Give them an out if timing doesn't work
- **Warm sign-off**: Holiday wishes, "reach out anytime"

---

<!-- #process -->
## Writing Process

### Before Writing

1. **Define outcome**: What should readers know/decide/do?
2. **Know audience**: Who reads this? What do they need?
3. **Gather data**: What metrics support the narrative?
4. **Outline structure**: Map the logical flow

### During Writing

1. **Write the ugly first draft**: Get ideas down, don't edit yet
2. **Let it rest**: Step away before revising
3. **Revise for clarity**: One idea per sentence
4. **Cut ruthlessly**: Remove 30% on first edit pass
5. **Read aloud**: Awkward sentences reveal themselves

### Before Sending

**Gate 0, Pre-Delivery Integrity (is it true?).** Before judgment or mechanics, confirm every factual claim, number, name, date, quote, capability, and reference traces to a source checked this session (Non-Negotiable Constraint 2). For a short or low-stakes doc this is a quick self-pass: each claim sourced, numbers recomputed, quotes verbatim, no invented options or filler, audience fit clean. For any consequential, external, client-facing, published, or leadership deliverable, run the full `anti-slop-protocol.md` audit.

**Order matters. Judgment first, mechanics second.** An automated linter (or the stop-slop pass) tests only what a pattern can see: banned words, em dashes, date formats, placeholders, ING starts. It cannot see a buried lead, a length mismatched to the ask, a reader being taught their own domain, a hedge whose real number is on disk, or an inverted referent. **A clean lint is not a compliant draft.** Running the linter first invites stopping there.

1. **Run the Content Quality checklist item by item** against the draft, and RECORD the verdicts. An unrecorded pass is indistinguishable from a skipped one.
2. **State the outcome**: Is purpose clear in opening? For a reply, is the lead their ask?
3. **Check data**: Are claims supported? Is any hedged figure exactly stated in a source already read? Is every coverage claim scoped to what was actually checked?
4. **Verify actions**: Do all commitments have dates?
5. **Review lowlights**: Do all have owner/action/path/date?
6. **Check referents**: Does any *none*, *them*, or *those* admit an inverted reading?
7. **Consistency check**: Formatting, acronyms, dates uniform?
8. **Final cut**: Can anything else be removed?
9. **THEN run the mechanical/anti-slop pass** (`python3 scripts/lint-deliverables.py FILE`, `--email` for an email body; then the `stop-slop` skill), and report both results, not just the lint.

**Highest-yield five when time is short**: Is the lead their actual question? Is any figure hedged that an open source would state exactly? Am I explaining something this reader already knows? Does every referent have one possible antecedent? Would cutting 30% lose anything?

### After Sending

1. **Reconcile the draft against the sent item.** Read what actually shipped, not what was drafted. Silent trims on send are common and they remove load-bearing content; a dropped caveat can cause the reader to re-ask, weeks later, a question the cut paragraph already answered.
2. **Record sent time, real recipient list, and attachments** in the correspondence record. Recipients on the draft are an intention; recipients on the sent item are a fact, and they differ.
3. **Note zero divergence when it happens.** A draft that ships verbatim is evidence the pre-send pass is working. A draft that gets trimmed every time is evidence it is not.

---

## Writing Checklist

### Content Quality
- [ ] Outcome/purpose stated in opening
- [ ] Active voice throughout
- [ ] Third person only (no I/we/our/us)
- [ ] Data supports all claims
- [ ] No hedge words (some, many, few, sometimes)
- [ ] No intention verbs (aim to, hope to, plan to)
- [ ] All "will" statements have dates
- [ ] All lowlights have action/owner/path/date
- [ ] Audience-appropriate context level
- [ ] Calibrated to reader's expertise (no explaining their own domain, no unrequested runbook)
- [ ] No meta-padding (contrastive filler, value-hedging openers, performative deference)
- [ ] Lead is the reader's actual ask, not an unrequested status update
- [ ] No hedged figure that a source already read states exactly
- [ ] Every coverage claim scoped to what was actually checked
- [ ] Every referent unambiguous, especially *none/them/those* answering a negative question
- [ ] No offer to run work the reader can self-serve with a tool named in the same message
- [ ] Premise checked: if correcting the reader, confirmed the fault is in their words and not my reading
- [ ] Client-facing artifact swept for the three leak classes (internal info, conversation voice, AI artifacts)
- [ ] Integrity (Gate 0): every factual claim traces to a source checked this session; full anti-slop pass for consequential or external docs
- [ ] Consumable shape (deliverables and reports): plain short version first, terms defined, an example per key point, evidence in an appendix
- [ ] No fact recited back to the reader who owns it

### Formatting Quality
- [ ] Acronyms spelled out on first use
- [ ] Numbers formatted correctly (1-9 spelled, 10+ numeral)
- [ ] Dates in Month Day, Year format
- [ ] Oxford comma used consistently
- [ ] No ampersands (unless proper name)
- [ ] Line numbers included (if review document)
- [ ] Page numbers in "Page X of Y" format
- [ ] Six pages or fewer (excluding appendix)
- [ ] Consistent formatting throughout

### Final Review
- [ ] Read aloud for flow
- [ ] Cut 30% of words
- [ ] Verify all data accuracy
- [ ] Confirm all names/titles are formal
- [ ] Check for ING words at sentence starts

---

## Common Corrections

### Before → After Examples

**Passive to Active:**
- ❌ "The issue was identified by the support team"
- ✅ "The support team identified the issue"

**First to Third Person:**
- ❌ "We completed the migration ahead of schedule"
- ✅ "The migration team completed the work ahead of schedule"

**Vague to Specific:**
- ❌ "Performance improved significantly"
- ✅ "Response time decreased from 2.3s to 0.8s (65% improvement)"

**Intention to Commitment:**
- ❌ "The team aims to complete testing next week"
- ✅ "The team will complete testing by December 20"

**Hedge to Precise:**
- ❌ "Many customers reported issues"
- ✅ "47 customers (12% of active accounts) reported issues"

**Complex to Plain:**
- ❌ "Utilize the dashboard to facilitate monitoring"
- ✅ "Use the dashboard to monitor"

**Over-Explaining to Peer-Level (expert reader):**
- ❌ "A certificate proves control of the domain, not the address, so the June cert date doesn't tell you when the IP was acquired"
- ✅ "The cert date bounds domain control, not IP tenure"

**Contrastive Padding to Direct:**
- ❌ "The reason is forensic, not operational"
- ✅ "The reason is forensic"

**Inverted Referent to Explicit** (answering a negatively phrased question):
- ❌ "very likely none of them"
- ✅ "very likely none of the roles are missing those four permissions"

**Over-Claimed Coverage to Scoped:**
- ❌ "I re-ran the check across the rest of your footprint"
- ✅ "I re-ran the check across the three segments I could read"

**Volunteered Labor to Equipped:**
- ❌ "If you'd rather we run it from our side, we can. Say the word and I'll extend it"
- ✅ "The console's inventory view lists this by account and exports to CSV; you can pull it any time"

**Claimed Finding to Confirmed Absence** (when the re-run changed nothing):
- ❌ "Found a couple more, so I'm attaching an updated report"
- ✅ "Nothing new turned up, so the four items already flagged are still the whole actionable set"

---

## Anti-Patterns

### Content Anti-Patterns
- ❌ Burying the lead (key point not in first paragraph)
- ❌ Task lists without impact metrics
- ❌ Lowlights without resolution paths
- ❌ Claims without supporting data
- ❌ Jargon for non-technical audiences
- ❌ Over-simplification for technical audiences
- ❌ Explaining an expert reader's own domain back to them
- ❌ Unrequested runbooks or step-by-step instructions for capable readers
- ❌ Spelling out an implication the reader reaches in one step
- ❌ Correcting a premise the reader never got wrong (check your own reading first)
- ❌ Burying the reader's actual question behind an unrequested status update
- ❌ Offering to run work the reader can self-serve with a tool named in the same message
- ❌ Re-sending a deliverable whose actionable content has not changed
- ❌ Claiming a finding when the data confirms an absence

### Style Anti-Patterns
- ❌ Passive voice
- ❌ First person pronouns
- ❌ Hedge words and qualifiers
- ❌ Hedging a figure that a source already read states exactly
- ❌ Ambiguous referents (*none*, *them*, *those*) that admit an inverted reading
- ❌ Coverage claims broader than what was actually checked
- ❌ Intention verbs without commitments
- ❌ ING words starting sentences
- ❌ Individual names instead of titles
- ❌ Contrastive padding ("X, not Y") where the foil adds nothing
- ❌ Value-hedging openers ("if it's useful", "one thing worth knowing")
- ❌ Performative deference ("you're better placed than I am")

### Format Anti-Patterns
- ❌ Inconsistent date formats
- ❌ Mixed number styles
- ❌ Undefined acronyms
- ❌ Missing page numbers
- ❌ Exceeding six pages
- ❌ Kitchen-sink appendices

---

<!-- #reference -->
## Quick Reference Card

| Rule | Standard |
|------|----------|
| Voice | Active only |
| Person | Third person only |
| Numbers 1-9 | Spell out |
| Numbers 10+ | Numerals |
| Dates | Month Day, Year |
| Acronyms | Spell out first use |
| Oxford comma | Required |
| Ampersand | Avoid |
| Max pages | Six |
| Lowlights | Action + Owner + Path + Date |
| "Will" | Must have date |
| Document | Must state outcome |
| Reply lead | The reader's ask, not a status update |
| Referents | One possible antecedent, especially answering a negative question |
| Figures | If a source already read states it exactly, state it exactly |
| Coverage claims | Scoped to what was actually checked |
| Self-servable work | Equip, do not operate. Exception: fixing our own incomplete deliverable |
| Correcting the reader | Check your own reading before assuming their premise is wrong |
| Unchanged deliverable | Do not re-send. Confirm the absence instead |
| Reader expertise | Do not explain their own domain back to them |
| Pre-send order | Judgment checklist first, mechanical pass second. A clean lint is NOT compliance |
| Post-send | Reconcile draft against the sent item, record divergence |
| Consumable output | Plain short version first, terms defined, an example per point, narrative over data dumps, evidence to an appendix |
| Integrity gate | Gate 0 first: every claim sourced this session; full anti-slop pass for consequential or external docs |

---

*This document governs all formal written output. Casual conversation and quick responses follow persona defaults. When in doubt, prioritize clarity over style.*
