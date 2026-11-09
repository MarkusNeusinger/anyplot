### Added

- **The review warns when the staged renders don't come from the code under
  review.** impl-generate and impl-repair stage `render.sha256` beside the
  PNGs: the sha256 of the implementation they rendered, with its `Quality:`
  header line reset to `pending`. impl-review compares it with the file at the
  PR head and, on a mismatch or a missing hash, posts a comment and a
  job-summary line. Warn-only for a first night: the review, its score, and the
  verdict stay as they were. The catalogue audit of 2026-11-08 traced 50
  findings to renders that didn't come from the merged code.

### Fixed

- **A repair can no longer send unchanged code back to review.** impl-repair
  fails unless its push changed the implementation file and the workspace holds
  the pushed file, and it fails without both theme renders, where it used to
  exit 0 and leave the previous renders under the repaired code. The crash
  comment names the gate that failed.
- **A generation whose branch was never pushed fails.** impl-generate used to
  check out `origin/main` instead, which put a regeneration's renders under
  the live implementation.
