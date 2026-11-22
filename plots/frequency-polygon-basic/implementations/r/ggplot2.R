#' anyplot.ai
#' frequency-polygon-basic: Frequency Polygon for Distribution Comparison
#' Library: ggplot2 4.0 | R 4.4.1
#' Quality: 86/100 | Updated: 2026-11-22

library(ggplot2)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID        <- if (THEME == "light") "#D0CECA" else "#3D3D39"

# Imprint palette
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
SCORE <- "Test score"  # role: value
GROUP <- "Cohort"      # role: group

# Data: replace this block with your own table, for example df <- read.csv("scores.csv", check.names = FALSE)
set.seed(42)
df <- tibble::tibble(
  !!SCORE := c(
    rnorm(200, mean = 72, sd = 8),
    rnorm(200, mean = 78, sd = 10),
    rnorm(200, mean = 75, sd = 7)
  ),
  !!GROUP := rep(c("Cohort A", "Cohort B", "Cohort C"), each = 200)
)

# Plot: reads only df and the constants above
df[[GROUP]] <- factor(df[[GROUP]], levels = unique(df[[GROUP]]))
BIN_WIDTH <- 3
BIN_START <- floor(min(df[[SCORE]]) / BIN_WIDTH) * BIN_WIDTH

p <- ggplot(df, aes(x = .data[[SCORE]], color = .data[[GROUP]], fill = .data[[GROUP]])) +
  geom_area(stat = "bin", binwidth = BIN_WIDTH, boundary = BIN_START, pad = TRUE,
            position = "identity", alpha = 0.18, color = NA) +
  geom_freqpoly(binwidth = BIN_WIDTH, boundary = BIN_START, pad = TRUE, linewidth = 1.0) +
  geom_point(stat = "bin", binwidth = BIN_WIDTH, boundary = BIN_START, pad = TRUE, size = 1.8) +
  scale_color_manual(values = IMPRINT_PALETTE) +
  scale_fill_manual(values = IMPRINT_PALETTE) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.06))) +
  labs(
    title = "frequency-polygon-basic · r · ggplot2 · anyplot.ai",
    x = SCORE,
    y = "Frequency",
    color = GROUP,
    fill = GROUP
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = GRID, linewidth = 0.25),
    panel.grid.minor  = element_blank(),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = 12),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.key        = element_rect(fill = PAGE_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10)
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
