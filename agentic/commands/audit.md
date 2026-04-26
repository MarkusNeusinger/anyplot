# Code Quality Audit

> Team-based code quality audit for the anyplot repository. Spawns up to fifteen specialized Opus agents (backend, frontend, infra, quality, llm-pipeline, db, security, observability, agentic, gcloud, github, plausible, pagespeed, seo, catalog) that analyze the codebase and live systems in parallel. Lead cross-validates high-severity findings, synthesizes a prioritized, effort-rated, auto-fix-aware action plan, and persists the report for regression tracking. Auditors that touch external systems degrade gracefully when credentials are missing — they never block the rest of the run.

## Context

@CLAUDE.md
@pyproject.toml

## Instructions

You are the **audit-lead**. Your job is to coordinate a team of specialist auditors, run a cross-validation pass on high-severity findings, and synthesize a single deduplicated, prioritized, persistable report.

### Phase 1: Setup

1. **Parse scope from `$ARGUMENTS`:**
   - Empty / `all` → spawn all 15 auditors
   - Single keyword → spawn only that auditor (see Scope Table)
   - Directory path → Lead determines which auditor(s) cover that path
   - Optional `since=<git-ref>` (e.g. `since=main`, `since=HEAD~10`) → **Incremental mode**: Lead computes the changed file list once via `git diff --name-only <ref>...HEAD` and passes the relevant subset to each auditor. Auditors must restrict their analysis to those files (plus their direct importers if a quick `mcp__serena__find_referencing_symbols` lookup is cheap). If `since=` is omitted, auditors run a full sweep of their scope. The five external-system auditors (`gcloud`, `github`, `plausible`, `pagespeed`, `seo`) ignore `since=` because their scope is live systems, not files.

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

   | Auditor | Primary Paths / Surface |
   |---|---|
   | `backend-auditor` | `api/`, `core/`, `automation/` |
   | `frontend-auditor` | `app/src/` |
   | `infra-auditor` | `.github/workflows/`, `prompts/`, Dockerfiles, top-level configs |
   | `quality-auditor` | `tests/`, `docs/`, `agentic/commands/`, README/CLAUDE.md |
   | `llm-pipeline-auditor` | `core/generators/`, `prompts/`, `core/config.py` (claude_*), `agentic/workflows/`, `.github/workflows/{spec,impl,bulk}-*.yml` |
   | `db-auditor` | `alembic/`, `core/database/`, `alembic.ini` |
   | `security-auditor` | repo-wide (primarily `api/`, `core/config.py`, `agentic/workflows/`, `.github/workflows/`) |
   | `observability-auditor` | `api/analytics.py`, `api/cache.py`, `app/src/analytics/`, `docs/reference/plausible.md` |
   | `agentic-auditor` | `CLAUDE.md`, `agentic/`, `prompts/`, `.claude/`, `agentic/commands/` (TAC-style: agent ergonomics) |
   | `gcloud-auditor` | live `anyplot` GCP project (Cloud Run, Cloud SQL, GCS, Cloud Build, Logs, IAM, Secret Manager) — **read-only** |
   | `github-auditor` | `MarkusNeusinger/anyplot` GitHub repo via `gh` (branches, PRs, issues, runs, labels, secrets/vars, branch protection) — **read-only** |
   | `plausible-auditor` | live Plausible Stats API for `anyplot.ai`, cross-checked against `api/analytics.py`, `app/src/analytics/`, `docs/reference/plausible.md` — **read-only** |
   | `pagespeed-auditor` | live `anyplot.ai` via PageSpeed Insights v5 REST (mobile + desktop) — **read-only** |
   | `seo-auditor` | live `anyplot.ai` via Google Search Console API + structural fetches (sitemap, robots, canonical, meta, JSON-LD) — **read-only** |
   | `catalog-auditor` | the plot catalog itself: `plots/` filesystem, Postgres rows, GCS preview integrity (sampled) — **read-only** |

   Create one task per active auditor, spawn them in parallel, and assign tasks. Catalog runs in parallel with the others; any cross-references against Plausible/SEO findings are computed by the Lead in Phase 3, not by `catalog-auditor` itself.

4. **Tool-budget hint** (paste into every auditor prompt): each auditor should keep itself under ~30 read/search tool calls (the `gcloud-auditor` may use ~50 because each `gcloud` invocation is one shell call). If they cannot finish within budget, they must report partial findings + a `COVERAGE: partial` flag rather than running unbounded.

