#' anyplot.ai
#' map-route-path: Route Path Map
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-05-21

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
OKABE_ITO   <- c("#009E73", "#D55E00", "#0072B2", "#CC79A7",
                 "#E69F00", "#56B4E9", "#F0E442")

# Data: Synthetic GPS track for a mountain trail in Colorado Rockies
n_points <- 200
t        <- seq(0, 2 * pi, length.out = n_points)

lon <- -105.6500 +
  0.085 * (t / (2 * pi)) +
  0.011 * sin(t * 2.5) +
  rnorm(n_points, 0, 0.0005)

lat <- 40.4100 +
  0.018 * sin(t * 1.1) +
  0.007 * cos(t * 3.5) +
  rnorm(n_points, 0, 0.0005)

# Elevation: classic ascent-peak-descent profile with realistic GPS noise
elevation <- 3100 +
  600 * sin(seq(0, pi, length.out = n_points)) +
  85  * sin(seq(0, 8 * pi, length.out = n_points)) +
  rnorm(n_points, 0, 22)

df <- tibble::tibble(
  lon       = lon,
  lat       = lat,
  sequence  = seq_len(n_points),
  elevation = elevation
)

# Endpoint markers (start = circle, end = square)
endpoints <- tibble::tibble(
  lon  = c(df$lon[1], df$lon[n_points]),
  lat  = c(df$lat[1], df$lat[n_points]),
  role = factor(c("Start", "End"), levels = c("Start", "End"))
)

# Plot
p <- ggplot(df, aes(x = lon, y = lat)) +
  geom_path(
    aes(color = elevation),
    linewidth = 2.0,
    lineend   = "round",
    linejoin  = "round"
  ) +
  geom_point(
    data   = endpoints,
    aes(shape = role, fill = role),
    size   = 6.5,
    color  = PAGE_BG,
    stroke = 1.8
  ) +
  scale_color_viridis_c(
    option = "viridis",
    name   = "Elevation (m)",
    guide  = guide_colorbar(
      barwidth       = 0.6,
      barheight      = 7,
      title.position = "top"
    )
  ) +
  scale_fill_manual(
    values = c("Start" = OKABE_ITO[1], "End" = OKABE_ITO[2]),
    name   = NULL
  ) +
  scale_shape_manual(
    values = c("Start" = 21, "End" = 22),
    name   = NULL
  ) +
  coord_fixed(ratio = 1.31) +
  labs(
    title = "Rocky Mountain Trail · map-route-path · r · ggplot2 · anyplot.ai",
    x     = "Longitude",
    y     = "Latitude"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill  = PAGE_BG,     color = PAGE_BG),
    panel.background  = element_rect(fill  = PAGE_BG,     color = NA),
    panel.border      = element_rect(color = INK_SOFT,    fill  = NA,   linewidth = 0.5),
    panel.grid.major  = element_line(color = INK_SOFT,    linewidth = 0.15),
    panel.grid.minor  = element_blank(),
    axis.line         = element_blank(),
    axis.title        = element_text(color = INK,         size  = 10),
    axis.text         = element_text(color = INK_SOFT,    size  = 8),
    plot.title        = element_text(color = INK,         size  = 12),
    legend.background = element_rect(fill  = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT,    size  = 8),
    legend.title      = element_text(color = INK,         size  = 10),
    legend.key        = element_rect(fill  = PAGE_BG,     color = NA),
    legend.margin     = margin(5, 8, 5, 8),
    plot.margin       = margin(10, 15, 10, 10, unit = "pt")
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
