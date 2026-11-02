### Security

- **The plot validator refuses banned objects under any name.** pygal binds
  `types.FunctionType` as `pygal.config.callable`, which the validator admitted
  because it bans `FunctionType` and `LambdaType` by name only. The walk of the
  admitted modules now decides by what an object is: a builtin or `types`
  member the validator bans, a module it bans together with that module's
  functions and classes, a loader, or a frame, wherever a public path reaches
  it. The walk found five more routes, now refused: `pathlib.Path`, re-exported
  by matplotlib and statsmodels; multiprocessing's `Pool`; altair's
  `importlib_version`; and the `tokenize` module. The review also bans
  `timeit` on every receiver and the `eval_str=` keyword, with which
  `inspect.signature` evaluates a function's annotations.

### Fixed

- **CI runs the plotting-library tests.** "Run Tests" installs the eight
  `lib-*` extras of the renderer image and sets `ANYPLOT_REQUIRE_LIBRARIES=1`,
  so a library that does not import fails its tests instead of skipping them.
  Before, the validator's walk saw matplotlib alone, and 32 harness, validator
  and normaliser cases never ran in CI.
- **The text probe of pygal, altair and lets-plot holds the drawn texts.** The
  harness wrote it through `os.fdopen`, whose `open` event names no path, so
  the plot guard refused the write and left an empty file. The reply had no
  texts for those three libraries. The probe now goes out through `os.write`.
