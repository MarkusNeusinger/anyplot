### Added

- **The data field reads JSON-stat datasets from statistics offices.** A
  JSON-stat 2.0 dataset as the Swiss BFS PxWeb API, Eurostat, Statistik Austria
  or Statistics Norway answer it (and a JSON-stat 1.x bundle of one dataset) is
  no longer refused as `unparseable`: the parser checks its sizes, categories and
  values strictly and flattens it into one long table, a column per dimension
  with more than one category, named by its label and holding the category
  labels, then `value`, in the dataset's own order (source format `json_stat`).
  The dimensions of one category, the dataset's title, source and notes become
  the notes pasted with the data, screened like any other note before the
  assistant reads them, so the table stays long and tidy and nothing of the
  dataset's context is lost.
