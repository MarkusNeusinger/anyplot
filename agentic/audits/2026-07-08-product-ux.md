# Audit Report: anyplot

**Date:** 2026-07-08 | **Scope:** product/UX (pipeline, rating criteria, tabs, functions, "interesting · minimalistic · beautiful · self-explanatory · fast · sensible") | **Mode:** full | **Engine:** workflow
**Health Score:** 43 | **Baseline:** ruff: 0 issues, format: clean (146 files)
**Auditors:** 8 ran (llm-pipeline, frontend, design, pagespeed, backend, seo, plausible, catalog) | **Findings:** 67 raw → 64 after dedup (57 actionable + 7 positive) | **Auto-fixable:** 2/57 (codemod), rest manual
**External sources:**
- Plausible site: anyplot.ai — Stats v1+v2, 30d window ending 2026-07-08 (full)
- PageSpeed: **blocked** — anonymous PSI quota 429 on 5/5 runs; no lab timestamps (5th consecutive audit)
- Search Console mode: structural-only (gcloud token lacks `webmasters.readonly` scope)
- Catalog: 324 specs / 3,261 metadata files (filesystem pass) + 7-URL GCS HEAD sample
- Not in scope this run: gcloud, github, security, infra, quality, db, observability, agentic auditors

## Dimension Scorecard (how close to exemplary?)

| Dimension | Grade | Score | Findings (C/H/M) | Biggest lever |
|---|---|---|---|---|
| Security | A+ | 100 | 0/0/0 | (limited by scope — security-auditor not in this run; 1 low: raw DB error text reaches clients) |
| Speed | A | 91 | 0/1/6 | Prewarm `/plots/filter` + `/specs/map` at startup — the two heaviest user-facing payloads are cold |
| Looks | A | 92 | 0/2/2 | Dark-mode styleOverrides for stock MUI components (tabs/dividers/skeletons fail contrast on dark) |
| Modern | A | 94 | 0/1/3 | Enrich the bot-serving HTML template — Google currently gets title+description only, no code |
| Correctness | B | 75 | 1/3/6 | **Fix the @seo_proxy 502 — every search/social crawler gets HTTP 502 on every page** |
| Maintainability | A | 91 | 0/0/9 | Resume targeted regen: 136 specs are still Python-only (70% of catalog below full coverage) |

## Summary

