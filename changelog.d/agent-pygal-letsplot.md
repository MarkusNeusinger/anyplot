### Added

- **"Use with my data" can adapt and render pygal and lets-plot.** The agent
  network's Python runtime (`agents/anyplot/render/runtimes/`) now serves the
  catalogue's pygal and lets-plot files next to matplotlib, seaborn, plotnine and
  altair. pygal saves through `render_to_png` and `cairosvg.svg2png` for the PNG and
  `render_to_file` for the HTML, whose target and file type the validator pins
  because libcairo writes the PNG past the plot guard; lets-plot saves through
  `ggsave` with `path="."`. The validator gains both import surfaces, keeps
  cairosvg's CSS stack unreachable, rules pygal's `css=`, `js=` and `defs=` config,
  and admits lets-plot's tooltip and label builders' `.format` with literal
  arguments. The normaliser rewrites pygal's HTML writes to `render_to_file`,
  expands lets-plot's star import from a static copy of `lets_plot.__all__`, removes
  its `lets-plot-images` epilogue, and sets both libraries' canvas, because R2's
  pixel cap refuses the catalogue's 4800x2700 PNGs outright; its four new guard
  rules and a new target form also lift plotnine from 264 to 267 and altair from 269
  to 273 eligible files. The plot guard imports cairosvg before it is armed and lets
  cssselect2 compile pygal's CSS selectors; the renderer image installs both
  libraries and libcairo, and lets-plot's row runs with its own 2048 MiB address
  space and Arrow's system allocator, which its native rasteriser needs. 209 of 325
  pygal and 284 of 325 lets-plot files are eligible. The eval fixtures cover both
  libraries: 120 more generated cases (360 in all) and one smoke case each (16 in the
  smoke set). `AGENT_LIBRARIES` keeps its default `matplotlib,seaborn` until each
  library's eval matrix reaches 80 %.

### Changed

- **R2 refuses a render as blank only when 99.7 % of it is one colour, not 98 %.**
  The agent network's blocking PNG check (`agents/anyplot/render/png.py`) refused
  sparse but complete charts: 33 of the 195 eligible pygal renders and lets-plot's
  point-basic (98.38 %) are 98 % one colour or more, the sparsest pygal one 99.44 %.
  A bare canvas (99.93 %) or a title alone (99.78 %) still fails. The cutoff holds
  for every library, and it refuses nothing the old one accepted.

### Fixed

- **The validator no longer lets a renamed save, a rebound `THEME` or a match
  capture through.** In plotnine's profile a save name imported under another name or
  used as a value (`from plotnine import ggsave as keep`, `g = ggsave`,
  `[ggsave][0]`, `functools.partial(ggsave, plot)`) escaped the save rule, so the
  exported code could write anywhere. In the matplotlib, seaborn, plotnine and altair
  profiles a second binding of `THEME` (`THEME = "x/../../elsewhere"` after the theme
  block) moved every save the same way, because the save rule checks the target's
  form, not the value of `THEME`. And a `match` capture could rebind a name that
  plotnine's expression rule read as a fixed string, handing plotnine code to
  evaluate. Every profile now refuses the first as a `banned-call` and any binding of
  `THEME` but its theme block as a `savefig-target`, and the expression rule counts a
  match capture as a binding.
