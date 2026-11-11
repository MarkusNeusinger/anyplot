### Added

- **The review records whether an implementation keeps the generator's
  static contract.** impl-review runs `automation/scripts/contract_check.py`
  on the file at the PR head and, on a regeneration, on its predecessor. Six
  rules: the mandated title tail, the theme read, the themed save target, no
  legacy brand colour, no named library colormap, and no hex outside the
  style guide's palette. Record-only: it writes a job-summary line and a
  notice, and nothing reads the result yet. On `main`, 919 of 4,863 files
  break the title rule, 499 hold a hex outside the palette, and 151 use a
  library colormap, so the rules that become defect lines are chosen from the
  nightly records. The palette rule only records: a colour outside the
  Imprint palette is allowed when there is a very good reason. (#13045)

### Fixed

- **A render hash of other code goes before new renders arrive.**
  impl-generate and impl-repair remove an earlier `render.sha256` before they
  upload the renders and write the new one last, with three attempts. They
  used to remove it only after a failed write, and when that removal failed
  too, the old hash stayed beside the new renders. (#13045)
- **One failed read of the render hash no longer reads as `unreadable`.**
  impl-review downloads `render.sha256` with three attempts, as it downloads
  the renders. (#13045)
