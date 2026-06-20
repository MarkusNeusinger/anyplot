# design-sync notes — anyplot.ai Design System

Target project: **anyplot.ai Design System** (`bdf69a23-f0d2-40d5-b6cb-3ef035579852`) on claude.ai/design.
This is an **app-shape** sync — the *source* is the `app/` website (`anyplot-website`), not a published component library, although the converter `shape` is the normal `"package"` (see `config.json`). Only `pkg`/`globalName`/`projectId` are conventional; the rest of the config exists to make an app build like a DS.

## How this sync is wired (gotchas)

- **Curated entry, not synth.** `app/designsync-entry.tsx` re-exports the 5 reusable components + `AppProviders`. It lives OUTSIDE the app tsconfig `include` so the app build/typecheck never touch it, and it deliberately does NOT import `src/main.tsx` (which would call `createRoot().render()` on load). `cfg.entry` points at it → PKG_DIR resolves to `app/`.
- **Component list = `cfg.componentSrcMap` keys.** The app ships no `.d.ts`, so the converter's `.d.ts`-based discovery finds nothing — every synced component must be listed in `componentSrcMap`. The 8 infrastructural components (error boundaries, data/router shell, FeedbackWidget) are simply omitted.
- **Props = `cfg.dtsPropsFor` (hand-written).** No `.d.ts` ⇒ auto prop-extraction yields nothing, so each component's props interface is hand-written. **If a component's real props change upstream, update `dtsPropsFor` by hand** — nothing extracts them automatically.
- **Barrel tsconfig.** `app/tsconfig.designsync.json` maps each `src/<barrel>` folder to its `index.*` BEFORE the `src/*` wildcard. Without the explicit mappings, the esbuild tsconfig-paths plugin's empty-extension probe matches the directory itself and esbuild fails to bundle it. Add a mapping there if a new barrel import appears in the transitive graph.
- **Provider chain.** `cfg.provider = AppProviders` = `MemoryRouter` → MUI `ThemeProvider(theme)` → `CssBaseline`. `useAnalytics` is context-free (a pure hook, no-ops off `anyplot.ai`), so SectionHeader/Footer only need the router, not an analytics provider.
- **CSS / tokens.** `cfg.cssEntry = src/styles/tokens.css` (the `var(--*)` token system, incl. `[data-theme="dark"]`). Component styles are MUI/emotion injected at runtime → build prints `[CSS_RUNTIME]` (expected, non-blocking). Tokens land inside `_ds_bundle.css`, reachable via the `styles.css` `@import` closure.
- **Render check uses system chrome:** `DS_CHROMIUM_PATH=/usr/bin/google-chrome` on every build/validate/capture/driver run. Playwright is installed in `.ds-sync` with `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` (no 200 MB download). Node is v20 (works; root `engines` asks for 22 but the converter doesn't need it).
- **`assets/` is preserved in the project.** The target's `assets/*.svg` (logo/favicon/palette-strip) are hand-authored, NOT produced by this build. They were deliberately kept OUT of the delete set. **On every re-sync, keep `assets/**` out of the deletes** or the reconciliation will remove them.

## MonoLisa fonts (re-fetch on a fresh clone)

MonoLisa is proprietary (© FaceType Foundry, CORS-locked GCS) and is **NOT in this public repo**. The variable ttf are fetched at sync time into `app/.designsync-fonts/` (the `.ttf`/`.woff2` binaries are gitignored; only the `@font-face` CSS there is committed) and shipped only to the private design project — never committed. `app/.designsync-fonts/monolisa.css` (the `@font-face`, committed) references them. On a fresh clone, re-fetch before building:

```sh
mkdir -p app/.designsync-fonts && cd app/.designsync-fonts
curl -sSfo MonoLisaVariableNormal.ttf https://storage.googleapis.com/anyplot-static/fonts/MonoLisaVariableNormal.ttf
curl -sSfo MonoLisaVariableItalic.ttf https://storage.googleapis.com/anyplot-static/fonts/MonoLisaVariableItalic.ttf
```

The variable ttf cover the full glyph range (normal + italic, weights 100–900, the `ss02` script set intact). CORS is browser-only, so `curl` works even though browser fetches are restricted to `anyplot.ai`.

## Known render warns
- None. (`[RENDER_THIN]` on Footer in an early pass was fixed by collapsing its preview to a single cell — its two variants differed only in a hidden link href.)

## Re-sync risks (what can silently go stale)
- **Fonts**: a fresh clone has no ttf until re-fetched (above). If the GCS objects move or access changes, MonoLisa silently won't ship and designs render in the fallback mono stack.
- **`assets/**` deletion**: see above — must stay out of every re-sync's delete set.
- **`dtsPropsFor` drift**: hand-written props can diverge from the real components; re-check against the sources on a major app change.
- **`componentSrcMap` paths**: if a component's source file moves, its `componentSrcMap` entry must move too.
- **conventions.md token names**: re-validate against the fresh build on re-sync (the conventions-header step does this) — a renamed/removed token in `tokens.css` would make the header name something that no longer exists.
- This replaced an older **hand-authored** version of the same project (landing.html, design_system.html, source/*.tsx). That content was intentionally removed; it lives in git history if ever needed.
