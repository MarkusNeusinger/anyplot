### Fixed

- **The assistant knows that the data panel opens files.** Its list of the page's controls left out `.open()`,
  dropping or pasting a file, and the sheet and table dropdowns, and said the page had no upload, so a user who
  asked to load an Excel file was told it could not be done. The data panel's bullet in
  `agents/anyplot/prompts/root.md` now names them with the formats and size caps (CSV, TSV, JSON or plain text up
  to 1 MB; Excel, ODS, Parquet, Feather, Arrow or NumPy up to 5 MB), plus `.replace()`, `.keep()` and `.view_all()`
  with its full view's buttons, and the disclaimer under the list covers only the settings the page does not have.
  `tests/unit/agents/test_prompt_controls.py` now checks the other direction too: every button the data card
  renders is named in that bullet. (#12548)
