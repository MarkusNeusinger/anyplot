### Fixed

- **Approved specifications merge on their own again.** Since GitHub's
  2026-06-11 change, workflow runs on a pull request that `GITHUB_TOKEN` opens
  sit at `action_required` until a human approves them, so the spec PR that
  `spec-create.yml` opened never got the required checks and the merge job
  failed with "the base branch policy prohibits the merge". Claude now opens
  the spec PR as `claude[bot]` with the Claude GitHub App token, the pattern
  daily-regen's spec polish already uses, so CI runs without an approval. The
  merge job acts only on the repository owner's `approved` label and verifies
  the PR fail-closed — Claude app author, `specification/<id>` into `main`,
  the issue referenced, and a diff limited to the spec files
  (`automation/scripts/spec_pr_guard.py`) — before it enables auto-merge
  pinned to the verified head commit. It waits up to 15 minutes for the merge,
  then dispatches `sync-postgres.yml`, because a `GITHUB_TOKEN` merge triggers
  no `push` workflows, and only then labels the issue `spec-ready`. The shared
  `spec-merge-main` concurrency group, which cancelled queued batch approvals,
  is gone, and `auto-update-pr-branches.yml` leaves spec PRs alone so its
  `GITHUB_TOKEN` merge commit cannot stall their checks. (#11868)
