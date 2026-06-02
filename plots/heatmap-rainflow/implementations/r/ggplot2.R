#' anyplot.ai
#' heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-06-02

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
    raw        = 3000 * exp(-amp_mpa / 30) * exp(-0.5 * ((mean_mpa - 60) / 50)^2),
    count      = as.integer(pmax(0, round(raw + abs(rnorm(n(), 0, raw * 0.1 + 10))))),
    count_plot = if_else(count <= 2L, NA_real_, as.double(count))
  ) %>%
  select(-raw)

# Plot
title_str <- "heatmap-rainflow · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = mean_mpa, y = amp_mpa, fill = count_plot)) +
  geom_tile() +
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
    panel.border      = element_rect(color = INK_SOFT,   fill = NA, linewidth = 0.5),
    axis.title        = element_text(color = INK,        size = 10),
    axis.text         = element_text(color = INK_SOFT,   size = 8),
    plot.title        = element_text(color = INK,        size = 12, hjust = 0.5),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
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
