#' anyplot.ai
#' contour-map-geographic: Contour Lines on Geographic Map
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: pending | Updated: 2026-11-26

library(ggplot2)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint sequential ramp for filled fields, sampled once per pressure band
SEQ_FIELDS <- if (THEME == "light") {
  list(colours = c("#66E2B2", "#009E73", "#024582", "#351E45"), values = c(0, 0.369, 0.803, 1))
} else {
  list(colours = c("#404C02", "#009E73", "#CDD9FF"), values = c(0, 0.487, 1))
}

# Synthetic atmospheric pressure field (North Atlantic / Europe)
# Classic pattern: Azores High (SW), Icelandic Low (NW), European ridge (E)
lon_seq <- seq(-30, 45, length.out = 60)
lat_seq <- seq(35, 72, length.out = 50)
grid    <- expand.grid(lon = lon_seq, lat = lat_seq)

grid$pressure <- with(grid,
  1013 +
  12 * exp(-((lon + 28)^2 + (lat - 32)^2) / 250) +     # Azores High centre
  (-15) * exp(-((lon + 22)^2 + (lat - 65)^2) / 200) +  # Icelandic Low centre
  5 * exp(-((lon - 12)^2 + (lat - 51)^2) / 280)         # European High ridge
)

# 4 hPa isobar intervals — standard for synoptic weather maps
isobar_breaks <- seq(998, 1026, by = 4)

# Compute isobar label positions — midpoint of the longest segment per level
pressure_matrix <- matrix(grid$pressure, nrow = length(lon_seq), ncol = length(lat_seq))
label_df <- do.call(rbind, lapply(isobar_breaks, function(level) {
  cl <- contourLines(lon_seq, lat_seq, pressure_matrix, levels = level)
  if (length(cl) == 0) return(NULL)
  main <- cl[[which.max(sapply(cl, function(c) length(c$x)))]]
  mid  <- ceiling(length(main$x) / 2)
  data.frame(lon = main$x[mid], lat = main$y[mid], label = as.character(level))
}))

band_fill <- scales::gradient_n_pal(SEQ_FIELDS$colours, SEQ_FIELDS$values)(
  seq(0, 1, length.out = length(isobar_breaks) - 1)
)

# World coastlines and political borders
world <- map_data("world")

# Plot
p <- ggplot() +
  geom_contour_filled(
    data   = grid,
    aes(x = lon, y = lat, z = pressure),
    breaks = isobar_breaks
  ) +
  geom_polygon(
    data      = world,
    aes(x = long, y = lat, group = group),
    fill      = NA,
    color     = INK,
    linewidth = 0.25
  ) +
  geom_contour(
    data      = grid,
    aes(x = lon, y = lat, z = pressure),
    breaks    = isobar_breaks,
    color     = INK,
    linewidth = 0.3,
    alpha     = 0.75
  ) +
  geom_label(
    data          = label_df,
    aes(x = lon, y = lat, label = label),
    color         = INK,
    fill          = PAGE_BG,
    size          = 3,
    label.size    = 0.15,
    label.padding = unit(0.1, "lines"),
    fontface      = "bold"
  ) +
  coord_fixed(xlim = c(-30, 45), ylim = c(35, 72), expand = FALSE) +
  scale_fill_manual(values = band_fill, drop = FALSE, name = "Pressure\n(hPa)") +
  labs(
    title = "N. Atlantic Isobars · contour-map-geographic · r · ggplot2 · anyplot.ai",
    x     = "Longitude (°E)",
    y     = "Latitude (°N)"
  ) +
  scale_x_continuous(labels = function(x) paste0(x, "°")) +
  scale_y_continuous(labels = function(x) paste0(x, "°")) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG,     color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG,     color = NA),
    panel.grid.major  = element_line(color = INK_SOFT,   linewidth = 0.15, linetype = "dotted"),
    panel.grid.minor  = element_blank(),
    panel.border      = element_rect(color = INK_SOFT,   fill = NA, linewidth = 0.4),
    axis.title        = element_text(color = INK,        size = 10),
    axis.text         = element_text(color = INK_SOFT,   size = 8),
    plot.title        = element_text(color = INK,        size = 12, face = "bold"),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT,   size = 8),
    legend.title      = element_text(color = INK,        size = 9),
    legend.key.size   = unit(0.4, "cm")
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
