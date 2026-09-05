### Fixed

- **A re-dispatched `impl-merge` run can finish the bookkeeping of a PR that is already merged** —
  the merge step has long treated "already merged" as success and continued to promotion,
  labels, issue close and the Postgres sync, which is the whole point of dispatching the
  workflow again after a run that crashed post-merge. It never got there: the completeness
  check before it fetched the PR branch, and `gh pr merge --delete-branch` had removed that
  branch at the merge, so the re-run died on `couldn't find remote ref`. Seen on #11295
  (2026-09-05): the GCP auth step failed 5 s after the squash, the images stayed in staging
  while the metadata on main already pointed at production, and the re-dispatch could not
  repair it. The check now reads the files from `origin/main` when the PR is merged — where
  the squash commit put them — and no longer tries to close a merged PR when they are absent. (#11307)
