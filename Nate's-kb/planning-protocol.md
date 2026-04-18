# Planning Protocol

**Keywords**: plan, roadmap, estimate, scope, breakdown, project, timeline, milestone, dependency, prioritize
**Purpose**: Systematic methodology for project planning, scoping, estimation, and roadmap creation
**Last Updated**: 2025-12-28

---

## Route F Integration

**When to Route F during planning:**

| Situation | Action |
|-----------|--------|
| Multiple valid approaches to scope | Route F: Compare options |
| Significant trade-offs (time vs. quality vs. scope) | Route F: Analyze trade-offs |
| Uncertainty about priorities | Route F: Evaluate priority options |
| Resource allocation decisions | Route F: Compare allocation strategies |
| Architecture/approach decisions embedded in plan | Route F: Technical analysis |

**When to skip Route F:**
- Simple task breakdowns with clear sequence
- Single obvious approach
- User explicitly wants speed over analysis

---

## Integration Notes

**Decision Engine Integration**:
- Triggered during Phase 2 (KB Consultation) when planning keywords detected
- Applies to Route D (Present Options) for scope decisions
- Use Route B (Execute with Context) for straightforward breakdowns

**Related KB Documents**:
- See: development-protocol.md (for technical implementation planning)
- See: research-protocol.md (for research that informs planning)
- See: writing-protocol.md (for documenting plans formally)

**Handoff Points**:
- Planning outputs feed into development-protocol.md task execution
- Customer project plans align with established engagement frameworks
- Complex plans may require research-protocol.md for unknowns


### Personality Integration
- All outputs filtered through Nathaniel.md personality kernel
- Maintain Nate's cultural voice and communication style
- See: Nathaniel.md for voice, values, and behavioral patterns

---

## Quick Reference

### Trigger Conditions
| Tier | Keywords |
|------|----------|
| 1 (Absolute) | plan, roadmap, project-plan |
| 2 (Strong) | estimate, scope, breakdown, timeline, milestone |
| 3 (Contextual) | prioritize, dependency, schedule + planning context |

### Output Formats
| Format | Use When | Detail Level |
|--------|----------|--------------|
| Quick Breakdown | Simple task decomposition | Tasks + sequence |
| Standard Plan | Typical project planning | Tasks + estimates + dependencies |
| Comprehensive Roadmap | Strategic initiatives | Phases + milestones + risks + resources |

---

## Planning Methodology

### Phase 1: Scope Definition

**Before Planning**:
1. **Define Objective**: What does "done" look like?
2. **Identify Stakeholders**: Who cares about this?
3. **Establish Constraints**: Time, budget, resources, dependencies
4. **Clarify Boundaries**: What's in scope vs explicitly out

**Scope Template**:
```markdown
## Project Scope: [Name]

**Objective**: [Clear statement of what will be achieved]
**Success Criteria**: [How we know it's done right]
**Stakeholders**: [Who is involved/affected]
**Constraints**:
- Time: [Deadline or timeframe]
- Resources: [Available people, budget, tools]
- Dependencies: [External factors]
**In Scope**: [What's included]
**Out of Scope**: [What's explicitly excluded]
```

### Phase 2: Work Breakdown

**Decomposition Rules**:
- Break work into tasks that can be completed in 1-5 days
- Each task has a clear deliverable
- Tasks are independently verifiable
- No task should be "and then magic happens"

**Work Breakdown Structure**:
```
Project
├── Phase 1: [Name]
│   ├── Task 1.1: [Specific deliverable]
│   ├── Task 1.2: [Specific deliverable]
│   └── Task 1.3: [Specific deliverable]
├── Phase 2: [Name]
│   ├── Task 2.1: [Specific deliverable]
│   └── Task 2.2: [Specific deliverable]
└── Phase 3: [Name]
    └── Task 3.1: [Specific deliverable]
```

**Task Definition Template**:
```markdown
### Task: [Name]
**Deliverable**: [What is produced]
**Effort**: [Estimate]
**Dependencies**: [What must complete first]
**Owner**: [Who is responsible]
**Acceptance Criteria**: [How we verify completion]
```

### Phase 3: Estimation

**Estimation Approaches**:

| Method | Use When | Accuracy |
|--------|----------|----------|
| T-Shirt Sizing | Early planning, rough scoping | Low (±50%) |
| Story Points | Relative complexity comparison | Medium (±30%) |
| Time-Based | Detailed planning, known work | Higher (±20%) |
| Three-Point | Uncertainty is high | Accounts for variance |

**T-Shirt Sizing**:
| Size | Relative Effort | Typical Duration |
|------|-----------------|------------------|
| XS | Trivial | < 2 hours |
| S | Small | 2-4 hours |
| M | Medium | 1-2 days |
| L | Large | 3-5 days |
| XL | Very Large | 1-2 weeks (should decompose) |

**Three-Point Estimation**:
```
Optimistic (O): Best case, everything goes right
Pessimistic (P): Worst case, problems encountered
Most Likely (M): Realistic expectation

Expected = (O + 4M + P) / 6
```

**Estimation Anti-Patterns**:
- ❌ Estimating without understanding scope
- ❌ Ignoring unknowns and risks
- ❌ Padding estimates instead of stating uncertainty
- ❌ Treating estimates as commitments
- ❌ Not revisiting estimates as information emerges

### Phase 4: Dependency Mapping

**Dependency Types**:
| Type | Description | Example |
|------|-------------|---------|
| Finish-to-Start | B can't start until A finishes | Deploy after testing |
| Start-to-Start | B can't start until A starts | Testing starts when dev starts |
| External | Depends on outside factor | Waiting for vendor response |
| Resource | Same person/resource needed | One dev, two tasks |

