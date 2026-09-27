# Workflow overview

## How anyplot automation works

anyplot uses GitHub Actions to automate the entire plot lifecycle: from specification creation to implementation generation, quality review, and deployment.

---

## The two main pipelines

### 1. Specification pipeline

```
Issue + [spec-request] label
       |
       v
spec-create.yml
  |-- Creates branch: specification/{spec-id}
  |-- Generates: specification.md + specification.yaml
  |-- Creates PR --> main
  |-- Posts analysis comment
       |
       v (maintainer adds [approved] label to Issue)
       |
spec-create.yml (merge job)
  |-- Merges PR to main
  |-- Adds [spec-ready] label
  |-- Triggers sync-postgres.yml
```

### 2. Report pipeline

See [Report Issues](report-issue.md) for details.

One unified template: **report-plot-issue.yml** - Report any plot problem (spec or implementation)

```
User reports issue (from anyplot.ai or GitHub)
       |
       v (report-pending label auto-added)
       |
report-validate.yml
  |-- Validates spec/impl exists
  |-- AI analyzes the issue
  |-- Posts structured analysis comment
  |-- Updates labels: report-validated + category:*
       |
       v
Ready for maintainer review (fix manually)
```

### 3. Implementation pipeline

```
Issue + [generate:{library}] label  OR  workflow_dispatch
       |
       v
impl-generate.yml
  |-- Creates branch: implementation/{spec-id}/{library}
  |-- AI generates code
  |-- Creates metadata/python/{library}.yaml (initial)
  |-- Tests execution
  |-- Uploads preview to GCS staging
  |-- Creates PR --> main
       |
       v
impl-review.yml
  |-- AI evaluates code + image
  |-- Posts review comment with score
  |-- Updates metadata/python/{library}.yaml (quality_score, review feedback)
  |-- Adds [quality:XX] label
       |
       |-- Meet Threshold --> [ai-approved] --> impl-merge.yml
       |                                        |-- Squash merge
       |                                        |-- Promotes GCS: staging --> production
       |                                        |-- Triggers sync-postgres.yml
       |
       |-- Below Threshold --> [ai-rejected] --> impl-repair.yml (max 4 attempts)
       |                                       |-- Reads AI feedback
       |                                       |-- Fixes implementation
       |                                       |-- Re-triggers impl-review.yml
       |
       |-- Regeneration (implementation already on main) --> regen gate, one review, no repair
                |-- Replace --> [regen:improved] + [ai-approved] --> impl-merge.yml
                |-- Keep    --> [regen:kept] --> PR closed, main and GCS unchanged
```

---

## Label system

### Specification labels (on Issues)

| Label | Meaning | Set By |
|-------|---------|--------|
| `spec-request` | New specification request | User |
| `spec-ready` | Specification merged, ready for implementations | Workflow |

### Implementation labels (on Issues)

| Label | Meaning | Set By |
|-------|---------|--------|
| `generate:{library}` | Trigger generation for library | User |
| `impl:{library}:pending` | Generation in progress | Workflow |
| `impl:{library}:done` | Implementation merged to main | Workflow |
| `impl:{library}:failed` | Set by `impl-generate.yml` after three failed generation attempts for the pair within a 12-hour window, or by `impl-review.yml` when the PR still scores below 50 after four repair attempts. Infrastructure failures (provider incident, cloud auth, GitHub API) are retried on a separate cap of 5 and never set this label; a pair paused that way carries no label. | Workflow |

### PR labels (on Pull Requests)

| Label | Meaning | Set By |
|-------|---------|--------|
| `ai-approved` | Quality check passed (based on cascading thresholds) | Workflow |
| `ai-rejected` | Quality check failed, triggers repair | Workflow |
| `ai-attempt-1/2/3/4` | Retry counter | Workflow |
| `quality:XX` | Quality score (e.g., quality:92) | Workflow |
| `quality-poor` | Score < 50, needs fundamental fixes | Workflow |
| `regen` | Regeneration of an implementation that is live on main (marker for humans and the watchdog; `impl-review.yml` decides "regeneration" from `origin/main`) | Workflow |
| `regen:forced` | Regeneration dispatched with `regen_gate=false`: bypasses the regen gate and takes the fresh-generation path | Workflow |
| `regen:improved` | The regen gate replaced the live implementation (added before `ai-approved`) | Workflow |
| `regen:kept` | The regen gate kept the live implementation; the PR is closed unmerged | Workflow |

