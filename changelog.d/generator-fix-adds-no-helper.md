### Changed

- **A regeneration's fix stays a top-down script.** The generator now reads
  that a fix in a regeneration or a repair round adds no function or class:
  repeated steps become a loop over their values or a few written-out calls.
  In the first catalogue batch of 2026-11-26, the regen gate kept 10 of 117
  regenerations only because a new helper function cost the KISS criterion
  (CQ-01) a point, one of them a repair round that had fixed 5 of 6 named
  defects and gained 12 points. (#14424)
