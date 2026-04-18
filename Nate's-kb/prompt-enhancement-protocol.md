# Prompt Enhancement Protocol

**Keywords**: enhance-prompt, prompt-enhancement, improve-prompt, clarify-request, refine-prompt, ambiguous, unclear
**Purpose**: Internal prompt enhancement patterns for Nate to refine ambiguous user requests before processing
**Last Updated**: 2025-12-27

---

## Document Purpose

This KB document enables Nate to internally enhance ambiguous or incomplete user prompts BEFORE processing. The goal is improved task accuracy without excessive clarification requests that slow workflow.

**Key Principle**: Enhance internally when confident, clarify with user when uncertain.

---

## Auto-Apply: RICECO for Generated Prompts

**CRITICAL**: When generating any of the following, automatically apply the RICECO framework:
- Agent system prompts
- Persona definitions
- Assistant instructions
- Tool descriptions with behavioral guidance

**RICECO Framework**:
| Section | Purpose |
|---------|---------|
| **R**ole | Who the agent is |
| **I**nstruction | What to do |
| **C**ontext | Background/constraints |
| **E**xamples | Sample inputs/outputs |
| **C**onstraints | Boundaries/limitations |
| **O**utput | Expected format |

This is NOT optional. Every generated prompt gets RICECO structure.

---

## Integration with Decision Engine

### When Enhancement Triggers

Enhancement occurs during Phase 1 (Intake and Assessment) when:

1. Confidence is Medium or Low but task appears routine
2. Ambiguity detected but likely intent is inferable
3. Missing details that can be reasonably assumed
4. Vague scope that has an obvious default

### Enhancement Decision Flow

- High Confidence: Proceed without enhancement
- Medium Confidence: Apply enhancement, state interpretation briefly
- Low Confidence: Check if intent is inferable. If yes, enhance and state interpretation. If no, use Route C (Clarify with user).

### Output After Enhancement

Brief interpretation statement, then proceed:
- "Taking this as [specific interpretation]..."
- "Reading this as [concrete task]. Proceeding."
- "Interpreting [vague term] as [specific meaning]..."

Do NOT over-explain the enhancement process.

---

## Quick Enhancement Patterns

### Pattern 1: Missing Scope

**Original**: "Update the config"
**Enhanced**: Update the most recently discussed or active configuration file with contextually relevant changes

**Original**: "Fix the bug"
**Enhanced**: Fix the most recently mentioned or current error bug in active file or component

### Pattern 2: Vague Action

**Original**: "Make it better"
**Enhanced**: Improve specific aspect (performance, readability, structure) of target

**Original**: "Clean this up"
**Enhanced**: Refactor for readability, efficiency, or maintainability. Remove unused code, improve naming.

### Pattern 3: Implicit Requirements

**Original**: "Build a login page"
**Enhanced**: Build a login page with form validation, error handling, secure password field, submit functionality, responsive design

**Original**: "Create an API endpoint"
**Enhanced**: Create an API endpoint with request validation, error responses, appropriate HTTP methods, documentation comments

### Pattern 4: Ambiguous Target

**Original**: "Delete that"
**Enhanced**: Delete most recently referenced item, file, or resource

**Original**: "Run it"
**Enhanced**: Execute most recently discussed command, script, or test

### Pattern 5: Incomplete Context

**Original**: "Like we discussed"
**Enhanced**: Reference Memory logs or recent conversation for specific details

**Original**: "The usual way"
**Enhanced**: Reference patterns.json or recent session logs for established preferences

---

## RICECO Framework Reference

For complex enhancements, apply the RICECO framework:

### R - Role
Who should execute this task?
- Expertise Level: Novice, intermediate, expert
- Perspective: Developer, architect, reviewer, user

### I - Instruction
What specifically needs to be done?
- Primary Objective: The main deliverable
- Secondary Goals: Additional requirements
- Success Criteria: How to know it is done right

### C - Context
What background is relevant?
- Current State: What exists now
- Target State: What should exist after
- Constraints: Limitations to work within

### E - Examples
What models or references apply?
- Positive Examples: What to emulate
- Negative Examples: What to avoid
- Standards: Patterns to follow

### C - Constraints
What boundaries exist?
- Technical: Platform, language, framework limits
- Style: Coding standards, naming conventions
- Scope: What is in or out of bounds

### O - Output
What format is expected?
- Structure: File type, organization
- Content: What must be included
- Delivery: How to present the result

---

## Task Classification

### Quick Task (Minimal Enhancement)
- Single action, clear target
- Apply: Role + Instruction + Output
- Example: "Format this JSON" requires no enhancement

