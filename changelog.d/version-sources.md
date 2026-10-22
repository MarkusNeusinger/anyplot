### Added

- **Dependabot watches the JavaScript render harness.** The root `package.json`
  (Chart.js, D3, ECharts, Highcharts, MUI X) gets weekly grouped minor and
  patch PRs; a major arrives as its own PR, because it changes the API the
  library prompt describes. (#12240)

### Changed

- **Library and runtime versions are read from the pins, never written by
  hand.** `core/library_versions.py` reads `uv.lock`, the root
  `package-lock.json`, `Manifest.toml`, `.python-version`, the setup actions
  and the R snapshot, and the database sync fills the Libraries page from it;
  `core/constants.py` carries no version any more. Ten of its fifteen numbers
  had drifted (matplotlib 3.9.0 against 3.11.2 locked, ECharts 5.5.1 against
  6.1.0), and a Dependabot bump now needs no edit. The library prompts' example
  headers carry no version; the JavaScript and Makie prompts state the API
  level they write for, and a test holds it to the lock's major. (#12240)

### Fixed

- **The pipeline installs the Python libraries from `uv.lock`.**
  `impl-generate.yml` and `impl-repair.yml` ran `uv pip install -e ".[lib-X]"`,
  which resolved `pyproject.toml`'s ranges afresh, so Dependabot's lock bumps
  never reached the pipeline and recorded versions drifted from the lock
  (plotnine 0.15.8 recorded, 0.15.7 locked). Both now run
  `uv sync --frozen --extra lib-X`, as the renderer image does. (#12240)
- **Implementation PRs can no longer change dependency files.** #9398 committed
  a `Manifest.toml` that a `Pkg.add` had re-resolved, which moved Makie from
  0.22.10 to 0.21.9 for every Julia implementation. `impl-generate.yml` now
  fails such a generation, `impl-merge.yml` refuses such a PR, and the
  generator and repair prompts say so. (#12240)