### Approval labels

| Label | Meaning | Set By |
|-------|---------|--------|
| `approved` | Human approved specification | Maintainer |
| `rejected` | Human rejected | Maintainer |

### Report labels (on Issues)

| Label | Meaning | Set By |
|-------|---------|--------|
| `report-pending` | Report submitted, awaiting validation | Auto (template) |
| `report-validated` | AI validated, ready for review | Workflow |
| `report:spec` | Issue with specification | Workflow |
| `report:impl` | Issue with implementation | Workflow |
| `report:impl:{library}` | Specific library affected | Workflow |
| `category:visual` | Design/visual issues | Workflow |
| `category:data` | Data quality issues | Workflow |
| `category:functional` | Non-functional elements | Workflow |
| `category:other` | Other issues | Workflow |

---

## Quality workflow (cascading thresholds)

- **Review 1 (Initial)**: Score >= 90
- **Review 2 (Repair 1)**: Score >= 80
- **Review 3 (Repair 2)**: Score >= 70
- **Review 4 (Repair 3)**: Score >= 60
- **Review 5 (Repair 4)**: Score >= 50
- **Failure**: < 50 after 4 repairs -> close PR, mark as failed

The cascade applies to fresh generations only. A regeneration takes the regen gate below.

---

## Regen gate (regenerations)

A regeneration is an implementation PR for a (spec, library) pair that already has an implementation on main — for example every PR that `daily-regen.yml` produces. It gets one review and no repair loop, and the live implementation is replaced only when the new one is visibly better:

1. `impl-review.yml` detects the regeneration from `origin/main` (the implementation file exists there), downloads the predecessor's production renders to `prev_images/`, and writes the previous review with stable weakness ids `W1`..`Wn` to `/tmp/anyplot-prev-review.md`.
2. The review scores the new render blind, then re-scores the predecessor's renders against the same criteria and writes its before/after judgement to `review_regen.json` (step 5f of `prompts/workflow-prompts/ai-quality-review.md`).
3. `automation/scripts/regen_gate.py` decides. Replace requires all of:
   - new score >= re-scored predecessor - 1 (the stored score is display-only);
   - at least one improvement with a named, visible location;
   - no regressions. On a `*-basic` spec, a replaced data scenario or added encodings count as regressions unless a change request asked for them.
4. Replace: `regen:improved`, then `ai-approved`, then the normal merge. Keep: `regen:kept`, the PR is closed with a comment (stored, re-scored, and new score, improvements, regressions, reason), the issue gets `impl:{library}:done` back, and nothing reaches main, GCS production, or the database.

Anything missing or malformed — no `review_regen.json`, an unknown weakness id, missing previous renders, a failed canvas gate, a score of 0 — keeps the live implementation. The gate step logs one `::notice::regen_gate spec=… lib=… prev_stored=… prev_rescored=… new=… verdict=… reason=…` line per decision.

To replace an implementation without the gate, dispatch with `regen_gate=false` (`impl-generate.yml` or `bulk-generate.yml`): the PR is labelled `regen:forced` and takes the fresh-generation path, including the repair loop — whose exhaustion path removes the old implementation from main.

The local `/regen` command (`agentic/commands/regen.md`) is an owner override without the review gate; it only withholds `ai-approved` when the new score is more than one point below the stored score.

---

## Key principles

1. **Decoupled**: Each library runs independently (no single point of failure)
2. **Partial OK**: 6/9 implementations done = fine
3. **No merge conflicts**: Per-library metadata files
4. **Auto-sync**: Database updated on every merge to main
5. **GCS flow**: staging --> production only after merge

---

## Workflow files

Located in `.github/workflows/`:

