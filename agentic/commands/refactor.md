# Refactor Planning

Create a plan to refactor the code using the specified markdown `Plan Format`. Research the codebase, understand the
current structure, and create a thorough refactoring plan that preserves all existing functionality.

## Variables

run_id: $1
prompt: $2

## Instructions

- If the run_id or prompt is not provided, stop and ask the user to provide them.
- Understand the refactoring goal from the `prompt`. This command produces a **plan only** — do NOT execute the
  refactor here.
- IMPORTANT: A refactor changes structure while preserving behavior. No functional changes allowed.
- Establish a test baseline BEFORE planning any changes — all tests must pass before and after.
- Create the plan at `agentic/specs/{YYMMDD}-{descriptive-name}.md` using today's UTC date (e.g.,
  `260501-extract-services.md`). Run `date -u +%y%m%d` if unsure.
- Research the codebase before writing the plan. For project layout, conventions, and tech stack, see
  `agentic/docs/project-guide.md` and read it only if needed.
- Replace every `<placeholder>` in the `Plan Format` with the requested value.

## Plan Format

```md
# Refactor: <refactor name>

## Metadata

run_id: `{run_id}`
prompt: `{prompt}`

## Refactor Description

<describe what is being refactored and why the current structure is insufficient>

## Current Structure

<describe the current file/module/class organization that will change>

## Target Structure

<describe the desired file/module/class organization after refactoring>

## Guard Rails

- All tests MUST pass before starting (baseline)
- No functional changes — behavior stays identical
- All tests MUST pass after every step
- All existing imports and public APIs must continue to work or be updated at all call sites

## Affected Files

### Files to Modify

<list existing files that need changes with bullet points explaining what changes>

### Files to Create

<list new files to be created with their purpose>

### Files to Remove

<list files that will be removed after their contents are moved, if any>

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Run Baseline Tests

- Run the full test suite and confirm all tests pass
- Record the test count as baseline

### 2. <First Refactor Step>

- <specific structural change>
- <update all references>
- Run tests to verify nothing broke

### 3. <Second Refactor Step>

- <specific structural change>
- <update all references>
- Run tests to verify nothing broke

### 4. Verify Final State

- Run full test suite — must match baseline pass count
- Verify no functional changes via `git diff` review

## Validation Commands

Execute these commands to validate the refactor is complete with zero regressions:

- `uv run pytest tests/ -v` - Run test suite (must match baseline)
- `uv run python -m py_compile api/**/*.py` - Check Python syntax
- `uv run ruff check .` - Lint check
- <additional validation commands>

## Notes

<optional: risks, edge cases, or follow-up work>
```

## Refactor

Use the refactor description from the `prompt` variable.

## Report

Return the path to the plan file created.
