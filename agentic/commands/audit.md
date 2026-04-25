# Code Quality Audit

> Team-based code quality audit for the anyplot repository. Spawns up to eight specialized Opus agents (backend, frontend, infra, quality, llm-pipeline, db, security, observability) that analyze the codebase in parallel. Lead cross-validates high-severity findings, synthesizes a prioritized, effort-rated, auto-fix-aware action plan, and persists the report for regression tracking.

## Context

@CLAUDE.md
@pyproject.toml

## Instructions

You are the **audit-lead**. Your job is to coordinate a team of specialist auditors, run a cross-validation pass on high-severity findings, and synthesize a single deduplicated, prioritized, persistable report.

### Phase 1: Setup

1. **Parse scope from `$ARGUMENTS`:**
   - Empty / `all` → spawn all 8 auditors
   - Single keyword → spawn only that auditor (see Scope Table)
   - Directory path → Lead determines which auditor(s) cover that path
   - Optional `since=<git-ref>` (e.g. `since=main`, `since=HEAD~10`) → **Incremental mode**: Lead computes the changed file list once via `git diff --name-only <ref>...HEAD` and passes the relevant subset to each auditor. Auditors must restrict their analysis to those files (plus their direct importers if a quick `mcp__serena__find_referencing_symbols` lookup is cheap). If `since=` is omitted, auditors run a full sweep of their scope.

2. **Run baseline measurements** (these are the ONLY Bash commands the Lead runs in this phase):
   ```bash
   uv run ruff check . 2>&1 | tail -5
   ```
   ```bash
   uv run ruff format --check . 2>&1 | tail -5
   ```
   In `since=` mode, additionally:
   ```bash
   git diff --name-only <ref>...HEAD
   ```
   Record ruff issue count, format status, and (if applicable) the changed-file count for the report header.

3. **Build a new agent team:** Create an "audit" team with the specialists matching the active scope. Each auditor is `general-purpose, opus`:

   | Auditor | Primary Paths |
   |---|---|
   | `backend-auditor` | `api/`, `core/`, `automation/` |
   | `frontend-auditor` | `app/src/` |
   | `infra-auditor` | `.github/workflows/`, `prompts/`, Dockerfiles, top-level configs |
   | `quality-auditor` | `tests/`, `docs/`, `agentic/commands/`, README/CLAUDE.md |
   | `llm-pipeline-auditor` | `core/generators/`, `prompts/`, `core/config.py` (claude_*), `agentic/workflows/`, `.github/workflows/{spec,impl,bulk}-*.yml` |
   | `db-auditor` | `alembic/`, `core/database/`, `alembic.ini` |
   | `security-auditor` | repo-wide (primarily `api/`, `core/config.py`, `agentic/workflows/`, `.github/workflows/`) |
   | `observability-auditor` | `api/analytics.py`, `api/cache.py`, `app/src/analytics/`, `docs/reference/plausible.md` |

   Create one task per active auditor, spawn them in parallel, and assign tasks.

4. **Tool-budget hint** (paste into every auditor prompt): each auditor should keep itself under ~30 read/search tool calls. If they cannot finish within budget, they must report partial findings + a `COVERAGE: partial` flag rather than running unbounded.

### Scope Table

| `$ARGUMENTS` | Active Auditors |
|------------|----------------|
| _(empty / `all`)_ | backend, frontend, infra, quality, llm-pipeline, db, security, observability |
| `backend` | backend-auditor only |
| `frontend` | frontend-auditor only |
| `infra` | infra-auditor only |
| `quality` or `tests` | quality-auditor only |
| `llm` or `pipeline` | llm-pipeline-auditor only |
| `db` or `database` | db-auditor only |
| `security` or `sec` | security-auditor only |
| `observability` or `obs` | observability-auditor only |
| `since=<ref>` (alone or combined) | Incremental mode for the selected scope |
| directory path | Lead determines which auditor(s) cover that path |

### Phase 2: Parallel Analysis

