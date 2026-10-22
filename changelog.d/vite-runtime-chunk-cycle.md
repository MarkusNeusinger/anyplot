### Fixed

- **The site renders again after the Vite 8.1 bump.** Since Vite 8.1.6, every
  page of anyplot.ai stayed blank: Rolldown put its CommonJS runtime helper
  into the app's `theme` chunk, which imports `mui`, while `mui` imported the
  helper back, so the browser threw `t is not a function` on load. Vite 8.3.5
  emits the helper as its own `rolldown-runtime` chunk, which removes the cycle.
