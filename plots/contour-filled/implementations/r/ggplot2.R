#' anyplot.ai
#' contour-filled: Filled Contour Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 85/100 | Created: 2026-09-04

library(ggplot2)
library(dplyr)
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

# --- Storytelling: call out the primary peak and valley -------------------
peak_row   <- surface[which.max(surface$z), ]
valley_row <- surface[which.min(surface$z), ]
# Offset labels toward the plot center so they stay inside the fixed domain
# regardless of how close the extremum sits to the -3..3 edge.
peak_label_y   <- peak_row$y - sign(peak_row$y) * 0.45
valley_label_y <- valley_row$y - sign(valley_row$y) * 0.45

# --- Plot ----------------------------------------------------------------
p <- ggplot(surface, aes(x, y, z = z)) +
  geom_contour_filled(breaks = level_breaks) +
  geom_contour(breaks = level_breaks, color = INK_SOFT, linewidth = 0.25, alpha = 0.5) +
  geom_point(
    data = dplyr::bind_rows(peak_row, valley_row), aes(x, y),
    inherit.aes = FALSE, shape = 21, size = 2.2, stroke = 0.6,
    color = INK, fill = PAGE_BG
  ) +
  annotate("text", x = peak_row$x, y = peak_label_y, label = "Peak",
           color = INK, size = 2.8, fontface = "bold") +
  annotate("text", x = valley_row$x, y = valley_label_y, label = "Valley",
           color = INK, size = 2.8, fontface = "bold") +
  scale_fill_manual(
    values = band_colors,
    guide = guide_legend(reverse = TRUE, title = "Elevation (m)")
  ) +
  coord_fixed(ratio = 1) +
  labs(
    title = "contour-filled · r · ggplot2 · anyplot.ai",
    x = "X Coordinate (km)",
    y = "Y Coordinate (km)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background     = element_rect(fill = PAGE_BG, color = NA),
    panel.grid           = element_blank(),
    panel.border         = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.25),
    axis.title           = element_text(color = INK, size = 10),
    axis.text            = element_text(color = INK_SOFT, size = 8),
    axis.ticks           = element_blank(),
    plot.title           = element_text(color = INK, size = 12),
    legend.background    = element_rect(fill = PAGE_BG, color = NA),
    legend.text          = element_text(color = INK_SOFT, size = 8),
    legend.title         = element_text(color = INK, size = 10),
    legend.key           = element_rect(fill = PAGE_BG, color = NA),
    legend.key.size      = unit(0.35, "cm"),
    legend.key.spacing.y = unit(1, "pt")
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