**Dependency Visualization**:
```
[Task A] ──► [Task B] ──► [Task C]
                │
                └──► [Task D]

Critical Path: A → B → C (longest sequence)
```

**Critical Path Identification**:
- Identify the longest chain of dependent tasks
- This determines minimum project duration
- Focus risk mitigation on critical path items
- Parallel work happens off critical path

### Phase 5: Risk Identification

**Risk Categories**:
| Category | Examples |
|----------|----------|
| Technical | Unknown technology, integration complexity |
| Resource | Key person unavailable, skill gaps |
| External | Vendor delays, API changes, approvals |
| Scope | Requirements unclear, scope creep |
| Timeline | Aggressive deadlines, competing priorities |

**Risk Assessment Matrix**:
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | H/M/L | H/M/L | [Action to reduce] |
| [Risk 2] | H/M/L | H/M/L | [Action to reduce] |

**Risk Response Strategies**:
- **Avoid**: Change plan to eliminate risk
- **Mitigate**: Reduce likelihood or impact
- **Transfer**: Shift risk to another party
- **Accept**: Acknowledge and monitor

### Phase 6: Timeline Construction

**Timeline Building**:
1. Start with critical path duration
2. Add buffer for risks (10-20% typical)
3. Account for non-working time (holidays, meetings)
4. Set milestones at phase boundaries
5. Identify decision points and dependencies

**Milestone Definition**:
```markdown
### Milestone: [Name]
**Date**: [Target date]
**Criteria**: [What must be true]
**Deliverables**: [What is produced]
**Decision Point**: [Any decisions needed here]
```

**Timeline Formats**:

**Simple List**:
```
Week 1: [Phase/Tasks]
Week 2: [Phase/Tasks]
Week 3: [Phase/Tasks]
Milestone: [Checkpoint]
```

**Gantt-Style** (text):
```
Task          | W1 | W2 | W3 | W4 |
--------------|----|----|----|----|
Task A        | ██ |    |    |    |
Task B        |    | ██ | ██ |    |
Task C        |    |    |    | ██ |
Milestone     |    |    | ◆  |    |
```

---

## Planning Outputs

### Quick Breakdown Format
```markdown
## [Project Name] - Task Breakdown

**Objective**: [One sentence]
**Timeline**: [Duration]

### Tasks
1. [ ] [Task 1] - [Estimate]
2. [ ] [Task 2] - [Estimate]
3. [ ] [Task 3] - [Estimate]

**Total Estimate**: [Sum]
**Dependencies**: [Key dependencies]
```

### Standard Plan Format
```markdown
## Project Plan: [Name]

**Objective**: [Clear goal]
**Timeline**: [Start] to [End]
**Owner**: [Responsible party]

---

### Scope
[In scope / Out of scope]

### Work Breakdown
| Phase | Task | Estimate | Owner | Dependencies |
|-------|------|----------|-------|--------------|
| 1 | [Task] | [Est] | [Who] | [Deps] |

### Timeline
[Week-by-week or milestone view]

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|

### Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
```

### Comprehensive Roadmap Format
```markdown
## Roadmap: [Initiative Name]

**Vision**: [What success looks like]
**Timeline**: [Quarters/Months]
**Stakeholders**: [Key parties]

---

### Executive Summary
[2-3 paragraph overview]

### Phases

#### Phase 1: [Name] - [Dates]
**Objective**: [Goal]
**Key Deliverables**:
- [Deliverable 1]
- [Deliverable 2]
**Milestone**: [Phase completion criteria]
**Resources**: [Required]
**Risks**: [Phase-specific risks]

[Repeat for each phase]

### Dependencies & Critical Path
[Visualization and explanation]

### Risk Register
[Full risk assessment]

### Resource Requirements
[People, budget, tools]

### Success Metrics
[How we measure success]

### Decision Points
[Key decisions and timing]
```

---

## Prioritization Frameworks

### MoSCoW Method
| Priority | Meaning | Guidance |
|----------|---------|----------|
| Must Have | Critical, non-negotiable | Project fails without these |
| Should Have | Important, high value | Include if possible |
| Could Have | Nice to have | Include if time permits |
| Won't Have | Out of scope for now | Explicitly deferred |

### Impact/Effort Matrix
```
        │ Low Effort │ High Effort │
────────┼────────────┼─────────────┤
High    │ Quick Wins │ Major       │
Impact  │ (Do First) │ Projects    │
────────┼────────────┼─────────────┤
Low     │ Fill-ins   │ Avoid       │
Impact  │            │ (or defer)  │
```

### Value vs Complexity
- Plot items on 2x2 grid
- Prioritize high value, low complexity
- Question high complexity, low value items

---

## Anti-Patterns

### Planning Anti-Patterns
- ❌ Planning without clear objective
- ❌ Skipping scope definition
- ❌ Tasks too large to track ("Build the system")
- ❌ Ignoring dependencies
- ❌ No risk consideration
- ❌ Over-planning (analysis paralysis)
- ❌ Under-planning (winging it)

### Estimation Anti-Patterns
- ❌ Single-point estimates for uncertain work
- ❌ Estimating under pressure to please
- ❌ Not accounting for meetings, reviews, rework
- ❌ Treating estimates as promises

---

## Quality Checklist

### Before Delivering Plan
- [ ] Objective clearly stated
- [ ] Scope defined (in and out)
- [ ] Tasks decomposed to actionable size
- [ ] Estimates provided with basis
- [ ] Dependencies identified
- [ ] Critical path understood
- [ ] Risks identified with mitigations
- [ ] Timeline realistic with buffer
- [ ] Success criteria defined
- [ ] Stakeholders identified

---

*Plans are hypotheses about the future. Build them thoughtfully, revisit them regularly, and adapt as reality unfolds.*
