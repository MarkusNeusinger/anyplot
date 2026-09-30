### Changed

- **Implementations compute with the runtime's libraries, not by hand.** The
  generator prompt and the review criteria list what each runtime installs —
  numpy, pandas, SciPy, scikit-learn and statsmodels for Python, base `stats`
  and the ggplot2 stat layers for R, Statistics and the Makie recipes for
  Julia, each JavaScript library's own API — and ask for the shortest version
  that reads as well. The review deducts one CQ-04 point, never more, for a
  written-out algorithm an available call provides, or a block a named shorter
  form replaces, and names the call and the line range. A test keeps the two
  copies of the list identical and in step with `pyproject.toml`, the R setup,
  `Project.toml` and the JavaScript render harness. (#12005)
- **The regen gate has a code-only path.** When no improvement fixes a visible
  defect, a regeneration still replaces the live implementation if it fixes a
  `CQ-04 (code)` defect the previous review named, calls the named replacement
  or removes the named code, is shorter, scores CQ-04 higher, and regresses
  nothing. The gate reads both sources for it, and the record counts it as
  `improvements.code`. (#12005)
