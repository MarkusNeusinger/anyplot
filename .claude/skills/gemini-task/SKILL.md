---
name: gemini-task
description: Hand a credential-free coding task worth an hour or more, up to a long refactor, to Gemini through a GitHub issue labelled `gemini`. The owner works it with Gemini in his interactive Antigravity CLI (agy) session; Gemini pushes a `gemini/*` branch and opens a draft PR, and Claude reviews the draft, marks it ready, and follows it through. Use when Claude routes implementation work to Gemini (write the issue), when Gemini is asked to pick up or continue a Gemini task (work it), or when a draft PR labelled `gemini` is waiting (take it over).
---

# Gemini tasks

The owner runs Gemini 4 Argon interactively in the Antigravity CLI (`agy`) in
this repository. That is the ordinary, intended use of his account. He decides
how much Gemini may run without asking; for a long task he lets it run the
tests and builds unattended (owner, 2026-10-22: he trusts it to keep to the
rules as he trusts Claude). Work flows in three steps:

1. Claude describes the task in a GitHub issue labelled `gemini`.
2. Gemini works it on a `gemini/*` branch in a dedicated clone, pushes the
   branch, and opens a draft PR. CI runs on the draft; the Copilot review does
   not, because the "Automated Copilot Code Review" ruleset skips drafts.
3. Claude reviews the draft and marks it ready, which starts Copilot, then
   follows the PR through. The owner merges.

On GitHub, Gemini writes only its own branch and its own draft PR. It never
merges, never marks a PR ready, and never touches gcloud or production. Every
other write outside the machine stays with Claude.

Nobody automates around the agy login. Only the owner starts agy, and he works
it himself. Claude never runs `agy`, not even read-only: Google's Antigravity
FAQ forbids running it from third-party coding agents such as Claude Code under
a consumer login, and a Google staff reply of 2026-10-16 confirmed that for the
unmodified binary. Nothing extracts, copies, or proxies the agy token, and
nothing calls Google endpoints with it (Antigravity terms, section 6). Claude's
second opinions call Gemini through Vertex AI instead (`/zweitmeinung`).

## 1. Claude: write the task

**Good Gemini tasks** need no credentials and no production access, can be
verified by commands that run locally, and are worth an hour of work or more.
Claude does a quick fix directly; the hand-over costs more than it saves there.
The longer Gemini is to run, the more planning goes in first: for a large task,
get a second opinion on the plan (`/zweitmeinung`) and write the owner's
decisions into the issue. Examples:

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
The exact commands that must pass, and the behavior to check by hand, if any.

## Decide yourself / report back
The routine choices Gemini makes and documents, and the questions it returns
instead of guessing.
```

Tell the owner the issue number. He works in a dedicated clone, never in the
checkout Claude uses. Two things keep production out of that session:

- the clone holds no `.env`,
- agy starts with a minimal environment, so no database setting or credential
  variable from the owner's shell reaches Gemini or the commands it runs.

One-time setup:

```bash
git clone https://github.com/MarkusNeusinger/anyplot.git ~/projects/anyplot-agy
```

Then, for each task:

```bash
cd ~/projects/anyplot-agy && env -i HOME="$HOME" USER="$USER" SHELL="$SHELL" PATH="$PATH" \
  TERM="$TERM" LANG="${LANG:-C.UTF-8}" PYTHON_DOTENV_DISABLED=1 agy --mode accept-edits
