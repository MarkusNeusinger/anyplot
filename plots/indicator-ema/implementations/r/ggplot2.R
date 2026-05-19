#' anyplot.ai
#' indicator-ema: Exponential Moving Average (EMA) Indicator Chart
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-05-19

library(ggplot2)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

OKABE_ITO <- c(
    "#009E73",  # 1 - brand green (price)
    "#D55E00",  # 2 - vermillion (EMA 12)
    "#0072B2"   # 3 - blue (EMA 26)
)

# Data - synthetic daily prices for a tech stock over ~180 trading days
n_days  <- 180
dates   <- seq.Date(as.Date("2024-01-02"), by = "day", length.out = n_days)
returns <- rnorm(n_days, mean = 0.0005, sd = 0.018)
close   <- 150 * cumprod(1 + returns)

calc_ema <- function(prices, period) {
    k   <- 2 / (period + 1)
    ema <- numeric(length(prices))
    ema[1] <- prices[1]
    for (i in seq(2, length(prices))) {
        ema[i] <- prices[i] * k + ema[i - 1] * (1 - k)
    }
    ema
}

df <- data.frame(
    date  = dates,
    close = close,
    ema12 = calc_ema(close, 12),
    ema26 = calc_ema(close, 26)
)

# Plot
p <- ggplot(df, aes(x = date)) +
    geom_line(aes(y = close, color = "Price"),    linewidth = 1.5, alpha = 0.80) +
    geom_line(aes(y = ema12, color = "EMA (12)"), linewidth = 1.1) +
    geom_line(aes(y = ema26, color = "EMA (26)"), linewidth = 1.1) +
    scale_color_manual(
        name   = NULL,
        values = c(
            "Price"    = OKABE_ITO[1],
            "EMA (12)" = OKABE_ITO[2],
            "EMA (26)" = OKABE_ITO[3]
        ),
        breaks = c("Price", "EMA (12)", "EMA (26)")
    ) +
    scale_x_date(date_labels = "%b %Y", date_breaks = "2 months") +
    scale_y_continuous(labels = dollar_format()) +
    labs(
        title = "Tech Stock EMA · indicator-ema · r · ggplot2 · anyplot.ai",
        x     = "Date",
        y     = "Closing Price (USD)"
    ) +
    theme_minimal(base_size = 14) +
    theme(
        plot.background    = element_rect(fill = PAGE_BG,     color = PAGE_BG),
        panel.background   = element_rect(fill = PAGE_BG,     color = NA),
        panel.grid.major.y = element_line(color = INK_SOFT,   linewidth = 0.3),
        panel.grid.major.x = element_blank(),
        panel.grid.minor   = element_blank(),
        panel.border       = element_blank(),
        axis.title         = element_text(color = INK,        size = 20),
        axis.text          = element_text(color = INK_SOFT,   size = 16),
        axis.line          = element_line(color = INK_SOFT,   linewidth = 0.5),
        plot.title         = element_text(color = INK,        size = 22, face = "bold"),
        legend.background  = element_rect(fill = ELEVATED_BG, color = INK_SOFT),
        legend.text        = element_text(color = INK_SOFT,   size = 16),
        legend.key         = element_rect(fill = ELEVATED_BG, color = NA),
        legend.position    = "bottom",
        plot.margin        = margin(20, 20, 20, 20, unit = "pt")
    )

# Save
ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 16,
    height   = 9,
    units    = "in",
    dpi      = 300
)
