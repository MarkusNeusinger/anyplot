### Changed

- **The prep eval scores a case by the table its turn leaves.** The session's data version after the turn must
  equal the table the case's expected operations make from the same version through the same server code
  (`apply_and_parse`, the `generate_data` parse): the same columns in order, dtypes, row count and cells, numbers
  within a 1e-9 relative tolerance, rows in their order unless the case sets `row_order: "any"`. Another sequence
  that makes the same table now matches: guard 2a of #12599 had read `de-hard-kette-gesamtzeile` as a miss when
  the root left out a `drop_columns` that the `aggregate` made anyway. The exact operation match stays as the
  diagnostic `ops_exact`, and it still decides a case that expects no data call, a `run_data_code` case, a
  `refuse` case and a case with `strict_operations: true`. A miss names what differs (`table_miss`, columns at
  most, never a cell), `check_cases` refuses an expectation that leaves its table as it is, and a unit test runs
  every table-scored fixture with a root that makes exactly its operations.
