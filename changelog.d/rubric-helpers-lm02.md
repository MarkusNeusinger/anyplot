### Changed

- **A plot script may use short helper functions.** The code criterion CQ-01
  now asks for a script that reads top to bottom, cell by cell (imports, data,
  plot, save), and scores it on four steps by how much of the drawing sits
  inside functions in total: a short helper above its first use, such as a
  skew-T transform, costs nothing, and the whole plot inside a `main()`, a
  builder, a class or a callback costs all three points. A Python class always
  costs a point, because the agent chat refuses classes. What the library or
  the harness asks for, such as the muix component or a Chart.js plugin, is
  not scored. The rubric, the generator, the regeneration and repair prompts
  and the adaptable-code zones say so together, replacing the interim rule of
  #14424 that a fix adds no function, and a stored review line that only asks
  to inline a short helper binds a regeneration no longer. In the first
  catalogue batch of 2026-11-26, the regen gate kept 10 of 117 regenerations
  only because a new helper cost CQ-01 a point.

### Fixed

- **Library mastery no longer credits what the spec's variant excludes.** A
  feature that is itself such an addition earns no LM-01 or LM-02 credit, in
  the re-score of the live file exactly as in the review of the new one. On a
  `-basic` spec that includes a control that changes what the chart shows,
  such as range selector buttons or a range slider, in the PNG or only in the
  HTML; hover, tooltips and zoom stay creditable. A re-score had credited a
  wrong-variant area chart's range selector on LM-02, so the regen gate's
  criterion floor kept it over an attempt that had removed the extras.
