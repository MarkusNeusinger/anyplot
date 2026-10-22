### Added

- **Dependabot watches the JavaScript render harness.** The root `package.json`
  (Chart.js, D3, ECharts, Highcharts, MUI X) gets weekly grouped minor and
  patch PRs; a major arrives as its own PR, because it changes the API the
  library prompt describes. (#12240)
- **Hand-written versions are checked against their pins.** A unit test holds
  each library's `version` in `core/constants.py`, the language runtime
  versions, and the example header in the JavaScript and Julia library prompts
  to `uv.lock`, the root `package-lock.json`, `Manifest.toml`, the setup
  actions and the R snapshot, so a bump that moves a pin updates them in the
  same PR. (#12240)

### Fixed

- **The Libraries page shows the pinned versions again.** Ten of the fifteen
  `version` entries had drifted: matplotlib said 3.9.0 against 3.11.2 locked,
  plotly 5.18.0 against 7.1.0, ECharts 5.5.1 against 6.1.0, and Makie 0.22
  against 0.21.9. The next database sync carries the corrected ones, and the
  ECharts, Makie and MUI X prompt headers name the pinned version too. (#12240)
- **Implementation PRs can no longer change dependency files.** #9398 committed
  a `Manifest.toml` that a `Pkg.add` had re-resolved, which moved Makie from
  0.22.10 to 0.21.9 for every Julia implementation. `impl-generate.yml` now
  fails such a generation, `impl-merge.yml` refuses such a PR, and the
  generator and repair prompts say so. (#12240)
