#' anyplot.ai
#' contour-basic: Basic Contour Plot
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-06-25

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
DIV_MID     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"

# Data: ocean temperature anomaly on a 60x60 regular grid
resolution <- 60
x_vals <- seq(-3, 3, length.out = resolution)
y_vals <- seq(-3, 3, length.out = resolution)
grid   <- expand.grid(x = x_vals, y = y_vals)

grid$temp <- (
  2.8 * exp(-((grid$x - 1.2)^2 + (grid$y - 0.8)^2) / 1.5) +
  1.6 * exp(-((grid$x + 1.5)^2 + (grid$y - 1.3)^2) / 2.0) -
  2.2 * exp(-((grid$x - 0.3)^2 + (grid$y + 1.9)^2) / 1.2) -
  1.5 * exp(-((grid$x + 1.8)^2 + (grid$y + 0.6)^2) / 1.8)
)

# Title
title_text <- "contour-basic · r · ggplot2 · anyplot.ai"

# Plot
p <- ggplot(grid, aes(x = x, y = y)) +
  geom_tile(aes(fill = temp)) +
  geom_contour(aes(z = temp), color = INK, linewidth = 0.4, alpha = 0.7, bins = 12) +
  scale_fill_gradient2(
    low      = "#AE3030",
    mid      = DIV_MID,
    high     = "#4467A3",
    midpoint = 0,
    name     = "ΔT (°C)"
  ) +
  coord_fixed() +
  labs(
    title = title_text,
    x     = "Longitude",
    y     = "Latitude"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_blank(),
    panel.grid.minor  = element_blank(),
    panel.border      = element_rect(color = INK_SOFT, fill = NA),
    axis.title        = element_text(color = INK,      size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK,      size = 12),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK,      size = 10),
    plot.margin       = margin(20, 20, 20, 20)
  )

# Save (square canvas: 6×6 in @ 400 dpi = 2400×2400 px)
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
