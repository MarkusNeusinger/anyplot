# ggplot2

ggplot2 is the canonical implementation of the grammar of graphics in R. This
is anyplot's first R-language entry; the file extension is **`.R`** and the
runtime is **Rscript**, not Python.

**API level:** ggplot2 4. The Posit snapshot in `.github/actions/setup-r/action.yml`
pins this major; write against its API, with the changes in "ggplot2 4.0 notes"
below, not 3.x habits.

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
library(patchwork)   # composing multiple ggplot objects (mosaic/grid layouts)
```

Optional dataset packages available in the CI runtime: `palmerpenguins`,
`gapminder`. Plus everything bundled with base R / ggplot2: `mtcars`, `iris`,
`diamonds`, `economics`, `mpg`, `faithful`.

## Reproducibility

```r
set.seed(42)  # first line of the # Data block
```

## Data block

The file follows the six zones of `prompts/adaptable-code.md` in R syntax: the column constants above the block, one `# Data` block that builds a `tibble` keyed by them and ends in `df`, and plot code below `# Plot` that reads columns through `.data[[...]]`:

```r
# Columns: set these to your table's column names
QUARTER      <- "Quarter"               # role: category
PRODUCT_LINE <- "Product line"          # role: group
SALES        <- "Sales (thousand USD)"  # role: value

# Data: replace this block with your own table, for example df <- read.csv("sales.csv", check.names = FALSE)
df <- tibble::tibble(
  !!QUARTER      := rep(c("Q1", "Q2", "Q3", "Q4"), times = 3),
  !!PRODUCT_LINE := rep(c("Electronics", "Clothing", "Home & Garden"), each = 4),
  !!SALES        := c(245, 312, 287, 425, 178, 195, 285, 310, 125, 210, 195, 165)
)

# Plot: reads only df and the constants above
df <- df |> mutate(across(all_of(c(QUARTER, PRODUCT_LINE)), \(v) factor(v, levels = unique(v))))
p <- ggplot(df, aes(x = .data[[QUARTER]], y = .data[[SALES]], fill = .data[[PRODUCT_LINE]])) +
  geom_col(position = position_dodge(width = 0.8), width = 0.75) +
  scale_fill_manual(values = IMPRINT_PALETTE) +
  labs(x = QUARTER, y = SALES, fill = PRODUCT_LINE, title = "bar-grouped · r · ggplot2 · anyplot.ai")
```

- `!!QUARTER :=` names a tibble column by the constant's value, so the column name is typed once.
- `.data[[QUARTER]]` reads a column whose name has spaces or a unit, which a bare name in `aes()` cannot.
- Set every axis and legend title with `labs()` from the constants: `aes()` with `.data[[...]]` does not reliably title the axes with the column name.
- A character column sorts alphabetically, on the axis and in the color mapping. The `factor(v, levels = unique(v))` line keeps the data's order, so the first group in the data gets `#009E73`.
- `scale_fill_manual()` gets all eight hues and uses the first n. Limits come from the data (`ylim(0, max(df[[SALES]], na.rm = TRUE) * 1.15)`) or stay automatic, never typed numbers.

## Create Plot

```r
p <- ggplot(df, aes(x = .data[[STUDY_HOURS]], y = .data[[EXAM_SCORE]])) +
  geom_point() +
  labs(x = STUDY_HOURS, y = EXAM_SCORE, title = plot_title) +
  theme_minimal(base_size = 8)
```

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (post-render gate in `impl-review.yml` rejects anything off by more than 16 px and re-triggers repair):

| Orientation | `ggsave` `width × height` (`units="in"`, `dpi=400`) | Final PNG     |
|-------------|------------------------------------------------------|---------------|
| Landscape   | `width = 8, height = 4.5`                            | 3200 × 1800   |
| Square      | `width = 6, height = 6`                              | 2400 × 2400   |

Pick the orientation that suits the spec. `ragg::agg_png` honours these values without trimming, so no extra tricks are required — just don't deviate.

## Figure Size & Sizing for 3200×1800 px (starting values — review-loop tunes)

