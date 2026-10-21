---
name: gemini-task
description: Hand a credential-free coding task, from a small fix to a longer refactor, to Gemini through a GitHub issue labelled `gemini`. The owner works it with Gemini in his interactive Antigravity CLI (agy) session on a local branch, and Claude takes the branch over into a reviewed PR. Use when Claude routes implementation work to Gemini (write the issue), when Gemini is asked to pick up or continue a Gemini task (work it), or when a finished `gemini/*` branch is waiting (take it over).
---

# Gemini tasks

The owner runs Gemini 4 Argon interactively in the Antigravity CLI (`agy`) in
this repository. That is the ordinary, intended use of his account, and he
approves every command Gemini runs. Work flows in three steps:

1. Claude describes the task in a GitHub issue labelled `gemini`.
2. Gemini works it on a local branch in a dedicated clone.
3. Claude reviews the branch, ships it, and the owner merges.

Gemini never pushes, never writes to GitHub, and never touches gcloud or
production. Credentials and every write outside the machine stay with Claude.

Nobody automates around the agy login. Nothing extracts, copies or proxies the
agy token, and nothing calls Google endpoints with it. The Antigravity terms
(section 6) forbid third-party tools and proxies, and Google suspended accounts
for exactly that in 2026. Claude may still run `agy -p` read-only for second
opinions (the `zweitmeinung` user skill). Claude never runs `agy -p` with
`--dangerously-skip-permissions` on this machine: that would let Gemini run
commands unattended with the owner's credentials.

## 1. Claude: write the task

**Good Gemini tasks** need no credentials and no production access. They can be
verified by commands that run locally, and they suit both small and long work.
Examples:

- a bug fix with a reproducer,
- a refactor across many files with existing coverage,
- tests for untested modules,
- a docs page built from facts in the repository.

**Not for Gemini:**

- anything under `.github/workflows/` or `alembic/`, or in the plot catalogue
  under `plots/`,
- Cloud Build, GCS, the database, or secrets,
- changes whose only verification is a live deploy.

**Write the issue** in English and in Google style.

- Never write `@claude` in it: the util-claude workflow reacts to that mention.
- Never put secrets or personal data in it. The repository is public.
- Put the body in a private temp file, then create the issue:

```bash
gh issue create --label gemini --title "<imperative summary>" --body-file "$D/issue.md"
```

**Body template:**

```markdown
## Goal
One paragraph: the outcome, and why.

## Context
Repo-relative paths, related PRs or issues, and the facts Gemini cannot look up.

## Steps
- [ ] One checkbox per reviewable step; a long refactor gets several.

## Constraints
Scope boundaries, what must not change, and the repository rules that matter most here.

## Acceptance
The exact commands that must pass, and the behaviour to check by hand, if any.

## Decide yourself / report back
The routine choices Gemini makes and documents, and the questions it returns
instead of guessing.
```

Tell the owner the issue number. He works in a dedicated clone, never in the
checkout Claude uses. The clone holds no `.env`, so nothing in it can reach the
production database, and pushing is disabled. One-time setup:

```bash
git clone https://github.com/MarkusNeusinger/anyplot.git ~/projects/anyplot-agy
git -C ~/projects/anyplot-agy remote set-url --push origin no-push
```

Then, for each task:

```bash
cd ~/projects/anyplot-agy && agy --mode accept-edits
```

In this mode file edits are accepted without asking, and every command still
asks him. Then he types `/gemini-task <number>`, or tells Gemini to work on the
issue.

## 2. Gemini: work the task

This section is for the Gemini agent in the owner's agy session.

1. **Read the task.** Use `gh issue view <number>`; with no number given, list
   the open tasks with `gh issue list --label gemini --state open` and ask the
   owner which one to take. Reading GitHub is fine. Never create, edit, comment
   on, label or close anything on GitHub.
