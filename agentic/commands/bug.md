# Bug Fix Planning

Create a plan to fix the bug using the specified markdown `Plan Format`. Research the codebase, identify the root cause,
and create a thorough fix plan.

## Variables

run_id: $1
prompt: $2

## Instructions

- If the run_id or prompt is not provided, stop and ask the user to provide them.
- Investigate the bug described in the `prompt` — identify the root cause before planning the fix.
- This command produces a **plan only** — do NOT implement the fix here.
- Create the plan at `agentic/specs/{YYMMDD}-{descriptive-name}.md` using today's UTC date (e.g.,
  `260501-fix-api-timeout.md`). Run `date -u +%y%m%d` if unsure.
- Research the codebase before writing the plan. For project layout, conventions, and tech stack, see
  `agentic/docs/project-guide.md` and read it only if needed.
- Replace every `<placeholder>` in the `Plan Format` with the requested value. Keep it specific and actionable —
  vague plans produce vague fixes.

## Plan Format

```md
# Bug: <bug name>

## Metadata

run_id: `{run_id}`
prompt: `{prompt}`

## Bug Description

<describe the bug, symptoms, and when it occurs>

## Root Cause Analysis

<explain the root cause of the bug after investigating the code>

## Affected Files

Files that need to be modified to fix the bug:

<list files with bullet points explaining why each needs changes>

## Fix Strategy

IMPORTANT: Execute every step in order, top to bottom.

### 1. <First Fix Step>

- <specific action>
- <specific action>

### 2. <Second Fix Step>

- <specific action>
- <specific action>

### 3. Add/Update Tests

- <add test to prevent regression>
- <verify fix with existing tests>

## Validation Commands

Execute these commands to validate the fix:

- `uv run pytest tests/ -v` - Run test suite
- `uv run python -m py_compile api/**/*.py` - Check Python syntax
- <additional validation commands>

## Notes

<optional: edge cases, related issues, or follow-up work>
```

## Bug

Use the bug description from the `prompt` variable.

## Report

Return the path to the plan file created.