| Workflow | Purpose |
|----------|---------|
| `spec-create.yml` | Creates new specifications |
| `impl-generate.yml` | Generates single implementation |
| `impl-review.yml` | AI quality review |
| `impl-repair.yml` | Fixes rejected implementations |
| `impl-merge.yml` | Merges approved PRs |
| `bulk-generate.yml` | Batch implementation generation |
| `daily-regen.yml` | Cron-driven regeneration of the oldest implementations (once a day at 02:17 UTC, off the top of the hour to dodge GitHub's scheduler overload). A spec's age counts from the newer of its last merged update and its last regen attempt (closed `regen` PRs), so a kept regeneration is not re-picked the next night |
| `watchdog-stuck-jobs.yml` | 6-hourly safety net: re-dispatches stuck reviews, repairs (including a repair that crashed after a rejection), merges and generations (straight to `impl-generate.yml`, marked only once the run exists), re-closes open `regen:kept` PRs, never rescues a regeneration into repair, and rescues daily-regen when its cron is silently starved by GitHub (>26 h without a run) |
| `report-validate.yml` | Validates user-submitted issue reports |
| `sync-postgres.yml` | Syncs `plots/` filesystem state to PostgreSQL on push to main |
| `sync-labels.yml` | Auto-syncs spec/impl labels after manual PR merges |
| `indexnow-submit.yml` | Pushes changed page URLs to IndexNow (Bing, Yandex, Seznam, Naver, Yep) on every push to main that touches `plots/`; a push that changes the workflow file itself or bumps `TEMPLATE_LAST_CHANGED` in `api/routers/seo.py` submits the full list, as does `workflow_dispatch` with `scope=sitemap` |
| `codeql.yml` | CodeQL scanning (actions, JavaScript/TypeScript, Python) on pushes to main, PRs and a weekly cron; `plots/**` is excluded from triggers and analysis, so pipeline PRs never start a scan |
| `ci-lint.yml` | Ruff lint check on PRs |
| `ci-tests.yml` | Unit + integration tests on PRs |
| `ci-image.yml` | Builds `api/Dockerfile` and smoke-tests the container before merge — `/health`, the reported version against `pyproject.toml`, the runtime stage's COPY payload, non-root uid — plus hadolint on both Dockerfiles. Skips when only `plots/**` or frontend sources changed |
| `notify-deployment.yml` | Records GitHub deployment events for `app` / `api` |
| `bot-serving-check.yml` | Daily synthetic monitor: curls the Cloud Run origin with crawler UAs and fails on non-200 or a page that is not the prerendered one. Routes are derived from the `@router.get("/seo-proxy/…")` decorators in `api/routers/seo.py` and the expected spec title from `plots/<spec>/specification.yaml`, so no literal here can go stale. A failure opens (or comments on) the fixed-title issue **Bot serving check is red**; the next green run closes it — the bot→seo-proxy path is invisible to human traffic and needs its own alarm |
| `util-claude.yml` | On-demand `@claude` utility (issue/PR comments) |

---

## Bulk operations

```bash
# All libraries for one spec:
gh workflow run bulk-generate.yml -f specification_id=scatter-basic -f library=all

# One library across all specs:
gh workflow run bulk-generate.yml -f specification_id=all -f library=matplotlib
```

**Concurrency limit**: Max 3 parallel implementations globally.

---

## CLI model tiers

The agentic workflows use abstract model tiers (`small`, `medium`, `large`) instead of CLI-specific model names. This allows the same command to work across different AI tools.

| Tier | Purpose | Claude | Copilot | Gemini |
|------|---------|--------|---------|--------|
| small | Fast/cheap tasks | haiku | gpt-4o-mini | gemini-2.0-flash |
| medium | Balanced tasks | sonnet | gpt-4o | gemini-2.0-flash-thinking |
| large | Complex tasks | opus | o1 | gemini-2.5-pro |

### Usage

```bash
# Use large tier (default for plan_build)
uv run agentic/workflows/plan_build.py "Add feature X" --model large

# Use medium tier with Copilot
uv run agentic/workflows/prompt.py "Quick fix" --model medium --cli copilot
```

### Override mappings

Override the default model for any tier via environment variables:

```bash
# Linux/WSL
export CLI_MODEL_CLAUDE_LARGE=claude-opus-4-7
export CLI_MODEL_COPILOT_MEDIUM=gpt-4-turbo

# Windows PowerShell
$env:CLI_MODEL_CLAUDE_LARGE = "claude-opus-4-7"
$env:CLI_MODEL_COPILOT_MEDIUM = "gpt-4-turbo"
```

All environment variable names follow the pattern: `CLI_MODEL_{CLI}_{TIER}`
