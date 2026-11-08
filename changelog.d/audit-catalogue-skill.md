### Added

- **A project skill audits the live catalogue and repairs what the owner
  picks.** `audit-catalogue` turns the MUI X 9 night's ad-hoc loop into rounds.
  `select_candidates.py` selects pairs read-only, from thumbs-down votes (one
  per visitor session, split at the last update), low or capped stored scores
  and kept defects, stale library versions or GCS renders (checked with a
  cache-buster), agent-validator refusals, or a library sweep. An audit
  workflow looks at both renders, the spec and the merged review, and a
  skeptic tries to refute every high or medium finding. `build_page.py` turns
  what survives into a private Artifact page with ids the owner picks from.
  Only then do fixes happen in fresh worktrees, checked by `check_fix.py`
  (scope, header, validator, a local render for Python and JavaScript in a
  scrubbed environment). `dispatch.sh` adopts them from their full SHA, one
  bulk-generate run at a time, so it never cancels a pending run such as
  daily-regen's, and only under an OK bound to a token over the queue and its
  planned SHAs. R and Julia go through a forced regeneration, stale renders
  through a re-render from `main`, and spec causes through a spec issue that
  is filed only on the owner's OK. `verify_merged.py` then checks every merged
  pair on the live site: the code on `main` against the fix, the metadata,
  the database row, both renders and the API. (#12825)
