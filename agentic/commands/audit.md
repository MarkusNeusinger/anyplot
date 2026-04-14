# Code Quality Audit

> Team-based code quality audit for the anyplot repository. Spawns specialized Opus agents that analyze backend, frontend, infrastructure, and quality aspects in parallel. The lead synthesizes findings into a prioritized, effort-rated action plan.

## Context

@CLAUDE.md
@pyproject.toml

## Instructions

You are the **audit-lead**. Your job is to coordinate a team of specialist auditors and synthesize their findings into a single, deduplicated, prioritized report.

### Phase 1: Setup

1. **Parse scope from arguments:**
   - `$ARGUMENTS` can be: empty/`all` (all 4 auditors), `backend`, `frontend`, `infra`, `quality`/`tests`, or a directory path
   - If a directory path is given, determine which auditor(s) are responsible

2. **Run Ruff baseline** (these are the ONLY Bash commands you run):
   ```bash
   uv run ruff check . 2>&1 | tail -5
   ```
   ```bash
   uv run ruff format --check . 2>&1 | tail -5
   ```
   Record the issue count and format status for the report header.

3. **Build a new agent team:** Create an "audit" team with the following specialists (based on active scope):
   - `backend-auditor` (general-purpose, opus) — analyzes `api/`, `core/`, `automation/`
   - `frontend-auditor` (general-purpose, opus) — analyzes `app/src/`
   - `infra-auditor` (general-purpose, opus) — analyzes workflows, prompts, Docker, configs
   - `quality-auditor` (general-purpose, opus) — analyzes tests, docs, commands

   Create one task per active auditor, spawn them in parallel, and assign tasks.

### Scope Table

| $ARGUMENTS | Active Auditors |
|------------|----------------|
| _(empty/all)_ | backend-auditor, frontend-auditor, infra-auditor, quality-auditor |
| `backend` | backend-auditor only |
| `frontend` | frontend-auditor only |
| `infra` | infra-auditor only |
| `quality` or `tests` | quality-auditor only |
| directory path | Lead determines which auditor(s) cover that path |

### Phase 2: Parallel Analysis

Each specialist receives a focused prompt (see below). They:
- Use **Serena tools** (`jet_brains_get_symbols_overview`, `jet_brains_find_symbol`, `search_for_pattern`, `list_dir`, `find_file`, `jet_brains_find_referencing_symbols`) and **Glob/Grep/Read** for code analysis
- Use `think_about_collected_information` after non-trivial research sequences
- Do **NOT** use Bash for file discovery or code searching — only for `uv run ruff`, `uv run pytest`, or similar shell-native commands
- Send findings to `audit-lead` via `SendMessage` when done
- Mark their task completed via `TaskUpdate`

### Phase 3: Synthesis (Lead)

After all specialists report back:

1. **Collect** all findings from messages
2. **Deduplicate** — merge identical issues found by different auditors
3. **Cross-validate** — flag any contradictions between auditors
4. **Rate each finding:**
   - **Importance** (1-5): 5=Critical/bugs/security, 4=High/code smells, 3=Medium/modernization, 2=Low/cosmetic, 1=Positive patterns to keep
   - **Effort**: S (<30min, 1 file, mechanical), M (1-3h, 2-5 files, local context), L (half day+, 5-15 files, design decisions), XL (multi-day, 15+ files, needs own plan)
5. **Sort**: Importance descending, then Effort ascending (quick wins first within each priority)
6. **Output** the report in the format below
7. **Cleanup**: Send `shutdown_request` to all auditors, then `TeamDelete`

### Output Format

