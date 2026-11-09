### Fixed

- **The ggplot2, plotly and bokeh catalogue tests hold rules, not the counts of one day.** Four corpus tests
  pinned the catalogue as it stood on 2026-10-29 and 2026-10-31: the ggplot2 eligibility sweep (6 files with
  SECURITY findings), the ggplot2 conventions (1,322 theme tokens), the files the R SECURITY profile flags and
  the plotly and bokeh files that end on the pinned figure save (318 and 321). Two regenerations on 2026-11-09
  broke them: flowmap-origin-destination's ggplot2 file (#12862) dropped the `maps` package, and
  map-marker-clustered's bokeh file (#12859) saves `curdoc()` and screenshots the figure's element. Main never ran
  these tests, because a merge that changes only implementation files skips pytest, so every Python PR inherited
  the failure. The tests now check each file:
  - a ggplot2 file is blocked exactly when its spec is a map spec or the SECURITY profile flags it, and the
    sweep's counts, eligible share and Markdown row follow from those files;
  - the R SECURITY profile flags no file or rule beyond the known ones, and every `library()` of an unavailable
    package, every `<<-`, every URL string and every call of a denied name is a finding;
  - each detected ggplot2 convention (theme tokens, markers, column constants, the standard save target)
    matches a plain reading of the file's text;
  - every plotly and bokeh file ends on the pinned figure save or carries the normaliser's note on why not,
    every module-level save of the theme PNG or of a named plot is pinned, and a bokeh file left alone exports
    through a browser screenshot of its own.
