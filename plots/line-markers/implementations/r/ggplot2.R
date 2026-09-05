#' anyplot.ai
#' line-markers: Line Plot with Markers
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 85/100 | Created: 2026-09-05

library(ggplot2)
library(tibble)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette (see prompts/default-style-guide.md "Categorical Palette")
IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green, always first series
  "#4467A3"   # 3 — blue, second series
)

# --- Data ---------------------------------------------------------------
# Quality-control inspection: diameter readings (mm) of a machined part,
# sampled once per shift across two production lines.
shift <- 1:16

line_a <- 24.98 + cumsum(rnorm(16, mean = 0, sd = 0.015)) +
  rnorm(16, mean = 0, sd = 0.01)
line_b <- 25.02 + cumsum(rnorm(16, mean = 0, sd = 0.015)) +
  rnorm(16, mean = 0, sd = 0.01)

n_shifts <- length(shift)
df <- tibble(
  shift = rep(shift, 2),
  diameter = c(line_a, line_b),
  production_line = factor(rep(c("Line A", "Line B"), each = n_shifts))
)

# Lines converge around shift 6 (diameters within 0.004mm) before diverging —
# call out the crossover as the chart's focal point.
cross_shift <- 6
cross_y <- mean(c(line_a[cross_shift], line_b[cross_shift]))

# --- Plot -----------------------------------------------------------------
title_text <- "line-markers · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = shift, y = diameter, color = production_line, shape = production_line, fill = production_line)) +
  geom_line(linewidth = 1.0) +
  geom_point(size = 3.2, stroke = 1.1) +
  annotate(
    "point", x = cross_shift, y = cross_y,
    shape = 1, size = 7, stroke = 0.8, color = INK_SOFT
  ) +
  annotate(
    "text", x = cross_shift, y = cross_y - 0.05,
    label = "Lines converge", color = INK_SOFT, size = 2.6, vjust = 1
  ) +
  scale_color_manual(values = IMPRINT_PALETTE) +
  scale_fill_manual(values = c(IMPRINT_PALETTE[1], PAGE_BG)) +
  scale_shape_manual(values = c(21, 24)) +
  scale_x_continuous(breaks = shift) +
  labs(
    title = title_text,
    x = "Inspection Shift",
    y = "Part Diameter (mm)",
    color = "Production Line",
    shape = "Production Line",
    fill = "Production Line"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.25),
    panel.grid.major.x = element_blank(),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12, face = "plain", margin = margin(b = 4)),
    plot.margin       = margin(t = 6, r = 10, b = 6, l = 6),
    legend.position   = "top",
    legend.margin     = margin(t = 0, b = 0),
    legend.box.spacing = unit(2, "pt"),
    legend.title      = element_blank(),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.key        = element_rect(fill = PAGE_BG, color = NA)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
