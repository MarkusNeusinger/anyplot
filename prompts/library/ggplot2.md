# ggplot2

ggplot2 is the canonical implementation of the grammar of graphics in R. This
is anyplot's first R-language entry; the file extension is **`.R`** and the
runtime is **Rscript**, not Python.

## IMPORTANT: No Workarounds

**If ggplot2 cannot implement a plot type natively, DO NOT shell out to
matplotlib, Python, or another backend.**

ggplot2 is a grammar-of-graphics library. It does NOT support out of the box:

- 3D plots (no wireframes, surfaces, 3D scatter)
- Network / graph visualizations (needs `ggraph` — out of scope here)
- Geographic maps (needs `sf` / `ggmap` — out of scope here)
- True interactivity (hover, zoom, brush, animation)

If the specification requires features outside ggplot2's grammar, the
implementation should FAIL rather than fall back to another library. Each
library implementation must use only that library's native capabilities.

## Interactive Spec Handling

ggplot2 produces **static PNG only**. When implementing specs that mention
interactive features:

- Specs whose PRIMARY value is interactivity (hover, zoom, click, brush) →
  **NOT_FEASIBLE**
- Specs with animation → use small multiples / `facet_wrap` as a static
  alternative
- Mixed specs (static + interactive) → implement static features only, omit
  interactive silently
- **NEVER** simulate tooltips, hover states, or controls. See AR-08 in
  `prompts/quality-criteria.md`.

---

## Imports

```r
library(ggplot2)
library(dplyr)
library(tidyr)
library(scales)
library(ragg)        # high-quality PNG device
```

Optional dataset packages available in the CI runtime: `palmerpenguins`,
`gapminder`. Plus everything bundled with base R / ggplot2: `mtcars`, `iris`,
`diamonds`, `economics`, `mpg`, `faithful`.

## Reproducibility

```r
set.seed(42)
```

## Create Plot

```r
p <- ggplot(df, aes(x = col_x, y = col_y)) +
  geom_point() +
  labs(x = x_label, y = y_label, title = plot_title) +
  theme_minimal(base_size = 14)
```

## Figure Size & Sizing for 4800×2700 px

ggplot2 inherits sizes via `theme(... base_size = ...)`. Override individual
elements for the anyplot canvas:

```r
p <- p +
  theme(
    text             = element_text(size = 14),  # base text
    axis.title       = element_text(size = 20),  # axis labels
    axis.text        = element_text(size = 16),  # tick labels
    plot.title       = element_text(size = 24),
    legend.text      = element_text(size = 16),
    legend.title     = element_text(size = 18)
  )

# Element sizes inside geoms (~3-4× ggplot2 defaults so they survive the
# 4800×2700 canvas):
# geom_point(size = 4)
# geom_line(linewidth = 1.5)
```

## Save (PNG, both themes)

Use the `ragg` device — it antialiases properly and ignores `Cairo` system
deps:

```r
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 16,
  height   = 9,
  units    = "in",
  dpi      = 300
)
```

## Colors

