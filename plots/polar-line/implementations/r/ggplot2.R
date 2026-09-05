#' anyplot.ai
#' polar-line: Polar Line Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 82/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome") ----
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data: mean wind speed by compass bearing for three monitoring stations ----
bearings <- seq(0, 350, by = 10)
stations <- c("Station A", "Station B", "Station C")
prevailing_bearing <- c(0, 120, 240)
mean_speed <- c(18, 14, 21)
gust_amplitude <- c(8, 6, 9)

wind <- tibble::tibble(
  station = rep(stations, each = length(bearings)),
  bearing = rep(bearings, times = length(stations)),
  prevailing = rep(prevailing_bearing, each = length(bearings)),
  base = rep(mean_speed, each = length(bearings)),
  amplitude = rep(gust_amplitude, each = length(bearings))
) %>%
  mutate(
    wind_speed = pmax(base + amplitude * cos((bearing - prevailing) * pi / 180) +
      rnorm(n(), 0, 1.2), 2)
  )

# Duplicate the bearing-0 point at 360 so each station's line closes into a loop
wind_closed <- wind %>%
  filter(bearing == 0) %>%
  mutate(bearing = 360) %>%
  bind_rows(wind, .) %>%
  arrange(station, bearing)

# --- Chrome ------------------------------------------------------------------
anyplot_theme <- theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor  = element_blank(),
    axis.line         = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = 12),
    legend.position   = "bottom",
    legend.background = element_blank(),
    legend.key        = element_rect(fill = PAGE_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10)
  )

# --- Plot ----------------------------------------------------------------------
p <- ggplot(wind_closed, aes(x = bearing, y = wind_speed, color = station)) +
  geom_path(linewidth = 1.1) +
  geom_point(data = filter(wind_closed, bearing != 360), size = 1.8) +
  scale_color_manual(values = IMPRINT_PALETTE[1:3]) +
  scale_x_continuous(
    breaks = seq(0, 315, by = 45),
    labels = c("N", "NE", "E", "SE", "S", "SW", "W", "NW"),
    limits = c(0, 360)
  ) +
  scale_y_continuous(limits = c(0, NA), expand = expansion(mult = c(0, 0.08))) +
  coord_polar(theta = "x", start = 0, direction = 1) +
  labs(
    title = "polar-line · r · ggplot2 · anyplot.ai",
    x = NULL,
    y = "Wind speed (km/h)",
    color = "Station"
  ) +
  anyplot_theme

# --- Save ------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
