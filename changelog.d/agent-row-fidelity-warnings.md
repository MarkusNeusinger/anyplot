### Added

- **A binding warning with counts when a plot's key repeats.** For the 90 specs whose plot draws one value per
  key, such as a bar per category, a cell per pair or a point per x of each series, the binding check warns
  when the bound key columns hold fewer keys than the rows that need a mark, for example `x: column 'Length'
  holds 9 values in 27 rows`. The bindings route, `set_bindings` and the session block carry it, and the
  assistant offers the counted `aggregate` instead of letting the plot code average the rows without a count,
  as a persona-test line chart did with 27 measurements. Scatter, box, histogram, strip and other plots where
  repeats are the point never warn, and no default binding changes.
- **A server line in "what changed" for rows the plot cannot draw.** When a bound column of a mark has empty
  cells, the shipped plot's changes say how many rows draw no mark, per role, for example `2 rows without y
  ('Exam Score')`, for all 15 libraries. It counts only the required roles that place a mark, never a label, an
  optional role or a spec's shorter list beside the rows, such as event dates, and it leaves the status as it
  is.
