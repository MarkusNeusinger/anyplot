# Pull Request

Follow the `Instructions` below to create a pull request for the current branch.

## Variables

run_id: $1
plan_file: $2

## Instructions

- Generate a PR title using conventional format: `<type>: <short description>`
  - Keep the title under 70 characters
  - Use the same type conventions as commits (feat, fix, chore, refactor)
- The PR body should include:
  - A `## Summary` section with 1-3 bullet points describing the changes
  - A `## Plan` section linking to the plan/spec file if one exists
  - A `## Test plan` section with a checklist of how to verify the changes
- Extract context from the commits and changed files to write the summary
- Do NOT include any "Generated with..." or "Authored by..." lines

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
   pipeline PRs (`github-actions[bot]`: spec-create, impl-*, auto-polish, daily-regen) and
   Dependabot bumps — those are aggregated at release time — plus a PR labelled `skip-changelog`.
   This rule is duplicated in `CLAUDE.md` and `.github/copilot-instructions.md`; keep all three in
   sync.
5. Run `git push -u origin $(git branch --show-current)` to push the branch (do NOT use `--force` or
   `--no-verify` unless the user explicitly asks for it)
6. Create the PR — non-draft, ready for review:

```
gh pr create --title "<pr_title>" --body "$(cat <<'EOF'
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
   exception (a substantive rework) are in `CLAUDE.md` § "PR Follow-Through", step 3.

## Report

Return ONLY the PR URL that was created (no other text).
