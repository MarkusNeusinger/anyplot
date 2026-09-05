#' anyplot.ai
#' polar-scatter: Polar Scatter Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

IMPRINT_PALETTE <- c(
  "#009E73", # 1 — brand green
  "#C475FD", # 2 — lavender
  "#4467A3", # 3 — blue
  "#BD8233"  # 4 — ochre
)

# --- Data: wind speed and direction observations by time of day -------------
periods    <- c("Morning", "Afternoon", "Evening", "Night")
n_per      <- c(40, 35, 35, 20)
dir_mean   <- c(50, 210, 170, 300)  # prevailing bearing per period, degrees
dir_sd     <- c(20, 25, 30, 35)
speed_mean <- c(9, 15, 11, 6)       # m/s
speed_sd   <- c(2, 3, 2.5, 1.5)

n_total <- sum(n_per)
period      <- factor(rep(periods, times = n_per), levels = periods)
theta       <- (rnorm(n_total, rep(dir_mean, times = n_per), rep(dir_sd, times = n_per))) %% 360
wind_speed  <- pmax(rnorm(n_total, rep(speed_mean, times = n_per), rep(speed_sd, times = n_per)), 0.5)

wind_obs <- tibble::tibble(theta = theta, wind_speed = wind_speed, period = period)

radius_max <- max(wind_obs$wind_speed) * 1.15

# --- Theme --------------------------------------------------------------------
grid_major <- scales::alpha(INK, 0.15)
grid_minor <- scales::alpha(INK, 0.08)

anyplot_theme <- theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = grid_major, linewidth = 0.3),
    panel.grid.minor  = element_line(color = grid_minor, linewidth = 0.15),
    axis.ticks        = element_blank(),
    axis.title.x      = element_blank(),
    axis.title.y      = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = 12, face = "bold"),
    legend.background = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10)
  )

# --- Plot ---------------------------------------------------------------------
p <- ggplot(wind_obs, aes(x = theta, y = wind_speed, fill = period)) +
  geom_point(shape = 21, size = 3.5, stroke = 0.4, color = PAGE_BG, alpha = 0.85) +
  scale_x_continuous(
    limits = c(0, 360),
    breaks = c(0, 90, 180, 270),
    labels = c("0° N", "90° E", "180° S", "270° W"),
    expand = c(0, 0)
  ) +
  scale_y_continuous(
    limits = c(0, radius_max),
    expand = expansion(mult = c(0, 0.05))
  ) +
  scale_fill_manual(values = IMPRINT_PALETTE, name = "Time of Day") +
  coord_polar(theta = "x", start = 0, direction = 1) +
  labs(
    title = "Wind Observations · polar-scatter · r · ggplot2 · anyplot.ai",
    y = "Wind Speed (m/s)"
  ) +
  anyplot_theme

# --- Save -----------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
