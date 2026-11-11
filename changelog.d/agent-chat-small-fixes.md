### Fixed

- **Five small fixes in the chat, from the persona round of 2026-11-11.**
  Dropping rows now says when a number column is below 0 only in the rows
  that went, so its total over the rest is higher than before (cancelled
  invoices with negative quantities raised a total unnoticed). A condition
  `not_missing` finds the cells that have a value. A question about the data
  that answered an error no longer uses up the turn's three questions, and
  the refusal after them no longer names a tool or a limit, which the
  assistant had passed on. Text between two pairs of asterisks in a reply
  shows as strong text instead of asterisks, never inside a word or code.
  After the user rebinds a role by hand, the assistant reads that binding
  as the user's choice instead of calling its earlier words a mistake.
  (#13062)
