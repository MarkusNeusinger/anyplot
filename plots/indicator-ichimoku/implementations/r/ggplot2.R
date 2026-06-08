#' anyplot.ai
#' indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 80/100 | Created: 2026-06-08

library(ggplot2)
library(dplyr)
library(tidyr)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green (bullish cloud / Tenkan-sen)
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue (Kijun-sen)
  "#BD8233",  # 4 — ochre (Chikou Span)
  "#AE3030",  # 5 — matte red (bearish cloud)
  "#2ABCCD",  # 6 — cyan
  "#954477",  # 7 — rose
  "#99B314"   # 8 — lime
)

# Data — synthetic daily OHLC for ~200 trading periods
n_periods <- 200
dates <- seq.Date(as.Date("2023-01-03"), by = "day", length.out = n_periods)
# Filter to weekdays only
dates <- dates[weekdays(dates) %in% c("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")]
dates <- dates[seq_len(min(160, length(dates)))]
n <- length(dates)

# Simulate a trending price series
log_returns <- cumsum(rnorm(n, mean = 0.0005, sd = 0.012))
close_prices <- 150 * exp(log_returns)

# Generate OHLC from close
daily_range <- abs(rnorm(n, mean = 0.008, sd = 0.004)) * close_prices
open_prices  <- close_prices - rnorm(n, 0, 0.003) * close_prices
high_prices  <- pmax(open_prices, close_prices) + daily_range * 0.6
low_prices   <- pmin(open_prices, close_prices) - daily_range * 0.4

# Ichimoku components (standard 9, 26, 52 parameters)
roll_high <- function(x, k) {
  sapply(seq_along(x), function(i) if (i < k) NA else max(x[(i - k + 1):i]))
}
roll_low <- function(x, k) {
  sapply(seq_along(x), function(i) if (i < k) NA else min(x[(i - k + 1):i]))
}

tenkan_sen <- (roll_high(high_prices, 9)  + roll_low(low_prices, 9))  / 2
kijun_sen  <- (roll_high(high_prices, 26) + roll_low(low_prices, 26)) / 2

# Senkou Spans plotted 26 periods ahead
span_a_raw <- (tenkan_sen + kijun_sen) / 2
span_b_raw <- (roll_high(high_prices, 52) + roll_low(low_prices, 52)) / 2

senkou_span_a <- c(rep(NA, 26), span_a_raw)[seq_len(n)]
senkou_span_b <- c(rep(NA, 26), span_b_raw)[seq_len(n)]

# Chikou Span: close shifted 26 periods back
chikou_span <- c(close_prices[27:n], rep(NA, 26))

df <- data.frame(
  date          = dates,
  open          = open_prices,
  high          = high_prices,
  low           = low_prices,
  close         = close_prices,
  tenkan_sen    = tenkan_sen,
  kijun_sen     = kijun_sen,
  senkou_span_a = senkou_span_a,
  senkou_span_b = senkou_span_b,
  chikou_span   = chikou_span,
  bullish       = senkou_span_a > senkou_span_b
)

# Candle direction for coloring
df$up <- df$close >= df$open
CANDLE_UP   <- IMPRINT_PALETTE[1]  # green — bullish candle
CANDLE_DOWN <- IMPRINT_PALETTE[5]  # matte red — bearish candle

# Cloud ribbon segments: split by bullish/bearish for two-color fill
# We build a long ribbon data frame for geom_ribbon, splitting where cloud flips
df_cloud <- df |>
  filter(!is.na(senkou_span_a) & !is.na(senkou_span_b)) |>
  mutate(
    upper = pmax(senkou_span_a, senkou_span_b),
    lower = pmin(senkou_span_a, senkou_span_b),
    cloud_type = if_else(senkou_span_a >= senkou_span_b, "bullish", "bearish")
  )

# Title length scaling
title_str <- "Nikkei 225 · indicator-ichimoku · r · ggplot2 · anyplot.ai"
n_title   <- nchar(title_str)
title_fs  <- max(8, round(12 * 67 / n_title))

# Build plot
p <- ggplot(df, aes(x = date)) +

  # Cloud (Kumo) — bearish fill first, then bullish on top
  geom_ribbon(
    data = filter(df_cloud, cloud_type == "bearish"),
    aes(ymin = lower, ymax = upper),
    fill  = IMPRINT_PALETTE[5],
    alpha = 0.25
  ) +
  geom_ribbon(
    data = filter(df_cloud, cloud_type == "bullish"),
    aes(ymin = lower, ymax = upper),
    fill  = IMPRINT_PALETTE[1],
    alpha = 0.25
  ) +

  # Senkou Spans (cloud boundaries)
  geom_line(aes(y = senkou_span_a), color = IMPRINT_PALETTE[1],
            linewidth = 0.5, linetype = "dashed", na.rm = TRUE) +
  geom_line(aes(y = senkou_span_b), color = IMPRINT_PALETTE[5],
            linewidth = 0.5, linetype = "dashed", na.rm = TRUE) +

  # Candlestick wicks
  geom_segment(
    aes(xend = date, y = low, yend = high, color = up),
    linewidth = 0.4
  ) +

  # Candlestick bodies
  geom_rect(
    aes(
      xmin = date - 0.3, xmax = date + 0.3,
      ymin = pmin(open, close), ymax = pmax(open, close),
      fill = up
    ),
    color = NA
  ) +

  # Ichimoku lines
  geom_line(aes(y = tenkan_sen),  color = IMPRINT_PALETTE[1],
            linewidth = 0.9, na.rm = TRUE) +
  geom_line(aes(y = kijun_sen),   color = IMPRINT_PALETTE[3],
            linewidth = 0.9, na.rm = TRUE) +
  geom_line(aes(y = chikou_span), color = IMPRINT_PALETTE[4],
            linewidth = 0.7, linetype = "dotted", na.rm = TRUE) +

  # Candle color scales
  scale_color_manual(
    values = c("TRUE" = CANDLE_UP, "FALSE" = CANDLE_DOWN),
    guide  = "none"
  ) +
  scale_fill_manual(
    values = c("TRUE" = CANDLE_UP, "FALSE" = CANDLE_DOWN),
    guide  = "none"
  ) +

  scale_x_date(date_breaks = "1 month", date_labels = "%b %Y",
               expand = expansion(mult = 0.01)) +
  scale_y_continuous(labels = label_dollar(), expand = expansion(mult = 0.03)) +

  labs(
    title = title_str,
    x     = NULL,
    y     = "Price (USD)"
  ) +

  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG,     color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG,     color = NA),
    panel.grid.major  = element_line(color = INK_MUTED,  linewidth = 0.2),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.title.y      = element_text(color = INK,      size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.text.x       = element_text(angle = 30, hjust = 1),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks        = element_line(color = INK_SOFT, linewidth = 0.3),
    plot.title        = element_text(color = INK, size = title_fs, face = "bold",
                                     margin = margin(b = 8)),
    plot.margin       = margin(12, 16, 10, 12)
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
