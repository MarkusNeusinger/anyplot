# Chore Planning

Create a plan to complete the chore using the specified markdown `Plan Format`. Research the codebase and create a
thorough plan.

## Variables

run_id: $1
prompt: $2

## Instructions

- If the run_id or prompt is not provided, stop and ask the user to provide them.
- Create a plan to complete the chore described in the `prompt`
- The plan should be simple, thorough, and precise
- Create the plan in the `agentic/specs/` directory with filename: `{YYMMDD}-{descriptive-name}.md`
    - Use today's date as YYMMDD prefix (e.g., "260207-update-readme.md")
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
# Chore: <chore name>

## Metadata

run_id: `{run_id}`
prompt: `{prompt}`

## Chore Description

<describe the chore in detail based on the prompt>

## Relevant Files

Use these files to complete the chore:

<list files relevant to the chore with bullet points explaining why. Include new files to be created under an h3 'New
Files' section if needed>

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers with bullet points. Start with foundational changes then move to specific changes. Last step should validate the work>

### 1. <First Task Name>

- <specific action>
- <specific action>

### 2. <Second Task Name>

- <specific action>
- <specific action>

## Validation Commands

Execute these commands to validate the chore is complete:

<list specific commands to validate the work. Be precise about what to run>
- Example: `uv run python -m py_compile apps/*.py` - Test to ensure the code compiles

## Notes

<optional additional context or considerations>
```

## Chore

Use the chore description from the `prompt` variable.

## Report

Return the path to the plan file created.
