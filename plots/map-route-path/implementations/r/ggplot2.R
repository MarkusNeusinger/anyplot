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

# Imprint palette: start marker = position 1, end marker = matte red (position 5)
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")
# Imprint sequential ramp for marks (a colored line sits on the page)
SEQ_MARKS <- if (THEME == "light") {
  list(colours = c("#009E73", "#4467A3", "#002850"), values = c(0, 0.338, 1))
} else {
  list(colours = c("#007755", "#009E73", "#CDD9FF"), values = c(0, 0.32, 1))
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
# View fitted to the route extent
x_rng <- range(df[[LON]]); y_rng <- range(df[[LAT]])
x_lim <- x_rng + c(-0.05, 0.05) * diff(x_rng)
y_lim <- y_rng + c(-0.14, 0.06) * diff(y_rng)

# Muted basemap drawn from the route: a coastline running south of the track (sea below,
# land above) and a quiet street grid on the land
smooth_path <- function(v, k = 41) as.numeric(stats::filter(v, rep(1 / k, k), sides = 2))
core <- seq(21, n_points - 20)
shore_x <- smooth_path(df[[LON]])[core] - 0.09 * diff(x_rng)
shore_y <- smooth_path(df[[LAT]])[core] - 0.13 * diff(y_rng) -
  0.02 * diff(y_rng) * sin(seq(0, 5 * pi, length.out = length(core)))
shore_x <- c(x_lim[1] - 0.2 * diff(x_lim), shore_x, x_lim[2] + 0.2 * diff(x_lim))
shore_y <- c(shore_y[1] - 0.12 * diff(y_rng), shore_y, shore_y[length(shore_y)] - 0.12 * diff(y_rng))
sea <- data.frame(x = c(shore_x, rev(range(shore_x))),
                  y = c(shore_y, rep(y_lim[1] - 0.2 * diff(y_lim), 2)))
SEA_FILL <- if (THEME == "light") alpha("#4467A3", 0.20) else alpha("#4467A3", 0.28)
STREET   <- alpha(INK_SOFT, 0.28)
streets_across <- do.call(rbind, lapply(seq(0.08, 0.92, length.out = 9), function(f) {
  data.frame(x = x_lim[1] + f * diff(x_lim) + c(-0.02, 0.03) * diff(x_lim),
             y = c(y_lim[2], y_lim[1]), id = f)
}))
ends <- df[c(1, n_points), ]
ends$role <- factor(c("Start", "End"), levels = c("Start", "End"))

# Sparse direction arrows: short segments along the path, pointing in travel direction
arrow_i <- seq(20, n_points - 20, by = 40)
arrows_df <- data.frame(
  x = df[[LON]][arrow_i],     y = df[[LAT]][arrow_i],
  xend = df[[LON]][arrow_i + 1], yend = df[[LAT]][arrow_i + 1]
)

p <- ggplot(df, aes(x = .data[[LON]], y = .data[[LAT]])) +
  geom_line(data = streets_across, aes(x = x, y = y, group = id), inherit.aes = FALSE,
            color = STREET, linewidth = 0.3) +
  geom_polygon(data = sea, aes(x = x, y = y), inherit.aes = FALSE,
               fill = SEA_FILL, color = NA) +
  geom_path(data = data.frame(x = shore_x, y = shore_y), aes(x = x, y = y),
            inherit.aes = FALSE, color = alpha("#4467A3", 0.55), linewidth = 0.5) +
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
  coord_fixed(ratio = 1 / cos(mean(df[[LAT]]) * pi / 180),
              xlim = x_lim, ylim = y_lim, expand = FALSE) +
  guides(fill = guide_legend(order = 1, title = NULL),
         shape = guide_legend(order = 1, title = NULL)) +
  labs(
    title = "Coastal Cycling Route · map-route-path · r · ggplot2 · anyplot.ai",
    x = LON, y = LAT, color = ELEVATION
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
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
