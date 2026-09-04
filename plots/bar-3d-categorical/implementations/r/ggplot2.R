#' anyplot.ai
#' bar-3d-categorical: 3D Bar Chart for Categorical Comparison
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 90/100 | Created: 2026-09-04

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette — 8 hues, theme-independent, hybrid-v3 sort
IMPRINT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# --- Data: crop yield across fertilizer x soil type (factorial design, 4 x 5 = 20 bars) ---
fertilizer_types <- c("Organic", "Nitrogen", "Phosphate", "Compound")
soil_types <- c("Clay", "Loam", "Sandy", "Silt", "Peat")

fertilizer_baseline <- c(Organic = 4.2, Nitrogen = 6.8, Phosphate = 5.5, Compound = 7.4)
soil_modifier <- c(Clay = -0.3, Loam = 0.6, Sandy = -0.8, Silt = 0.2, Peat = 0.1)

trial <- expand.grid(
  fertilizer = fertilizer_types,
  soil = soil_types,
  stringsAsFactors = FALSE
) |>
  mutate(
    fertilizer = factor(fertilizer, levels = fertilizer_types),
    soil = factor(soil, levels = soil_types),
    i = as.integer(fertilizer) - 1L,
    j = as.integer(soil) - 1L,
    yield = fertilizer_baseline[as.character(fertilizer)] +
      soil_modifier[as.character(soil)] +
      rnorm(n(), mean = 0, sd = 0.25)
  )

# --- Isometric projection: rotate by azimuth, tilt by elevation, drop depth ----
# See specification.md "Notes": elevation ~30 deg, azimuth ~45 deg.
AZIMUTH   <- 45 * pi / 180
ELEVATION <- 30 * pi / 180

project_iso <- function(gx, gy, gz) {
  rx <- gx * cos(AZIMUTH) - gy * sin(AZIMUTH)
  ry <- gx * sin(AZIMUTH) + gy * cos(AZIMUTH)
  screen_x <- rx
  screen_y <- ry * sin(ELEVATION) + gz * cos(ELEVATION)
  list(x = screen_x, y = screen_y)
}

shade <- function(hex, amount) {
  channel <- col2rgb(hex) / 255
  if (amount >= 0) {
    channel <- channel + (1 - channel) * amount
  } else {
    channel <- channel * (1 + amount)
  }
  rgb(channel[1], channel[2], channel[3])
}

# --- Bar geometry: footprint with spacing, height scaled to a comfortable range ---
CELL <- 1.0
BAR_W <- 0.62
BAR_D <- 0.62
MARGIN <- (CELL - BAR_W) / 2
HEIGHT_SCALE <- 3.2 / max(trial$yield)
fert_colors <- setNames(IMPRINT_PALETTE[seq_along(fertilizer_types)], fertilizer_types)

# Painter's algorithm: draw far bars first so nearer bars occlude them correctly
trial <- trial |> arrange(desc(i + j))

faces <- vector("list", nrow(trial) * 12)
labels_rows <- vector("list", nrow(trial))
slot <- 0
for (row in seq_len(nrow(trial))) {
  bar <- trial[row, ]
  x0 <- bar$i + MARGIN
  x1 <- bar$i + MARGIN + BAR_W
  y0 <- bar$j + MARGIN
  y1 <- bar$j + MARGIN + BAR_D
  h <- bar$yield * HEIGHT_SCALE
  base_hex <- fert_colors[[as.character(bar$fertilizer)]]
  poly_id_base <- row * 3

  top_corners <- list(c(x0, y0, h), c(x1, y0, h), c(x1, y1, h), c(x0, y1, h))
  left_corners <- list(c(x0, y0, 0), c(x0, y1, 0), c(x0, y1, h), c(x0, y0, h))
  right_corners <- list(c(x0, y0, 0), c(x1, y0, 0), c(x1, y0, h), c(x0, y0, h))

  face_specs <- list(
    list(corners = top_corners, fill_hex = shade(base_hex, 0.35), poly_id = poly_id_base),
    list(corners = left_corners, fill_hex = shade(base_hex, -0.10), poly_id = poly_id_base + 1),
    list(corners = right_corners, fill_hex = shade(base_hex, -0.35), poly_id = poly_id_base + 2)
  )
  for (face in face_specs) {
    for (order in seq_along(face$corners)) {
      corner <- face$corners[[order]]
      screen <- project_iso(corner[1], corner[2], corner[3])
      slot <- slot + 1
      faces[[slot]] <- data.frame(
        poly_id = face$poly_id, order = order,
        px = screen$x, py = screen$y, fill_hex = face$fill_hex
      )
    }
  }

  top_center <- project_iso((x0 + x1) / 2, (y0 + y1) / 2, h)
  labels_rows[[row]] <- data.frame(px = top_center$x, py = top_center$y + 0.18, label = sprintf("%.1f", bar$yield))
}
faces_df <- bind_rows(faces)
labels_df <- bind_rows(labels_rows)

