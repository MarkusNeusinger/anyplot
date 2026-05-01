# Tactical Agentic Coding Audit

> Team-based audit of agentic readiness using the TAC (Tactical Agentic Coding) framework. Spawns specialist Opus agents that analyze the 12 TAC leverage points in parallel. The lead synthesizes findings into a prioritized action plan scored by agentic KPI impact.

## Context

@CLAUDE.md
@pyproject.toml

## Instructions

You are the **agentic-lead**. Your job is to coordinate a team of specialist auditors and synthesize their findings into a single, deduplicated, prioritized Tactical Agentic Coding report.

### The 12 TAC Leverage Points

**In-Agent Leverage (Core Four — points 1-4):**
1. **Context** — Minimum context required to solve a problem, avoiding context pollution and confusion
2. **Model** — Different tasks require different compute levels; routing between base and heavy models
3. **Prompt** — Version-controlled, isolated, reusable prompts as first-class assets
4. **Tools** — Custom MCP servers, scripts, and executable capabilities for agent action

**Through-Agent Leverage (Environment — points 5-8):**
5. **Standard Out** — Clear verbose logs and error traces that blind agents can read to self-correct
6. **Types** — Strict types creating traceable information flow across the codebase
7. **Documentation** — Agent-specific docs with conditional routing (read X only when doing Y)
8. **Architecture** — Consistent, modular codebase solving the Agent Navigation Problem

**Through-Agent Leverage (Workflow — points 9-12):**
9. **Tests** — Automated feedback loops (linters, unit tests, E2E) enabling closed-loop self-validation
10. **Plans (Specs)** — Large tasks planned via Markdown specs before implementation; plans are scaled prompts
11. **Templates** — Meta-prompts solving problem classes (chores, bugs, features) rather than one-off issues
12. **ADWs** — Scripts chaining deterministic code with non-deterministic agent prompts for SDLC automation

### Agentic KPIs

Each finding is scored against four agentic KPIs:
- **Size** — Can the agent handle larger, more complex tasks?
- **Attempts** — Does the agent need fewer retries to get it right?
- **Streak** — Can the agent sustain longer runs of correct work without human intervention?
- **Presence** — Does the agent require less human oversight and hand-holding?

---

### Phase 1: Setup

1. **Parse scope from arguments:**
   - `$ARGUMENTS` can be: empty/`all` (all 3 auditors), `core`, `environment`/`env`, `workflow`, or a specific leverage point by number (1-12) or name
   - If a specific leverage point is given, determine which auditor covers it and only spawn that auditor

2. **Quick structural scan** (these are the ONLY Bash commands you run):
   ```bash
   echo "=== Agentic Infrastructure ===" && ls -d .claude/ agentic/ prompts/ .github/workflows/ tests/ docs/ 2>/dev/null
   ```
   Record which agentic infrastructure directories exist for the report header.

3. **Build a new agent team:** Create an `agentic-audit` team with the following specialists (based on active scope):
   - `core-auditor` (general-purpose, opus) — Leverage Points 1-4: Context, Model, Prompt, Tools
   - `environment-auditor` (general-purpose, opus) — Leverage Points 5-8: Stdout, Types, Docs, Architecture
   - `workflow-auditor` (general-purpose, opus) — Leverage Points 9-12: Tests, Plans, Templates, ADWs

   Create one task per active auditor, spawn them in parallel, and assign tasks.

### Scope Table

| $ARGUMENTS | Active Auditors |
|------------|----------------|
| _(empty/all)_ | core-auditor, environment-auditor, workflow-auditor |
| `core` | core-auditor only (points 1-4) |
| `environment` or `env` | environment-auditor only (points 5-8) |
| `workflow` | workflow-auditor only (points 9-12) |
| `1` or `context` | core-auditor (point 1 only) |
| `2` or `model` | core-auditor (point 2 only) |
| `3` or `prompt` or `prompts` | core-auditor (point 3 only) |
| `4` or `tools` | core-auditor (point 4 only) |
| `5` or `stdout` | environment-auditor (point 5 only) |
| `6` or `types` | environment-auditor (point 6 only) |
| `7` or `docs` or `documentation` | environment-auditor (point 7 only) |
| `8` or `architecture` or `arch` | environment-auditor (point 8 only) |
| `9` or `tests` | workflow-auditor (point 9 only) |
| `10` or `plans` or `specs` | workflow-auditor (point 10 only) |
| `11` or `templates` | workflow-auditor (point 11 only) |
| `12` or `adws` or `workflows` | workflow-auditor (point 12 only) |

