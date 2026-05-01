# Chore Planning

Create a plan to complete the chore using the specified markdown `Plan Format`. Research the codebase and create a
thorough plan.

## Variables

run_id: $1
prompt: $2

## Instructions

- If the run_id or prompt is not provided, stop and ask the user to provide them.
- Plan the chore described in the `prompt`. This command produces a **plan only** — do NOT execute the chore here.
- Keep the plan simple, thorough, and precise. Avoid over-scoping (no extra modes or speculative steps).
- Create the plan at `agentic/specs/{YYMMDD}-{descriptive-name}.md` using today's UTC date (e.g.,
  `260501-update-readme.md`). Run `date -u +%y%m%d` if unsure.
- Research the codebase before writing the plan. For project layout, conventions, and tech stack, see
  `agentic/docs/project-guide.md` and read it only if needed.
- Replace every `<placeholder>` in the `Plan Format` with the requested value.

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
