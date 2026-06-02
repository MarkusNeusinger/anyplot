#' anyplot.ai
#' heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-06-02

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens (Imprint palette, theme-adaptive chrome)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Data: synthetic rainflow counting results for a structural steel component
# Amplitude = half stress range (MPa), Mean = mean stress (MPa)
n_bins       <- 20
amp_centers  <- seq(5, 100, length.out = n_bins)
mean_centers <- seq(-40, 140, length.out = n_bins)

df <- expand.grid(amp_mpa = amp_centers, mean_mpa = mean_centers) %>%
  mutate(
    # Steeper amplitude decay + tighter Gaussian → concentrated hot-spot with
    # large zero-count regions at high amplitude and extreme mean values
    raw        = 3000 * exp(-amp_mpa / 15) * exp(-0.5 * ((mean_mpa - 60) / 25)^2),
    count      = as.integer(pmax(0, round(raw + abs(rnorm(n(), 0, raw * 0.1 + 5))))),
    count_plot = if_else(count <= 2L, NA_real_, as.double(count))
  ) %>%
  select(-raw)

# Contour threshold at 25% of peak to outline the dominant fatigue cycle zone
contour_at <- max(df$count, na.rm = TRUE) * 0.25

# Plot
title_str <- "heatmap-rainflow · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = mean_mpa, y = amp_mpa, fill = count_plot)) +
  geom_tile() +
  geom_contour(aes(z = count), color = INK_SOFT, linewidth = 0.4,
               breaks = contour_at, alpha = 0.7) +
  scale_fill_gradient(
    low            = "#009E73",
    high           = "#4467A3",
    na.value       = PAGE_BG,
    name           = "Cycle Count",
    trans          = "sqrt",
    labels         = scales::comma,
    guide          = guide_colorbar(
      barheight      = unit(10, "lines"),
      title.position = "top"
    )
  ) +
  scale_x_continuous(breaks = scales::pretty_breaks(n = 6)) +
  scale_y_continuous(breaks = scales::pretty_breaks(n = 6)) +
  labs(
    title = title_str,
    x     = "Mean Stress (MPa)",
    y     = "Stress Amplitude (MPa)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG,     color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG,     color = NA),
    panel.grid        = element_blank(),
    panel.border      = element_blank(),
    axis.line         = element_line(color = INK_SOFT,   linewidth = 0.5),
    axis.title        = element_text(color = INK,        size = 10),
    axis.text         = element_text(color = INK_SOFT,   size = 8),
    plot.title        = element_text(color = INK,        size = 12, hjust = 0.5),
    legend.background = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT,   size = 8),
    legend.title      = element_text(color = INK,        size = 10),
    plot.margin       = margin(20, 20, 20, 20)
  )

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
