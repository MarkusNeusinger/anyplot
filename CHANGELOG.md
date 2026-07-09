# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning is product communication
rather than library SemVer: major for milestone releases, minor for feature batches, patch for
fix-only (see `agentic/commands/release.md`).

Every non-exempt PR adds its entries under `[Unreleased]`; a release moves that section under a
new version heading (see `agentic/commands/release.md`). Product, pipeline-infrastructure, and
docs changes are covered here. **Exempt:** the automated plot pipeline's routine output
(spec-create, impl-generate/review/repair/merge, spec auto-polish, and daily-regen PRs) and
individual Dependabot bumps — listing those per entry would drown the file (900+ automated
commits per release window). Where the release window had such activity, they are summarized in
aggregate instead: an italic *Catalog* line at the end of the version section and a single
**Dependencies:** bullet under `### Changed`, both created or updated at release time.

## [Unreleased]

### Changed

- **Bot-served pages now carry the site's actual content** — the crawler-facing HTML
  (`/seo-proxy/*`, what Googlebot & social bots see) grows from a title+description shell to a
  real document: spec hubs list and link every implementation, implementation pages embed the
  full source in a `<pre>` block plus hub/sibling links, both carry the preview image and
  JSON-LD (`BreadcrumbList`, `ItemList`, `SoftwareSourceCode`), and every bot page ends with a
  site-wide nav. Display names derive from `core/constants.py`, never hand-maintained (audit
  2026-07-08 High#6).

### Added

- **`llms.txt` for AI agents** — `/llms.txt` previously fell through to the SPA shell (flagged
  by Lighthouse's Agentic Browsing audit as non-conformant); now a spec-conformant file per
  llmstxt.org (H1 + summary blockquote + H2 link sections) covering catalog, docs, the MCP
  endpoint and the repo, served directly in nginx like robots.txt so mapped crawler UAs aren't
  proxied into a `/seo-proxy/llms.txt` 404 (#9618).
- **`bot-serving-check.yml` synthetic monitor** — daily scheduled workflow that curls the
  Cloud Run origin with Googlebot/Twitterbot UAs plus a human-UA control (and an `llms.txt`
  check) and fails on non-200 or missing per-route titles, so the crawler-only serving path can
  never break silently again. Targets the origin because Cloudflare's bot management 403s
  GitHub-runner IPs (#9617, #9619).
- **Product/UX audit 2026-07-08** (`agentic/audits/2026-07-08-product-ux.md`) — 8-auditor
  workflow run scoped to pipeline, rating criteria, tabs, and product qualities; Health Score 43,
  headlined by a critical crawler outage (every bot UA gets 502 from the `@seo_proxy` hop) and
  quality-score calibration drift (#9616).
- **Legal page "other projects" block** — below the disclaimer, cross-linking the maintainer's
  other projects kurrentschrift.ink and cite-citadel, tracked as `external_link` with
  destinations `kurrentschrift` / `cite_citadel`; deliberately without `noreferrer` so the
  target sites' analytics can attribute the traffic (#9616).

- **Project skill layer under `.claude/skills/`** — six skills, ported from the kurrentschrift
  and cite-citadel setups and adapted to anyplot: `verify-frontend` (browser-drive changed flows,
  both viewports × both themes, cloud playwright-core fallback probe), `verify-api` (read sweep +
  shared-prod-DB discipline), `verify-core` (pytest/ruff/mypy gates + registry smoke), `open-pr`
  (gates → PR → CI watch → review-thread resolution with runnable GraphQL recipes),
  `optimize-skills` (session-transcript retro mining), and `babysit-pipeline` (bulk-generate
  monitoring with the battle-tested poller scripts promoted from gitignored local state).
  CLAUDE.md gained a Self-Verification routing table wiring diff paths to the skills (#9615).
- **`/dependabot` and `/catalog-status` commands** — batch-processing of Dependabot PRs with the
  GITHUB_TOKEN/auto-merge gotchas encoded, and a reproducible catalog-status report (light/dark
  migration counts, per-spec library coverage, open impl-PR classification). Both derived from a
  13-session transcript retro; the same retro added working rules to CLAUDE.md (explicit
  authorization for external writes, proactive progress reporting, absolute-path discipline)
  (#9615).
- **`CHANGELOG.md` introduced, with the v1.0.0–v3.0.0 history backfilled** from the GitHub
  releases. The per-PR changelog contract is wired into `CLAUDE.md`,
  `.github/copilot-instructions.md`, and `/pull_request`; a new `/release` command
  (`agentic/commands/release.md`) codifies the version-bump → tag → GitHub-release flow (#9614).
- **Design-sync inputs for the anyplot.ai Design System.** `.design-sync/` carries the app-shape
  sync inputs so the Design System on claude.ai/design can be synced from `app/` via
  `/design-sync`; MonoLisa is fetched from GCS and never committed (#9213).

### Changed

- **ECharts upgraded 5.5.1 → 6.1.0** — major bump of a rendered charting library; echarts
  previews regenerate against the new major through the regular pipeline (#9609).
- **Post-restructure `app/` cleanup:** dead components removed and stale doc paths fixed (#8630);
  ECharts / MUI X labels shortened in the `/stats` library list (#8666).
- **Dependencies:** grouped bumps across Python (starlette, cryptography, python-multipart,
  sqlalchemy, uvicorn, 15-update python-minor group), npm (esbuild, undici), and GitHub Actions
  (#8668, #8823, #8824, #8864, #8978, #8980, #9074, #9513, #9515).

### Removed

- **Catalog curation: 13 interactive-first specs removed** — plot types whose value is inherently
  interactive don't fit a static-first catalog (#8645).

### Fixed

- **Crawler 502 outage fixed** — since at least 2026-06-12, every crawler UA (googlebot,
  bingbot, twitterbot, discord, whatsapp, …) received HTTP 502 on every page: the nginx
  `@seo_proxy` hop verifies the upstream TLS chain of `api.anyplot.ai`, which is 4 certificates
  deep (leaf → Let's Encrypt YE1 → ISRG Root YE cross-sign → ISRG Root X2), while nginx's
  default `proxy_ssl_verify_depth` is 1. Depth raised to 4 in both proxy locations — humans saw
  a healthy site the whole time, making this a de-facto site-wide noindex (#9617).
- **All react-refresh ESLint warnings resolved** — `PALETTE` / `snippet()` extracted from
  `PalettePage.tsx` into `PalettePage.helpers.ts` (following the `MapPage.helpers.ts` pattern),
  and the `react-refresh/only-export-components` rule scoped off for test modules
  (`*.test.{ts,tsx}`, `test-utils.tsx`), which never participate in Fast Refresh (#9616).

## [3.0.0] — 2026-06-10 — Julia & JavaScript, 15 libraries & the Imprint palette

anyplot 3.0 doubles the language count — Julia and JavaScript join Python and R, growing the
catalog from 10 to 15 libraries, including the first browser-rendered and first React libraries —
and re-colors every existing implementation with the new Imprint palette. One clean break earns
the major version: Highcharts is now native JavaScript.

### Added

- **Julia / Makie.jl — 3rd language.** Julia 1.11 + CairoMakie with full pipeline support: CI
  runtime via `setup-julia`, `Project.toml` environment, makie arms in every impl workflow,
  dedicated prompts, Julia syntax highlighting in the code viewer (#7613).
- **JavaScript — 4th language: Chart.js, D3.js, Apache ECharts.** First browser-rendered runtime:
  a Node 22 + Playwright headless-Chromium harness (`automation/js-render/render.mjs`) renders
  each snippet at exact gallery pixels and emits both the PNG and a self-contained interactive
  HTML (#8244); JS implementations get the Interactive toggle on the site (#8251). The library
  registry gained a `framework` field and per-library file-extension overrides (#8244).
- **MUI X Charts — first React library.** Community `@mui/x-charts` as the first
  `framework: react` / `.tsx` library; the render harness gained an esbuild branch that bundles
  React components in a theme-aware MUI `ThemeProvider` (#8517).
- **Imprint — anyplot's own palette.** 8-hue colorblind-safe categorical palette + 3 semantic
  anchors replacing Okabe-Ito project-wide, with a named API in `core/palette.py` and
  `imprint_seq` / theme-adaptive `imprint_div` colormaps (#7692). `/palette` rebuilt: per-pixel
  OKLCH color wheel, chroma/ΔE/WCAG metrics, compare-with overlays, unified `IMPRINT` copy-paste
  object for Python/R/Julia/JS, pairwise ΔE matrices for normal + CVD vision (#7692, #8125).
- **Frontend CI gates:** Prettier, sorted imports, unused-import lint, and full type-checking now
  run on every PR (#8519); new `app/ARCHITECTURE.md` documents the structure (#8596).

### Changed

- **Frontend restructure (11 PRs):** `routes/` registry, `layouts/` + `sections/` split, feature
  folders, central API client, theme module, typed global config, `src/*` aliases (#8519–#8581).
- **Render canvas halved** to 3200×1800 / 2400×2400 with proportional-sizing review rules,
  validated by a 540-render style experiment (#7387); typography recalibrated across all
  libraries (#7389, #7391–#7428); hard canvas-size gate (±16 px) enforced pre-review (#7517);
  AR-09 edge-clipping auto-reject (#7528).
- **Palette migration:** ~1,300 existing implementations re-colored in a one-shot deterministic
  hex-swap wave (#7776–#7798), with semantic red/amber/green restored where color carries
  meaning (#7777).
- **Pipeline & ops:** watchdog rescues stale `ai-approved`, attempt-less `ai-rejected`, and
  label-less impl PRs (#7687); impl-merge sweeps stale failure labels (#7616); daily-regen
  rebalanced to 10×/day on Sonnet (#7717, #7286); impl-generate can overlay `prompts/` from the
  trigger branch for experiments (#7385); `/audit` retooled as goal-directed across 6 graded
  dimensions (#8023, #8024).
- **Dependencies:** 21 updates including playwright 1.55, esbuild 0.25, aiohttp 3.14,
  claude-code-action 1.0.133, plus grouped python/npm/MUI/react/actions bumps.

### Removed

- **Breaking: Highcharts Python wrapper.** Highcharts is now native `highcharts.js` instead of
  the `highcharts-core` Python wrapper, following the most-used-variant rule; all 322 legacy
  Python implementations and their metadata were removed — old Python deep links fall back to
  the spec hub (#8516).

### Fixed

- **Frontend performance:** above-the-fold landing counts no longer stall up to 2 s, `/specs`
  thumbnails lazy-load, `/stats` uses aggregate COUNT queries, empty-filter fast path (#7694).
- Tag chips correctly filter `/plots` again (#7516); visitors chart includes today (#7610);
  masthead on xs (#7891); dark-mode overlay buttons (#8021).
- Dual alembic heads that had stalled the production Postgres sync (#7285); silent chartjs/d3
  version-lookup failures (#8248); duplicate ruff key breaking main (#7683).

*Catalog: 885 regenerations + 310 new implementations across 15 libraries; 46 automated
spec-polish PRs; R/ggplot2 coverage 30 → 126; first 8 specs at full 15/15 coverage; 327 specs.*

## [2.4.0] — 2026-05-18 — R/ggplot2, multi-language pipeline & in-app feedback

anyplot is no longer Python-only — R / ggplot2 is the 10th supported library, riding on a new
multi-language pipeline that generalizes the spec → impl → review → merge flow beyond Python.

### Added

- **R / ggplot2 — 10th library, 2nd language** with the generalized multi-language pipeline:
  spec, generation, review, merge, code viewer, libraries page, language counts (#6944, #6961).
- **In-app feedback widget** reachable from any page (#7143), with dark-mode adaptation and
  clearer placeholder copy (#7282).
- **`/stats`:** Plausible visitors chart and a daily-impl timeline (#6608).
- **Language-aware navigation:** `/plots?lang=` filtering, cross-language carousel on plot pages,
  language in cards, titles, and analytics (#7141, #7142, #7144).
- **Ops:** review-retry listener + stuck-jobs watchdog workflows (#6084); local style-variant
  experimentation script (#6378).

### Changed

- Pseudo-function styling for 404 page, footer, empty state, and library card (#6436);
  daily-regen cadence 2 h → hourly (#6943).
- **Dependencies:** 13 Dependabot bumps across Python (mypy, urllib3, authlib), npm (react, mui),
  and GitHub Actions.

### Fixed

- Non-Python pipeline hardening: `renv` stdout suppression in the version probe (#6948), broken
  `renv.lock` removed (#6950), `prism/r` type shim so `tsc` no longer blocks Cloud Build (#7052).
- Language preserved through `/debug` deep links (#7066); no horizontal scroll on `/stats` and
  `/mcp` (#6902); breadcrumb truncation + initial FAB lift on deep links (#7283); lowercase
  language in plot-page SEO titles (#7206).

*Catalog: 30 ggplot2 implementations at release across foundational plot types; ~1,200
regenerations rolled across all 10 libraries during the window.*

## [2.3.0] — 2026-05-07 — 10 new plot types & end-to-end auto-merge

### Added

- **`/map` page** — force-directed spec map clustered by tag similarity, with a landing-page
  teaser (#5647, #5649, #5665).
- **OG images redesigned** in the any.plot() visual identity — branded cards with light/dark
  variants (#5659).
- **Mobile debug:** on-device console + richer ErrorBoundary (#5808); avatar in the legal page
  operator block (#5726).
- **10 new plot types** across 9 libraries: area-stacked, bar-horizontal, bland-altman-basic,
  count-basic, ice-basic, radar-multi, scatter-embedding, scatter-regression-polynomial,
  shap-waterfall, spiral-timeseries.

### Changed

- **Tag-vocabulary policy is now asymmetric** (#5856, #5859): `plot_type` is canonical (table
  authoritative, new types via PR); `data_type` / `domain` / `features` are advisory — polish
  only moves misclassified tags or canonicalizes synonyms, and no longer strips valid niche tags.
- **End-to-end auto-merge:** polish and impl PRs squash-merge themselves once green via
  `gh pr merge --auto` set on creation (#5955); behind branches auto-update after every push to
  `main` (#5957, #5958).
- **Pipeline:** autonomous spec polish + cross-library similarity audit in daily-regen pre-flight
  (#5714); daily-regen gained `spec_id` and `model` inputs (#5706); resumable single-step regen
  (#5650); transient-retry hardening across impl-generate/review (#5819, #5725, #5724);
  evaluate-plot switched to the canonical 6-category rubric (#5818).
- **Repo:** implementations moved under `plots/{spec}/implementations/python/{library}.py` to
  make room for other languages (#5648); 64 `Optional[X]` → `X | None` modernizations (#5727).
- **Docs:** library-expansion roadmap (#5951); FCP/TTFB Web-Vitals events documented and
  `/seo-proxy/map` handler added so bots get a real title for the map (#5818).

### Fixed

- iOS Safari load failure — `requestIdleCallback` polyfilled (#5816).
- POTD GitHub source link includes the language segment (#5663); letterbox strips around the
  preview removed (#5943).
- Frontend lint 32 → 0 errors, including React 19 `set-state-in-effect` refactors (#5818);
  fire-and-forget analytics tasks could be GC'd mid-flight — now held in a module-level set
  (#5727).

*Catalog: coverage filled for horizon-basic/seaborn (#5851).*

## [2.2.0] — 2026-04-29 — Regen wave, Cloudflare Access on /debug & 4-attempt pipeline

### Added

- **Cloudflare Access on `/debug`** with a service-token fallback for CI (#5522); same-origin
  `/api` proxy fixes the cookie scope (#5551); hard reload fires the page gate cleanly when the
  JWT lapses (#5552).
- **`/regen` command** for unattended library regeneration; `/audit` framework split into
  per-agent files with 7 new auditors (#5413, #5451).
- **Mandatory PR follow-through** codified in `CLAUDE.md` (#5553).

### Changed

- Repair budget bumped 3 → 4 attempts with cascading quality thresholds (90/80/70/60/50);
  `ADMIN_TOKEN` PAT for impl-merge ruleset bypass (#5523, #5521).
- Daily-regen runs on Sonnet (#5452) and skips the 20:00–24:00 Berlin window (#5517).
- **Dependencies:** 8 Dependabot bumps (uvicorn, setuptools, sqlalchemy, matplotlib,
  react-router-dom, grouped npm/python/actions).

*Catalog: 12-spec regen wave at ~3.5× v2.1.0 throughput; network-basic filled to 9/9;
area-mountain-panorama gained bokeh.*

## [2.1.0] — 2026-04-25 — Tri-state theme, pipeline resilience & 2 new plot types

### Added

- **Tri-state theme mode** — system / light / dark with live OS sync; the site follows the OS
  theme by default while respecting an explicit override (#5412).
- **2 new plot types:** venn-labeled-items (9/9) and area-mountain-panorama, whose spec was
  refined mid-flight to require jagged piecewise-linear ridgelines (#5411).
- Landing-page interaction analytics for hero/libraries/palette/nav/footer (#5400).

### Changed

- **Self-healing pipeline** against transient Claude Code Action failures (#5410): generate retry
  budget 2 → 3, repair and review auto-retry once; marker counts paginate properly.
- In-memory caching for spec lookups; review feedback from prior attempts is passed back into
  regeneration runs; code-view paper aesthetic (#5401).

### Fixed

- Scroll restoration on route change (#5403, #5404); mobile search width (#5363).

*Catalog: coverage filled (donut-basic/plotnine, contour-basic/pygal); 5 specs regenerated.*

## [2.0.0] — 2026-04-23 — anyplot.ai Relaunch

The project rebrands from pyplots.ai to anyplot.ai, ships a redesigned homepage, the Okabe-Ito
color palette, and first-class dark mode for the site and every plot preview. Major because
URLs, schema, and the public domain all change. (The annotated tag `v1.1.0-pyplots-final`,
2026-04-14, marks the last pyplots.ai state before the rebrand.)

### Added

- **New homepage & visual identity:** hero, libraries / palette / specifications sections,
  MonoLisa typography, Okabe-Ito colorblind-safe palette, theme-adaptive chrome.
- **Dark mode (site + plots):** every plot ships `plot-light` and `plot-dark` variants; theme
  tokens drive all chrome; mandatory theme-readability check in the AI quality pipeline.

### Changed

- **Breaking: domain migration** `pyplots.ai` → `anyplot.ai` (bookmarks and MCP clients should
  switch), with nginx redirect-loop fixes.
- **Breaking: URL restructure** — canonical spec URL is `/{specId}/{language}/{library}`; hub
  view consolidated under `/{specId}` with optional `?language=` filter; Catalog → Plots rename.
- **Breaking: schema** — multi-language restructure with a new `languages` table; implementations
  expose `preview_url_light` / `preview_url_dark` (legacy `preview_url` aliases the light
  variant).
- **CI/infrastructure:** 6 workflows migrated from service-account keys to Workload Identity
  Federation; bulk-generate moved to paced sequential dispatch with a global mutex; daily cron
  regenerates the oldest not-recently-updated spec on a 4 h cadence with a Berlin-evening
  blackout.
- **Dependencies:** MUI 7 → 9, Vite 7 → 8, FastMCP v3, FastAPI 0.136, anthropic 0.97, plus
  security bumps (cryptography, mako, authlib, python-multipart).

## [1.1.0] — 2026-04-10 — Visual Redesign & Theme Tokenization

### Added

- **Theme tokenization:** 80+ hardcoded hex colors and font strings centralized into
  `app/src/theme/index.ts`, with new tokens, shared style constants, and a central `LIB_ABBREV`
  map; full style-guide doc.

### Changed

- **Plot of the Day redesign:** terminal-style frame with a `$ python plots/...` prompt linking
  to the GitHub source, split layout, real library + Python versions.
- Responsive polish: mobile breadcrumb abbreviations, smoother RelatedSpecs grid progression.

### Fixed

- **WCAG AA:** 15+ contrast violations fixed; all text meets 4.5:1; keyboard-accessible zoom
  container with focus-visible.
- Pre-existing lint errors (setState in useEffect → render-time ref); AbortController fetch
  cleanup on unmount.

## [1.0.0] — 2026-04-07 — pyplots.ai launch

First formal release of pyplots.ai — an AI-powered platform for Python data-visualization
examples. At launch: 309 specifications, 2,668 implementations across 9 libraries, and 1,798
interactive HTML previews.

### Added

- Browse, filter, and search plots across 11 tag categories with AND/OR logic.
- Implementation pages: syntax-highlighted code, AI quality reviews, interactive previews; copy
  code, download PNG, fullscreen.
- `/stats` dashboard, Plot of the Day, and similar specifications/implementations via tag-based
  Jaccard similarity.
- MCP server for AI-assistant integration.
- Stack: FastAPI + async SQLAlchemy + PostgreSQL; React 19 + Vite + MUI + TypeScript; 13 GitHub
  Actions workflows (spec creation, impl generation, AI review, auto-merge); Cloud Run +
  Cloud SQL + GCS; 1,081 unit tests.

[Unreleased]: https://github.com/MarkusNeusinger/anyplot/compare/v3.0.0...HEAD
[3.0.0]: https://github.com/MarkusNeusinger/anyplot/compare/v2.4.0...v3.0.0
[2.4.0]: https://github.com/MarkusNeusinger/anyplot/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/MarkusNeusinger/anyplot/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/MarkusNeusinger/anyplot/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/MarkusNeusinger/anyplot/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/MarkusNeusinger/anyplot/compare/v1.1.0...v2.0.0
[1.1.0]: https://github.com/MarkusNeusinger/anyplot/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/MarkusNeusinger/anyplot/releases/tag/v1.0.0