When routing to a single leverage point, include the point number in the task description so the auditor focuses on that point only.

### Phase 2: Parallel Analysis

Each specialist receives a focused prompt (see below). They:
- Use **Serena tools** (`mcp__serena__get_symbols_overview`, `mcp__serena__find_symbol`, `search_for_pattern`, `list_dir`, `find_file`, `mcp__serena__find_referencing_symbols`) and **Glob/Grep/Read** for code analysis
- Do **NOT** use Bash for file discovery or code searching — only for `uv run ruff`, `uv run pytest`, or similar shell-native commands
- Send findings to `agentic-lead` via `SendMessage` when done
- Mark their task completed via `TaskUpdate`

### Phase 3: Synthesis (Lead)

After all specialists report back:

1. **Collect** all findings from messages
2. **Deduplicate** — merge identical issues found by different auditors
3. **Cross-validate** — flag any contradictions between auditors
4. **Score each finding:**
   - **Impact Score** (1-10): How much does fixing this improve agentic capability?
   - **KPI Impact**: Which KPIs improve — Size, Attempts, Streak, Presence (can be multiple)
   - **Effort**: S (<30min, 1 file, mechanical), M (1-3h, 2-5 files, local context), L (half day+, 5-15 files, design decisions), XL (multi-day, 15+ files, needs own plan)
5. **Categorize into action groups:**
   - **Quick Wins** (Impact >= 6, Effort S or M) — high leverage, low effort
   - **Strategic Investments** (Impact >= 6, Effort L or XL) — high leverage, high effort
   - **Backlog** (Impact < 6) — nice-to-have improvements
6. **Output** the report in the format below
7. **Cleanup**: Send `shutdown_request` to all auditors, then `TeamDelete`

### Output Format

```markdown
# TAC Audit Report

**Date:** {date} | **Scope:** {scope} | **Infrastructure:** {which agentic dirs exist}

## Executive Summary
{3-5 sentences: overall agentic readiness, strongest areas, biggest gaps, maturity level}

**Agentic Maturity Level:** {1-5}/5
- 1: Manual — no agentic infrastructure
- 2: Assisted — basic prompts and docs exist
- 3: Structured — versioned prompts, types, tests, some automation
- 4: Orchestrated — composable workflows, specs, templates, MCP tools
- 5: Autonomous — full ADW pipeline, self-healing, minimal human presence

## Leverage Point Scores

| # | Leverage Point | Score | KPI Impact | Top Finding |
|---|---------------|-------|------------|-------------|
| 1 | Context | {1-10} | {Size,Streak} | {one-line} |
| 2 | Model | {1-10} | {Attempts,Size} | {one-line} |
| ... | ... | ... | ... | ... |
| 12 | ADWs | {1-10} | {Presence,Size} | {one-line} |

**Average Score:** {x.x}/10

## Quick Wins (Impact >= 6, Effort S/M)
| # | Leverage Point | Finding | Impact | KPI | Effort | Files |
|---|---------------|---------|--------|-----|--------|-------|
| 1 | {name} | {description} | {1-10} | {KPIs} | S/M | `{files}` |

## Strategic Investments (Impact >= 6, Effort L/XL)
| # | Leverage Point | Finding | Impact | KPI | Effort | Files |
|---|---------------|---------|--------|-----|--------|-------|

## Backlog (Impact < 6)
| # | Leverage Point | Finding | Impact | KPI | Effort | Files |
|---|---------------|---------|--------|-----|--------|-------|

## Positive Patterns
{Good agentic practices already in place — preserve these}
- {pattern}

## Statistics
- Total findings: {N} | Quick Wins: {n}, Strategic: {n}, Backlog: {n}
- By cluster: Core (1-4): {n}, Environment (5-8): {n}, Workflow (9-12): {n}
```

### Exclusions (apply to ALL auditors)

Do NOT flag:
- Plot implementations in `plots/` (AI-generated, different style rules)
- Generated files or lock files (`uv.lock`, `yarn.lock`, etc.)
- Third-party code or `node_modules/`
- Issues already covered by pyproject.toml exclusions
- The absence of features the project explicitly chose not to implement
- Personal preference or style opinions — only flag things with measurable agentic impact

---

## Specialist Prompts

### core-auditor

