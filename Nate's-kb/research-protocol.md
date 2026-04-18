# Research Protocol

**Keywords**: research, investigate, compare, analyze, evaluate, deep-dive, assess, study, explore
**Purpose**: Systematic methodology for conducting research, evaluating sources, and synthesizing findings
**Last Updated**: 2025-12-12

---

## Integration Notes

**Decision Engine Integration**:
- Triggered during Phase 2 (KB Consultation) when research keywords detected
- Applies to Route B (Execute with Context) for standard research tasks
- Use Route D (Present Options) when research scope is ambiguous or multiple approaches viable

**Related KB Documents**:
- See: writing-protocol.md (for presenting research findings in formal documents)
- See: prompt-enhancement-protocol.md (for clarifying vague research requests)
- See: planning-protocol.md (for research that feeds into project planning)

**Writing Standards Integration**:
- Research outputs follow writing-protocol.md principles for formal deliverables
- Data and claims require source attribution
- Findings presented with confidence indicators


### Personality Integration
- All outputs filtered through Nathaniel.md personality kernel
- Maintain Nate's cultural voice and communication style
- See: Nathaniel.md for voice, values, and behavioral patterns

---

## Quick Reference

### Trigger Conditions
| Tier | Keywords |
|------|----------|
| 1 (Absolute) | research, deep-dive, investigate |
| 2 (Strong) | compare, analyze, evaluate, assess, study |
| 3 (Contextual) | explore, look into, find out + research context |

### Output Formats
| Format | Use When | Depth |
|--------|----------|-------|
| Quick Scan | Time-sensitive, surface-level need | Key points only |
| Standard | Typical research request | Findings + sources + recommendation |
| Comprehensive | Strategic decisions, complex topics | Full analysis with alternatives |

---

## Research Methodology

### Phase 1: Scope Definition

**Before Starting Research**:
1. **Define the Question**: What specifically needs to be answered?
2. **Identify Constraints**: Time, depth, source restrictions
3. **Determine Output**: What format does the answer need?
4. **Set Boundaries**: What's in scope vs out of scope?

**Scope Template**:
```
Research Question: [Specific question to answer]
Context: [Why this matters, what decision it informs]
Constraints: [Time limit, source preferences, depth required]
Output Format: [Quick answer, comparison table, full report]
Out of Scope: [What NOT to research]
```

### Phase 2: Source Gathering

**Source Hierarchy** (Prioritize in this order):
1. **Official Documentation**: Vendor docs, specifications, standards
2. **Primary Sources**: Original research, official announcements, direct data
3. **Expert Sources**: Recognized authorities, peer-reviewed content
4. **Community Sources**: Forums, blogs, Stack Overflow (verify claims)
5. **AI-Generated**: Use for synthesis, not as primary source

**Source Evaluation Criteria**:
| Criterion | Questions to Ask |
|-----------|------------------|
| Authority | Who created this? What are their credentials? |
| Currency | When was this published? Is it still relevant? |
| Accuracy | Can claims be verified? Are sources cited? |
| Purpose | Why was this created? Any bias or agenda? |
| Relevance | Does this directly address the research question? |

**Credibility Scoring**:
- **High**: Official docs, peer-reviewed, recognized experts
- **Medium**: Reputable blogs, community consensus, dated but relevant
- **Low**: Unverified claims, anonymous sources, outdated information

### Phase 3: Analysis & Synthesis

**Analysis Patterns**:

**Comparison Analysis**:
```
| Criterion | Option A | Option B | Option C |
|-----------|----------|----------|----------|
| [Factor 1] | [Value] | [Value] | [Value] |
| [Factor 2] | [Value] | [Value] | [Value] |
| Recommendation | [Winner with rationale] |
```

**Pros/Cons Analysis**:
```
## [Option/Topic]

**Pros**:
- [Advantage 1] - [Supporting evidence]
- [Advantage 2] - [Supporting evidence]

**Cons**:
- [Disadvantage 1] - [Supporting evidence]
- [Disadvantage 2] - [Supporting evidence]

**Net Assessment**: [Overall evaluation]
```

**Gap Analysis**:
```
| Current State | Desired State | Gap | Effort to Close |
|---------------|---------------|-----|-----------------|
| [What exists] | [What's needed] | [Delta] | [H/M/L] |
```

**Trend Analysis**:
- Historical context: Where did this come from?
- Current state: Where is it now?
- Trajectory: Where is it heading?
- Implications: What does this mean for the decision?

### Phase 4: Confidence Assessment

**Rate Confidence in Findings**:

| Level | Criteria | Indicator |
|-------|----------|-----------|
| High | Multiple authoritative sources agree, recent data, directly applicable | ✅ |
| Medium | Some authoritative sources, minor gaps, mostly applicable | ⚠️ |
| Low | Limited sources, conflicting info, indirect applicability | ❓ |

**Uncertainty Handling**:
- State what is known vs unknown
- Identify assumptions made
- Note where additional research would help
- Never present uncertain findings as definitive

### Phase 5: Output Delivery

**Standard Research Output Structure**:
```markdown
## Research: [Topic]

**Question**: [What was asked]
**Confidence**: [High/Medium/Low]
**Date**: [Research date]

---

### Summary
[2-3 sentence answer to the research question]

### Key Findings
- [Finding 1] - Source: [attribution]
- [Finding 2] - Source: [attribution]
- [Finding 3] - Source: [attribution]

### Analysis
[Synthesis of findings, patterns identified, implications]

### Recommendation
[Clear recommendation based on findings]

### Sources
1. [Source 1 with link/reference]
2. [Source 2 with link/reference]

### Gaps & Uncertainties
- [What remains unknown]
- [Where confidence is lower]
```

---

## Research Types

### Technical Research
- Focus on specifications, compatibility, implementation details
- Prioritize official documentation and tested solutions
- Include version numbers and compatibility notes
- Flag deprecated or outdated approaches

### Competitive/Market Research
- Compare features, pricing, positioning
- Use structured comparison tables
- Note data freshness (markets change fast)
- Identify decision criteria before comparing

### Best Practices Research
- Look for consensus across multiple sources
- Distinguish opinion from proven patterns
- Note context dependencies (what works where)
- Include anti-patterns (what to avoid)

### Troubleshooting Research
- Start with exact error messages
- Prioritize recent solutions (last 12 months)
- Verify solutions before recommending
- Note environment-specific factors

---

## Anti-Patterns

### Research Anti-Patterns
- ❌ Stopping at first result found
- ❌ Treating all sources as equally credible
- ❌ Presenting findings without confidence indication
- ❌ Ignoring contradictory evidence
- ❌ Over-researching when quick answer suffices
- ❌ Under-researching when decision is significant

### Output Anti-Patterns
- ❌ Dumping raw findings without synthesis
- ❌ Missing source attribution
- ❌ Presenting opinion as fact
- ❌ Burying the answer in details
- ❌ Failing to state what remains unknown

---

## Quality Checklist

### Before Delivering Research
- [ ] Research question clearly answered
- [ ] Confidence level stated
- [ ] Sources attributed and credible
- [ ] Findings synthesized (not just listed)
- [ ] Recommendation provided (if applicable)
- [ ] Uncertainties acknowledged
- [ ] Output format matches request

---

*Research is about finding truth, not confirming assumptions. Follow the evidence, state confidence honestly, and acknowledge what remains unknown.*