# Isometric views can put two different grid cells on the same screen column
# (cells sharing fertilizer_index - soil_index land on one diagonal); when their
# heights are close, the value labels collide. Nudge later labels (bottom-to-top)
# apart from earlier ones sharing a column so every value stays legible.
MIN_LABEL_GAP <- 0.34
label_order <- order(labels_df$py)
for (k in seq_along(label_order)[-1]) {
  cur <- label_order[k]
  for (prev in label_order[seq_len(k - 1)]) {
    if (abs(labels_df$px[cur] - labels_df$px[prev]) < 0.45) {
      gap <- labels_df$py[cur] - labels_df$py[prev]
      if (gap < MIN_LABEL_GAP) {
        labels_df$py[cur] <- labels_df$py[prev] + MIN_LABEL_GAP
      }
    }
  }
}

# --- Base-plane grid lines (relate bars to their categorical position) --------
n_fert <- length(fertilizer_types)
n_soil <- length(soil_types)
grid_lines <- vector("list", (n_fert + 1) + (n_soil + 1))
slot <- 0
for (i in 0:n_fert) {
  a <- project_iso(i, 0, 0)
  b <- project_iso(i, n_soil, 0)
  slot <- slot + 1
  grid_lines[[slot]] <- data.frame(line_id = slot, px = c(a$x, b$x), py = c(a$y, b$y))
}
for (j in 0:n_soil) {
  a <- project_iso(0, j, 0)
  b <- project_iso(n_fert, j, 0)
  slot <- slot + 1
  grid_lines[[slot]] <- data.frame(line_id = slot, px = c(a$x, b$x), py = c(a$y, b$y))
}
grid_df <- bind_rows(grid_lines)

# --- Category tick labels along the two front edges ---------------------------
fert_ticks <- bind_rows(lapply(seq_along(fertilizer_types) - 1L, function(i) {
  p <- project_iso(i + 0.5, -0.45, 0)
  data.frame(px = p$x, py = p$y, label = fertilizer_types[i + 1])
}))
soil_ticks <- bind_rows(lapply(seq_along(soil_types) - 1L, function(j) {
  p <- project_iso(-0.35, j + 0.5, 0)
  data.frame(px = p$x, py = p$y, label = soil_types[j + 1])
}))
fert_axis_label <- project_iso(n_fert / 2, -0.9, 0)
soil_axis_label <- project_iso(-0.9, n_soil / 2, 0)

# --- Theme-adaptive chrome — bespoke isometric canvas (no meaningful cartesian axes) ---
anyplot_theme <- theme_void(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    legend.background  = element_rect(fill = ELEVATED_BG, color = INK_SOFT),
    legend.margin      = margin(t = 6, r = 12, b = 6, l = 8),
    legend.text        = element_text(color = INK_SOFT, size = 7.5, margin = margin(r = 6)),
    legend.title       = element_text(color = INK, size = 10),
    plot.title         = element_text(color = INK, size = 12, face = "bold", hjust = 0.5),
    plot.caption       = element_text(color = INK_SOFT, size = 7, hjust = 0.5),
    legend.position    = "right"
  )

p <- ggplot() +
  geom_path(data = grid_df, aes(x = px, y = py, group = line_id), color = INK_SOFT, alpha = 0.2, linewidth = 0.4) +
  geom_polygon(
    data = faces_df, aes(x = px, y = py, group = poly_id, fill = fill_hex),
    color = PAGE_BG, linewidth = 0.3, show.legend = FALSE
  ) +
  geom_point(
    data = data.frame(fertilizer = factor(fertilizer_types, levels = fertilizer_types)),
    aes(x = 0, y = 0, color = fertilizer), alpha = 0
  ) +
  geom_text(data = labels_df, aes(x = px, y = py, label = label), color = INK, size = 2.5, fontface = "bold") +
  geom_text(data = fert_ticks, aes(x = px, y = py, label = label), color = INK_SOFT, size = 2.3, angle = 30) +
  geom_text(data = soil_ticks, aes(x = px, y = py, label = label), color = INK_SOFT, size = 2.7, angle = -30) +
  annotate("text", x = fert_axis_label$x, y = fert_axis_label$y, label = "Fertilizer", color = INK, size = 3.0, angle = 30, fontface = "italic") +
  annotate("text", x = soil_axis_label$x, y = soil_axis_label$y, label = "Soil Type", color = INK, size = 3.0, angle = -30, fontface = "italic") +
  scale_fill_identity() +
  scale_color_manual(values = fert_colors, name = "Fertilizer", guide = guide_legend(override.aes = list(alpha = 1, size = 5, shape = 15))) +
  coord_fixed(ratio = 1) +
  labs(
    title = "bar-3d-categorical · r · ggplot2 · anyplot.ai",
    caption = "Bar height = Crop yield (tons/hectare)"
  ) +
  anyplot_theme

ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
