#' anyplot.ai
#' hexbin-map-geographic: Hexagonal Binning Map
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-05-27

library(ggplot2)
library(dplyr)
library(tibble)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# NYC metro area taxi pickups — simulated density clusters
# Cluster centres: Midtown, Greenwich Village, UWS, Chelsea, S.Brooklyn,
#                  Midtown East, Lower Manhattan, JFK-adjacent, LGA-adjacent, Jersey City
cluster_centers <- tibble::tibble(
  lat   = c(40.756, 40.730, 40.775, 40.744, 40.676,
             40.762, 40.710, 40.645, 40.769, 40.727),
  lon   = c(-73.989, -74.003, -73.981, -73.995, -73.982,
             -73.971, -73.997, -73.794, -73.863, -74.077),
  n     = c(5000L, 3200L, 2400L, 2600L, 1800L,
             1400L, 1000L, 700L, 600L, 500L),
  s_lat = c(0.010, 0.009, 0.011, 0.009, 0.013,
             0.010, 0.009, 0.009, 0.008, 0.009),
  s_lon = c(0.013, 0.011, 0.013, 0.011, 0.015,
             0.012, 0.011, 0.012, 0.010, 0.011)
)

pickups <- dplyr::bind_rows(
  lapply(seq_len(nrow(cluster_centers)), function(i) {
    cc <- cluster_centers[i, ]
    tibble::tibble(
      lat = rnorm(cc$n, cc$lat, cc$s_lat),
      lon = rnorm(cc$n, cc$lon, cc$s_lon)
    )
  })
) |> dplyr::filter(
  lat >= 40.60, lat <= 40.83,
  lon >= -74.15, lon <= -73.75
)

plot_title <- "hexbin-map-geographic · r · ggplot2 · anyplot.ai"
title_size <- max(8L, round(12 * min(1.0, 67 / nchar(plot_title))))

p <- ggplot(pickups, aes(x = lon, y = lat)) +
  geom_hex(bins = 38, alpha = 0.88) +
  scale_fill_gradient(
    low    = "#009E73",
    high   = "#4467A3",
    name   = "Pickup\nCount",
    labels = scales::comma,
    guide  = guide_colorbar(barwidth = 0.8, barheight = 8)
  ) +
  scale_x_continuous(
    labels = function(x) sprintf("%.2f°W", -x),
    expand = expansion(mult = 0.01)
  ) +
  scale_y_continuous(
    labels = function(y) sprintf("%.2f°N", y),
    expand = expansion(mult = 0.01)
  ) +
  labs(
    x     = "Longitude",
    y     = "Latitude",
    title = plot_title
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK_SOFT, linewidth = 0.15),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK,      size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK,      size = title_size, face = "bold"),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK,      size = 9),
    legend.position   = "right",
    plot.margin       = margin(0.4, 0.4, 0.4, 0.4, "cm")
  )

ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
