### Added

- **Node and Chromium in the renderer's toolchain image, not served yet.** The
  toolchain image (`agents/renderer/toolchain.Dockerfile`) gains a Node stage of
  its own: the official Node 22 build, the pipeline's major, checked against
  nodejs.org's SHA-256; the repository's `package-lock.json` installed with
  `npm ci --ignore-scripts`; and Playwright's Chromium headless shell alone, with
  the libraries it links and libgbm unpacked without Mesa and LLVM. The
  renderer's JavaScript row runs Node by its path (`/opt/node/bin/node`, never on
  the sandbox's PATH) on the catalogue's own harness, with Liberation fonts for
  that row alone, so the catalogue's Helvetica and Arial font stack resolves as
  on the pipeline's runner while Python's renders keep their fonts. The build
  derives MUI X's import allowlist from the installed packages' exports maps, for
  the harness's sandbox mode and the code profile that come next. 1,565 of the
  1,617 Chart.js, D3, ECharts, Highcharts and MUI X catalogue files render in the
  image unchanged (wall p95 2.4 s at 2 CPUs); the 52 that fail are MUI X files
  written for 7.29. The image build, CI and the deploy's candidate smoke each
  render through the row; the agent chat does not offer JavaScript yet. The
  images grow by 565 MB.

### Changed

- **The JavaScript harness reads its packages from `ANYPLOT_NODE_MODULES`.**
  `automation/js-render/render.mjs` keeps finding `node_modules` two levels above
  itself in a checkout, so the pipeline renders as before; the renderer image,
  where the harness sits elsewhere, names the directory. `package.json`,
  `package-lock.json` and `automation/js-render/` join the toolchain's hash, the
  build context and the CI image job's change filter.
