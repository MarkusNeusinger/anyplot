# anyplot.ai — design conventions

anyplot.ai is a reference catalogue styled like **a code editor over a paper magazine**: warm editorial paper × terminal/tmux overlay (arXiv × lazygit, *never* a SaaS dashboard or AI-startup landing). Code is the native register — section headers carry shell prompts, buttons read as method calls.

## Setup (required)

Every component is MUI-based and reads the anyplot theme + design tokens from context. Always wrap your tree in **`AppProviders`** (a DS export): it applies the MUI `ThemeProvider` (anyplot theme), `CssBaseline`, and an in-memory router so the link-bearing components render. Without it, components fall back to MUI defaults and lose the brand.

```jsx
const { AppProviders, SectionHeader, CodeHighlighter } = window.Anyplot;

ReactDOM.createRoot(document.getElementById('ds-root')).render(
  <AppProviders>
    <div style={{ maxWidth: 'var(--max)', margin: '0 auto', padding: '0 var(--gutter)' }}>
      <SectionHeader prompt="❯" title={<>browse the <em>full</em> catalog</>} linkText="all plots →" linkTo="/plots" />
      <CodeHighlighter language="python" code={'import anyplot as ap\nap.plot()'} />
    </div>
  </AppProviders>
);
```

Link `styles.css` once — it `@import`s the tokens, MonoLisa fonts, and component styles. **Dark mode** flips via `[data-theme="dark"]` on `<html>`; never hard-code light/dark colors — the `var(--*)` tokens adapt automatically.

## Styling idiom — CSS custom properties (+ MUI `sx`)

Style with the `var(--*)` tokens, not invented hex. The vocabulary (all defined in `styles.css`):

- **Surfaces** — warm off-white, *never* pure `#fff`: `--bg-page`, `--bg-surface`, `--bg-elevated`
- **Ink** (warm grayscale text) + hairlines: `--ink`, `--ink-soft`, `--ink-muted`, `--rule`
- **imprint palette — 8 categorical hues, reserved for PLOTS/charts, not UI chrome:** `--imprint-green` (`#009E73`, the brand), `--imprint-lavender`, `--imprint-blue`, `--imprint-ochre`, `--imprint-red`, `--imprint-cyan`, `--imprint-rose`, `--imprint-lime`; `--imprint-amber` = warning.
- **Type stacks:** `--mono` ( = `--serif` = `--sans`, all MonoLisa); **code surface:** `--code-bg`, `--code-text`, `--code-border` (+ `--code-comment`/`-keyword`/`-string`/… syntax tokens)
- **Layout:** `--gutter` (24px), `--max` (1240px — paper/reading width), `--max-catalog` (2200px — plot grids)

## Typography — one typeface, two voices

**MonoLisa everywhere** — body, UI, nav, buttons, logo, headlines. There is no second font. The editorial accent is **italic**, which auto-triggers MonoLisa's `ss02` script set (enabled globally via `font-feature-settings: "ss02"` on `html`). So: upright = structure/prose/labels; `font-style: italic` = emphasis/taglines/title accents (renders as flowing script). Bold (700) only at display sizes.

## Color discipline (the core rule)

Brand green `--imprint-green` appears in only ~5–10 deliberate spots per page (logo dot, one italic accent, hover, active nav, terminal cursor). **Everything else is warm grayscale.** The 8-hue palette is precious — spend it on charts, not buttons/banners/hero backgrounds, or the plots lose their punch.

## Idioms

- **Section headers** = shell prompts: use `SectionHeader` with `prompt="❯"` (the default; `$` or `~/path/` only when it adds meaning — no other glyphs). Title renders in script italic; an `<em>` child flips to brand green.
- **Buttons & labels:** lowercase, read as code — `browse plots →`, `.copy()`, `.open()`. Self-evident, not explained.
- **Voice:** precise, understated, code-native. Avoid sales-y/corporate words ("unlock", "leverage", "powered by AI", "supercharge") and emoji.

## Where the truth lives

- `styles.css` → `_ds_bundle.css` — every token, light + dark, names verbatim from upstream.
- `guidelines/style-guide.md` — the full brand guide (palette rationale, type roles, three-tier layout, animation, anti-patterns). Read it before introducing anything new.

## Don't

- Pure `#fff` / `#000` backgrounds — use `--bg-page` and the dark tokens.
- The categorical palette on UI chrome — it belongs to plots.
- A second font, or decorative italic — italic is semantic emphasis only.
