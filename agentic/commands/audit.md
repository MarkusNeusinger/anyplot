# Code Quality Audit

> Team-based, goal-directed audit for the anyplot repository. Its north star is not "list bugs" but **"how far is anyplot from an exemplary repository, and what is the shortest path there?"** measured across six dimensions — **Security, Speed, Looks (Aussehen/UX), Modern, Correctness, Maintainability**. Spawns up to 22 specialized agents (backend, frontend, chat-frontend, design, infra, quality, llm-pipeline, db, security, observability, agentic, agents, sandbox, public-lane, gcloud, github, plausible, pagespeed, seo, catalog, site, landing) that analyze the codebase, the live systems, and the public surfaces in parallel. Lead cross-validates the high-severity findings and the ones an outside reader meets first (domain-routed), synthesizes a prioritized, dimension-tagged, effort-rated, auto-fix-aware action plan with a per-dimension scorecard, and persists the report for regression tracking. Auditors that touch external systems degrade gracefully when credentials are missing — they never block the rest of the run.

## Context

@CLAUDE.md
@pyproject.toml

## Mission: drive anyplot toward an exemplary repository

Every `/audit` run exists to move anyplot closer to a repository other people would hold up as a model — beautiful, secure, fast, and modern. To make that goal operational and trend-comparable, every finding is tagged with exactly one **dimension** (see Dimension Taxonomy), and the report rolls findings up into a per-dimension scorecard plus an overall Health Score.

Auditors therefore surface two kinds of finding:
- **Defects** — something is wrong, slow, insecure, ugly, or dated and should be fixed.
- **Exemplary gaps** — nothing is broken, but a best-in-class repo in this space would have something anyplot lacks (see Exemplary Repository Rubric). These are real findings, rated by impact and effort like any other.

The point is a report that answers "where are we strong, where are we weak, and what do I fix first to look exemplary?" — not an undifferentiated bug list.

anyplot is also its owner's public showcase: people open the site and the repository to judge the work, and some of them decide within minutes. Severity alone ranks a typo on the landing page below a rare race in a script nobody opens, although far more readers meet the typo. Every finding therefore also says **who meets it first** (`SEEN_BY`: a visitor of the site, a visitor of the repository page, a reader of the code, or nobody outside), and the report lists what an outside reader meets in a section of its own.

## Instructions

You are the **audit-lead**. Your job is to coordinate a team of specialist auditors, run a cross-validation pass on high-severity findings, and synthesize a single deduplicated, prioritized, dimension-scored, persistable report.

### Phase 1: Setup

1. **Parse scope from `$ARGUMENTS`:**
   - Empty / `all` → spawn all 22 auditors
   - Single keyword → spawn only that auditor or group (see Scope Table); several keywords → their union
   - Directory path → Lead determines which auditor(s) cover that path
   - Optional `since=<git-ref>` (e.g. `since=main`, `since=HEAD~10`) → **Incremental mode**: Lead computes the changed file list once via `git diff --name-only <ref>...HEAD` and passes the relevant subset to each auditor. Auditors must restrict their analysis to those files (plus their direct importers if a quick Grep lookup is cheap). If `since=` is omitted, auditors run a full sweep of their scope. The seven auditors of live systems and public surfaces (`gcloud`, `github`, `plausible`, `pagespeed`, `seo`, `site`, `landing`) ignore `since=` because their scope is not a set of files.

2. **Run baseline measurements** (these are the ONLY Bash commands the Lead runs in this phase):
   ```bash
   uv run --extra dev ruff check . 2>&1 | tail -5
   ```
   ```bash
   uv run --extra dev ruff format --check . 2>&1 | tail -5
   ```
   In `since=` mode, additionally:
   ```bash
   git diff --name-only <ref>...HEAD
   ```
   Record ruff issue count, format status, and (if applicable) the changed-file count for the report header.

