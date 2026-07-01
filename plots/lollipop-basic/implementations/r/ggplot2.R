#' anyplot.ai
#' lollipop-basic: Basic Lollipop Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 83/100 | Created: 2026-07-01

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# Theme tokens — Imprint palette (prompts/default-style-guide.md)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)
BRAND <- IMPRINT_PALETTE[1]

# Data — aerobic fitness index by sport discipline (12 disciplines, sorted)
disciplines <- c(
  "Triathlon", "Running", "Gymnastics", "Swimming", "Rowing",
  "Cycling", "Soccer", "Skiing", "Basketball", "Tennis",
  "Volleyball", "Hiking"
)
scores <- c(94, 91, 89, 87, 85, 83, 80, 78, 76, 74, 71, 67)

df <- data.frame(discipline = disciplines, score = scores) |>
  arrange(score) |>
  mutate(discipline = factor(discipline, levels = discipline))

baseline <- 60

# Plot — horizontal lollipop; stems extend from baseline to score value
p <- ggplot(df, aes(x = score, y = discipline)) +
  geom_segment(
    aes(x = baseline, xend = score, y = discipline, yend = discipline),
    color     = INK_SOFT,
    linewidth = 0.7
  ) +
  geom_point(
    color = BRAND,
    size  = 3.5
  ) +
  scale_x_continuous(
    limits = c(baseline, 100),
    breaks = seq(60, 100, 10),
    expand = expansion(mult = c(0, 0.05))
  ) +
  labs(
    x     = "Aerobic Fitness Index",
    y     = NULL,
    title = "lollipop-basic · r · ggplot2 · anyplot.ai"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x  = element_line(color = INK, linewidth = 0.2),
    panel.grid.major.y  = element_blank(),
    panel.grid.minor    = element_blank(),
    axis.title.x        = element_text(color = INK, size = 10),
    axis.text.x         = element_text(color = INK_SOFT, size = 8),
    axis.text.y         = element_text(color = INK, size = 8),
    plot.title          = element_text(color = INK, size = 12),
    plot.title.position = "plot",
    plot.margin         = margin(12, 16, 12, 8),
    axis.line.x         = element_line(color = INK_SOFT, linewidth = 0.5),
    axis.line.y         = element_blank(),
    axis.ticks          = element_blank()
  )

# Save — ragg device for correct PNG output in CI
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
