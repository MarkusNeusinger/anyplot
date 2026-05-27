#' anyplot.ai
#' pie-portfolio-interactive: Interactive Portfolio Allocation Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 84/100 | Created: 2026-05-27

library(ggplot2)
library(dplyr)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

ANYPLOT_PALETTE <- c(
  "#009E73",  # 1 — Equities (brand green)
  "#C475FD",  # 2 — Fixed Income (lavender)
  "#4467A3",  # 3 — Alternatives (blue)
  "#BD8233"   # 4 — Cash (ochre)
)

# Portfolio holdings ordered by asset class
cat_levels <- c("Equities", "Fixed Income", "Alternatives", "Cash")
cat_colors <- setNames(ANYPLOT_PALETTE, cat_levels)

holdings <- data.frame(
  holding  = c(
    "US Large Cap", "Intl Developed", "Emerging Mkts", "US Small Cap",
    "US Treasuries", "Inv Grade Corp", "High Yield",
    "Real Estate", "Commodities",
    "Money Market"
  ),
  category = factor(c(
    rep("Equities", 4),
    rep("Fixed Income", 3),
    rep("Alternatives", 2),
    "Cash"
  ), levels = cat_levels),
  weight   = c(20, 18, 12, 5, 12, 10, 8, 6, 4, 5),
  stringsAsFactors = FALSE
)

# Pre-compute angular midpoints for label placement
holdings <- holdings |>
  arrange(category) |>
  mutate(
    cum_end   = cumsum(weight),
    cum_start = lag(cum_end, default = 0),
    midpoint  = (cum_start + cum_end) / 2
  )

# Asset class summary for the inner ring
categories <- holdings |>
  group_by(category) |>
  summarise(weight = sum(weight), .groups = "drop") |>
  mutate(
    cum_end   = cumsum(weight),
    cum_start = lag(cum_end, default = 0),
    midpoint  = (cum_start + cum_end) / 2
  )

# Title sizing (scale down only if longer than 67-char baseline)
title_str  <- "pie-portfolio-interactive · r · ggplot2 · anyplot.ai"
n_chars    <- nchar(title_str)
ratio      <- if (n_chars > 67) 67 / n_chars else 1.0
title_size <- max(8, round(12 * ratio))

# Double-donut: inner ring = asset classes, outer ring = individual holdings
p <- ggplot() +
  # Outer ring: individual holdings
  geom_col(
    data      = holdings,
    aes(x = 3.2, y = weight, fill = category),
    width     = 1.0,
    color     = PAGE_BG,
    linewidth = 0.5
  ) +
  # Inner ring: asset class summary
  geom_col(
    data      = categories,
    aes(x = 2.0, y = weight, fill = category),
    width     = 0.9,
    color     = PAGE_BG,
    linewidth = 1.0
  ) +
  # Inner ring labels (skip Cash at 5% — too small)
  geom_text(
    data       = filter(categories, weight >= 8),
    aes(x = 2.0, y = midpoint,
        label  = paste0(gsub(" ", "\n", as.character(category)), "\n", weight, "%")),
    color      = PAGE_BG,
    size       = 2.3,
    fontface   = "bold",
    lineheight = 0.82
  ) +
  # Outer ring percentage labels for larger holdings (>= 10%)
  geom_text(
    data     = filter(holdings, weight >= 10),
    aes(x = 3.2, y = midpoint,
        label = paste0(weight, "%")),
    color    = PAGE_BG,
    size     = 2.6,
    fontface = "bold"
  ) +
  coord_polar(theta = "y", start = 0) +
  xlim(c(0.7, 4.2)) +
  scale_fill_manual(
    values = cat_colors,
    name   = "Asset Class"
  ) +
  labs(
    title    = title_str,
    subtitle = "Model Portfolio · 10 Holdings · Inner ring: asset class  |  Outer ring: individual holding"
  ) +
  theme_void(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    plot.title        = element_text(
      color  = INK,
      size   = title_size,
      hjust  = 0.5,
      face   = "bold",
      margin = margin(t = 16, b = 4)
    ),
    plot.subtitle     = element_text(
      color  = INK_MUTED,
      size   = 7,
      hjust  = 0.5,
      margin = margin(b = 8)
    ),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10, face = "bold"),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.key.size   = unit(0.45, "cm"),
    legend.position   = "bottom",
    legend.direction  = "horizontal",
    plot.margin       = margin(10, 20, 20, 20)
  )

# Save — square canvas: 2400 x 2400 px (6 in x 400 dpi)
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