3. **Determine the active auditor set.** Each auditor is `general-purpose` and runs on the model its row names; this audit optimizes for finding quality, not cost, so don't downgrade a model. The routing follows `agentic/docs/agent-operations.md`: Opus for reviews that need judgment, Fable for the high-risk ones (security, the sandbox, the public lane and its privacy). Pass the model explicitly for every auditor, because a workflow agent otherwise inherits the model of the session that started it. The active set is:

   | Auditor | Primary Paths / Surface | Default dimensions | Model |
   |---|---|---|---|
   | `backend-auditor` | `api/` (without the agent routers), `core/` | correctness, maintainability, speed | opus |
   | `frontend-auditor` | `app/src/` without the agent chat, plus the app's configuration (code quality: types, hooks, state, a11y-correctness) | correctness, maintainability, modern | opus |
   | `chat-frontend-auditor` | the agent chat's frontend: `app/src/hooks/useAgentSession*`, `app/src/lib/agent.ts`, `app/src/sections/agent-chat/`, `app/src/pages/AgentChatPage*` | correctness, maintainability | opus |
   | `design-auditor` | `app/src/` (visual design, theme/dark-mode, responsive, UX polish, design-system consistency), reasoned from the code | looks | opus |
   | `infra-auditor` | `.github/workflows/`, `.github/actions/`, `prompts/`, Dockerfiles and `cloudbuild.yaml` of every service, `infra/`, top-level configs | security, maintainability, modern | opus |
   | `quality-auditor` | `tests/`, `docs/`, `scripts/`, `tools/`, `agentic/commands/`, README/CLAUDE.md accuracy, tooling strictness, repo-health files | maintainability, modern | opus |
   | `llm-pipeline-auditor` | `prompts/`, `automation/`, `scripts/evaluate-plot.py`, `core/config.py` (claude_*), `agentic/workflows/`, `.github/workflows/{spec,impl,bulk,daily}-*.yml` | correctness, speed, maintainability | opus |
   | `db-auditor` | `alembic/`, `core/database/`, `alembic.ini` | correctness, speed | opus |
   | `security-auditor` | repo-wide (primarily `api/`, `core/config.py`, `agentic/workflows/`, `.github/workflows/`, the edge configuration) | security | fable |
   | `observability-auditor` | `api/analytics.py`, `api/cache.py`, `app/src/hooks/useAnalytics.ts`, `app/src/analytics/`, `docs/reference/plausible.md`, the agent telemetry and the machine-readers log | maintainability, speed | opus |
   | `agentic-auditor` | `CLAUDE.md`, `agentic/`, `prompts/`, `.claude/` with its skills, `agentic/commands/` (TAC-style: agent ergonomics) | maintainability, modern | opus |
   | `agents-auditor` | the agent network's data and orchestration layer: `agents/anyplot/` without `code/` and `render/`, plus `agents/evals/` | correctness, maintainability | opus |
   | `sandbox-auditor` | generated-code handling and the render sandbox: `agents/anyplot/code/`, `agents/anyplot/render/`, `agents/renderer/` | security, correctness | fable |
   | `public-lane-auditor` | the public agent chat end to end: `agents/main.py`, the session, queue, policy, and telemetry modules, `api/routers/agent*.py`, `api/agent_*.py` | security, correctness | fable |
   | `gcloud-auditor` | live `anyplot` GCP project (Cloud Run, Cloud SQL, GCS, Cloud Build, Logs, IAM, Secret Manager) — **read-only** | security, speed | opus |
   | `github-auditor` | `MarkusNeusinger/anyplot` GitHub repo via `gh` (branches, PRs, issues, runs, labels, secrets/vars, branch protection) — **read-only** | maintainability, security | opus |
   | `plausible-auditor` | live Plausible Stats API for `anyplot.ai`, cross-checked against `api/analytics.py`, `app/src/hooks/useAnalytics.ts`, `docs/reference/plausible.md` — **read-only** | maintainability | opus |
   | `pagespeed-auditor` | live `anyplot.ai` via PageSpeed Insights v5 REST (mobile + desktop) — **read-only** | speed, looks | opus |
   | `seo-auditor` | live `anyplot.ai` via Google Search Console API + structural fetches (sitemap, robots, canonical, meta, JSON-LD) — **read-only** | modern, maintainability | opus |
   | `catalog-auditor` | the plot catalog's files: `plots/` filesystem, GCS preview integrity (sampled) — **read-only** | maintainability, correctness | opus |
   | `site-auditor` | live `anyplot.ai` as a first-time visitor, in a headless browser of its own (screenshots, desktop and mobile, both themes) — **read-only** | looks, correctness | opus |
   | `landing-auditor` | the repository as an outside reader meets it on GitHub: README, root listing, releases, PR/issue/Actions tabs, public files that read oddly out of context — **read-only** | maintainability | opus |

   The "Default dimensions" column is a *hint* for which pillars each auditor most often touches; the auditor still tags every finding with the single dimension that best fits it (see Dimension Taxonomy). Catalog runs in parallel with the others; any cross-references against Plausible/SEO findings are computed by the Lead in Phase 3, not by `catalog-auditor` itself.

4. **Depth and budget** (paste into every auditor prompt):
   - **Auditors that read code or docs have no call cap.** A cap of thirty calls cannot read a module of four thousand lines. Read the largest and most central files of the scope properly, hundreds of lines at a time; then three to five mid-sized files as a calibration of the typical quality; then the tests of what you read.
   - **Say what you read.** Every report lists in `READ` the files read in full or in large part, and in `NOT_COVERED` what in scope was not reached. A scope too large to finish gets `COVERAGE: partial`; an honest partial report beats a full one built on file heads.
   - **Auditors of live systems keep their cap** (it protects quotas and rate limits): about 30 calls, about 50 for the `gcloud-auditor` and the `landing-auditor`, and for the `site-auditor` about 80 page loads. The cap in each auditor's file wins.
   - **Evidence, and the counter-evidence.** Every finding carries primary evidence (`EVIDENCE`). Before reporting a behaviour as wrong, unhandled, or undocumented, look for the test that pins it, the comment or doc that records the decision, and the guard elsewhere: this repository documents its decisions heavily, and such claims are often wrong.

5. **Read-only and degraded-mode contract** (applies to every auditor that touches a system outside this repo — `gcloud`, `github`, `plausible`, `pagespeed`, `seo`, `site`, `landing`, plus any HTTP fetches used by `catalog`):
   - **Read-only is absolute.** Do not run any command, API call, or HTTP method that creates, updates, deletes, sets, enables/disables, deploys, grants, patches, merges, closes, comments, dispatches, restarts, rotates, or otherwise changes anything — anywhere. This includes any `gcloud … create/update/delete/set/enable/disable/deploy/patch/add-iam-policy-binding/run-services-update-traffic`, any `gh pr/issue/run/secret/variable/label/workflow` write, any non-`GET`/`HEAD` HTTP call, any `bq` mutation, any `gcloud auth login/application-default login`. If unsure whether a command is read-only, do not run it.
   - **Auth never blocks the run.** If a credential is missing or the wrong project/account is active, the auditor reports `COVERAGE: blocked` if it cannot do meaningful work, or `COVERAGE: partial` (optionally an auditor-specific reduced mode such as `structural-only` or `filesystem-only`) if it can still complete part of its job, plus a single `LIMITATION:` line explaining what was unavailable, then returns no/partial findings. Other auditors are unaffected. The Lead never aborts `/audit` because of one auditor's auth failure — it just notes the limitation in the Coverage section.
   - **Flexibility.** The starter checks listed in each specialist prompt are *ideas*, not a checklist to grind through. Each auditor uses judgment about what is most worth surfacing for THIS run within the tool budget, and is free to drop low-signal areas or follow a thread that is producing real findings.

