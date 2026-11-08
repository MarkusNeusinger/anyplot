#' anyplot.ai
#' surface-basic: Basic 3D Surface Plot
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 83/100 | Updated: 2026-11-08
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

# Screen coordinates: px = x cos(a) - y sin(a), depth = x sin(a) + y cos(a),
# py = depth sin(e) + z z_scale cos(e); used for the mesh and the axis box
X_proj <- X * cos(azim) - Y * sin(azim)
Y_rot <- X * sin(azim) + Y * cos(azim)
Y_proj <- Y_rot * sin(elev) + Z * z_scale * cos(elev)

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

# Every box segment in data units (start x0/y0/z0, end x1/y1/z1), tagged by
# the layer it is drawn in; projected to the screen once, below.
box_3d <- bind_rows(
  # Pane grid on the floor and the two back walls, at the tick values
  tibble::tibble(layer = "grid", x0 = x_ticks, y0 = y_lo, z0 = z_lo, x1 = x_ticks, y1 = y_hi, z1 = z_lo),
  tibble::tibble(layer = "grid", x0 = x_lo, y0 = y_ticks, z0 = z_lo, x1 = x_hi, y1 = y_ticks, z1 = z_lo),
  tibble::tibble(layer = "grid", x0 = x_ticks, y0 = y_hi, z0 = z_lo, x1 = x_ticks, y1 = y_hi, z1 = z_hi),
  tibble::tibble(layer = "grid", x0 = x_lo, y0 = y_ticks, z0 = z_lo, x1 = x_lo, y1 = y_ticks, z1 = z_hi),
  tibble::tibble(layer = "grid", x0 = x_lo, y0 = y_hi, z0 = z_ticks, x1 = x_hi, y1 = y_hi, z1 = z_ticks),
  tibble::tibble(layer = "grid", x0 = x_lo, y0 = y_lo, z0 = z_ticks, x1 = x_lo, y1 = y_hi, z1 = z_ticks),
  # Outer edges of the back panes
  tibble::tibble(
    layer = "edge",
    x0 = c(x_lo, x_lo, x_lo, x_hi, x_lo, x_lo), y0 = c(y_hi, y_lo, y_hi, y_hi, y_hi, y_lo),
    z0 = c(z_lo, z_lo, z_lo, z_lo, z_hi, z_hi), x1 = c(x_hi, x_lo, x_lo, x_hi, x_hi, x_lo),
    y1 = y_hi, z1 = c(z_lo, z_lo, z_hi, z_hi, z_hi, z_hi)
  ),
  # Front x, y and z axis lines
  tibble::tibble(
    layer = "axis",
    x0 = c(x_lo, x_hi, x_lo), y0 = y_lo, z0 = z_lo,
    x1 = c(x_hi, x_hi, x_lo), y1 = c(y_lo, y_hi, y_lo), z1 = c(z_lo, z_lo, z_hi)
  ),
  # Outward ticks on the three axes
  tibble::tibble(layer = "tick", x0 = x_ticks, y0 = y_lo, z0 = z_lo, x1 = x_ticks, y1 = y_lo - tick_len, z1 = z_lo),
  tibble::tibble(layer = "tick", x0 = x_hi, y0 = y_ticks, z0 = z_lo, x1 = x_hi + tick_len, y1 = y_ticks, z1 = z_lo),
  tibble::tibble(
    layer = "tick", x0 = x_lo, y0 = y_lo, z0 = z_ticks,
    x1 = x_lo + left_x * tick_len, y1 = y_lo + left_y * tick_len, z1 = z_ticks
  )
)
box_df <- box_3d |>
  mutate(
    x = x0 * cos(azim) - y0 * sin(azim),
    y = (x0 * sin(azim) + y0 * cos(azim)) * sin(elev) + z0 * z_scale * cos(elev),
    xend = x1 * cos(azim) - y1 * sin(azim),
    yend = (x1 * sin(azim) + y1 * cos(azim)) * sin(elev) + z1 * z_scale * cos(elev)
  )

# Tick labels and axis titles in data units, projected the same way. Titles
# sit beyond the tick labels, rotated along their edge on screen: a step along
# x moves (cos a, sin a sin e) on screen, a step along y (-sin a, cos a sin e).
text_df <- bind_rows(
  tibble::tibble(
    kind = "tick", x0 = x_ticks, y0 = y_lo - 2.6 * tick_len, z0 = z_lo,
    label = as.character(x_ticks), hjust = 0.5, angle = 0
  ),
  tibble::tibble(
    kind = "tick", x0 = x_hi + 2.6 * tick_len, y0 = y_ticks, z0 = z_lo,
    label = as.character(y_ticks), hjust = 0.5, angle = 0
  ),
  tibble::tibble(
    kind = "tick", x0 = x_lo + left_x * 1.6 * tick_len, y0 = y_lo + left_y * 1.6 * tick_len, z0 = z_ticks,
    label = formatC(z_ticks, format = "f", digits = 1), hjust = 1, angle = 0
  ),
  tibble::tibble(
    kind = "title",
    x0 = c(mean(c(x_lo, x_hi)), x_hi + 5.2 * tick_len, x_lo + left_x * 4.6 * tick_len),
    y0 = c(y_lo - 5.2 * tick_len, mean(c(y_lo, y_hi)), y_lo + left_y * 4.6 * tick_len),
    z0 = c(z_lo, z_lo, mean(c(z_lo, z_hi))),
    label = c("X", "Y", "Z (height)"), hjust = 0.5,
    angle = c(
      atan2(sin(azim) * sin(elev), cos(azim)) * 180 / pi,
      atan2(cos(azim) * sin(elev), -sin(azim)) * 180 / pi,
      90
    )
  )
) |>
  mutate(
    x = x0 * cos(azim) - y0 * sin(azim),
    y = (x0 * sin(azim) + y0 * cos(azim)) * sin(elev) + z0 * z_scale * cos(elev)
  )

# --- Plot ----------------------------------------------------------------------
p <- ggplot() +
  geom_segment(data = filter(box_df, layer == "grid"), aes(x = x, y = y, xend = xend, yend = yend),
               color = adjustcolor(INK, alpha.f = 0.15), linewidth = 0.2) +
  geom_segment(data = filter(box_df, layer == "edge"), aes(x = x, y = y, xend = xend, yend = yend),
               color = adjustcolor(INK_SOFT, alpha.f = 0.6), linewidth = 0.25) +
  geom_polygon(data = mesh_df, aes(x = x, y = y, group = group, fill = z),
               color = adjustcolor(INK_SOFT, alpha.f = 0.45), linewidth = 0.07, alpha = 0.95) +
  geom_segment(data = filter(box_df, layer == "axis"), aes(x = x, y = y, xend = xend, yend = yend),
               color = INK_SOFT, linewidth = 0.35) +
  geom_segment(data = filter(box_df, layer == "tick"), aes(x = x, y = y, xend = xend, yend = yend),
               color = INK_SOFT, linewidth = 0.3) +
  geom_text(data = filter(text_df, kind == "tick"), aes(x = x, y = y, label = label, hjust = hjust),
            color = INK_SOFT, size = 2.8, vjust = 0.5) +
  geom_text(data = filter(text_df, kind == "title"), aes(x = x, y = y, label = label, angle = angle),
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
