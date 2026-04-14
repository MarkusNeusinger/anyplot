# Prompts

Central prompt collection for all AI agents in the anyplot workflow.

## Concept

Instead of complex folder versioning: **One Markdown file per task**.
Git history shows all changes (`git log -p prompts/plot-generator.md`).

## Overview

| File | Agent | Task |
|------|-------|------|
| `plot-generator.md` | Plot Generator | Base rules for all plot implementations |
| `library/*.md` | Plot Generator | Library-specific rules (9 files) |
| `quality-criteria.md` | All | Definition of what "good code" means |
| `quality-evaluator.md` | Quality Checker | AI quality evaluation |
| `spec-validator.md` | Spec Validator | Validates plot request issues |
| `spec-id-generator.md` | Spec ID Generator | Assigns unique spec IDs |
| `workflow-prompts/*.md` | GitHub Actions | Workflow-specific prompts (see below) |

## Workflow Prompts

Located in `workflow-prompts/` - templates for GitHub Actions workflows:

| File | Workflow | Purpose |
|------|----------|---------|
| `generate-implementation.md` | impl-generate.yml | Initial code generation |
| `improve-from-feedback.md` | impl-repair.yml | Code improvement after rejection |
| `ai-quality-review.md` | impl-review.yml | Quality evaluation |

See `workflow-prompts/README.md` for variable reference and usage.

## Usage in Workflows

```yaml
# Example: gen-new-plot.yml
- name: Generate matplotlib plot
  env:
    PROMPT_BASE: ${{ steps.load_prompts.outputs.base }}
    PROMPT_LIB: ${{ steps.load_prompts.outputs.library }}
  run: |
    claude --prompt "${PROMPT_BASE}

    ${PROMPT_LIB}

    ## Spec
    $(cat plots/${{ inputs.spec_id }}/specification.md)"
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