You are the **core-auditor** on the agentic-audit team. Analyze leverage points 1-4: Context, Model, Prompt, and Tools.

**Your scope covers "In-Agent Leverage" — what agents can directly see and use.**

#### Leverage Point 1: Context

**Core Question:** Can an agent see all necessary files and architecture without being overwhelmed?

**Audit Criteria:**
- Are there mechanisms to limit what the agent sees (conditional docs, scoped context)?
- Are there massive files (>1000 lines) that would bloat the context window?
- Is there a `CLAUDE.md` or equivalent providing the minimum viable context?
- Is context scoped per task type (not one giant document for everything)?

**Where to look:**
- `CLAUDE.md` — primary agent-facing context
- `.claude/` — tool configuration, settings
- `agentic/commands/context.md` — conditional documentation routing
- `agentic/docs/` — project guides
- `agentic/context/` — feature-specific context documents
- `README.md`, `.github/copilot-instructions.md`
- Any file over 1000 lines (bloat risk)

**What to check:**
- Does CLAUDE.md stay focused or try to cover everything?
- Is there a conditional documentation system ("If modifying UI, read X")?
- Can an agent understand the project without reading hundreds of files?
- Are there patterns to prevent context window overflow on large tasks?
- Is context split by concern (setup vs. conventions vs. architecture)?

#### Leverage Point 2: Model

**Core Question:** Is the right model size used for the right task?

**Audit Criteria:**
- Are there Information Dense Keywords (IDKs) like `think hard` to activate reasoning?
- Are there routing mechanisms between base models (for chores) and heavy models (for complex features)?
- Is model selection documented or configurable?

**Where to look:**
- `agentic/workflows/` — do orchestrators specify model sizes?
- `agentic/workflows/modules/agent.py` — model defaults and selection
- `agentic/commands/*.md` — do commands specify model requirements?
- `.github/workflows/*.yml` — what models are used in CI?
- Any configuration referencing `claude`, `opus`, `sonnet`, `haiku`, or model names

**What to check:**
- Are expensive models (opus) reserved for complex reasoning tasks?
- Are cheaper models (sonnet/haiku) used for mechanical tasks?
- Is there a model selection strategy or matrix?
- Do workflow orchestrators allow model overrides per phase?

#### Leverage Point 3: Prompt

**Core Question:** Are prompts version-controlled, isolated, and reusable assets?

**Audit Criteria:**
- Is there a dedicated prompts folder (e.g., `.claude/commands/` or `prompts/`)?
- Are prompts isolated files, not inline strings in code or workflows?
- Are prompts parameterized (template variables) for reuse?
- Is there prompt duplication that should be consolidated?

**Where to look:**
- `prompts/` — prompt library
- `prompts/library/` — library-specific prompts
- `prompts/templates/` — template files
- `prompts/workflow-prompts/` — workflow prompts
- `agentic/commands/` — slash command prompts
- `.github/workflows/*.yml` — check for inline prompts (anti-pattern)

**What to check:**
- Are prompts stored as separate versioned files (not inline)?
- Is there a clear naming convention?
- Do prompts have clear structure (role, context, instructions, output format)?
- Are prompt responsibilities well-scoped (single responsibility)?
- Is there duplication across prompts?
- Do prompts reference file paths that could become stale?

#### Leverage Point 4: Tools

**Core Question:** Does the repo give agents executable capabilities via custom tools?

**Audit Criteria:**
- Are there custom MCP servers (e.g., for database access, browser testing)?
- Are there specific scripts built for agents to execute?
- Are common multi-step operations automated as single tool calls?

**Where to look:**
- `api/mcp/` — MCP server implementation
- `.claude/` — MCP server configuration
- `automation/scripts/` — CLI tools
- `scripts/` — standalone scripts
- `core/` — utility functions that could become tools
- `pyproject.toml` — script entry points

**What to check:**
- Is there a custom MCP server? What tools does it expose?
- Are common agent operations wrapped as tools or scripts?
- Could any repetitive multi-step operations become a single tool?
- Do scripts use proper CLI interfaces (Click, argparse) for agent usage?
- Are tools documented (parameters, return values)?

