#' anyplot.ai
#' scatter-3d: 3D Scatter Plot
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-09-10

library(ggplot2)
library(dplyr)
library(tibble)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME            <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG          <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK              <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT         <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_SEQ_LOW  <- "#009E73"
IMPRINT_SEQ_HIGH <- "#4467A3"

# --- Data: CT-scanned porosity defects inside a 3D-printed titanium bracket -
# Three weak layer-adhesion zones plus scattered background porosity, in
# build-plate coordinates (mm). Defect size (micrometers) is the 4th variable.
n_zone      <- 55
zone_x      <- c(-9, 7, 1)
zone_y      <- c(6, -7, 9)
zone_z      <- c(5, 7, -6)
zone_spread <- c(2.6, 3.1, 2.3)

x <- c(
  rnorm(n_zone, zone_x[1], zone_spread[1]),
  rnorm(n_zone, zone_x[2], zone_spread[2]),
  rnorm(n_zone, zone_x[3], zone_spread[3]),
  runif(20, -15, 15)
)
y <- c(
  rnorm(n_zone, zone_y[1], zone_spread[1]),
  rnorm(n_zone, zone_y[2], zone_spread[2]),
  rnorm(n_zone, zone_y[3], zone_spread[3]),
  runif(20, -15, 15)
)
z <- c(
  rnorm(n_zone, zone_z[1], zone_spread[1]),
  rnorm(n_zone, zone_z[2], zone_spread[2]),
  rnorm(n_zone, zone_z[3], zone_spread[3]),
  runif(20, -15, 15)
)
defect_size_um <- c(
  rgamma(n_zone, shape = 6, scale = 8) + 15,
  rgamma(n_zone, shape = 5, scale = 7) + 15,
  rgamma(n_zone, shape = 7, scale = 6) + 15,
  rgamma(20, shape = 2, scale = 6) + 10
)

# --- Orthographic projection (azimuth 35°, elevation 20°) --------------------
# ggplot2 has no native 3D geom, so the third axis is folded into 2D screen
# space via a standard rotate-then-project transform (the same math a 3D
# chart library applies internally), rendered with geom_point/geom_segment.
az <- 35 * pi / 180
el <- 20 * pi / 180

x_rot  <- x * cos(az) + y * sin(az)
y_rot  <- -x * sin(az) + y * cos(az)
z_rot  <- z
depth  <- y_rot * sin(el) + z_rot * cos(el) # larger = closer to viewer
y_tilt <- y_rot * cos(el) - z_rot * sin(el)

points_df <- tibble(
  proj_x         = x_rot,
  proj_y         = y_tilt,
  depth          = depth,
  defect_size_um = defect_size_um
) %>%
  mutate(
    depth_norm  = rescale(depth, to = c(0, 1)),
    point_size  = 2.2 + depth_norm * 3.3,
    point_alpha = 0.45 + depth_norm * 0.5
  ) %>%
  arrange(depth)

# --- Bounding-box wireframe (static 3D reference frame) ----------------------
pad <- 1.15
xr  <- range(x) * pad
yr  <- range(y) * pad
zr  <- range(z) * pad

corners        <- expand.grid(cx = xr, cy = yr, cz = zr)
corners_x_rot  <- corners$cx * cos(az) + corners$cy * sin(az)
corners_y_rot  <- -corners$cx * sin(az) + corners$cy * cos(az)
corners_z_rot  <- corners$cz
corners$proj_x <- corners_x_rot
corners$proj_y <- corners_y_rot * cos(el) - corners_z_rot * sin(el)

edge_from <- c(1, 3, 5, 7, 1, 2, 5, 6, 1, 2, 3, 4)
edge_to   <- c(2, 4, 6, 8, 3, 4, 7, 8, 5, 6, 7, 8)
edges_df <- tibble(
  x    = corners$proj_x[edge_from],
  y    = corners$proj_y[edge_from],
  xend = corners$proj_x[edge_to],
  yend = corners$proj_y[edge_to]
)

# --- Axis labels, extended past the box tips along their own direction -------
tip_idx  <- c(2, 3, 5) # X, Y, Z edges all start at corner 1
dir_x    <- corners$proj_x[tip_idx] - corners$proj_x[1]
dir_y    <- corners$proj_y[tip_idx] - corners$proj_y[1]
dir_len  <- sqrt(dir_x^2 + dir_y^2)
label_gap <- 1.8

axis_labels <- tibble(
  label = c("X (mm)", "Y (mm)", "Z (mm)"),
  x     = corners$proj_x[tip_idx] + dir_x / dir_len * label_gap,
  y     = corners$proj_y[tip_idx] + dir_y / dir_len * label_gap
)

# --- Plot ---------------------------------------------------------------------
p <- ggplot() +
  geom_segment(
    data = edges_df,
    aes(x = x, y = y, xend = xend, yend = yend),
    color = INK_SOFT, linewidth = 0.35, alpha = 0.5
  ) +
  geom_point(
    data = points_df,
    aes(x = proj_x, y = proj_y, color = defect_size_um,
        size = point_size, alpha = point_alpha)
  ) +
  geom_text(
    data = axis_labels,
    aes(x = x, y = y, label = label),
    color = INK_SOFT, size = 3.2, fontface = "bold"
  ) +
  scale_color_gradient(low = IMPRINT_SEQ_LOW, high = IMPRINT_SEQ_HIGH,
                        name = "Defect size (µm)") +
  scale_size_identity() +
  scale_alpha_identity() +
  coord_fixed(ratio = 1, clip = "off") +
  labs(
    title   = "scatter-3d · r · ggplot2 · anyplot.ai",
    caption = "CT-scanned porosity defects in a 3D-printed titanium bracket · build-plate coordinates, ±15 mm per axis"
  ) +
  theme_void(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    plot.title        = element_text(color = INK, size = 12, hjust = 0.5,
                                      margin = margin(b = 10)),
    plot.caption      = element_text(color = INK_SOFT, size = 8, hjust = 0.5,
                                      margin = margin(t = 10)),
    legend.title      = element_text(color = INK, size = 10),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.position   = "right",
    plot.margin       = margin(15, 25, 15, 15)
  )

# --- Save (PNG, both themes) ---------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
