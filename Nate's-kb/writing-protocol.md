# Writing Protocol

**Keywords**: write, writing, document, memo, report, email, update, brief, summary, draft, edit, review-doc, 6-pager, narrative, notes, thread, slack, letter, correspondence, communication, message, compose
**Purpose**: Writing standards for all written deliverables
**Last Updated**: 2025-12-25
**Version**: 2.0 (TOC-Dynamic-Loading enabled)

---

## Section Routing (TOC-Dynamic-Loading)

**Load only the section(s) matching task keywords. Fallback to full load if ambiguous.**

| Keywords | Anchor | Lines | Description |
|----------|--------|-------|-------------|
| standards, voice, tone, audience, concise | #standards | ~105 | Basic writing standards and voice |
| format, typography, headers, lists, tables | #formatting | ~70 | Formatting and typography rules |
| 6-pager, narrative, email, memo, template, brief | #documents | ~390 | Document types and templates |
| process, draft, edit, review, checklist | #process | ~120 | Writing process and quality checks |
| quick, reference, rules | #reference | ~20 | Quick reference card |

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

### Conciseness

- Cover fewer topics deeply rather than many topics thinly
- Question every word: "Does this add value?"
- If a sentence works without a word, remove the word
- Target: Say it in half the words, then cut again

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

1. **State the outcome**: Is purpose clear in opening?
2. **Check data**: Are claims supported with metrics?
3. **Verify actions**: Do all commitments have dates?
4. **Review lowlights**: Do all have owner/action/path/date?
5. **Consistency check**: Formatting, acronyms, dates uniform?
6. **Final cut**: Can anything else be removed?

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

---

## Anti-Patterns

### Content Anti-Patterns
- ❌ Burying the lead (key point not in first paragraph)
- ❌ Task lists without impact metrics
- ❌ Lowlights without resolution paths
- ❌ Claims without supporting data
- ❌ Jargon for non-technical audiences
- ❌ Over-simplification for technical audiences

### Style Anti-Patterns
- ❌ Passive voice
- ❌ First person pronouns
- ❌ Hedge words and qualifiers
- ❌ Intention verbs without commitments
- ❌ ING words starting sentences
- ❌ Individual names instead of titles

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

---

*This document governs all formal written output. Casual conversation and quick responses follow persona defaults. When in doubt, prioritize clarity over style.*
