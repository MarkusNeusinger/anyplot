#' anyplot.ai
#' flowmap-origin-destination: Origin-Destination Flow Map
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 81/100 | Created: 2026-05-20

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#8A8A82" else "#6E6D66"
IMPRINT     <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                 "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Simplified world coastlines (lon, lat pairs) for the basemap
coastlines <- list(
  north_america = c(-168, 65, -160, 70, -140, 70, -125, 70, -100, 69, -85, 70,
                    -80, 63, -94, 59, -90, 57, -82, 55, -79, 52, -77, 60, -70, 59,
                    -64, 60, -61, 56, -56, 52, -60, 47, -66, 45, -70, 42, -74, 40.5,
                    -76, 37, -76, 35, -81, 31, -80, 26, -82, 27, -83, 29, -89, 30,
                    -94, 29.5, -97, 26, -97, 22, -94, 18.5, -90, 21, -87, 21, -88, 16,
                    -84, 15, -83, 10, -79, 9, -80, 7, -85, 10, -87, 13, -92, 14.5,
                    -96, 16, -105, 20, -106, 23, -112, 29, -115, 31, -117, 32.5,
                    -120, 34.5, -124, 40, -124, 48, -130, 55, -140, 60, -150, 61,
                    -158, 58, -165, 62),
  south_america = c(-77, 8, -72, 12, -62, 10.5, -52, 5, -50, 0, -44, -2.5, -35, -5,
                    -35, -9, -39, -14, -41, -22, -48, -26, -53, -34, -58, -38,
                    -62, -40, -65, -45, -68, -50, -69, -55, -74, -52, -75, -45,
                    -73, -37, -71, -28, -70, -18, -76, -14, -81, -6, -80, -1, -77, 4),
  greenland     = c(-73, 78, -60, 82, -30, 83, -20, 75, -22, 70, -40, 65, -44, 60,
                    -50, 62, -54, 67, -58, 75),
  cuba          = c(-85, 21.9, -82, 23.1, -77, 22.3, -74.2, 20.2, -77.5, 19.9, -80, 21.8),
  hispaniola    = c(-74.5, 18.4, -72.8, 19.9, -69.5, 19.8, -68.3, 18.6, -71.5, 17.6),
  newfoundland  = c(-59.4, 47.6, -55.5, 51.6, -53, 49, -53.6, 46.6),
  iceland       = c(-24, 65.5, -22, 66.4, -16, 66.5, -13.6, 65.1, -18.7, 63.4, -22.5, 63.8),
  great_britain = c(-5, 50, 1.5, 51, 1.7, 52.8, 0, 53.5, -1.5, 55, -2, 57, -1.8, 57.6,
                    -4, 58.6, -5, 58.6, -6.2, 57, -5.5, 56, -4.8, 54.8, -3, 54.5,
                    -3.2, 53.4, -4.6, 53.2, -4.2, 52.3, -5.2, 51.7, -3.4, 51.4, -5.7, 50.1),
  ireland       = c(-6, 52, -6, 54, -7.5, 55.3, -10, 54.2, -10.3, 52, -8, 51.5),
  eurasia       = c(-9, 43.5, -9, 38.7, -8.8, 37, -5.6, 36, -2, 36.7, 0, 38.7, 3, 42,
                    3.5, 43.3, 6, 43, 8.5, 44.3, 10.5, 43, 12.5, 41.8, 15.6, 38,
                    16.5, 39.8, 18.5, 40.2, 16, 41.7, 13.5, 43.6, 12.3, 45.3, 13.7, 45.6,
                    15.5, 44, 19.5, 41.8, 19.3, 40.3, 21, 38, 23, 36.5, 24, 38, 23, 40.3,
                    26, 40.8, 26.5, 39.5, 27.3, 37, 29, 36.6, 32, 36.1, 36, 36.5, 35.9, 35,
                    35, 33, 34.3, 31.3, 32.6, 30, 34.3, 27.8, 35, 29.5, 35, 28, 38, 24,
                    39, 21.5, 42, 16.5, 43.3, 12.7, 45, 12.8, 49, 14, 52, 15.5, 55, 17,
                    57.8, 19, 59.8, 22.5, 58.5, 23.6, 56.4, 26.3, 54, 24.2, 51.5, 24.3,
                    51.2, 26.1, 50, 26.5, 48, 29.5, 50.3, 30, 51.5, 27.9, 54, 26.7,
                    56.3, 27.2, 58, 25.7, 61.6, 25.2, 66.5, 25.4, 68.5, 23.5, 70, 21,
                    72.8, 19, 73.5, 15.5, 75, 12, 76.5, 8.5, 77.5, 8, 79.5, 10.3,
                    80.2, 13.2, 80, 15.5, 82.3, 17, 86.5, 20, 88.5, 22, 90.5, 22.5,
                    91.8, 22.3, 92.5, 20.6, 94.3, 17, 94.5, 16, 97.6, 16.5, 98.5, 13,
                    98.3, 8, 100.3, 5.5, 101, 3, 103.5, 1.3, 104.3, 1.4, 103.4, 4.5,
                    102.3, 6.2, 100.4, 8.4, 99.2, 10, 100, 13.4, 100.9, 12.8, 102.5, 12,
                    105, 8.7, 106.6, 10.4, 109.2, 12, 109.3, 13.5, 108.5, 15.3,
                    106.5, 17.5, 105.7, 19, 107.5, 21.5, 109.5, 21.5, 110.5, 20.4,
                    111, 21.5, 113.5, 22.2, 117, 23.5, 119.5, 25.5, 121.5, 28.5,
                    122, 30.8, 121, 32.3, 120, 34.5, 119.2, 35, 120.6, 36.2, 122.5, 37,
                    118.8, 37.4, 118, 38.5, 121, 40.8, 121.5, 39, 124, 39.8, 125.3, 37.7,
                    126.5, 34.5, 129.3, 35.2, 129.5, 37, 128.3, 38.6, 129.7, 40.8,
                    130.7, 42.5, 133, 42.8, 135.5, 43.8, 138.5, 47, 140.5, 50,
                    141.4, 52.2, 140.5, 53.5, 137.5, 54, 135.3, 54.8, 140, 58, 143, 59.3,
                    149, 59.6, 154, 59.2, 155, 61.5, 160, 61.8, 163, 64, 170, 64.5,
                    180, 65, 180, 69, 170, 70, 160, 69.7, 150, 71, 140, 72.5, 130, 71,
                    120, 73, 112, 74, 105, 77.5, 98, 76, 90, 75.5, 80, 73.5, 72, 72.5,
                    70, 67, 66, 69.5, 59, 69, 55, 68.5, 44, 68.3, 41, 66.5, 36, 66.5,
                    33, 69, 25, 71, 18, 70, 14, 68, 12, 65.5, 8, 63, 5, 61.5, 5.5, 59,
                    8, 58, 10.5, 59.3, 11.5, 58, 12.7, 56, 14.2, 55.4, 16, 56.2,
                    16.7, 57.8, 19, 59.5, 17.5, 61, 17.5, 62.5, 21, 64.5, 22, 65.8,
                    25.3, 65.5, 25, 64.5, 21.5, 63, 21.3, 61, 23, 60, 29, 60.5, 26, 59.5,
                    23.5, 59.2, 21.5, 57.5, 21, 56, 21, 55, 19.5, 54.4, 14.3, 53.9,
                    11, 54, 10, 54.5, 10.5, 57.7, 8.2, 56.8, 8.6, 55, 8.7, 53.9, 7, 53.5,
                    5, 53.2, 4, 51.9, 2, 51, 1.5, 50.1, 0, 49.5, -1.2, 49.4, -1.8, 48.6,
                    -4.7, 48.4, -2.5, 47.3, -1.2, 46, -1.5, 43.4, -4, 43.4),
  black_sea     = c(28, 41.2, 31.5, 41.2, 36, 41.7, 41.5, 41.5, 41.6, 42.6, 39.5, 44,
                    37.5, 44.7, 38.2, 46, 35, 45.3, 33.5, 44.5, 32.5, 45.4, 30.5, 46.5,
                    29.6, 45.3, 28.6, 44, 27.9, 42.5),
  caspian_sea   = c(47, 44.5, 49.5, 46.5, 53, 47, 53, 45, 51.5, 44, 52.8, 41.5, 54, 40.5,
                    53.5, 37, 51, 36.7, 49, 38, 49.5, 40.4, 48, 42),
  sicily        = c(12.4, 38.1, 15.6, 38.3, 15.1, 36.7),
  africa        = c(-5.6, 35.9, -1, 35.3, 3, 36.8, 10, 37.2, 11, 35, 10, 34, 11, 33,
                    15, 32.3, 20, 30.5, 20, 32.5, 25, 32, 29, 31, 32.3, 31.3, 32.5, 29.8,
                    33.5, 27, 35.5, 24, 37, 21, 38.5, 18, 40, 15.5, 43.2, 11.5, 44, 10.5,
                    51.2, 11.8, 51, 10.4, 49, 6, 47.5, 4, 42, -1, 40, -3, 39, -6.5,
                    40, -10.5, 40.5, -15, 37, -17.5, 35, -21, 35.5, -24, 32.8, -26,
                    32, -29, 28, -33, 25, -34, 20, -34.8, 18.4, -34, 17.8, -31, 15, -27,
                    14.5, -22.5, 11.8, -17.5, 13.5, -11, 12, -6, 9.5, -1, 9.8, 3,
                    8.5, 4.5, 6, 4.3, 4.5, 6.3, 1, 6, -2, 4.8, -7.5, 4.3, -11.5, 6.8,
                    -13.3, 9, -15, 11, -16.8, 13.5, -17.4, 14.7, -16.5, 19.5, -17, 21,
                    -15, 25, -13, 27.7, -10, 29.5, -9.6, 30.5, -6.8, 34),
  madagascar    = c(49.3, -12, 50.5, -15.5, 49.5, -17.5, 47.2, -25, 45, -25.5,
                    43.5, -22, 44.4, -16.5, 47, -15),
  sri_lanka     = c(79.8, 9.8, 81.8, 7.5, 81.2, 6.1, 80, 6.2),
  honshu        = c(130, 31.3, 131.5, 31.5, 132, 33.8, 134.5, 33.8, 135.8, 33.5,
                    136.9, 34.3, 139, 34.7, 140.9, 35.7, 141, 38.3, 142, 39.5,
                    141.4, 41.4, 140.2, 40.8, 139.9, 39.5, 139.5, 38.2, 137, 37,
                    136, 35.8, 133, 35.5, 131, 34.4, 129.7, 33.2),
  hokkaido      = c(140, 41.5, 141.7, 42.5, 143.3, 42, 145.5, 43.3, 144.5, 44,
                    141.8, 45.4, 141.4, 43.5, 140, 42.5),
  taiwan        = c(120.1, 23, 120.8, 22, 121.9, 24.5, 121.5, 25.3),
  luzon         = c(120, 18.5, 122.2, 18.5, 122, 16, 121.5, 14, 124, 12.5, 123.5, 13.8,
                    121, 13.8, 120, 16),
  mindanao      = c(122, 7, 124, 8.5, 126.5, 9.5, 126.3, 6.3, 125.5, 5.7, 124, 6.4),
  sumatra       = c(95.3, 5.6, 98, 4, 100.5, 2, 104, -1, 106, -3.2, 105.8, -5.9,
                    104.5, -5.8, 102, -3.8, 100.5, -1, 98.7, 1.7),
  java          = c(105.2, -6.8, 108, -6.3, 111, -6.4, 114.5, -7.7, 114.5, -8.7,
                    111, -8.2, 106.5, -7.4),
  borneo        = c(109, 1.5, 110, 1.7, 111.5, 2.5, 113.5, 3.5, 115.5, 5.2, 117, 7,
                    119, 5.2, 118, 4.3, 118, 1, 119, 0.8, 117.5, -1, 116.5, -3.8,
                    114.5, -4, 111.5, -3, 110, -1.5),
  sulawesi      = c(119.5, -5.5, 119.8, -3.5, 118.8, -2.5, 119.5, 0, 120.5, 1.2,
                    124.8, 1.5, 123, 0.4, 120.2, 0.6, 121, -1, 123.3, -1, 122, -3,
                    123, -4.8, 122, -4.8, 120.5, -2.8, 120.5, -5.5),
  new_guinea    = c(131, -1.3, 134, -0.9, 137, -1.5, 141, -2.6, 145.8, -5, 147.5, -6.2,
                    147.8, -8, 150, -10.4, 146, -8.2, 143.5, -9, 141, -9.1, 139, -8.1,
                    138, -5.3, 135, -4.4, 132.8, -4, 132, -2.8),
  australia     = c(113.5, -22, 114, -26, 115, -30, 115, -33.5, 117.5, -35, 123.5, -33.9,
                    126, -32.3, 131, -31.5, 134, -32.8, 137.7, -35.5, 138.5, -34.5,
                    138, -33, 140, -37.8, 143, -38.7, 146.4, -39.1, 150, -37.5,
                    153, -31.5, 153.5, -28, 152.7, -25, 149.5, -22, 146, -18.8,
                    145.3, -15, 143.5, -14, 142.5, -10.7, 141.6, -12.8, 141.5, -16.5,
                    140, -17.7, 136.7, -15.9, 135.8, -13, 136.9, -12.2, 132.6, -11.5,
                    131, -12.2, 129.5, -14.9, 126.5, -13.9, 125, -15.5, 122.2, -17.5,
                    121, -19.5, 117, -20.6, 114, -21.8),
  tasmania      = c(144.6, -40.7, 148.3, -40.9, 148, -43.2, 146, -43.6)
)
world <- bind_rows(lapply(names(coastlines), function(nm) {
  xy <- matrix(coastlines[[nm]], ncol = 2, byrow = TRUE)
  data.frame(group = nm, long = xy[, 1], lat = xy[, 2])
}))

