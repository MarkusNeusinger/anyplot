### Added

- **A browser check that the site renders, before and after every merge.**
  `scripts/site-smoke.mjs` loads the home page, `/plots` and a spec page in
  headless Chromium and fails on a JavaScript error or an empty page. The
  app-image CI job runs it against the built container, so a dependency bump
  that breaks the boot fails its PR, and a new rule in `CLAUDE.md` (with the
  recipe in the `open-pr` skill and the Dependabot batch command) runs it
  against production after every merge. On 2026-10-22 a vite bump passed
  every check and left every page blank for about 45 minutes.
