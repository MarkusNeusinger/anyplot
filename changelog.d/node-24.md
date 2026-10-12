### Changed

- **The frontend toolchain names Node 24.** `app/.nvmrc` moves from 22 to 24,
  the version CI has run since the test workflow pinned it, so `nvm use` in
  `app/` gives the same Node as the pipeline. `engines.node` keeps the build
  path's floor (22.12); the dev-only test stack reaches higher (jsdom 30.1
  installs on `^22.22.2 || ^24.15.0 || >=26.0.0`), which the version `.nvmrc`
  names satisfies. The app image keeps its `node:22-alpine` builder, which
  tracks the 22 line inside that range. (#12141)
