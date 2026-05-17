#' anyplot.ai
#' frequency-polygon-basic: Frequency Polygon for Distribution Comparison
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-05-17

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
OKABE_ITO   <- c("#009E73", "#D55E00", "#0072B2", "#CC79A7",
                 "#E69F00", "#56B4E9", "#F0E442")

# --- Data -------------------------------------------------------------------
set.seed(42)
df <- data.frame(
  score = c(
    rnorm(200, mean = 72, sd = 8),   # Group A
    rnorm(200, mean = 78, sd = 10),  # Group B
    rnorm(200, mean = 75, sd = 7)    # Group C
  ),
  group = rep(c("Cohort A", "Cohort B", "Cohort C"), each = 200)
)

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = score, color = group, fill = group)) +
  geom_freqpoly(binwidth = 3, linewidth = 1.2, alpha = 0.3) +
  scale_color_manual(values = OKABE_ITO[1:3]) +
  scale_fill_manual(values = OKABE_ITO[1:3]) +
  labs(
    title = "frequency-polygon-basic · ggplot2 · anyplot.ai",
    x = "Test Score",
    y = "Frequency",
    color = "Group",
    fill = "Group"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 20),
    axis.text         = element_text(color = INK_SOFT, size = 16),
    plot.title        = element_text(color = INK, size = 24),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 16),
    legend.title      = element_text(color = INK, size = 18)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 16,
  height   = 9,
  units    = "in",
  dpi      = 300
)
