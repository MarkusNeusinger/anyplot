# Workflow Prompts

Centralized prompt templates for GitHub Actions workflows that invoke
`anthropics/claude-code-action@v1`.

## How prompts are wired

Each workflow embeds a short `prompt:` block under the Claude action that does
two things:

1. Tells Claude to read the relevant prompt file from disk (the bulk of the
   instructions live there, version-controlled separately from the workflow YAML).
2. Lists per-run variables (`LIBRARY`, `SPEC_ID`, `PR_NUMBER`, `ATTEMPT`, …) as
   plain bullets that Claude treats as context — there is no `sed`-substitution
   step, the variables flow into the prompt YAML at workflow runtime via
   GitHub Actions templating.

Example (from `.github/workflows/impl-review.yml`):

```yaml
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

## Available Prompts

| File | Workflow | Purpose |
|------|----------|---------|
| `impl-generate-claude.md` | `impl-generate.yml` | Initial code generation for one (spec, library) |
| `impl-repair-claude.md` | `impl-repair.yml` | Repair after a rejected AI review (max 3 attempts) |
| `ai-quality-review.md` | `impl-review.yml` | Quality evaluation of a generated implementation |
| `report-analysis.md` | `report-validate.yml` | Triage and structure user-submitted issue reports |

## Variable Reference

Variables are documented per prompt file (most accept the same `LIBRARY`,
`SPEC_ID`, `LANGUAGE`, `ATTEMPT`, `PR_NUMBER` set). They are **not** substituted
by the workflow into the prompt body via `sed` — the workflow embeds them as
plain bullet lines and Claude reads them as context.

| Variable | Example | Notes |
|----------|---------|-------|
| `LANGUAGE` | `python` | Only `python` supported today; future multi-language work will derive per-spec |
| `LIBRARY` | `matplotlib` | One of the 9 supported libraries |
| `SPEC_ID` | `scatter-basic` | Matches `_SPEC_ID_RE` (lowercase alphanum + hyphens) |
| `PR_NUMBER` | `42` | Pull-request number under review |
| `ATTEMPT` | `1` / `2` / `3` | Repair attempt counter (1-indexed) |
| `BRANCH` | `implementation/scatter-basic/matplotlib` | Branch being worked on |

## Why External Prompts?

1. **Testability** — Prompts can be validated independently (see `tests/unit/prompts/`).
2. **Consistency** — Same instructions across `claude` and `claude_retry` steps in the same workflow.
3. **Maintainability** — Single place to update; workflow YAMLs stay short and readable.
4. **Version control** — Git history tracks all prompt changes (`git log -p prompts/workflow-prompts/`).
5. **Security** — Untrusted user input (issue body, branch name) is not interpolated into the prompt body; per-run variables are passed as plain bullets, not as templated values.
