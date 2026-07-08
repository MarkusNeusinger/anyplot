---
name: verify-frontend
description: Run and visually verify the anyplot app after frontend changes — start the dev servers, click through ONLY the flows the change touches via a browser MCP (claude-in-chrome or the Playwright plugin locally, playwright-core probe in the cloud), watch console and network, and judge style and legibility at a desktop AND a mobile viewport in BOTH light and dark theme. Use when asked to run, start, screenshot, verify, test in the browser, or visually check the app or a frontend change.
---

# Verify the frontend in the browser

React 19 + Vite 8 SPA (`app/`, port 3000, yarn) backed by the FastAPI
service (`api/`, port 8000). The frontend calls the API directly at
`VITE_API_URL || http://localhost:8000` (`app/src/global-config.ts`) —
there is **no Vite proxy and no `/api` prefix** on backend routes.
All paths below are relative to the repo root.

This skill is a **feedback loop**: after a frontend change, don't just
confirm the page loads — drive it like a user and observe four
channels: interaction (snapshots/clicks), console + network, visual
style & legibility (screenshots at two viewports × two themes,
actually looked at), and performance when plausibly affected.
Report findings; don't silently "fix" design questions.

**Scope: only what the change touches.** Derive affected pages from
the diff (`git diff --name-only origin/main...` + the route registry
in `app/src/routes/`) and drive exactly those. Shared code
(`lib/api`, theme module, `layouts/`, `components/`) widens the scope
to representative consumers; everything the diff cannot reach is out
of scope. Structure and conventions: `app/ARCHITECTURE.md`.

## 1 · Start the servers (skip if already up)

Check first — they are often already running:

```bash
curl -fsS http://localhost:8000/health && curl -fsS -o /dev/null -w 'vite:%{http_code}\n' http://localhost:3000/
```

If not, start both in the background (Bash `run_in_background: true`):

```bash
uv run python -m api.main
```

```bash
cd app && yarn && yarn dev
```

Expected: `/health` returns 200 and `vite:200`. Then prove the DB
path end to end:

```bash
curl -fsS http://localhost:8000/libraries | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d), "libraries")'
```

Expected: `15 libraries`. **Note the DB is the shared Cloud SQL
production database** (see `/verify-api` gotchas) — the frontend is
read-only against it, but anything that writes (feedback widget)
lands in real data.

## 2 · Drive the app

Pick the harness by what ToolSearch finds (one `select:` query, names
comma-separated **without whitespace**):

