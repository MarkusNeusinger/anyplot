# The chat reads a short list of date forms and says plainly when a cell fits none

- Date: 2026-11-19
- Proposed: a gate of shape rules in front of a general date reader, built so that nothing that had
  read before would stop reading. It had grown with every review round (173 pinned forms after
  five rounds) and was an open pull request.
- Decided: no growth of rules for every variant. Support a few, the most common forms, and when
  something looks like a date but fits none, say so directly instead of trying to fix everything; in
  his words, that causes more problems in the end than it helps. The open pull request was closed
  unmerged, and a conversion now reads exactly what the paste reads, with one reader. On the same day
  he added one form, a day with a written month and a year (`8 Nov 2026`), because his own live test
  had used it, and left two-digit years out.
- Where: #13199
