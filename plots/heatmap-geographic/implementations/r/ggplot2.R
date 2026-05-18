#' anyplot.ai
#' heatmap-geographic: Geographic Heatmap for Spatial Density
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-05-18

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Data: simulated convective storm event locations over the eastern United States
gulf_coast <- data.frame(
  longitude = rnorm(420, mean = -90, sd = 3.0),
  latitude  = rnorm(420, mean = 30,  sd = 1.8)
)
great_plains <- data.frame(
  longitude = rnorm(500, mean = -96, sd = 4.5),
  latitude  = rnorm(500, mean = 37,  sd = 3.0)
)
appalachians <- data.frame(
  longitude = rnorm(330, mean = -79, sd = 2.5),
  latitude  = rnorm(330, mean = 40,  sd = 2.2)
)
florida_pen <- data.frame(
  longitude = rnorm(250, mean = -82, sd = 1.5),
  latitude  = rnorm(250, mean = 27,  sd = 1.5)
)

events <- rbind(gulf_coast, great_plains, appalachians, florida_pen)

# Kernel density estimation over eastern US
lon_range <- c(-105, -65)
lat_range <- c(24,   51)

kde_out <- MASS::kde2d(
  x    = events$longitude,
  y    = events$latitude,
  n    = 200,
  h    = c(2.5, 2.0),
  lims = c(lon_range, lat_range)
)

kde_df          <- expand.grid(longitude = kde_out$x, latitude = kde_out$y)
kde_df$density  <- as.vector(kde_out$z)
kde_df$density[kde_df$density < quantile(kde_df$density, 0.15)] <- NA

# Plot
p <- ggplot() +
  geom_raster(
    data        = kde_df,
    aes(x = longitude, y = latitude, fill = density),
    interpolate = TRUE
  ) +
  scale_fill_viridis_c(
    option   = "inferno",
    name     = "Storm\nDensity",
    na.value = "transparent",
    guide    = guide_colorbar(
      barwidth       = 1.5,
      barheight      = 8,
      title.position = "top",
      title.hjust    = 0.5
    )
  ) +
  coord_cartesian(xlim = lon_range, ylim = lat_range, expand = FALSE) +
  labs(
    title = "Convective Storm Event Density · heatmap-geographic · r · ggplot2 · anyplot.ai",
    x     = "Longitude",
    y     = "Latitude"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK_SOFT, linewidth = 0.25, linetype = "dotted"),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.title        = element_text(color = INK,      size = 20),
    axis.text         = element_text(color = INK_SOFT, size = 16),
    plot.title        = element_text(color = INK,      size = 22, margin = margin(b = 12)),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.4),
    legend.text       = element_text(color = INK_SOFT, size = 16),
    legend.title      = element_text(color = INK,      size = 18),
    legend.position   = "right",
    plot.margin       = margin(15, 15, 15, 15)
  )

# Add geographic borders when the maps package is available
if (requireNamespace("maps", quietly = TRUE)) {
  countries <- map_data("world", region = c("USA", "Canada", "Mexico"))
  us_states <- map_data("state")

  p <- p +
    geom_polygon(
      data    = countries,
      mapping = aes(x = long, y = lat, group = group),
      fill    = NA, color = INK_SOFT, linewidth = 0.5,
      inherit.aes = FALSE
    ) +
    geom_polygon(
      data    = us_states,
      mapping = aes(x = long, y = lat, group = group),
      fill    = NA, color = INK_SOFT, linewidth = 0.2,
      inherit.aes = FALSE
    )
}

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 16,
  height   = 9,
  units    = "in",
  dpi      = 300
)
