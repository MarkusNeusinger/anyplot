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
- **The data panel shows what the assistant changed, with `.undo()`.** After every
  parse that stores a dataset (a paste, or a transcription's `.use()`) the page asks
  for the step-1 summary, so the assistant's description of the data is the first
  turn in the thread, and the composer takes data requests ("read Anteil as numbers",
  "sum per month") before the confirmation. A turn whose `done` carries a new data
  version replaces the preview, the profile and the bindings, takes the page back to
  step 1 and shows a `# changed` block above the preview with one line per operation
  and `.undo()`, which restores the version before, unconfirmed and without a new
  summary. Two enum-only analytics events count it, `agent_data_prepared{changes}`
  and `agent_data_undo{version}`.
- **The mock BFF plays the data changes.** `app/scripts/agent-bff-mock.mjs` answers
  `summarize_data` with a scripted summary, plays a `set_type`, an `aggregate` (by the
  column the message names, such as "gruppier nach x") or a `rename` on messages that
  ask for percentages, grouping or a rename, carries the new version in
  `done.dataset`, and restores it through the undo route.

### Changed

- **Step-1 turns skip the run queue's minute rule.** A turn that starts while the
  data is unconfirmed cannot render (the pipeline answers `not_ready`, and nothing can
  confirm the data during a turn), so the queue gives it the slot but counts no start
  in the sliding window: the summary after a paste, a data request and the plot that
  follows the confirmation no longer wait a minute for each other, while whole
  pipeline runs keep one start a minute (`agents/anyplot/run_queue.py`).
