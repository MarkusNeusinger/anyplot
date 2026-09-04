#' anyplot.ai
#' contour-density: Density Contour Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-09-04

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

# stat_density_2d evaluates its KDE grid exactly over the trained scale
# range, so a data point sitting right at the min/max of that range leaves
# no room for its contour to close and the outermost isoband gets cut into
# a wedge. Padding the scale limits beyond the data range gives the KDE
# grid slack on all sides so every contour closes cleanly.
x_rng  <- range(df$eruption_duration)
y_rng  <- range(df$waiting_time)
x_pad  <- diff(x_rng) * 0.08
y_pad  <- diff(y_rng) * 0.08

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = eruption_duration, y = waiting_time)) +
  stat_density_2d(
    aes(fill = after_stat(level)),
    geom        = "polygon",
    color       = NA,
    contour_var = "density",
    n           = 200,
    bins        = 8
  ) +
  geom_point(color = INK, size = 1.3, alpha = 0.35) +
  scale_fill_gradient(low = "#009E73", high = "#4467A3", name = "Density") +
  scale_x_continuous(limits = c(x_rng[1] - x_pad, x_rng[2] + x_pad), expand = expansion(mult = 0.02)) +
  scale_y_continuous(limits = c(y_rng[1] - y_pad, y_rng[2] + y_pad), expand = expansion(mult = 0.02)) +
  labs(
    title    = "Old Faithful Eruptions · contour-density · r · ggplot2 · anyplot.ai",
    subtitle = "Two distinct eruption modes: short/frequent and long/rare bursts",
    x        = "Eruption Duration (min)",
    y        = "Waiting Time to Next Eruption (min)"
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
    plot.subtitle     = element_text(color = INK_SOFT, size = 9),
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
