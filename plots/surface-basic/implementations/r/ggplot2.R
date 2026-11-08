#' anyplot.ai
#' surface-basic: Basic 3D Surface Plot
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: pending | Updated: 2026-11-08
# anyplot.ai
# surface-basic: Basic 3D Surface Plot
# Library: ggplot2 | R
#
# ggplot2 has no native 3D device (no wireframe/surface geom), so the surface
# is rendered as a hand-projected mesh: rotate the (x, y, z) grid by a fixed
# elevation/azimuth, project it onto the 2D canvas, then draw one
# depth-sorted geom_polygon quad per grid cell (a painter's-algorithm mesh).
# The screen-coordinate axes carry no data meaning, so they are hidden and a
# projected 3D axis box with x, y and z ticks in data units is drawn instead.
# Height is encoded twice — via the visual elevation of each quad and via its
# fill color — for redundant, colorblind-safe readability.

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# --- Data: bimodal Gaussian response surface ----------------------------------
# z = f(x, y) over a 45x45 grid, e.g. a yield surface from two process
# settings — one dominant optimum plus a smaller secondary optimum.
n <- 45
x_vals <- seq(-4, 4, length.out = n)
y_vals <- seq(-4, 4, length.out = n)

X <- outer(y_vals, x_vals, function(y, x) x)
Y <- outer(y_vals, x_vals, function(y, x) y)
Z <- exp(-((X - 1.5)^2 + (Y - 1.5)^2) / 4) +
  0.6 * exp(-((X + 2)^2 + (Y + 2)^2) / 3)

# --- 3D -> 2D isometric projection ---------------------------------------------
elev <- 30 * pi / 180
azim <- -35 * pi / 180
z_scale <- 3 # visually amplify height relative to the x/y spatial extent

# Screen coordinates of data points (x, y, z); used for the mesh and the axis box
project <- function(x, y, z) {
  depth <- x * sin(azim) + y * cos(azim)
  list(
    px = x * cos(azim) - y * sin(azim),
    py = depth * sin(elev) + z * z_scale * cos(elev),
    depth = depth
  )
}

P <- project(X, Y, Z)
X_proj <- P$px
Y_proj <- P$py
Y_rot <- P$depth

# One quad per grid cell: its 4 projected corners, mean height (fill) and
# mean depth (paint order — farthest cells first so nearer ones draw on top).
quads <- vector("list", (n - 1) * (n - 1))
k <- 1
for (i in 1:(n - 1)) {
  for (j in 1:(n - 1)) {
    quads[[k]] <- list(
      x = c(X_proj[i, j], X_proj[i, j + 1], X_proj[i + 1, j + 1], X_proj[i + 1, j]),
      y = c(Y_proj[i, j], Y_proj[i, j + 1], Y_proj[i + 1, j + 1], Y_proj[i + 1, j]),
      z = mean(c(Z[i, j], Z[i, j + 1], Z[i + 1, j + 1], Z[i + 1, j])),
      depth = mean(c(Y_rot[i, j], Y_rot[i, j + 1], Y_rot[i + 1, j + 1], Y_rot[i + 1, j]))
    )
    k <- k + 1
  }
}
quads <- quads[order(-vapply(quads, function(q) q$depth, numeric(1)))]

mesh_df <- bind_rows(lapply(seq_along(quads), function(g) {
  q <- quads[[g]]
  tibble::tibble(x = q$x, y = q$y, z = q$z, group = g)
}))

# --- 3D axis box ----------------------------------------------------------------
# Viewed from this azimuth, the corner (x_min, y_max) is farthest away: the two
# walls meeting there and the floor sit behind the surface, while the x axis
# (front-left floor edge y = y_min), the y axis (front-right floor edge
# x = x_max) and the z axis (left corner x_min, y_min) are drawn in front.
x_lo <- min(x_vals); x_hi <- max(x_vals)
y_lo <- min(y_vals); y_hi <- max(y_vals)
x_ticks <- pretty(x_vals)
y_ticks <- pretty(y_vals)
z_ticks <- pretty(c(0, max(Z)), n = 4)
z_lo <- min(z_ticks); z_hi <- max(z_ticks)
tick_len <- 0.06 * (x_hi - x_lo)
# Floor direction that points straight left on screen, for the z ticks
left_x <- -cos(azim)
left_y <- sin(azim)

seg3d <- function(x, y, z, xend, yend, zend) {
  a <- project(x, y, z)
  b <- project(xend, yend, zend)
  tibble::tibble(x = a$px, y = a$py, xend = b$px, yend = b$py)
}

# Pane grid on the floor and the two back walls, at the tick values
pane_grid <- bind_rows(
  seg3d(x_ticks, y_lo, z_lo, x_ticks, y_hi, z_lo),           # floor, along y
  seg3d(x_lo, y_ticks, z_lo, x_hi, y_ticks, z_lo),           # floor, along x
  seg3d(x_ticks, y_hi, z_lo, x_ticks, y_hi, z_hi),           # back wall y = y_max
  seg3d(x_lo, y_ticks, z_lo, x_lo, y_ticks, z_hi),           # back wall x = x_min
  seg3d(x_lo, y_hi, z_ticks, x_hi, y_hi, z_ticks),           # z levels on y = y_max
  seg3d(x_lo, y_lo, z_ticks, x_lo, y_hi, z_ticks)            # z levels on x = x_min
)

