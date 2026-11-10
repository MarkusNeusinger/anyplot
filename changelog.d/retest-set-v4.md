### Added

- **Review retest set v4: the catalogue audit's implementations before their
  fixes.** `automation/retest/set-v4.yaml` holds 28 implementations from the
  catalogue audit of 2026-11-08 as fresh items, frozen from the audit's
  pre-fix snapshot before the fixes of 2026-11-08/09 replaced the production
  renders: 17 stand-ins for the plot type (a 3D spec drawn flat, a defining
  mark replaced, a map without real geography), dark-render misses, the three
  regenerations whose review named the defect and merged anyway, and six
  controls that should keep their score. Sets v1 to v3 hold none of them, so
  the audit's rule proposals (a stand-in scores SC-01 = 0, a named defect line
  blocks approval, a closer look at the dark render) had nothing to be
  measured on. Only on-canvas renders qualify, as the canvas gate sends no
  other render to a review. The workflow's `set` input takes `v4`; its 56
  renders go up with the owner's one-time upload, and its labels stay drafts
  until the owner confirms them. (#12957)

### Fixed

- **The retest's `freeze` writes the lock only after a verified upload.** It
  wrote `set-v<N>.lock.json` before it uploaded, so a failed or partial upload
  left a lock behind, and a dry run with `--write-lock` wrote one for objects
  that weren't public. Either lock makes the prep job accept a set whose
  renders its bundle step can't download. `freeze` now writes the lock once
  every uploaded object matches it, and refuses `--write-lock` without
  `--execute`. (#12957)