2. **Work in the dedicated clone on your own branch.** That clone is
   `~/projects/anyplot-agy`; if you find yourself in any other checkout, stop
   and tell the owner. Use absolute paths throughout. To start a task:

   ```bash
   git fetch origin
   git switch -c gemini/<number>-<slug> origin/main
   ```

   To continue a task from an earlier session, switch to its branch, read
   `git log origin/main..HEAD`, and resume at the first open step.
3. **Set `PYTHON_DOTENV_DISABLED=1`** for every command, and never create or
   copy a `.env` into the clone.
4. **Implement one step at a time, inside the issue's scope.** The rules in
   `AGENTS.md` apply: English everywhere, files edited with your edit tool, no
   lint-disable comments, documentation updated with behaviour, and a changelog
   fragment under `changelog.d/` for any change that is not exempt.
5. **Run the acceptance commands and the gates for what you changed:**

   ```bash
   uv run ruff check . && uv run ruff format --check .
   uv run --extra typecheck mypy api core --pretty            # Python changes
   uv run pytest tests/unit tests/integration                 # or the narrower set the issue names
   cd app && yarn lint && yarn type-check && yarn test --run && yarn build   # app/ changes
   ```

6. **Commit each finished step** on your branch with a conventional message
   whose body ends with `Refs #<number>`. Do not push.
7. **Hand over** in the body of your last commit, under the heading `Hand-over`:
   - what changed and why,
   - the commands you ran and their results,
   - the decisions you made,
   - the steps still open,
   - your questions.

   Then tell the owner the branch name, and stop.

**Never** do any of these:

- `git push`, or any write through `gh`,
- any `gcloud` command,
- `alembic upgrade` against anything but a throwaway database,
- read or edit `.env`, or read files under `~/.config`,
- run the app or tests against the production database,
- install tools globally,
- merge or rebase other branches into yours.

## 3. Claude: take the branch over

1. **Fetch the work.** Bring the branch over from the clone into a fresh
   worktree of your own checkout. Fetching from a local repository runs none of
   its hooks or config.

   ```bash
   git fetch ~/projects/anyplot-agy gemini/<number>-<slug>:gemini/<number>-<slug>
   git worktree add .claude/worktrees/gemini-<number> gemini/<number>-<slug>
   ```

   Read the hand-over with `git log origin/main..gemini/<number>-<slug>`. Open
   steps or questions go back to the owner first.
2. **Review independently.** Start a fresh Opus subagent and give it only two
   things: the issue's Acceptance section and
   `git diff origin/main...gemini/<number>-<slug>`. Leave out the brief's
   reasoning and Gemini's hand-over. It reports defects.
   - Add Fable for high-risk diffs: security, production data, sandboxing,
     privacy.
   - Gemini never reviews its own work.
3. **Fix, gate and ship.** Work in that worktree and rebase onto `origin/main`
   there. Fix what the review
   found, run the open-pr gates, then open the PR with `/pull_request`. The PR
   body says:
   - `Closes #<number>`,
   - that the change was implemented by Gemini 4 Argon in the owner's
     interactive agy session and reviewed by Claude.

   Follow the PR through as `/open-pr` describes; Copilot reviews last, as on
   every PR.
4. **Clean up.** After the merge, remove your worktree. Deleting a local
   branch needs the owner's OK, here and in the clone, like any branch deletion.
5. **Record the task in the ledger.**

## Ledger

Append one JSON line per task to `~/.claude/team-ledger.jsonl`, for example:

```json
{"date": "2026-10-21", "repo": "anyplot", "task": "#12345", "lane": "gemini-interactive", "claude_tokens": 41000, "outcome": "accepted", "rework_rounds": 1, "review_findings": 2, "note": "refactor, 14 files"}
```

- `claude_tokens` comes from the review subagent's completion notification plus
  the take-over work.
- `outcome` is `accepted`, `reworked` or `discarded`.

Gemini's own usage shows in the owner's agy quota and is not recorded here. The
ledger answers the question that matters: how many Claude tokens one accepted
change costs in this lane, compared with an Opus subagent doing the same work.
