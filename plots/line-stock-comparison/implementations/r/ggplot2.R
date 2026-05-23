#' anyplot.ai
#' line-stock-comparison: Stock Price Comparison Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-05-23

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
# Reduce grid opacity in dark mode — ggplot2 lacks alpha on element_line,
# so embed alpha into the hex color via adjustcolor()
GRID_COLOR  <- adjustcolor(INK_SOFT, alpha.f = if (THEME == "dark") 0.35 else 0.55)

ANYPLOT_PALETTE <- c("#009E73", "#9418DB", "#B71D27", "#16B8F3")

# Data - approximately 1 year of trading days starting Jan 2023
all_dates     <- seq(as.Date("2023-01-03"), by = "day", length.out = 400)
trading_dates <- all_dates[!weekdays(all_dates) %in% c("Saturday", "Sunday")]
trading_dates <- trading_dates[1:252]

tickers <- c("NVDA", "MSFT", "AAPL", "SPY")
mu      <- c(0.0020, 0.0007, 0.0005, 0.0003)
sigma   <- c(0.028,  0.015,  0.012,  0.008)

prices_list <- lapply(seq_along(tickers), function(i) {
    returns <- rnorm(length(trading_dates) - 1, mean = mu[i], sd = sigma[i])
    data.frame(
        date    = trading_dates,
        symbol  = tickers[i],
        rebased = cumprod(c(1.0, exp(returns))) * 100
    )
})

df        <- do.call(rbind, prices_list)
df$symbol <- factor(df$symbol, levels = tickers)

# Key 2023 market events
svb_region <- data.frame(
    xmin = as.Date("2023-03-06"), xmax = as.Date("2023-03-17"),
    ymin = -Inf, ymax = Inf
)
ai_surge_date  <- as.Date("2023-05-24")
rate_peak_date <- as.Date("2023-10-26")

# Plot
p <- ggplot(df, aes(x = date, y = rebased, color = symbol)) +
    # SVB collapse period — shaded rect
    geom_rect(
        data = svb_region,
        aes(xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax),
        fill = "#B71D27", alpha = 0.07,
        inherit.aes = FALSE
    ) +
    # Reference line at 100
    geom_hline(yintercept = 100, color = INK_SOFT, linewidth = 0.5,
               linetype = "dashed") +
    # Event marker lines
    geom_vline(xintercept = c(ai_surge_date, rate_peak_date),
               color = INK_SOFT, linewidth = 0.35, linetype = "dotted") +
    # Stock lines
    geom_line(linewidth = 1.1, alpha = 0.92) +
    # Rotated event labels alongside vertical markers
    annotate("text", x = as.Date("2023-03-11"), y = 102,
             label = "SVB Collapse", color = INK_SOFT, size = 2.1,
             angle = 90, hjust = 0, vjust = -0.4, fontface = "italic") +
    annotate("text", x = ai_surge_date, y = 102,
             label = "NVDA AI Surge", color = INK_SOFT, size = 2.1,
             angle = 90, hjust = 0, vjust = -0.4, fontface = "italic") +
    annotate("text", x = rate_peak_date, y = 102,
             label = "Rates Peak", color = INK_SOFT, size = 2.1,
             angle = 90, hjust = 0, vjust = -0.4, fontface = "italic") +
    scale_color_manual(values = setNames(ANYPLOT_PALETTE, tickers), name = NULL) +
    scale_x_date(date_labels = "%b '%y", date_breaks = "2 months") +
    labs(
        title = "line-stock-comparison · r · ggplot2 · anyplot.ai",
        x     = "Date",
        y     = "Rebased Price (Start = 100)"
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background  = element_rect(fill = PAGE_BG, color = NA),
        panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.2),
        panel.grid.minor  = element_blank(),
        panel.border      = element_blank(),
        axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
        axis.title        = element_text(color = INK, size = 10),
        axis.text         = element_text(color = INK_SOFT, size = 8),
        axis.text.x       = element_text(angle = 30, hjust = 1),
        plot.title        = element_text(color = INK, size = 12,
                                          margin = margin(b = 8)),
        legend.background = element_rect(fill = ELEVATED_BG,
                                          color = INK_SOFT, linewidth = 0.3),
        legend.text       = element_text(color = INK_SOFT, size = 8),
        legend.title      = element_text(color = INK, size = 10),
        legend.position   = "right",
        plot.margin       = margin(12, 12, 12, 12)
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