# Major global air hub coordinates and IATA codes
airports <- data.frame(
  name   = c("New York", "London", "Paris", "Dubai", "Tokyo",
             "Singapore", "Sydney", "Hong Kong", "Amsterdam", "Frankfurt"),
  code   = c("NYC", "LHR", "CDG", "DXB", "TYO",
             "SIN", "SYD", "HKG", "AMS", "FRA"),
  lat    = c(40.64, 51.47, 49.00, 25.25, 35.55,
             1.35, -33.95, 22.31, 52.31, 50.03),
  lon    = c(-73.78, -0.45, 2.55, 55.36, 139.78,
             103.99, 151.18, 113.92, 4.76, 8.57),
  region = c("Americas", "Europe", "Europe", "Middle East", "Asia Pacific",
             "Asia Pacific", "Asia Pacific", "Asia Pacific", "Europe", "Europe"),
  stringsAsFactors = FALSE
)

# Synthetic international air passenger flows (millions per year)
flows_raw <- data.frame(
  origin = c("New York", "New York", "New York", "London", "London",
             "London", "Dubai", "Dubai", "Dubai", "Singapore",
             "Singapore", "Singapore", "Tokyo", "Frankfurt", "Amsterdam"),
  dest   = c("London", "Paris", "Dubai", "Dubai", "Tokyo",
             "Amsterdam", "Singapore", "Frankfurt", "Tokyo", "Hong Kong",
             "Sydney", "Tokyo", "Hong Kong", "Amsterdam", "Paris"),
  flow   = c(4.2, 2.8, 3.6, 6.5, 3.1, 2.5, 5.8, 3.4, 2.6, 4.7,
             2.3, 3.2, 5.1, 3.8, 2.9),
  stringsAsFactors = FALSE
)

