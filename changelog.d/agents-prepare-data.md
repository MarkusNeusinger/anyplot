### Added

- **The assistant changes your data in step 1, and you can undo it.** Ask in words
  to read a column as numbers or dates, drop a total row, sum per month, rename,
  sort or pivot, and the root agent's new `prepare_data` tool chooses from a fixed
  set of operations (`rename`, `drop_columns`, `drop_rows`, `set_type`, `aggregate`,
  `sort`, `pivot_longer`, `pivot_wider`, at most five per call) that the agents
  service applies with pandas to the stored canonical CSV (`agents/anyplot/data/prepare.py`)
  and stores as the next dataset version (`agents/anyplot/dataset_versions.py`, the
  last five kept). The model never writes data rows. The turn's `done` event carries
  the new version with one change line per operation, unconfirmed, and
  `POST .../dataset/undo` restores the previous version. `ToolSafety` validates the
  operations against the same models first; a condition value and a rename's name
  are the only tool arguments exempt from the link rule, because they are compared or
  written, never followed.
- **The step-1 summary.** The messages action `summarize_data` asks the assistant to
  describe the data in two to four sentences (rows, columns with types and units,
  missing values, percentages, the proposed bindings, one question when something
  is ambiguous) without the scope judge; the profile now carries `mean` and
  `median` for numeric columns, and the model-facing profile JSON leaves empty
  fields out.
- **The prep eval.** `python -m agents.evals.prep` drives 17 German and English data
  requests through `/v1` in process with the real model and scores the root's
  `prepare_data` calls by exact operation match, order-insensitive, with an 80 % gate
  (`agents/evals/fixtures/prep/`).
- **The mock BFF plays the data changes.** `app/scripts/agent-bff-mock.mjs` answers
  `summarize_data` with a scripted summary, plays a `set_type`, an `aggregate` or a
  `rename` on messages that ask for percentages, grouping or a rename, carries the new
  version in `done.dataset`, and restores it through the undo route.