**How to work:**
1. Use `list_dir` to explore directories listed above
2. Use `mcp__serena__get_symbols_overview` on key files
3. Use `search_for_pattern` for patterns like `CLAUDE.md`, model references, `mcp`, `prompt`
4. Use Read to examine prompt files and configuration
5. Use `mcp__serena__find_symbol` with `depth=1` to inspect MCP tools and CLI commands
6. Use Grep to count lines in large files: check for >1000-line files as context bloat risk
7. **Do NOT use Bash** for `find`, `ls`, `grep`, `cat` — use Serena/Glob/Grep/Read tools instead
8. You MAY use Bash for: `uv run python -c "..."` to inspect tool registrations

**Report format:** Send findings to `agentic-lead` via `SendMessage`. Structure each finding as:
```
LEVERAGE_POINT: {number}. {name}
CURRENT_STATE: {what exists today — be specific about files and patterns}
GAP: {what's missing or suboptimal}
OPTIMIZATION: {concrete action to take}
IMPACT: {1-10}
KPI: {which KPIs improve: Size/Attempts/Streak/Presence}
EFFORT: {S/M/L/XL}
FILES: {relevant file paths}
```

If a leverage point is already well-implemented, report it as a positive pattern:
```
LEVERAGE_POINT: {number}. {name}
POSITIVE: {what's working well and should be preserved}
FILES: {relevant file paths}
```

### environment-auditor

You are the **environment-auditor** on the agentic-audit team. Analyze leverage points 5-8: Standard Out, Types, Documentation, and Architecture.

**Your scope covers "Through-Agent Leverage (Environment)" — what the codebase provides passively to help agents work correctly.**

#### Leverage Point 5: Standard Out

**Core Question:** Can a blind agent read terminal output to self-correct?

**Audit Criteria:**
- Are errors swallowed or verbosely printed to stdout?
- Does the application output clear success/error states?
- Can an agent reading only terminal output understand what went wrong and how to fix it?

**Where to look:**
- `api/main.py` — logging configuration
- `api/exceptions.py` — custom exceptions, error formatting
- `api/` — error handling patterns across routers
- `core/` — utility error handling
- `agentic/workflows/modules/agent.py` — agent execution logging
- `agentic/workflows/*.py` — workflow stderr/stdout patterns
- `.github/workflows/*.yml` — CI output verbosity

**What to check:**
- Do scripts output clear error messages when they fail?
- Are there structured logging patterns (not just print statements)?
- Do errors include enough context for self-correction (file path, expected vs. actual)?
- Is stderr used for diagnostics and stdout for data (especially in piped workflows)?
- Are there silent failures an agent would miss?
- Do failing tests produce clear, actionable output?
- Do CI workflows capture and surface useful error output?

#### Leverage Point 6: Types

**Core Question:** Do strict types create a traceable flow of information?

**Audit Criteria:**
- Are strict types, classes, or interfaces heavily used?
- Are domain models clearly defined so an agent can search for a type and understand its lifecycle?
- Can an agent find a type definition and trace it through the entire codebase?

**Where to look:**
- `core/database/models.py` — ORM models
- `core/database/types.py` — custom type decorators
- `api/schemas.py` — API request/response schemas
- `api/dependencies.py` — FastAPI dependency injection
- `app/src/types/` — TypeScript type definitions
- `app/tsconfig.json` — TypeScript strict mode
- `agentic/workflows/modules/state.py` — workflow state types
- `agentic/workflows/modules/agent.py` — agent data types
- `pyproject.toml` — type checking configuration (mypy)

**What to check:**
- Are Python type hints used consistently across `api/` and `core/`?
- Are Pydantic models used for data validation at boundaries?
- Is TypeScript in strict mode? Are there `any` type escapes?
- Are function signatures fully typed (parameters AND return types)?
- Do workflow scripts use typed data structures (not raw dicts)?
- Is there a type checking step in CI?
- Are there untyped `Any`, `dict`, `list` without parameters?

#### Leverage Point 7: Documentation

**Core Question:** Is there agent-specific documentation with conditional routing?

**Audit Criteria:**
- Is there an `ai_docs/` or equivalent folder with agent-specific docs?
- Is there "Conditional Documentation" that tells agents when to read what?
- Is documentation structured for machines (not just humans)?

**Where to look:**
- `agentic/docs/` — agent-facing documentation
- `agentic/commands/context.md` — conditional documentation router
- `agentic/context/` — feature-specific context documents
- `docs/` — general documentation
- `docs/concepts/`, `docs/reference/`, `docs/workflows/`
- `CLAUDE.md` — primary agent-facing docs
- `.github/copilot-instructions.md`

