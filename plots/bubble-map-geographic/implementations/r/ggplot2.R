#' anyplot.ai
#' bubble-map-geographic: Bubble Map with Sized Geographic Markers
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-05-18

library(ggplot2)
library(ragg)
library(tibble)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
LAND_BG     <- if (THEME == "light") "#EFEBDD" else "#2A2A26"
OCEAN_BG    <- if (THEME == "light") "#D6E8F2" else "#182530"
GRID_COLOR  <- if (THEME == "light") "#AACCDC" else "#2C4455"
IMPRINT     <- c("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD")

# Data: Major world cities with population (millions, 2023 estimates)
cities <- tibble(
  city       = c(
    "Tokyo", "Delhi", "Shanghai", "São Paulo", "Mexico City",
    "Cairo", "Mumbai", "Beijing", "New York", "Dhaka",
    "Karachi", "Buenos Aires", "Kolkata", "Lagos", "Istanbul",
    "Kinshasa", "Manila", "Rio de Janeiro", "Tianjin", "Guangzhou",
    "Los Angeles", "Moscow", "Shenzhen", "Bangalore", "Paris",
    "Jakarta", "Chennai", "Lima", "Chicago", "Lahore",
    "London", "Tehran", "Seoul", "Bangkok", "Nairobi",
    "Sydney", "Singapore", "Ho Chi Minh City", "Bogotá", "Johannesburg"
  ),
  lat        = c(
     35.7,  28.6,  31.2, -23.5,  19.4,
     30.1,  19.1,  39.9,  40.7,  23.8,
     24.9, -34.6,  22.6,   6.5,  41.0,
     -4.3,  14.6, -22.9,  39.1,  23.1,
     34.1,  55.8,  22.5,  12.9,  48.9,
     -6.2,  13.1, -12.1,  41.9,  31.6,
     51.5,  35.7,  37.6,  13.8,  -1.3,
    -33.9,   1.3,  10.8,   4.7, -26.2
  ),
  lon        = c(
    139.7,  77.2, 121.5, -46.6, -99.1,
     31.2,  72.9, 116.4, -74.0,  90.4,
     67.0, -58.4,  88.4,   3.4,  29.0,
     15.3, 121.0, -43.2, 117.2, 113.3,
   -118.2,  37.6, 114.1,  77.6,   2.3,
    106.8,  80.3, -77.0, -87.6,  74.3,
     -0.1,  51.4, 126.9, 100.5,  36.8,
    151.2, 103.8, 106.7, -74.1,  28.0
  ),
  population = c(
    37.4, 32.9, 28.5, 22.4, 22.1,
    21.8, 21.7, 21.5, 18.8, 22.5,
    17.2, 15.5, 14.9, 14.9, 15.4,
    17.1, 14.4, 13.7, 15.7, 16.1,
    12.5, 12.4, 13.4, 12.8, 11.1,
    11.2, 10.5, 11.0,  8.9, 14.0,
     9.5,  9.6,  9.9, 11.1,  5.3,
     5.4,  6.0,  9.3, 11.3,  6.1
  ),
  continent  = c(
    "Asia", "Asia", "Asia", "S. America", "N. America",
    "Africa", "Asia", "Asia", "N. America", "Asia",
    "Asia", "S. America", "Asia", "Africa", "Europe",
    "Africa", "Asia", "S. America", "Asia", "Asia",
    "N. America", "Europe", "Asia", "Asia", "Europe",
    "Asia", "Asia", "S. America", "N. America", "Asia",
    "Europe", "Asia", "Asia", "Asia", "Africa",
    "Oceania", "Asia", "Asia", "S. America", "Africa"
  )
)

# Simplified landmass outlines (lon, lat) as a quiet basemap: no map package is available
land_shapes <- list(
  "North America" = list(c(-168, -162, -141, -125, -95, -80, -62, -56, -66, -70, -76, -81, -80, -84, -90, -97, -97, -92, -88, -87, -83, -79, -84, -92, -105, -110, -115, -118, -124, -124, -135, -148, -158, -165),
                         c(66, 70, 70, 70, 72, 70, 60, 52, 45, 42, 35, 31, 25, 30, 29, 27, 21, 18, 21, 15, 10, 9, 8, 14, 20, 24, 30, 34, 40, 48, 58, 60, 57, 62)),
  "Greenland"     = list(c(-55, -45, -20, -20, -60, -70, -55), c(60, 60, 70, 82, 82, 76, 68)),
  "South America" = list(c(-77, -72, -62, -52, -50, -35, -39, -41, -48, -58, -57, -65, -68, -69, -74, -73, -71, -70, -76, -81, -80, -78),
                         c(8, 12, 10, 5, 0, -5, -14, -22, -26, -35, -39, -41, -50, -55, -50, -40, -30, -18, -14, -5, 0, 5)),
  "Africa"        = list(c(-17, -10, -6, 10, 11, 20, 32, 35, 43, 51, 40, 40, 35, 32, 26, 18, 12, 13, 9, 9, -5, -13, -17),
                         c(21, 30, 36, 37, 33, 31, 31, 28, 12, 12, -3, -15, -24, -29, -34, -34, -17, -7, 0, 4, 5, 8, 14)),
  "Madagascar"    = list(c(44, 47, 50, 49, 44), c(-25, -25, -15, -12, -17)),
  "Eurasia"       = list(c(-9, -9, -4, 2, 8, 10, 14, 21, 24, 30, 28, 40, 60, 70, 100, 115, 140, 160, 180, 180, 170, 163, 156, 155, 143, 135, 140, 130, 128, 126, 125, 121, 118, 122, 120, 122, 118, 110, 108, 106, 109, 105, 100, 103, 98, 98, 94, 92, 87, 80, 78, 73, 72, 67, 57, 56, 50, 48, 51, 56, 59, 52, 43, 39, 35, 35, 36, 28, 26, 23, 22, 19, 12, 16, 10, 3, -1),
                         c(37, 43, 48, 51, 54, 57, 55, 55, 60, 60, 70, 67, 69, 73, 77, 73, 72, 70, 68, 65, 60, 57, 51, 58, 59, 54, 48, 42, 35, 35, 40, 40, 38, 37, 32, 30, 24, 21, 21, 18, 12, 9, 13, 1, 8, 16, 17, 22, 21, 15, 8, 16, 21, 24, 25, 27, 30, 29, 24, 25, 22, 16, 13, 21, 28, 32, 36, 37, 40, 40, 37, 42, 45, 38, 44, 43, 37)),
  "Great Britain" = list(c(-5, 1, 2, -2, -3, -6, -5, -3, -5), c(50, 51, 53, 56, 58, 58, 55, 54, 52)),
  "Japan"         = list(c(130, 135, 140, 141, 142, 140, 138, 132), c(32, 34, 35, 40, 45, 42, 37, 35)),
  "Sumatra"       = list(c(95, 98, 106, 105, 101), c(5, 4, -3, -6, -3)),
  "Borneo"        = list(c(109, 117, 119, 116, 110), c(1, 7, 1, -4, -3)),
  "Java"          = list(c(105, 114, 114, 106), c(-6, -7, -8.5, -7.5)),
  "Luzon"         = list(c(120, 122, 124, 121), c(18, 18, 13, 14)),
  "Australia"     = list(c(114, 122, 130, 137, 142, 146, 153, 150, 141, 135, 130, 115, 114),
                         c(-22, -18, -12, -12, -11, -19, -26, -37, -38, -35, -32, -34, -26))
)
land <- do.call(rbind, lapply(names(land_shapes), function(nm) {
  data.frame(shape = nm, lon = land_shapes[[nm]][[1]], lat = land_shapes[[nm]][[2]])
}))

