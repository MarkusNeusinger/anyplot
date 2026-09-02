#' anyplot.ai
#' candlestick-volume: Stock Candlestick Chart with Volume
#' Library: ggplot2 | R 4.4
#' Quality: pending | Created: 2026-09-02

library(ggplot2)
library(scales)
library(ragg)
library(gridExtra)

set.seed(42)

# --- Theme tokens ------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

UP_COLOR   <- "#009E73"  # Imprint position 1 — bullish (semantic: profit/up -> green)
DOWN_COLOR <- "#AE3030"  # Imprint position 5 — bearish (semantic: loss/down -> red)

# --- Data: 60 trading days of a synthetic tech stock --------------------
n_days <- 60
calendar_days <- seq(as.Date("2024-02-05"), by = "day", length.out = 90)
trading_days <- calendar_days[!format(calendar_days, "%u") %in% c("6", "7")][1:n_days]

daily_returns <- rnorm(n_days, mean = 0.0006, sd = 0.017)
close <- 150 * cumprod(1 + daily_returns)
open <- c(
  close[1] * (1 + rnorm(1, 0, 0.004)),
  close[-n_days] * (1 + rnorm(n_days - 1, 0, 0.005))
)
body_hi <- pmax(open, close)
body_lo <- pmin(open, close)
high <- body_hi + runif(n_days, 0.1, 1.4) * (close * 0.01)
low <- body_lo - runif(n_days, 0.1, 1.4) * (close * 0.01)
volume <- pmax(5e5, round(2.4e6 + abs(daily_returns) * 5.5e7 + rnorm(n_days, 0, 2.5e5)))
direction <- factor(ifelse(close >= open, "Up", "Down"), levels = c("Up", "Down"))

stock <- tibble::tibble(
  date = trading_days, open, high, low, close, volume, direction, body_lo, body_hi
)

candle_width <- 0.32
x_breaks <- stock$date[seq(1, n_days, by = 7)]
x_limits <- range(stock$date) + c(-1, 1)
title_text <- "NovaTech Inc. · candlestick-volume · r · ggplot2 · anyplot.ai"

# --- Shared chrome -------------------------------------------------------
anyplot_theme <- theme_minimal(base_size = 7) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.minor    = element_blank(),
    panel.grid.major.x  = element_blank(),
    panel.grid.major.y  = element_line(color = INK, linewidth = 0.18),
    axis.line           = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks          = element_blank(),
    axis.title          = element_text(color = INK, size = 10),
    axis.text           = element_text(color = INK_SOFT, size = 8),
    legend.position     = "none"
  )

# --- Price pane (top, ~71% of vertical space) -----------------------------
p_price <- ggplot(stock, aes(x = date)) +
  geom_segment(aes(xend = date, y = low, yend = high, color = direction), linewidth = 0.6) +
  geom_rect(
    aes(xmin = date - candle_width, xmax = date + candle_width, ymin = body_lo, ymax = body_hi, fill = direction),
    color = NA
  ) +
  scale_color_manual(values = c(Up = UP_COLOR, Down = DOWN_COLOR)) +
  scale_fill_manual(values = c(Up = UP_COLOR, Down = DOWN_COLOR)) +
  scale_x_date(breaks = x_breaks, limits = x_limits, expand = expansion(mult = 0.015)) +
  scale_y_continuous(labels = label_dollar()) +
  labs(
    title = title_text,
    subtitle = "Green candle = price up (close ≥ open)  ·  Red candle = price down (close < open)",
    y = "Price (USD)", x = NULL
  ) +
  anyplot_theme +
  theme(
    axis.text.x   = element_blank(),
    axis.line.x   = element_blank(),
    plot.title    = element_text(color = INK, size = 12, face = "plain"),
    plot.subtitle = element_text(color = INK_SOFT, size = 8),
    plot.margin   = margin(t = 14, r = 16, b = 4, l = 12)
  )

# --- Volume pane (bottom, ~29% of vertical space) --------------------------
p_volume <- ggplot(stock, aes(x = date)) +
  geom_col(aes(y = volume, fill = direction), width = candle_width * 2) +
  scale_fill_manual(values = c(Up = UP_COLOR, Down = DOWN_COLOR)) +
  scale_x_date(
    breaks = x_breaks, limits = x_limits,
    labels = label_date("%b %d"), expand = expansion(mult = 0.015)
  ) +
  scale_y_continuous(labels = label_number(scale = 1e-6, suffix = "M")) +
  labs(y = "Volume", x = "Trading Date") +
  anyplot_theme +
  theme(plot.margin = margin(t = 4, r = 16, b = 12, l = 12))

# --- Combine panes with a shared, width-aligned x-axis ----------------------
g_price <- ggplotGrob(p_price)
g_volume <- ggplotGrob(p_volume)
aligned_widths <- grid::unit.pmax(g_price$widths, g_volume$widths)
g_price$widths <- aligned_widths
g_volume$widths <- aligned_widths
combined <- arrangeGrob(g_price, g_volume, ncol = 1, heights = c(2.5, 1))

# --- Save --------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = combined,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400,
  bg       = PAGE_BG
)
