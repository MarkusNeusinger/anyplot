### Changed

- **Three plot-quality rules from the agent chat's live tests, in the shared
  style guide and rubric.** Ordered categories (Likert levels, grades, sizes)
  take ordered steps of one Imprint ramp in their natural order, with a red or
  green pole only on its matching side (VQ-07); labels that tell the reader
  nothing, such as "100 %" on every bar of a 100 % stacked chart, are clutter
  (VQ-03); axis and legend titles are text for a reader, not raw column
  identifiers (`Reaktionszeit_ms` → "Reaktionszeit (ms)", VQ-06), and a legend
  after a reshape names the level ("Q1"), not the full header (SC-04). They
  live in `prompts/default-style-guide.md` and `prompts/quality-criteria.md`,
  which the catalogue pipeline and the agent's adapter and reviewer both read,
  so one edit changes the rule for both; the agent prompts that used to exempt
  every column name as written now point at the shared rule.
