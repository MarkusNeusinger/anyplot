#' anyplot.ai
#' burndown-sprint: Agile Sprint Burndown Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-06-14

library(ggplot2)
library(dplyr)
library(tidyr)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green (actual burndown)
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue (ideal line)
  "#BD8233",  # 4 — ochre
  "#AE3030",  # 5 — matte red
  "#2ABCCD",  # 6 — cyan
  "#954477",  # 7 — rose
  "#99B314"   # 8 — lime
)

ANYPLOT_AMBER <- "#DDCC77"  # scope-change marker (warning/caution)

# Sprint data — 10 working days, starting with 52 story points
# Scope change on day 4 (+8 points added)
sprint_days <- 1:10
total_scope  <- 52
scope_change_day <- 4
scope_added      <- 8

# Ideal burndown: straight line from total_scope to 0 over 10 days
# After scope change on day 4, total scope becomes 60
ideal_initial <- seq(total_scope, 0, length.out = 11)[sprint_days]

# Adjusted ideal after scope increase on day 4:
# Days 1-4: original ideal; days 5-10: rebaselined from remaining scope to 0
ideal_revised <- c(
  seq(total_scope, total_scope - (total_scope / 10) * 4, length.out = 5),
  seq(total_scope - (total_scope / 10) * 4 + scope_added, 0, length.out = 6)
)[-1]

# Actual remaining work (step function — discrete completions)
actual_remaining <- c(52, 47, 43, 40, 56, 50, 44, 35, 22, 0)

df <- data.frame(
  day       = sprint_days,
  remaining = actual_remaining,
  ideal     = ideal_initial
)

# Weekend bands: in a Mon-Fri sprint, days 6-7 are weekend (Sat-Sun)
# For a 10-working-day sprint, no weekends fall within working days —
# so we shade between-day gaps to show non-working days (days 5.5-7.5 as weekend)
# Actually, sprint days 1-5 = week 1, 6-10 = week 2; weekend falls between them
# We shade x = 5.5 to 6.5 to indicate the weekend gap

# Scope change annotation
scope_change_x <- scope_change_day + 0.5  # between day 4 and 5

# Title
plot_title <- "burndown-sprint · r · ggplot2 · anyplot.ai"

# Compute title font size (67-char baseline)
title_chars <- nchar(plot_title)
title_size  <- max(8, round(12 * 67 / title_chars))

p <- ggplot(df, aes(x = day)) +

  # Weekend shading band (between working week 1 and 2)
  annotate(
    "rect",
    xmin = 5.5, xmax = 6.5,
    ymin = -Inf, ymax = Inf,
    fill = INK_SOFT, alpha = 0.08
  ) +

  # Ideal burndown line (dashed, blue)
  geom_line(
    aes(y = ideal, linetype = "Ideal"),
    color     = IMPRINT_PALETTE[3],
    linewidth = 0.9,
    linetype  = "dashed"
  ) +

  # Actual remaining work as step series
  geom_step(
    aes(y = remaining, linetype = "Actual"),
    color     = IMPRINT_PALETTE[1],
    linewidth = 1.2
  ) +

  # Points on actual line for daily readings
  geom_point(
    aes(y = remaining),
    color = IMPRINT_PALETTE[1],
    size  = 3.0,
    shape = 16
  ) +

  # Scope change marker — vertical dashed line in amber
  geom_vline(
    xintercept = scope_change_x,
    color      = ANYPLOT_AMBER,
    linewidth  = 0.8,
    linetype   = "dotted"
  ) +

  # Scope change annotation label
  annotate(
    "text",
    x     = scope_change_x + 0.12,
    y     = 54,
    label = "+8 pts\nscope added",
    color = ANYPLOT_AMBER,
    size  = 2.8,
    hjust = 0,
    fontface = "bold"
  ) +

  # Weekend annotation
  annotate(
    "text",
    x     = 6.0,
    y     = 2,
    label = "weekend",
    color = INK_MUTED,
    size  = 2.2,
    angle = 90
  ) +

  # Legend entries via manual scale (geom_step doesn't carry aes(linetype) well,
  # so we use a dummy guide via override)
  scale_linetype_manual(
    name   = NULL,
    values = c("Actual" = "solid", "Ideal" = "dashed"),
    guide  = "none"
  ) +

  # Axes
  scale_x_continuous(
    breaks = sprint_days,
    labels = paste0("Day ", sprint_days),
    expand = expansion(mult = c(0.03, 0.05))
  ) +
  scale_y_continuous(
    limits = c(0, 62),
    breaks = seq(0, 60, by = 10),
    expand = expansion(mult = c(0.02, 0.04))
  ) +

  labs(
    title = plot_title,
    x     = "Sprint Day",
    y     = "Remaining Story Points"
  ) +

  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK_SOFT, linewidth = 0.2),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks        = element_line(color = INK_SOFT, linewidth = 0.3),
    axis.title        = element_text(color = INK,      size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.text.x       = element_text(angle = 30, hjust = 1),
    plot.title        = element_text(color = INK,      size = title_size,
                                     margin = margin(b = 10)),
    plot.margin       = margin(20, 20, 15, 15)
  )

# Add manual legend using a secondary annotation approach
# Draw colored segments in the top-right for the legend
legend_x    <- 8.2
legend_y_a  <- 58   # Actual
legend_y_i  <- 53   # Ideal

p <- p +
  # Actual legend swatch
  annotate("segment",
    x = legend_x, xend = legend_x + 0.9,
    y = legend_y_a, yend = legend_y_a,
    color = IMPRINT_PALETTE[1], linewidth = 1.2
  ) +
  annotate("point",
    x = legend_x + 0.45, y = legend_y_a,
    color = IMPRINT_PALETTE[1], size = 2.5
  ) +
  annotate("text",
    x = legend_x + 1.05, y = legend_y_a,
    label = "Actual", color = INK_SOFT, size = 2.8, hjust = 0
  ) +
  # Ideal legend swatch
  annotate("segment",
    x = legend_x, xend = legend_x + 0.9,
    y = legend_y_i, yend = legend_y_i,
    color = IMPRINT_PALETTE[3], linewidth = 0.9, linetype = "dashed"
  ) +
  annotate("text",
    x = legend_x + 1.05, y = legend_y_i,
    label = "Ideal", color = INK_SOFT, size = 2.8, hjust = 0
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
