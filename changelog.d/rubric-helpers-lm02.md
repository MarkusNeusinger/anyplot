### Changed

- **A plot script may use short helper functions.** The code criterion CQ-01
  now asks for a script that reads top to bottom, cell by cell (imports, data,
  plot, save), and deducts a `main()` or other entry-point function, a class,
  a function that wraps the plot or the save, and nesting; a short helper
  above its first use, such as a skew-T transform, costs nothing. The rubric,
  the generator, the regeneration and repair prompts and the adaptable-code
  zones say so together, replacing the interim rule of #14424 that a fix adds
  no function. In the first catalogue batch of 2026-11-26, the regen gate kept
  10 of 117 regenerations only because a new helper cost CQ-01 a point.

### Fixed

- **Library mastery no longer credits what the spec's variant excludes.** A
  feature that is itself such an addition, such as range selector buttons on
  a `-basic` spec, earns no LM-01 or LM-02 credit, in the re-score of the live
  file exactly as in the review of the new one. A re-score had credited a
  wrong-variant area chart's range selector on LM-02, so the regen gate's
  criterion floor kept it over an attempt that had removed the extras.
