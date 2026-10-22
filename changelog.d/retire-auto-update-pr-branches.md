### Removed

- **The auto-update workflow for PR branches.** `auto-update-pr-branches.yml`
  merged `main` into every open PR with auto-merge after each push to `main`.
  The `main` ruleset's checks are not strict, so no PR needed it, and its
  merge commits, authored by `github-actions[bot]`, held each PR's CI at
  `action_required` until someone approved the runs by hand (eight times on
  one PR on 2026-10-22). Auto-merge now fires on the PR's own green head.