ggplot2 inherits sizes via `theme(... base_size = ...)`. Override individual
elements for the anyplot canvas:

```r
p <- p +
  theme(
    text             = element_text(size = 7),   # base text
    axis.title       = element_text(size = 10),  # axis labels
    axis.text        = element_text(size = 8),   # tick labels
    plot.title       = element_text(size = 12),  # kept compact for the long mandated title
    legend.text      = element_text(size = 8),
    legend.title     = element_text(size = 10)
  )

# Element sizes inside geoms (~2-3× ggplot2 defaults, density-aware):
# geom_point(size = 2.5)
# geom_line(linewidth = 1.0)
```

> `geom_text(size = N)` is in mm (× 2.845 ≈ pt), unlike `element_text(size = N)` which is pt. Annotation `size` should be ~2.5–4, never the same numeric scale as the theme.

See `prompts/default-style-guide.md` "Proportional Sizing" for review criteria.

## Save (PNG, both themes)

Use the `ragg` device — it antialiases properly and ignores `Cairo` system
deps:

```r
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
```

## Colors

Use the Imprint palette (see `prompts/default-style-guide.md` "Categorical
Palette"). First series is **always** `#009E73`.

```r
IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — first categorical series (brand green)
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue
  "#BD8233",  # 4 — ochre
  "#AE3030",  # 5 — matte red (semantic anchor for bad / loss / error)
  "#2ABCCD",  # 6 — cyan
  "#954477",  # 7 — rose
  "#99B314"   # 8 — lime
)
ANYPLOT_AMBER <- "#DDCC77"  # warning / caution (outside the categorical pool)

# Single-series
geom_point(color = IMPRINT_PALETTE[1])

# Multi-series — categorical
scale_color_manual(values = IMPRINT_PALETTE)
scale_fill_manual(values  = IMPRINT_PALETTE)

# Continuous — only the two Imprint palette-derived cmaps are allowed:
# Sequential (single-polarity)
scale_color_gradient(low = "#009E73", high = "#4467A3")
scale_fill_gradient(low  = "#009E73", high = "#4467A3")
# Diverging (around a meaningful midpoint, often 0)
scale_color_gradient2(low = "#AE3030", mid = "#FAF8F1", high = "#4467A3", midpoint = 0)
scale_fill_gradient2(low  = "#AE3030", mid = "#FAF8F1", high = "#4467A3", midpoint = 0)
```

Never use `viridis::scale_*_viridis_*()`, `scale_*_distiller()`/`scale_*_brewer()`,
`rainbow()`, `heat.colors()`, `terrain.colors()`, `topo.colors()` or `hsv()` —
only the two anyplot stops above.

## Theme-adaptive Chrome (ggplot2 mapping)

Read `ANYPLOT_THEME` from the environment and flip chrome tokens. Data colors
stay identical between themes — only the surrounding chrome changes.

```r
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

anyplot_theme <- theme_minimal(base_size = 8) +
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

p <- ggplot(df, aes(x = .data[[STUDY_HOURS]], y = .data[[EXAM_SCORE]])) +
  geom_point(color = IMPRINT_PALETTE[1], size = 2.5) +
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
values. The same single `.R` file handles both themes — no two-file split. It
follows the zones of "Data block" above.

```r
library(ggplot2)
library(dplyr)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
STUDY_HOURS <- "Study hours per day"  # role: x
EXAM_SCORE  <- "Exam score (%)"       # role: y

# Data: replace this block with your own table, for example df <- read.csv("scores.csv", check.names = FALSE)
set.seed(42)
hours <- rnorm(100, mean = 6, sd = 2)
df <- tibble::tibble(
  !!STUDY_HOURS := hours,
  !!EXAM_SCORE  := hours * 8 + rnorm(100, sd = 5) + 30
)

# Plot: reads only df and the constants above
p <- ggplot(df, aes(x = .data[[STUDY_HOURS]], y = .data[[EXAM_SCORE]])) +
  geom_point(color = IMPRINT_PALETTE[1], size = 2.5, alpha = 0.7) +
  labs(title = "scatter-basic · r · ggplot2 · anyplot.ai", x = STUDY_HOURS, y = EXAM_SCORE) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor = element_line(color = INK, linewidth = 0.2),
    axis.title       = element_text(color = INK,      size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    plot.title       = element_text(color = INK,      size = 12)
  )

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/r/ggplot2.R` — executed
  twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` (ggplot2 is PNG-only
  in this catalog; no HTML variant).

## R-Specific Gotchas

- Use `linewidth =` for `geom_line()` and `element_line()` in modern ggplot2
  (≥ 3.4). `size =` triggers a deprecation warning, and on `geom_bar()` /
  `geom_col()` outlines ggplot2 4.0 ignores it entirely.
- `theme()` chains compose right-to-left: a later `theme()` overrides an
  earlier one. Start with `theme_minimal(base_size = ...)`, then layer
  `anyplot_theme`.
- `ggsave()` resets the active graphics device. Use `device = ragg::agg_png`
  explicitly — the platform default Cairo path is not installed in the CI
  image.
- Use `tibble::tibble(...)` — `dplyr::tibble` was removed in dplyr ≥ 1.0;
  `tibble::tibble` is the correct path. It also takes the `!!QUARTER :=`
  column names of the Data block, which plain `data.frame(...)` does not.
- Avoid `print(p)` at script end — `ggsave()` already renders the plot, and an
  extra `print()` opens an unused interactive device.

## ggplot2 4.0 notes

Each item below changed between ggplot2 3.5 and 4.0: the old form still runs,
but renders differently or prints a deprecation warning.

- **Label borders:** set the border width with `linewidth` (`0` for no border)
  and its colour with `border.colour`. `label.size` is deprecated, and
  `annotate("label", ..., label.size = 0)` is ignored outright ("Ignoring
  unknown parameters"), so the label gets the default 0.25 mm border.
- **Horizontal error bars:** `geom_errorbar(aes(y = term, xmin = lo, xmax = hi),
  orientation = "y", width = 0.2)`. `geom_errorbarh()` is deprecated.
- **Box, crossbar, pointrange:** `fatten` is deprecated. Style the parts
  directly: `geom_boxplot(median.linewidth = , box.linewidth = ,
  whisker.linewidth = )`, `geom_crossbar(middle.linewidth = )`, and the point
  `size` in `geom_pointrange()`.
- **Violin quantiles:** `geom_violin(quantiles = c(0.25, 0.5, 0.75),
  quantile.linetype = 1)`. `draw_quantiles` is deprecated, and quantiles are now
  computed from the data rather than from the density.
- **Histograms and other binning stats:** pass `boundary` (or explicit `breaks`)
  together with `binwidth` or `bins`, for example `binwidth = 5, boundary = 0`.
  ggplot2 4.0 moved the default bin edges, so unanchored bins shift between
  versions and rarely land on round values.
- **`theme_void()` borders:** its root `rect` now has `linewidth = 0`, so a border
  such as `legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT)`
  disappears. Give every bordered `element_rect()` an explicit `linewidth`.
- **Rotated axis text:** set both `hjust` and `vjust`. On a top axis
  (`scale_x_discrete(position = "top")`) use `vjust = 0`; without it ggplot2 4.0
  pushes the labels up into the title.
- **Several legends:** fix their order with `guides(colour = guide_legend(order
  = 1), size = guide_legend(order = 2))`. The default order changed in 4.0 and is
  not stable across versions.
- **Subtitle, caption and tag** inherit from `text`, no longer from `title`:
  style `plot.subtitle`, `plot.caption` and `plot.tag` explicitly instead of
  through `title`.
- **Renamed:** `coord_transform()` replaces `coord_trans()`, and
  `annotation_borders()` replaces `borders()`.
- **Facet panel order:** `facet_wrap(as.table = )` is deprecated. Set the order
  with a two-letter `dir` instead: the letters name the starting corner and the
  first one the filling direction, so `dir = "lb"` starts bottom-left and fills
  left to right, as `as.table = FALSE` did.
