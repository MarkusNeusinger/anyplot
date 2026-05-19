#' anyplot.ai
#' indicator-ema: Exponential Moving Average (EMA) Indicator Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 92/100 | Created: 2026-05-19

library(ggplot2)
library(scales)
library(tidyr)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

OKABE_ITO <- c(
    "Price"    = "#009E73",
    "EMA (12)" = "#D55E00",
    "EMA (26)" = "#0072B2"
)

# Data
n_days <- 180
dates  <- seq.Date(as.Date("2024-01-02"), by = "day", length.out = n_days)
close  <- 150 * cumprod(1 + rnorm(n_days, mean = 0.0005, sd = 0.018))

# Inline EMA via Reduce — no helper function needed
k12   <- 2 / (12 + 1)
k26   <- 2 / (26 + 1)
ema12 <- Reduce(function(e, x) x * k12 + e * (1 - k12), close, accumulate = TRUE)
ema26 <- Reduce(function(e, x) x * k26 + e * (1 - k26), close, accumulate = TRUE)

df <- data.frame(date = dates, close = close, ema12 = ema12, ema26 = ema26)

# Detect EMA crossovers (sign change in ema12 - ema26)
diff_ema   <- df$ema12 - df$ema26
cross_idx  <- which(diff(sign(diff_ema)) != 0) + 1
crossovers <- df[cross_idx, , drop = FALSE]

# Long form for idiomatic ggplot2 multi-series mapping
df_long <- pivot_longer(df, cols = c(close, ema12, ema26),
                        names_to = "series", values_to = "price")
df_long$series <- factor(df_long$series,
    levels = c("close", "ema12", "ema26"),
    labels = c("Price", "EMA (12)", "EMA (26)"))

# Plot
p <- ggplot(df_long, aes(x = date, y = price, color = series)) +
    geom_vline(data = crossovers, aes(xintercept = date),
               color = INK_SOFT, linetype = "dashed",
               linewidth = 0.4, alpha = 0.7) +
    geom_line(aes(linewidth = series, alpha = series)) +
    geom_point(data = crossovers, aes(x = date, y = ema12),
               shape = 21, size = 4, fill = PAGE_BG,
               color = OKABE_ITO[["EMA (12)"]], stroke = 1.5,
               inherit.aes = FALSE) +
    scale_color_manual(name = NULL, values = OKABE_ITO,
                       breaks = c("Price", "EMA (12)", "EMA (26)")) +
    scale_linewidth_manual(
        values = c("Price" = 1.5, "EMA (12)" = 1.1, "EMA (26)" = 1.1),
        guide  = "none") +
    scale_alpha_manual(
        values = c("Price" = 0.80, "EMA (12)" = 1.0, "EMA (26)" = 1.0),
        guide  = "none") +
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
        plot.title         = element_text(color = INK,        size = 24, face = "bold"),
        legend.background  = element_rect(fill = ELEVATED_BG, color = INK_SOFT),
        legend.text        = element_text(color = INK_SOFT,   size = 16),
        legend.key         = element_rect(fill = ELEVATED_BG, color = NA),
        legend.position    = "bottom",
        plot.margin        = margin(20, 20, 20, 20, unit = "pt")
    )

ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 16,
    height   = 9,
    units    = "in",
    dpi      = 300
)
