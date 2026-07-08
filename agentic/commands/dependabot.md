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
- Per the changelog contract, individual Dependabot bumps get NO `CHANGELOG.md` entries —
  they are aggregated into one **Dependencies:** bullet at release time (`/release` step 2).

## Run

1. `git fetch origin main` and list: `gh pr list --author "app/dependabot" --json number,title,mergeStateStatus,statusCheckRollup`
2. Per PR, in order:
   - Checks green → `gh pr merge <num> --auto --squash`.
   - Checks pending on an up-to-date branch → enable auto-merge anyway; it fires when green.
   - **BEHIND branch**: update it via `gh api -X PUT repos/{owner}/{repo}/pulls/<num>/update-branch`
     (the installed `gh` has no `pr update-branch` subcommand). **Gotcha:** branch updates pushed
     with `GITHUB_TOKEN` (incl. `auto-update-pr-branches.yml`) do NOT trigger required checks —
     if checks stay `expected`/missing after the update, disable auto-merge, then
     `gh pr close <num> && gh pr reopen <num>` to re-trigger them.
   - `mergeStateStatus` is computed async — after any update, poll it a few seconds until it
     stabilizes before deciding (UNKNOWN → BEHIND/CLEAN/BLOCKED).
3. A dep bump breaking tests/config (e.g. a major with changed exports): consult **Context7**
   for the library's current API (CLAUDE.md MCP tools section) — do not grep `node_modules`
   `.d.ts` files. Fix on the Dependabot branch or note the PR for manual handling.
4. When all PRs have auto-merge set, **stop — do not leave a background monitor running.**
   Auto-merge needs no supervision, and orphaned monitors fire notifications into later
   sessions. Report the list with each PR's end state instead.

## Report

Per PR: number, title, action taken (auto-merge set / updated+re-triggered / needs manual
attention + why).
