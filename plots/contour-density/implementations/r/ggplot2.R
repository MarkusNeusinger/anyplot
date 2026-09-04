#' anyplot.ai
#' contour-density: Density Contour Plot
#' Library: ggplot2 | R 4.4
#' Quality: pending | Created: 2026-09-04

library(ggplot2)
library(ragg)
library(scales)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# --- Data -----------------------------------------------------------------
# Old Faithful geyser: eruption duration vs. waiting time until the next
# eruption. The bivariate distribution is famously bimodal, which makes it a
# clean showcase for density contours (short/frequent vs. long/rare bursts).
df <- data.frame(
  eruption_duration = faithful$eruptions,
  waiting_time      = faithful$waiting
)

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = eruption_duration, y = waiting_time)) +
  stat_density_2d(
    aes(fill = after_stat(level)),
    geom      = "polygon",
    color     = NA,
    contour_var = "density",
    bins      = 9
  ) +
  geom_point(color = INK, size = 1.1, alpha = 0.25) +
  scale_fill_gradient(low = "#009E73", high = "#4467A3", name = "Density") +
  scale_x_continuous(expand = expansion(mult = 0.04)) +
  scale_y_continuous(expand = expansion(mult = 0.04)) +
  labs(
    title = "Old Faithful Eruptions · contour-density · r · ggplot2 · anyplot.ai",
    x     = "Eruption Duration (min)",
    y     = "Waiting Time to Next Eruption (min)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = scales::alpha(INK, 0.15), linewidth = 0.4),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12, face = "bold"),
    legend.title      = element_text(color = INK, size = 10),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.background = element_blank(),
    legend.key        = element_blank()
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
