#' anyplot.ai
#' spiral-timeseries: Spiral Time Series Chart
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-09-09

library(ggplot2)
library(dplyr)
library(tibble)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data: daily average temperature, one revolution per year -----------
dates <- seq(as.Date("2021-01-01"), as.Date("2024-12-31"), by = "day")
years <- as.integer(format(dates, "%Y"))
doy   <- as.integer(format(dates, "%j"))

df <- tibble(
  date       = dates,
  year       = years,
  year_index = years - min(years),
  doy_frac   = (doy - 1) / 365.25
) %>%
  mutate(
    temperature = 10 - 15 * cos(2 * pi * doy_frac) +
      0.3 * year_index + rnorm(n(), mean = 0, sd = 1.8)
  )

# --- Archimedean spiral geometry -----------------------------------------
R0       <- 0.6                       # inner radius (spiral start)
GAP      <- 1.0                       # radial distance added per full cycle
N_CYCLES <- max(df$year_index) + 1

df <- df %>%
  mutate(
    radius = R0 + GAP * (year_index + doy_frac),
    angle  = 2 * pi * doy_frac,
    x      = radius * sin(angle),
    y      = radius * cos(angle)
  )

# Concentric rings mark each full-cycle boundary
circle_theta <- seq(0, 2 * pi, length.out = 200)
circles <- do.call(rbind, lapply(0:N_CYCLES, function(i) {
  r <- R0 + GAP * i
  tibble(x = r * sin(circle_theta), y = r * cos(circle_theta), ring = i)
}))

# Radial spokes mark month subdivisions within each cycle
month_angle <- 2 * pi * (0:11) / 12
r_max <- R0 + GAP * N_CYCLES
spokes <- tibble(
  x    = R0 * sin(month_angle),
  y    = R0 * cos(month_angle),
  xend = r_max * sin(month_angle),
  yend = r_max * cos(month_angle)
)

# One label per revolution, at the top of the spiral, for orientation
cycle_labels <- df %>%
  distinct(year, year_index) %>%
  mutate(x = 0, y = R0 + GAP * year_index + 0.25)

# --- Title (length-scaled fontsize; see prompts/plot-generator.md) ------
plot_title <- "spiral-timeseries · r · ggplot2 · anyplot.ai"
title_size <- max(8, round(12 * min(1, 67 / nchar(plot_title))))

# --- Plot -----------------------------------------------------------------
p <- ggplot() +
  geom_path(data = circles, aes(x, y, group = ring),
            color = INK, linewidth = 0.3, alpha = 0.18) +
  geom_segment(data = spokes, aes(x = x, y = y, xend = xend, yend = yend),
               color = INK, linewidth = 0.3, alpha = 0.18) +
  geom_path(data = df, aes(x, y, color = temperature, group = 1),
            linewidth = 1.4, lineend = "round") +
  geom_text(data = cycle_labels, aes(x, y, label = year),
            color = INK_SOFT, size = 3.2) +
  scale_color_gradient(low = IMPRINT_PALETTE[1], high = IMPRINT_PALETTE[3],
                        name = "Avg temp (°C)") +
  coord_fixed(ratio = 1) +
  labs(title = plot_title) +
  theme_void(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    plot.title        = element_text(color = INK, size = title_size,
                                      hjust = 0.5, margin = margin(b = 14)),
    legend.position    = "right",
    legend.background  = element_rect(fill = ELEVATED_BG, color = NA),
    legend.title       = element_text(color = INK, size = 10),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    plot.margin        = margin(10, 10, 10, 10)
  ) +
  guides(color = guide_colorbar(barwidth = unit(0.5, "cm"),
                                 barheight = unit(6, "cm")))

# --- Save (square canvas: symmetric radial layout) -------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