# Outer edges of the back panes
pane_edges <- bind_rows(
  seg3d(x_lo, y_hi, z_lo, x_hi, y_hi, z_lo),
  seg3d(x_lo, y_lo, z_lo, x_lo, y_hi, z_lo),
  seg3d(x_lo, y_hi, z_lo, x_lo, y_hi, z_hi),
  seg3d(x_hi, y_hi, z_lo, x_hi, y_hi, z_hi),
  seg3d(x_lo, y_hi, z_hi, x_hi, y_hi, z_hi),
  seg3d(x_lo, y_lo, z_hi, x_lo, y_hi, z_hi)
)

# Front axis lines and their outward ticks
axis_lines <- bind_rows(
  seg3d(x_lo, y_lo, z_lo, x_hi, y_lo, z_lo),                 # x axis
  seg3d(x_hi, y_lo, z_lo, x_hi, y_hi, z_lo),                 # y axis
  seg3d(x_lo, y_lo, z_lo, x_lo, y_lo, z_hi)                  # z axis
)
axis_ticks <- bind_rows(
  seg3d(x_ticks, y_lo, z_lo, x_ticks, y_lo - tick_len, z_lo),
  seg3d(x_hi, y_ticks, z_lo, x_hi + tick_len, y_ticks, z_lo),
  seg3d(x_lo, y_lo, z_ticks, x_lo + left_x * tick_len, y_lo + left_y * tick_len, z_ticks)
)

x_lab <- project(x_ticks, y_lo - 2.6 * tick_len, z_lo)
y_lab <- project(x_hi + 2.6 * tick_len, y_ticks, z_lo)
z_lab <- project(x_lo + left_x * 1.6 * tick_len, y_lo + left_y * 1.6 * tick_len, z_ticks)
tick_labels <- bind_rows(
  tibble::tibble(x = x_lab$px, y = x_lab$py, label = as.character(x_ticks), hjust = 0.5),
  tibble::tibble(x = y_lab$px, y = y_lab$py, label = as.character(y_ticks), hjust = 0.5),
  tibble::tibble(x = z_lab$px, y = z_lab$py, label = formatC(z_ticks, format = "f", digits = 1), hjust = 1)
)

# Axis titles sit beyond the tick labels, rotated along their edge on screen
x_dir <- project(c(x_lo, x_hi), y_lo, z_lo)
y_dir <- project(x_hi, c(y_lo, y_hi), z_lo)
x_title <- project(mean(c(x_lo, x_hi)), y_lo - 5.2 * tick_len, z_lo)
y_title <- project(x_hi + 5.2 * tick_len, mean(c(y_lo, y_hi)), z_lo)
z_title <- project(x_lo + left_x * 4.6 * tick_len, y_lo + left_y * 4.6 * tick_len, mean(c(z_lo, z_hi)))
axis_titles <- tibble::tibble(
  x = c(x_title$px, y_title$px, z_title$px),
  y = c(x_title$py, y_title$py, z_title$py),
  label = c("X", "Y", "Z (height)"),
  angle = c(
    atan2(diff(x_dir$py), diff(x_dir$px)) * 180 / pi,
    atan2(diff(y_dir$py), diff(y_dir$px)) * 180 / pi,
    90
  )
)

# --- Plot ----------------------------------------------------------------------
p <- ggplot() +
  geom_segment(data = pane_grid, aes(x = x, y = y, xend = xend, yend = yend),
               color = adjustcolor(INK, alpha.f = 0.15), linewidth = 0.2) +
  geom_segment(data = pane_edges, aes(x = x, y = y, xend = xend, yend = yend),
               color = adjustcolor(INK_SOFT, alpha.f = 0.6), linewidth = 0.25) +
  geom_polygon(data = mesh_df, aes(x = x, y = y, group = group, fill = z),
               color = adjustcolor(INK_SOFT, alpha.f = 0.45), linewidth = 0.07, alpha = 0.95) +
  geom_segment(data = axis_lines, aes(x = x, y = y, xend = xend, yend = yend),
               color = INK_SOFT, linewidth = 0.35) +
  geom_segment(data = axis_ticks, aes(x = x, y = y, xend = xend, yend = yend),
               color = INK_SOFT, linewidth = 0.3) +
  geom_text(data = tick_labels, aes(x = x, y = y, label = label, hjust = hjust),
            color = INK_SOFT, size = 2.8, vjust = 0.5) +
  geom_text(data = axis_titles, aes(x = x, y = y, label = label, angle = angle),
            color = INK, size = 3.5) +
  scale_fill_gradient(low = "#009E73", high = "#4467A3", name = "Height (z)",
                      limits = c(z_lo, z_hi), breaks = z_ticks) +
  coord_fixed(clip = "off") +
  labs(
    title = "surface-basic · r · ggplot2 · anyplot.ai",
    subtitle = "Isometric projection · elevation 30° · azimuth -35°"
  ) +
  theme_void(base_size = 8) +
  theme(
    plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    plot.margin = margin(12, 12, 12, 12),
    plot.title = element_text(color = INK, size = 12, margin = margin(b = 4)),
    plot.subtitle = element_text(color = INK_SOFT, size = 8, margin = margin(b = 6)),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.margin = margin(6, 6, 6, 6),
    legend.text = element_text(color = INK_SOFT, size = 8),
    legend.title = element_text(color = INK, size = 10)
  )

# --- Save -----------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot = p,
  device = ragg::agg_png,
  width = 8,
  height = 4.5,
  units = "in",
  dpi = 400
)
