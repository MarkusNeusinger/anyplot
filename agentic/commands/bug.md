# Bug Fix Planning

Create a plan to fix the bug using the specified markdown `Plan Format`. Research the codebase, identify the root cause,
and create a thorough fix plan.

## Variables

run_id: $1
prompt: $2

## Instructions

- If the run_id or prompt is not provided, stop and ask the user to provide them.
- Investigate the bug described in the `prompt`
- Identify the root cause before planning the fix
- Create the plan in the `agentic/specs/` directory with filename: `{YYMMDD}-{descriptive-name}.md`
    - Use today's date as YYMMDD prefix (e.g., "260207-fix-api-timeout.md")
- Research the codebase starting with `README.md`
- Replace every <placeholder> in the `Plan Format` with the requested value

## Codebase Structure

- `README.md` - Project overview and instructions (start here)
- `api/` - FastAPI backend
  - `main.py` - App entry point
  - `routers/` - API route handlers
- `app/` - React frontend (Vite + TypeScript)
  - `src/` - Source code
- `core/` - Shared Python modules
  - `config.py` - Configuration
  - `database/` - Database utilities, models, and repositories
- `plots/` - Plot specifications and implementations
- `tests/` - Test suites
- `agentic/` - Agentic Layer
  - `commands/` - Prompt templates
  - `workflows/` - Workflow scripts (`uv run`)
  - `specs/` - Generated plans

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
