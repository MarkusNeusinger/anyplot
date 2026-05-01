# Task Classification

Classify the task description into exactly one category.

## Task

$ARGUMENTS

## Rules

Analyze the task and classify it:

- `bug` — Something is broken, errors occur, regressions, 404s, crashes, incorrect behavior, things that used to work
- `feature` — New functionality, additions, enhancements, new pages, new endpoints, new capabilities
- `chore` — Maintenance, cleanup, config changes, dependency updates, documentation, CI/CD, formatting
- `refactor` — Restructuring code while preserving behavior: extracting modules, reorganizing files, splitting classes, renaming for clarity, moving code between files

## Response

Respond with ONLY a JSON object on a single line. No preamble, no explanation, no markdown, no code fences. The
response will be passed directly to `JSON.parse()`, so any extra text breaks the caller.

Schema (one of `bug`, `feature`, `chore`, `refactor`):

{"type": "bug", "reason": "one sentence explaining why"}
