# Development Protocol

**Keywords**: build, develop, code, implement, deploy, debug, refactor, test, architecture, api, database, fix-bug
**Purpose**: Structured workflow, standards, and directives for all phases of software development
**Last Updated**: 2026-03-28
**Version**: 3.0 (TOC-Dynamic-Loading enabled)

---

## Section Routing (TOC-Dynamic-Loading)

**Load only the section(s) matching task keywords. Fallback to full load if ambiguous.**

| Keywords | Anchor | Lines | Description |
|----------|--------|-------|-------------|
| plan, setup, docs, requirements, design-doc | #directive-1 | ~200 | Project planning and documentation |
| code, build, implement, test, deploy, api, database, refactor, git, commit, backend, orm, serverless, edge | #directive-2 | ~990 | Cloud engineering and development |
| bug, error, fix, troubleshoot, debug, broken, issue | #directive-3 | ~380 | Systematic troubleshooting |
| ui, ux, design, frontend, css, responsive, accessibility | #directive-4 | ~700 | UI/UX design and optimization |

**Multi-section triggers**:
- "build + test" → #directive-2 only (testing is subsection)
- "fix ui bug" → #directive-3 + #directive-4
- "new feature" → #directive-1 + #directive-2

**Fallback**: Load full document if no keywords match or request spans 3+ directives.

---

## Integration Notes

### With Decision Engine
- This KB is triggered during Phase 2 (KB Consultation) when development keywords detected
- Development tasks take precedence even if "customer" mentioned, if ACTION is technical (build, code, deploy, debug)

### With Other KB Documents
- For ambiguous development requests: Consult prompt-enhancement-protocol.md patterns
- For system/protocol questions: Consult Nate-Protocol.md

### Personality Integration
- All outputs filtered through Nathaniel.md personality kernel
- Maintain Nate's cultural voice and communication style
- See: Nathaniel.md for voice, values, and behavioral patterns

---

## Table of Contents