5. **Read-only and degraded-mode contract** (applies to every auditor that touches a system outside this repo — `gcloud`, `github`, `plausible`, `pagespeed`, `seo`, plus any HTTP fetches used by `catalog`):
   - **Read-only is absolute.** Do not run any command, API call, or HTTP method that creates, updates, deletes, sets, enables/disables, deploys, grants, patches, merges, closes, comments, dispatches, restarts, rotates, or otherwise changes anything — anywhere. This includes any `gcloud … create/update/delete/set/enable/disable/deploy/patch/add-iam-policy-binding/run-services-update-traffic`, any `gh pr/issue/run/secret/variable/label/workflow` write, any non-`GET`/`HEAD` HTTP call, any `bq` mutation, any `gcloud auth login/application-default login`. If unsure whether a command is read-only, do not run it.
   - **Auth never blocks the run.** If a credential is missing or the wrong project/account is active, the auditor reports `COVERAGE: blocked` (or `COVERAGE: degraded` if it can still do part of its job) plus a single `LIMITATION:` line explaining what was unavailable, then returns no/partial findings. Other auditors are unaffected. The Lead never aborts `/audit` because of one auditor's auth failure — it just notes the limitation in the Coverage section.
   - **Flexibility.** The starter checks listed in each specialist prompt are *ideas*, not a checklist to grind through. Each auditor uses judgment about what is most worth surfacing for THIS run within the tool budget, and is free to drop low-signal areas or follow a thread that is producing real findings.

### Scope Table

| `$ARGUMENTS` | Active Auditors |
|------------|----------------|
| _(empty / `all`)_ | backend, frontend, infra, quality, llm-pipeline, db, security, observability, agentic, gcloud, github, plausible, pagespeed, seo, catalog |
| `backend` | backend-auditor only |
| `frontend` | frontend-auditor only |
| `infra` | infra-auditor only |
| `quality` or `tests` | quality-auditor only |
| `llm` or `pipeline` | llm-pipeline-auditor only |
| `db` or `database` | db-auditor only |
| `security` or `sec` | security-auditor only |
| `observability` or `obs` | observability-auditor only |
| `agentic` | agentic-auditor only |
| `gcloud` or `gcp` | gcloud-auditor only |
| `github` or `gh` | github-auditor only |
| `plausible` | plausible-auditor only |
| `pagespeed` or `psi` | pagespeed-auditor only |
| `seo` | seo-auditor only |
| `catalog` | catalog-auditor only |
| `since=<ref>` (alone or combined) | Incremental mode for the selected scope (ignored by the five external-system auditors) |
| directory path | Lead determines which auditor(s) cover that path |

### Phase 2: Parallel Analysis

Each specialist receives a focused prompt loaded from `agentic/commands/audit/<name>-auditor.md` (see the Specialist Prompts index below). They:
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

1. Route each such finding to **a different** auditor whose scope overlaps the affected files / surface:
   - Backend ↔ security / db / llm-pipeline (depending on the file)
   - Frontend ↔ observability (analytics paths) or quality (test gaps)
   - Infra ↔ security (workflow injection / secret exposure) or github (workflow runs side) or gcloud (deploy-target side)
   - llm-pipeline ↔ infra (workflow side) or backend (SDK call site)
   - Agentic ↔ quality (commands/docs overlap) or infra (prompts and workflow integration)
   - Gcloud ↔ observability (logs/metrics overlap) or infra (deploy/workflow side) or security (IAM/secrets)
   - Github ↔ infra (workflow files) or quality (issue/docs hygiene) or security (branch protection, secret hygiene)
   - Plausible ↔ observability (event drift) or frontend (Web Vitals → component code)
   - Pagespeed ↔ frontend (perf opportunities → component code) or infra (caching/headers/Cloud Run config)
   - Seo ↔ frontend (missing meta/JSON-LD → component code) or infra (robots/sitemap/headers) or pagespeed (lab vs field Web Vitals)
   - Catalog ↔ db (FS/DB drift) or llm-pipeline (specs failing generation) or infra (sync workflow)
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
7b. **Optional cross-auditor synthesis** — only when the relevant auditors all ran in this session and produced data:
   - **Deprecation candidates** (Catalog × Plausible × SEO): specs that show up as low-traffic in Plausible AND zero-impression in Search Console AND have low coverage / low quality in catalog → emit a single Medium-importance finding listing the candidate spec-ids with effort `M` and auto-fix `manual`.
   - **Web Vitals lab vs field divergence** (Pagespeed × Plausible / Pagespeed × SEO): URLs where lab CWV passes but field CWV fails (or vice-versa) → emit one finding per affected URL, importance derived from how far off the field metric is.
   - These are computed from the auditors' findings, not by re-querying. If any required auditor is `COVERAGE: blocked`, skip the synthesis silently.
