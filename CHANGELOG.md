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

### Added

- **`CODE_OF_CONDUCT.md`** — Contributor Covenant 2.1, linked from `docs/contributing.md`
  (closes the last repo-health gap from audit 2026-07-15 Medium#29) (#9644).
- **Bot-served pages got a real SEO surface** — `seo_home()` now emits the site-level JSON-LD
  (`WebApplication`, `WebSite`+`SearchAction`, `Organization`) that previously only lived in the
  SPA shell nginx never serves to bots, plus a descriptive title/meta and real body copy;
  `/seo-proxy/plots` and `/seo-proxy/specs` render a server-side link to every spec hub, so
  crawlers can reach all 324 hubs (they were orphans); `Google-InspectionTool`/`GoogleOther`
  UAs are now routed to the bot pages like Googlebot (audit 2026-07-15 High#10/#11,
  Medium#40/#41) (#9642).
- **`core/palette.py` unit tests** — the last untested core module now has coverage: pool
  contract, semantic anchors, theme-adaptive neutrals, lazy cmaps and the
  matplotlib-free-import guarantee (audit 2026-07-15 Medium#28) (#9642).
- **Impl check constraints exist as a migration** — `ck_quality_score_range` /
  `ck_review_verdict_valid` lived only in the ORM; a new alembic migration adds them (with
  pre-normalization of violating rows and a real downgrade) (audit 2026-07-15 Medium#18) (#9642).
- **Repo health:** PR template with changelog/docs checklist and an `.editorconfig` mirroring
  ruff + frontend conventions (audit 2026-07-15 Medium#29) (#9642).
- **Full 2026-07-15 codebase audit report** — persisted output of a 16-auditor `/audit` run
  with domain-routed cross-validation (`agentic/audits/2026-07-15-all.md`, mirrored to
  `latest.md`). Health Score 30/100 with correctness (C, 60) as the weak pillar; headlines are a
  live `heatmap-calendar` retry loop (#1010), 15-library pipeline/config drift, dark-mode
  white-surface leaks, and 97 reviewer-rejected implementations live on main, plus an open-issue
  triage with a recommended work queue. Report only, no source changes (#9641).
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

- **Hot listing paths stop fetching every code blob** — MCP `list_specs` /
  `search_specs_by_tags` and `/libraries/{id}/images` used `get_all_with_code()`, dragging the
  full multi-MB code corpus through the DB per request; the MCP tools now resolve code
  *presence* via a lightweight id probe (`get_ids_with_code`) and the images endpoint fetches
  only its own library's code (`get_by_library_with_code`); the now-unused `get_all_with_code()`
  was removed (audit 2026-07-15 Medium#5, issue #7696) (#9644).
- **Frontend a11y pass** — card actions reveal on `:focus-within` and stay visible on touch
  devices instead of hover-only; the NavBar search button and nav links have `:focus-visible`
  outlines; mobile nav/theme-toggle tap targets reach 44px; off-palette Tailwind green and a
  rogue Python-blue were replaced with imprint palette hues; `AppDataProvider`/theme context
  values are memoized so consumers stop re-rendering every frame (audit 2026-07-15
  Medium#7/#10/#11/#12).
- **Frontend production image builds on `node:22-alpine`** — `node:20` is EOL April 2026; 22
  matches the JS render harness (audit 2026-07-15 Medium#16) (#9642).
- **Spec-detail tabs are self-explanatory now** — the Code tab (Spec tab on hub pages) starts
  open instead of everything collapsed, the selected tab shows a small caret signaling the
  click-to-collapse toggle, the quality tab reads "Quality 91" (with an explanatory
  `aria-label`) instead of a bare number, and tabs↔panels got standard `id`/`aria-controls`
  wiring (audit 2026-07-08 High#5 + Low#1) (#9622).
- **Bot-served pages now carry the site's actual content** — the crawler-facing HTML
  (`/seo-proxy/*`, what Googlebot & social bots see) grows from a title+description shell to a
  real document: spec hubs list and link every implementation, implementation pages embed the
  full source in a `<pre>` block plus hub/sibling links, both carry the preview image and
  JSON-LD (`BreadcrumbList`, `ItemList`, `SoftwareSourceCode`), and every bot page ends with a
  site-wide nav. Display names derive from `core/constants.py`, never hand-maintained (audit
  2026-07-08 High#6) (#9621).
- **Gallery cold path prewarmed** — the startup cache prewarm now also computes the two
  heaviest user-facing payloads, `/plots/filter` (`filter:all`) and `/specs/map`, so the first
  visitor of a fresh Cloud Run instance no longer waits on the full DB roundtrip for the
  gallery or the map page (audit 2026-07-08 Quick Win 2) (#9620).
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

- **anyplot.ai white-screen outage (2026-07-23, ~22:15–23:00 UTC): vite pinned back to
  8.0.16** — the npm-minor Dependabot group (#9657) bumped vite 8.0.16 → 8.1.5, whose rolldown
  1.1.5 bundler emits a broken `mui`/`@emotion` chunk under our `manualChunks` split; the
  deployed app died at chunk init (`TypeError: t is not a function`) into a blank page while
  every HTTP check stayed 200 and all CI stayed green (jsdom tests never execute the built
  bundle). Bisect across builds pinned it byte-exactly: with vite 8.0.16 the mui chunk hash
  reverts to the known-good build's. Dependabot now ignores vite minor/major bumps until the
  upstream codegen issue is verified fixed in a real browser.
- **Scheduled implementation regeneration is harder to starve silently** — `daily-regen.yml`'s
  cron had gone silent for multi-day stretches (a mix of GitHub's documented top-of-hour
  scheduler overload and the workflow being manually disabled), and because every run that did
  start was green, nothing alarmed. The cron now fires at :17 instead of :00, and
  `watchdog-stuck-jobs.yml` gained a cron-liveness rescue that re-dispatches daily-regen
  whenever main has seen no new run created for >10 h outside the Berlin-evening quiet window
  (a manually disabled workflow stays disabled — the rescue cannot and does not re-enable it),
  capping scheduler-side starvation at typically ~half a day instead of weeks (#9649).
- **The whole Claude pipeline generates again — CI runs pass the repo's permission allowlist
  explicitly** — since the July 5 `claude-code-action` bump (bundled CLI 2.1.170 → 2.1.195, by
  now 2.1.211), Claude Code ignores `permissions.allow` from a committed `.claude/settings.json`
  in untrusted workspaces, and a CI checkout is never trusted; every impl-generate/repair, spec-create, polish and similarity run
  had its Write/Edit/Bash calls silently denied (19–20 denials per run, zero files produced,
  zero implementations generated repo-wide since July 1). All 12 `claude-code-action` steps now
  pass `--settings .claude/settings.json` in `claude_args`, which the trust gate honors as an
  explicit opt-in (#9651).
- **Metadata step no longer executes a comment as a command** — a backtick-quoted fragment
  inside the double-quoted Python heredoc of impl-generate's "Create library metadata file"
  step was command-substituted by bash (`--model: command not found` in every run log); the
  comment now uses single quotes (#9651).
- **Tag search uses the GIN index and stops treating `%`/`_` as wildcards** —
  `SpecRepository.search_by_tags` cast the JSONB `tags` column to text and ran LIKE, which the
  `ix_specs_tags` GIN index can never serve (sequential scan on every MCP tag search) and which
  let LIKE metacharacters in tag values wildcard-match; on PostgreSQL it now emits per-category
  JSONB containment (`tags @> …`), and the SQLite test fallback escapes LIKE metacharacters
  (audit 2026-07-15 Medium#17) (#9644).
- **Feedback rate limiting no longer trusts a spoofable header entry** — `/feedback` keyed its
  per-IP rate limit and duplicate suppression on the client-controlled *first* `x-forwarded-for`
  entry, so a caller could evade the limit or poison another user's bucket; it now prefers
  Cloudflare's `cf-connecting-ip` and otherwise uses the rightmost, infrastructure-appended
  entry (audit 2026-07-15 Medium#20) (#9644).
- **Runaway impl-generate retry loop can no longer self-amplify** — the 3-attempt cap counted
  prior failures by paginating issue comments and fell back to "0 failures" whenever the count
  API call rate-limited, so every failure re-dispatched forever (issue #1010 flooded ~1,200
  Actions runs in 38h). The counter now fails closed (an unreadable count = cap reached, no
  auto-retry) and correctly sums per-page counts on issues with >100 comments (audit 2026-07-15
  Critical#1).
- **`spec-create.yml` PR/issue bodies show real content again** — three quoted heredocs
  (`<<'EOF'`) never expanded variables, shipping literal `$SPEC_CONTENT` into PR bodies; bodies
  are now built via unquoted heredocs (literal backticks escaped so no command substitution)
  and passed with `--body-file`. The post-merge comment also lists all 15 generate labels
  (audit 2026-07-15 High#3) (#9642).
- **`impl-merge.yml` no longer closes issues early** — the auto-close step read a stale
  hardcoded 11-library list while 4 JS libraries were still pending; it now derives the list
  from `core/constants.py` `SUPPORTED_LIBRARIES` at run time (audit 2026-07-15 High#4) (#9642).
- **Local evaluator accepts what the pipeline actually emits** — `scripts/evaluate-plot.py`
  looked for `plot.png` while implementations emit `plot-{light,dark}.png`, auto-rejecting
  every compliant impl; it is now theme-aware via `ANYPLOT_THEME` (legacy `plot.png` still
  accepted), runs impls with the theme env set, and its big static rubric is sent as a cached
  system prompt (Anthropic prompt caching) instead of being re-billed per call
  (audit 2026-07-15 High#5, Medium#25) (#9642).
- **Async Cloud SQL fallback actually works** — the Cloud SQL connector path wrapped a sync
  pg8000 engine in `async_sessionmaker`, deferring a crash to the first request; it now uses
  the connector's async path (`create_async_engine` + `async_creator` with asyncpg) and closes
  via `close_async()` (audit 2026-07-15 High#6) (#9642).
- **API robustness triple** — MCP `search_specs_by_tags` no longer crashes on impls with NULL
  `impl_tags`; `DatabaseQueryError` returns a generic client message instead of reflecting raw
  SQLAlchemy error text (full detail still logged server-side); `api/cache.py` prunes per-key
  locks when a factory raises (404-probe traffic no longer grows `_locks` unbounded) and holds
  strong references to background refresh tasks so stale-while-revalidate can't be jammed by
  GC (audit 2026-07-15 Medium#1/#3/#4/#22) (#9642).
- **Library/language registry updates reach the prod DB** — the Postgres seed switched from
  `on_conflict_do_nothing` to an upsert, so version/description changes in `core/constants.py`
  propagate instead of being silently dropped (audit 2026-07-15 Medium#2) (#9642).
- **Dark-mode overlay controls and dropdown surfaces** — the copy button, action pills and
  loading pill on catalog/spec cards reused hardcoded white; they now share the theme-aware
  `overlayButtonSx` helper, and MUI Menu/Popover papers are wired to `var(--bg-elevated)` /
  `var(--ink)` so filter dropdowns follow the theme (audit 2026-07-15 High#1/#2) (#9642).
- **CORS origins come from config again** — `api/main.py` hardcoded `https://anyplot.ai`,
  leaving the promised `https://www.anyplot.ai` origin blocked and `settings.cors_origins`
  dead; the middleware now reads the settings list (audit 2026-07-15 Low) (#9642).
- **Agentic runbook fixes** — workflow-module artifacts land in `agentic/runs/` again (a
  doubled path segment wrote to `agentic/agentic/runs/`), and the run-timeout error derives
  its duration from the actual timeout instead of a hardcoded "5 minutes"
  (audit 2026-07-15 Medium#30, Low) (#9642).
- **Documentation reconciled with the 15-library reality** — generation/similarity/repair
  prompts, `prompts/workflow-prompts/README.md`, `/prime`, `.github/copilot-instructions.md`,
  and `agentic/docs/project-guide.md` no longer claim 9/11 Python-only libraries; the repair
  prompt says attempt `{ATTEMPT}/4` matching the workflow; `docs/reference/plausible.md` drops
  the removed `potd_dismiss`/PlotOfTheDay events; the README documents Streamable HTTP as the
  only MCP transport (the SSE endpoint is gone); stale `plot.png` code examples are
  theme-aware; a leaked personal `file://` path was scrubbed from a palette doc
  (audit 2026-07-15 Medium#14/#24/#26/#27/#31/#32/#33) (#9642).
- **Global keyboard shortcuts no longer hijack focused elements on `/plots`** — the
  window-level Space/Enter/Backspace handler now bails out when the keystroke targets an
  interactive element (button, link, focused card/chip/toggle), so keyboard-activating a card
  no longer double-fires with a random-plot jump (audit 2026-07-08 Quick Win 1) (#9620).
- **Dark-mode contrast for stock MUI components** — the MUI palette is locked to light-mode
  hexes (it can't hold CSS variables), so unselected tab labels, dividers, skeletons, and
  alerts rendered light-theme colors on dark backgrounds (~2.1:1 label contrast). MuiTab,
  MuiDivider, MuiSkeleton, and MuiAlert are now wired to the CSS-var system
  (`--ink-soft`/`--rule`/`--bg-elevated`), and the two `borderColor: 'divider'` usages in
  SpecTabs/RelatedSpecs use `var(--rule)` (audit 2026-07-08 High#4) (#9622).
- **Review rubric finally knows all 15 libraries** — the workflow-active reviewer prompt and
  scoring criteria still described the 9-Python-library era: the file-extension guide called
  highcharts Python and knew no `.js`/`.tsx`, SC-04's title rule rejected `javascript` (and in
  `quality-criteria.md` even `julia`) as a language token — silently costing every correct
  JS/Julia title points — `${LANGUAGE}`/`${EXT}` were referenced in the prompt but never passed
  by `impl-review.yml`, the interactive-fairness rules (don't penalize hover/zoom invisible in
  the PNG) lived only in a file no workflow reads, and the step-10 `review_checklist.json`
  example still showed the pre-rebalance 5-category shape (`library_features`, 40/25/20/10/5
  maxima) that corrupted ~6% of stored checklists. All lists are corrected to the canonical
  registry, the fairness rules (plus a JS-harness note for CQ-05) moved into the running prompt,
  AR-05 gained rows for chartjs/d3/echarts/muix, and new registry-derived tests in
  `tests/unit/prompts/` fail on any future library-list drift (audit 2026-07-08 Medium#1 +
  Medium#12) (#9623).
- **15-library drift sweep across secondary surfaces** — four independent audit findings traced
  to the same root cause: the library expansion never propagated beyond the pipeline.
  `core/constants.py` now derives `LIBRARY_NAMES`/`LANGUAGE_NAMES` from the canonical registry
  and `insights.py`/`debug.py` import them instead of hand-written maps (the `/debug` page
  showed raw ids for all four JS libraries), `app/index.html` meta/OG/Twitter/JSON-LD copy and
  the landing tagline no longer say "9 python libraries" (now 15 libraries across Python, R,
  Julia & JavaScript; JSON-LD keywords refreshed, stale okabe-ito reference replaced by the
  Imprint palette), and `scripts/evaluate-plot.py` dropped its dead Python-era highcharts
  pattern block and derives the AR-07 static-library set from the registry (audit 2026-07-08
  Medium#5 + Medium#6 + Low#8) (#9624).
- **Analytics hygiene: bots out, /plots visible, docs in sync** — nginx's `/api/event`
  Plausible proxy now returns 202 (without forwarding) for crawler UAs and headless/automation
  clients (HeadlessChrome, puppeteer/playwright/selenium, scripted HTTP libraries, empty UA) —
  the unfiltered synthetic waves inflated visitor counts ~40% and broke trend lines. Pageview
  URLs keep the real pathname for reserved pages, so `/plots` no longer records as `/` (the
  site's #2 page was invisible in Plausible; filter paths move from `/lib/x` to `/plots/lib/x`),
  and `/debug` fires a pageview at all. `docs/reference/plausible.md` caught up with the shipped
  product: `/map` + `/debug` pages, `nav_map` source, the previously undocumented
  `library_filter` event with its `framework` prop, and the 15-library value list (audit
  2026-07-08 High#7 repo-side + Medium#10 + Low#12/#15) (#9625).
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

### Security

- **Issue templates no longer auto-apply workflow trigger labels** — `spec-request` /
  `report-pending` previously flowed unauthenticated issue text straight into write-privileged
  Claude agents; the labels must now be added by a maintainer (GitHub requires triage rights to
  label), which puts a human review in front of every agent run (audit 2026-07-15 High#7) (#9642).
- **Composite actions SHA-pinned** — `setup-node`/`setup-r`/`setup-julia` used floating tags
  while every workflow pins to SHAs; all four `uses:` refs are now SHA-pinned and the
  Dependabot `github-actions` entry covers the composite-action directories so the pins stay
  fresh (audit 2026-07-15 Medium#13) (#9642).
- **Frontend nginx ships security headers** — new `app/security-headers.conf` (CSP tuned to
  Plausible/GCS/API needs, `nosniff`, `X-Frame-Options SAMEORIGIN`, `Referrer-Policy`, HSTS)
  included in both server blocks and re-included in every `add_header` location
  (audit 2026-07-15 Medium#21) (#9642).

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
