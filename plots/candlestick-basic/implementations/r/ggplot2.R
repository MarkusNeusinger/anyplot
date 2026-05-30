#' anyplot.ai
#' candlestick-basic: Basic Candlestick Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 91/100 | Created: 2026-05-30

library(ggplot2)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette — semantic finance mapping (position 1: gain, position 5: loss)
BULL_COLOR <- "#009E73"  # bullish / gain
BEAR_COLOR <- "#AE3030"  # bearish / loss

# --- Data --------------------------------------------------------------------
# NovaTech Corp (NVTK) — 40 trading days, Jan–Mar 2024
all_dates   <- seq(as.Date("2024-01-02"), by = "day", length.out = 60)
trade_dates <- all_dates[!weekdays(all_dates) %in% c("Saturday", "Sunday")]
trade_dates <- head(trade_dates, 40)
n           <- length(trade_dates)

price  <- 148.0
opens  <- numeric(n)
highs  <- numeric(n)
lows   <- numeric(n)
closes <- numeric(n)

for (i in seq_len(n)) {
    daily_range <- runif(1, 1.5, 4.5)
    open_i      <- price + rnorm(1, 0, 0.5)
    close_i     <- open_i + rnorm(1, 0.2, daily_range * 0.45)
    high_i      <- max(open_i, close_i) + runif(1, 0.2, daily_range * 0.35)
    low_i       <- min(open_i, close_i) - runif(1, 0.2, daily_range * 0.35)
    opens[i]    <- open_i
    highs[i]    <- high_i
    lows[i]     <- low_i
    closes[i]   <- close_i
    price       <- close_i
}

df <- data.frame(
    date      = trade_dates,
    x         = seq_len(n),
    open      = opens,
    high      = highs,
    low       = lows,
    close     = closes
)
df$direction   <- ifelse(df$close >= df$open, "up", "down")
df$body_top    <- pmax(df$open, df$close)
df$body_bottom <- pmin(df$open, df$close)
df$xmin        <- df$x - 0.38
df$xmax        <- df$x + 0.38

# Closing price trend line (linear fit) for visual storytelling
trend_fit <- lm(close ~ x, data = df)
trend_y   <- fitted(trend_fit)

# --- X-axis breaks -----------------------------------------------------------
break_idx    <- seq(1, n, by = 5)
break_labels <- format(trade_dates[break_idx], "%b %d")

# --- Plot --------------------------------------------------------------------
p <- ggplot(df) +
    # High-low wicks
    geom_segment(
        aes(x = x, xend = x, y = low, yend = high, color = direction),
        linewidth = 0.45, show.legend = FALSE
    ) +
    # Subtle trend overlay (closing prices)
    geom_line(
        data = data.frame(x = df$x, close = trend_y),
        aes(x = x, y = close),
        color = INK_SOFT, linewidth = 0.5, linetype = "dashed",
        inherit.aes = FALSE, alpha = 0.55
    ) +
    # Open-close bodies
    geom_rect(
        aes(xmin = xmin, xmax = xmax, ymin = body_bottom, ymax = body_top,
            fill = direction, color = direction),
        linewidth = 0.2
    ) +
    scale_color_manual(
        values = c("up" = BULL_COLOR, "down" = BEAR_COLOR),
        guide  = "none"
    ) +
    scale_fill_manual(
        values = c("up" = BULL_COLOR, "down" = BEAR_COLOR),
        labels = c("up" = "Bullish", "down" = "Bearish"),
        breaks = c("up", "down"),
        name   = NULL
    ) +
    scale_x_continuous(
        breaks = break_idx,
        labels = break_labels,
        expand = expansion(mult = c(0.02, 0.02))
    ) +
    scale_y_continuous(
        labels = label_dollar(accuracy = 0.01),
        expand = expansion(mult = c(0.03, 0.04))
    ) +
    labs(
        title = "NovaTech Corp (NVTK) · candlestick-basic · r · ggplot2 · anyplot.ai",
        x     = NULL,
        y     = "Price (USD)"
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background    = element_rect(fill = PAGE_BG,     color = PAGE_BG),
        panel.background   = element_rect(fill = PAGE_BG,     color = NA),
        panel.grid.major.y = element_line(color = INK_SOFT,   linewidth = 0.2),
        panel.grid.major.x = element_blank(),
        panel.grid.minor   = element_blank(),
        axis.title         = element_text(color = INK,        size = 10),
        axis.text          = element_text(color = INK_SOFT,   size = 8),
        axis.text.x        = element_text(angle = 40, hjust = 1),
        axis.line          = element_line(color = INK_SOFT,   linewidth = 0.3),
        axis.ticks         = element_line(color = INK_SOFT,   linewidth = 0.3),
        plot.title         = element_text(color = INK,        size = 12,
                                          margin = margin(b = 8)),
        legend.background  = element_rect(fill = ELEVATED_BG, color = INK_SOFT,
                                          linewidth = 0.3),
        legend.text        = element_text(color = INK_SOFT,   size = 8),
        legend.key.size    = unit(0.9, "lines"),
        legend.position    = "top",
        legend.direction   = "horizontal",
        plot.margin        = margin(t = 10, r = 14, b = 8, l = 8)
    )

# --- Save --------------------------------------------------------------------
ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 8,
    height   = 4.5,
    units    = "in",
    dpi      = 400
)
