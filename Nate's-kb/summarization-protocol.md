# Summarization Protocol

**Keywords**: meeting, summarize, transcript, notes, summary, recap, minutes, webinar, presentation, interview
**Purpose**: Comprehensive guide for summarizing any spoken/written content into structured, actionable documentation
**Last Updated**: 2025-12-12

---

## Integration Notes

**Decision Engine Integration**:
- Triggered during Phase 2 (KB Consultation) when meeting/transcript keywords detected
- Applies to Route B (Execute with Context) for standard summaries
- Use Route D (Present Options) if content type or format unclear

**Related KB Documents**:
- See: prompt-enhancement-protocol.md (for clarifying vague transcript requests)
- See: writing-protocol.md (for prose quality standards)

**Writing Standards Integration**:
- Narrative sections follow writing-protocol.md principles: active voice, conciseness, plain language, data-backed claims
- Exception: First-person professional perspective retained (overrides writing-protocol.md third-person rule for this document type)
- Formatting standards from writing-protocol.md apply: numbers, dates, acronyms, Oxford comma
- Meeting summaries prioritize speed and signal extraction; formal polish is secondary to accuracy and actionability


### Personality Integration
- All outputs filtered through Nathaniel.md personality kernel
- Maintain Nate's cultural voice and communication style
- See: Nathaniel.md for voice, values, and behavioral patterns

---

## Quick Reference

### Trigger Conditions
| Tier | Keywords |
|------|----------|
| 1 (Absolute) | summarize-meeting, meeting-summary, transcript-summary |
| 2 (Strong) | meeting, transcript, summarize, recap, minutes, webinar |
| 3 (Contextual) | notes, call, discussion, presentation, interview + summary context |

### Output Formats
| Format | Use When | Length |
|--------|----------|--------|
| Brief | Quick update, exec consumption | 1 page max |
| Standard | Normal meeting documentation | 1-2 pages |
| Comprehensive | Complex/critical meetings | 2-4 pages |

---

## Content Type Detection

Before processing, identify what type of content was submitted:

| Content Type | Indicators | Adaptation |
|--------------|------------|------------|
| **Meeting Transcript** | Multiple speakers, back-and-forth dialogue, action items | Full template with all sections |
| **Webinar/Presentation** | Single presenter, educational content, Q&A section | Focus on key takeaways, skip "decisions" |
| **Interview** | Two parties, Q&A format, exploratory | Focus on insights, quotes, themes |
| **Status Update** | One speaker, progress report | Focus on status, blockers, next steps |
| **Brainstorm Session** | Rapid ideas, loose structure | Focus on ideas generated, themes, priorities |
| **Escalation Call** | Urgent tone, problem-focused | Focus on issue, impact, resolution, timeline |

**Detection Protocol**:
1. Scan first 20% of content for speaker patterns
2. Identify dominant format (dialogue vs monologue)
3. Check for urgency indicators
4. Select appropriate template adaptation

---

## Summarization Protocol

### Phase 1: Pre-Processing

**Input Analysis** (Do this first):
```
1. CONTENT TYPE: [Meeting/Webinar/Interview/Status/Brainstorm/Escalation]
2. TRANSCRIPT QUALITY: [High/Medium/Low] 
   - High: Clear speakers, complete sentences, minimal gaps
   - Medium: Some unclear portions, occasional gaps
   - Low: Significant gaps, unclear attribution, fragmented
3. CONTEXT AVAILABLE: [Full/Partial/None]
   - Full: Know project, attendees, history
   - Partial: Some context, gaps exist
   - None: Cold transcript, no background
4. ESTIMATED LENGTH: [Brief/Standard/Comprehensive]
5. URGENCY INDICATORS: [Yes/No] - Time-sensitive items detected?
```

### Phase 2: Extraction

**Action Item Detection Patterns**:
Scan for these linguistic markers:
- **Commitment verbs**: "will", "going to", "plan to", "need to", "should", "must"
- **Assignment phrases**: "[Name] will...", "assigned to", "owned by", "responsible for"
- **Deadline markers**: "by [date]", "before", "end of week", "next sprint", "ASAP"
- **Follow-up signals**: "circle back", "follow up", "check in", "revisit", "reconnect"

**Decision Detection Patterns**:
- **Agreement markers**: "agreed", "decided", "confirmed", "approved", "signed off"
- **Consensus phrases**: "we'll go with", "the plan is", "moving forward with"
- **Rejection markers**: "won't", "not going to", "ruled out", "rejected"

