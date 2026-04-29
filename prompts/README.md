# Prompts

Central prompt collection for all AI agents in the anyplot workflow.

## Concept

Instead of complex folder versioning: **One Markdown file per task**.
Git history shows all changes (`git log -p prompts/plot-generator.md`).

## Overview

| File | Agent | Task |
|------|-------|------|
| `plot-generator.md` | Plot Generator | Base rules for all plot implementations |
| `default-style-guide.md` | Plot Generator | Default visual style (colors, typography, layout) |
| `library/*.md` | Plot Generator | Library-specific rules (9 files) |
| `quality-criteria.md` | All | Definition of what "good code" means |
| `quality-evaluator.md` | Quality Checker | AI quality evaluation |
| `spec-validator.md` | Spec Validator | Validates plot request issues |
| `spec-id-generator.md` | Spec ID Generator | Assigns unique spec IDs |
| `spec-tags-generator.md` | Spec ID Generator | AI rules for spec-level tag assignment |
| `impl-tags-generator.md` | Quality Checker | AI rules for impl-level tag assignment |
| `templates/*.{md,yaml}` | Spec Validator | Starter templates for `specification.md` / `specification.yaml` |
| `workflow-prompts/*.md` | GitHub Actions | Workflow-specific prompts (see below) |

## Workflow Prompts

Located in `workflow-prompts/` — full instruction sets that the
`anthropics/claude-code-action@v1` step in each workflow tells Claude to read.
Variables are passed as plain text in the workflow's `prompt:` body (no
`sed`-substitution step).

| File | Workflow | Purpose |
|------|----------|---------|
| `impl-generate-claude.md` | `impl-generate.yml` | Initial code generation for one (spec, library) |
| `impl-repair-claude.md` | `impl-repair.yml` | Repair after a rejected AI review (max 4 attempts) |
| `ai-quality-review.md` | `impl-review.yml` | Quality evaluation of a generated implementation |
| `report-analysis.md` | `report-validate.yml` | Triage and structure user-submitted issue reports |

See `workflow-prompts/README.md` for the wiring pattern + per-variable reference.

## Usage in Workflows

```yaml
# Example: from .github/workflows/impl-review.yml
- uses: anthropics/claude-code-action@<sha>  # v1
  with:
    claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
    claude_args: "--model sonnet"
    prompt: |
      Read `prompts/workflow-prompts/ai-quality-review.md` and follow those instructions.

      Variables for this run:
      - LIBRARY: ${{ steps.pr.outputs.library }}
      - SPEC_ID: ${{ steps.pr.outputs.specification_id }}
      - PR_NUMBER: ${{ steps.pr.outputs.pr_number }}
      - ATTEMPT: ${{ steps.attempts.outputs.display }}
```

## Prompt Structure

Each prompt follows this pattern:

```markdown
# [Agent Name]

## Role
You are [description]...

## Task
[What the agent should do]

## Rules
[Specific instructions]

## Input
[What the agent receives]

## Output
[What the agent should deliver]
```

## Making Changes

1. Edit the file
2. Test (locally or via PR)
3. Commit with descriptive message

```bash
git commit -m "prompts: improve matplotlib color handling"
```

View old versions: `git log -p prompts/library/matplotlib.md`
