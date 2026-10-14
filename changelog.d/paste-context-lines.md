### Added

- **The assistant reads the notes pasted with a table.** The lines the parser
  leaves out above and below a pasted table (a title, an export's metadata, a
  source line, "time is the date column, make it a line chart") are kept as
  `context_lines`, at most 2,000 characters, instead of vanishing. The dataset
  route runs the cells' pre-filter and then the scope judge on them; a refusal or
  an outage drops only the notes with a warning, stores the table and costs no
  strike. The kept notes reach the root fenced as `<user_notes>` with the
  `summarize_data` turn and through `get_dataset_profile`, travel with every data
  version, and show in the data panel as `# notes sent to the assistant`. The
  root uses them as context for the whole chat and acts on a clear request in
  them right away, the plot still waiting for the user's confirmation; the scope
  rubric and seven new scope-eval cases cover ordinary notes and an injection
  hidden among them. (#12168)
