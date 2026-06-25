#' anyplot.ai
#' ecdf-basic: Basic ECDF Plot
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-06-25

library(ggplot2)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID_COLOR  <- if (THEME == "light") "#1A1A1726" else "#F0EFE826"

IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green (first categorical series)
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue
  "#BD8233",  # 4 — ochre
  "#AE3030",  # 5 — matte red
  "#2ABCCD",  # 6 — cyan
  "#954477",  # 7 — rose
  "#99B314"   # 8 — lime
)

# Data: exam scores comparing two student cohorts
n <- 200
scores_a <- rnorm(n, mean = 68, sd = 14)  # standard curriculum
scores_b <- rnorm(n, mean = 76, sd = 10)  # enriched curriculum

df <- data.frame(
  score  = c(scores_a, scores_b),
  cohort = rep(c("Class A", "Class B"), each = n)
)

# Plot
p <- ggplot(df, aes(x = score, color = cohort, linetype = cohort)) +
  stat_ecdf(linewidth = 1.2, pad = FALSE) +
  scale_color_manual(
    name   = "Student Cohort",
    values = c("Class A" = IMPRINT_PALETTE[1], "Class B" = IMPRINT_PALETTE[2])
  ) +
  scale_linetype_manual(
    name   = "Student Cohort",
    values = c("Class A" = "solid", "Class B" = "dashed")
  ) +
  scale_x_continuous(breaks = seq(20, 120, by = 10)) +
  scale_y_continuous(
    labels = percent_format(accuracy = 1),
    breaks = seq(0, 1, by = 0.25)
  ) +
  labs(
    title = "ecdf-basic · r · ggplot2 · anyplot.ai",
    x     = "Exam Score",
    y     = "Cumulative Proportion"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.5),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.5),
    plot.title        = element_text(color = INK, size = 12),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    legend.position   = "bottom",
    plot.margin       = margin(20, 20, 20, 20)
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
