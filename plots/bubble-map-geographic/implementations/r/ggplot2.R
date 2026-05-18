#' anyplot.ai
#' bubble-map-geographic: Bubble Map with Sized Geographic Markers
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-05-18

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)
library(tibble)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
OCEAN_BG    <- if (THEME == "light") "#D6E8F2" else "#182530"
GRID_COLOR  <- if (THEME == "light") "#AACCDC" else "#2C4455"
OKABE_ITO   <- c("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9")

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

# Continent reference labels for geographic context
region_labels <- tibble(
  label = c("NORTH\nAMERICA", "SOUTH\nAMERICA", "EUROPE", "AFRICA", "ASIA", "AUSTRALIA"),
  lon   = c(-100, -60, 10, 20, 95, 134),
  lat   = c(50, -20, 55, 4, 48, -27)
)

# Color mapping by continent (Okabe-Ito order, Asia first = #009E73)
continent_colors <- c(
  "Asia"       = OKABE_ITO[1],
  "Africa"     = OKABE_ITO[2],
  "N. America" = OKABE_ITO[3],
  "S. America" = OKABE_ITO[4],
  "Europe"     = OKABE_ITO[5],
  "Oceania"    = OKABE_ITO[6]
)

LABEL_COLOR <- if (THEME == "light") "#7A8C96" else "#4A6070"

# Plot
p <- ggplot(cities, aes(x = lon, y = lat)) +
  geom_text(
    data  = region_labels,
    aes(x = lon, y = lat, label = label),
    color = LABEL_COLOR,
    size  = 4,
    fontface = "bold",
    lineheight = 0.85,
    inherit.aes = FALSE
  ) +
  geom_point(
    aes(size = population, color = continent),
    alpha = 0.70,
    shape = 16
  ) +
  scale_color_manual(
    values = continent_colors,
    name   = "Continent"
  ) +
  scale_size_area(
    max_size = 24,
    name     = "Population",
    breaks   = c(5, 10, 20, 37),
    labels   = c("5M", "10M", "20M", "37M")
  ) +
  scale_x_continuous(
    breaks = seq(-150, 150, by = 30),
    labels = function(x) paste0(abs(x), ifelse(x < 0, "°W", ifelse(x > 0, "°E", "°")))
  ) +
  scale_y_continuous(
    breaks = seq(-60, 80, by = 30),
    labels = function(y) paste0(abs(y), ifelse(y < 0, "°S", ifelse(y > 0, "°N", "°")))
  ) +
  coord_fixed(ratio = 1.3, xlim = c(-175, 175), ylim = c(-62, 82)) +
  labs(
    title    = "World’s Largest Cities · bubble-map-geographic · r · ggplot2 · anyplot.ai",
    subtitle = "Bubble size proportional to city population (millions), 2023 estimates",
    x        = "Longitude",
    y        = "Latitude"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG,     color = PAGE_BG),
    panel.background  = element_rect(fill = OCEAN_BG,    color = NA),
    panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.4),
    panel.grid.minor  = element_blank(),
    panel.border      = element_rect(color = INK_SOFT,   fill = NA, linewidth = 0.6),
    axis.title        = element_text(color = INK,        size = 20),
    axis.text         = element_text(color = INK_SOFT,   size = 14),
    plot.title        = element_text(color = INK,        size = 22, face = "bold"),
    plot.subtitle     = element_text(color = INK_SOFT,   size = 16),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.4),
    legend.text       = element_text(color = INK_SOFT,   size = 14),
    legend.title      = element_text(color = INK,        size = 16),
    legend.key        = element_rect(fill = NA,          color = NA),
    plot.margin       = margin(20, 30, 20, 20)
  )

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