The product core is in genuinely strong shape — token-disciplined design system, exemplary caching architecture, 0 ruff issues, 0 null quality scores across 3,261 metadata files, and analytics that can actually answer product questions. Two things drag the score: a **critical crawler outage** (nginx routes every bot UA to a broken `@seo_proxy` hop → sustained 502s = de-facto noindex of the whole site) and a cluster of **"the 15-library expansion never propagated"** drift (rubric prompts, index.html/OG copy, plausible.md, debug library names all still describe the 9-Python-library era). Third theme, straight at your question: the **quality score no longer discriminates** (median 89 vs the rubric's own 72–78 target) and the **spec-detail tabs aren't self-explanatory** (all-collapsed on first visit, quality tab is a bare number). Shortest path to exemplary: fix the 502 today, then the two Quick Wins, then the dark-mode MUI overrides and the seo-proxy enrichment.

## Quick Wins (Importance ≥4 & Effort=S)

| # | Finding | Dim | Auto-fix | Files | Hint |
|---|---------|-----|----------|-------|------|
| 1 | Global Space/Enter/Backspace shortcuts on /plots fire even when a card/chip/toggle has keyboard focus | correctness | manual | `app/src/pages/PlotsPage.tsx`, `ImageCard.tsx` | Bail out when `e.target.closest('button,[role="button"],[tabindex],a')` in the window keydown handler |
| 2 | Gallery cold path not prewarmed: `/plots/filter` + `/specs/map` missing from startup prewarm/SWR | speed | manual | `api/main.py`, `api/routers/plots.py`, `specs.py` | Add `filter:all` + `_refresh_specs_map` to the `_prewarm_cache()` refreshers tuple |

## Critical (Importance 5)

| # | Finding | Dim | Effort | Auto-fix | Files | Hint |
|---|---------|-----|--------|----------|-------|------|
| 1 | Every search/social crawler gets HTTP 502 on every page — nginx `$is_bot` map routes to broken `@seo_proxy` TLS hop (verified on /, /plots, /about, spec + impl pages for googlebot/bingbot/twitterbot/discord/slack/whatsapp UAs; sustained 5xx = de-facto site-wide noindex) [CV:KEEP] | correctness | M | manual | `app/nginx.conf`, `api/routers/seo.py` | Reproduce in the container (`curl -A Googlebot`), check upstream SSL verify failure; likely CA bundle / `proxy_ssl_server_name on` fix. Then add the synthetic bot-UA check (see High #6 / Medium) |

## High (Importance 4)

| # | Finding | Dim | Effort | Auto-fix | Files | Hint |
|---|---------|-----|--------|----------|-------|------|
| 1 | Global keyboard shortcuts hijack focused cards/chips on /plots (Quick Win 1) [CV:KEEP] | correctness | S | manual | `PlotsPage.tsx`, `ImageCard.tsx` | Interactive-element bail-out in window keydown |
| 2 | Gallery cold path not prewarmed (Quick Win 2) [CV:KEEP] | speed | S | manual | `api/main.py`, `plots.py`, `specs.py` | Extend `_prewarm_cache()` refreshers |
| 3 | Quality score no longer discriminates: catalog median 89 vs rubric's own 72–78 target (3,261 scores: 87% ≥85, 1% <72; anti-inflation anchors demonstrably not applied; daily-regen picks oldest, not worst) [CV:KEEP] | correctness | L | manual | `prompts/quality-criteria.md`, `prompts/workflow-prompts/ai-quality-review.md`, `.github/workflows/daily-regen.yml` | (1) store first-review score next to final score, (2) add 2–3 image anchor few-shots ("this is a 70 / a 90"), (3) point daily-regen at lowest-scoring specs so the score becomes load-bearing |
| 4 | MUI palette locked to `mode:'light'` — stock MUI components fail contrast in dark theme (unselected tab labels ~2.1:1 on dark bg, dividers/skeletons/alerts wrong) [CV:KEEP] | looks | M | manual | `app/src/theme/palette.ts`, `theme/components.ts`, `SpecTabs` | styleOverrides from the CSS-var system: MuiTab → `var(--ink-soft)`, MuiDivider → `var(--rule)`, MuiSkeleton → `var(--rule)` |
| 5 | Spec-detail tabs not self-explanatory: all-collapsed on first visit (main content hidden), click-to-collapse has no affordance, quality tab is an unexplained bare number [CV:KEEP] | looks | M | manual | `app/src/sections/spec-detail/SpecTabs/index.tsx` | Default-open the Code tab in detail mode; drop or signal the collapse toggle; label "quality 87" or tooltip "87/100 ai review score" |
| 6 | Pages served to Googlebot are thin shells: title+description only — no code sample, no JSON-LD, no internal links (the site's actual value never reaches the index) [CV:KEEP] | modern | M | manual | `api/routers/seo.py`, `app/nginx.conf` | Enrich `BOT_HTML_TEMPLATE`: `<pre>` code block, preview `<img>`, BreadcrumbList + SoftwareSourceCode JSON-LD, hub↔impl `<a>` links |
| 7 | ~40–45% of recorded visitors are unfiltered crawler traffic (China 349/~830 visitors at 0.44 pv/visitor; headless-Chrome waves firing CWV without pageviews) — inflates visitors, breaks trend lines [CV:KEEP] | correctness | M | manual | `plausible:event/pageview`, `app/index.html`, nginx `/api/event` proxy | Drop datacenter-ASN / HeadlessChrome UAs at the event proxy; country exclusions in Plausible; filter CN/RU when reading history |

## Medium (Importance 3)

| # | Finding | Dim | Effort | Auto-fix | Files | Hint |
|---|---------|-----|--------|----------|-------|------|
| 1 | Stale 5-category checklist example in reviewer prompt corrupts stored review JSON (~6% of shipped review checklists shape-inconsistent: `library_features` vs `library_mastery`, stray keys) | correctness | S | manual | `prompts/workflow-prompts/ai-quality-review.md` | Rewrite the step-10 example to the canonical 6-category shape + "exactly these six keys"; optional one-off normalization of existing YAMLs |
| 2 | `/libraries/{id}/images` loads the entire ~13MB code corpus of ALL libraries to serve one | speed | S | manual | `api/routers/libraries.py`, `core/database/repositories.py` | `get_by_library(...)` + `undefer(code)`, or delete the endpoint if no consumer; wrap in `get_or_set_cache` |
| 3 | MCP tools return broken `website_url` `/python/{spec_id}` instead of `/{spec_id}` (3 call sites) | correctness | S | manual | `api/mcp/server.py` | Replace with `/{spec.id}`; unit-test URL shape against the sitemap tiers |
| 4 | `/proxy/html` refetches interactive plot HTML from GCS per iframe load — fresh client, no cache, no Cache-Control | speed | S | manual | `api/routers/proxy.py`, `api/main.py` | Shared client + `get_or_set_cache` keyed on (url, origin) + add `/proxy/html` to cache-header whitelist |
| 5 | Library display names hand-duplicated in 3 places; `/debug` already shows raw ids for the 4 JS libs | maintainability | S | manual | `api/routers/insights.py`, `debug.py`, `core/constants.py` | Derive `LIBRARY_NAMES` once from `LIBRARIES_METADATA` |
| 6 | Stale "9 python libraries" copy across index.html meta/OG/Twitter/JSON-LD ×5 + LandingPage; head tags also duplicate (Helmet appends, doesn't replace shell defaults) *(merged: design + seo)* | modern | S | manual | `app/index.html`, `app/src/pages/LandingPage.tsx` | Update to 15-libraries/4-languages (or count-free copy); move head defaults into a root-layout Helmet block so per-route tags replace |
| 7 | Nav vocabulary assumes insider knowledge: specs vs plots, `mcp`, `pal`/`libs` shorthands — no tooltips | looks | S | manual | `app/src/layouts/NavBar.tsx` | Title/Tooltip per NAV_LINK in the masthead comment style; keep the minimal aesthetic |
| 8 | Cloudflare-managed robots.txt blocks all AI assistant crawlers (ClaudeBot, GPTBot, CCBot, Google-Extended `Disallow: /`) — overrides the `use=reference` content signal | modern | S | manual | Cloudflare dashboard, `app/public/robots.txt` | Deliberate decision: allow retrieval/citation crawlers, keep training blocks if desired |
| 9 | PSI lab visibility blocked for the 5th consecutive audit — `PAGESPEED_API_KEY` never provisioned | speed | S | manual | `psi:*`, `agentic/audits/latest.md` | Free GCP API key with PSI API enabled → secret `PAGESPEED_API_KEY` |
| 10 | `/plots` pageviews recorded as `/` — the #2 page is invisible in analytics (47 visitors, 0 pageviews in 30d) | correctness | S | manual | `app/src/hooks/useAnalytics.ts` | Keep the `/plots` prefix in `buildPlausibleUrl` for reserved routes that are real pages; `/debug` fires no pageview at all |
| 11 | AR-06/08/09 score-0 auto-rejects collide with impl-review's score==0 "invalid output" path — legit rejections never reach impl-repair, land as `ai-review-failed` | correctness | M | manual | `.github/workflows/impl-review.yml`, rubric prompts | Distinct sentinel (`auto_reject.txt`) checked before the invalid-score branch, or map AR-rejects to score=1 |
| 12 | Rubric prompts don't know 4 of 15 libraries exist: JS libs missing from workflow-active reviewer; SC-04 penalizes every JS impl; `${LANGUAGE}`/`${EXT}` never supplied; interactive-fairness rules live only in a file that never runs | maintainability | M | manual | `prompts/workflow-prompts/ai-quality-review.md`, `quality-criteria.md`, `quality-evaluator.md`, `impl-review.yml` | Pass LANGUAGE/EXT from `core/constants.py` as run vars; regenerate library lists; move interactive-fairness + per-language CQ guidance into the files that run |
| 13 | FilterMenu arrow-key highlight never scrolls into view; search input lacks combobox ARIA | correctness | M | manual | `FilterMenu.tsx`, `FilterSearch.tsx` | `aria-activedescendant` + `scrollIntoView({block:'nearest'})` on highlight change |
| 14 | Duplicated 50-line tag-chip rendering block in SpecTabs (spec tags vs impl tags) | maintainability | M | manual | `SpecTabs/index.tsx` | Extract `TagChipGroup` and render twice |
| 15 | react-helmet-async is archived/unmaintained; React 19 hoists `<title>/<meta>` natively | modern | M | codemod | `routes/index.tsx`, 4 pages, `useUrlSync.ts` | Mechanical: bare `<title>/<meta>` per page, drop HelmetProvider + dependency |
| 16 | Hover-only card actions unreachable on touch and invisible to keyboard focus (ImageCard copy button opacity:0 but in tab order; SpecOverview action row same) *(merged: frontend + design)* | looks | M | manual | `ImageCard.tsx`, `SpecOverview.tsx` | Reveal on `:focus-visible`/`:focus-within`; `@media (hover:none)` low-opacity always; theme-adapt the white pill |
| 17 | No synthetic monitoring of the bot-serving path (exactly how the 502 outage shipped and persisted) + no Search Console API access | maintainability | M | manual | `app/nginx.conf`, `.github/workflows/` | Scheduled action curling 2–3 prod URLs with Googlebot/Twitterbot UA, fail on non-200 or missing `<title>`; post-deploy + daily |
| 18 | Usage reality: code tab + spec-detail copy ARE the product (all 29 copy_code from spec_detail); quality tab, random filter, grid quick-copy, feedback widget, POTD, map search/pin, og-sharing effectively dead in 30d | maintainability | M | manual | `plausible:event/tab_toggle`, `ImageCard.tsx`, `FeedbackWidget.tsx` | Optimize the code-tab/copy flow; surface or prune the dead periphery; check grid copy button actually renders |
| 19 | New-spec creation nearly stalled: May 0, Jun 10, Jul 0 (vs Dec–Mar 27–159/mo) — "spannend" needs fresh subject matter | maintainability | M | manual | `plots/*/specification.yaml` | Light cadence: one themed batch of 5–10 spec requests/month (June's sports batch was the model) |
| 20 | Last 3 old-design metadata files: line-stress-strain (bokeh, letsplot), heatmap-cohort-retention (plotnine) still single-preview, no dark variant | correctness | M | manual | `plots/line-stress-strain/metadata/...`, `plots/heatmap-cohort-retention/metadata/...` | Three targeted impl-generate runs finish the light/dark migration at 100% |
| 21 | Field Web Vitals (human-only): LCP p75 right at the 2.5s boundary, FCP/TTFB p75 needs-improvement; raw dashboard numbers are bot-skewed 3× worse | speed | L | manual | `plausible:event/LCP`, `TTFB`, `app/index.html` | TTFB is the lever (Cloud Run region/cold starts, edge caching); re-measure after bot filtering lands |
| 22 | Gallery has no list virtualization — DOM grows unbounded browsing the full catalog (~4,900 impls) | speed | L | manual | `ImagesGrid.tsx`, `useInfiniteScroll.ts` | react-virtuoso VirtuosoGrid; interim: derive tooltip state, cap batches |
| 23 | Three monolithic pages (PalettePage 2027*, DebugPage 1898, MapPage 1292 lines) break the otherwise clean sections/ decomposition (*PalettePage.helpers.ts extraction landed in PR #9616 during this audit) | maintainability | L | manual | `PalettePage.tsx`, `DebugPage.tsx`, `MapPage.tsx` | Extract sections/palette, sections/map, sections/debug with co-located tests |
| 24 | Flagship 3D/geo specs are the sparsest (6–7 impls, Python-only) and missing makie — the library that would shine there | maintainability | L | manual | `plots/scatter-3d/`, `surface-basic/`, 10 more | Targeted regen (makie, echarts, ggplot2) on the 3D cluster first; record legitimate per-library exclusions explicitly |
| 25 | 70% of the catalog lacks the newer libraries — 136 specs still Python-only (8 impls), only ~65 at 14–15 | maintainability | XL | manual | `plots/`, `core/constants.py` | Resume babysit-pipeline systematically; burn down the 8/9/10-impl buckets with targeted (not `all`) regen |

## Low (Importance 2)

| # | Finding | Dim | Effort | Auto-fix | Files | Hint |
|---|---------|-----|--------|----------|-------|------|
| 1 | Tabs/TabPanel missing id/aria-controls wiring; click-to-collapse is nonstandard tabs semantics | correctness | S | manual | `SpecTabs/index.tsx`, `md.tsx` | Standard a11yProps helper |
| 2 | NavBar search button loses focus indicator via `all:unset`; active link lacks `aria-current` | correctness | S | manual | `NavBar.tsx` | `:focus-visible` outline + `aria-current="page"` |
| 3 | Motion/focus polish: `rise` + loader animations ignore `prefers-reduced-motion`; MapPage/DebugPage remove outlines without replacement | looks | S | manual | `tokens.css`, `LoaderSpinner.tsx`, `MapPage.tsx` | Extend the reduced-motion block; copy SpecDetailView's focus-visible pattern |
| 4 | Hero stacks three competing taglines; centered "from .md to art." breaks the left-aligned rhythm | looks | S | manual | `HeroSection.tsx` | Keep one emotional tagline (typewriter), left-align the rest |
| 5 | DatabaseQueryError reflects raw SQLAlchemy error text to API clients (contradicts the no-leak policy in the same file) | security | S | manual | `api/routers/plots.py`, `api/exceptions.py` | Log detail server-side; generic client message |
| 6 | Cloud SQL async fallback wraps a sync pg8000 engine in async_sessionmaker — would 500 on first query if ever configured | correctness | S | manual | `core/database/connection.py` | Fail fast with RuntimeError in that branch |
| 7 | Leftover `/hello/{name}` demo endpoint on the production API; three conflicting version strings | maintainability | S | manual | `api/routers/health.py` | Delete; source version from one constant |
| 8 | Previous-gen model default (`claude-sonnet-4-6`) + dead Python-highcharts pattern block in local evaluator | modern | S | manual | `core/config.py`, `scripts/evaluate-plot.py` | Bump to claude-sonnet-5 after side-by-side; derive patterns from constants |
| 9 | pagespeed-auditor brief's auth contract is factually wrong ("works without a key … plenty") — failed 5/5 runs | maintainability | S | manual | `agentic/commands/audit/pagespeed-auditor.md` | Rewrite: key required in practice; probe once, fail fast to blocked |
| 10 | python.anyplot.ai nginx server block + docs exist but DNS doesn't resolve — dead config invites drift | maintainability | S | manual | `app/nginx.conf`, `docs/reference/seo.md` | Finish the launch or delete the block; one-line decision comment |
| 11 | Cross-site links (now on /legal per maintainer decision): consider ONE contextual sentence on /about with a descriptive anchor for kurrentschrift; the rel handling (`noopener`, no `noreferrer`, followed) is right *(merged: design + seo; original footer-placement advice overtaken by events)* | modern | S | manual | `app/src/pages/AboutPage.tsx` | Optional follow-up; sitewide keyword-anchor links would look spammy — brand anchor is correct |
| 12 | Ghost event `library_filter` with unregistered `framework` prop, undocumented (9 events/30d, values invisible in dashboards) | maintainability | S | manual | `LibrariesPage.tsx`, `docs/reference/plausible.md` | Rename into taxonomy or register+document the prop |
| 13 | Outbound clicks double-tracked: auto "Outbound Link: Click" (33) overlaps custom `external_link` (12) | maintainability | S | manual | `app/index.html`, `docs/reference/plausible.md` | Pick one; document the survivor |
| 14 | `search_no_results` shows real content gaps (backtest equity curve, arrow/flow map) but 200ms debounce leaks keystrokes | maintainability | S | manual | `FilterBar.tsx` | File the two spec requests; fire on ~1s idle or blur/enter |
| 15 | plausible.md (updated 2026-04-25) + index.html drifted from the shipped product (missing nav_map, library_filter, /map, /debug; 9-library lists) | maintainability | S | manual | `docs/reference/plausible.md`, `app/index.html` | One doc-sync pass regenerating event tables from code |
| 16 | Git-tracked strays in plots/: two ~200KB render PNGs (gitignore matches but never untracked), leaked `_run_plotly.py`, 5 stale .gitkeep | maintainability | S | manual | `plots/bar-basic/...`, `plots/contour-3d/...` | `git rm --cached`; grep automation/ before deleting the runner |
| 17 | plot_type synonym drift: 6 singletons ('graph', 'curve', 'evaluation', …) where established tags exist (advisory facets policy-exempt, untouched) | maintainability | S | manual | 6 `specification.yaml` files | Normalize the synonyms only |
| 18 | 118 specs have `updated: null`; date quoting inconsistent across generations of tooling | maintainability | S | codemod | `plots/*/specification.yaml` | One-shot codemod: `updated := created` where null; normalize quoting |
| 19 | Duplicate-adjacent spec clusters (regression-linear/-polynomial/-lowess; sma/ema) read as variations of one page | maintainability | S | manual | `plots/scatter-regression-*/`, `plots/indicator-*ma/` | Cross-check traffic; consider merging weak siblings into variants |
| 20 | evaluate-plot.py: no prompt caching (image-first ordering defeats it), tight max_tokens, freeform JSON instead of structured output | modern | M | manual | `scripts/evaluate-plot.py`, `core/config.py` | Rubric-first + cache_control, ~4000 max_tokens, json_schema output format |
| 21 | `search_by_tags` matches via substring LIKE over stringified JSON — cross-category false positives, unindexable | correctness | M | manual | `core/database/repositories.py` | JSONB containment per category (`@>`) + optional GIN index |
| 22 | Ten sub-70 quality-score impls sit approved, 7/10 are pygal faking contours/maps/trees it has no primitives for | correctness | M | manual | `plots/*/metadata/python/pygal.yaml` ×7, altair ×2, seaborn ×1 | Regenerate with opus per the migration playbook, or allow explicit per-library opt-outs |
| 23 | useUrlSync bypasses React Router with raw `history.replaceState` — router location permanently stale on /plots, Back leaves the page | maintainability | M | manual | `useUrlSync.ts`, `useFilterState.ts` | Document as intentional or migrate to `useSearchParams(..., {replace:true})` |

## Positive Patterns (Importance 1)

- **Two-stage rubric + review-pipeline resilience** — 9-check auto-reject with false-positive guards, "correct but boring" cap, both-themes checklist, cascading review/repair. Reference this structure; don't redesign it (llm-pipeline).
- **Frontend engineering baseline** — green strict tsc on app+test configs, ~zero `any`, 80+ co-located test files, all-lazy routes with route-scoped error boundaries, typed API layer (frontend).
- **Token discipline & coherent terminal-editorial design language** — single CSS-var source, AA-checked ink scales, theme-adaptive previews, method-call microcopy (design).
- **Caching architecture** — per-key stampede locks with lifecycle-bound pruning, SWR with self-owned sessions, startup prewarm, deferred multi-MB columns, batched sync (backend).
- **Sitemap pipeline** — 324/324 specs, zero drift both directions, documented duplicate-content decisions (seo).
- **Analytics instrumentation** — 31-event taxonomy with journey props that answered "what do visitors actually do" directly from live data (plausible).
- **Metadata review layer** — 0 null quality_scores across 3,261 files, zero manual-merge bypasses detected, 100% consistent spec structure, all sampled previews live (catalog).

## Statistics

- Total: 57 actionable (+7 positive) | Critical: 1, High: 7, Medium: 25, Low: 23 (+1 medium became part of a merge)
- By Dimension: security 1, speed 7, looks 6, modern 7, correctness 15, maintainability 21
- Effort: S 31, M 20, L 5, XL 1
- Auto-fix: codemod 2, manual 55
- By Auditor (raw): llm-pipeline 7, frontend 11, design 9, pagespeed 2, backend 11, seo 8, plausible 9, catalog 10 — 3 cross-auditor merges applied
- Cross-validation: 8 reviewed (all importance ≥4), 0 dropped, 0 downgraded — every high-severity finding survived an independent domain-expert refutation attempt
- Coverage: 3 full (frontend, plausible, catalog), 4 partial/structural (llm-pipeline, design, backend, seo), 1 blocked (pagespeed — anonymous PSI quota; recurring, see Medium #9)

## Cross-auditor themes (synthesis)

1. **"The 15-library expansion never propagated to secondary surfaces"** — found independently by four auditors: rubric prompts (llm-pipeline M12), index.html/OG/JSON-LD copy (design+seo M6), plausible.md + event docs (plausible L15), debug/insights library names (backend M5). One sweep with `core/constants.py` as the single source closes all of them.
- **Lab vs field Web Vitals divergence**: not computable — pagespeed blocked (5th time). Field-only verdict: interaction is fast (INP/CLS good), first paint is the weak spot, TTFB the lever.
- **Deprecation candidates**: catalog's duplicate clusters (regression trio, sma/ema) should be cross-checked against per-spec traffic before merging — per-spec Plausible breakdown wasn't pulled this run.
