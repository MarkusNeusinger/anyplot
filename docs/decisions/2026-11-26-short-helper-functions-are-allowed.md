# A plot script reads top to bottom, and short helper functions are allowed

- Date: 2026-11-26
- Proposed: the code criterion CQ-01 deducted a point for any function in a plot script ("no
  functions/classes"), and since 2026-11-25 the regen gate keeps the live file when any criterion
  falls below its re-score. In the first catalogue batch of 2026-11-26 it kept 10 of 117
  regenerations only on CQ-01, because the attempt had added helpers such as `skew_x` or `add_ref`;
  #14424 told the generator to add no helper as an interim rule.
- Decided: the script reads top to bottom, cell by cell, with no `main()` and nothing nested, and
  short helper functions are allowed. His words, translated from German: "I just don't want it to
  say only 'run main' at the bottom, with the rest nested somehow; the whole thing should read
  cleanly from top to bottom, cell by cell. Short helper functions are, I think, no deterioration
  there." The exact boundary is the agents' reading of his words, with the fixes of a second
  opinion that he adopted: four steps by how much of the drawing sits inside functions in total,
  from a short helper above its first use, which costs nothing, to the whole plot inside a
  `main()`, a builder, a class or a callback; a point for any Python class, because the agent
  chat refuses classes; and no score for what the library or the harness asks for, such as the
  muix component.
- Where: #14701
