### Fixed

- **A web table copied one cell per line, and an inline list such as
  `a:7,b:12,c:5`, are data now.** Both are shapes from the owner's live session.
  The page sent them to the chat as a message, the plot button stayed grey,
  and the assistant answered that it cannot read data from a message. The page
  now routes them as data (`routeInput.ts`, rules 12 and 13), and the server's
  parser reads them by code (`layouts.py`, source formats `cell_lines` and
  `pair_list`). The parser takes the header from a line split at ` · `, leaves
  out a label block below the rows, keeps a range such as `62–100` as one text
  cell, and adds a warning that says how it read the text. Short text of up to
  2,000 characters that is mostly values goes to the server's transcriber,
  which offers its table for `.use()`. Longer text counts only in a format the
  parser knows: the transcriber now reads at most 2,000 characters (4,000
  before), so long free text never reaches a model as data. A ratio, a time, a
  URL, code and prose stay messages. (#13019)
- **The plot button takes pasted data whenever Enter would.** One pure rule
  (`plotClick` in `plotChain.ts`) now decides both whether the button is
  active and what its click does, so the two can no longer disagree. With the
  admin's `all` pressed, a pasted table left `.plot_all()` inert and only Enter
  read it. Now the one click reads the table and opens the fan-out once it
  reads clean. A table typed over stored data is read first too, never plotted
  as the old data's fan-out or sent as a plot request. A table in the message
  box goes by the dataset's own limits, so a long one goes as data with Enter
  and with the button. (#13019)
