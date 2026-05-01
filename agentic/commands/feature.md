# Feature Planning

Create a plan to implement the feature using the specified markdown `Plan Format`. Research the codebase, understand
existing patterns, and create a thorough implementation plan.

## Variables

run_id: $1
prompt: $2

## Instructions

- If the run_id or prompt is not provided, stop and ask the user to provide them.
- Understand the feature requirements from the `prompt` and research existing patterns in the codebase to ensure
  consistency. This command produces a **plan only** — do NOT implement the feature here.
- Create the plan at `agentic/specs/{YYMMDD}-{descriptive-name}.md` using today's UTC date (e.g.,
  `260501-add-plot-export.md`). Run `date -u +%y%m%d` if unsure.
- Research the codebase before writing the plan. For project layout, conventions, and tech stack, see
  `agentic/docs/project-guide.md` and read it only if needed.
- Replace every `<placeholder>` in the `Plan Format` with the requested value. Be specific about API shapes,
  component names, and file paths so a downstream agent can implement without guessing.

## Plan Format

```md
# Feature: <feature name>

## Metadata

run_id: `{run_id}`
prompt: `{prompt}`

## Feature Description

<describe the feature, its purpose, and expected behavior>

## Requirements

- <requirement 1>
- <requirement 2>
- <requirement 3>

## Relevant Files

### Existing Files to Modify

<list existing files that need changes with bullet points explaining why>

### New Files to Create

<list new files to be created with their purpose>

## Implementation Plan

IMPORTANT: Execute every step in order, top to bottom.

### 1. <Foundation Step>

- <specific action>
- <specific action>

### 2. <Core Implementation>

- <specific action>
- <specific action>

### 3. <Integration Step>

- <specific action>
- <specific action>

### 4. Add Tests

- <unit tests>
- <integration tests if needed>

## Validation Commands

Execute these commands to validate the feature:

- `uv run pytest tests/ -v` - Run test suite
- `uv run python -m py_compile api/**/*.py` - Check Python syntax
- `cd app && yarn build` - Build frontend
- <additional validation commands>

## Notes

<optional: design decisions, alternatives considered, or future enhancements>
```

## Feature

Use the feature description from the `prompt` variable.

## Report

Return the path to the plan file created.
