### Changed

- **The regen gate keeps a regeneration that trades one criterion for another.**
  A regeneration now replaces the live implementation only when each of the 24
  review criteria, design and library mastery included, scores at least its
  value in the same session's re-score of the live file (reason code
  `criterion_below` otherwise). The one-point score tolerance nets the criteria
  against each other, so a carrier's gain, such as the continuous-ramp upgrade
  that VQ-07 now rewards, could pay for a two-point loss elsewhere. An
  incomplete re-score or new review keeps the same way; a change request the
  review confirms applied lifts the floor for a criterion that fell, never for
  a missing score. The adapt route keeps its own floor, the technical items,
  because its renders are held identical, and now also turns off when the
  re-score leaves a technical item out. (#14255)