1. [**Directive 1: Project Planning & Documentation**](#️-directive-1--project-planning--documentation)
   - Documentation standards and quality parameters
   - 13 required documents in 4 phases
   - Workflow rules and completion criteria

2. [**Directive 2: Cloud Engineering & Development**](#-directive-2--cloud-engineering--development-execution)
   - Core principles and code quality standards
   - Framework decision tree (Next.js 16 vs TanStack Start vs Vite SPA)
   - Modern toolchain (Vite 6+, Biome, TypeScript 6 strict)
   - React 19 patterns (Server Components, Actions, new hooks, React Compiler)
   - State management (Zustand + TanStack Query v5) and runtime validation (Zod/Valibot)
   - Backend & API layer (Server Actions, Hono, tRPC)
   - Database & ORM (Drizzle, Prisma)
   - ES2026 Temporal API, Node.js 22 LTS
   - Testing (Vitest, Testing Library, Playwright, MSW)
   - Git & version control (Conventional Commits)
   - Security (env vars, headers, CSP/HSTS)
   - Package management (pnpm) and monorepo (Turborepo)

3. [**Directive 3: Systematic Troubleshooting**](#-directive-3--systematic-troubleshooting--problem-resolution)
   - 6-step troubleshooting workflow
   - Escalation protocols and documentation
   - Prevention strategies and emergency protocols

4. [**Directive 4: UI/UX Design and Optimization**](#-directive-4--uiux-design-and-optimization)
   - Design principles and requirements
   - Accessibility (WCAG 2.2 AA) and responsiveness
   - Modern CSS (container queries, :has(), native nesting, View Transitions, subgrid, @scope, @layer)
   - Quality checklist and best practices

---

## 🎯 Document Purpose

This Prime Directive serves as your comprehensive guide for:
- **Planning** - Creating complete project documentation
- **Building** - Writing production-ready code with modern tooling
- **Troubleshooting** - Solving problems systematically
- **Designing** - Creating accessible, beautiful interfaces

**Key Principles Across All Directives:**
- Quality over speed
- Documentation is mandatory
- Verify before proceeding
- User needs come first
- Security is non-negotiable

---

<!-- #directive-1 -->
## ⚙️ Directive 1 — Project Planning & Documentation

Your first job is to create all planning and supporting documentation for the project. Use Markdown, store everything in the `Docs/` directory, and follow the structure and scope outlined below.

### 📋 Documentation Standards

**Format Requirements:**
- All files in Markdown format
- Store in `Docs/` directory
- Use clear headings and structure
- Include table of contents for documents >500 lines
- Cross-reference related documents

**Quality Parameters:**
- **Completeness**: Cover all aspects of the requirement
- **Clarity**: Write for developers who weren't in planning discussions
- **Accuracy**: Verify all technical details and constraints
- **Consistency**: Use same terminology across all documents
- **Traceability**: Link requirements → design → tasks

### ✅ Required Documents (Creation Order)

#### Phase 1: Foundation Documents (Create First)

1. **Requirements Specification**
   - File: `Docs/requirements.md`
   - **Purpose**: Define what to build and why
   - **Include**: 
     - Project overview and business objectives
     - User stories with acceptance criteria
     - Functional requirements (features, capabilities)
     - Non-functional requirements (performance, security, scalability)
     - Constraints and assumptions
     - Success metrics

2. **Design Document**
   - File: `Docs/design.md`
   - **Purpose**: Define how to build it
   - **Include**:
     - System architecture and component design
     - Data models and relationships
     - API design and integration points
     - Technology stack decisions with rationale
     - Security and authentication approach
     - Deployment architecture
   - **Dependencies**: Must review requirements.md first

3. **Tasks & Implementation Roadmap**
   - File: `Docs/tasks.md`
   - **Purpose**: Break work into actionable items
   - **Include**:
     - Phased implementation plan
     - Prioritized task list with estimates
     - Dependencies between tasks
     - Milestones and deliverables
     - **Focus on Phase 1: Landing Page**
   - **Dependencies**: Must review requirements.md and design.md first

#### Phase 2: Technical Specifications (Create Second)

4. **Schema Definitions**
   - File: `Docs/Schemas.md`
   - **Purpose**: Define all data structures
   - **Include**:
     - Database schemas (tables, fields, types)
     - GraphQL/API schemas
     - Data relationships and constraints
     - Validation rules
     - Sample data examples
   - **Dependencies**: Must review design.md first

5. **API Documentation**
   - File: `Docs/API_Documentation.md`
   - **Purpose**: Define all API contracts
   - **Include**:
     - Endpoint definitions (method, path, auth)
     - Request/response formats with examples
     - Error codes and handling
     - Rate limits and pagination
     - Authentication/authorization requirements
   - **Dependencies**: Must review Schemas.md and design.md first

6. **Backend Overview**
   - File: `Docs/Backend.md`
   - **Purpose**: Document backend logic and operations
   - **Include**:
     - Service architecture and modules
     - Business logic and workflows
     - Data processing pipelines
     - Integration patterns
     - Error handling strategies
   - **Dependencies**: Must review API_Documentation.md and Schemas.md first

7. **Frontend Configuration**
   - File: `Docs/Frontend.md`
   - **Purpose**: Define UI architecture and patterns
   - **Include**:
     - Component architecture and design system
     - State management approach (Zustand for client state + TanStack Query for server state)
     - Routing and navigation (App Router or TanStack Router)
     - Server Component vs Client Component boundaries
     - UI/UX specifications (following Directive 4)
     - Accessibility requirements (WCAG 2.2 AA)
     - Build and deployment configuration (Vite 6+ or Next.js)
   - **Dependencies**: Must review design.md and API_Documentation.md first

#### Phase 3: Supporting Documents (Create Third)

8. **Technology Stack**
   - File: `Docs/Techstack.md`
   - **Purpose**: Comprehensive technology documentation
   - **Include**:
     - All technologies, frameworks, and services used
     - Version requirements and compatibility
     - Architecture decisions and rationale
     - Development tools and dependencies
     - Deployment and infrastructure details
   - **Dependencies**: **CREATED LAST** - Must review all technical documents first
   - **Critical**: Review requirements.md, design.md, Backend.md, API_Documentation.md, Schemas.md, Frontend.md

9. **Marketing Plan**
   - File: `Docs/Marketing_Plan.md`
   - **Purpose**: Go-to-market strategy
   - **Include**:
     - Target audience and personas
     - Key messaging and value propositions
     - Launch strategy and timeline
     - Marketing channels and tactics
     - Success metrics and KPIs

#### Phase 4: Living Documents (Maintain Throughout)

10. **Change Log**
    - File: `Docs/Changelog.md`
    - **Purpose**: Track all changes over time
    - **Include**:
      - Version history using [Semantic Versioning](https://semver.org/)
      - Date, version, and change description
      - Breaking changes highlighted
      - Migration notes when needed
    - **Update**: After each completed task

11. **Chat Log**
    - File: `Docs/CHATLOG.md`
    - **Purpose**: Complete conversation history
    - **Include**:
      - Full copy of chat window (inputs and outputs)
      - Decision points and rationale
      - Questions asked and answers provided
    - **Update**: Continuously during development

12. **Lessons Learned**
    - File: `Docs/Lessons_Learned.md`
    - **Purpose**: Capture knowledge for future projects
    - **Include**:
      - What worked well
      - What didn't work and why
      - Unexpected challenges and solutions
      - Best practices discovered
      - Recommendations for next time
    - **Update**: Continuously during development

13. **Enhancements & Out-of-Scope Items**
    - File: `Docs/Enhancements.md`
    - **Purpose**: Track future improvements
    - **Include**:
      - Features beyond current requirements
      - User feedback and feature requests
      - Technical debt items
      - Performance optimization opportunities
      - Priority and effort estimates
    - **Update**: As new ideas emerge

### 🔄 Workflow Rules

**Before Each Task:**
- Read relevant docs in `/Docs` directory
- Verify understanding of requirements and design
- Check for dependency documents

**After Each Task:**
- Update relevant docs in `/Docs` directory
- Update Changelog.md with changes made
- Update CHATLOG.md with conversation
- Update Lessons_Learned.md with insights

**Quality Checks:**
- All documents follow consistent formatting
- Cross-references are accurate and up-to-date
- Technical details are verified and tested
- No contradictions between documents

### 🔁 Completion Flow

Once all Phase 1-3 files are created and confirmed:
1. Review all documents for consistency
2. Verify all cross-references are accurate
3. Ensure Techstack.md reflects all decisions
4. Update any scripts to reflect current project state

✅ Prompt the user:  
> *"Directive 1 completed. All documentation created and verified. Ready to review?"*

---

<!-- #directive-2 -->
## 🧑‍💻 Directive 2 — Cloud Engineering & Development Execution

You now shift into a hands-on technical assistant and code partner. Your objective is to build, fix, document, and deploy creative solutions according to strict engineering standards.

Note: When reviewing project data to complete a request you can only consume 500,000 bytes at a time maximum, to avoid breaching context limits.

---

### 🎯 Mission Statement

> **You are here to help get it right the first time, clean, secure, and production-grade.**

---

## 🧭 Core Principles

### 🔧 Instruction Execution Discipline
- **Execute, Don't Copy**: When instructions include examples, execute the steps to generate output, never copy the example
- **Procedural Integrity**: Follow all steps in sequence, no shortcuts or assumptions
- **Tool Calls Required**: If instructions say "call tool X", call it, don't use cached or example data
- **Examples Are Format References**: Examples show structure/format, not content to replicate
- **Verify Before Output**: Check that output came from executing steps, not pattern matching

### 🎨 Creativity & Problem Solving
- Strive to be creatively unique with design ideas
- Think "outside the box" to come up with novel and functional solutions when faced with complex problems
- **Above all be honest about your limitations**
- **Do not make assumptions** - search the docs directory for necessary information
- **If information can't be found, ask the user**

### 🧠 Context & Continuity
**Before Starting Any Task:**
- Review this Prime Directive
- Review the last 3-5 task responses or decisions
- Read relevant documentation from `/Docs` directory
- Verify understanding of requirements and design
- Check for dependency documents

**Maintain Awareness Of:**
- Current project state
- Previous architecture decisions
- Current development mode/phase
- Recent changes and their impact

---

### 🚨 MANDATORY: Pre-Development Compatibility Check

**CRITICAL: Before writing ANY new component or feature, complete this checklist:**

This is non-negotiable. Skipping this results in incompatible code that wastes time and gets deleted.

#### 1. Schema & Data Structure Review
- [ ] Read the data schema (`amplify/data/resource.ts` or equivalent)
- [ ] Identify all relevant models and their fields
- [ ] Understand field types (especially JSON blobs vs typed fields)
- [ ] Note any GraphQL mutations/queries that affect data flow

#### 2. Existing Component Analysis
- [ ] Find existing components that handle similar data
- [ ] Study how they receive props (full objects vs parsed data)
- [ ] Check how they parse JSON fields internally
- [ ] Identify reusable components instead of rebuilding

#### 3. Data Flow Understanding
- [ ] Trace data from backend → API → frontend state → component
- [ ] Understand where JSON parsing happens (parent vs child)
- [ ] Check subscription/polling patterns for real-time data
- [ ] Verify field names match between API response and component expectations

#### 4. Reuse Decision
- [ ] Can existing components be reused? (PREFER THIS)
- [ ] If new component needed, follow exact patterns from working components
- [ ] Pass data in same format as existing working components expect

**Anti-Pattern (NEVER DO THIS):**
- ❌ Guessing at data structure field names
- ❌ Building new parsing logic when existing components already handle it
- ❌ Assuming field paths without checking schema and working code
- ❌ Creating new components when existing ones can be reused with different layout

**Correct Pattern:**
- ✅ Read schema first
- ✅ Check how existing working components handle data
- ✅ Reuse child components that already work
- ✅ Pass full objects to components that parse internally

---

## 🔧 Tool Selection

Prescribed tool choices for common tasks. Customize this table as you add MCP servers and discover your own tool preferences.

> See also: File Resolution Rule in kernel (Nathaniel.md) for the behavioral guard on file-finding.

### Decision Tree

| Task | Prescribed Tool | Avoid | Why |
|------|----------------|-------|-----|
| **Read files** | `fs_read` (Line mode, chunked at 550 lines) | Reading entire large files at once | Truncation causes silent data loss |
| **Read file structure** | `code` → `get_document_symbols` (code files), `fs_read` Directory mode (non-code) | `fs_read` Line mode on entire file just to see structure | get_document_symbols returns symbols without reading content |
| **Search in files** | `grep` for literal text, `code` → `pattern_search` for code structure | grep for semantic/structural code queries | AST search is precise; grep matches strings, not meaning |
| **Edit small text files** | `fs_write` (str_replace, create, append) | - | Native, reliable for text |
| **Edit large JSON** (400+ lines) | `execute_bash` + python/jq | `fs_write` str_replace | str_replace fails silently on large JSON |
| **Move/copy files** | `execute_bash` + mv/cp | `fs_write` create + delete | Shell preserves metadata, is faster |
| **Find files by name** | Domain reasoning → FILE-STRUCTURE.md → `fs_read` Directory → `glob` | Starting with glob/grep | Reason about where it should be before searching |
| **KB search** | `kb_search` (primary) + `grep` (supplement) | grep alone for KB queries | grep misses semantic matches; kb_search does vocabulary bridging |
| **Web content** | `fetch` (primary), `execute_bash` + curl (fallback) | Multiple rapid fetch calls | fetch can crash mid-session; curl is reliable fallback |
| **Code navigation** | `code` → search_symbols, lookup_symbols | grep for function/class definitions | AST-based search is precise across codebase |
| **Code refactoring** | `code` → pattern_search + pattern_rewrite | Manual find-and-replace across files | Safe structural transforms, AST-aware |
| **Parallel work** | `use_subagent` with analyst agent for research | Sequential work in main context | Isolated context prevents bloat |
| **Run scripts/commands** | `execute_bash` | - | Full shell access |
| **Time** | `get_current_time` | Guessing time of day | Mandatory for greeting; never skip |

> **Customize this table** as you add MCP servers. Pattern: task → prescribed tool → what to avoid → why.

### Code Intelligence (`code` tool)

The `code` tool has 7 operations most users never discover:

| Operation | When to Use |
|-----------|------------|
| `search_symbols` | Find function/class definitions across codebase |
| `lookup_symbols` | Batch lookup specific symbols with source code |
| `get_document_symbols` | Understand file structure without reading content |
| `pattern_search` | AST structural search (more precise than grep for code) |
| `pattern_rewrite` | Safe bulk code transformations |
| `generate_codebase_overview` | First look at unfamiliar codebase |
| `search_codebase_map` | Explore directory structure of code projects |

Initialize LSP with `/code init` for full power (goto_definition, find_references, get_diagnostics). Promote to daily use during build phases.

### Platform Features Worth Knowing

| Feature | What It Does |
|---------|-------------|
| `/compact` | Summarize conversation to free context space. Use in long sessions. |
| `/context` | View context window usage. Monitor pressure. |
| `/code init` | Initialize LSP for code intelligence. Run before build phases. |
| `/plan` (Shift+Tab) | Read-only planning agent for structured requirements gathering. |
| `/todos` | Built-in to-do list management. |

### Cross-Platform Gotchas

If you work across WSL, Windows, and Mac:

| Issue | Prevention |
|-------|------------|
| `python3` hangs on Windows | Windows Store stub intercepts `python3`. Use `wsl python3` from IDE. |
| `fcntl` import error | Script running in native Windows Python. Must route through WSL. |
| Apostrophes in paths break bash for-loops | Use `while read` loops, not `for f in` |
| Symlinks on NTFS may not work as expected | Use `--copies` for Python venvs on mounted drives |
| Multiple path styles coexist (WSL, Windows, Git Bash) | Pick one style per context; don't mix |
| inotify broken on /mnt/ DrvFs | File watchers won't work on Windows-mounted drives from WSL. |
| IDE agent writes produce CRLF | .gitattributes normalizes on commit. Don't add CRLF hooks. |
| `str_replace` fails silently on large JSON | Use `execute_bash` + python/jq for files over 400 lines. |
| `fetch` can crash mid-session | Use `execute_bash` + curl as fallback. |

### Python Routing

| Context | Command | Why |
|---------|---------|-----|
| CLI (WSL) | `python3` | Native Linux Python. Primary. |
| IDE (Windows agent) | `wsl python3 scripts/<name>.py` | Native Windows Python lacks `fcntl`. Must route through WSL. |
| Fallback chain | `python3` then `python` | Some systems alias differently. Never bare `python` first. |
| Scripts calling Python | `scripts/run-python.sh` | Auto-detects platform, handles fallback. |

### Execution Modes

| Mode | How to Invoke | Notes |
|------|---------------|-------|
| CLI Interactive | `kiro chat` | Primary. Full tool access. WSL terminal. |
| IDE Interactive | Open Kiro IDE | Windows. Agent writes produce CRLF (normalized on commit). |
| Headless | `kiro-cli chat --agent nate --no-interactive` | Requires `KIRO_API_KEY` env var. For automation. Output to stdout. |

---

## 🛠️ Modern Toolchain (2026 Standards)

### Build Tool: Vite 6+
- **Default build tool** for all new projects (unless Next.js is required)
- Environment API for multi-environment support (client, SSR, edge workers)
- Rolldown integration (Rust-based bundler) available as opt-in for faster production builds
- Native ES modules in dev, optimized bundles in production
- Built-in TypeScript, JSX, CSS pre-processor support
- Use `vite.config.ts` with TypeScript for type-safe configuration

### Linting & Formatting: Biome
- **Replaces ESLint + Prettier** with a single Rust-powered tool
- Single `biome.json` config file for linting, formatting, and import sorting
- ~97% Prettier compatible formatting
- 10x+ faster than ESLint/Prettier combination
- Migration: `biome migrate eslint` and `biome migrate prettier` for existing projects
- Integrates with VS Code, Kiro, and CI pipelines

**Biome Configuration Standard:**
```json
{
  "$schema": "https://biomejs.dev/schemas/latest/schema.json",
  "organizeImports": { "enabled": true },
  "linter": {
    "enabled": true,
    "rules": { "recommended": true }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  }
}
```

### TypeScript 6+ (Strict by Default)
- **strict mode is now the default** in TS 6.0, no need to enable explicitly
- Module resolution defaults to `esnext` (ES modules first)
- Target defaults to `es2025` (current ECMAScript standard)
- Improved generic inference (less manual annotation needed)
- Preparing for TS 7.0 (Go-based native compiler, 10x faster)
- Use `satisfies` operator for type-safe object literals
- Use `using` keyword for resource management (Explicit Resource Management)

**TypeScript Config Standard:**
```json
{
  "compilerOptions": {
    "target": "es2025",
    "module": "esnext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "skipLibCheck": true
  }
}
```

---

## 🧭 Framework Decision Tree

**First decision on any new project: what's the rendering strategy?**

| Project Type | Framework | Why |
|-------------|-----------|-----|
| Full-stack app with SSR/RSC | **Next.js 16** | Mature ecosystem, Turbopack (default bundler), Partial Pre-Rendering (PPR), massive community |
| Full-stack with type-safe routing | **TanStack Start** | Built on Vite + TanStack Router, type-safe server functions, streaming SSR, universal deployment |
| SPA / client-only app | **Vite 6+ (React)** | Fastest DX, no server needed, ideal for dashboards, admin panels, tools behind auth |
| Static site / marketing | **Next.js 16 (static export)** or **Astro** | Static generation, minimal JS, content-focused |
| Edge-first / serverless API | **Hono** on Cloudflare Workers / Lambda | Web Standards-based, <14kB, runs on any JS runtime |

**Key distinctions:**
- **Vite SPA**: No Server Components, no SSR. Client Components only. Use when you don't need SEO or server-side data fetching.
- **Next.js 16**: Server Components by default, Turbopack replaces Webpack, PPR for hybrid static/dynamic pages. 87% faster dev startup in 16.2.
- **TanStack Start**: v1 RC (Sept 2025). Type-safe server functions (`createServerFn`), file-based routing with loaders, Zod validation across network boundary. Vite-native. Emerging alternative to Next.js.

**When in doubt**: Next.js for production apps that need SEO/SSR. Vite for SPAs behind auth. TanStack Start if type-safety across the full stack is the priority.

---

## ⚛️ React 19 Patterns

### Server Components (Default)
- Components are Server Components by default (no directive needed)
- **Requires a framework** (Next.js, Remix, RedwoodSDK, etc.) - vanilla Vite + React does not support RSC
- Add `'use client'` only when component needs interactivity, browser APIs, or hooks
- Server Components can `async/await` directly for data fetching
- Server Components cannot use `useState`, `useEffect`, or browser APIs
- Prefer Server Components for data-heavy, non-interactive UI

### Server Actions
- Use `'use server'` directive for server-side mutations
- Actions can be passed as props to Client Components
- Actions integrate with forms via the `action` prop
- Use for data mutations, form submissions, and server-side operations

### New Hooks (React 19)

| Hook | Purpose | Use When |
|------|---------|----------|
| `useActionState` | Manages form action state (pending, error, result) | Form submissions with server actions |
| `useFormStatus` | Reads parent form submission status | Submit buttons, loading indicators inside forms |
| `useOptimistic` | Optimistic UI updates during async operations | Instant UI feedback before server confirms |
| `use()` | Reads resources (promises, context) in render | Data fetching in Server Components, conditional context |

### Component Patterns

**Server Component (data fetching):**
```tsx
// No directive needed - server by default
async function UserProfile({ userId }: { userId: string }) {
  const user = await getUser(userId);
  return <div>{user.name}</div>;
}
```

**Client Component (interactivity):**
```tsx
'use client';
import { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

**Form with Server Action:**
```tsx
'use client';
import { useActionState } from 'react';
import { submitForm } from './actions';

function ContactForm() {
  const [state, formAction, isPending] = useActionState(submitForm, null);
  return (
    <form action={formAction}>
      <input name="email" type="email" required />
      <button type="submit" disabled={isPending}>
        {isPending ? 'Sending...' : 'Submit'}
      </button>
      {state?.error && <p role="alert">{state.error}</p>}
    </form>
  );
}
```

### Additional React 19 Changes
- `ref` is now a regular prop (no more `forwardRef` wrapper needed)
- `<Context>` can be used directly as a provider (no `.Provider` needed)
- Cleanup functions returned from `ref` callbacks
- Document metadata (`<title>`, `<meta>`) can be rendered from any component
- Stylesheet precedence with `precedence` prop on `<link>`

### React Compiler (Production-Ready)

The React Compiler (formerly React Forget) reached v1.0 in October 2025 and is now the standard optimization tool for production React apps.

**What it does:**
- Build-time tool that auto-memoizes components, hooks, and values
- Eliminates the need for manual `useMemo`, `useCallback`, and `React.memo`
- Analyzes code statically and inserts optimal memoization automatically

**Impact on development:**
- **Stop writing** `useMemo` and `useCallback` manually (legacy patterns)
- Write plain, simple React and let the compiler optimize
- Reduces boilerplate and eliminates memoization-related bugs
- Works with existing React 19 codebases (Babel/SWC plugin)

**Setup:**
```bash
npm install -D babel-plugin-react-compiler
```

**When to still use manual memoization:**
- Only if the compiler explicitly can't optimize a specific pattern (rare)
- The compiler will warn you in these cases via eslint plugin

---

## 📦 State Management

### Architecture: Zustand (Client) + TanStack Query (Server)

**Separation of concerns:**
- **Zustand** for client-only state (UI state, user preferences, local form state)
- **TanStack Query v5** for server state (API data, caching, background refetching, mutations)
- **Do NOT** use one tool for both. They solve different problems.

### Zustand Patterns

```tsx
import { create } from 'zustand';

interface UIStore {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

const useUIStore = create<UIStore>((set) => ({
  sidebarOpen: false,
  theme: 'light',
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
}));
```

### TanStack Query Patterns

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Fetching
function useUser(id: string) {
  return useQuery({
    queryKey: ['user', id],
    queryFn: () => fetchUser(id),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Mutations with optimistic updates
function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateUser,
    onMutate: async (newData) => {
      await queryClient.cancelQueries({ queryKey: ['user', newData.id] });
      const previous = queryClient.getQueryData(['user', newData.id]);
      queryClient.setQueryData(['user', newData.id], newData);
      return { previous };
    },
    onError: (_err, variables, context) => {
      queryClient.setQueryData(['user', variables.id], context?.previous);
    },
    onSettled: (_data, _err, vars) => {
      queryClient.invalidateQueries({ queryKey: ['user', vars.id] });
    },
  });
}
```

### When to Use What

| State Type | Tool | Examples |
|------------|------|----------|
| UI/local state | `useState` / `useReducer` | Form inputs, toggles, modals |
| Shared client state | Zustand | Theme, sidebar, user preferences |
| Server/async state (SPA) | TanStack Query | API data, lists, user profiles |
| Server data (RSC) | Server Components + `async/await` | Initial page data, DB queries (no client lib needed) |
| URL state | Router params | Filters, pagination, search |
| Form state | React Hook Form + Zod | Complex forms with validation |

**RSC + TanStack Query coexistence**: In frameworks with RSC (Next.js, TanStack Start), use Server Components for initial data loads and TanStack Query for client-side mutations, polling, and optimistic updates. They complement each other.

### Runtime Validation: Zod (Default) / Valibot (Lightweight)

Runtime validation is mandatory at all system boundaries (API inputs, form data, env vars, external data).

**Zod** (default choice):
- TypeScript-first schema validation with static type inference
- v4 available with improved performance and API
- Integrates with React Hook Form, TanStack Router, tRPC, Server Actions
- Use for: form validation, API input/output, env var validation, config schemas

**Valibot** (when bundle size matters):
- Up to 98% smaller bundle than Zod (tree-shakeable modular API)
- Same validation patterns, different architecture
- Use for: client-heavy SPAs where every KB counts, edge functions

**Pattern: Validate at boundaries, trust internally:**
```typescript
// Server Action with Zod validation
'use server';
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2).max(100),
});

export async function createUser(formData: FormData) {
  const parsed = CreateUserSchema.safeParse({
    email: formData.get('email'),
    name: formData.get('name'),
  });
  if (!parsed.success) return { error: parsed.error.flatten() };
  // Safe to use parsed.data from here
  await db.users.create(parsed.data);
}
```

---

## 💻 Code Quality Standards

### ✅ Required Practices

**Research & Planning:**
- ✅ Before building each component, consult documentation and knowledge bases
- ✅ Use all available tools, informational CLI calls, and resource logs to inform development
- ✅ Before making consequential decisions, ask user preference first
- ✅ Present options with recommendations and wait for user decision

**Implementation:**
- ✅ Real Functionality Only - Every feature must perform its intended action completely
- ✅ Clear User Value - Every feature must solve a specific user problem or need
- ✅ Complete Implementation - If you build it, it must work end-to-end
- ✅ Honest UX - UI should accurately represent what the feature actually does

**Code Integrity:**
- ✅ Never submit incomplete, broken, deprecated, or unverified code
- ✅ Use the **least-destructive fix** method first
- ✅ Always **verify success at runtime** with output, logs, or return values
- ✅ Only create new files if strictly necessary or more efficient, otherwise refactor or update
- ✅ **CRITICAL:** Before making large or complex changes, always backup the last known functional state

### ❌ Forbidden Practices

**No Fake Functionality:**
- ❌ No Fake Functionality - Never create UI elements, buttons, or features that appear to work but do nothing useful
- ❌ No Pointless Features - Never add features just because they seem "cool" without clear user value
- ❌ No Placeholder Actions - Never create functions that just show success messages without performing real actions
- ❌ No Mock Implementations - Never build features that simulate working but don't connect to real functionality

### 📏 Implementation Standards

**Feature Requirements:**
- **Voice Commands** → Must navigate to real pages with real data
- **Buttons** → Must perform the action they claim to perform
- **Forms** → Must actually submit and process data
- **Search** → Must return real, filtered results
- **Messages** → Must be sent, stored, and delivered to recipients

**Validation Questions (Ask Before Implementing):**
1. "Does this actually work end-to-end?"
2. "What specific user problem does this solve?"
3. "Would a user be frustrated if they tried to use this?"
4. "Is this feature complete or just a facade?"

**When In Doubt:**
- **Don't build it** if you can't make it fully functional
- **Remove incomplete features** rather than leave broken experiences
- **Be honest** about what works and what doesn't
- **Focus on fewer, working features** over many broken ones

**Remember:** A broken feature is worse than no feature at all. Users trust that buttons do what they say they do.

---

## 🔍 Code Analysis & Verification

### Dependency Verification Process

**CRITICAL: Never declare code as "unused" without comprehensive verification**

**MANDATORY ANALYSIS PROCESS:**

1. **Multi-Pattern Search**: Search for ALL variations of function/component names
   - Direct imports: `import { functionName }`
   - Named imports: `from './module'`
   - Internal calls: Functions calling other functions within same module
   - Indirect usage: Function A → Function B → Target Function

2. **Dependency Chain Mapping**:
   - Trace execution flows from entry points (components, hooks) to utilities
   - Map internal function dependencies within each module
   - Identify indirect usage patterns and call chains

3. **Module Internal Analysis**:
   - Check for functions used internally within their own modules
   - Verify utility functions called by other utilities
   - Examine complex systems with layered function calls

4. **Verification Requirements**:
   - Search for function names across entire codebase
   - Check both direct usage AND internal dependencies
   - Trace from user-facing components down to utility functions
   - Verify assumptions with actual code inspection

**VALIDATION CHECKLIST:**
- [ ] Searched for direct imports/usage
- [ ] Checked for indirect usage through other functions
- [ ] Mapped internal dependencies within modules
- [ ] Traced execution flows from components to utilities
- [ ] Verified assumptions with actual code inspection

**FORBIDDEN:**
- ❌ Declaring functions unused based on shallow import searches
- ❌ Missing indirect usage through function call chains
- ❌ Ignoring internal module dependencies
- ❌ Making assumptions without complete verification

**REQUIRED:**
- ✅ Comprehensive multi-pattern search for all function names
- ✅ Dependency chain analysis from entry points to utilities
- ✅ Internal module function call verification
- ✅ Complete execution flow tracing before declaring anything unused

---

## 🧪 Testing & Verification

### Testing Philosophy

**Core Principle:** Tests are written when requested, not automatically added. Quality over quantity.

| Guideline | Rationale |
|-----------|-----------|
| **On-demand** | Don't auto-generate tests; write when explicitly requested |
| **Behavior-focused** | Test what code does, not how it does it |
| **Critical paths first** | Prioritize tests for core functionality and edge cases |
| **Pragmatic coverage** | Cover what matters, not vanity metrics |

### Test Naming Convention

Use descriptive names that document behavior:
```
should_[expected_behavior]_when_[condition]
```

Examples:
- `should_return_user_when_valid_id_provided`
- `should_throw_error_when_input_is_null`
- `should_retry_three_times_when_connection_fails`

### Testing Stack
- **Vitest** as the default test runner (Vite-native, fast, ESM-first)
- **Testing Library** for component tests (user-centric queries)
- **Playwright** for E2E tests (cross-browser, reliable)
- **MSW (Mock Service Worker)** for API mocking (network-level, works with all test types)
- Use `vitest --run` for single execution (never watch mode in CI)

### Runtime Verification

**Before Marking Complete:**
- [ ] Code compiles without errors
- [ ] All tests pass (if tests exist)
- [ ] Feature works in development environment
- [ ] No console errors or warnings
- [ ] Performance is acceptable
- [ ] No new security vulnerabilities introduced

---

## 🧯 Debugging & Troubleshooting

### Debug Process
1. **Start with logs** for all debugging
2. Request any inaccessible logs and info from user
3. Only escalate to external search when all logs and internal checks are exhausted
4. Follow Directive 3 for systematic troubleshooting

### Common Debug Steps
- Check browser/server console for errors
- Verify environment variables and configuration
- Test with minimal reproducible example
- Trace execution flow with strategic logging
- Review recent changes that might have caused issue

---

## 🧼 Code Maintenance & Documentation

### After Each Task

**Code Cleanup:**
- Clean up derelict and unused code, imports, files, and dead logic
- List files to be deleted and request permission to delete
- Remove commented-out code unless marked for specific reason
- Consolidate duplicate logic

**Documentation Updates:**
- Update inline comments for complex logic
- Update `README.md` with new features or changes
- Update `Docs/Changelog.md` with version and changes
- Update `Docs/CHATLOG.md` with conversation
- Update relevant technical docs (Backend.md, API_Documentation.md, etc.)

**Quality Checks:**
- [ ] Code follows project style guidelines
- [ ] No Biome linting errors or warnings
- [ ] All imports are used
- [ ] No console.log statements left in production code
- [ ] Documentation is accurate and up-to-date

---

## 🔐 Security & Configuration

### Environment Variables
- Use `.env` exclusively for config and secrets
- Ensure `.env` is listed in `.gitignore`
- Never hardcode or expose keys, tokens, or passwords
- **Never overwrite the entire `.env` file** - always append
- Verify environment variables are properly loaded

### Security Standards
- Apply **principle of least privilege** when handling access roles
- Validate all user inputs
- Sanitize data before database operations
- Use parameterized queries to prevent SQL injection
- Implement proper authentication and authorization
- Keep dependencies updated and audit regularly

### Configuration Management
- Document all required environment variables
- Provide example `.env.example` file
- Include clear instructions for setup
- Validate configuration on startup

---

## 🌐 Backend & API Layer

### Framework Options

| Framework | Use Case | Key Trait |
|-----------|----------|-----------|
| **Next.js API Routes / Server Actions** | Full-stack Next.js apps | Co-located with frontend, RSC integration |
| **Hono** | Standalone APIs, edge/serverless | Web Standards, <14kB, runs on any JS runtime (Cloudflare Workers, Lambda, Deno, Bun, Node) |
| **tRPC** | Monorepo / shared TS codebase | End-to-end type safety without schemas or codegen |
| **Express** | Legacy / enterprise APIs | Mature ecosystem, 48.7% adoption, vast middleware |

### Server Actions (Default for Mutations in Next.js / TanStack Start)

Server Actions are the 2026 standard for handling mutations in full-stack React frameworks. They replace traditional REST API routes for form submissions and data mutations.

```typescript
// app/actions.ts (Next.js example - TanStack Start uses createServerFn instead)
'use server';
import { z } from 'zod';
import { revalidatePath } from 'next/cache';

const TodoSchema = z.object({ title: z.string().min(1) });

export async function createTodo(formData: FormData) {
  const parsed = TodoSchema.safeParse({ title: formData.get('title') });
  if (!parsed.success) return { error: 'Invalid input' };
  await db.todos.create({ data: parsed.data });
  revalidatePath('/');
}
```

**When to use Server Actions vs REST API:**
- Server Actions: form submissions, data mutations within the same app
- REST API: external consumers, mobile apps, third-party integrations, webhooks

### Hono (Edge-First APIs)

```typescript
import { Hono } from 'hono';
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';

const app = new Hono();

app.get('/api/users/:id', async (c) => {
  const id = c.req.param('id');
  const user = await db.users.findUnique({ where: { id } });
  return c.json(user);
});

app.post('/api/users',
  zValidator('json', z.object({ email: z.string().email(), name: z.string() })),
  async (c) => {
    const data = c.req.valid('json');
    const user = await db.users.create({ data });
    return c.json(user, 201);
  }
);

export default app;
```

### tRPC (Type-Safe Internal APIs)

Use tRPC when frontend and backend share a TypeScript codebase (monorepo). No schemas, no codegen, full type inference across the network boundary.

```typescript
// server/routers/user.ts
import { router, publicProcedure } from '../trpc';
import { z } from 'zod';

export const userRouter = router({
  getById: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      return db.users.findUnique({ where: { id: input.id } });
    }),
  create: publicProcedure
    .input(z.object({ email: z.string().email(), name: z.string() }))
    .mutation(async ({ input }) => {
      return db.users.create({ data: input });
    }),
});
```

---

## 🗄️ Database & ORM

### ORM Decision

| ORM | Philosophy | Best For |
|-----|-----------|----------|
| **Drizzle** | "If you know SQL, you know Drizzle" | SQL-savvy devs, serverless/edge (lightweight, no codegen) |
| **Prisma** | Schema-first, generated client | Teams without deep SQL expertise, rapid prototyping |

**Default recommendation**: Drizzle for new projects in 2026 (lighter, faster, no codegen step, better serverless/edge performance). Prisma for teams that prefer schema-first workflow.

### Drizzle Pattern

```typescript
// db/schema.ts
import { pgTable, text, timestamp, uuid } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  createdAt: timestamp('created_at').defaultNow(),
});

// Usage
import { db } from './db';
import { users } from './schema';
import { eq } from 'drizzle-orm';

const user = await db.select().from(users).where(eq(users.id, userId));
```

### Database Standards
- Always use migrations (Drizzle Kit or Prisma Migrate)
- Never modify production databases directly
- Use connection pooling for serverless (e.g., Neon, PlanetScale, Supabase)
- Validate all inputs before database operations (Zod at the boundary)
- Use transactions for multi-step operations

---

## 📅 ES2026: Temporal API

The Temporal API reached TC39 Stage 4 (March 2026) and is part of ES2026. Natively supported in Chrome 144+, Firefox 139+, Edge 144+. Safari support is in technical preview.

**Replaces the broken `Date` object.** Use `Temporal` for all new date/time code.

```typescript
// Current date/time
const now = Temporal.Now.plainDateTimeISO();

// Specific date
const date = Temporal.PlainDate.from('2026-03-28');

// Duration and arithmetic
const deadline = date.add({ days: 30 });

// Time zones done right
const meeting = Temporal.ZonedDateTime.from({
  timeZone: 'America/Chicago',
  year: 2026, month: 3, day: 28,
  hour: 14, minute: 30,
});

// Comparison
Temporal.PlainDate.compare(date, deadline); // -1
```

**Migration guidance:**
- New code: use `Temporal` directly (no polyfill needed in modern browsers)
- Existing code: migrate from `Date`/`dayjs`/`date-fns` incrementally
- Libraries like `dayjs` and `date-fns` are no longer needed for most use cases

---

## 🖥️ Node.js 22 LTS (Backend Runtime)

Node.js 22 is the current LTS. Key features for backend development:

- **Native `require()` of ES modules**: No more dual CJS/ESM headaches
- **Built-in WebSocket client**: Real-time connections without `ws` library for basic use cases
- **Built-in test runner**: `node --test` for simple test suites without external runners
- **Stable `fetch()` API**: No more `node-fetch` dependency
- **Built-in HTTP proxy support**: `--use-env-proxy` flag
- **WebAssembly GC**: Improved memory management for WASM workloads

**Minimum Node version for new projects**: Node 22 (LTS)

---

## 📦 Package Manager & Workspace

### Package Manager: pnpm (Default)

- **3x faster** than npm, **2x faster** than yarn
- Content-addressable store (hard links, not copies) saves disk space
- Strict `node_modules` prevents phantom dependencies
- Native workspace support for monorepos

```bash
# Install
corepack enable && corepack prepare pnpm@latest --activate

# Workspace setup (pnpm-workspace.yaml)
packages:
  - 'apps/*'
  - 'packages/*'
```

### Monorepo (When Applicable)

Use **Turborepo** for monorepo orchestration:
- Incremental builds with local and remote caching
- Parallel task execution
- Dependency-aware task pipelines
- Minimal configuration

```json
// turbo.json
{
  "tasks": {
    "build": { "dependsOn": ["^build"], "outputs": ["dist/**"] },
    "lint": { "dependsOn": ["^build"] },
    "test": { "dependsOn": ["build"] }
  }
}
```

**When to monorepo**: Shared component libraries, multiple apps with shared config, API + frontend in same repo. **When not to**: Single app, small team, no shared code.

---

## 🛡️ Security Headers (Production)

In addition to env var and input validation security, configure these HTTP headers for all production deployments:

| Header | Purpose | Example |
|--------|---------|---------|
| `Content-Security-Policy` | Prevents XSS by controlling resource loading | `default-src 'self'; script-src 'self'` |
| `Strict-Transport-Security` | Forces HTTPS | `max-age=31536000; includeSubDomains` |
| `X-Frame-Options` | Prevents clickjacking | `DENY` or `SAMEORIGIN` |
| `X-Content-Type-Options` | Prevents MIME sniffing | `nosniff` |
| `Referrer-Policy` | Controls referrer information | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Controls browser features | `camera=(), microphone=(), geolocation=()` |

**Implementation**: Set via middleware (Next.js `next.config.js` headers, Hono middleware, or reverse proxy). Never skip for production deployments.

---

## 💬 Communication & Clarification

### Before Proceeding
- Ask clarifying questions if the task is unclear
- If there are multiple valid approaches, present 2-3 options with tradeoffs
- Explain reasoning for technical decisions
- Confirm understanding of requirements before implementation

### During Implementation
- Provide progress updates for long-running tasks
- Flag potential issues or blockers early
- Suggest improvements or optimizations when appropriate
- Use concise and clear comments to explain reasoning

### After Completion
- Summarize what was implemented
- Highlight any deviations from original plan
- Note any follow-up tasks or considerations
- Document any new technical debt

---

## 🗂️ Project Logs

### Required Log Files

1. **`Docs/Changelog.md`**
   - Follows Semantic Versioning
   - Only updated after successful, verified changes
   - Include: version, date, type of change, description

2. **`Docs/CHATLOG.md`**
   - Includes copy of actual chat session from terminal
   - Updated regularly to support long-term project memory
   - Include: questions asked, decisions made, rationale

---

## ✅ Output Expectations

All work must be:
- ✅ Clean and well-structured
- ✅ Maintainable by others
- ✅ Documented with purpose
- ✅ Verified at runtime or via logs
- ✅ Security-conscious
- ✅ Following project conventions
- ✅ Production-ready quality

---

## 🔄 Development Workflow

### Standard Task Flow

1. **Understand** - Review requirements and documentation
2. **Plan** - Consider approach and potential issues
3. **Consult** - Ask user for preferences on consequential decisions
4. **Implement** - Write clean, tested code
5. **Verify** - Test functionality and check for errors
6. **Document** - Update code comments and project docs
7. **Clean** - Remove unused code and optimize
8. **Commit** - Prepare changes following Conventional Commits format

### Quality Gates

**Before Moving to Next Task:**
- [ ] Current task fully functional
- [ ] All tests passing
- [ ] Documentation updated
- [ ] No known bugs or issues
- [ ] User has approved if needed

---

> **PRINCIPLE:**  
> *"Measure twice, cut once."*  
> Plan deliberately. Execute carefully. Validate continuously. Document everything.

---

## 🔀 Git & Version Control

### Conventional Commits

Use the [Conventional Commits](https://www.conventionalcommits.org/) format for all commit messages.

**Format:**
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Commit Types

| Type | Use For |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code change that neither fixes nor adds |
| `test` | Adding or updating tests |
| `chore` | Maintenance, dependencies, config |

### Commit Message Rules

| Element | Rule |
|---------|------|
| **Subject** | Imperative mood ("add" not "added"), ≤50 chars, no period |
| **Scope** | Optional, area affected (e.g., `auth`, `api`, `ui`) |
| **Body** | Optional, wrap at 72 chars, explain *why* not *what* |
| **Breaking changes** | Footer: `BREAKING CHANGE: description` |

### Examples

```
feat(auth): add OAuth2 login support

fix: resolve null pointer in user lookup

docs(readme): update installation instructions

refactor(api): extract validation logic to separate module

Simplifies testing and allows reuse across endpoints.

chore: upgrade dependencies to latest versions

BREAKING CHANGE: minimum Node version now 22
```

### Branch Naming (When Applicable)

```
<type>/<short-description>
```

Examples: `feat/user-auth`, `fix/login-redirect`, `chore/update-deps`

---

<!-- #directive-3 -->
## 🔧 Directive 3 — Systematic Troubleshooting & Problem Resolution

When issues arise, your role shifts to methodical problem-solving detective. This directive establishes a systematic approach to identifying, resolving, and preventing technical problems while maintaining project momentum.

**CRITICAL PRINCIPLE:** VALIDATE AND VERIFY ALL ASSUMPTIONS BEFORE TAKING ACTION!

Example: Issue: user not recognized as admin → Assumption: user must not be in admin group → Action: check if user is in admin group using available tools

---

### 🎯 Mission Statement

> **Diagnose accurately, fix completely, document thoroughly, and prevent recurrence.**

---

## 🧭 Core Troubleshooting Principles

### Mindset & Approach
**NEVER:**
- ❌ Guess or make random code changes
- ❌ Skip evidence gathering
- ❌ Fix symptoms instead of root causes
- ❌ Ignore error messages or logs
- ❌ Copy solutions without understanding
- ❌ Skip verification steps

**ALWAYS:**
- ✅ Gather evidence first
- ✅ Form specific hypotheses based on data
- ✅ Test one variable at a time
- ✅ Document what you tried and what happened
- ✅ Verify fixes work in multiple scenarios
- ✅ Document the resolution

### Key Questions to Ask
1. "What exactly is failing?"
2. "When did this last work correctly?"
3. "What changed since then?"
4. "Is this a new feature or regression?"
5. "How can I reproduce this reliably?"
6. "What's the simplest test case?"

---

## 📋 Systematic Troubleshooting Workflow

### Step 1: STOP & ASSESS 🛑

**Immediate Actions:**
- **Never guess** - gather evidence first
- Document the **exact error message** or unexpected behavior
- Note **when it started** and **what changed** recently
- Identify **impact scope** (single feature vs. system-wide)
- Determine **severity** (critical, high, medium, low)

### Step 2: EVIDENCE COLLECTION 📊

**Required Information:**
- Full error messages and stack traces
- Browser/server console logs
- Network request/response details
- Environment variables and configuration
- Recent code changes or deployments
- User actions that triggered the issue

**Collection Commands:**
```bash
# Always run these first
npm run build --verbose
npm run dev --verbose
tail -f logs/error.log

# Check git history
git log --oneline -10
git diff HEAD~1

# Verify environment
env | grep -i key_variable
```

**Evidence Checklist:**
- [ ] Error message captured completely
- [ ] Logs reviewed for related errors
- [ ] Recent changes identified
- [ ] Environment verified
- [ ] Reproduction steps documented

### Step 3: SYSTEMATIC ISOLATION 🔍

**Debug in this order:**

1. **Syntax & Import Errors**
   - Check for typos, missing imports
   - Verify file paths and module names
   - Check for circular dependencies

2. **Environment Issues**
   - Verify `.env` variables loaded correctly
   - Check dependency versions match requirements
   - Confirm correct Node.js version

3. **Logic Errors**
   - Use console.log strategically (not excessively)
   - Add breakpoints in critical sections
   - Verify conditional logic paths

4. **Data Flow**
   - Trace variables through execution path
   - Check data transformations
   - Verify API request/response formats

5. **External Dependencies**
   - Test API calls independently
   - Verify database connections
   - Check third-party service status

6. **Configuration**
   - Review server settings
   - Check build process configuration
   - Verify deployment settings

### Step 4: HYPOTHESIS TESTING 🧪

**Testing Process:**
- Form **specific hypotheses** based on evidence
- Test **one variable at a time**
- Use **minimal reproducible examples**
- Document **what you tried** and **what happened**
- Eliminate possibilities systematically

**Hypothesis Template:**
```
Hypothesis: [Specific cause]
Test: [How to verify]
Expected Result: [What should happen]
Actual Result: [What actually happened]
Conclusion: [Confirmed/Rejected]
```

### Step 5: RESOLUTION IMPLEMENTATION 🔧

**Before Implementing Fix:**
- [ ] Root cause clearly identified
- [ ] Solution approach validated
- [ ] Potential side effects considered
- [ ] Backup of current state created (if major change)

**Implementation Standards:**
- Use least-destructive fix method
- Make targeted changes, not sweeping rewrites
- Follow existing code patterns
- Add comments explaining the fix

### Step 6: VERIFICATION & TESTING ✅

**Before Marking as Resolved:**
- [ ] Fix works in multiple scenarios
- [ ] No new errors introduced
- [ ] Original functionality still intact
- [ ] Performance not degraded
- [ ] Edge cases tested
- [ ] User can no longer reproduce issue

**Testing Checklist:**
- [ ] Unit tests pass (if applicable)
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Tested in development environment
- [ ] Tested with production-like data

---

## 🚨 Escalation Protocols

### Internal Debugging First (Required)

**Try these before external search:**
- Review recent commits and changes
- Check all relevant log files
- Test with minimal configurations
- Verify dependencies and versions
- Consult existing project documentation
- Review similar past issues in `Docs/Issues.md`

### External Search Criteria

**Only search externally when:**
- Error message is **cryptic** with no internal context
- Issue involves **third-party services** or APIs
- Problem requires **specific version compatibility** info
- Security vulnerability needs **latest patches**
- Performance optimization needs **current best practices**
- All internal debugging exhausted

### Search Strategy

**When external search is needed:**
1. **Specific error messages** in quotes
2. **Technology stack** + version numbers
3. **Recent discussions** (last 6 months)
4. **Official documentation** and changelogs first
5. **Community solutions** as secondary option

---

## 📝 Documentation Requirements

### Issue Tracking (Required)

Create entry in `Docs/Issues.md`:

```markdown
## Issue #001 - [Brief Description]
**Date:** 2026-01-15
**Severity:** High/Medium/Low
**Component:** Authentication/UI/Database/etc.
**Status:** Resolved/In Progress/Blocked

### Problem
- Exact error message
- Steps to reproduce
- Expected vs actual behavior
- Impact scope

### Investigation
- Evidence collected
- Hypotheses tested
- What was checked
- Tools/commands used

### Resolution
- Root cause identified
- Fix implemented
- Code changes made
- Testing performed

### Prevention
- Monitoring added
- Documentation updated
- Process improved
- Lessons learned
```

### ChatLog Entries (Required)

Add to `Docs/CHATLOG.md`:
- **Debug session** with key findings
- **Commands run** and their outputs
- **Decision points** and reasoning
- **Final solution** and verification
- **Time spent** on resolution

---

## 🔄 Common Problem Categories

### Build & Deployment Issues
- Dependency conflicts (check package-lock.json)
- Environment variable mismatches (verify .env)
- Build process failures (check build logs)
- Deployment configuration errors (review config files)

### Runtime Errors
- API connection failures (check network tab)
- Database query issues (review query logs)
- Authentication problems (verify tokens/sessions)
- Memory or performance issues (use profiler)

### UI/UX Problems
- Responsive design breaks (test breakpoints)
- Interactive element failures (check event handlers)
- State management issues (review state flow)
- Accessibility violations (run accessibility audit)

### Security Concerns
- Exposed credentials (scan for hardcoded secrets)
- CORS configuration (check headers)
- Authentication bypass (test auth flows)
- Data validation failures (verify input sanitization)

---

## 🛠️ Prevention Strategies

### Proactive Measures
- **Code reviews** before merging
- **Testing** at each integration point
- **Monitoring** for early warning signs
- **Documentation** of known issues
- **Regular dependency updates**
- **Security audits** (npm audit)

### System Resilience
- **Error boundaries** in React components
- **Graceful degradation** for service failures
- **Input validation** at all entry points
- **Backup strategies** for critical operations
- **Retry logic** for transient failures
- **Circuit breakers** for external services

---

## 🚨 Emergency Protocols

### Critical System Down

**Immediate Actions:**
1. **Triage** - assess severity and impact
2. **Rollback** to last known good state if possible
3. **Isolate** the problem component
4. **Communicate** status to stakeholders
5. **Document** everything for post-mortem

**Priority Order:**
1. Restore basic functionality
2. Identify root cause
3. Implement temporary fix
4. Plan permanent solution
5. Conduct post-mortem

### Data Integrity Issues

**CRITICAL - Follow This Order:**
1. **STOP** all write operations immediately
2. **Backup** current state before any changes
3. **Assess** scope of data corruption
4. **Plan** recovery strategy carefully
5. **Test** recovery on non-production first
6. **Verify** data integrity after recovery
7. **Document** incident and prevention measures

---

> **PRINCIPLE:**  
> *"A problem well-defined is half-solved."*  
> Understand completely. Fix precisely. Document thoroughly. Prevent systematically.

---

<!-- #directive-4 -->
## 🎨 Directive 4 — UI/UX Design and Optimization

For all designs we create, ensure they are visually **stunning**, **modern**, and **non-cookie-cutter**. Each webpage should feel **uniquely crafted**, polished, and fully capable of serving as a **production-ready** interface. The design must reflect intentionality and taste, avoid generic layouts or uninspired component arrangements.

---

### 🎯 Mission Statement

> **Create beautiful, functional, accessible interfaces that users love to use.**

---

## 🧭 Core Design Principles

### Design Philosophy
- **Creativity First** - Strive for unique, memorable designs
- **User-Centric** - Every design decision serves user needs
- **Intentional** - Every element has a purpose
- **Production-Ready** - Polished and professional quality
- **Accessible** - Usable by everyone, regardless of ability

### Quality Standards
- **Visual Excellence** - Stunning, modern aesthetics
- **Functional Integrity** - Beautiful AND functional
- **Consistency** - Cohesive design language throughout
- **Performance** - Fast, smooth, responsive
- **Maintainability** - Clean, reusable components

---

## 🛠️ Technology Stack

### Default Template Support
- **JSX syntax** - React component structure
- **Tailwind CSS v4** - Utility-first styling with CSS-first configuration (`@theme` in CSS replaces `tailwind.config.js`)
- **React 19 hooks** - Modern state management
- **Lucide React** - Icon library

### Recommended Additions
- **Framer Motion** - Smooth animations
- **React Hook Form + Zod** - Form handling with type-safe validation
- **Radix UI / Base UI** - Accessible unstyled primitives
- **View Transitions API** - Native page transitions

---

## 📐 Design Requirements

### 1. Responsive Design (Required)

**Mobile-First Approach:**
- Design for mobile screens first (320px+)
- Scale up to tablet (768px+)
- Optimize for desktop (1024px+)
- Support large screens (1440px+)

**Breakpoint Standards:**
```css
/* Tailwind breakpoints */
sm: 640px   /* Small devices */
md: 768px   /* Tablets */
lg: 1024px  /* Laptops */
xl: 1280px  /* Desktops */
2xl: 1536px /* Large screens */
```

**Container Queries (Prefer Over Media Queries for Components):**
```css
/* Component-level responsive design */
.card {
  container-type: inline-size;
}

@container (min-width: 400px) {
  .card-title {
    font-size: 1.5rem;
  }
}
```

Container queries allow components to respond to their parent container size rather than the viewport. Use for reusable components that appear in different layout contexts.

**Dynamic Viewport Units:**
```css
/* Use dvh instead of vh for mobile-safe full-height layouts */
.hero {
  height: 100dvh; /* Accounts for mobile browser UI */
}
```

**Testing Checklist:**
- [ ] Mobile (375x667) - iPhone SE
- [ ] Tablet (768x1024) - iPad
- [ ] Laptop (1366x768) - Common laptop
- [ ] Desktop (1920x1080) - Full HD
- [ ] No horizontal scroll at any breakpoint
- [ ] Touch targets minimum 44x44px on mobile
- [ ] Container queries tested in different parent sizes

### 2. Accessibility (WCAG 2.2 AA Required)

WCAG 2.2 (W3C Recommendation, October 2023) is the current standard. It adds 9 new success criteria over WCAG 2.1, with 4 at AA level. Key additions below.

**Semantic HTML:**
- Use proper heading hierarchy (h1 → h2 → h3)
- Use semantic elements (nav, main, article, section, footer)
- Use button for actions, a for navigation
- Use form elements with proper labels

**Keyboard Navigation:**
- All interactive elements keyboard accessible
- Logical tab order
- Visible focus indicators
- Skip to main content link
- Escape key closes modals/dropdowns

**Focus Management (NEW in WCAG 2.2):**
- **2.4.11 Focus Not Obscured (AA)**: When an element receives keyboard focus, it must not be entirely hidden by sticky headers, footers, or overlays
- Ensure focused elements are at least partially visible at all times
- Test with sticky/fixed positioned elements

**Color & Contrast:**
- Text contrast ratio ≥ 4.5:1 (normal text)
- Text contrast ratio ≥ 3:1 (large text 18pt+)
- Don't rely on color alone for information
- Support dark mode where applicable

**Target Size (NEW in WCAG 2.2):**
- **2.5.8 Target Size Minimum (AA)**: Interactive targets must be at least 24x24 CSS pixels, or have sufficient spacing
- Exception: inline text links, browser-default controls
- Touch targets on mobile should still aim for 44x44px minimum

**Dragging Movements (NEW in WCAG 2.2):**
- **2.5.7 Dragging Movements (AA)**: Any functionality using dragging must have a non-dragging alternative
- Drag-and-drop must offer click/tap alternative (e.g., move up/down buttons)

**Authentication (NEW in WCAG 2.2):**
- **3.3.8 Accessible Authentication (AA)**: Don't require cognitive function tests (memorizing passwords, solving puzzles) as the sole authentication method
- Support password managers, passkeys, or copy-paste for authentication
- CAPTCHAs must have accessible alternatives

**Input Assistance (NEW in WCAG 2.2):**
- **3.3.7 Redundant Entry (A)**: Don't ask users to re-enter information they've already provided in the same process
- Auto-populate previously entered data or allow selection from prior entries
- **3.2.6 Consistent Help (A)**: Help mechanisms (chat, phone, FAQ) must appear in the same relative order across pages

**Screen Reader Support:**
- Meaningful alt text for images
- ARIA labels for icon buttons
- ARIA live regions for dynamic content
- Proper form error announcements

**Accessibility Checklist:**
- [ ] Semantic HTML structure
- [ ] Keyboard navigation works
- [ ] Focus indicators visible and not obscured
- [ ] Color contrast meets standards
- [ ] Alt text for all images
- [ ] ARIA labels where needed
- [ ] Screen reader tested
- [ ] Target sizes meet 24x24px minimum
- [ ] Drag alternatives provided
- [ ] Authentication doesn't require cognitive tests
- [ ] No redundant data entry required
- [ ] Help mechanisms consistently placed

### 3. Modern CSS (2026 Standards)

**Native CSS Nesting (No Preprocessor Required):**
```css
.card {
  padding: 1rem;

  & h2 {
    font-size: 1.375rem;
  }

  &:hover {
    box-shadow: 0 4px 12px rgb(0 0 0 / 0.1);
  }
}
```

**:has() Parent Selector:**
```css
/* Style parent based on child state */
.form:has(input:invalid) {
  border-color: var(--color-error);
}

/* Card with image gets different layout */
.card:has(img) {
  grid-template-rows: auto 1fr;
}
```

**View Transitions API:**
```css
/* Smooth page/route transitions */
::view-transition-old(root),
::view-transition-new(root) {
  animation-duration: 0.3s;
}

/* Named transitions for specific elements */
.hero-image {
  view-transition-name: hero;
}
```
Supported in Chrome, Edge, Safari. Firefox 144+. Use for SPA route transitions and MPA cross-page transitions.

**Subgrid:**
```css
.parent {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
}

.child {
  display: grid;
  grid-template-columns: subgrid;
  grid-column: span 3;
}
```
Allows nested grids to align with parent grid tracks.

**@scope (Component Isolation):**
```css
@scope (.card) {
  h2 { color: var(--card-heading); }
  p { color: var(--card-text); }
}
```
Scoped styling without heavy class naming strategies like BEM.

**Cascade Layers (@layer):**
```css
@layer base, components, utilities;

@layer base {
  * { box-sizing: border-box; }
}

@layer components {
  .btn { padding: 0.5rem 1rem; }
}

@layer utilities {
  .text-center { text-align: center; }
}
```
Controls CSS priority without specificity wars. Essential for large projects and design system architecture.

**Color Level 5:**
```css
.button {
  background: color-mix(in srgb, var(--primary) 80%, white);
}
```
Modern color functions including `color-mix()`, `lab()`, `lch()`, `oklch()` for precise color manipulation.

### 4. Visual Design Standards

**Typography:**
- Clear hierarchy (size, weight, spacing)
- Readable font sizes (16px minimum for body)
- Appropriate line height (1.5-1.8 for body text)
- Limited font families (2-3 maximum)

**Color Palette:**
- Primary color (brand identity)
- Secondary color (accents)
- Neutral colors (backgrounds, text)
- Semantic colors (success, warning, error, info)
- Consistent color usage throughout
- Use CSS custom properties for theming

**Spacing & Layout:**
- Consistent spacing scale (4px, 8px, 16px, 24px, 32px, 48px, 64px)
- Adequate whitespace (don't cram elements)
- Visual rhythm and balance
- Grid-based layouts (CSS Grid + Flexbox)

**Iconography:**
- Use **Lucide React icons** exclusively
- Consistent icon size and style
- Icons support the content, not distract
- Meaningful icons with text labels when needed

### 5. Component Design

**Reusability:**
- Build modular, reusable components
- Single responsibility principle
- Composable components
- Prop-driven customization

**Component Standards:**
```typescript
interface ComponentProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
}
```

**Component Checklist:**
- [ ] TypeScript types defined
- [ ] Props documented
- [ ] Default props set
- [ ] Responsive behavior
- [ ] Accessible markup
- [ ] Loading states
- [ ] Error states
- [ ] Empty states

### 6. Interactive Elements

**Buttons:**
- Clear visual hierarchy (primary, secondary, tertiary)
- Hover, active, focus, disabled states
- Loading state with spinner
- Appropriate size for touch targets (minimum 24x24px, prefer 44x44px on mobile)
- Descriptive text (not just "Click here")

**Forms:**
- Clear labels for all inputs
- Inline validation with helpful messages
- Error states clearly visible
- Success feedback
- Disabled state during submission
- Keyboard accessible
- No redundant entry (WCAG 2.2)

**Navigation:**
- Clear current page indicator
- Logical menu structure
- Mobile-friendly (hamburger menu if needed)
- Breadcrumbs for deep navigation
- Search functionality where appropriate
- Consistent help placement (WCAG 2.2)

**Feedback:**
- Loading indicators for async operations
- Success/error messages
- Toast notifications for non-blocking feedback
- Progress indicators for multi-step processes

---

## 🎨 Design Workflow

### Step 1: Understand Requirements
- Review `Docs/requirements.md` for user needs
- Review `Docs/design.md` for technical constraints
- Identify key user flows
- Define success criteria

### Step 2: Plan Component Structure
- Identify reusable components
- Define component hierarchy
- Plan state management
- Consider data flow

### Step 3: Design & Implement
- Start with mobile layout
- Build reusable components first
- Implement responsive breakpoints + container queries
- Add interactive states
- Implement accessibility features

### Step 4: Polish & Optimize
- Add animations and transitions (View Transitions API where appropriate)
- Optimize performance
- Test across devices
- Refine spacing and alignment
- Review color contrast

### Step 5: Verify Quality
- [ ] Responsive design tested
- [ ] Accessibility audit passed (WCAG 2.2 AA)
- [ ] Cross-browser tested
- [ ] Performance acceptable
- [ ] User flows intuitive
- [ ] Documentation updated

---

## ✅ Quality Checklist

### Before Marking Complete

**Visual Quality:**
- [ ] Design is unique and creative
- [ ] Consistent design language
- [ ] Professional polish
- [ ] No generic templates
- [ ] Intentional design decisions

**Functionality:**
- [ ] All interactive elements work
- [ ] Forms submit correctly
- [ ] Navigation functions properly
- [ ] No broken links or buttons
- [ ] Loading states implemented

**Responsiveness:**
- [ ] Mobile-first design
- [ ] All breakpoints tested
- [ ] Container queries for reusable components
- [ ] No horizontal scroll
- [ ] Touch targets adequate (24x24px minimum, 44x44px preferred)
- [ ] Images responsive

**Accessibility:**
- [ ] WCAG 2.2 AA compliant
- [ ] Keyboard navigation works
- [ ] Focus not obscured by sticky elements
- [ ] Screen reader compatible
- [ ] Color contrast sufficient
- [ ] Semantic HTML used
- [ ] Drag alternatives provided
- [ ] Authentication accessible

**Performance:**
- [ ] Fast initial load
- [ ] Smooth animations (respect prefers-reduced-motion)
- [ ] No layout shift
- [ ] Optimized images (WebP, AVIF)
- [ ] Minimal bundle size

**Code Quality:**
- [ ] Reusable components
- [ ] TypeScript types defined
- [ ] Clean, maintainable code
- [ ] Proper documentation
- [ ] No console errors

---

## 🚫 Design Anti-Patterns

### Avoid These Mistakes

**Visual:**
- ❌ Generic, cookie-cutter layouts
- ❌ Inconsistent spacing
- ❌ Poor color contrast
- ❌ Too many font families
- ❌ Cluttered interfaces

**Functional:**
- ❌ Non-functional decorative buttons
- ❌ Unclear navigation
- ❌ Missing feedback on actions
- ❌ Inaccessible forms
- ❌ Broken responsive design
- ❌ Drag-only interactions without alternatives

**Technical:**
- ❌ Inline styles everywhere
- ❌ Non-reusable components
- ❌ Missing TypeScript types
- ❌ Hardcoded values
- ❌ Poor component structure
- ❌ Using only media queries when container queries are more appropriate

---

## 💡 Best Practices

### Animation & Motion
- Use subtle, purposeful animations
- Respect `prefers-reduced-motion` media query
- Keep animations under 300ms for UI feedback
- Use easing functions (ease-in-out)
- Animate `transform` and `opacity` (GPU-accelerated, performant)
- Use View Transitions API for route/page transitions
- Use CSS `@starting-style` for entry animations (defines initial styles before transition-in)

### Performance Optimization
- Lazy load images and components
- Use proper image formats (WebP, AVIF with fallbacks)
- Minimize bundle size with code splitting
- Code splitting for routes (dynamic imports)
- Optimize re-renders (React Compiler handles this automatically, stop writing manual `useMemo`/`useCallback`)
- Use `content-visibility: auto` for off-screen content

### User Experience
- Provide immediate feedback
- Show loading states (skeleton screens preferred over spinners)
- Handle errors gracefully
- Guide users through flows
- Make actions reversible when possible

### Maintainability
- Document component usage
- Use consistent naming conventions
- Keep components small and focused
- Extract repeated patterns
- Write self-documenting code
- Use CSS custom properties for design tokens

---

## 📚 Documentation Requirements

### Component Documentation
Each component should include:
- Purpose and use cases
- Props and their types
- Usage examples
- Accessibility notes
- Known limitations

### Design System Documentation
Maintain in `Docs/Frontend.md`:
- Color palette with hex codes and CSS custom properties
- Typography scale
- Spacing system
- Component library
- Design patterns
- Accessibility guidelines (WCAG 2.2 AA)

---

> **PRINCIPLE:**  
> *"Design is not just what it looks like and feels like. Design is how it works."*  
> — Steve Jobs  
> Create with intention. Build with purpose. Design for everyone.

---

## 🔍 Code Review Protocol

When reviewing code (own or others'), follow this systematic approach.

### Review Methodology

**Review Order** (Check in this sequence):
1. **Security**: Credentials, injection vulnerabilities, auth issues
2. **Correctness**: Does it do what it claims?
3. **Edge Cases**: Null handling, empty states, boundaries
4. **Performance**: Obvious inefficiencies, N+1 queries, memory leaks
5. **Maintainability**: Readability, naming, structure
6. **Style**: Consistency with codebase conventions

### Severity Classification

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| 🔴 Blocker | Security issue, data loss risk, broken functionality | Must fix before merge |
| 🟠 Major | Bug, significant performance issue, missing error handling | Should fix before merge |
| 🟡 Minor | Code smell, suboptimal approach, minor inefficiency | Fix or acknowledge |
| 🔵 Suggestion | Style preference, alternative approach, nice-to-have | Optional |

### Feedback Delivery

**Constructive Feedback Pattern**:
```
[Severity] [Category]: [Observation]
Why: [Reason this matters]
Suggestion: [Specific improvement]
```

**Feedback Anti-Patterns**:
- ❌ "This is wrong" (no explanation)
- ❌ "I would do it differently" (no reason)
- ❌ Nitpicking style while ignoring bugs
- ❌ Rewriting code in comments

**Feedback Best Practices**:
- ✅ Be specific about what and why
- ✅ Offer solutions, not just problems
- ✅ Acknowledge good patterns too
- ✅ Prioritize feedback by severity
- ✅ Ask questions when intent unclear

### Self-Review Before Submission

Before requesting review:
1. Run Biome and fix issues
2. Run tests and verify passing
3. Review own diff line by line
4. Check for debug code (console.log, etc.)
5. Verify documentation updated

---

## 📊 Quick Reference Summary

### Directive 1: Documentation Checklist
- [ ] requirements.md - What to build
- [ ] design.md - How to build it
- [ ] tasks.md - Implementation roadmap
- [ ] Schemas.md - Data structures
- [ ] API_Documentation.md - API contracts
- [ ] Backend.md - Backend logic
- [ ] Frontend.md - UI architecture
- [ ] Techstack.md - Technology decisions (LAST)
- [ ] Marketing_Plan.md - Go-to-market
- [ ] Changelog.md - Version history (continuous)
- [ ] CHATLOG.md - Conversation history (continuous)
- [ ] Lessons_Learned.md - Knowledge capture (continuous)
- [ ] Enhancements.md - Future improvements (continuous)

### Directive 2: Development Standards
**Toolchain:**
- Build: Vite 6+ (Rolldown bundler) or Next.js 16 (Turbopack)
- Full-stack: Next.js 16 / TanStack Start (RSC, Server Actions)
- SPA: Vite 6+ (client-only)
- Lint/Format: Biome (replaces ESLint + Prettier)
- Language: TypeScript 6+ (strict by default, target es2025)
- Framework: React 19 (Server Components, Actions, React Compiler)
- Client State: Zustand
- Server State: TanStack Query v5
- Backend API: Server Actions / Hono / tRPC
- ORM: Drizzle (default) or Prisma
- Validation: Zod (default) or Valibot
- Testing: Vitest + Testing Library + Playwright + MSW
- Package Manager: pnpm
- Runtime: Node.js 22 LTS
- Date/Time: Temporal API (ES2026)

**Before Starting:**
- Review Prime Directive
- Review last 3-5 decisions
- Read relevant docs
- Verify requirements
- Run Pre-Development Compatibility Check

**During Development:**
- Consult documentation first
- Ask user for consequential decisions
- Build real functionality only
- Test each component
- Verify at runtime

**After Completion:**
- Clean up unused code
- Update documentation
- Run Biome checks
- Verify no errors

### Directive 3: Troubleshooting Steps
1. **Stop & Assess** - Gather evidence, don't guess
2. **Collect Evidence** - Logs, errors, recent changes
3. **Isolate Systematically** - Debug in order
4. **Test Hypotheses** - One variable at a time
5. **Implement Fix** - Least-destructive method
6. **Verify Resolution** - Test multiple scenarios

### Directive 4: Design Requirements
- ✅ Responsive (mobile-first + container queries)
- ✅ Accessible (WCAG 2.2 AA)
- ✅ Beautiful (unique, intentional)
- ✅ Functional (works end-to-end)
- ✅ Performant (fast, smooth)
- ✅ Modern CSS (nesting, :has(), @layer, View Transitions)
- ✅ Documented (component docs)

---

## 🎓 Key Principles Across All Directives

### Quality First
- Never submit incomplete or broken code
- Verify everything at runtime
- Test before marking complete
- Document as you go

### User-Centric
- Every feature solves a user problem
- Accessibility is mandatory (WCAG 2.2 AA)
- Clear, honest UX
- Intuitive user flows

### Security-Conscious
- Never hardcode credentials
- Validate all inputs
- Principle of least privilege
- Keep dependencies updated

### Communication
- Ask when unclear
- Present options with recommendations
- Document decisions
- Update stakeholders

### Continuous Improvement
- Learn from each task
- Document lessons learned
- Prevent recurring issues
- Share knowledge

---

## 🚀 Getting Started

### For New Projects
1. Start with **Directive 1** - Create all documentation
2. Review and get user approval
3. Move to **Directive 2** - Begin development
4. Use **Directive 3** when issues arise
5. Follow **Directive 4** for all UI work

### For Existing Projects
1. Review existing documentation
2. Identify gaps and update docs
3. Follow relevant directive for current task
4. Maintain documentation continuously

### For Troubleshooting
1. Jump to **Directive 3**
2. Follow 6-step workflow
3. Document the issue and resolution
4. Update relevant docs

---

<!-- #maintenance -->
## 📝 Document Maintenance

**This Prime Directive should be:**
- Reviewed at project start
- Referenced during development
- Updated when processes improve
- Shared with team members

**Version History:**
- v1.0 - Initial comprehensive directive
- v2.0 - TOC-Dynamic-Loading, expanded all directives
- v3.0 - Modernized toolchain (Vite 6, Biome, TS 6, React 19, React Compiler), WCAG 2.2 AA, modern CSS (container queries, :has(), nesting, View Transitions, subgrid, @scope, @layer), Zustand + TanStack Query state management, Vitest testing stack, backend/API layer (Server Actions, Hono, tRPC), ORM (Drizzle/Prisma), ES2026 Temporal API, Node.js 22 LTS, security headers, pnpm + Turborepo, framework decision tree (Next.js 16 / TanStack Start / Vite SPA)

---

**Remember:** These directives exist to ensure quality, consistency, and success. Follow them, and you'll build better software faster.