Use the Okabe-Ito palette (see `prompts/default-style-guide.md` "Categorical
Palette"). First series is **always** `#009E73`.

```r
OKABE_ITO <- c(
  "#009E73",  # 1 — first categorical series
  "#D55E00",  # 2
  "#0072B2",  # 3
  "#CC79A7",  # 4
  "#E69F00",  # 5
  "#56B4E9",  # 6
  "#F0E442"   # 7
)

# Single-series
geom_point(color = OKABE_ITO[1])

# Multi-series — categorical
scale_color_manual(values = OKABE_ITO)
scale_fill_manual(values  = OKABE_ITO)

# Continuous — NOT Okabe-Ito:
scale_color_viridis_c(option = "viridis")   # sequential
scale_color_viridis_c(option = "cividis")   # sequential CVD-safe
scale_fill_distiller(palette = "BrBG")      # diverging
```

Never use `rainbow()`, `heat.colors()`, `terrain.colors()`, `topo.colors()` or
`hsv()` based palettes — they all fail CVD and luminance ordering.

## Theme-adaptive Chrome (ggplot2 mapping)

Read `ANYPLOT_THEME` from the environment and flip chrome tokens. Data colors
stay identical between themes — only the surrounding chrome changes.

```r
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

anyplot_theme <- theme_minimal(base_size = 14) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor  = element_line(color = INK, linewidth = 0.2),
    panel.border      = element_rect(color = INK_SOFT, fill = NA),
    axis.title        = element_text(color = INK),
    axis.text         = element_text(color = INK_SOFT),
    axis.line         = element_line(color = INK_SOFT),
    plot.title        = element_text(color = INK),
    plot.subtitle     = element_text(color = INK_SOFT),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT),
    legend.text       = element_text(color = INK_SOFT),
    legend.title      = element_text(color = INK)
  )

# `panel.grid.*` `linewidth` is the line width in mm. ggplot2 does not expose
# `alpha` for grid lines, so use a faint INK color and rely on the natural
# contrast against PAGE_BG instead.

p <- ggplot(df, aes(x, y)) +
  geom_point(color = OKABE_ITO[1], size = 4) +
  anyplot_theme
```

## Geoms (most common)

```r
geom_point()        # scatter
geom_line()         # line
geom_col()          # bar from precomputed values   (stat = "identity")
geom_bar()          # bar from counts               (stat = "count")
geom_boxplot()      # boxplot
geom_violin()       # violin
geom_histogram()    # histogram
geom_density()      # density
geom_tile()         # heatmap / raster
geom_smooth()       # regression / loess overlay
geom_errorbar()     # error bars
facet_wrap(~group)  # small multiples
facet_grid(rows ~ cols)
```

## Script Skeleton

A complete ggplot2 implementation reads `ANYPLOT_THEME`, generates data, builds
the plot, and saves both themed PNGs by being invoked twice with different env
values. The same single `.R` file handles both themes — no two-file split.

```r
library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
OKABE_ITO   <- c("#009E73", "#D55E00", "#0072B2", "#CC79A7",
                 "#E69F00", "#56B4E9", "#F0E442")

# --- Data -------------------------------------------------------------------
df <- tibble::tibble(
  x = rnorm(100),
  y = rnorm(100)
)

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x, y)) +
  geom_point(color = OKABE_ITO[1], size = 4, alpha = 0.7) +
  labs(title = "scatter-basic · r · ggplot2 · anyplot.ai", x = "X", y = "Y") +
  theme_minimal(base_size = 14) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor = element_line(color = INK, linewidth = 0.2),
    axis.title       = element_text(color = INK,      size = 20),
    axis.text        = element_text(color = INK_SOFT, size = 16),
    plot.title       = element_text(color = INK,      size = 24)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 16,
  height   = 9,
  units    = "in",
  dpi      = 300
)
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/r/ggplot2.R` — executed
  twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` (ggplot2 is PNG-only
  in this catalog; no HTML variant).

## R-Specific Gotchas

- Use `linewidth =` for `geom_line()` and `element_line()` in modern ggplot2
  (≥ 3.4). `size =` triggers a deprecation warning.
- `theme()` chains compose right-to-left: a later `theme()` overrides an
  earlier one. Start with `theme_minimal(base_size = ...)`, then layer
  `anyplot_theme`.
- `ggsave()` resets the active graphics device. Use `device = ragg::agg_png`
  explicitly — the platform default Cairo path is not installed in the CI
  image.
- Use `tibble::tibble(...)` (or plain `data.frame(...)`) — `dplyr::tibble` was
  removed in dplyr ≥ 1.0; `tibble::tibble` is the correct path.
- Avoid `print(p)` at script end — `ggsave()` already renders the plot, and an
  extra `print()` opens an unused interactive device.
