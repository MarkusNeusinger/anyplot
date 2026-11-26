#' anyplot.ai
#' map-connection-lines: Connection Lines Map (Origin-Destination)
#' Library: ggplot2 | R
#' Quality: 85/100 | Created: 2026-05-28

library(ggplot2)
library(dplyr)
library(ragg)
if (!requireNamespace("maps", quietly = TRUE)) install.packages("maps", repos = "https://cran.r-project.org")

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Imprint marks ramp (colored lines on the page), per theme
SEQ_MARKS <- if (THEME == "light") {
  list(colours = c("#009E73", "#4467A3", "#002850"), values = c(0, 0.338, 1))
} else {
  list(colours = c("#007755", "#009E73", "#CDD9FF"), values = c(0, 0.32, 1))
}

# Columns
CITY       <- "city"          # role: label
LAT        <- "lat"           # role: y
LON        <- "lon"           # role: x
PASSENGERS <- "passengers_m"  # role: value

# Natural Earth projection (Savric et al.): lon/lat in degrees -> planar x/y
natural_earth <- function(lon, lat) {
  l <- lon * pi / 180
  p <- lat * pi / 180
  p2 <- p^2
  p4 <- p2^2
  data.frame(
    x = l * (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4))),
    y = p * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4)))
  )
}

# Great-circle arc by spherical linear interpolation
great_circle_arc <- function(lon1, lat1, lon2, lat2, n = 80L) {
  r <- pi / 180
  v1 <- c(cos(lat1 * r) * cos(lon1 * r), cos(lat1 * r) * sin(lon1 * r), sin(lat1 * r))
  v2 <- c(cos(lat2 * r) * cos(lon2 * r), cos(lat2 * r) * sin(lon2 * r), sin(lat2 * r))
  d  <- acos(pmax(pmin(sum(v1 * v2), 1), -1))
  t  <- seq(0, 1, length.out = n)
  xyz <- outer(sin((1 - t) * d) / sin(d), v1) + outer(sin(t * d) / sin(d), v2)
  data.frame(
    lon = atan2(xyz[, 2], xyz[, 1]) / r,
    lat = atan2(xyz[, 3], sqrt(xyz[, 1]^2 + xyz[, 2]^2)) / r
  )
}

# Data: major international hub airports and annual passengers per route (millions)
airports <- tibble::tibble(
  !!CITY := c("New York", "London", "Tokyo", "Dubai", "Sydney", "Sao Paulo",
              "Singapore", "Cape Town", "Mumbai", "Los Angeles", "Frankfurt", "Hong Kong"),
  !!LAT  := c(40.64, 51.48, 35.55, 25.25, -33.95, -23.43,
              1.36, -33.96, 19.09, 33.94, 50.03, 22.31),
  !!LON  := c(-73.78, -0.45, 139.78, 55.36, 151.17, -46.47,
              103.99, 18.60, 72.87, -118.41, 8.57, 113.91),
  # label placement relative to the marker
  hjust  = c(1.15, 1.15, -0.15, -0.15, 0.5, 1.15, -0.15, 1.15, 0.4, 1.15, -0.15, -0.15),
  vjust  = c(0.5, 0.5, 0.5, -0.4, 1.8, 0.5, 1.4, 0.5, 1.9, 0.5, -0.5, 1.3)
)

routes <- tibble::tibble(
  origin = c("New York", "London", "Dubai", "Singapore", "Los Angeles",
             "Frankfurt", "New York", "London", "Dubai", "Sao Paulo",
             "Tokyo", "Hong Kong", "Mumbai", "Sydney", "Cape Town"),
  dest   = c("London", "Dubai", "Mumbai", "Tokyo", "Tokyo",
             "Dubai", "Los Angeles", "Frankfurt", "Cape Town", "London",
             "Los Angeles", "Singapore", "Dubai", "Los Angeles", "Dubai"),
  !!PASSENGERS := c(3.2, 4.8, 3.1, 2.9, 5.1, 3.6, 4.3, 2.1, 1.9, 1.4,
                    4.7, 3.8, 2.6, 2.3, 1.1)
)
df <- routes |>
  left_join(airports[, c(CITY, LAT, LON)], by = c("origin" = CITY)) |>
  rename(origin_lat = all_of(LAT), origin_lon = all_of(LON)) |>
  left_join(airports[, c(CITY, LAT, LON)], by = c("dest" = CITY)) |>
  rename(dest_lat = all_of(LAT), dest_lon = all_of(LON))