**Risk/Issue Detection Patterns**:
- **Concern language**: "worried about", "concerned", "risk", "issue", "problem", "blocker"
- **Uncertainty markers**: "not sure", "unclear", "TBD", "need to figure out"
- **Dependency flags**: "waiting on", "blocked by", "depends on", "contingent"

### Phase 3: Sentiment Analysis

**Meeting Tone Assessment**:
| Indicator | Positive | Neutral | Negative |
|-----------|----------|---------|----------|
| Language | "great progress", "on track", "excited" | Factual, procedural | "concerned", "frustrated", "behind" |
| Pace | Energetic, collaborative | Steady, methodical | Tense, interruptions |
| Outcomes | Decisions made, alignment | Information shared | Unresolved, disagreement |

**Engagement Health Score** (for customer meetings):
```
ENGAGEMENT HEALTH: [Green/Yellow/Red]

Green: Customer engaged, positive sentiment, clear alignment
Yellow: Some concerns raised, minor friction, needs attention
Red: Significant issues, relationship strain, escalation risk
```

---

## Output Template (Standard Format)

```markdown
**Date**: [YYYY-MM-DD]
**Content Type**: [Meeting/Webinar/Interview/etc.]
**Attendees**:
- [Name] ([Role])
- [Name] ([Role])
- (Noted absences: [Names if mentioned])

**Summary**: [One sentence overview of purpose and key outcome]

**Confidence Score**: [High/Medium/Low] - [Brief reason if not High]

---

## 🚨 Urgent Items (if any)
- [Time-sensitive item requiring immediate attention]
- [Critical blocker or risk]

---

**Topics of Discussion**: [One sentence narrative]
- [Topic 1]
- [Topic 2]
- [Topic 3]

**Key Decisions**: [One sentence narrative]
- ✅ [Decision 1] - [Owner if stated]
- ✅ [Decision 2] - [Owner if stated]
- ⏳ [Pending decision] - awaiting [what]

**Issues and Risks**: [One sentence narrative]
- 🔴 [Critical risk/issue]
- 🟡 [Moderate concern]
- 🟢 [Minor/monitored item]

**Timeline**: [One sentence narrative]
- [Date/Sprint]: [Milestone]
- [Date/Sprint]: [Milestone]

**Action Items**: [One sentence narrative]
| Action | Owner | Due | Priority |
|--------|-------|-----|----------|
| [Action 1] | [Name] | [Date] | High/Med/Low |
| [Action 2] | [Name] | [Date] | High/Med/Low |

**Documentation Needs**: [One sentence narrative]
- [Doc need 1]
- [Doc need 2]

**Follow-up**: [One sentence narrative]
- [Follow-up 1] - [Date if known]
- [Follow-up 2]

---

## Meeting Tone
**Overall Sentiment**: [Positive/Neutral/Concerned/Tense]
**Engagement Health**: [Green/Yellow/Red] (customer meetings only)
**Key Observation**: [One sentence on meeting dynamics]

---

## Narrative Summary

[Full narrative in first person. 2-4 paragraphs.]

---

## Stakeholder Relevance

| Stakeholder | Relevant Sections | Priority |
|-------------|-------------------|----------|
| [Executive] | Summary, Decisions, Risks | High |
| [Technical Lead] | Topics, Action Items, Timeline | High |
| [Project Manager] | All sections | Medium |
| [Team Members] | Action Items, Next Steps | Medium |

**Suggested Distribution**: [List of roles/names who should receive this summary]

---

## Cross-Reference
**Related Previous Meetings**: [Reference if known, or "N/A - standalone"]
**Open Items from Prior Sessions**: [Carried forward items if applicable]
```

---

## Format Variations

### Brief Format (Executive Summary)
Use when: Quick update needed, exec audience, time-constrained

```markdown
**[Date] - [Meeting Type] Summary**

**Key Outcome**: [One sentence]

**Decisions Made**:
- [Decision 1]
- [Decision 2]

**Critical Items**:
- 🚨 [Urgent item if any]
- ⚠️ [Key risk if any]

**Next Steps**: [Top 3 action items with owners]

**Engagement Health**: [Green/Yellow/Red]
```

### Comprehensive Format
Use when: Critical meetings, escalations, strategic sessions

Add to Standard Format:
- Detailed discussion breakdown by topic
- Full quotes for critical statements
- Complete attendee participation notes
- Detailed risk analysis with mitigation
- Historical context and continuity tracking
- Appendix with raw action items

---

## Section Guidelines

### Summary (Header)
- One sentence capturing essence
- Include: purpose, key outcome, scope
- Pattern: "[Type] focused on [topic] with [outcome]"

### Confidence Score
- **High**: Clear transcript, full context, unambiguous content
- **Medium**: Some gaps but core content clear
- **Low**: Significant uncertainty, note specific gaps