6. **Limits on production and the live site** (paste into every auditor prompt; they hold for every auditor, whatever its scope):
   - **Nothing in the repository changes.** No Edit or Write on a tracked file, and `git` stays read-only (`log`, `show`, `diff`, `blame`, `ls-files`, `status`): no checkout, stash, commit, or fetch. The checkout stays on the branch it was found on.
   - **Don't start the app, the API, the agents service, or a migration, and don't run a script that loads `.env`**: it points at the shared production database. The commands an auditor file permits (`ruff`, `yarn type-check`, the unit tests) are fine, and so is reading the one named key an auditor file prescribes out of `.env` for a read-only API.
   - **Never print a secret's value.** Check a credential by exit code or by its name; show `***` in any command you quote.
   - **A browser check runs in a headless browser of the auditor's own** (`agentic/commands/audit/site-shots.mjs`), never in the shared Playwright MCP browser, whose current tab every session on the machine steers.
   - **`https://anyplot.ai/agent` is opened only by the `site-auditor`, at most twice, without any input.** Every load holds one of the sessions an anonymous network may have open (`AGENT_IP_MAX_SESSIONS`, 8), and the owner's own browser shares that network. No auditor starts an agent run.
   - **An `/og/` image request adds to a public counter** (a share or a machine read): at most three per run, with a crawler user agent, and only when a finding needs the image.
   - **Never open `/debug`**, and never use the admin token.
   - **Don't start sub-agents**, and stop only processes you started, by their PID.

### Orchestration: how the Lead runs the auditors

The audit has the same logical shape regardless of mechanism — fan out the active auditors (Phase 2), domain-route a cross-validation pass over the high-severity and the publicly visible findings (Phase 2.5), then synthesize (Phase 3). Pick the execution mechanism by what is available:

**Preferred — Workflow tool (deterministic).** If you are permitted to call the `Workflow` tool (ultracode on, or the user opted into workflows), drive Phases 2 + 2.5 with the committed script `agentic/commands/audit/audit.workflow.js`:
1. For each active auditor, `Read` its prompt file (`agentic/commands/audit/<name>-auditor.md`) and build a single combined prompt = **Shared Rules** (Depth and budget, Limits on production and the live site, Severity Calibration, Dimension Taxonomy + tagging rule, Who meets a finding, Exemplary Repository Rubric, Read-only/degraded-mode contract, Exclusions, Findings Schema) **+** the auditor file's contents. The script forces structured output via the Findings Schema, so the auditor returns validated JSON rather than the text protocol.
2. Invoke `Workflow({ scriptPath: "agentic/commands/audit/audit.workflow.js", args: { auditors: [{ name, prompt, model }], partnerMap: <cross-validation routing>, baseline: { ruff, format } } })`, with `model` taken from the auditor's row in the active-set table. Pass `args` as a real JSON object (the script also defends against `args` arriving JSON-stringified). The script fans out one agent per auditor, then cross-validates each finding Phase 2.5 selects with a domain-routed skeptic on the auditor's own model, and returns verdict-applied structured findings (`{ reports: [{ auditor, coverage, read, not_covered, findings, crossValidationStats }], baseline }`).
3. The Lead does NOT write files from inside the workflow. The script returns the structured reports; the Lead performs Phase 3 synthesis (Health Score, Dimension Scorecard, dedup, persist) itself, because persistence needs `Write`.
4. The script is **generic and args-driven** — it never hardcodes the auditor roster. Adding or editing an auditor never requires touching the `.js` file.

**Fallback — team-based.** If the Workflow tool is not available, run the classic team flow: build an "audit" team, create one task per active auditor (`general-purpose`, on the model its roster row names), spawn them in parallel, and have each send findings to `audit-lead` via `SendMessage` (text protocol mirroring the Findings Schema), mark its task done via `TaskUpdate`, and the Lead routes cross-validation by message and synthesizes. After synthesis, send `shutdown_request` to all auditors, then `TeamDelete`.

Both mechanisms use the **same** active set, Shared Rules, Findings Schema, Dimension Taxonomy, cross-validation routing, and synthesis — only the plumbing differs. Everything below (Phases 2–3, schema, output) is mechanism-agnostic.

### Scope Table

| `$ARGUMENTS` | Active Auditors |
|------------|----------------|
| _(empty / `all`)_ | backend, frontend, chat-frontend, design, infra, quality, llm-pipeline, db, security, observability, agentic, agents, sandbox, public-lane, gcloud, github, plausible, pagespeed, seo, catalog, site, landing |
| `backend` | backend-auditor only |
| `frontend` | frontend-auditor only |
| `chat` or `chat-frontend` | chat-frontend-auditor only |
| `design` or `looks` or `ux` | design-auditor only |
| `infra` | infra-auditor only |
| `quality` or `tests` | quality-auditor only |
| `llm` or `pipeline` | llm-pipeline-auditor only |
| `db` or `database` | db-auditor only |
| `security` or `sec` | security-auditor only |
| `observability` or `obs` | observability-auditor only |
| `agentic` | agentic-auditor only |
| `agents` | the agent network as a group: agents-auditor, sandbox-auditor, public-lane-auditor, chat-frontend-auditor |
| `sandbox` | sandbox-auditor only |
| `lane` or `public-lane` | public-lane-auditor only |
| `gcloud` or `gcp` | gcloud-auditor only |
| `github` or `gh` | github-auditor only |
| `plausible` | plausible-auditor only |
| `pagespeed` or `psi` | pagespeed-auditor only |
| `seo` | seo-auditor only |
| `catalog` | catalog-auditor only |
| `site` | site-auditor only |
| `landing` | landing-auditor only |
| `showcase` | the public surfaces as a group: site-auditor, landing-auditor |
| `since=<ref>` (alone or combined) | Incremental mode for the selected scope (ignored by the seven auditors of live systems and public surfaces) |
| directory path | Lead determines which auditor(s) cover that path |

