#' anyplot.ai
#' radar-multi: Multi-Series Radar Chart
#' Library: ggplot2 3.5 | R 4.4
#' Quality: pending | Created: 2026-08-17

library(ggplot2)
library(dplyr)
library(tidyr)
library(scales)
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

# --- Plot -------------------------------------------------------------------
p <- ggplot(radar_df, aes(x = attribute, y = score, group = phone, color = phone, fill = phone)) +
  geom_polygon(alpha = 0.25, linewidth = 1.0) +
  geom_point(size = 2.5) +
  coord_radar(start = -pi / 2) +
  scale_y_continuous(limits = c(0, 100), breaks = seq(0, 100, 20), expand = expansion(mult = c(0, 0.18))) +
  scale_color_manual(values = IMPRINT_PALETTE) +
  scale_fill_manual(values = IMPRINT_PALETTE) +
  labs(
    title = "radar-multi · r · ggplot2 · anyplot.ai",
    x = NULL, y = NULL, color = NULL, fill = NULL
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
    plot.title         = element_text(color = INK, size = 12, hjust = 0.5),
    legend.position    = "bottom",
    legend.background  = element_rect(fill = ELEVATED_BG, color = INK_SOFT),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_blank()
  )

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