### Urgent Items
- Only include genuinely time-sensitive items
- If none, omit section entirely
- Use sparingly to maintain impact

### Topics of Discussion
- Extract substantive topics only
- Group related items
- Order by importance or chronological flow
- Exclude small talk and tangents

### Key Decisions
- Only actual decisions (not discussions)
- Mark pending decisions with ⏳
- Include decision owner/authority
- Note approval status

### Issues and Risks
- Use severity indicators (🔴🟡🟢)
- Include impact if stated
- Note mitigation if discussed
- Flag unresolved items

### Timeline
- Specific dates when mentioned
- Sprint/phase references
- Relative timing with anchor date
- Flag missed deadlines

### Action Items
- Table format for clarity
- Owner required (or "TBD")
- Due date required (or "TBD")
- Priority based on discussion emphasis

### Meeting Tone
- Objective assessment, not editorializing
- Based on language patterns observed
- Engagement health for customer meetings only

### Stakeholder Relevance
- Map content to audience needs
- Prioritize distribution list
- Enable targeted sharing

---

## Narrative Writing Guidelines

### Voice and Perspective
- First person perspective
- Never mention role explicitly
- "We" for team actions
- "I" for personal observations

### Tone Calibration
| Meeting Tone | Narrative Tone |
|--------------|----------------|
| Positive | Confident, forward-looking |
| Neutral | Factual, balanced |
| Concerned | Measured, solution-focused |
| Tense | Calm, de-escalating |

### Structure
- **P1**: Context and key accomplishments
- **P2**: Important discussions or concerns
- **P3**: Decisions and next steps
- **P4**: Assessment and outlook (optional)

### Length by Format
- Brief: 1 paragraph
- Standard: 2-3 paragraphs
- Comprehensive: 3-4 paragraphs

---

## Content Type Adaptations

### Meeting (Standard)
Full template as documented above.

### Webinar/Presentation
**Modify**:
- Replace "Attendees" with "Presenter(s)" and "Audience"
- Replace "Key Decisions" with "Key Takeaways"
- Replace "Action Items" with "Recommended Actions"
- Add "Resources Mentioned" section
- Omit "Engagement Health"

### Interview
**Modify**:
- Replace "Topics of Discussion" with "Themes Explored"
- Add "Notable Quotes" section
- Replace "Key Decisions" with "Key Insights"
- Focus narrative on interviewee perspective

### Escalation Call
**Modify**:
- Add "Issue Summary" section at top
- Add "Impact Assessment" section
- Add "Resolution Status" with timeline
- Emphasize ownership and accountability
- Always include Engagement Health

### Brainstorm Session
**Modify**:
- Replace "Key Decisions" with "Ideas Generated"
- Add "Ideas Prioritized" section
- Replace "Action Items" with "Ideas to Pursue"
- Lighter structure, capture creativity

---

## Quality Checklist

### Content Accuracy
- [ ] All attendees captured
- [ ] Content type correctly identified
- [ ] Key decisions accurately stated
- [ ] Action items complete with owners
- [ ] Timeline items have dates/references
- [ ] No fabricated information

### Structure Compliance
- [ ] Confidence score included
- [ ] Each section has narrative + bullets
- [ ] Urgent items flagged (if applicable)
- [ ] Stakeholder relevance mapped
- [ ] Format matches complexity

### Voice and Tone
- [ ] First person perspective
- [ ] No role self-reference
- [ ] Tone matches meeting sentiment
- [ ] Professional but conversational
- [ ] No editorializing beyond facts

### Completeness
- [ ] No duplicate content across sections
- [ ] Cross-references included (if applicable)
- [ ] Distribution guidance provided
- [ ] Engagement health scored (customer meetings)

---

## Handling Edge Cases

### Poor Transcript Quality
```
If transcript quality is Low:
1. Note in Confidence Score: "Low - [specific issues]"
2. Use "[unclear]" for uncertain portions
3. Mark uncertain items with "(?)"
4. State assumptions explicitly
5. Recommend clarification if critical items affected
```

### Missing Context
```
If context is None/Partial:
1. Note in header: "Context: Limited - summary based on transcript only"
2. Avoid assumptions about project history
3. Use generic role descriptions if names unclear
4. Flag items that would benefit from context
```

### Multiple Meetings Referenced
```
If transcript references other meetings:
1. Note in Cross-Reference section
2. Distinguish current meeting content from references
3. Flag action items carried forward vs new
```

### Conflicting Information
```
If speakers contradict each other:
1. Note both positions
2. Mark as "Unresolved: [topic]"
3. Flag for follow-up clarification
4. Do not pick a side
```