### Phase 2: Parallel Analysis

Each specialist receives a focused prompt loaded from `agentic/commands/audit/<name>-auditor.md` (see the Specialist Prompts index below), prepended with the Shared Rules. They:
- Use **Glob/Grep/Read** for code analysis
- Pause and consolidate findings after non-trivial research sequences
- Do **NOT** use Bash for file discovery or code searching — only for the per-auditor whitelisted shell commands
- Follow the depth and budget rules of Phase 1 (no call cap for code and docs, the stated cap for live systems); set `COVERAGE: partial` if forced to stop early, and always report `READ` and `NOT_COVERED`
- Tag every finding with exactly one **dimension** (see Dimension Taxonomy) and one reader (see Who meets a finding), and emit it per the **Findings Schema**
- Return findings (structured JSON in Workflow mode; text protocol via `SendMessage` in team mode)

#### Severity Calibration (use the SAME yardstick across all auditors)

| Importance | Definition | anyplot-typical examples |
|---|---|---|
| **5 — Critical** | Production-breaking bugs, real security risks, data-loss potential, broken builds | Workflow uses unquoted `${{ github.event.issue.title }}` in `run:` (script injection); raw `ANTHROPIC_API_KEY` logged; Alembic migration without `downgrade()`; SQL constructed via f-string |
| **4 — High** | Significant code smells with concrete failure modes, test gaps for core paths, clear performance bottlenecks, or a high-impact exemplary gap | N+1 query in `core/database/repositories.py`; missing retry/timeout on a model call; `any` covering an entire MUI component tree; prompt file references a removed library; no dark-mode contrast on a primary surface |
| **3 — Medium** | Modernization, consistency, maintainability — non-urgent but real debt; medium-impact exemplary gap | Outdated 3.10-style typing where 3.14 idioms apply; inconsistent router naming; duplicated pydantic schemas; missing CONTRIBUTING.md |
| **2 — Low** | Cosmetic, comment-only, nit-level | Inconsistent docstring style; unused dev-only `print`; trailing whitespace not auto-fixed |
| **1 — Positive** | Patterns worth preserving (no action needed; informational) | Solid repository pattern in `core/database/`; well-isolated cache layer in `api/cache.py`; clean theme-token usage |

Auditors MUST self-check against this table before assigning a number; if unsure between two levels, choose the lower one.

#### Dimension Taxonomy (tag every finding with exactly ONE)

The dimension answers "which pillar of an exemplary repo does this finding move?" Pick the single best fit; do not multi-tag.

| Dimension | What it covers | Owns (typical auditors) |
|---|---|---|
| **security** | Auth, secrets, injection, CVEs, IAM, branch protection, data exposure | security, gcloud, github, infra |
| **speed** | Latency, CWV, bundle size, N+1, cold starts, caching, query plans | pagespeed, backend, db, gcloud |
| **looks** | Visual design, theme/dark-mode correctness, responsive layout, UX polish, design-system consistency, a11y *as user experience* | design, pagespeed (a11y/visual audits) |
| **modern** | Up-to-date deps & framework idioms, current language features, no deprecated APIs, modern tooling/CI, structured data | frontend, backend, infra, agentic, seo |
| **correctness** | Bugs, broken builds, data integrity, wrong behavior, failing/missing tests for core paths | backend, frontend, db, llm-pipeline, catalog |
| **maintainability** | Code smells, duplication, dead code, docs/repo-health, naming, agent ergonomics, hygiene | quality, agentic, observability, github |

When a finding plausibly fits two dimensions, prefer the one a reader would act on first (a slow query that is also a smell → **speed**; an insecure dependency that is also outdated → **security**).

#### Who meets a finding (tag every finding with exactly ONE)

`SEEN_BY` names the first outside reader who would meet the finding. It is a second axis next to importance, not a part of it: importance says how bad a thing is, `SEEN_BY` says how many people it greets.

| `SEEN_BY` | Who | Typical findings |
|---|---|---|
| **site-visitor** | Anyone who opens `anyplot.ai`, often for a minute or two | A layout break, a typo, a slow or failing page, a number that contradicts another page, a feature nobody can find |
| **repo-visitor** | Someone who opens the repository page: the README, the root listing, the releases, the PR, issue, and Actions tabs | A false README claim, a stale public report, a pull request open for months, a red Actions tab |
| **code-reader** | Someone who opens source files or docs and reads them like a review | A module of four thousand lines, a swallowed error, a doc that contradicts the code |
| **internal** | Only the maintainer or an operator | An IAM binding, a retention setting, a flaky job, a cost |

When unsure between two, choose the reader further from the site (the lower row). A security hole stays `internal` unless a reader of the code would spot it; its importance carries the weight.

#### Exemplary Repository Rubric (the target each auditor measures against)

Beyond "is anything broken?", each auditor should ask "what would the best repo in this space have that anyplot lacks?" and emit any high-value gap as a finding. A concise target per pillar:

