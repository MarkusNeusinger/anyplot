#' anyplot.ai
#' contour-filled: Filled Contour Plot
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-09-04

library(ggplot2)
library(dplyr)
library(tidyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
DIV_MID     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"

# --- Data --------------------------------------------------------------------
# Classic "peaks" surface: two Gaussian peaks and a saddle-shaped valley,
# a smooth 2D scalar field with a natural zero midpoint (peak vs. valley).
peaks <- function(x, y) {
  3 * (1 - x)^2 * exp(-(x^2) - (y + 1)^2) -
    10 * (x / 5 - x^3 - y^5) * exp(-x^2 - y^2) -
    1 / 3 * exp(-(x + 1)^2 - y^2)
}

grid_axis <- seq(-3, 3, length.out = 80)
surface <- expand.grid(x = grid_axis, y = grid_axis) %>%
  mutate(z = peaks(x, y))

# --- Colors --------------------------------------------------------------
# imprint_div (diverging): matte-red -> theme-adaptive midpoint -> blue,
# used because the surface has a meaningful zero midpoint (valley vs. peak).
n_levels <- 12
level_breaks <- pretty(range(surface$z), n = n_levels)
band_colors <- colorRampPalette(c("#AE3030", DIV_MID, "#4467A3"))(length(level_breaks) - 1)

# --- Plot ----------------------------------------------------------------
p <- ggplot(surface, aes(x, y, z = z)) +
  geom_contour_filled(breaks = level_breaks) +
  geom_contour(breaks = level_breaks, color = INK_SOFT, linewidth = 0.25, alpha = 0.5) +
  scale_fill_manual(
    values = band_colors,
    guide = guide_legend(reverse = TRUE, title = "Elevation")
  ) +
  coord_fixed(ratio = 1) +
  labs(
    title = "contour-filled · r · ggplot2 · anyplot.ai",
    x = "X Coordinate",
    y = "Y Coordinate"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    panel.border      = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.4),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    legend.key        = element_rect(fill = PAGE_BG, color = NA)
  )

# --- Save --------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
