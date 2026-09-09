#' anyplot.ai
#' sparkline-basic: Basic Sparkline
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 80/100 | Created: 2026-09-09

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK <- if (THEME == "light") "#1A1A17" else "#F0EFE8"

# Imprint palette (see prompts/default-style-guide.md "Categorical Palette")
BRAND <- "#009E73" # position 1 — the trend line, ALWAYS first series
LOW_MARK <- "#AE3030" # position 5 — series minimum
HIGH_MARK <- "#4467A3" # position 3 — series maximum

# --- Data ---------------------------------------------------------------------
# Single stock's closing price over one trading quarter — the sparkline
# convention of embedding a trend inline (financial table cell) without any
# axes, ticks, or gridlines.
n_points <- 90
day <- 1:n_points
closing_price <- 142 + 14 * sin(2 * pi * day / 45 - 1) + cumsum(rnorm(n_points, mean = 0.12, sd = 1.3))

trend <- data.frame(day = day, closing_price = closing_price)
i_min <- which.min(closing_price)
i_max <- which.max(closing_price)
i_last <- n_points

# --- Plot -----------------------------------------------------------------
# geom_ribbon fills the area under the line for the classic sparkline look;
# geom_point marks the series extremes and the latest value — the only
# highlights the spec allows before it stops being "basic".
p <- ggplot(trend, aes(x = day, y = closing_price)) +
  geom_ribbon(aes(ymin = min(closing_price), ymax = closing_price), fill = BRAND, alpha = 0.12) +
  geom_line(color = BRAND, linewidth = 1.6, lineend = "round") +
  geom_point(data = trend[i_min, ], color = LOW_MARK, size = 3.2) +
  geom_point(data = trend[i_max, ], color = HIGH_MARK, size = 3.2) +
  geom_point(data = trend[i_last, ], color = BRAND, size = 3.6) +
  scale_x_continuous(expand = expansion(mult = c(0.01, 0.03))) +
  scale_y_continuous(expand = expansion(mult = c(0.18, 0.18))) +
  labs(title = "sparkline-basic · r · ggplot2 · anyplot.ai") +
  theme_void(base_size = 8) +
  theme(
    aspect.ratio = 0.16, # thin horizontal band — the sparkline's defining shape
    plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    plot.title = element_text(color = INK, size = 12, hjust = 0.5, margin = margin(b = 30)),
    plot.margin = margin(t = 30, r = 140, b = 30, l = 140)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot = p,
  device = ragg::agg_png,
  width = 8,
  height = 4.5,
  units = "in",
  dpi = 400
)