8. **Persist** the final report to disk:
   - Path: `agentic/audits/{YYYY-MM-DD}-{scope_slug}.md` (e.g. `agentic/audits/2026-04-25-all.md`, `agentic/audits/2026-04-25-backend.md`, `agentic/audits/2026-04-25-since_main.md`)
   - **Build `scope_slug` deterministically from `$ARGUMENTS`:**
     - Empty / `all` → `all`
     - Single keyword (`backend`, `frontend`, `infra`, `quality`, `tests`, `llm`, `pipeline`, `db`, `database`, `security`, `sec`, `observability`, `obs`, `agentic`, `gcloud`, `gcp`, `github`, `gh`, `plausible`, `pagespeed`, `psi`, `seo`, `catalog`) → that keyword verbatim
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
**External sources:** {only include lines that apply}
- GCP project: {project-id} (gcloud-auditor)
- Plausible site: {anyplot.ai} (plausible-auditor)
- PageSpeed analysisUTCTimestamps: {url → ts list} (pagespeed-auditor)
- Search Console mode: {full | structural-only} | freshness: {date} (seo-auditor)
- GitHub: {gh user / repo} (github-auditor)
- Catalog DB rows: {n specs / n implementations} (catalog-auditor)

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
- By Auditor: backend {n}, frontend {n}, infra {n}, quality {n}, llm {n}, db {n}, security {n}, obs {n}, agentic {n}, gcloud {n}, github {n}, plausible {n}, pagespeed {n}, seo {n}, catalog {n}
- Cross-validation: {n} reviewed, {n} dropped, {n} downgraded
- Coverage: {n} auditors complete, {n} partial, {n} blocked (auth/credentials missing — list which)
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

Each auditor's full prompt lives in its own file under `agentic/commands/audit/`. The Lead reads the file for each active auditor and passes its content as the spawn prompt. Editing one auditor's prompt does not touch the others.

| Auditor | Prompt file |
|---|---|
| `backend-auditor` | `agentic/commands/audit/backend-auditor.md` |
| `frontend-auditor` | `agentic/commands/audit/frontend-auditor.md` |
| `infra-auditor` | `agentic/commands/audit/infra-auditor.md` |
| `quality-auditor` | `agentic/commands/audit/quality-auditor.md` |
| `llm-pipeline-auditor` | `agentic/commands/audit/llm-pipeline-auditor.md` |
| `db-auditor` | `agentic/commands/audit/db-auditor.md` |
| `security-auditor` | `agentic/commands/audit/security-auditor.md` |
| `observability-auditor` | `agentic/commands/audit/observability-auditor.md` |
| `agentic-auditor` | `agentic/commands/audit/agentic-auditor.md` |
| `gcloud-auditor` | `agentic/commands/audit/gcloud-auditor.md` |
| `github-auditor` | `agentic/commands/audit/github-auditor.md` |
| `plausible-auditor` | `agentic/commands/audit/plausible-auditor.md` |
| `pagespeed-auditor` | `agentic/commands/audit/pagespeed-auditor.md` |
| `seo-auditor` | `agentic/commands/audit/seo-auditor.md` |
| `catalog-auditor` | `agentic/commands/audit/catalog-auditor.md` |

**Spawn pattern (Lead):** for each active auditor, Read the corresponding file and use its full contents as the task prompt. Prepend the shared rules from Phase 1 (tool budget, severity calibration, read-only / degraded-mode contract for external auditors) so each spawned subagent has the full context without the per-auditor file having to repeat them. The auditor files describe scope and how-to-work; the orchestrator (this file) owns the cross-cutting rules.

**Adding a new auditor:** create `agentic/commands/audit/<name>-auditor.md`, add a row to the Auditor table in Phase 1 + a Scope-Table entry + a Statistics-line key in Phase 3 + a row above. No other code changes required.