- **Security (exemplary):** least-privilege everywhere; secrets only in Secret Manager with rotation; all `pull_request_target`/`issue_comment` workflows gated by `author_association` and never interpolate untrusted `${{ github.event.* }}` into `run:`/prompts; third-party actions pinned to SHA; zero High/Critical dependency CVEs; documented threat model (`SECURITY.md`).
- **Speed (exemplary):** all Core Web Vitals in the "good" bucket (field + lab); a tracked JS/CSS bundle budget; no N+1; indexes on every filtered/ordered column; warm Cloud Run (min-instances tuned to traffic); cache hit-rate observable.
- **Looks (exemplary):** a single coherent design system; dark + light mode both correct (contrast, no hardcoded colors, theme tokens only); responsive at mobile/tablet/desktop; consistent spacing/typography scale; polished empty/loading/error states; WCAG AA.
- **Modern (exemplary):** current language idioms (Python ≥3.14, React 19, MUI 9 patterns), no deprecated APIs, dependencies near-current, modern CI (caching, matrix, pinned actions), structured data / JSON-LD for content pages.
- **Correctness (exemplary):** green CI on every required check; meaningful test coverage on core paths; no swallowed errors; migrations reversible; spec→impl pipeline idempotent.
- **Maintainability (exemplary):** complete repo-health set (README, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY.md, issue/PR templates, `.editorconfig`); docs match code; no dead code; consistent naming; clean agent ergonomics (right-sized commands, fresh CLAUDE.md).

Exemplary gaps are tagged with the matching dimension and rated by impact/effort like any other finding. Do not invent low-value gaps to pad the rubric — only surface a gap if closing it would visibly move anyplot toward exemplary.

### Phase 2.5: Cross-Validation (Lead / Workflow stage)

