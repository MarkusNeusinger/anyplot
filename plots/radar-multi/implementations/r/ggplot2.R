#' anyplot.ai
#' radar-multi: Multi-Series Radar Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 82/100 | Created: 2026-08-17

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

IMPRINT_PALETTE <- c(
  "#009E73", # 1 — brand green, always first series
  "#C475FD", # 2 — lavender
  "#4467A3", # 3 — blue
  "#BD8233", # 4 — ochre
  "#AE3030", # 5 — matte red
  "#2ABCCD", # 6 — cyan
  "#954477", # 7 — rose
  "#99B314"  # 8 — lime
)

# coord_polar() munges straight polygon edges into arcs when interpolating
# between vertices; is_linear = TRUE keeps the radar spokes and value rings
# as straight-edged polygons, matching the spec's "closed polygon" per axis.
coord_radar <- function(start = 0, direction = 1) {
  ggproto("CoordRadar", CoordPolar,
    theta = "x", r = "y", start = start, direction = sign(direction),
    is_linear = function(coord) TRUE
  )
}

# --- Data -----------------------------------------------------------------
attributes <- c("Battery Life", "Camera", "Performance", "Display", "Value", "Durability")

radar_df <- tibble::tibble(
  phone = rep(c("Aurora X12", "Nimbus S8", "Ridgeline Pro"), each = length(attributes)),
  attribute = factor(rep(attributes, times = 3), levels = attributes),
  score = c(
    72, 65, 88, 80, 55, 70,   # Aurora X12   — performance-focused flagship
    90, 78, 60, 68, 82, 75,   # Nimbus S8    — battery + value pick
    58, 92, 75, 95, 45, 85    # Ridgeline Pro — camera + display, premium price
  )
)

# Faint alternating ring bands (drawn back-to-front: wide band first, then a
# narrower band painted in the page color to punch out the "gap") give the
# grid a touch of depth beyond the mandated gridlines alone.
ring_hi <- data.frame(attribute = factor(attributes, levels = attributes), score = 80)
ring_lo <- data.frame(attribute = factor(attributes, levels = attributes), score = 60)

# --- Plot -------------------------------------------------------------------
p <- ggplot(radar_df, aes(x = attribute, y = score, group = phone, color = phone, fill = phone)) +
  geom_polygon(data = ring_hi, aes(x = attribute, y = score), inherit.aes = FALSE, fill = INK, alpha = 0.05) +
  geom_polygon(data = ring_lo, aes(x = attribute, y = score), inherit.aes = FALSE, fill = PAGE_BG) +
  geom_polygon(alpha = 0.25, linewidth = 1.0) +
  geom_point(size = 3.2) +
  coord_radar(start = -pi / 2) +
  scale_y_continuous(limits = c(0, 100), breaks = seq(0, 100, 20), expand = expansion(mult = c(0, 0.18))) +
  scale_color_manual(values = IMPRINT_PALETTE) +
  scale_fill_manual(values = IMPRINT_PALETTE) +
  labs(
    title = "radar-multi · r · ggplot2 · anyplot.ai",
    caption = "Each phone leads on a different axis — no single winner across all six attributes",
    x = NULL, y = "Score (0-100)", color = NULL, fill = NULL
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.border       = element_blank(),
    axis.line          = element_blank(),
    axis.ticks         = element_blank(),
    panel.grid.major   = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor   = element_blank(),
    axis.text.x        = element_text(color = INK, size = 10),
    axis.text.y        = element_text(color = INK_SOFT, size = 8),
    axis.title.y       = element_text(color = INK_SOFT, size = 7, hjust = 0.85, margin = margin(r = 4)),
    plot.title         = element_text(color = INK, size = 12, face = "bold", hjust = 0.5),
    plot.caption       = element_text(color = INK_SOFT, size = 7, hjust = 0.5, margin = margin(t = 8)),
    legend.position    = "bottom",
    legend.background  = element_rect(fill = ELEVATED_BG, color = INK_SOFT),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_blank()
  ) +
  guides(fill = guide_legend(override.aes = list(alpha = 0.5)))

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