---

## Anti-Patterns

**Content**:
- ❌ Copy-pasting transcript verbatim
- ❌ Including every minor comment
- ❌ Fabricating details not in transcript
- ❌ Missing clearly stated action items
- ❌ Vague bullets ("discussed various topics")

**Structure**:
- ❌ Narrative that repeats bullets
- ❌ Skipping confidence score
- ❌ Omitting stakeholder relevance
- ❌ Wrong format for content type

**Voice**:
- ❌ Third-person perspective
- ❌ Role self-reference ("As the consultant...")
- ❌ Editorializing beyond observations
- ❌ Tone mismatch with meeting sentiment

**Process**:
- ❌ Skipping pre-processing phase
- ❌ Not detecting content type
- ❌ Ignoring urgency indicators
- ❌ Missing cross-references when available

---

## Embedded Example

### Input (Excerpt)
```
Sprint review meeting. <Name1>, <Name2>, <Name3>, <Name4> present. <Name5> and <Name6> absent.

Francisco: "We finished the VPN config for IonWave and got the infrastructure deployed for Spectra."

Tom: "I'm concerned about the data sync - we have a major RFP going out today and the preview environment needs to stay stable."

Brian: "Understood. We'll monitor closely. Francisco, can you and Tom sync on the pipeline review after this?"

Francisco: "Sure, I'll set that up."

Brian: "Great. Status doc by Monday?"

Francisco: "Yes, I'll have it ready."
```

### Output (Standard Format)
```markdown
**Date**: 2025-05-09
**Content Type**: Sprint Review Meeting
**Attendees**:
- Francisco (Dev Lead)
- Tom (Customer Representative)
- Brian (Facilitator)
- <Name> (Participant)
- (Noted absences: Chris, Derek)

**Summary**: Sprint review focused on AWS migration progress for IonWave and Spectra, with infrastructure milestones achieved and careful planning needed for upcoming data synchronization due to customer RFP timing.

**Confidence Score**: High - Clear transcript, all speakers identified

---

**Topics of Discussion**: Team reviewed completed infrastructure work and planned upcoming sync activities.
- VPN configuration completion for IonWave
- Infrastructure deployment for Spectra
- Data synchronization planning and timing concerns
- Pipeline review coordination

**Key Decisions**: Team aligned on monitoring approach and documentation timeline.
- ✅ Monitor performance closely during sync activities
- ✅ Status document delivery by Monday - Francisco
- ⏳ Data sync timing - awaiting Tom's approval based on RFP status

**Issues and Risks**: Customer raised timing concern requiring careful coordination.
- 🟡 Major RFP release today using preview environment
- 🟡 Performance sensitivity during data synchronization window

**Timeline**: Near-term milestones identified.
- Monday: Status document delivery
- TBD: Data synchronization (pending RFP timing)

**Action Items**:
| Action | Owner | Due | Priority |
|--------|-------|-----|----------|
| Pipeline review meeting | Francisco + Tom | This week | High |
| Status document | Francisco | Monday | High |
| Performance monitoring setup | Team | Before sync | Medium |

**Follow-up**:
- Francisco and Tom to meet on pipeline review
- Status document distribution Monday

---

## Meeting Tone
**Overall Sentiment**: Positive with appropriate caution
**Engagement Health**: Green - collaborative, concerns addressed constructively
**Key Observation**: Team demonstrated good risk awareness while maintaining momentum

---

## Narrative Summary

The sprint review highlighted solid progress on our AWS migration initiatives. The team successfully completed VPN configuration for IonWave and deployed the core infrastructure for Spectra, keeping us on track for upcoming milestones.

Tom raised an important consideration about a major RFP releasing today that relies on the preview environment. This requires us to be thoughtful about data synchronization timing to avoid any performance impact during a critical customer-facing period. The team quickly aligned on implementing proper monitoring and maintaining clear communication before proceeding.

We wrapped up with clear next steps: Francisco and Tom will connect on the pipeline review, and we'll have a status document ready by Monday. The overall tone was positive with good progress and appropriate risk awareness.

---

## Stakeholder Relevance

| Stakeholder | Relevant Sections | Priority |
|-------------|-------------------|----------|
| Leadership | Summary, Decisions, Risks | High |
| Dev Team | Topics, Action Items, Timeline | High |
| Customer (Tom) | All sections | High |
| PMO | Timeline, Action Items | Medium |

**Suggested Distribution**: <Name1>, <Name2>, <Name3>, <Name4>, Project Stakeholders
```

---

*This document enables Nate to produce consistent, high-quality summaries of any content type while maintaining a professional voice and ensuring actionable output.*
