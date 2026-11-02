### Security

- **The plot validator refuses banned objects under any name.** pygal binds
  `types.FunctionType` as `pygal.config.callable`, which the validator admitted
  because it bans `FunctionType` and `LambdaType` by name only. The walk of the
  admitted modules now decides by what an object is: a builtin or `types`
  member the validator bans, a module it bans together with that module's
  functions and classes, a loader, a frame, or a wrapper of any of these,
  wherever a public path reaches it. The walk found five more routes, now
  refused: `pathlib.Path`, re-exported by matplotlib and statsmodels;
  multiprocessing's `Pool`; altair's `importlib_version`; and the `tokenize`
  module. The reviews also ban `timeit` on every receiver and the `eval_str=`
  keyword, with which `inspect.signature` evaluates a function's annotations
  (#12519).
- **No route to a module-scoped ban through an expression or `**`.** A path
  that leads to a `MODULE_ESCAPES` entry is only a receiver, a callee or a
  plain alias, so `[matplotlib.cbook][0].Path` and an annotated alias are
  refused. A banned keyword is refused when `**` passes it from a dict held in
  a name or filled by subscript or `.update`, and so is a keyword name built
  at run time, unless its literal head rules out every banned keyword
  (plotly's `f"xaxis{n}"` passes) (#12519).

### Fixed

- **CI runs the plotting-library tests.** "Run Tests" installs libcairo and
  the eight `lib-*` extras of the renderer image, without its image-export
  stacks, and sets `ANYPLOT_REQUIRE_LIBRARIES=1`, so a library that does not
  import fails its tests instead of skipping them. Before, the validator's
  walk saw matplotlib alone, and 32 harness, validator and normaliser cases
  never ran in CI (#12519).
- **The text probe of pygal, altair and lets-plot holds the drawn texts.** The
  harness wrote it through `os.fdopen`, whose `open` event names no path, so
  the plot guard refused the write and left an empty file. The reply had no
  texts for those three libraries since #12503. The probe now goes out
  through `os.write`, a FIFO at its name no longer blocks the write, a failed
  write is logged as `probe_failed` per launch, and an empty or unreadable
  probe reaches the `pipeline_render` line as `InvalidProbe` (#12519).
