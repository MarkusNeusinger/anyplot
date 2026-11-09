### Changed

- **Each `role: column` pair on the data card changes its own column.** The
  bindings line under the preview (`direction: day (UTC) · frequency: new
  chats`) only listed the bindings, and `.change()` at its end was easy to
  miss. Now each pair is a button with a dotted underline: a click opens the
  dropdowns with that role's dropdown focused and its list open, or a family's
  `+ y` focused. Escape inside the dropdowns closes them and returns the focus
  to the pair. While the dropdowns would not answer, during a step or with the
  fan-out's panel open, the pairs stay plain text. `.change()` still opens
  every dropdown. On a phone each pair is a 32 px target, and the rows of a
  line that wraps never overlap. (#13005)
