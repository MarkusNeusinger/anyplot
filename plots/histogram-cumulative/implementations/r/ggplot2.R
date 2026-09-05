#' anyplot.ai
#' histogram-cumulative: Cumulative Histogram
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 84/100 | Created: 2026-09-05

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome") ----
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
BRAND    <- "#009E73"  # Imprint palette position 1 — always first series

# --- Data: net fill weight of cereal boxes on a packaging line (target 500 g) ----
box_weights <- rnorm(600, mean = 500, sd = 9)

bin_width <- 3
breaks <- seq(
  floor(min(box_weights) / bin_width) * bin_width,
  ceiling(max(box_weights) / bin_width) * bin_width,
  by = bin_width
)
counts <- hist(box_weights, breaks = breaks, plot = FALSE)$counts

# Right bin edge + running total up to that edge; the leading zero anchors the
# step at the histogram's left boundary so geom_step starts from the ground.
cum_df <- data.frame(
  weight    = c(breaks[1], breaks[-1]),
  cum_count = c(0, cumsum(counts))
)
n_total <- length(box_weights)

# --- Plot -------------------------------------------------------------------
p <- ggplot(cum_df, aes(x = weight, y = cum_count)) +
  geom_hline(yintercept = n_total, linetype = "dashed", color = INK_SOFT, linewidth = 0.4) +
  geom_step(color = BRAND, linewidth = 1.1, direction = "hv") +
  geom_point(data = cum_df[-1, ], color = BRAND, size = 2) +
  labs(
    title = "histogram-cumulative · r · ggplot2 · anyplot.ai",
    x     = "Box fill weight (g)",
    y     = "Cumulative count"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor.x = element_blank(),
    panel.grid.minor.y = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.25),
    axis.line         = element_line(color = INK_SOFT),
    axis.ticks        = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = 12)
  )

# --- Save (PNG, both themes) --------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
