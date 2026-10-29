### Added

- **ggplot2 in "Use with my data", for the admin's live tests.** `RRuntime`
  (`agents/anyplot/render/runtimes/r.py`) serves ggplot2 on the R code profile:
  `plot.R` renders through the renderer's R row in exec mode under the
  preloaded exec filter, the export downloads as `plot.R` with `Rscript
  plot.R` in its header, and the registry picks a runtime by the library's
  language. The admin deploy names ggplot2 next to the six Python libraries,
  and its 80 % eval matrix gates the public release. ADAPTATION refuses a
  working form that keeps a dataset package (gapminder, palmerpenguins), and
  when R reads integers beyond 2^53 as the nearest double, the plot's first
  note names the columns and counts the cells, so no value changes unannounced.
  A scripted identity adaptation of a fixture renders 3200x1800 in both themes
  through the local Docker backend with `exec_deny: on`.
- **An adapter prompt per language.** `adapter.md` keeps the rules every
  language shares and names a slot wherever the code differs;
  `adapter_python.md` and `adapter_r.md` fill them. The R prompt teaches the
  placeholder `df <- load_user_data()`, column constants read through
  `.data[[...]]`, the protected statements, the packages the adapter may
  attach and what the validator refuses. The Python prompt is byte for byte
  the one before, which a test pins by its SHA-256.
- **ggplot2 eval fixtures.** The ten matrix specs for ggplot2 (60 cases, 420
  generated in all) with the smoke case `scatter-basic-ggplot2-renamed`; the
  eligibility sweep and the development fixture seed find each library's
  files under its language (325 ggplot2 files: 4 clean, 306 coupled, 15
  blocked).

### Fixed

- **The scope judge refused served libraries as another library.** Its
  rubric named matplotlib and seaborn as the only libraries the assistant
  adapts, so this plot in plotnine, altair, pygal, lets-plot or ggplot2, all
  served to the admin, could get the `other_library` pointer. The rubric now
  gets the served libraries from `AGENT_LIBRARIES` and the catalogue's others,
  grouped by language, and a question about the session's code is in scope in
  any served language. The adapter prompt's sentences that only matplotlib's
  probe makes true moved into the Python passages, so the R prompt says that
  the host gates judge an R render without a probe.
- **Agent result code highlighted in the wrong language.** The result card
  highlighted every version in the page's current language, so after a
  library switch a matplotlib version showed as R; it now takes the language
  of the version's own library.
