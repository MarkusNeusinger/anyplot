# Frontend Architecture

React 19 + Vite + TypeScript (strict) + MUI 9, packaged with yarn. This is the
frontend-specific companion to [`agentic/docs/project-guide.md`](../agentic/docs/project-guide.md);
structure follows patterns popularized by mature MUI dashboards (thin pages,
feature sections, central route/theme/config modules).

## Directory layout

```
src/
  main.tsx           Bootstrap only: root render, global CSS, web vitals
  app.tsx            Provider composition (ThemeProvider → CssBaseline → AppRouter)
  global-config.ts   Typed CONFIG: app metadata, API base URLs (VITE_*), isDev
  routes/            Router (index.tsx, lazy-loaded pages, error boundaries)
                     and paths.ts — the single source of truth for app URLs
  layouts/           App shell: RootLayout, Layout (AppDataProvider), NavBar,
                     Footer, MastheadRule, BareLayout
  pages/             One component per route; coordinate hooks + sections
  sections/          Feature UI, grouped by surface:
    landing/           Hero, NumbersStrip, LibrariesSection, PlotOfTheDay…
    plots-gallery/     FilterBar/ (feature folder), ImagesGrid, ImageCard…
    spec-detail/       SpecTabs/ (feature folder), SpecDetailView, SpecOverview…
    libraries/         LibraryCard
  components/        Shared primitives only (LoaderSpinner, SectionHeader,
                     ErrorBoundary, CodeHighlighter, ThemeToggle, …)
  hooks/             Reusable state/data hooks (useFilterState, useCodeFetch,
                     useForceGraphSimulation, …) — barrel in index.ts
  lib/               Third-party/client isolation: api.ts (apiGet/apiPost,
                     ApiError, endpoints registry, fetchWithAuth)
  theme/             tokens.ts (design tokens), palette/typography/components
                     option modules, create-theme.ts; index.ts re-exports all
  utils/             Pure helpers (filters, fuzzySearch, responsiveImage, …)
  constants/         Domain constants (libraries, language maps); re-exports CONFIG
  types/             Shared domain types (PlotImage, Implementation, …)
  analytics/         reportWebVitals
  styles/            tokens.css (CSS custom properties, dark mode), fonts.css
```

## Conventions

- **Imports** are absolute from the `src/` alias (`import { paths } from 'src/routes/paths'`);
  no relative `../` imports. ESLint (perfectionist) enforces sorted, grouped imports.
- **Naming**: `PascalCase.tsx` components, `useXxx.ts` hooks, lowercase modules elsewhere.
- **URLs** never appear as string literals in components — use `paths.*` from
  `src/routes/paths` (static routes, `paths.plotsFiltered(param, value)`,
  `paths.spec(specId, language, library)`).
- **API access** goes through `src/lib/api` (`apiGet`/`apiPost` + `endpoints`);
  raw `fetch()` lives only inside that module. Callers own caching/abort/dedup.
- **Config**: read `CONFIG` from `src/global-config` instead of `import.meta.env`.
- **Theme**: design tokens (colors, font stacks, style constants) come from
  `src/theme` (tokens); MUI theme composition lives in `theme/create-theme.ts`.
  Dark mode works via CSS custom properties (`styles/tokens.css`, `[data-theme]`).
- **Feature folders**: when a section component outgrows one file (FilterBar,
  SpecTabs), it becomes a folder with `index.tsx` as orchestrator + focused
  sub-components, keeping the import path stable.

## Data flow

Pages coordinate; hooks fetch and hold state; sections/components render.
`RootLayout` (via `Layout`'s `AppDataProvider`) loads app-wide data once
(specs, libraries, languages, stats); route components are lazy-loaded in
`routes/index.tsx` with `RouteErrorBoundary` keeping the shell alive on errors.

## Testing

Vitest + Testing Library, jsdom, globals enabled. Tests are colocated
(`X.test.tsx` next to `X.tsx`) and render through `src/test-utils`, which wraps
the real app theme and a `MemoryRouter`. Mock `globalThis.fetch` (not
`lib/api`) so URL construction stays covered. Coverage scope is configured in
`vitest.config.ts`.

## Quality gates

```bash
cd app
yarn lint && yarn fm:check && yarn type-check && yarn test && yarn build
```

CI (`.github/workflows/ci-tests.yml`, job `test-frontend`) runs the same gates;
`yarn type-check` covers app and test files (`tsconfig.test.json`). During
development, `vite-plugin-checker` surfaces TS/ESLint errors in the browser.

## Adding things

- **Page**: create `pages/NewPage.tsx`, register it lazily in
  `routes/index.tsx`, add its path to `routes/paths.ts` (and to
  `RESERVED_TOP_LEVEL` — spec ids share the URL root).
- **Section**: create it under `sections/<surface>/`, export from the folder
  barrel, render it from a page.
- **Hook**: create `hooks/useNewThing.ts`, export from `hooks/index.ts`,
  colocate `useNewThing.test.ts`.
- **Endpoint**: add a builder to `endpoints` in `lib/api.ts` (alphabetical).
