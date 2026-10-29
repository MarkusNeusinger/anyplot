### Added

- **The R (ggplot2) code profile for "Use with my data", not served yet.**
  `agents/anyplot/code/profiles/r/` reads ggplot2 code with tree-sitter
  (`tree-sitter` 0.26.0 and `tree-sitter-language-pack` 0.13.0, whose
  bundled grammars need no download; the agents image keeps only the R
  grammar, 0.6 MB of 184 MB): the protected regions, a normaliser that
  strips the header, blanks the catalogue title and sets only the save's
  dpi for ragg's truncation (all 325 catalogue files land on 3200x1800 or
  2400x2400), the SECURITY and ADAPTATION validator with the named
  bypasses as tests, the readiness scan (4 clean, 306 coupled, 15 blocked;
  a missing marker never blocks), a readr loader typed from the data's
  kinds, which also count the integer cells past 2^53 a double would
  change, and an error grammar that never quotes R's message. A denied
  name is refused where it can run (a callee, a function argument, a
  value outside a data mask), so a user's column called `source` or
  `file` passes. The edit applier and the export header now take the
  language as a parameter, with Python's output unchanged; the runtime
  and the registry entry follow in the next step.