Each specialist receives a focused prompt (see below). They:
- Use **Serena tools** (`mcp__serena__get_symbols_overview`, `mcp__serena__find_symbol`, `search_for_pattern`, `list_dir`, `find_file`, `mcp__serena__find_referencing_symbols`) and **Glob/Grep/Read** for code analysis. **Tool-naming note:** `mcp__serena__*` is the canonical MCP-registered prefix that matches `.claude/settings.json` (`mcp__serena__*` is in `permissions.allow`); some other repo docs (`CLAUDE.md`, `.serena/project.yml`, `agentic/commands/prime.md`) still reference legacy aliases like `jet_brains_*` or unprefixed names — treat those as the same tools and prefer the `mcp__serena__*` form here.
- Use `think_about_collected_information` after non-trivial research sequences
- Do **NOT** use Bash for file discovery or code searching — only for the per-auditor whitelisted shell commands
- Stay within the tool budget (~30 calls); set `COVERAGE: partial` if forced to stop early
- Send findings to `audit-lead` via `SendMessage` when done
- Mark their task completed via `TaskUpdate`

#### Severity Calibration (use the SAME yardstick across all auditors)

| Importance | Definition | anyplot-typical examples |
|---|---|---|
| **5 — Critical** | Production-breaking bugs, real security risks, data-loss potential, broken builds | Workflow uses unquoted `${{ github.event.issue.title }}` in `run:` (script injection); raw `ANTHROPIC_API_KEY` logged; Alembic migration without `downgrade()`; SQL constructed via f-string |
| **4 — High** | Significant code smells with concrete failure modes, test gaps for core paths, clear performance bottlenecks | N+1 query in `core/database/repositories/`; missing retry/timeout on Anthropic SDK call; `any` covering an entire MUI component tree; prompt file references a removed library |
| **3 — Medium** | Modernization, consistency, maintainability — non-urgent but real debt | Outdated 3.10-style typing where 3.14 idioms apply; inconsistent router naming; duplicated pydantic schemas |
| **2 — Low** | Cosmetic, comment-only, nit-level | Inconsistent docstring style; unused dev-only `print`; trailing whitespace not auto-fixed |
| **1 — Positive** | Patterns worth preserving (no action needed; informational) | Solid repository pattern in `core/database/`; well-isolated cache layer in `api/cache.py` |

Auditors MUST self-check against this table before assigning a number; if unsure between two levels, choose the lower one.

### Phase 2.5: Cross-Validation (Lead)

Before synthesis, the Lead runs a sanity pass on every finding with `IMPORTANCE >= 4`:

1. Route each such finding to **a different** auditor whose scope overlaps the affected files:
   - Backend ↔ security / db / llm-pipeline (depending on the file)
   - Frontend ↔ observability (analytics paths) or quality (test gaps)
   - Infra ↔ security (workflow injection / secret exposure)
   - llm-pipeline ↔ infra (workflow side) or backend (SDK call site)
2. The reviewing auditor responds with one of:
   - `KEEP` — finding stands as rated
   - `DOWNGRADE` — drop one importance level (with one-sentence reason)
   - `DROP` — false positive (with one-sentence reason)
3. The Lead records each verdict alongside the finding. `DROP` removes the finding; `DOWNGRADE` re-rates it. The reviewer's reason is preserved in the synthesis notes (not the final report) for traceability.
4. Findings with `IMPORTANCE <= 3` skip cross-validation to keep the pass cheap.

### Phase 3: Synthesis (Lead)

After all specialists report back and cross-validation has run:

