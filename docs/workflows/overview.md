# Workflow Overview

## How anyplot Automation Works

anyplot uses GitHub Actions to automate the entire plot lifecycle: from specification creation to implementation generation, quality review, and deployment.

---

## The Two Main Pipelines

### 1. Specification Pipeline

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

### 2. Report Pipeline

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

### 3. Implementation Pipeline

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
       |-- Score >= 90 --> [ai-approved] --> impl-merge.yml
       |                                        |-- Squash merge
       |                                        |-- Promotes GCS: staging --> production
       |                                        |-- Triggers sync-postgres.yml
       |
       |-- Score < 90 --> [ai-rejected] --> impl-repair.yml (max 3 attempts)
                                               |-- Reads AI feedback
                                               |-- Fixes implementation
                                               |-- Re-triggers impl-review.yml
```

---

## Label System

### Specification Labels (on Issues)

| Label | Meaning | Set By |
|-------|---------|--------|
| `spec-request` | New specification request | User |
| `spec-ready` | Specification merged, ready for implementations | Workflow |

### Implementation Labels (on Issues)

| Label | Meaning | Set By |
|-------|---------|--------|
| `generate:{library}` | Trigger generation for library | User |
| `impl:{library}:pending` | Generation in progress | Workflow |
| `impl:{library}:done` | Implementation merged to main | Workflow |
| `impl:{library}:failed` | Max retries exhausted | Workflow |

### PR Labels (on Pull Requests)

| Label | Meaning | Set By |
|-------|---------|--------|
| `ai-approved` | Quality check passed (score >= 90, or >= 50 after 3 attempts) | Workflow |
| `ai-rejected` | Quality check failed, triggers repair | Workflow |
| `ai-attempt-1/2/3` | Retry counter | Workflow |
| `quality:XX` | Quality score (e.g., quality:92) | Workflow |
| `quality-poor` | Score < 50, needs fundamental fixes | Workflow |

### Approval Labels

| Label | Meaning | Set By |
|-------|---------|--------|
| `approved` | Human approved specification | Maintainer |
| `rejected` | Human rejected | Maintainer |

### Report Labels (on Issues)

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

## Quality Workflow

- **Score >= 90**: Immediately approved and merged
- **Score < 90**: Repair loop (up to 3 attempts)
- **After 3 attempts**:
  - Score >= 50: Merge anyway
  - Score < 50: Close PR, mark as failed

---

## Key Principles

1. **Decoupled**: Each library runs independently (no single point of failure)
2. **Partial OK**: 6/9 implementations done = fine
3. **No merge conflicts**: Per-library metadata files
4. **Auto-sync**: Database updated on every merge to main
5. **GCS flow**: staging --> production only after merge

---

## Workflow Files

Located in `.github/workflows/`:

| Workflow | Purpose |
|----------|---------|
| `spec-create.yml` | Creates new specifications |
| `impl-generate.yml` | Generates single implementation |
| `impl-review.yml` | AI quality review |
| `impl-repair.yml` | Fixes rejected implementations |
| `impl-merge.yml` | Merges approved PRs |
| `bulk-generate.yml` | Batch implementation generation |
| `daily-regen.yml` | Cron-driven regeneration of the oldest implementations |
| `report-validate.yml` | Validates user-submitted issue reports |
| `sync-postgres.yml` | Syncs `plots/` filesystem state to PostgreSQL on push to main |
| `sync-labels.yml` | Auto-syncs spec/impl labels after manual PR merges |
| `ci-lint.yml` | Ruff lint check on PRs |
| `ci-tests.yml` | Unit + integration tests on PRs |
| `notify-deployment.yml` | Records GitHub deployment events for `app` / `api` |
| `util-claude.yml` | On-demand `@claude` utility (issue/PR comments) |

---

## Bulk Operations

```bash
# All libraries for one spec:
gh workflow run bulk-generate.yml -f specification_id=scatter-basic -f library=all

# One library across all specs:
gh workflow run bulk-generate.yml -f specification_id=all -f library=matplotlib
```

**Concurrency limit**: Max 3 parallel implementations globally.

---

## CLI Model Tiers

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

### Override Mappings

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
