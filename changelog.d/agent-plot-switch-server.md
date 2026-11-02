### Added

- **The plot memory: your decisions about the plot, kept across a library switch.** The agents service
  keeps the decisions of each shipped change (a reference line, a formula as an annotation, outliers as
  red stars, an axis label, the x limits) as entries of a closed kind with library-neutral text, and every
  later plot hands them to the adapter and the reviewer, in any library. The root passes them with the
  run, since it cannot call a tool after a shipped plot, and the memory keeps them only once that plot
  ships. Only you clear it: `GET` and `DELETE /debug/agent/sessions/{sid}/memory[/{id}]` list the
  entries and remove one or all, and once the memory has held a decision, a removed one never comes
  back from the requests behind an earlier plot. (#12520)
- **A library switch carries the tuned plot over.** The switch now writes a carry (the theme you asked
  for, the texts the plot must show) and answers what would carry and whether to offer the plot in the
  new library; the `carry_plot` action makes that plot from the new library's catalogue code with your
  decisions, and checks the label in code. Versions are filed under their (spec, library) pair, so the
  later plot-type switch reuses the same path. `agents/evals/carry.py` checks the owner's five examples
  live from matplotlib to plotly and ggplot2. (#12520)

### Changed

- **A library switch keeps a request kept for the first plot.** The data and bindings it was written for
  stay, so it now waits for the first plot in the new library instead of being dropped. (#12520)
- **`.start_over()` keeps your remembered decisions.** It starts again from the catalogue code, the way
  out of code that went wrong, always on the catalogue base, and applies the plot memory to the new
  plot. (#12520)

### Fixed

- **A formula in a plotly plot is typeset.** The renderer's browser loads no MathJax, so a LaTeX string was
  drawn with its dollar signs; the plotly adapter now writes formulas with plotly's HTML tags
  (`ax<sup>2</sup>`), as the switch eval's first live run showed. (#12520)