1. **Collect** all findings from messages (post cross-validation)
2. **Deduplicate** — merge identical issues found by different auditors; keep the highest IMPORTANCE and union the FILES
3. **Flag contradictions** — if two auditors disagree on the same file, surface that explicitly in the synthesis notes
4. **Rate each finding:**
   - **Importance** (1-5): see Severity Calibration table above
   - **Effort**: S (<30min, 1 file, mechanical), M (1-3h, 2-5 files, local context), L (half day+, 5-15 files, design decisions), XL (multi-day, 15+ files, needs own plan)
   - **Auto-fix**: classify each finding as `ruff` (auto-fixable via `uv run ruff check --fix`), `eslint` (`yarn lint --fix`), `format` (`uv run ruff format`), `codemod` (mechanical rewrite that a small script could do), or `manual` (requires judgment)
5. **Compute Health Score (30-100):**
   - Start at 100
   - Subtract: `min(70, 10 * critical_count + 3 * high_count + 1 * medium_count)`
   - Round to integer; clamp to `[30, 100]` (the cap on subtractions intentionally floors the score at 30 so that very-bad audits remain comparable to bad ones)
   - This score is reproducible and trend-comparable across runs
6. **Build Quick Wins list:** every finding with `IMPORTANCE >= 4` AND `EFFORT == S`. This list answers "what should we tackle first?" and goes near the top of the report.
7. **Sort** within each importance bucket: Effort ascending, then Auto-fix `ruff` / `eslint` / `format` / `codemod` / `manual` (auto-fixable first)
8. **Persist** the final report to disk:
   - Path: `agentic/audits/{YYYY-MM-DD}-{scope_slug}.md` (e.g. `agentic/audits/2026-04-25-all.md`, `agentic/audits/2026-04-25-backend.md`, `agentic/audits/2026-04-25-since_main.md`)
   - **Build `scope_slug` deterministically from `$ARGUMENTS`:**
     - Empty / `all` → `all`
     - Single keyword (`backend`, `frontend`, `infra`, `quality`, `tests`, `llm`, `pipeline`, `db`, `database`, `security`, `sec`, `observability`, `obs`) → that keyword verbatim
     - Directory path → replace `/` with `_`, drop leading/trailing `_`, lowercase (e.g. `core/database/` → `core_database`)
     - `since=<ref>` → `since_<ref>` with `<ref>` sanitized: replace any character not matching `[A-Za-z0-9._-]` with `_` (e.g. `since=feature/foo` → `since_feature_foo`, `since=HEAD~10` → `since_HEAD_10`)
     - Combinations (e.g. `backend since=main`) → join the parts with `_` (`backend_since_main`)
     - Final slug must match `^[A-Za-z0-9._-]+$`; if anything still doesn't match after the rules above, fall back to `all`
   - Also overwrite `agentic/audits/latest.md` with the same content
   - Create `agentic/audits/` if missing
9. **Output** the report (see Output Format below) inline AND confirm the persisted path
10. **Cleanup**: Send `shutdown_request` to all auditors, then `TeamDelete`

### Output Format

```markdown
# Audit Report: anyplot

**Date:** {date} | **Scope:** {scope} | **Mode:** {full | incremental since=<ref>, N files}
**Health Score:** {0-100} | **Baseline:** ruff: {N issues}, format: {status}
**Auditors:** {n} ran ({list}) | **Findings:** {total} | **Auto-fixable:** {n}/{total}

## Summary
{2-3 sentences: overall health, key themes, biggest risks}

## Quick Wins (Importance ≥4 & Effort=S)
| # | Finding | Auto-fix | Files | Hint |
|---|---------|----------|-------|------|
| 1 | {description} | ruff/eslint/format/codemod/manual | `{files}` | {one-line fix hint} |

## Critical (Importance 5)
| # | Finding | Effort | Auto-fix | Files | Hint |
|---|---------|--------|----------|-------|------|
| 1 | {description} | S/M/L/XL | ruff/eslint/format/codemod/manual | `{files}` | {one-line fix hint} |

## High (Importance 4)
| # | Finding | Effort | Auto-fix | Files | Hint |
|---|---------|--------|----------|-------|------|

## Medium (Importance 3)
| # | Finding | Effort | Auto-fix | Files | Hint |
|---|---------|--------|----------|-------|------|

## Low (Importance 2)
| # | Finding | Effort | Auto-fix | Files | Hint |
|---|---------|--------|----------|-------|------|

## Positive Patterns (Importance 1)
- {good patterns to keep}

## Statistics
- Total: {N} | Critical: {n}, High: {n}, Medium: {n}, Low: {n}
- Effort: S {n}, M {n}, L {n}, XL {n}
- Auto-fix: ruff {n}, eslint {n}, format {n}, codemod {n}, manual {n}
- By Auditor: backend {n}, frontend {n}, infra {n}, quality {n}, llm {n}, db {n}, security {n}, obs {n}
- Cross-validation: {n} reviewed, {n} dropped, {n} downgraded
- Coverage: {n} auditors complete, {n} partial
```

