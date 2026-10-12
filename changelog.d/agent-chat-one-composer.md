### Changed

- **The agent chat has one composer.** The result card no longer carries its
  own `.refine()` box under the code: it duplicated the thread's composer, which
  already reads "ask about this plot, or ask for a change" and sends the same
  turn, and the assistant decides either way whether the text is a change or a
  question. The card keeps the image, the code, the downloads and the
  quick-feedback control; follow-ups go through the one box at the foot of the
  thread.
