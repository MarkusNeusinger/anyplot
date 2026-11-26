#' anyplot.ai
#' map-projections: World Map with Different Projections
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 86/100 | Updated: 2026-11-26

library(ggplot2)
library(maps)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
OCEAN_BG    <- if (THEME == "light") "#C4DCF0" else "#152030"
LAND_BG     <- if (THEME == "light") "#D4C9A8" else "#2A3020"

IMPRINT <- c(
    "#009E73", "#C475FD", "#AE3030", "#4467A3",
    "#99B314", "#954477", "#BD8233"
)

# --- Data: every lon/lat point of every layer in one table --------------------
world <- map_data("world")

# Graticule every 30 degrees; the equator and prime meridian are two of its lines
lat_dense <- seq(-90, 90, length.out = 541)
lon_dense <- seq(-180, 180, length.out = 1081)
meridians <- do.call(rbind, lapply(seq(-180, 180, by = 30), function(lon0) {
    data.frame(lon = lon0, lat = lat_dense, group = paste0("mer_", lon0))
}))
parallels <- do.call(rbind, lapply(seq(-90, 90, by = 30), function(lat0) {
    data.frame(lon = lon_dense, lat = lat0, group = paste0("par_", lat0))
}))

# Tissot indicatrices: 5 degree geodesic circles on a 30 x 60 degree grid
r_deg    <- 5
t_circle <- seq(0, 2 * pi, length.out = 73)
centers  <- expand.grid(lat0 = seq(-60, 60, by = 30), lon0 = seq(-150, 150, by = 60))
tissot   <- do.call(rbind, lapply(seq_len(nrow(centers)), function(i) {
    lat0 <- centers$lat0[i]
    lon0 <- centers$lon0[i]
    data.frame(
        lon   = lon0 + r_deg * cos(t_circle) / max(cos(lat0 * pi / 180), 0.08),
        lat   = pmax(pmin(lat0 + r_deg * sin(t_circle), 89.9), -89.9),
        group = paste0("t_", lon0, "_", lat0)
    )
}))

pts <- rbind(
    data.frame(lon = world$long, lat = world$lat, group = world$group, layer = "world"),
    data.frame(rbind(meridians, parallels), layer = "graticule"),
    data.frame(tissot, layer = "tissot")
)

# Mollweide projection of all points at once: solve
# 2*theta + sin(2*theta) = pi*sin(lat) by Newton-Raphson, vectorised
phi   <- pts$lat * pi / 180
theta <- phi
for (i in 1:60) {
    theta <- theta - (2 * theta + sin(2 * theta) - pi * sin(phi)) /
        pmax(2 + 2 * cos(2 * theta), 1e-9)
}
theta[abs(phi) >= pi / 2 - 1e-9] <- sign(phi[abs(phi) >= pi / 2 - 1e-9]) * pi / 2
pts$x <- (2 * sqrt(2) / pi) * (pts$lon * pi / 180) * cos(theta)
pts$y <- sqrt(2) * sin(theta)

world     <- pts[pts$layer == "world", ]
graticule <- pts[pts$layer == "graticule", ]
tissot    <- pts[pts$layer == "tissot", ]
boundary  <- data.frame(
    x = 2 * sqrt(2) * cos(seq(0, 2 * pi, length.out = 721)),
    y = sqrt(2) * sin(seq(0, 2 * pi, length.out = 721))
)

# --- Plot --------------------------------------------------------------------
p <- ggplot() +
    # Ocean fill
    geom_polygon(
        data = boundary, aes(x = x, y = y),
        fill = OCEAN_BG, color = NA
    ) +
    # Land masses (country polygons)
    geom_polygon(
        data = world, aes(x = x, y = y, group = group),
        fill = LAND_BG, color = NA
    ) +
    # Country borders / coastlines
    geom_path(
        data = world, aes(x = x, y = y, group = group),
        color = INK_SOFT, linewidth = 0.25, alpha = 0.80
    ) +
    # Graticule (30° grid, lighter than the coastlines)
    geom_path(
        data = graticule, aes(x = x, y = y, group = group),
        color = INK_SOFT, linewidth = 0.12, alpha = 0.40
    ) +
    # Tissot indicatrices — anyplot brand green (position 1)
    geom_polygon(
        data = tissot, aes(x = x, y = y, group = group),
        fill = IMPRINT[1], color = PAGE_BG,
        linewidth = 0.06, alpha = 0.78
    ) +
    # Ellipse outline
    geom_path(
        data = boundary, aes(x = x, y = y),
        color = INK_SOFT, linewidth = 0.40
    ) +
    coord_fixed() +
    labs(
        title    = "map-projections · r · ggplot2 · anyplot.ai",
        subtitle = "Mollweide equal-area projection  ·  green Tissot circles: equal area, changing shape"
    ) +
    theme_void(base_size = 8) +
    theme(
        plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG),
        plot.title      = element_text(
            color  = INK, size = 12, hjust = 0.5,
            margin = margin(t = 14, b = 6)
        ),
        plot.subtitle   = element_text(
            color  = INK_SOFT, size = 9.5, hjust = 0.5,
            margin = margin(b = 12)
        ),
        plot.margin     = margin(8, 50, 12, 50)
    )

# --- Save --------------------------------------------------------------------
ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 8,
    height   = 4.5,
    units    = "in",
    dpi      = 400
)