### Exclusions (apply to ALL auditors)

Do NOT flag:
- Plot implementations in `plots/` (AI-generated, different style rules)
- Generated files or lock files (`uv.lock`, `yarn.lock`, etc.)
- Third-party code or `node_modules/`
- Issues already covered by pyproject.toml exclusions
- Past audit reports in `agentic/audits/` (don't audit your own output)
- Mechanical metadata in `alembic/versions/` headers (revision IDs, down_revision); the **content** of migrations is the db-auditor's responsibility

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
2. Use `mcp__serena__get_symbols_overview` on key files to understand architecture
3. Use `mcp__serena__find_symbol` with `depth=1` to inspect classes and their methods
4. Use `search_for_pattern` to find anti-patterns (e.g. `bare except`, `type: ignore`, `Any`, `TODO`, `FIXME`)
5. Use `mcp__serena__find_referencing_symbols` to check if code is actually used
6. Use `think_about_collected_information` after research sequences
7. **Do NOT use Bash** for `find`, `ls`, `grep`, `cat` — use Serena/Glob/Grep/Read tools instead
8. You MAY use Bash for: `uv run ruff check api/ core/ automation/` or `uv run pytest tests/unit -x -q`

**Report format:** Send findings to `audit-lead` via `SendMessage`. Start the message with one `COVERAGE: full` or `COVERAGE: partial` line, then list findings:
```
COVERAGE: full | partial
---
FINDING: {short title}
IMPORTANCE: {1-5}     # see Severity Calibration table
EFFORT: {S/M/L/XL}
AUTO-FIX: {ruff | eslint | format | codemod | manual}
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
- **MUI 9 patterns**: Correct theme usage, sx prop vs styled, consistent component usage
- **Dead code**: Unused components, unused imports, unreachable code, commented-out code
- **Error handling**: Error boundaries, loading states, empty states, fallbacks
- **Consistency**: Naming conventions, file organization, export patterns

**How to work:**
1. Use `list_dir` to understand `app/src/` structure
2. Use Glob to find all `.tsx` and `.ts` files: `**/*.tsx`, `**/*.ts` in `app/src/`
3. Use `mcp__serena__get_symbols_overview` on key components
4. Use Grep to search for anti-patterns (e.g. `: any`, `eslint-disable`, `@ts-ignore`, `console.log`)
5. Use `search_for_pattern` for cross-file patterns
6. Use `think_about_collected_information` after research sequences
7. **Do NOT use Bash** for `find`, `ls`, `grep`, `cat` — use Serena/Glob/Grep/Read tools instead
8. You MAY use Bash for: `cd app && yarn type-check 2>&1 | tail -20`

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
2. Use `mcp__serena__get_symbols_overview` on test files to check test method quality
3. Use `search_for_pattern` to find test anti-patterns (e.g. `assert True`, `pass`, empty test bodies)
4. Use Glob to find all `.md` docs files, then Read key ones to check staleness
5. Use Grep to verify cross-references (e.g. file paths mentioned in docs actually exist)
6. Use `think_about_collected_information` after research sequences
7. **Do NOT use Bash** for `find`, `ls`, `grep`, `cat` — use Serena/Glob/Grep/Read tools instead
8. You MAY use Bash for: `uv run pytest tests/ --co -q 2>&1 | tail -20` (list collected tests)

**Report format:** Same as backend-auditor — send findings to `audit-lead` via `SendMessage`.

### llm-pipeline-auditor

You are the **llm-pipeline-auditor** on the audit team. anyplot's core is a spec→impl LLM pipeline; you own its end-to-end quality. Your scope spans `core/generators/`, `prompts/`, the `claude_*` knobs in `core/config.py`, the orchestration in `agentic/workflows/`, and the AI-pipeline GitHub workflows (`.github/workflows/{spec,impl,bulk,daily}-*.yml`).

**Your scope:**
- **Anthropic SDK usage**: Correct `client.messages.create` shape; explicit `max_tokens`, `timeout`, and retry on `RateLimitError` / `APIStatusError`; streaming used where it should be; no swallowed `APIError`
- **Model selection**: Per-task model choice (Haiku for cheap classification, Sonnet for generation, Opus for review) is consistent with `core/config.py` `claude_model` / `claude_review_model`; no hardcoded model strings sneaking past config
- **Token & cost discipline**: `max_tokens` matched to expected output size; system-prompt sizes reasonable; no obviously redundant context concatenation
- **Prompt caching**: For long, stable system prompts and library guides, are `cache_control` blocks present (`{"type": "ephemeral"}`)? Missing caching on ≥1k-token static prefixes is a finding
- **Prompt quality** (in `prompts/`): clarity of role + task + format; explicit refusal of unsafe outputs; consistent placeholder syntax; library-guides aligned with what `core/generators/` actually requests; no dangling references to renamed/removed files
- **Output schema stability**: When prompts demand JSON, is parsing defensive (try/except around `json.loads`, schema validation)? Are tool-use blocks preferred over freeform JSON for structured outputs?
- **Hallucination mitigation**: Grounding via examples, explicit "say I don't know" instructions for uncertain answers, retrieval/context separation
- **Pipeline resilience**: spec→impl→review→merge in workflows handles failures (impl-repair path), no infinite retry loops, idempotent re-runs, clear failure modes
- **Workflow ↔ code drift**: Do workflow inputs/outputs match what `core/generators/` and `agentic/workflows/modules/` expect?

**How to work:**
1. `list_dir` on `prompts/`, `core/generators/`, `agentic/workflows/`
2. `mcp__serena__get_symbols_overview` on `core/generators/plot_generator.py` and any sibling generators
3. `mcp__serena__find_symbol` on the `Anthropic` / `client.messages.create` call sites
4. Grep for: `anthropic\.`, `messages.create`, `max_tokens`, `cache_control`, hardcoded model strings (`claude-`, `sonnet`, `haiku`, `opus`), bare `except` around SDK calls
5. Read each prompt file at least skim-depth; look for placeholder mismatches and library references
6. `mcp__serena__find_referencing_symbols` on each prompt-loader function to see who consumes which prompt
7. `think_about_collected_information` after the SDK + prompt scan
8. **Do NOT use Bash** for file discovery
9. You MAY use Bash for: `uv run python -c "from core.config import settings; print(settings.claude_model, settings.claude_max_tokens)"` to confirm runtime config

**Tool budget:** ~30 calls. If insufficient, set `COVERAGE: partial` and prioritize the SDK call sites + the 5 most-loaded prompts.

**Report format:** Same as backend-auditor.

### db-auditor

You are the **db-auditor** on the audit team. Analyze `alembic/`, `core/database/`, and `alembic.ini`. anyplot uses async SQLAlchemy 2.0 with asyncpg locally and a hybrid Cloud SQL Connector / pg8000 path in CI — migration safety and async-correctness matter.

**Your scope:**
- **Alembic migrations** (`alembic/versions/`, ~15 files): every migration has a real `downgrade()` (not `pass`); no destructive ops without an explicit data-migration step; long-running ALTERs flagged for production lock risk; revision chain unbroken; no merged divergent heads left behind
- **Schema design** (`core/database/models.py`): Indexes on every FK and on every column used in WHERE/ORDER BY in repositories; sane `ON DELETE` cascades; nullable vs not-null deliberate; appropriate column types (no TEXT where ENUM/VARCHAR fits); composite indexes for multi-column filters
- **Async correctness**: `AsyncSession` usage consistent; no sync DB calls inside async paths; greenlet-safe attribute access (`selectinload`/`joinedload` rather than lazy-loaded attributes after session close); proper `await session.commit()` / `rollback()` around units of work
- **Repository layer** (`core/database/repositories/`): N+1 queries, missing eager loads, raw-SQL strings (and whether they're parameterized), repository methods returning domain objects vs leaking ORM models
- **Connector hybrid (asyncpg vs pg8000)**: Code paths cleanly separated; no asyncpg-only features used where pg8000 is the connector
- **Migration ↔ model drift**: Models declare columns/indexes that aren't in any migration, or vice versa

**How to work:**
1. `list_dir` on `alembic/versions/` and `core/database/`
2. `mcp__serena__get_symbols_overview` on `core/database/models.py` and each repository file
3. Read each migration file (they're typically small — Read the whole list); flag missing `downgrade()` or `op.execute(...)` raw-SQL without a parameterization story
4. Grep for: `op\.drop_`, `op\.alter_column`, `pass\s*$` inside `def downgrade`, `lazy=`, `selectinload`, `joinedload`, raw `text("...")` in repositories, `await .* commit\(\)`
5. `mcp__serena__find_referencing_symbols` on each model class to find query call sites (N+1 hunting)
6. `think_about_collected_information` after the migration sweep
7. **Do NOT use Bash** for file discovery
8. You MAY use Bash for: `uv run alembic check` (catches model↔migration drift) and `uv run alembic history --indicate-current 2>&1 | tail -20`

**Tool budget:** ~30 calls. If insufficient, set `COVERAGE: partial` and prioritize the latest 5 migrations + repository files with the most call sites.

**Report format:** Same as backend-auditor.

### security-auditor

You are the **security-auditor** on the audit team. anyplot has a public, unauthenticated API surface, calls Anthropic + GCS, and runs many GitHub workflows including some triggered by external events. Your scope is repo-wide but focused on `api/`, `core/config.py`, `agentic/workflows/`, and `.github/workflows/`.

**Your scope:**
- **Secret handling**: Where are secrets read (`os.getenv`, `os.environ`, settings)? Are any logged, echoed, or returned in error responses? Are GCS service account credentials handled correctly? Any hardcoded fallbacks?
- **Workflow injection**: `${{ github.event.* }}` interpolated directly into `run:` blocks (script injection); use of `pull_request_target` without a pinned, sanitized checkout; missing `permissions:` block (default-write tokens); third-party actions referenced by tag instead of SHA
- **Public API surface**: Endpoints in `api/routers/` that touch the DB or the LLM pipeline without rate limiting; CORS configuration; reflection of user input into responses (XSS via SVG/HTML); SSRF risk in any proxy / fetch endpoint
- **SQL injection**: Any raw SQL constructed via f-strings or `%`-formatting (must be parameterized via `text(...).bindparams()` or ORM)
- **Dependency CVEs**: `uv run --with pip-audit pip-audit` for Python deps (ephemeral; `pip-audit` is intentionally not a project dep) and `yarn audit` (Yarn 1.22 syntax) for frontend deps — flag any High/Critical
- **MCP server (`api/mcp/`)**: Authentication on the MCP endpoints (or deliberate lack thereof, documented); input validation
- **CSP / security headers**: Frontend response headers (if served from FastAPI), iframe restrictions for og-image endpoints

**How to work:**
1. `list_dir` on `.github/workflows/` and `api/routers/`
2. Grep across the repo for: `os\.getenv`, `os\.environ`, `\${{\s*github\.event\.`, `pull_request_target`, `permissions:`, `actions/checkout@`, `f"\s*SELECT`, `f"\s*INSERT`, `f"\s*UPDATE`, `\.format\(.*SELECT`, `eval\(`, `exec\(`, `subprocess\.`, `shell=True`
3. `mcp__serena__find_symbol` on each FastAPI router function to see what it accepts and reflects
4. Read every workflow file that triggers on `pull_request_target`, `issue_comment`, or `workflow_dispatch` end-to-end
5. `think_about_collected_information` after the workflow + API scan
6. **Do NOT use Bash** for file discovery
7. You MAY use Bash for: `uv run --with pip-audit pip-audit 2>&1 | tail -30` (ephemeral install — `pip-audit` is intentionally NOT a project dep) and `cd app && yarn audit --level high --groups dependencies 2>&1 | tail -30` (Yarn 1.22 syntax, matches `packageManager` in `app/package.json`)

**Tool budget:** ~30 calls. If insufficient, set `COVERAGE: partial` and prioritize: workflow injection vectors, secret leakage paths, and any raw-SQL site.

**Report format:** Same as backend-auditor.

### observability-auditor

You are the **observability-auditor** on the audit team. anyplot uses Plausible (server-side via `api/analytics.py` + client-side via `app/src/analytics/`) and has a TTL cache layer in `api/cache.py` plus Web-Vitals reporting. Your job is to detect drift between code, docs, and frontend usage.

**Your scope:**
- **Plausible event consistency**: Every event emitted from `api/analytics.py` and `app/src/analytics/useAnalytics.ts` is documented in `docs/reference/plausible.md`, and vice versa — no orphan events on either side. Event names use a consistent naming convention.
- **Web Vitals pipeline** (`app/src/analytics/reportWebVitals.ts`): Reports LCP / CLS / INP / FCP / TTFB; metrics actually arrive at Plausible (correct event payload shape); no dev-only console-noise leaking into prod
- **Server-side analytics correctness**: Fire-and-forget pattern in `api/analytics.py` doesn't block the main response; failures are caught and logged, not raised; respects DNT / opt-out if applicable
- **Cache observability** (`api/cache.py`): Hit/miss logging or counters present; TTL values reasonable (not "never expire" for content that changes); refresh task failures surfaced
- **Structured logging**: Use of `logging.getLogger(__name__)` consistently; no `print()` in production paths; log levels sensible (no INFO-spam, no missed ERRORs); log context (request IDs, spec IDs) carried through async boundaries
- **LLM observability**: Around each Anthropic SDK call there should be at minimum: input-token-count log, output-token-count log, latency log, and error log. Missing instrumentation is a Medium-to-High finding for a system whose largest cost driver is LLM calls.
- **Tracing / metrics**: No Sentry or OpenTelemetry detected — flag this as a known gap (Importance 3) only if logging coverage is also weak; otherwise note as Positive Pattern that the team has chosen logs-only

**How to work:**
1. `list_dir` on `app/src/analytics/`, plus Read `api/analytics.py`, `api/cache.py`, `docs/reference/plausible.md`
2. `mcp__serena__find_symbol` on the Plausible event-emitting functions in both backend and frontend
3. `mcp__serena__find_referencing_symbols` on each event-emitter to count call sites and check naming
4. Grep for: `print\(`, `logging\.`, `logger\.`, `plausible`, `track`, `event\(`, around the Anthropic SDK call sites
5. Read `docs/reference/plausible.md` and cross-check every documented event against actual emit sites; flag mismatches in both directions
6. `think_about_collected_information` after the analytics + logging scan
7. **Do NOT use Bash** for file discovery
8. You MAY use Bash for: `cd app && yarn build 2>&1 | tail -20` to check that the analytics bundle builds cleanly

**Tool budget:** ~30 calls. If insufficient, set `COVERAGE: partial` and prioritize Plausible event drift first, LLM-call instrumentation second.

**Report format:** Same as backend-auditor.
