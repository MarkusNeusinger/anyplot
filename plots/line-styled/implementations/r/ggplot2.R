#' anyplot.ai
#' line-styled: Styled Line Plot
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(tidyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data --------------------------------------------------------------------
# Quarterly revenue trend for four product lines, indexed to a common base
# year so line-style distinction (not color) carries the reading for anyone
# printing this chart in black and white.
quarters <- 1:24
df <- tibble::tibble(
  quarter    = rep(quarters, times = 4),
  revenue    = c(
    100 + cumsum(rnorm(24, mean = 2.6, sd = 3.0)),
    100 + cumsum(rnorm(24, mean = 1.1, sd = 2.4)),
    100 + cumsum(rnorm(24, mean = 0.4, sd = 3.4)),
    100 + cumsum(rnorm(24, mean = -0.8, sd = 2.0))
  ),
  product = factor(
    rep(c("Hardware", "Software", "Services", "Accessories"), each = 24),
    levels = c("Hardware", "Software", "Services", "Accessories")
  )
)

line_styles <- c(
  "Hardware"    = "solid",
  "Software"    = "dashed",
  "Services"    = "dotted",
  "Accessories" = "dotdash"
)

title_str <- "line-styled · r · ggplot2 · anyplot.ai"

# --- Plot ---------------------------------------------------------------------
p <- ggplot(df, aes(x = quarter, y = revenue, color = product, linetype = product)) +
  geom_line(linewidth = 1.1) +
  scale_color_manual(values = IMPRINT_PALETTE[1:4]) +
  scale_linetype_manual(values = line_styles) +
  labs(
    title    = title_str,
    x        = "Quarter",
    y        = "Revenue Index (base = 100)",
    color    = "Product Line",
    linetype = "Product Line"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor   = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.line          = element_line(color = INK_SOFT),
    axis.ticks         = element_blank(),
    plot.title         = element_text(color = INK, size = 12),
    legend.background  = element_rect(fill = ELEVATED_BG, color = NA),
    legend.key         = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_text(color = INK, size = 10),
    legend.position    = "right"
  )

# --- Save ----------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