```

`env -i` passes only the variables named, so a `DATABASE_URL`,
`INSTANCE_CONNECTION_NAME`, or `GOOGLE_APPLICATION_CREDENTIALS` exported in the
owner's shell never reaches `core/database/connection.py` in a child command.
In this mode file edits are accepted without asking, and commands ask him
unless he allows them; for a long task he allows the acceptance commands and
the gates. Then he types `/gemini-task <number>`, or tells Gemini to work on
the issue.

## 2. Gemini: work the task

This section is for the Gemini agent in the owner's agy session.

1. **Read the task.** Use `gh issue view <number>`; with no number given, list
   the open tasks with `gh issue list --label gemini --state open` and ask the
   owner which one to take. Reading GitHub is fine. Your only writes are your
   own branch and your own draft PR (step 7); never create, edit, comment on,
   label, or close anything else.
2. **Work in the dedicated clone on your own branch.** That clone is
   `~/projects/anyplot-agy`; if you find yourself in any other checkout, stop
   and tell the owner. Use absolute paths throughout. To start a new task, and
   only then, fetch:

   ```bash
   git fetch origin
   git switch -c gemini/<number>-<slug> origin/main
   ```

   To continue a task from an earlier session, switch to its branch and bring
   in what Claude may have pushed to it with
   `git pull --ff-only origin gemini/<number>-<slug>`. Then run `git status`,
   `git log origin/main..HEAD` (full messages, not `--oneline`) and
   `gh pr view --comments` for the review comments, and resume at the first step
   no commit names as done.
3. **Keep production out.** The clone holds no `.env`; never create or copy one.
   Prefix Python commands with `PYTHON_DOTENV_DISABLED=1` as a second guard;
   each command runs in a fresh shell, so an `export` does not carry over. If a
   check needs a database, use a throwaway local one, as the
   `/verify-migrations` skill does. Never set `DATABASE_URL` or
   `INSTANCE_CONNECTION_NAME` to anything else.
4. **Implement one step at a time, inside the issue's scope.** The rules in
   `AGENTS.md` apply: English everywhere, files edited with your edit tool, no
   lint-disable comments, and documentation updated with behavior. A change
   that is not exempt adds a changelog fragment under `changelog.d/` without
   any `(#...)` reference; Claude adds the PR number later.
5. **Run the acceptance commands and the gates for what you changed:**

   ```bash
   PYTHON_DOTENV_DISABLED=1 uv run ruff check . && uv run ruff format --check .
   PYTHON_DOTENV_DISABLED=1 uv run --extra typecheck mypy api core --pretty     # Python changes
   PYTHON_DOTENV_DISABLED=1 uv run pytest tests/unit tests/integration -n auto  # or the narrower set the issue names
   PYTHON_DOTENV_DISABLED=1 uv run python -m tools.changelog check --base origin/main
   cd app && yarn lint && yarn fm:check && yarn type-check && yarn test && yarn build   # app/ changes
   ```

6. **Commit each finished step** on your branch with a conventional message.
   Its body names the step (for example `Step 2 of 5: …`) and ends with
   `Refs #<number>`, followed by a co-author trailer crediting yourself, the
   way Claude signs its commits. Fill in the name of the model you actually
   run as in this session; never copy a model name from an older commit:

   ```text
   Refs #<number>

   Co-Authored-By: Antigravity (<your current model name>) <noreply@google.com>
   ```

7. **Hand over** when you finish or stop, whether on a blocker or at the end of
   the session. Push your branch and open a draft PR, or update the one you
   opened before. Write the body into a temp file first. It carries
   `Closes #<number>` and lists:
   - what changed and why,
   - the commands you ran and their results,
   - the decisions you made,
   - the steps still open,
   - your questions.

   ```bash
   git push -u origin gemini/<number>-<slug>
   gh pr create --draft --label gemini --title "<type>: <summary>" --body-file <file>   # first hand-over
   gh pr edit <pr> --body-file <file>                                                   # later ones
   ```

   Then tell the owner the PR number, and stop.

**Never** do any of these:

- push to any branch but your own `gemini/*` branch, or force-push,
- write anything through `gh` beyond creating, editing, and commenting on your
  own draft PR; never `gh pr ready`, `gh pr merge`, or a label on anything else,
- any `gcloud` command,
- `alembic upgrade` against anything but a throwaway database,
- read or edit `.env`, or read files under `~/.config`,
- edit anything under `.git/`, including its config and hooks,
- run the app or tests against the production database,
- install tools globally,
- merge or rebase other branches into yours.

## 3. Claude: take the draft over

1. **Find the drafts.** When the owner says Gemini is done, or at the start of a
   session, list them with `gh pr list --draft --label gemini`. Read the PR body
   (the hand-over) and the CI results on the draft. Open steps or questions go
   back to the owner first.
2. **Check it out** into a fresh worktree of your own checkout:

   ```bash
   git fetch origin gemini/<number>-<slug>:gemini/<number>-<slug>
   git worktree add .claude/worktrees/gemini-<number> gemini/<number>-<slug>
   ```

3. **Review independently.** Start a fresh Opus subagent and give it only two
   things: the issue's Acceptance section and
   `git diff origin/main...gemini/<number>-<slug>`. Leave out the brief's
   reasoning and Gemini's hand-over. It reports defects.
   - Add Fable for high-risk diffs: security, production data, sandboxing,
     privacy.
   - Gemini never reviews its own work.
4. **Fix or send back.** Fix small defects yourself in the worktree and push
   them to the branch; Gemini pulls them before it continues. Larger ones go
   back as a PR comment (`gh pr comment`), and the owner tells Gemini to
   continue. Bring in a newer `origin/main` by merging it into the branch, never
   by rebasing a pushed branch.
5. **Ship.** Run the open-pr gates, add the PR number to the changelog
   fragment, and add one Summary bullet to the PR body: the change was
   implemented by Gemini 4 Argon in the owner's interactive agy session and
   reviewed by Claude. This is provenance for the reviewer, not a "Generated
   with" footer. Then `gh pr ready <pr>` starts the Copilot review; follow the
   PR through as `/open-pr` describes. Merge only on the owner's explicit OK in
   the session.
6. **Clean up.** After the merge, remove your worktree. Deleting a local
   branch needs the owner's OK, here and in the clone, like any branch deletion.
7. **Record the task in the ledger.**

## Ledger

Append one JSON line per task to `~/.claude/team-ledger.jsonl`, for example:

```json
{"date": "2026-10-21", "repo": "anyplot", "task": "#12345", "lane": "gemini-interactive", "claude_tokens": 41000, "outcome": "accepted", "rework_rounds": 1, "review_findings": 2, "note": "refactor, 14 files"}
```

- `claude_tokens` comes from the review subagent's completion notification plus
  the take-over work.
- `outcome` is `accepted`, `reworked`, or `discarded`.

Gemini's own usage shows in the owner's agy quota and is not recorded here. The
ledger answers the question that matters: how many Claude tokens one accepted
change costs in this lane, compared with an Opus subagent doing the same work.
