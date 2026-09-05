#' anyplot.ai
#' histogram-2d: 2D Histogram Heatmap
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 82/100 | Created: 2026-09-05

library(ggplot2)
library(tibble)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# --- Data --------------------------------------------------------------------
# Daily returns (%) for two correlated asset classes: equities vs. bonds.
n <- 20000
equity_returns <- rnorm(n, mean = 0.05, sd = 1.2)
bond_returns <- 0.35 * equity_returns + rnorm(n, mean = 0.02, sd = 0.5)

df <- tibble(equity_returns = equity_returns, bond_returns = bond_returns)

# --- Plot ---------------------------------------------------------------------
title_text <- "histogram-2d · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = equity_returns, y = bond_returns)) +
  geom_bin2d(bins = 28) +
  scale_fill_gradient(
    low = "#009E73",
    high = "#4467A3",
    name = "Count",
    trans = "sqrt",
    labels = scales::label_comma()
  ) +
  stat_density_2d(color = INK_SOFT, linewidth = 0.25, alpha = 0.5) +
  labs(
    title = title_text,
    x = "Equity Daily Return (%)",
    y = "Bond Daily Return (%)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.line         = element_line(color = INK_SOFT),
    plot.title        = element_text(color = INK, size = 12),
    legend.title      = element_text(color = INK, size = 10),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.key.height = unit(0.35, "in")
  )

# --- Save ----------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
