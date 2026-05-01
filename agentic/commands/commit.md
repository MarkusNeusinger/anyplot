# Commit

Follow the `Instructions` below to create a git commit with a properly formatted conventional commit message.

## Variables

run_id: $1
task_type: $2

## Instructions

- Generate a concise commit message using conventional commit format: `<type>: <message>`
- The `<type>` should match the task_type variable if provided, mapped as follows:
  - `feature` → `feat`
  - `bug` → `fix`
  - `chore` → `chore`
  - `refactor` → `refactor`
  - If no task_type is provided, infer the type from the changes
- The `<message>` should be:
  - Present tense (e.g., "add", "fix", "update", not "added", "fixed", "updated")
  - 72 characters or less for the first line
  - Descriptive of the actual changes made
  - No period at the end
  - Lowercase start
- Examples:
  - `feat: add CSV export to API endpoints`
  - `fix: resolve 404 error on /api/plots`
  - `chore: update dependencies to latest versions`
  - `refactor: simplify JSON parsing logic`

## Run

Run steps 1 and 2 in parallel; only proceed to staging once you have read the full diff.

1. Run `git diff HEAD` to read every change that will be committed.
2. Run `git status` to confirm the set of modified/untracked files.
3. Stage changes with `git add <specific files>` — never use `git add -A` or `git add .`, which can pull in
   `.env`, credentials, or large binaries by accident.
4. Run `git commit -m "<generated_commit_message>"` to create the commit. Do not pass `--no-verify`; if a
   pre-commit hook fails, fix the underlying issue and create a new commit (do NOT amend the previous one,
   since the failed commit was never written).

## Report

Return ONLY the commit message that was used (no other text).
