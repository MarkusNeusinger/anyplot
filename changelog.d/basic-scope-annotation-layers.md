### Changed

- **`-basic` specs name reference lines, highlights and callouts in their variant bullet.** The 6 seeded
  and 7 bar-family `-basic` specs now list them, because the review and the regeneration read that list as
  complete: an unnamed mean line and callout survived a count-basic regeneration while a named cumulative
  line was removed. Each bullet is edited in place, keeps its `C` id and still names every exclusion it
  named before. A new style-lint warning (W7) flags a `-basic` variant bullet that leaves one out, and the
  spec template asks spec-create to name all three.
