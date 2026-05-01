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

Run steps 1-3 in parallel; analyze the full output before drafting the PR body. Only push (step 4) once the
branch state matches what the PR description claims.

1. Run `git diff origin/main...HEAD --stat` to see changed files summary
2. Run `git log origin/main..HEAD --oneline` to see commits in this branch
3. Run `git branch --show-current` to get the current branch name
4. Run `git push -u origin $(git branch --show-current)` to push the branch (do NOT use `--force` or
   `--no-verify` unless the user explicitly asks for it)
5. Create the PR — non-draft, ready for review:

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

## Report

Return ONLY the PR URL that was created (no other text).
