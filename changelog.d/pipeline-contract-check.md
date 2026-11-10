### Added

- **The review records whether an implementation keeps the generator's
  static contract.** impl-review runs `automation/scripts/contract_check.py`
  on the file at the PR head and, on a regeneration, on its predecessor: the
  mandated title tail, the theme read, the themed save target, no legacy
  brand colour, and no named library colormap. Record-only: it writes a
  job-summary line and a notice, and nothing reads the result yet. On `main`,
  919 of 4,863 files break the title rule and 143 the colormap rule, so the
  rules that become defect lines are chosen from the nightly records.

### Fixed

- **A render hash of other code can no longer sit beside new renders.**
  impl-generate and impl-repair remove an earlier `render.sha256` before they
  upload the renders and write the new one last, with three attempts. They
  used to remove it only after a failed write, and when that removal failed
  too, the old hash stayed beside the new renders.
- **One failed read of the render hash no longer reads as `unreadable`.**
  impl-review downloads `render.sha256` with three attempts, as it downloads
  the renders.
