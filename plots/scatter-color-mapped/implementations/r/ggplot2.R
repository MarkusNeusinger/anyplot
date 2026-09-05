#' anyplot.ai
#' scatter-color-mapped: Color-Mapped Scatter Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 82/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data ---------------------------------------------------------------
# Weather-station network: temperature rises toward the south and falls
# with elevation-like noise, giving the color channel a real spatial signal.
n_stations <- 320
longitude <- runif(n_stations, -9, 9)
latitude <- runif(n_stations, 36, 54)
temperature_c <- 26 - 0.55 * (latitude - 36) + rnorm(n_stations, 0, 2.2)

stations <- tibble::tibble(longitude, latitude, temperature_c)

# --- Plot -----------------------------------------------------------------
title_text <- "Weather Station Temperatures · scatter-color-mapped · r · ggplot2 · anyplot.ai"
title_size <- round(12 * min(1, 67 / nchar(title_text)))

p <- ggplot(stations, aes(x = longitude, y = latitude, color = temperature_c)) +
  geom_point(size = 3, alpha = 0.8) +
  scale_color_gradient(
    name = "Temperature (°C)",
    low = IMPRINT_PALETTE[1],
    high = IMPRINT_PALETTE[3]
  ) +
  labs(
    title = title_text,
    x = "Longitude (°)",
    y = "Latitude (°)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = alpha(INK, 0.15), linewidth = 0.3),
    panel.grid.minor  = element_line(color = alpha(INK, 0.08), linewidth = 0.2),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = title_size),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.title      = element_text(color = INK, size = 10),
    legend.text       = element_text(color = INK_SOFT, size = 8)
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
