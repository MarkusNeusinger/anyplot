#' anyplot.ai
#' map-connection-lines: Connection Lines Map (Origin-Destination)
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 83/100 | Updated: 2026-11-26

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
  list(colours = c("#009E73", "#024582", "#351E45"), values = c(0, 0.687, 1))
} else {
  list(colours = c("#6F7E20", "#009E73", "#CDD9FF"), values = c(0, 0.21, 1))
}

# Columns
CITY       <- "city"          # role: label
LAT        <- "lat"           # role: y
LON        <- "lon"           # role: x
PASSENGERS <- "passengers_m"  # role: value

# Data: major international hub airports and annual passengers per route (millions)
airports <- tibble::tibble(
  !!CITY := c("New York", "London", "Tokyo", "Dubai", "Sydney", "Sao Paulo",
              "Singapore", "Cape Town", "Mumbai", "Los Angeles", "Frankfurt", "Hong Kong"),
  !!LAT  := c(40.64, 51.48, 35.55, 25.25, -33.95, -23.43,
              1.36, -33.96, 19.09, 33.94, 50.03, 22.31),
  !!LON  := c(-73.78, -0.45, 139.78, 55.36, 151.17, -46.47,
              103.99, 18.60, 72.87, -118.41, 8.57, 113.91),
  # label placement relative to the marker
  hjust  = c(1.1, 1.3, -0.3, -0.15, 0.5, 1.15, -0.15, 1.15, 0.4, 1.15, -0.15, -0.15),
  vjust  = c(-1.0, 0.5, 0.5, -0.4, 1.8, 0.5, 1.4, 0.5, 1.9, 0.5, -0.5, 1.3)
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

# Plot: great-circle arcs by spherical interpolation, 80 points per route
R_DEG <- pi / 180
N_ARC <- 80L
arc_df <- df |>
  mutate(
    route = row_number(),
    p1x = cos(origin_lat * R_DEG) * cos(origin_lon * R_DEG),
    p1y = cos(origin_lat * R_DEG) * sin(origin_lon * R_DEG),
    p1z = sin(origin_lat * R_DEG),
    p2x = cos(dest_lat * R_DEG) * cos(dest_lon * R_DEG),
    p2y = cos(dest_lat * R_DEG) * sin(dest_lon * R_DEG),
    p2z = sin(dest_lat * R_DEG),
    ang = acos(pmax(pmin(p1x * p2x + p1y * p2y + p1z * p2z, 1), -1))
  ) |>
  tidyr::crossing(t = seq(0, 1, length.out = N_ARC)) |>
  arrange(route, t) |>
  mutate(
    wa = sin((1 - t) * ang) / sin(ang),
    wb = sin(t * ang) / sin(ang),
    ax = wa * p1x + wb * p2x,
    ay = wa * p1y + wb * p2y,
    az = wa * p1z + wb * p2z,
    lon = atan2(ay, ax) / R_DEG,
    lat = atan2(az, sqrt(ax^2 + ay^2)) / R_DEG
  ) |>
  group_by(route) |>
  # a longitude jump over 180 degrees marks an antimeridian crossing: start a new segment
  mutate(seg_id = route * 10 + cumsum(c(0, abs(diff(lon)) > 180))) |>
  ungroup()

# Base map layers in lon/lat: country polygons, graticule every 30 degrees, map outline
lats <- seq(-90, 90, length.out = 181)
lons <- seq(-180, 180, length.out = 361)
geo <- bind_rows(
  arcs     = arc_df |> select(lon, lat, seg_id, all_of(PASSENGERS)),
  airports = airports |> select(all_of(c(CITY, LAT, LON, "hjust", "vjust"))) |>
    rename(lat = all_of(LAT), lon = all_of(LON)),
  world    = map_data("world") |> select(lon = long, lat, group),
  graticule = bind_rows(
    lapply(seq(-60, 60, by = 30), function(a) tibble::tibble(lon = lons, lat = a, g = paste0("lat", a))),
    lapply(seq(-150, 150, by = 30), function(o) tibble::tibble(lon = o, lat = lats, g = paste0("lon", o)))
  ),
  outline  = tibble::tibble(lon = c(rep(-180, length(lats)), rep(180, length(lats))), lat = c(lats, rev(lats))),
  .id = "layer"
)

# Natural Earth projection (Savric et al.): lon/lat in degrees -> planar x/y
geo <- geo |>
  mutate(
    phi  = lat * R_DEG,
    phi2 = phi^2,
    phi4 = phi2^2,
    x = lon * R_DEG * (0.8707 - 0.131979 * phi2 +
                         phi4 * (-0.013791 + phi4 * (0.003971 * phi2 - 0.001529 * phi4))),
    y = phi * (1.007226 + phi2 * (0.015085 + phi4 * (-0.044475 + 0.028874 * phi2 - 0.005916 * phi4)))
  )
arc_df    <- filter(geo, layer == "arcs")
airports  <- filter(geo, layer == "airports")
world_map <- filter(geo, layer == "world")
graticule <- filter(geo, layer == "graticule")
outline   <- filter(geo, layer == "outline")

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
