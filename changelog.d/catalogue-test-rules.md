### Fixed

- **The catalogue corpus tests hold rules, not the counts of one day.** The corpus tests of the ggplot2, Makie,
  plotly and bokeh profiles, the Python theme-token check and the tree-sitter file gates pinned the catalogue as
  it stood between 2026-10-10 and 2026-10-31: file counts (325, 1,617), split counts (4 clean, 306 coupled, 15
  blocked), rewrite counts (34 dpi rewrites, 122 renamed keywords), lists of flagged files and of non-token theme
  conditionals. Two regenerations on 2026-11-09 broke four of them: flowmap-origin-destination's ggplot2 file
  (#12862) dropped the `maps` package, and map-marker-clustered's bokeh file (#12859) saves `curdoc()` and
  screenshots the figure's element. About 140 more regenerations were due the same night. Main never ran these
  tests, because a merge that changes only implementation files skips pytest, so every Python PR inherited the
  failure (#12877). The tests now check each file:
  - a file is blocked exactly when its spec is a map spec, the SECURITY profile flags it or its structure fails,
    and the sweeps' counts, eligible shares and Markdown rows follow from those files;
  - the SECURITY profiles flag no file or rule beyond the known ones, and every import of an unavailable
    package, every `<<-`, every URL string and every call of a denied name is a finding;
  - each detected convention (theme tokens, markers, column constants, the palette, the protected save) and
    each `data-block` and `deprecated-api` hint matches a plain reading of the file's text;
  - the normalisers make only their known rewrites, each where the text calls for it, and leave no catalogue
    header or title behind;
  - every plotly and bokeh file ends on the pinned figure save or carries the normaliser's note on why not, and a
    bokeh file left alone exports through a browser screenshot of its own;
  - every theme conditional built only from literals, `THEME` and the file's tokens is a token;
  - the parse gates read every merged implementation, the specs whose metadata names one.
