# The generator checks the Data block outside Python in its contract self-check

- Date: 2026-11-27
- Proposed: The rubric change of #14701 made the review's CQ-01 criterion score code structure only, so a JavaScript, R or Julia file without the Data block layout its library prompt mandates no longer lost a review point, and these languages have no adaptability checker of their own. A batch check had measured that a library-prompt line that no check enforces reaches about half of the regenerated files, and a checked one nearly all. On the table was a rule in the generator's contract self-check that checks the layout statically.
- Decided: He decided "Per Self-Check": the generator's contract self-check enforces the layout, with a `data-block` rule for ggplot2, makie and the five JavaScript libraries. The session that built it settled the details: must-fix like the other library mandates, and only what the spec's data shape needs, as the Python checker waives it.
- Where: #NNNNN
