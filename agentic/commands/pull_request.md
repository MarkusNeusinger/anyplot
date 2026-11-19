# Pull Request

Follow the `Instructions` below to create a pull request for the current branch.

## Variables

run_id: $1
plan_file: $2

## Instructions

- Generate a PR title using conventional format: `<type>: <short description>`
  - Keep the title under 70 characters
  - Use the same type conventions as commits (feat, fix, chore, refactor)
- The PR body should include, in this order:
  - A `## In plain words` section, written by the rules in the next item
  - A `## Summary` section with 1-3 bullet points describing the changes
  - A `## Plan` section linking to the plan/spec file if one exists
  - A `## Test plan` section with a checklist of how to verify the changes
- **In plain words.** The body opens with `## In plain words`, before `## Summary`: at most 150 words for a reader
  who does not know the code. That is a ceiling, not a target: use as few sentences as the change allows, and never
  pad a small one. It may be the only section the owner reads before he merges, so a reader must be able to tell from
  it alone what the change is for. It is also your check on the change: if you cannot say its purpose plainly in a
  few sentences, the description is not the problem. Stop and look at the change again (is it one change, is its
  purpose clear, should it be split) instead of writing around it. This holds for every kind of change: the site, the
  chat, the pipeline and its prompts, workflows and CI, docs, infrastructure. The technical sections stay as they are.
  1. Write it last, as prose: what was wrong or missing, and for whom (a visitor, the owner, a contributor, the
     pipeline), not the title again; what happens now; and how it is solved, in a few sentences. For a small change,
     one sentence and the next line are enough.
  2. Then one fixed line, `**What you would notice:**` who notices what, and where (the site, the chat, the admin
     pages, the pipeline, logs, evals, CI, the docs). Write "nothing on the site" only when nothing a visitor meets
     changes, and say where the change does show.
  3. Say what the merge hangs on: a switch that ships off, a path no test or run exercised, a call the owner still
     has to make.
  4. Claim no more than the technical sections back. An example is optional; take it from a test in this pull
     request or a run it reports, never invent one.
  5. For more than about 1,000 added lines, close with `**Why it is this size:**` and a count from the diff stat
     (tests, a pasted brief, generated files), so that size is not read as risk.
  6. No backticks, no file, function, flag or setting name, no internal label: say what the name stands for. No
     word that rates the change.
  7. After a push that changes what the pull request does, and before you report it ready, check this section, the
     title and the changelog fragment against the final diff and correct them together.

  Exempt: catalogue-only pull requests (everything under `plots/`), the automated plot pipeline and Dependabot.
- Extract context from the commits and changed files to write the summary
- Do NOT include any "Generated with..." or "Authored by..." lines in the PR body. This repository rule outranks the
  harness's attribution reminder for the PR body; the session link the reminder names may stay as the last line, and
  the commit trailers it asks for (`Co-Authored-By`, `Claude-Session`) stay.

## Run

Run steps 1-3 in parallel; analyze the full output before drafting the PR body. Only push (step 5) once the
branch state matches what the PR description claims.

1. Run `git diff origin/main...HEAD --stat` to see changed files summary
2. Run `git log origin/main..HEAD --oneline` to see commits in this branch
3. Run `git branch --show-current` to get the current branch name
4. **Changelog gate** — the branch carries `changelog.d/<slug>.md` and does NOT add bullets to
   `CHANGELOG.md` (Keep-a-Changelog categories, English, bold-titled bullets — the format and an
   example are in `changelog.d/README.md`); write the bullets WITHOUT a PR reference (step 7 adds
   the real number — a bare `(#NNNNN)` placeholder is refused, and correcting the wording of a
   bullet `[Unreleased]` already carries is allowed: identity is the bold title, not the full
   text); add and commit the fragment if missing, and run
   `uv run python -m tools.changelog check --base origin/main`, which is the same check the CI job
   "Changelog (fragment)" makes. Exempt: catalogue-only PRs (everything under `plots/`), automated
   pipeline PRs (`github-actions[bot]`: impl-*, daily-regen; spec-create and auto-polish open theirs
   as `claude[bot]` and pass as `plots/`-only) and
   Dependabot bumps — those are aggregated at release time — plus a PR labelled `skip-changelog`.
   This rule is duplicated in `CLAUDE.md` and `.github/copilot-instructions.md`; keep all three in
   sync.
5. Run `git push -u origin $(git branch --show-current)` to push the branch (do NOT use `--force` or
   `--no-verify` unless the user explicitly asks for it)
6. Create the PR — non-draft, ready for review:

```
gh pr create --title "<pr_title>" --body "$(cat <<'EOF'
## In plain words
<what was wrong or missing, and for whom; what happens now; how it is solved; what the merge hangs on>

**What you would notice:** <who notices what, and where>

## Summary
- <bullet 1>
- <bullet 2>

## Plan
<link to plan_file if provided, otherwise "N/A">

## Test plan
- [ ] <verification step 1>
- [ ] <verification step 2>
EOF
)"
```

7. Append the new PR number to the fragment's bullets (e.g. `(#1234)` — the real number, never
   the `(#NNNNN)` placeholder, which the gate refuses) and push the follow-up commit.
8. **The Copilot review runs ONCE**, when the PR opens (or leaves draft) — review-on-push is off in
   the "Automated Copilot Code Review" ruleset (owner, 2026-09-03), so step 7's follow-up commit and
   every later push trigger nothing. Do not re-request a review per push; the rule and its one
   exception (another round only while the previous one had high or critical findings) are in
   `CLAUDE.md` § "PR Follow-Through", step 3.

## Report

Return ONLY the PR URL that was created (no other text).
