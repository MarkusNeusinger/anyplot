### Changed

- **The frontend toolchain names Node 24.** `app/.nvmrc` moves from 22 to 24,
  the version CI has run since the test workflow pinned it, so `nvm use` in
  `app/` gives the same Node as the pipeline. `engines.node` now states the
  floor that installs: 22.22.2 or later, which jsdom 30.1 requires; on an older
  22 `yarn install` stops with an engine error. The app image keeps its
  `node:22-alpine` builder, which tracks the 22 line and satisfies the floor.