```markdown
# Audit Report: anyplot

**Date:** {date} | **Scope:** {scope} | **Baseline:** ruff: {N issues}, format: {status}

## Summary
{2-3 sentences: overall health, key themes}

## Critical (Importance 5)
| # | Finding | Effort | Files | Hint |
|---|---------|--------|-------|------|
| 1 | {description} | S/M/L/XL | `{files}` | {one-line fix hint} |

## High (Importance 4)
| # | Finding | Effort | Files | Hint |
|---|---------|--------|-------|------|

## Medium (Importance 3)
| # | Finding | Effort | Files | Hint |
|---|---------|--------|-------|------|

## Low (Importance 2)
| # | Finding | Effort | Files | Hint |
|---|---------|--------|-------|------|

## Positive Patterns (Importance 1)
- {good patterns to keep}

## Statistics
- Total: {N} | S: {n}, M: {n}, L: {n}, XL: {n}
- Backend: {n}, Frontend: {n}, Infra: {n}, Quality: {n}
```

### Exclusions (apply to ALL auditors)

Do NOT flag:
- Plot implementations in `plots/` (AI-generated, different style rules)
- Generated files or lock files (`uv.lock`, `yarn.lock`, etc.)
- Third-party code or `node_modules/`
- Issues already covered by pyproject.toml exclusions

---

## Specialist Prompts

### backend-auditor

You are the **backend-auditor** on the audit team. Analyze `api/`, `core/`, and `automation/` directories.

**Your scope:**
- **FastAPI patterns**: Router organization, REST conventions, dependency injection, response schemas, async/await correctness
- **Repository pattern**: Implementation in `core/`, data access consistency, query patterns
- **Type safety**: Missing type hints, `Any` overuse, incorrect types, Protocol/ABC usage
- **Code smells**: Dead code, duplication, overly complex functions (high cyclomatic complexity), god classes
- **Error handling**: Consistency, missing error handlers, bare except clauses, error propagation
- **Python modernization**: Old patterns that could use 3.14 features, deprecated APIs
- **Performance**: N+1 queries, unnecessary computations, inefficient patterns, missing caching opportunities
- **Import hygiene**: Unused imports, circular imports, import order

**How to work:**
1. Use `list_dir` to understand directory structure of `api/`, `core/`, `automation/`
2. Use `jet_brains_get_symbols_overview` on key files to understand architecture
3. Use `jet_brains_find_symbol` with `depth=1` to inspect classes and their methods
4. Use `search_for_pattern` to find anti-patterns (e.g. `bare except`, `type: ignore`, `Any`, `TODO`, `FIXME`)
5. Use `jet_brains_find_referencing_symbols` to check if code is actually used
6. Use `think_about_collected_information` after research sequences
7. **Do NOT use Bash** for `find`, `ls`, `grep`, `cat` — use Serena/Glob/Grep/Read tools instead
8. You MAY use Bash for: `uv run ruff check api/ core/ automation/` or `uv run pytest tests/unit -x -q`

**Report format:** Send findings to `audit-lead` via `SendMessage`. Structure as a list:
```
FINDING: {short title}
IMPORTANCE: {1-5}
EFFORT: {S/M/L/XL}
FILES: {comma-separated file paths}
DESCRIPTION: {what's wrong and why it matters}
HINT: {one-line fix suggestion}
```

### frontend-auditor

You are the **frontend-auditor** on the audit team. Analyze the `app/src/` directory.

**Your scope:**
- **Component quality**: Structure, reusability, separation of concerns, prop drilling vs context
- **TypeScript strictness**: `any` usage, missing interfaces, proper generics, type-only imports
- **Hooks**: Custom hook patterns, missing dependency arrays, stale closures, unnecessary re-renders
- **Performance**: Missing `memo`/`useMemo`/`useCallback` where needed, large bundles, unnecessary renders
- **Accessibility**: Missing aria-labels, keyboard navigation, focus management, color contrast
- **MUI 7 patterns**: Correct theme usage, sx prop vs styled, consistent component usage
- **Dead code**: Unused components, unused imports, unreachable code, commented-out code
- **Error handling**: Error boundaries, loading states, empty states, fallbacks
- **Consistency**: Naming conventions, file organization, export patterns

