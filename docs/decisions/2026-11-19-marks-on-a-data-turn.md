# A chat turn that changes the data names every plot axis it reassigned, and blocks nothing

- Date: 2026-11-19
- Proposed: a turn of the chat that changes the table can also put other columns on the plot's axes; in one of five
  test runs of one request the assistant did so unasked, and the page took the new bindings silently. Three options:
  show a line in the server's words for each reassigned axis; also keep a column on an axis that still has it; or
  run a second reader on every turn that changes the data.
- Decided: show the line and block nothing. The marks are a list that grows when needed. A second reader may come
  later, only on the marked turns, only if the count calls for it, counted first and behind a switch. His reasons:
  one unasked change in five test runs is thin; a good enough model or clear enough rules make a second reader
  unnecessary; and the assistant must not get more input than it has.
- Where: #13229
