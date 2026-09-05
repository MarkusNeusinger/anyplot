#' anyplot.ai
#' polar-bar: Polar Bar Chart (Wind Rose)
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 75/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(tidyr)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint categorical palette — first series is always brand green
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030")

# Data — synthetic meteorological wind rose: 16 compass directions, 5 speed bins
directions <- c(
  "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
)
speed_bins <- c("0-5 kt", "5-10 kt", "10-15 kt", "15-20 kt", "20+ kt")

# Prevailing westerlies: weight toward SW/W, light toward N/NE
direction_weights <- c(2, 3, 4, 5, 6, 5, 7, 9, 8, 10, 14, 12, 10, 7, 5, 3)
wind_direction <- sample(directions,
  size = 3000, replace = TRUE,
  prob = direction_weights / sum(direction_weights)
)
wind_speed <- sample(speed_bins,
  size = 3000, replace = TRUE,
  prob = c(0.35, 0.30, 0.20, 0.10, 0.05)
)

wind_counts <- tibble(
  direction = factor(wind_direction, levels = directions),
  speed     = factor(wind_speed, levels = speed_bins)
) %>%
  count(direction, speed, name = "n")

wind_df <- expand_grid(
  direction = factor(directions, levels = directions),
  speed     = factor(speed_bins, levels = speed_bins)
) %>%
  left_join(wind_counts, by = c("direction", "speed")) %>%
  mutate(
    n = replace_na(n, 0),
    frequency = n / sum(n) * 100
  )

# Plot — bars radiate from center, angle = direction, stacked by speed bin
p <- ggplot(wind_df, aes(x = direction, y = frequency, fill = speed)) +
  geom_col(width = 1, color = PAGE_BG, linewidth = 0.3) +
  coord_polar(theta = "x", start = -pi / 16, clip = "off") +
  scale_fill_manual(values = IMPRINT_PALETTE, name = "Wind speed") +
  scale_y_continuous(labels = label_percent(scale = 1), expand = expansion(mult = c(0, 0.05))) +
  labs(title = "polar-bar · r · ggplot2 · anyplot.ai", x = NULL, y = NULL) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_blank(),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.line         = element_blank(),
    axis.ticks        = element_blank(),
    axis.text.x       = element_text(color = INK_SOFT, size = 9, margin = margin(t = 8, r = 8, b = 8, l = 8)),
    axis.text.y       = element_text(color = INK_SOFT, size = 7),
    plot.title        = element_text(color = INK, size = 12, hjust = 0.5),
    plot.margin       = margin(t = 15, r = 15, b = 15, l = 15),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    legend.position   = "bottom"
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