**What to check:**
- Is there documentation specifically written for agents (not just humans)?
- Does a conditional documentation system exist ("read X when doing Y")?
- Are context documents created for complex features or recent changes?
- Is documentation kept up to date when code changes?
- Are there dead links or stale references?
- Is the project guide comprehensive enough for a new agent to be productive?
- Are there docs for each major subsystem?

#### Leverage Point 8: Architecture

**Core Question:** Is the codebase consistent enough to solve the Agent Navigation Problem?

**Audit Criteria:**
- Are there clear entry points (separated concerns)?
- Do test folders mirror the exact structure of source folders?
- Is the architecture consistent and predictable?

**Where to look:**
- Top-level directory structure
- `api/` — routers, services, dependencies
- `app/src/` — components, hooks, pages, types
- `core/` — shared module organization
- `agentic/` — agentic layer organization
- `tests/` vs. source structure — do they mirror?
- Naming conventions across the codebase

**What to check:**
- Is the directory structure consistent and predictable?
- Can an agent navigate to the right file without searching (clear naming)?
- Are there clear separation of concerns (routers vs. services vs. models)?
- Is the same pattern used for similar things?
- Are there circular dependencies or unexpected coupling?
- Do test paths mirror source paths exactly?
- Are naming conventions consistent (snake_case Python, camelCase TS, kebab-case files)?

**How to work:**
1. Use `list_dir` with `recursive=false` to map top-level and sub-directory structure
2. Use `mcp__serena__get_symbols_overview` on key files to check type annotations
3. Use `search_for_pattern` for anti-patterns (e.g., `Any`, `# type: ignore`, `print(`, `: any`, `console.log`)
4. Use Read to examine config files (`tsconfig.json`, `pyproject.toml` type sections)
5. Use Grep to find logging, error handling, and type annotation patterns
6. Compare `tests/` structure with `api/`, `core/`, `automation/` structure
7. **Do NOT use Bash** for `find`, `ls`, `grep`, `cat` — use Serena/Glob/Grep/Read tools instead
8. You MAY use Bash for: `uv run ruff check api/ core/ --select ANN 2>&1 | tail -20`

**Report format:** Same as core-auditor — send findings to `agentic-lead` via `SendMessage` using the `LEVERAGE_POINT` / `POSITIVE` format.

### workflow-auditor

You are the **workflow-auditor** on the agentic-audit team. Analyze leverage points 9-12: Tests, Plans, Templates, and ADWs.

**Your scope covers "Through-Agent Leverage (Workflow)" — the automated systems enabling agents to validate, plan, and execute work autonomously.**

#### Leverage Point 9: Tests

**Core Question:** Can agents run a single command to self-validate their changes?

**Audit Criteria:**
- Are there automated linters (Ruff, ESLint), unit tests (pytest, vitest), and E2E tests (Playwright)?
- Can an agent run a single command to verify if changes broke anything?
- Do tests form a "closed-loop" feedback system for agent self-correction?

**Where to look:**
- `tests/` — test suite structure
- `tests/unit/`, `tests/integration/`, `tests/e2e/`
- `tests/conftest.py` — shared fixtures
- `pyproject.toml` — pytest and ruff configuration
- `.github/workflows/ci-lint.yml`, `ci-tests.yml` — CI pipeline
- `app/vitest.config.ts` — frontend test config
- `app/eslint.config.js` — frontend linting

**What to check:**
- Can an agent run `uv run pytest` and get clear pass/fail with actionable output?
- Is the test suite fast enough for agent iteration (< 60s for unit tests)?
- Do tests cover the critical paths agents commonly modify?
- Are there test fixtures making it easy to write new tests?
- Is there a linter configured and integrated (`ruff`, `eslint`)?
- Can agents run targeted tests (e.g., `pytest tests/unit/api/`)?
- Are test failure messages clear and actionable?
- Is there a pre-commit hook or CI gate?

#### Leverage Point 10: Plans (Specs)

**Core Question:** Are large tasks planned via Markdown specs before implementation?

**Audit Criteria:**
- Is there a `specs/` or `plans/` directory?
- Do Markdown plans include step-by-step tasks, relevant files, and validation commands?
- Are plans treated as "scaled prompts" — detailed enough for autonomous execution?

**Where to look:**
- `agentic/specs/` — spec/plan files
- `agentic/context/` — context documents
- `plots/*/specification.md` — plot specifications
- `agentic/workflows/plan.py` — planning workflow
- `agentic/workflows/plan_build.py` — plan+build orchestrator
- `agentic/commands/` — commands that reference specs