# Continent reference labels for geographic context
region_labels <- tibble(
  label = c("NORTH\nAMERICA", "SOUTH\nAMERICA", "EUROPE", "AFRICA", "ASIA", "AUSTRALIA"),
  lon   = c(-100, -60, 10, 20, 95, 134),
  lat   = c(50, -20, 55, 4, 48, -27)
)

# Color mapping by continent (Imprint order, Asia first = #009E73)
continent_colors <- c(
  "Asia"       = IMPRINT[1],
  "Africa"     = IMPRINT[2],
  "N. America" = IMPRINT[3],
  "S. America" = IMPRINT[4],
  "Europe"     = IMPRINT[5],
  "Oceania"    = IMPRINT[6]
)

# Largest bubbles first so smaller ones stay visible on top
cities <- cities[order(-cities$population), ]

plot_title <- "World\u2019s Largest Cities \u00b7 bubble-map-geographic \u00b7 r \u00b7 ggplot2 \u00b7 anyplot.ai"

# Plot
p <- ggplot(cities, aes(x = lon, y = lat)) +
  geom_polygon(
    data  = land,
    aes(x = lon, y = lat, group = shape),
    fill  = LAND_BG,
    color = INK_MUTED,
    linewidth = 0.25,
    inherit.aes = FALSE
  ) +
  geom_text(
    data  = region_labels,
    aes(x = lon, y = lat, label = label),
    color = INK_MUTED,
    size  = 2.4,
    fontface = "bold",
    lineheight = 0.85,
    inherit.aes = FALSE
  ) +
  geom_point(
    aes(size = population, fill = continent),
    alpha  = 0.70,
    shape  = 21,
    color  = PAGE_BG,
    stroke = 0.3
  ) +
  scale_fill_manual(
    values = continent_colors,
    name   = "Continent"
  ) +
  scale_size_area(
    max_size = 12,
    name     = "Population",
    breaks   = c(6, 10, 20, 37),
    labels   = c("6M", "10M", "20M", "37M")
  ) +
  guides(
    size = guide_legend(order = 1, override.aes = list(fill = INK_SOFT, alpha = 0.5)),
    fill = guide_legend(order = 2, override.aes = list(size = 4, alpha = 0.85))
  ) +
  scale_x_continuous(
    breaks = seq(-150, 150, by = 30),
    labels = function(x) paste0(abs(x), ifelse(x < 0, "\u00b0W", ifelse(x > 0, "\u00b0E", "\u00b0")))
  ) +
  scale_y_continuous(
    breaks = seq(-60, 80, by = 30),
    labels = function(y) paste0(abs(y), ifelse(y < 0, "\u00b0S", ifelse(y > 0, "\u00b0N", "\u00b0")))
  ) +
  coord_fixed(ratio = 1.3, xlim = c(-175, 175), ylim = c(-62, 82), expand = FALSE) +
  labs(
    title    = plot_title,
    subtitle = "Bubble area proportional to city population (millions), 2023 estimates",
    x        = "Longitude",
    y        = "Latitude"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG,     color = PAGE_BG),
    panel.background  = element_rect(fill = OCEAN_BG,    color = NA),
    panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.25),
    panel.grid.minor  = element_blank(),
    panel.border      = element_rect(color = INK_SOFT,   fill = NA, linewidth = 0.4),
    axis.title        = element_text(color = INK,        size = 10),
    axis.text         = element_text(color = INK_SOFT,   size = 8),
    plot.title        = element_text(color = INK,        size = 11, face = "bold"),
    plot.subtitle     = element_text(color = INK_SOFT,   size = 8),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT,   size = 8),
    legend.title      = element_text(color = INK,        size = 10),
    legend.key        = element_rect(fill = NA,          color = NA),
    plot.margin       = margin(10, 15, 10, 10)
  )

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