# Join origin and destination coordinates
flows <- flows_raw |>
  left_join(airports[, c("name", "lat", "lon", "region")],
            by = c("origin" = "name")) |>
  rename(origin_lat = lat, origin_lon = lon, origin_region = region) |>
  left_join(airports[, c("name", "lat", "lon")],
            by = c("dest" = "name")) |>
  rename(dest_lat = lat, dest_lon = lon)

region_colors <- c(
  "Americas"     = IMPRINT[1],
  "Europe"       = IMPRINT[2],
  "Middle East"  = IMPRINT[3],
  "Asia Pacific" = IMPRINT[4]
)

# Label anchors placed in open water/land away from the arcs, joined to their
# airport by a thin leader line so the dense European cluster stays readable
airports$label_lon <- c(-82, -18, -14,  60, 150, 96, 136, 108,   4,  22)
airports$label_lat <- c( 32,  58,  40,  15,  43, -6, -38,  31,  62,  58)

# Keep legend order matched to the Imprint palette order rather than alphabetical
flows$origin_region <- factor(flows$origin_region, levels = names(region_colors))
airports$region     <- factor(airports$region, levels = names(region_colors))

p <- ggplot() +
  geom_polygon(
    data = world,
    aes(x = long, y = lat, group = group),
    fill      = NA,
    color     = INK_MUTED,
    linewidth = 0.2
  ) +
  geom_curve(
    data = flows,
    aes(
      x         = origin_lon, y         = origin_lat,
      xend      = dest_lon,   yend      = dest_lat,
      color     = origin_region,
      linewidth = flow
    ),
    curvature = -0.3,
    alpha     = 0.65,
    arrow     = arrow(length = unit(0.008, "npc"), type = "open")
  ) +
  geom_segment(
    data = airports,
    aes(x = lon, y = lat, xend = label_lon, yend = label_lat),
    color     = INK_SOFT,
    linewidth = 0.25
  ) +
  geom_point(
    data = airports,
    aes(x = lon, y = lat, fill = region),
    shape  = 21,
    color  = PAGE_BG,
    size   = 3.5,
    stroke = 0.8
  ) +
  geom_label(
    data = airports,
    aes(x = label_lon, y = label_lat, label = code),
    color         = INK,
    fill          = ELEVATED_BG,
    border.colour = INK_SOFT,
    linewidth     = 0.2,
    size          = 2.8,
    fontface      = "bold",
    label.padding = unit(0.12, "lines")
  ) +
  scale_color_manual(values = region_colors, name = "Origin Region") +
  scale_fill_manual(values = region_colors, name = "Origin Region") +
  scale_linewidth_continuous(range = c(0.4, 2.8), name = "Flow (M pax/yr)") +
  coord_cartesian(xlim = c(-100, 165), ylim = c(-40, 65), expand = FALSE) +
  labs(
    title    = "Global Air Passenger Flows · flowmap-origin-destination · r · ggplot2 · anyplot.ai",
    subtitle = "LHR–DXB is the busiest corridor at 6.5M pax/yr",
    x = "Longitude", y = "Latitude"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major    = element_line(color = scales::alpha(INK_SOFT, 0.3),
                                       linewidth = 0.1),
    panel.grid.minor    = element_blank(),
    axis.text           = element_text(color = INK_SOFT, size = 8),
    axis.title          = element_text(color = INK, size = 10),
    axis.ticks          = element_blank(),
    plot.title.position = "plot",
    plot.title          = element_text(color = INK, size = 10, face = "bold",
                                       margin = margin(b = 4)),
    plot.subtitle       = element_text(color = INK_SOFT, size = 8,
                                       margin = margin(b = 6)),
    legend.background   = element_rect(fill = ELEVATED_BG, color = INK_SOFT,
                                       linewidth = 0.3),
    legend.text         = element_text(color = INK_SOFT, size = 8),
    legend.title        = element_text(color = INK, size = 10),
    legend.key          = element_rect(fill = NA, color = NA),
    legend.position     = "right",
    plot.margin         = margin(t = 8, r = 12, b = 8, l = 8)
  ) +
  guides(
    fill      = guide_legend(order = 1),
    color     = guide_legend(order = 1),
    linewidth = guide_legend(order = 2,
                             override.aes = list(color = INK_SOFT, alpha = 1))
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
