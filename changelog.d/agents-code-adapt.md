### Added

- **Deterministic code handling for "Use with my data" in `agents/anyplot/code/`.**
  Plain Python with no ADK import that turns a catalogue implementation into
  code the agent network can adapt and run: `regions.py` finds the THEME
  block, the Imprint palette, the `df = load_user_data()` placeholder, the
  savefig calls and the canvas keywords by AST; `normalise.py` removes the
  catalogue header, empties the catalogue title string (648 of 650 files),
  removes the `sys.path` guard family (`sys`, `__file__`,
  `importlib`, `pathlib`, `os.chdir`) and path-wrapped savefig targets, drops
  `bbox_inches` and rescales the dpi so that `figsize * dpi` renders exactly
  3200x1800 or 2400x2400 (638 of 650 matplotlib and seaborn files; 10 of 10
  rendered legacy `bbox_inches="tight"` files came out exact); `readiness.py`
  classifies a pair as blocked (13 map specs, disabled library, SECURITY
  findings, no THEME block, single-theme or other non-standard savefig
  target), coupled (literal limits, data-coordinate annotations, literal
  statistics, short palettes, fixed date locators, synthetic data, each a
  line-naming hint for the adapter) or clean (78, 535 and 37 of the 650
  matplotlib and seaborn files); `edits.py` applies an
  `AdaptPlan` with exact-once matching and protected regions; `loader.py`
  swaps the placeholder for a relative `pd.read_csv("data.csv", ...)` with
  dtypes from the dataset profile; `export.py` adds the attribution header to
  the downloadable `plot.py`. A catalogue sweep in the unit tests keeps the
  normaliser idempotent and on the canvas for every reachable figure size.
  (#12110)
