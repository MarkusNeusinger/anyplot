#' anyplot.ai
#' heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# --- Data -----------------------------------------------------------------
# Hourly website visits, angular = hour of day (wraps continuously),
# radial = day of week (Monday innermost ring, Sunday outermost).
days  <- c("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
hours <- 0:23

traffic <- expand.grid(day = days, hour = hours, stringsAsFactors = FALSE) %>%
  mutate(
    day_idx    = match(day, days),
    is_weekend = day %in% c("Sat", "Sun"),
    baseline   = ifelse(
      is_weekend,
      20 + 70 * exp(-(hour - 14)^2 / 30),
      40 + 90 * exp(-(hour - 8)^2 / 6) + 100 * exp(-(hour - 18)^2 / 8)
    ),
    visits     = pmax(0, baseline + rnorm(n(), mean = 0, sd = 8))
  )

# --- Plot -------------------------------------------------------------------
# Tiles are offset by +0.5h so cell edges land on whole hours (0-1, 1-2, ...);
# the y-axis leaves a hole below day_idx=1 so rings read outward from a
# center gap instead of overlapping at a point.
p <- ggplot(traffic, aes(x = hour + 0.5, y = day_idx, fill = visits)) +
  geom_tile(width = 1, height = 1, color = PAGE_BG, linewidth = 0.2) +
  coord_polar(theta = "x") +
  scale_x_continuous(
    limits = c(0, 24), expand = c(0, 0),
    breaks = c(0, 6, 12, 18), labels = c("12am", "6am", "12pm", "6pm")
  ) +
  scale_y_continuous(
    limits = c(-1.5, 7.5), expand = c(0, 0),
    breaks = 1:7, labels = days
  ) +
  scale_fill_gradient(low = "#009E73", high = "#4467A3", name = "Visits/hr") +
  labs(
    title    = "Hourly Website Traffic · heatmap-polar · r · ggplot2 · anyplot.ai",
    subtitle = "Hour of day (angular) · Day of week (radial)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK_SOFT, linewidth = 0.15),
    panel.grid.minor  = element_blank(),
    axis.title        = element_blank(),
    axis.ticks        = element_blank(),
    axis.text.x       = element_text(color = INK_SOFT, size = 8),
    axis.text.y       = element_text(color = INK, size = 8, face = "bold"),
    plot.title        = element_text(color = INK, size = 12, hjust = 0.5),
    plot.subtitle     = element_text(color = INK_SOFT, size = 8, hjust = 0.5),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    legend.background = element_rect(fill = PAGE_BG, color = NA)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
