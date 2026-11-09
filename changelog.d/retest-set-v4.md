### Added

- **Review retest set v4: the catalogue audit's pairs before their fixes.**
  `automation/retest/set-v4.yaml` holds 28 pairs from the catalogue audit of
  2026-11-08, frozen from the audit's pre-fix snapshot before that night's
  fixes replaced the production renders: 17 stand-ins for the plot type (a 3D
  spec drawn flat, a defining mark replaced, a map without real geography),
  dark-render misses, the three post-rework pairs whose review named the
  defect and merged anyway, and six controls that should keep their score.
  Sets v1 to v3 hold none of these pairs, so the audit's rule proposals
  (a stand-in scores SC-01 = 0, a named defect line blocks approval, a closer
  look at the dark render) had nothing to be measured on. Only on-canvas
  renders qualify, as the canvas gate sends no other render to a review. The
  workflow's `set` input takes `v4`; its 56 renders go up with the owner's
  one-time upload, and its labels stay drafts until the owner confirms them.
