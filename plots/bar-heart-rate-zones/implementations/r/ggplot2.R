#' anyplot.ai
#' bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 91/100 | Created: 2026-06-14

library(ggplot2)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID_COLOR  <- if (THEME == "light") "#D0CFC7" else "#3A3A36"

# Zone colors — semantic Imprint palette mapping (conventional HR zone hue associations):
# Z1 recovery (grey) -> fixed #6B6A63  |  Z4 threshold (orange) -> Imprint ochre #BD8233
# Z2 endurance (blue) -> Imprint #4467A3  |  Z5 maximum (red) -> semantic red #AE3030
# Z3 aerobic (green) -> Imprint brand green #009E73
ZONE_COLORS <- c(
  Z1 = "#6B6A63",
  Z2 = "#4467A3",
  Z3 = "#009E73",
  Z4 = "#BD8233",
  Z5 = "#AE3030"
)

# Data — 60-minute tempo run workout
zones <- c("Z1", "Z2", "Z3", "Z4", "Z5")
df <- data.frame(
  zone    = factor(zones, levels = zones),
  minutes = c(8, 22, 15, 12, 3),
  hr_low  = c(100, 120, 140, 155, 170),
  hr_high = c(119, 139, 154, 169, 185)
)
# Intensity alpha: de-emphasise low zones, fully saturate high zones
df$intensity <- c(0.55, 0.70, 0.82, 0.92, 1.00)
df$bar_label <- paste0(df$minutes, " min")

# x-axis labels: zone code + name + bpm range
zone_names <- c("Recovery", "Endurance", "Aerobic", "Threshold", "Maximum")
x_labels <- setNames(
  paste0(zones, " – ", zone_names, "\n", df$hr_low, "–", df$hr_high, " bpm"),
  zones
)

# Plot
p <- ggplot(df, aes(x = zone, y = minutes, fill = zone, alpha = I(intensity))) +
  geom_col(width = 0.62) +
  geom_text(
    aes(label = bar_label, y = minutes),
    vjust    = -0.6,
    color    = INK,
    size     = 3.5,
    fontface = "bold"
  ) +
  scale_fill_manual(values = ZONE_COLORS, guide = "none") +
  scale_x_discrete(labels = x_labels) +
  scale_y_continuous(
    expand = expansion(mult = c(0, 0.20)),
    labels = function(x) paste0(x, " min"),
    breaks = seq(0, 25, by = 5)
  ) +
  labs(
    title = "60-Minute Tempo Run · bar-heart-rate-zones · r · ggplot2 · anyplot.ai",
    x     = NULL,
    y     = "Time (minutes)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor.x = element_blank(),
    panel.grid.major.y = element_line(color = GRID_COLOR, linewidth = 0.3),
    panel.grid.minor.y = element_blank(),
    axis.title.y       = element_text(color = INK, size = 10),
    axis.text.x        = element_text(color = INK_SOFT, size = 7.5, lineheight = 1.3),
    axis.text.y        = element_text(color = INK_SOFT, size = 8),
    axis.ticks         = element_blank(),
    plot.title         = element_text(color = INK, size = 12, margin = margin(b = 12)),
    plot.margin        = margin(16, 20, 16, 16)
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
