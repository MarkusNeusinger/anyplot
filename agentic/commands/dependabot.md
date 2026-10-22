# Dependabot Batch Processing

Safely process the open Dependabot PRs: verify, enable auto-merge per PR, and handle the
known GitHub quirks. Every gotcha below cost real session round-trips.

## Instructions

- **Never bulk-merge unverified.** Merging a batch of Dependabot PRs in one sweep without
  per-PR check verification is blocked by the permission classifier and cost ~7 recovery
  cycles once. Process per PR: verify checks, then enable auto-merge.
- Auto-merge is the mechanism of choice: `gh pr merge <num> --auto --squash` — the PR merges
  itself when checks pass; no polling needed.
- Grouped bumps (npm-minor, python-minor, actions) are one PR each — treat like any other.
- **One lock-file PR at a time, and every `app/` bump checked in the browser.** Of the PRs that
  touch the same lock file (`uv.lock`, `app/yarn.lock`), only one has auto-merge at a time: several
  squash-merged within a minute have duplicated package blocks in `uv.lock`. After an `app/` PR
  merges, wait for its `deploy-app` build and run the site smoke (`/open-pr` skill §4,
  `scripts/site-smoke.mjs`) before the next `app/` PR gets auto-merge. On 2026-10-22 vite 8.1.6
  (#12225) passed every check, blanked every page, and stayed unnoticed for about 45 minutes
  inside a batch. Comment `@dependabot rebase` on the next PR of a chain before you enable its
  auto-merge, and expect Dependabot to close and regroup a PR now and then ("updatable in another
  way"); list the PRs again when it does.
- Per the changelog contract, individual Dependabot bumps get NO `CHANGELOG.md` entries —
  they are aggregated into one **Dependencies:** bullet at release time (`/release` step 2).

## Run

1. `git fetch origin main` and list: `gh pr list --author "app/dependabot" --json number,title,mergeStateStatus,statusCheckRollup`
2. Per PR, in order:
   - Checks green → `gh pr merge <num> --auto --squash`.
   - Checks pending on an up-to-date branch → enable auto-merge anyway; it fires when green.
   - **BEHIND branch**: leave it alone. BEHIND does not block the merge — the `main` ruleset is
     not strict (`strict_required_status_checks_policy: false`), so auto-merge fires on a behind
     branch. **Never** run `gh api -X PUT .../pulls/<num>/update-branch` on a Dependabot PR: the
     resulting merge commit is authored by `github-actions[bot]`, GitHub then gates that head's
     workflow runs behind manual approval (`action_required`, so the checks never report), and
     Dependabot permanently stops rebasing a branch once a foreign commit lands on it. PR #9674
     burned 174 runs in 22 h this way, and #12229 collected eight such commits on 2026-10-22
     from `auto-update-pr-branches.yml`, which was retired for it.
   - **Already poisoned** (head commit authored by `github-actions[bot]`, checks stuck at
     `action_required`): approve the gated runs once —
     `gh api -X POST repos/{owner}/{repo}/actions/runs/<id>/approve`. Approved runs do report
     the required contexts on a bot-authored head (verified on #9674), and since no workflow
     updates PR branches any more (only `impl-merge.yml` updates its own `implementation/` PRs)
     the head stays put, so one approval is enough. `@dependabot recreate` also works and additionally restores a
     clean `dependabot[bot]` head, but it re-resolves the versions.
   - `mergeStateStatus` is computed async — after any update, poll it a few seconds until it
     stabilizes before deciding (UNKNOWN → BEHIND/CLEAN/BLOCKED).
3. A dep bump breaking tests/config (e.g. a major with changed exports): consult **Context7**
   for the library's current API (CLAUDE.md MCP tools section) — do not grep `node_modules`
   `.d.ts` files. Fix on the Dependabot branch or note the PR for manual handling.
4. When the last PR has merged and its deploys finished, run the site smoke once more
   (`/open-pr` skill §4). A failure is an incident: report it at once with the merges since the
   last passing run. Then **stop — do not leave a background monitor running.** Orphaned
   monitors fire notifications into later sessions. Report the list with each PR's end state
   instead.

## Report

Per PR: number, title, action taken (auto-merge set / updated+re-triggered / needs manual
attention + why), and the site smoke's result after the last merge.
