#' anyplot.ai
#' map-marker-clustered: Clustered Marker Map
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-05-23

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
WATER_BG    <- if (THEME == "light") "#CDDFF0" else "#101E2A"
LAND_FILL   <- if (THEME == "light") "#E0EBD5" else "#263322"

IMPRINT <- c(
    "#009E73",  # 1: Music venues
    "#C475FD",  # 2: Sports venues
    "#AE3030"   # 3: Arts venues
)
categories <- c("Music", "Sports", "Arts")

# --- Data -------------------------------------------------------------------
metro_areas <- data.frame(
    lat = c(
        40.71, 34.05, 41.88, 29.76, 33.45, 39.95, 29.42,
        32.72, 32.78, 30.27, 47.61, 39.74, 42.36, 25.77,
        45.52, 44.98, 33.75, 42.33, 36.17, 36.16
    ),
    lon = c(
        -74.01, -118.24, -87.63, -95.37, -112.07, -75.17, -98.49,
        -117.16, -96.80, -97.74, -122.33, -104.99, -71.06, -80.19,
        -122.68, -93.27, -84.39, -83.05, -115.14, -86.78
    ),
    weight = c(15, 12, 10, 7, 7, 6, 5, 5, 5, 5, 4, 4, 4, 3, 3, 2, 2, 2, 2, 2)
)

n_venues <- 460
city_idx <- sample(
    nrow(metro_areas), n_venues,
    replace = TRUE,
    prob    = metro_areas$weight / sum(metro_areas$weight)
)

venues <- data.frame(
    lat      = metro_areas$lat[city_idx] + rnorm(n_venues, 0, 0.55),
    lon      = metro_areas$lon[city_idx] + rnorm(n_venues, 0, 0.75),
    category = sample(categories, n_venues, replace = TRUE, prob = c(0.40, 0.35, 0.25))
)

# Grid-based pre-clustering — simulates a fixed zoom-level snapshot
grid_res <- 3.5
clusters <- venues %>%
    mutate(
        clat = round(lat / grid_res) * grid_res,
        clon = round(lon / grid_res) * grid_res
    ) %>%
    group_by(clat, clon) %>%
    summarize(
        count    = dplyr::n(),
        category = names(sort(table(category), decreasing = TRUE))[1],
        .groups  = "drop"
    )

# Simplified contiguous-US outline (lon, lat), clockwise from the north-west corner
us_outline <- data.frame(
    long = c(
        -124.7, -122.8, -95.2, -94.6, -93.0, -91.5, -89.6, -92.0, -90.4, -88.0,
        -86.5, -84.6, -83.5, -83.4, -82.5, -83.1, -83.4, -81.7, -79.0, -79.0,
        -76.2, -76.3, -74.7, -71.5, -70.8, -70.2, -69.2, -67.8, -67.8, -67.0,
        -68.5, -70.2, -70.7, -70.6, -71.0, -70.0, -70.6, -71.4, -72.9, -73.7,
        -74.0, -74.0, -74.9, -75.1, -75.9, -76.0, -75.5, -76.5, -77.9, -79.0,
        -80.9, -81.4, -81.3, -80.5, -80.1, -80.15, -80.4, -81.1, -81.8, -82.7,
        -82.8, -83.7, -84.3, -85.3, -86.5, -88.0, -89.4, -89.2, -90.1, -91.3,
        -93.8, -94.7, -96.4, -97.2, -97.4, -99.1, -99.5, -100.3, -101.4, -102.4,
        -103.1, -104.5, -105.0, -106.5, -108.2, -108.2, -111.1, -114.8, -117.1, -117.3,
        -118.4, -119.2, -120.5, -120.65, -121.9, -122.5, -123.0, -123.8, -124.4, -124.1,
        -124.5, -124.1, -124.0
    ),
    lat = c(
        48.4, 49.0, 49.0, 48.7, 48.6, 48.1, 48.0, 46.8, 46.6, 47.4,
        46.5, 46.5, 46.0, 45.1, 43.0, 42.1, 41.7, 41.5, 42.8, 43.3,
        43.6, 44.2, 45.0, 45.0, 45.4, 46.5, 47.45, 47.07, 45.7, 44.8,
        44.2, 43.6, 43.0, 42.6, 42.3, 41.8, 41.55, 41.4, 41.25, 40.9,
        40.6, 40.0, 38.95, 38.4, 37.1, 36.9, 35.25, 34.7, 33.9, 33.3,
        32.0, 30.7, 29.9, 28.4, 26.8, 25.8, 25.2, 25.15, 26.1, 27.7,
        28.9, 29.9, 30.0, 29.7, 30.4, 30.25, 30.2, 29.2, 29.1, 29.3,
        29.7, 29.35, 28.4, 27.6, 25.95, 26.4, 27.5, 28.3, 29.8, 29.8,
        29.0, 29.65, 30.65, 31.75, 31.78, 31.33, 31.33, 32.5, 32.53, 33.1,
        33.75, 34.15, 34.45, 35.15, 36.6, 37.8, 38.0, 39.4, 40.4, 41.9,
        42.8, 44.0, 46.2
    ),
    group = 1
)

# --- Plot -------------------------------------------------------------------
p <- ggplot() +
    geom_polygon(
        data      = us_outline,
        aes(x = long, y = lat, group = group),
        fill      = LAND_FILL,
        color     = INK_MUTED,
        linewidth = 0.15
    ) +
    geom_point(
        data   = clusters,
        aes(x = clon, y = clat, size = count, fill = category),
        shape  = 21,
        color  = PAGE_BG,
        alpha  = 0.90,
        stroke = 0.5
    ) +
    geom_text(
        data     = clusters,
        aes(x = clon, y = clat, label = count),
        size     = 2.5,
        color    = "white",
        fontface = "bold"
    ) +
    scale_fill_manual(
        values = setNames(IMPRINT, categories),
        name   = "Venue Type"
    ) +
    scale_size(
        range  = c(4, 18),
        name   = "Venues",
        breaks = c(5, 20, 50, 80),
        guide  = guide_legend(
            override.aes = list(fill = INK_SOFT, color = PAGE_BG, stroke = 0.5)
        )
    ) +
    coord_fixed(
        ratio = 1.3,
        xlim  = c(-126, -66),
        ylim  = c(23.5, 50.5)
    ) +
    labs(
        title = "Venue Clusters · map-marker-clustered · r · ggplot2 · anyplot.ai",
        x     = "Longitude",
        y     = "Latitude"
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background  = element_rect(fill = WATER_BG, color = NA),
        panel.grid.major  = element_line(color = INK_SOFT, linewidth = 0.15),
        panel.grid.minor  = element_blank(),
        panel.border      = element_rect(fill = NA, color = INK_SOFT, linewidth = 0.3),
        axis.title        = element_text(color = INK, size = 10),
        axis.text         = element_text(color = INK_SOFT, size = 8),
        plot.title        = element_text(color = INK, size = 11, face = "bold"),
        legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
        legend.text       = element_text(color = INK_SOFT, size = 8),
        legend.title      = element_text(color = INK, size = 9),
        legend.key        = element_rect(fill = NA, color = NA),
        plot.margin       = margin(10, 15, 10, 10)
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