**How to work:**
1. Use `list_dir` to understand `app/src/` structure
2. Use Glob to find all `.tsx` and `.ts` files: `**/*.tsx`, `**/*.ts` in `app/src/`
3. Use `jet_brains_get_symbols_overview` on key components
4. Use Grep to search for anti-patterns (e.g. `: any`, `eslint-disable`, `@ts-ignore`, `console.log`)
5. Use `search_for_pattern` for cross-file patterns
6. Use `think_about_collected_information` after research sequences
7. **Do NOT use Bash** for `find`, `ls`, `grep`, `cat` — use Serena/Glob/Grep/Read tools instead
8. You MAY use Bash for: `cd /home/tirao/pyplots/app && yarn tsc --noEmit 2>&1 | tail -20`

**Report format:** Same as backend-auditor — send findings to `audit-lead` via `SendMessage`.

### infra-auditor

You are the **infra-auditor** on the audit team. Analyze `.github/workflows/`, `prompts/`, Dockerfiles, and configuration files.

**Your scope:**
- **GitHub Workflows**: Consistency, naming, job dependencies, parallelization, secret handling, security (script injection), concurrency settings, reusable workflows vs duplication, trigger conditions, error handling
- **Prompt quality**: Clarity, structure, consistency across prompt files, outdated references, missing edge cases, template completeness, library-specific rules alignment
- **Docker**: Dockerfile best practices, layer optimization, security (running as root), base image freshness
- **Configuration**: `pyproject.toml` consistency, `tsconfig.json` strictness, Vite config, ESLint config, Ruff config
- **Security**: Exposed secrets, insecure permissions, missing pinning of actions, `${{ github.event }}` injection risks
- **Config drift**: Mismatches between workflow configs and actual project structure

**How to work:**
1. Use `list_dir` to find all workflow files, prompt files, Docker files, config files
2. Use `find_file` with masks like `*.yml`, `*.yaml`, `Dockerfile*`, `*.toml`, `*.json`
3. Use Read to examine workflow files (they're YAML, not code — Serena symbols won't help)
4. Use `search_for_pattern` to find patterns across workflows (e.g. inconsistent action versions, missing `concurrency:`)
5. Use Grep to check for security anti-patterns (e.g. `${{ github.event`, `pull_request_target`, insecure permissions)
6. Use `think_about_collected_information` after research sequences
7. **Do NOT use Bash** for `find`, `ls`, `grep`, `cat` — use Serena/Glob/Grep/Read tools instead

**Report format:** Same as backend-auditor — send findings to `audit-lead` via `SendMessage`.

### quality-auditor

You are the **quality-auditor** on the audit team. Analyze `tests/`, `docs/`, `agentic/commands/`, and documentation files.

**Your scope:**
- **Test coverage gaps**: Which modules in `api/`, `core/`, `automation/` lack corresponding tests? Compare `tests/` structure with source structure
- **Test quality**: Assertion quality (not just `assert True`), fixture organization, mock patterns, test naming, parametrize usage
- **Documentation staleness**: Do docs match actual code behavior? Are there broken internal links? Outdated instructions?
- **Cross-references**: Do workflows reference existing files? Are library names consistent across `prompts/`, `core/`, workflows?
- **Command consistency**: Are agentic commands in `agentic/commands/` well-structured, up-to-date, consistent with each other?
- **README quality**: Is the main README accurate and helpful? Does it reflect current project state?
- **CLAUDE.md accuracy**: Does CLAUDE.md match the actual project structure and conventions?

**How to work:**
1. Use `list_dir` to map `tests/` structure and compare with `api/`, `core/`, `automation/` structure
2. Use `jet_brains_get_symbols_overview` on test files to check test method quality
3. Use `search_for_pattern` to find test anti-patterns (e.g. `assert True`, `pass`, empty test bodies)
4. Use Glob to find all `.md` docs files, then Read key ones to check staleness
5. Use Grep to verify cross-references (e.g. file paths mentioned in docs actually exist)
6. Use `think_about_collected_information` after research sequences
7. **Do NOT use Bash** for `find`, `ls`, `grep`, `cat` — use Serena/Glob/Grep/Read tools instead
8. You MAY use Bash for: `uv run pytest tests/ --co -q 2>&1 | tail -20` (list collected tests)

**Report format:** Same as backend-auditor — send findings to `audit-lead` via `SendMessage`.
