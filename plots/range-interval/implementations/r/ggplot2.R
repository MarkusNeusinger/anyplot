#' anyplot.ai
#' range-interval: Range Interval Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-05-18

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
BRAND       <- "#009E73"  # Okabe-Ito position 1 — first categorical series

# --- Data -------------------------------------------------------------------
df <- data.frame(
  month = c("Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
  min_temp = c(-2, 1, 8, 14, 20, 25, 28, 27, 22, 15, 7, 0),
  max_temp = c(5, 9, 16, 22, 28, 32, 35, 34, 28, 20, 12, 6)
) %>%
  mutate(month = factor(month, levels = unique(month)))

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = month, ymin = min_temp, ymax = max_temp)) +
  geom_linerange(
    color = BRAND,
    linewidth = 5.5,
    alpha = 0.85
  ) +
  geom_point(
    aes(y = min_temp),
    color = BRAND,
    size = 3.5,
    alpha = 0.95
  ) +
  geom_point(
    aes(y = max_temp),
    color = BRAND,
    size = 3.5,
    alpha = 0.95
  ) +
  labs(
    title = "range-interval · r · ggplot2 · anyplot.ai",
    x = "Month",
    y = "Temperature (°C)"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    panel.grid.major.y = element_line(
      color = INK_SOFT,
      linewidth = 0.2
    ),
    panel.border = element_blank(),
    axis.title = element_text(color = INK, size = 20),
    axis.text = element_text(color = INK_SOFT, size = 16),
    axis.ticks = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.line.y = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.line.x = element_blank(),
    plot.title = element_text(color = INK, size = 24),
    legend.position = "none"
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