# Plot: arcs are split where they cross the antimeridian, then projected
arc_df <- bind_rows(lapply(seq_len(nrow(df)), function(i) {
  pts <- great_circle_arc(df$origin_lon[i], df$origin_lat[i], df$dest_lon[i], df$dest_lat[i])
  pts$seg_id <- i * 10 + cumsum(c(0, abs(diff(pts$lon)) > 180))
  pts[[PASSENGERS]] <- df[[PASSENGERS]][i]
  pts
}))
arc_df[, c("x", "y")] <- natural_earth(arc_df$lon, arc_df$lat)

world_map <- map_data("world")
world_map[, c("x", "y")] <- natural_earth(world_map$long, world_map$lat)
airports[, c("x", "y")] <- natural_earth(airports[[LON]], airports[[LAT]])

# Graticule every 30 degrees and the map outline, in projected space
lats <- seq(-90, 90, length.out = 181)
lons <- seq(-180, 180, length.out = 361)
graticule <- bind_rows(
  lapply(seq(-60, 60, by = 30), function(a) cbind(natural_earth(lons, rep(a, length(lons))), g = paste0("lat", a))),
  lapply(seq(-150, 150, by = 30), function(o) cbind(natural_earth(rep(o, length(lats)), lats), g = paste0("lon", o)))
)
outline <- natural_earth(c(rep(-180, length(lats)), rep(180, length(lats))),
                         c(lats, rev(lats)))

title_str  <- "Global Flight Routes · map-connection-lines · r · ggplot2 · anyplot.ai"
title_size <- max(round(12 * 67 / nchar(title_str)), 8L)

p <- ggplot() +
  geom_polygon(data = outline, aes(x = x, y = y), fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3) +
  geom_polygon(data = world_map, aes(x = x, y = y, group = group),
               fill = INK_MUTED, color = NA, alpha = 0.22) +
  geom_path(data = graticule, aes(x = x, y = y, group = g),
            color = INK_SOFT, linewidth = 0.1, alpha = 0.3) +
  geom_path(data = arc_df,
            aes(x = x, y = y, group = seg_id,
                color = .data[[PASSENGERS]], linewidth = .data[[PASSENGERS]]),
            alpha = 0.6, lineend = "round") +
  geom_point(data = airports, aes(x = x, y = y),
             shape = 21, size = 2.8, fill = IMPRINT_PALETTE[1], color = PAGE_BG, stroke = 0.9) +
  geom_text(data = airports, aes(x = x, y = y, label = .data[[CITY]], hjust = hjust, vjust = vjust),
            color = INK, size = 3.1) +
  scale_color_gradientn(
    colours = SEQ_MARKS$colours, values = SEQ_MARKS$values,
    name = "Passengers\n(millions)",
    guide = guide_colorbar(barwidth = 0.7, barheight = 5.0, title.position = "top",
                           ticks.colour = INK_SOFT)
  ) +
  scale_linewidth_continuous(range = c(0.5, 2.6), guide = "none") +
  coord_fixed(expand = FALSE) +
  labs(title = title_str, x = NULL, y = NULL) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    axis.text         = element_blank(),
    axis.title        = element_blank(),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = title_size, hjust = 0.5, margin = margin(b = 6)),
    legend.background = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 9),
    legend.position   = "right",
    plot.margin       = margin(8, 12, 8, 8)
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
