### Added

- **A feedback case's turn record keeps the shape of each tool call's
  arguments.** The record named the tool, the guards' verdict and the
  answer's code, but nothing of what a call asked for, so a triage had to
  infer a stored filter's condition from the user's words. Each call now
  carries closed codes of its typed arguments: per data operation its name
  and codes (an `aggregate`'s function and period, a `sort`'s direction),
  for a condition of a `keep_rows`, `drop_rows` or `blank` its test, the
  shape of its value (`iso_date`, `year_month`, `number`, `list`) and its
  column's kind in the current table, and for a plot run or a kept request
  whether a change request came, and counts. Never a value of the data, a
  column name, a bound, a text or an id: the record's models admit closed
  codes, booleans and bounded counts only, and a call's shape small counts
  only, which a test checks field by field. The case detail on `/debug`
  lists the shape under each call. (#13144)
