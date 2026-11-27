#' anyplot.ai
#' map-route-path: Route Path Map
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 85/100 | Updated: 2026-11-26

library(ggplot2)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID        <- alpha(INK, 0.15)
LAND        <- if (THEME == "light") "#ECE8DA" else "#2A2A25"  # quiet land fill
SEA         <- if (THEME == "light") "#E4ECEA" else "#1E2624"  # quiet sea tint
COAST       <- alpha(INK_SOFT, 0.55)

# Imprint palette: start marker = position 1, end marker = matte red (position 5)
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")
# Imprint sequential ramp for marks (a colored line sits on the page)
SEQ_MARKS <- if (THEME == "light") {
  list(colours = c("#009E73", "#024582", "#351E45"), values = c(0, 0.687, 1))
} else {
  list(colours = c("#6F7E20", "#009E73", "#CDD9FF"), values = c(0, 0.21, 1))
}

# Columns: set these to your table's column names
LON       <- "Longitude (°)"   # role: x
LAT       <- "Latitude (°)"    # role: y
SEQUENCE  <- "Waypoint"        # role: order
ELEVATION <- "Elevation (m)"   # role: color

# Data: coastal cycling route south of Monterey, California; replace with your own
# table, for example df <- read.csv("track.csv", check.names = FALSE)
set.seed(42)
n_points <- 240
s <- seq(0, 1, length.out = n_points)
df <- tibble::tibble(
  !!LON       := -121.945 + 0.125 * s + 0.003 * sin(s * 9 * pi) + rnorm(n_points, 0, 0.00006),
  !!LAT       := 36.640 - 0.060 * s + 0.020 * sin(s * 2.4 * pi) + 0.006 * cos(s * 7 * pi) +
                 rnorm(n_points, 0, 0.00006),
  !!SEQUENCE  := seq_len(n_points),
  !!ELEVATION := pmax(2, 8 + 70 * sin(s * 3 * pi)^2 * (0.4 + 0.6 * s) +
                 12 * sin(s * 17 * pi) + rnorm(n_points, 0, 2))
)

# Plot: reads only df and the constants above
# Simplified basemap: a smooth coastline just southwest of the route with land to the
# northeast; replace with real land polygons for your own region
sc <- seq(-0.15, 1.15, length.out = 120)
coast_lon <- -121.945 + 0.125 * sc - 0.009
coast_lat <- 36.640 - 0.060 * sc + 0.020 * sin(sc * 2.4 * pi) - 0.016
land <- data.frame(x = c(coast_lon, rev(coast_lon) + 0.5), y = c(coast_lat, rev(coast_lat) + 0.5))
coast <- data.frame(x = coast_lon, y = coast_lat)
x_pad <- 0.04 * diff(range(df[[LON]]))
y_pad <- 0.06 * diff(range(df[[LAT]]))
ends <- df[c(1, n_points), ]
ends$role <- factor(c("Start", "End"), levels = c("Start", "End"))

# Sparse direction arrows: short segments along the path, pointing in travel direction
arrow_i <- seq(20, n_points - 20, by = 40)
arrows_df <- data.frame(
  x = df[[LON]][arrow_i],     y = df[[LAT]][arrow_i],
  xend = df[[LON]][arrow_i + 1], yend = df[[LAT]][arrow_i + 1]
)

p <- ggplot(df, aes(x = .data[[LON]], y = .data[[LAT]])) +
  geom_polygon(data = land, aes(x = x, y = y), inherit.aes = FALSE,
               fill = LAND, color = NA) +
  geom_path(data = coast, aes(x = x, y = y), inherit.aes = FALSE,
            color = COAST, linewidth = 0.5) +
  geom_path(aes(color = .data[[ELEVATION]]), linewidth = 2.2,
            lineend = "round", linejoin = "round") +
  geom_segment(
    data = arrows_df, aes(x = x, y = y, xend = xend, yend = yend),
    inherit.aes = FALSE, color = INK, linewidth = 0.6,
    arrow = arrow(length = unit(2.6, "mm"), type = "closed", angle = 28)
  ) +
  geom_point(
    data = ends, aes(shape = role, fill = role),
    size = 6.5, color = PAGE_BG, stroke = 1.6
  ) +
  scale_color_gradientn(
    colours = SEQ_MARKS$colours, values = SEQ_MARKS$values,
    guide = guide_colorbar(order = 2, barwidth = 0.6, barheight = 7, title.position = "top")
  ) +
  scale_fill_manual(values = c(Start = IMPRINT_PALETTE[1], End = IMPRINT_PALETTE[5])) +
  scale_shape_manual(values = c(Start = 21, End = 22)) +
  scale_x_continuous(n.breaks = 6) +
  coord_fixed(ratio = 1 / cos(mean(df[[LAT]]) * pi / 180), expand = FALSE,
              xlim = range(df[[LON]]) + c(-x_pad, x_pad),
              ylim = range(df[[LAT]]) + c(-y_pad, y_pad)) +
  guides(fill = guide_legend(order = 1, title = NULL),
         shape = guide_legend(order = 1, title = NULL)) +
  labs(
    title = "Coastal Cycling Route · map-route-path · r · ggplot2 · anyplot.ai",
    x = LON, y = LAT, color = ELEVATION
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = SEA, color = NA),
    panel.border      = element_blank(),
    panel.grid.major  = element_line(color = GRID, linewidth = 0.3),
    panel.grid.minor  = element_blank(),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.5),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = 12),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    legend.key        = element_rect(fill = ELEVATED_BG, color = NA),
    legend.margin     = margin(6, 10, 6, 10),
    legend.box.margin = margin(0, 0, 0, 12),
    plot.margin       = margin(10, 20, 10, 10, unit = "pt")
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
