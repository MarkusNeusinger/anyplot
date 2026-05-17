#' anyplot.ai
#' ohlc-bar: OHLC Bar Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-05-17

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

# --- Data: Realistic stock prices over 50 trading days ----------------------
dates <- seq(as.Date("2024-01-01"), by = "1 day", length.out = 50)
# Filter to trading days (Mon-Fri)
trading_dates <- dates[weekdays(dates) %in% c("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")]
trading_dates <- trading_dates[1:45]

# Generate realistic OHLC data with trend
n <- length(trading_dates)
returns <- rnorm(n, mean = 0.001, sd = 0.015)
close_prices <- 150 * cumprod(1 + returns)

ohlc_data <- data.frame(
  date = trading_dates,
  open = close_prices + rnorm(n, mean = -0.5, sd = 0.8),
  close = close_prices,
  high = pmax(close_prices, close_prices + abs(rnorm(n, mean = 1.5, sd = 0.6))),
  low = pmin(close_prices, close_prices - abs(rnorm(n, mean = 1.5, sd = 0.6)))
) %>%
  mutate(
    direction = ifelse(close > open, "up", "down"),
    color_val = if_else(direction == "up", OKABE_ITO[1], OKABE_ITO[2]),
    x_pos = as.numeric(date)
  )

# --- Build plot segments for high-low and open-close ticks ------------------
# Main high-low vertical lines
hl_segments <- ohlc_data %>%
  mutate(
    y_min = low,
    y_max = high
  ) %>%
  select(x_pos, y_min, y_max, direction, color_val)

# Open tick marks (left side, small horizontal)
open_segments <- ohlc_data %>%
  mutate(
    x_start = x_pos - 1.5,
    x_end = x_pos,
    y = open
  ) %>%
  select(x_start, x_end, y, direction, color_val)

# Close tick marks (right side, small horizontal)
close_segments <- ohlc_data %>%
  mutate(
    x_start = x_pos,
    x_end = x_pos + 1.5,
    y = close
  ) %>%
  select(x_start, x_end, y, direction, color_val)

# --- Create the plot --------------------------------------------------------
p <- ggplot() +
  # High-low vertical lines
  geom_segment(
    data = hl_segments,
    aes(x = x_pos, xend = x_pos, y = y_min, yend = y_max, color = direction),
    linewidth = 1.2,
    show.legend = FALSE
  ) +
  # Open tick marks (left)
  geom_segment(
    data = open_segments,
    aes(x = x_start, xend = x_end, y = y, yend = y, color = direction),
    linewidth = 1.0,
    show.legend = FALSE
  ) +
  # Close tick marks (right)
  geom_segment(
    data = close_segments,
    aes(x = x_start, xend = x_end, y = y, yend = y, color = direction),
    linewidth = 1.0,
    show.legend = FALSE
  ) +
  scale_color_manual(
    values = c("up" = OKABE_ITO[1], "down" = OKABE_ITO[2])
  ) +
  scale_x_continuous(
    breaks = seq(1, nrow(ohlc_data), by = 5),
    labels = format(ohlc_data$date[seq(1, nrow(ohlc_data), by = 5)], "%b %d"),
    expand = c(0.02, 0)
  ) +
  labs(
    title = "ohlc-bar · ggplot2 · anyplot.ai",
    x = "Date",
    y = "Price ($)"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.25),
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    axis.title       = element_text(color = INK,      size = 20),
    axis.text        = element_text(color = INK_SOFT, size = 16),
    axis.text.x      = element_text(angle = 45, hjust = 1),
    plot.title       = element_text(color = INK,      size = 24, margin = margin(b = 12))
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
