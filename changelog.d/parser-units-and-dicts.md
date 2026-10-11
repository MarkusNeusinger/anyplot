### Added

- **The data field reads units, flat objects and Python literals without a
  model.** A column whose every cell carries the same unit (`65 %`, `15,6 h`,
  `€ 5`, `CHF 1.200`) is read as numbers, the unit moving into the column name
  (`Anteil (%)`) with a warning, so a pie chart's numeric role binds to a
  percent column pasted from a spreadsheet; a column where only some cells
  carry a unit, or two units, stays text. A JSON object of plain values and an
  array of `[category, value]` pairs become a two-column table (`category`,
  `value`; source format `json_pairs`). A Python literal, also behind an
  assignment such as `cat_day = {...}`, with single quotes, trailing commas,
  tuples and `True` / `False` / `None`, is read like JSON: `ast.literal_eval`
  evaluates literals only, a name or a call is refused, and a bracket count
  refuses more than 50 nesting levels before anything is evaluated, so a 200 KB
  nested blob never reaches the stack.