**What to check:**
- Is there a spec-first workflow for complex features?
- Are specs stored in version control with clear naming?
- Do specs follow a consistent template (problem, solution, files, acceptance criteria)?
- Do specs include enough detail for an agent to implement without ambiguity?
- Are specs linked to issues for traceability?
- Is the spec-to-implementation pipeline automated?
- Do spec templates include validation commands the agent should run after implementation?

#### Leverage Point 11: Templates

**Core Question:** Are there meta-prompts solving problem classes (chores, bugs, features)?

**Audit Criteria:**
- Are there meta-prompts (e.g., `/chore`, `/bug`, `/feature`) that generate plans?
- Do templates encode engineering best practices and guard rails?
- Are templates designed to produce the Markdown plans from Point 10?

**Where to look:**
- `agentic/commands/` — slash command templates (all `.md` files)
- `prompts/templates/` — prompt templates
- `prompts/workflow-prompts/` — workflow-specific prompts
- `prompts/library/` — library-specific prompts
- `.github/ISSUE_TEMPLATE/` — issue templates

**What to check:**
- Are there reusable command templates for common agent tasks (bug, feature, chore, refactor)?
- Do templates encode best practices (conflict checks, quality criteria, guard rails)?
- Are templates parameterized (variables like `$1`, `$ARGUMENTS`)?
- Is there consistency across templates (same structure, same conventions)?
- Do templates produce structured output (Markdown plans, JSON)?
- Are templates documented (what they do, when to use)?
- Is there template duplication that should be consolidated?
- Do templates leverage the team pattern where appropriate?

#### Leverage Point 12: ADWs (Agentic Developer Workflows)

**Core Question:** Are there scripts chaining deterministic code with agentic prompts for SDLC automation?

**Audit Criteria:**
- Is there an `ADWs/` or `workflows/` directory?
- Are there scripts (Python, Bash) that automate SDLC steps (e.g., `plan_build_test.py`)?
- Do workflows use the PETER framework: Prompt input, Trigger, Environment, Review?
- Can workflows run AFK (Away From Keyboard) with minimal human presence?

**Where to look:**
- `agentic/workflows/` — composable workflow scripts
- `agentic/workflows/modules/` — shared workflow modules (agent.py, state.py, orchestrator.py)
- `.github/workflows/` — GitHub Actions (13 workflows)
- `.github/workflows/impl-generate.yml`, `impl-review.yml`, `impl-merge.yml` — implementation pipeline
- `.github/workflows/spec-create.yml` — spec creation
- `automation/scripts/` — automation CLI tools

**What to check:**
- Are there ADW scripts combining deterministic steps (file ops, git) with agentic steps (LLM)?
- Do workflows use state persistence across phases?
- Is there a composable architecture (plan -> build -> test -> review)?
- Do workflows handle errors gracefully (retries, fallbacks)?
- Is the spec-to-implementation pipeline fully automated end-to-end?
- Do CI workflows trigger agentic processing?
- Is there workflow monitoring/observability?
- Are workflow runs logged and auditable?
- Could any manual multi-step processes be automated as ADWs?
- Do workflows run successfully AFK (without human checking in)?

**How to work:**
1. Use `list_dir` to explore `tests/`, `agentic/specs/`, `agentic/workflows/`, `agentic/commands/`, `prompts/`
2. Use `mcp__serena__get_symbols_overview` on workflow scripts and test files
3. Use `mcp__serena__find_symbol` to inspect workflow classes, fixtures, orchestrators
4. Use Read to examine spec files, templates, and workflow configurations
5. Use `search_for_pattern` for patterns like `prompt_claude_code`, `WorkflowState`, `@pytest.fixture`, `$ARGUMENTS`
6. Use Glob to find all test files (`**/*test*.py`, `**/*.test.ts`) and template files
7. **Do NOT use Bash** for `find`, `ls`, `grep`, `cat` — use Serena/Glob/Grep/Read tools instead
8. You MAY use Bash for: `uv run pytest tests/ --co -q 2>&1 | tail -20` or `uv run ruff check . 2>&1 | tail -5`

**Report format:** Same as core-auditor — send findings to `agentic-lead` via `SendMessage` using the `LEVERAGE_POINT` / `POSITIVE` format.
