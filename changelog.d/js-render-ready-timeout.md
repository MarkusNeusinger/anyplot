### Fixed

- **JavaScript render harness waits 2.5 s, not 30 s, for the ready signal.**
  `automation/js-render/render.mjs` passed the `{ timeout: 2500 }` options to
  `page.waitForFunction` in the argument slot, so every snippet without
  `window.__anyplotReady` sat through Playwright's 30 s default before the
  fonts-ready fallback ran. The options now sit in the third slot, which
  shortens every such render by about 27 s across all JavaScript libraries.
