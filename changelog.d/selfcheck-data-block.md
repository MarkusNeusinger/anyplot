### Added

- **The generator's contract self-check checks the Data block of new R,
  Julia and JavaScript files.** `contract_check.py` gains a `data-block`
  rule for ggplot2, makie and the five JavaScript libraries, quoting each
  library prompt's "Data block" section: the `# Data` and `# Plot` markers
  (`//` in JavaScript), column constants with `# role:` comments above the
  block, and the `df` or `const data` the block binds. It asks only for what
  the spec's data shape needs, as the Python checker does, and reads the
  shape from the spec through the adaptability checker's mirror; map specs
  aren't judged. The review's CQ-01 criterion now scores code structure
  only, so the self-check enforces this layout instead of a review point.
  On a first generation the line must be fixed. On a regeneration
  (`selfcheck --regeneration true`, from the session's `IS_REGENERATION`)
  it's only reported, because a regeneration in these languages keeps its
  working data code. The review's record-only check lists it on every file;
  the record goes to version 3 and names the shape it used. On `main`, the
  rule flags 1,242 of 1,617 JavaScript files (5 of 323 in MUI X), 297 of
  325 R files and 305 of 325 Julia files. (#14730)