Before synthesis, every finding with `IMPORTANCE >= 4`, and every finding with `IMPORTANCE >= 3` that a visitor of the site or of the repository page meets (`SEEN_BY: site-visitor | repo-visitor`), is peer-reviewed by a **different, domain-overlapping** reviewer (in Workflow mode this is a pipeline stage that spawns a domain reviewer carrying the partner lens; in team mode the Lead routes by message). This is a specialist peer-review with the **burden of proof on DROP** — a finding is dropped only on positive evidence it is a false positive, never merely because a budget-limited reviewer couldn't fully re-derive it. The domain routing — the reviewer must bring expertise the original auditor lacks, not just re-read:

   - Backend ↔ security / db / llm-pipeline (depending on the file)
   - Frontend ↔ design (theme/UX overlap) or observability (analytics paths) or quality (test gaps)
   - Chat-frontend ↔ frontend (shared hooks and components) or design (the chat's states) or public-lane (the server side of the wire format)
   - Quality ↔ agentic (commands and agent-facing docs) or backend (a doc statement about the code) or landing (how a stale doc reads in public)
   - Db ↔ backend (the call sites of a query) or infra (the migration job in CI)
   - Security ↔ infra (workflow triggers and permissions) or public-lane (the agent chat) or sandbox (model-written code) or gcloud (IAM and secrets)
   - Observability ↔ plausible (what fires at runtime) or backend (the emitting code) or public-lane (telemetry claims)
   - Agents ↔ sandbox (the code the data layer hands over) or public-lane (limits and sessions) or llm-pipeline (shared rules and prompts)
   - Sandbox ↔ security (escape classes) or agents (what reaches the validator)
   - Public-lane ↔ security (authentication, headers, abuse) or gcloud (the deployed limits and service accounts) or observability (telemetry claims)
   - Site ↔ design (the component behind a visual finding) or frontend (a broken page) or seo (what crawlers get)
   - Landing ↔ quality (README and docs accuracy) or github (tabs, runs, branches)
   - Design ↔ frontend (component code behind the visual issue) or pagespeed (a11y/visual lab audits)
   - Infra ↔ security (workflow injection / secret exposure) or github (workflow runs side) or gcloud (deploy-target side)
   - llm-pipeline ↔ infra (workflow side) or backend (SDK call site)
   - Agentic ↔ quality (commands/docs overlap) or infra (prompts and workflow integration)
   - Gcloud ↔ observability (logs/metrics overlap) or infra (deploy/workflow side) or security (IAM/secrets)
   - Github ↔ infra (workflow files) or quality (issue/docs hygiene) or security (branch protection, secret hygiene)
   - Plausible ↔ observability (event drift)
   - Pagespeed ↔ frontend (perf opportunities → component code) or design (visual/a11y → component code) or infra (caching/headers/Cloud Run config)
   - Seo ↔ frontend (missing meta/JSON-LD → component code) or infra (robots/sitemap/headers) or pagespeed (lab vs field Web Vitals)
   - Catalog ↔ db (FS/DB drift) or llm-pipeline (specs failing generation) or infra (sync workflow)

The reviewer responds with one of:
   - `KEEP` — finding stands as rated
   - `DOWNGRADE` — drop one importance level (with one-sentence reason)
   - `DROP` — false positive (with one-sentence reason)

`DROP` removes the finding; `DOWNGRADE` re-rates it (and may move it out of the cross-validation tier). The reviewer's reason is preserved in the synthesis notes (not the final report) for traceability. Every other finding skips cross-validation to keep the pass cheap, and the report's statistics say how many went unverified.

### Phase 3: Synthesis (Lead)

After all specialists report back and cross-validation has run:

1. **Collect** all findings (post cross-validation)
2. **Deduplicate** — merge identical issues found by different auditors; keep the highest IMPORTANCE, union the FILES, keep the dimension of the highest-rated copy, and keep the `SEEN_BY` nearest to the site (site-visitor before repo-visitor before code-reader before internal)
3. **Flag contradictions** — if two auditors disagree on the same file, surface that explicitly in the synthesis notes
4. **Mark what is already tracked** — match the findings against the open GitHub issues (`gh issue list --state open`, read-only) and, in an interactive session with the Todoist tools, against the owner's Todoist project Anyplot. A tracked finding keeps its row and its rating and gains `(tracked: #NNNN)` or `(tracked: Todoist)` in its hint, so the report shows what is new at a glance. Likewise drop a finding that restates one of the Exclusions.
5. **Confirm each finding's rating:**
   - **Importance** (1-5): see Severity Calibration table above
   - **Dimension** (1 of 6): see Dimension Taxonomy — every finding must carry exactly one
   - **Seen by** (1 of 4): see Who meets a finding — every finding must carry exactly one
   - **Effort**: S (<30min, 1 file, mechanical), M (1-3h, 2-5 files, local context), L (half day+, 5-15 files, design decisions), XL (multi-day, 15+ files, needs own plan)
   - **Auto-fix**: classify each finding as `ruff` (auto-fixable via `uv run --extra dev ruff check --fix`), `eslint` (`yarn lint --fix`), `format` (`uv run --extra dev ruff format`), `codemod` (mechanical rewrite that a small script could do), or `manual` (requires judgment)
6. **Compute Health Score (30-100)** — unchanged formula, trend-comparable across all prior reports:
   - Start at 100
   - Subtract: `min(70, 10 * critical_count + 3 * high_count + 1 * medium_count)`
   - Round to integer; clamp to `[30, 100]` (the cap on subtractions intentionally floors the score at 30 so that very-bad audits remain comparable to bad ones)
7. **Compute the Dimension Scorecard** — a per-pillar grade so the user sees exactly where anyplot is and isn't exemplary. For each dimension D in {security, speed, looks, modern, correctness, maintainability}, using only findings tagged D:
   - `penalty_D = min(70, 10 * critical_D + 3 * high_D + 1 * medium_D)` (same weights as Health Score)
   - `score_D = clamp(100 - penalty_D, 30, 100)`
   - Letter grade (deterministic): ≥95 `A+`, ≥90 `A`, ≥85 `A-`, ≥80 `B+`, ≥75 `B`, ≥70 `B-`, ≥65 `C+`, ≥60 `C`, ≥55 `C-`, ≥50 `D`, <50 `F`
   - A dimension with zero findings scores `A+` **but** annotate it `(no findings — limited by coverage)` if the auditors that own that dimension were `blocked`/`partial`, so a high grade is never mistaken for proven excellence.
8. **Build Quick Wins list:** every finding with `IMPORTANCE >= 4` AND `EFFORT == S`. This list answers "what should we tackle first?" and goes near the top of the report.
9. **Build the First impressions list:** every finding with `SEEN_BY: site-visitor` or `SEEN_BY: repo-visitor` and `IMPORTANCE >= 2`, site visitors first, then importance descending, then effort ascending. This list answers "what does an outside reader meet?" and follows the Quick Wins. A finding may appear in both lists and in its importance bucket.
10. **Sort** within each importance bucket: Effort ascending, then Auto-fix `ruff` / `eslint` / `format` / `codemod` / `manual` (auto-fixable first)
11. **Optional cross-auditor synthesis** — only when the relevant auditors all ran in this session and produced data:
   - **Deprecation candidates** (Catalog × Plausible × SEO): specs that show up as low-traffic in Plausible AND zero-impression in Search Console AND have low coverage / low quality in catalog → emit a single Medium-importance `maintainability` finding listing the candidate spec-ids with effort `M` and auto-fix `manual`.
   - **Web Vitals lab vs field divergence** (Pagespeed × SEO; Plausible carries no vitals since 2026-11-08): URLs where lab CWV passes but field CWV fails (or vice-versa) → emit one `speed` finding per affected URL, importance derived from how far off the field metric is.
   - **Exemplary-gap rollup** (any auditor): if multiple auditors flagged the same missing-best-practice theme (e.g. missing repo-health files, no JSON-LD anywhere, no bundle budget), merge into one rollup finding tagged with the dominant dimension.
   - These are computed from the auditors' findings, not by re-querying. If any required auditor is `COVERAGE: blocked`, skip that synthesis silently.
12. **Persist** the final report to disk:
   - Path: `agentic/audits/{YYYY-MM-DD}-{scope_slug}.md` (e.g. `agentic/audits/2026-07-15-all.md`; a `backend` run of the same day would be `2026-07-15-backend.md`, a `since=main` run `2026-07-15-since_main.md`)
   - **The report is public and is read out of context.** A report whose headline is a score and an open incident reads as the state of the repository for as long as it is the newest file here. Open it, right under the H1, with a status line that says what it is: `> **Status ({date}):** a snapshot of this date, not updated afterwards. Findings are fixed in later pull requests; the changelog after this date says which.`
   - Report an incident in the past tense of its own date ("was running on {date}"), never as "ongoing": the sentence outlives the incident.
   - **Build `scope_slug` deterministically from `$ARGUMENTS`:**
     - Empty / `all` → `all`
     - Single keyword (`backend`, `frontend`, `chat`, `chat-frontend`, `design`, `looks`, `ux`, `infra`, `quality`, `tests`, `llm`, `pipeline`, `db`, `database`, `security`, `sec`, `observability`, `obs`, `agentic`, `agents`, `sandbox`, `lane`, `public-lane`, `gcloud`, `gcp`, `github`, `gh`, `plausible`, `pagespeed`, `psi`, `seo`, `catalog`, `site`, `landing`, `showcase`) → that keyword verbatim
     - Directory path → replace `/` with `_`, drop leading/trailing `_`, lowercase (e.g. `core/database/` → `core_database`)
     - `since=<ref>` → `since_<ref>` with `<ref>` sanitized: replace any character not matching `[A-Za-z0-9._-]` with `_` (e.g. `since=feature/foo` → `since_feature_foo`, `since=HEAD~10` → `since_HEAD_10`)
     - Combinations (e.g. `backend since=main`) → join the parts with `_` (`backend_since_main`)
     - Final slug must match `^[A-Za-z0-9._-]+$`; if anything still doesn't match after the rules above, fall back to `all`
   - Also overwrite `agentic/audits/latest.md` with the same content
   - Create `agentic/audits/` if missing
13. **Output** the report (see Output Format below) inline AND confirm the persisted path
14. **Cleanup**: in team mode, send `shutdown_request` to all auditors, then `TeamDelete`. In Workflow mode, no cleanup is needed (the workflow self-terminates).

### Output Format

```markdown
# Audit Report: anyplot

**Date:** {date} | **Scope:** {scope} | **Mode:** {full | incremental since=<ref>, N files} | **Engine:** {workflow | team}
**Health Score:** {30-100} | **Baseline:** ruff: {N issues}, format: {status}
**Auditors:** {n} ran ({list}) | **Findings:** {total} | **Auto-fixable:** {n}/{total}
**External sources:** {only include lines that apply}
- GCP project: {project-id} (gcloud-auditor)
- Plausible site: {anyplot.ai} (plausible-auditor)
- PageSpeed analysisUTCTimestamps: {url → ts list} (pagespeed-auditor)
- Search Console mode: {full | structural-only} | freshness: {date} (seo-auditor)
- GitHub: {gh user / repo} (github-auditor, landing-auditor)
- Catalog: {n specs / n implementations} on the filesystem (catalog-auditor)
- Site: anyplot.ai, {n} page loads (site-auditor)

## Dimension Scorecard (how close to exemplary?)
| Dimension | Grade | Score | Findings (C/H/M) | Biggest lever |
|---|---|---|---|---|
| Security | {A+..F} | {30-100} | {c}/{h}/{m} | {one-line: the single highest-impact fix} |
| Speed | | | | |
| Looks | | | | |
| Modern | | | | |
| Correctness | | | | |
| Maintainability | | | | |

## Summary
{2-3 sentences: overall health, weakest pillar(s), biggest risks, shortest path to a more exemplary repo}

## Quick Wins (Importance ≥4 & Effort=S)
| # | Finding | Dim | Auto-fix | Files | Hint |
|---|---------|-----|----------|-------|------|
| 1 | {description} | {dimension} | ruff/eslint/format/codemod/manual | `{files}` | {one-line fix hint} |

## First impressions (what an outside reader meets)
| # | Finding | Seen by | Importance | Effort | Files | Hint |
|---|---------|---------|------------|--------|-------|------|
| 1 | {description} | site-visitor/repo-visitor | {2-5} | S/M/L/XL | `{files}` | {one-line fix hint} |

## Critical (Importance 5)
| # | Finding | Dim | Effort | Auto-fix | Files | Hint |
|---|---------|-----|--------|----------|-------|------|
| 1 | {description} | {dimension} | S/M/L/XL | ruff/eslint/format/codemod/manual | `{files}` | {one-line fix hint} |

## High (Importance 4)
| # | Finding | Dim | Effort | Auto-fix | Files | Hint |
|---|---------|-----|--------|----------|-------|------|

## Medium (Importance 3)
| # | Finding | Dim | Effort | Auto-fix | Files | Hint |
|---|---------|-----|--------|----------|-------|------|

## Low (Importance 2)
| # | Finding | Dim | Effort | Auto-fix | Files | Hint |
|---|---------|-----|--------|----------|-------|------|

## Positive Patterns (Importance 1)
- {good patterns to keep}

## Statistics
- Total: {N} | Critical: {n}, High: {n}, Medium: {n}, Low: {n}
- By Dimension: security {n}, speed {n}, looks {n}, modern {n}, correctness {n}, maintainability {n}
- By Reader: site-visitor {n}, repo-visitor {n}, code-reader {n}, internal {n}
- Effort: S {n}, M {n}, L {n}, XL {n}
- Auto-fix: ruff {n}, eslint {n}, format {n}, codemod {n}, manual {n}
- By Auditor: backend {n}, frontend {n}, chat-frontend {n}, design {n}, infra {n}, quality {n}, llm {n}, db {n}, security {n}, obs {n}, agentic {n}, agents {n}, sandbox {n}, public-lane {n}, gcloud {n}, github {n}, plausible {n}, pagespeed {n}, seo {n}, catalog {n}, site {n}, landing {n}
- Tracked already: {n} of {total} match an open issue or task
- Cross-validation: {n} reviewed, {n} dropped, {n} downgraded, {n} below the bar and unverified
- Coverage: {n} auditors complete, {n} partial, {n} blocked (auth/credentials missing — list which); per partial auditor, what `NOT_COVERED` names
```

### Exclusions (apply to ALL auditors)

Do NOT flag:
- **Solo Developer Policy**: Branch protection on `main` with `required_approving_review_count: 0` is an intentional project choice for solo development to avoid self-blocking. As long as Pull Requests are enforced and CI status checks are mandatory, this is the approved configuration.
- **No quickstart for a local copy of the site**: the owner decided against one (2026-11-04). People use the plots on the site or the code in the repository, so its absence is not a gap.
- Plot implementations in `plots/` (AI-generated, different style rules), and how a rendered plot looks: the `/audit-catalogue` skill audits the renders in rounds of its own
- Generated files or lock files (`uv.lock`, `yarn.lock`, etc.)
- Third-party code or `node_modules/`
- Issues already covered by pyproject.toml exclusions
- Past audit reports in `agentic/audits/` (don't audit your own output)
- Mechanical metadata in `alembic/versions/` headers (revision IDs, down_revision); the **content** of migrations is the db-auditor's responsibility

---

## Findings Schema (authoritative — prepended to every auditor as part of the Shared Rules)

Every finding, in every auditor, in every mechanism, carries these fields. This list is authoritative and supersedes any field enumeration in an individual auditor file.

| Field | Type | Notes |
|---|---|---|
| `FINDING` | string | Short title |
| `IMPORTANCE` | 1–5 | Severity Calibration table |
| `DIMENSION` | enum | one of `security \| speed \| looks \| modern \| correctness \| maintainability` (Dimension Taxonomy) |
| `SEEN_BY` | enum | one of `site-visitor \| repo-visitor \| code-reader \| internal` (Who meets a finding) |
| `EFFORT` | enum | `S \| M \| L \| XL` |
| `AUTO-FIX` | enum | `ruff \| eslint \| format \| codemod \| manual` |
| `FILES` | string(s) | comma-separated paths, or a non-file resource handle (`gcp:…`, `gh:…`, `plausible:…`, `psi:…`, `sc:…`, `site:…`) |
| `EVIDENCE` | string | primary evidence: `path:line` with a short verbatim quote, a screenshot path plus what is visible in it, or a read-only command plus its output. A finding without it is dropped in synthesis |
| `DESCRIPTION` | string | what's wrong (or what's missing vs. exemplary) and why it matters |
| `HINT` | string | one-line fix suggestion |

Every report also carries, once per auditor, `COVERAGE`, `READ` (the files, pages, or resources read in full or in large part), and `NOT_COVERED` (what in scope was not reached).

Text-protocol form (team mode) — one block per finding, preceded by the per-auditor `COVERAGE:`, `READ:`, and `NOT_COVERED:` lines (and any auditor-specific header):
```
COVERAGE: full | partial | blocked
READ: {files, pages, or resources read in full or in large part}
NOT_COVERED: {what in scope was not reached}
---
FINDING: {short title}
IMPORTANCE: {1-5}
DIMENSION: {security | speed | looks | modern | correctness | maintainability}
SEEN_BY: {site-visitor | repo-visitor | code-reader | internal}
EFFORT: {S/M/L/XL}
AUTO-FIX: {ruff | eslint | format | codemod | manual}
FILES: {comma-separated file paths or resource handle}
EVIDENCE: {path:line with a short quote, a screenshot path, or a command and its output}
DESCRIPTION: {what's wrong / missing and why it matters}
HINT: {one-line fix suggestion}
```
In Workflow mode the same fields are returned as validated JSON (see `audit.workflow.js`); the auditor does not hand-format the block.

## Specialist Prompts

Each auditor's full prompt lives in its own file under `agentic/commands/audit/`. The Lead reads the file for each active auditor and passes its content (prepended with the Shared Rules) as the spawn prompt. Editing one auditor's prompt does not touch the others, and the orchestration (`audit.workflow.js`) never needs to change.

| Auditor | Prompt file |
|---|---|
| `backend-auditor` | `agentic/commands/audit/backend-auditor.md` |
| `frontend-auditor` | `agentic/commands/audit/frontend-auditor.md` |
| `chat-frontend-auditor` | `agentic/commands/audit/chat-frontend-auditor.md` |
| `design-auditor` | `agentic/commands/audit/design-auditor.md` |
| `infra-auditor` | `agentic/commands/audit/infra-auditor.md` |
| `quality-auditor` | `agentic/commands/audit/quality-auditor.md` |
| `llm-pipeline-auditor` | `agentic/commands/audit/llm-pipeline-auditor.md` |
| `db-auditor` | `agentic/commands/audit/db-auditor.md` |
| `security-auditor` | `agentic/commands/audit/security-auditor.md` |
| `observability-auditor` | `agentic/commands/audit/observability-auditor.md` |
| `agentic-auditor` | `agentic/commands/audit/agentic-auditor.md` |
| `agents-auditor` | `agentic/commands/audit/agents-auditor.md` |
| `sandbox-auditor` | `agentic/commands/audit/sandbox-auditor.md` |
| `public-lane-auditor` | `agentic/commands/audit/public-lane-auditor.md` |
| `gcloud-auditor` | `agentic/commands/audit/gcloud-auditor.md` |
| `github-auditor` | `agentic/commands/audit/github-auditor.md` |
| `plausible-auditor` | `agentic/commands/audit/plausible-auditor.md` |
| `pagespeed-auditor` | `agentic/commands/audit/pagespeed-auditor.md` |
| `seo-auditor` | `agentic/commands/audit/seo-auditor.md` |
| `catalog-auditor` | `agentic/commands/audit/catalog-auditor.md` |
| `site-auditor` | `agentic/commands/audit/site-auditor.md` (its browser helper: `agentic/commands/audit/site-shots.mjs`) |
| `landing-auditor` | `agentic/commands/audit/landing-auditor.md` |

**Spawn pattern (Lead):** for each active auditor, Read the corresponding file and use its full contents as the task prompt. Prepend the **Shared Rules** (depth and budget, limits on production and the live site, Severity Calibration, Dimension Taxonomy + tagging rule, who meets a finding, Exemplary Repository Rubric, read-only / degraded-mode contract, Exclusions, Findings Schema) so each spawned subagent has the full context without the per-auditor file having to repeat them. The auditor files describe scope and how-to-work; the orchestrator (this file) owns the cross-cutting rules.

**Adding a new auditor:** create `agentic/commands/audit/<name>-auditor.md`, add a row to the active-set table in Phase 1 (with its default dimensions and its model) + a Scope-Table entry + a cross-validation routing line + a Statistics-line key in Phase 3 + the slug keyword in the Persist step + a row above, and update the count in the summary at the top and in the `all` rule. No code changes required — `audit.workflow.js` is generic and reads the roster from `args`.

**When the repository changes shape** (a directory moves, a service or a route is renamed, a new top-level area appears), the auditor files go stale silently: an auditor that is pointed at a path that no longer exists reports nothing about it. Before a full run, check each auditor file's paths against the tree (`git ls-files`), and check that every top-level directory with code has an auditor in the active-set table.