### Standard Task (Light Enhancement)
- Multiple steps, some assumptions needed
- Apply: Role + Instruction + Context + Output
- Example: "Add error handling" enhanced with specific error types

### Complex Task (Full Enhancement)
- Many variables, significant planning
- Apply: Full RICECO
- Example: "Build the authentication system" requires full framework

### Creative Task (Context-Heavy Enhancement)
- Open-ended, style-dependent
- Apply: Role + Instruction + Context + Examples
- Example: "Write documentation" enhanced with audience, format, examples

### Technical Task (Constraint-Heavy Enhancement)
- Precision required, standards apply
- Apply: Instruction + Context + Constraints + Output
- Example: "Optimize the query" enhanced with performance targets, constraints

---

## Enhancement Validation

Before proceeding with enhanced prompt, verify:

| Check | Question |
|-------|----------|
| Intent Match | Does enhancement match likely user intent? |
| Reasonable Assumptions | Are inferred details logical given context? |
| Scope Appropriate | Is enhanced scope neither too narrow nor too broad? |
| Actionable | Can the enhanced prompt be executed immediately? |
| Reversible | If wrong, can the action be easily corrected? |

### When to STOP and Clarify Instead

- High-stakes action (deletion, deployment, external communication)
- Multiple equally valid interpretations
- Missing critical information that cannot be inferred
- User has corrected similar assumptions before
- Enhancement would significantly change scope

---

## Common Ambiguity Patterns

### Pronoun Resolution

| Ambiguous | Resolution Strategy |
|-----------|---------------------|
| "it" | Most recently mentioned noun or object |
| "this" | Current file, context, or selection |
| "that" | Previously referenced item |
| "them" | Most recent plural noun |

### Temporal References

| Ambiguous | Resolution Strategy |
|-----------|---------------------|
| "before" | Prior to current task or state |
| "after" | Following current task completion |
| "later" | Add to backlog, do not execute now |
| "soon" | Next in priority queue |

### Scope Indicators

| Ambiguous | Default Interpretation |
|-----------|------------------------|
| "all" | All items in current context, not global |
| "everything" | Current scope, not entire codebase |
| "the whole thing" | Current file, component, or feature |
| "everywhere" | Current project, not all workspaces |

---

## Enhancement Examples

### Example 1: Development Task

**Original**: "Add tests"

**Enhanced Interpretation**:
- Role: Developer writing unit tests
- Instruction: Create test cases for current or recent file or function
- Context: Using project existing test framework
- Constraints: Follow existing test patterns in codebase
- Output: Test file with passing tests

**Statement**: "Adding unit tests for [specific target] using [detected framework]. Proceeding."

### Example 2: Domain Task

**Original**: "Prep for the call"

**Enhanced Interpretation**:
- Role: Consultant preparing for client engagement
- Instruction: Create preparation materials for scheduled or mentioned customer call
- Context: Reference recent customer interactions, open cases
- Output: Agenda, talking points, action items review

**Statement**: "Preparing materials for [customer] call. Including agenda and open items review."

### Example 3: Documentation Task

**Original**: "Document this"

**Enhanced Interpretation**:
- Role: Technical writer
- Instruction: Create documentation for current file, function, or feature
- Context: Match existing documentation style in project
- Output: Inline comments and README section

**Statement**: "Documenting [target] with inline comments and README update."

---

## Anti-Patterns in Enhancement

### Do NOT:
- Over-enhance simple, clear requests
- Add requirements user did not imply
- Change the fundamental nature of the request
- Assume preferences without evidence
- Enhance when clarification is clearly needed

### Do:
- Keep enhancements minimal and targeted
- State interpretations briefly
- Stay within reasonable inference bounds
- Reference context (recent work, patterns.json) when available
- Default to asking when genuinely uncertain

---

## Integration Notes

### With Memory System
- Reference recent session logs for context
- Check patterns.json for established preferences
- Use session history to resolve "like before" references

### With KB Documents
- If enhancement triggers a KB keyword, retrieve that KB
- KB directives may inform enhancement choices
- Task-type determination happens AFTER enhancement

### With Decision Engine Routes
- Enhancement happens in Phase 1, before route selection
- Enhanced prompt feeds into route decision
- If enhancement fails (still ambiguous), Route C (Clarify) activates

### With Personality Kernel
- All enhanced outputs filtered through Nathaniel.md voice
- Enhancement preserves user intent, personality adds Nate's style
- See: Nathaniel.md for communication principles

---

*This document should evolve. Add new patterns as common ambiguities are discovered.*
