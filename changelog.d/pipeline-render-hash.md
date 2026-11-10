### Added

- **The review warns when the staged renders don't come from the code under
  review.** impl-generate and impl-repair stage `render.sha256` beside the
  PNGs: the sha256 of the implementation they rendered, with its `Quality:`
  header line reset to `pending`. impl-review compares it with the file at the
  PR head and, on a mismatch or a missing hash, posts a comment and a
  job-summary line. Warn-only for a first night: the review, its score, and the
  verdict stay as they were. Both workflows also record, warn-only, whether a
  render is older than the implementation file. The catalogue audit of
  2026-11-08 traced 50 findings to renders that didn't come from the merged
  code. (#13034)

### Fixed

- **A repair can no longer send unchanged code back to review.** impl-repair
  fails unless its push changed the implementation file and the workspace holds
  the pushed file, and it fails without both theme renders, where it used to
  exit 0 and leave the previous renders under the repaired code. The crash
  comment names the gate that failed. (#13034)
- **A generation whose code was never pushed fails.** impl-generate used to
  check out `origin/main` when the branch was missing, which put a
  regeneration's renders under the live implementation. It now also fails when
  the implementation file on the pushed branch isn't the file in the
  workspace, which is the case when an earlier run left its branch behind.
  (#13034)
- **The manual re-render script promotes only the renders.**
  `scripts/migrate_render_and_upload.py` copied everything in staging to
  production; it now copies the `plot-*` objects, as impl-merge does, so a
  staged `render.sha256` or `adapt/` record never reaches production.
  (#13034)
- **`regen_gate.py sanitize-source` keeps line endings.** It used to rewrite
  CRLF as LF, so a CRLF file was committed in a form other than the one
  rendered. (#13034)