- **`mcp__claude-in-chrome__*`** (user's real Chrome): core set
  `tabs_context_mcp,navigate,computer,read_page,tabs_create_mcp`, plus
  `read_console_messages,read_network_requests` for the channels.
  Call `tabs_context_mcp` first; create a new tab, don't reuse.
- **`mcp__plugin_playwright_playwright__browser_*`** (isolated
  Chromium): `browser_navigate,browser_snapshot,browser_click,
  browser_take_screenshot,browser_console_messages,
  browser_network_requests,browser_resize`.
- **Neither found** (Claude Code on the web) → §2b cloud fallback.

The loop, per page/flow the diff touches:

1. Navigate to `http://localhost:3000/<route>`.
2. **Resize before judging.** Check **both** viewports for every
   in-scope surface: 1440×900 (desktop) and 390×844 (mobile).
3. **Check both themes.** The masthead's `◐` toggle cycles
   system → light → dark. Judge every in-scope surface in light AND
   dark — theme-adaptive chrome and dual plot previews
   (`plot-light`/`plot-dark` image variants) are core product
   features; a surface that only works in one theme is a finding.
4. After navigation to a lazy route, wait for text unique to the
   target page before snapshotting.
5. Screenshot to `/tmp/anyplot-ui/<page>-<viewport>-<theme>.png` and
   **Read the file — actually look at it**. A DOM snapshot proves
   presence; only the screenshot shows clipped layouts, illegible
   type, wrong plot variant.
6. Read console messages after each flow — any new error/warning is a
   finding (see Gotchas for known noise).
7. Scan network requests once per page for 4xx/5xx. A plot page's
   preview image must come from the GCS URL with the correct
   light/dark variant for the active theme.

Reference flows — a catalog, not a checklist; pick only what the diff
touches:

- Landing: hero, libraries / palette / specifications sections,
  masthead (branch + release tag), footer.
- `/plots`: tag-chip filtering (chips must actually narrow results),
  `?lang=` filter, search, thumbnail lazy-load.
- `/{specId}` hub → `/{specId}/{language}/{library}` detail: code
  viewer with syntax highlighting (incl. R/Julia/`.tsx`), copy
  button, PNG download, fullscreen, light/dark preview swap on theme
  change, **Interactive toggle** on JS + interactive-Python
  implementations, cross-language carousel.
- `/stats`: charts render, library list, visitors chart.
- `/palette`: color wheel, hue cards, copy-paste `IMPRINT` object.
- `/map`: force-graph renders and nodes navigate.

## 2b · Cloud fallback — playwright-core probe (no MCP)

The container ships Chromium under `PLAYWRIGHT_BROWSERS_PATH`. One-time
setup per container (scratchpad is ephemeral):

```bash
SCRATCH=<the session scratchpad dir named in the prompt>
cd "$SCRATCH" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i playwright-core
```

`PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` is load-bearing; **never run
`playwright install`.** Then start the servers (§1) and run the
bundled probe:

```bash
NODE_PATH="$SCRATCH/node_modules" SHOTS=/tmp/anyplot-ui \
  node .claude/skills/verify-frontend/cloud-probe.mjs \
  http://localhost:3000/ http://localhost:3000/plots
```

It reports, per URL × viewport (default `1440,390,360,320`, override
`WIDTHS=`): horizontal overflow + widest offender, the `h1` computed
type voice, deduped JS errors / 4xx-5xx with paths — machine-readable
lines, exact pixels. Then **Read the screenshots** under `SHOTS`. For
custom measurements or multi-step flows, extend the `evaluate()`
block in a scratchpad copy. Only when both MCP and Chromium are
absent do you fall back to static gates (`yarn build`, type-check) —
and then say plainly that no flow was driven.

## 3 · Style fidelity & legibility

Judge screenshots against `docs/reference/style-guide.md` (voice:
lowercase, monospace, no emoji; the pseudo-function styling) and the
theme tokens in `app/src/theme/` — read them fresh each run rather
than restating values here. Method:

- Compare each screenshot against what guide + tokens prescribe
  (MonoLisa type, Imprint palette accents, theme-adaptive chrome).
- Computed styles beat squinting: evaluate
  `getComputedStyle(el).fontFamily` / `.color` and match against the
  theme tokens.
- Legibility: at 390 px nothing may clip, overlap, or fall under
  ~13 px; WCAG-AA contrast holds in BOTH themes (regression watch —
  v1.1.0 fixed 15+ violations).

Style questions are **findings to report**, not things to silently
fix — palette and typography decisions are settled in the style guide.

## 4 · Performance

Only when the change can plausibly move performance (data loading,
bundle/chunk changes, list rendering) or the user asks. Watch the
known-regression spots from #7694: above-the-fold landing counts
(must not stall), `/specs` thumbnail lazy-load, `/stats` query time.
Compare against dev-mode expectations, not prod budgets.

## 5 · Run (human path)

`/start` slash command, or the two §1 commands in two terminals, then
open `http://localhost:3000/` (Vite is pinned to 3000 — not 5173).

## Gotchas

- **No `/api` prefix.** Backend routes are `/specs`, `/health`,
  `/stats`, `/libraries`, `/plots/filter`. `curl
  localhost:8000/api/specs` 404s and has repeatedly wasted rounds.
- **yarn, not npm** — `npm install` in `app/` creates a stray
  `package-lock.json`.
- **Masthead fetches the GitHub releases API live** (1 h localStorage
  cache, `useLatestRelease.ts`). Unauthenticated rate-limiting can
  403 in console — known noise locally, don't chase it, don't let it
  mask real failures.
- **`yarn dev` overlays TS/ESLint errors** (vite-plugin-checker), but
  HMR itself is permissive — a page can render while `tsc` would
  fail. The commit gate is
  `yarn lint && yarn fm:check && yarn type-check && yarn test`; Cloud
  Build additionally runs `tsc && vite build` and fails on strict-TS
  errors HMR tolerated.
- **`/debug` is Cloudflare-Access-gated in prod** — locally it talks
  to the API directly (`debugBaseUrl`), so local success does not
  prove the prod CF-cookie path.
- **Lazy routes race snapshots** — wait for target-page text before
  snapshotting; re-snapshot after any DOM change (stale uids).
- **Theme toggle is tri-state** (system/light/dark): to force a
  specific theme, click past "system", and remember the OS theme
  drives what "system" shows.

## Troubleshooting

- Port 8000/3000 already in use → the server is already running;
  just use it (that's why §1 checks first).
- Frontend loads but every list is empty + console shows CORS or
  connection errors on `:8000` → the API isn't up (or `VITE_API_URL`
  points elsewhere); fix the API first, the frontend is fine.
