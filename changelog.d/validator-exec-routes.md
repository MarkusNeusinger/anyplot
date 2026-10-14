### Security

- **The agent chat's code validator closes exec and process routes through
  allowed modules.** It accepted `np.testing.measure("...")`, which compiles
  and runs any string. A survey of every public function and re-exported module
  of the admitted packages now bans their test, build, process and
  import-by-name submodules and helpers (`testing`, `backends`, `animation`,
  `test()`, `switch_backend`, `x13_*`, `mpl.tempfile`, ...), keeps resolved
  attribute paths inside the import surface (`scipy.datasets` after
  `import scipy.stats`), and refuses matplotlib and pandas settings that start
  LaTeX, ffmpeg or Ghostscript or import a backend by name (`rc-key`,
  `usetex=`, `backend=`). A test pins every first-level submodule of the
  packages admitted whole as reviewed or banned, so a library upgrade cannot
  add one unnoticed.
- **The render harness arms an audit hook in plot mode too.** `PlotGuard`
  refuses every `exec` of plot code, processes, sockets, native libraries and
  any write beyond the PNG and its probe, while imports, reads and drawing go
  on; all 474 catalogue matplotlib and seaborn files that pass the validator
  render under it. Data mode's `DataGuard` now refuses `exec` and `compile`
  past the snippet's own run, and lets `namedtuple` through, so
  `DataFrame.itertuples()` works in a data snippet.
