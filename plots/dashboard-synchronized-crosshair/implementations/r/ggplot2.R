#' anyplot.ai
#' dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 89/100 | Created: 2026-05-23

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

IMPRINT <- c(
    "#009E73", "#C475FD", "#AE3030", "#4467A3",
    "#99B314", "#954477", "#BD8233"
)

# 200 trading days of synthetic stock data
n        <- 200
all_days <- seq.Date(as.Date("2024-01-02"), by = "day", length.out = 300)
dates    <- all_days[!weekdays(all_days) %in% c("Saturday", "Sunday")][seq_len(n)]

log_ret <- rnorm(n, mean = 0.0005, sd = 0.015)
price   <- 100 * cumprod(1 + log_ret)

vol_base <- exp(rnorm(n, log(2.5), 0.45))
volume   <- vol_base * (1 + 4 * abs(log_ret) / max(abs(log_ret)))

# RSI 14-period (simple moving average approximation)
delta <- c(0, diff(price))
gains  <- pmax(delta, 0)
losses <- pmax(-delta, 0)
avg_g  <- as.numeric(stats::filter(gains,  rep(1 / 14, 14), sides = 1))
avg_l  <- as.numeric(stats::filter(losses, rep(1 / 14, 14), sides = 1))
rs     <- ifelse(avg_l == 0, Inf, avg_g / avg_l)
rsi    <- 100 - 100 / (1 + rs)

df <- tibble::tibble(
    date   = rep(dates, 3),
    value  = c(price, volume, rsi),
    metric = factor(
        rep(c("Price (USD)", "Volume (M)", "RSI (14)"), each = n),
        levels = c("Price (USD)", "Volume (M)", "RSI (14)")
    )
)

metric_colors <- c(
    "Price (USD)" = IMPRINT[1],
    "Volume (M)"  = IMPRINT[2],
    "RSI (14)"    = IMPRINT[3]
)

event_date <- dates[120]

p <- ggplot(dplyr::filter(df, !is.na(value)), aes(x = date, y = value)) +
    geom_vline(
        xintercept = as.numeric(event_date),
        color      = INK_MUTED,
        linewidth  = 0.5,
        linetype   = "dashed"
    ) +
    geom_line(aes(color = metric), linewidth = 1.1) +
    geom_text(
        data = tibble::tibble(
            date   = event_date,
            y_pos  = Inf,
            metric = factor("Price (USD)", levels = c("Price (USD)", "Volume (M)", "RSI (14)"))
        ),
        aes(x = date, y = y_pos, label = "Event"),
        color       = INK_MUTED,
        size        = 2.5,
        hjust       = -0.15,
        vjust       = 1.5,
        inherit.aes = FALSE
    ) +
    facet_wrap(~metric, ncol = 1, scales = "free_y", strip.position = "right") +
    scale_color_manual(values = metric_colors, guide = "none") +
    scale_x_date(
        date_labels = "%b '%y",
        date_breaks = "2 months",
        expand      = expansion(mult = 0.01)
    ) +
    scale_y_continuous(labels = label_number(accuracy = 0.1)) +
    labs(
        title    = "dashboard-synchronized-crosshair · r · ggplot2 · anyplot.ai",
        subtitle = "Tech stock 2024 — price, volume & RSI across 200 trading days",
        x        = NULL,
        y        = NULL
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background = element_rect(fill = PAGE_BG, color = NA),
        panel.grid.major = element_line(
            color     = adjustcolor(INK_SOFT, alpha.f = 0.3),
            linewidth = 0.2
        ),
        panel.grid.minor = element_blank(),
        panel.border        = element_blank(),
        axis.line.x.bottom  = element_line(color = INK_SOFT, linewidth = 0.3),
        axis.line.y.left    = element_line(color = INK_SOFT, linewidth = 0.3),
        panel.spacing    = unit(0.4, "cm"),
        axis.text        = element_text(color = INK_SOFT, size = 8),
        axis.title       = element_text(color = INK, size = 10),
        plot.title       = element_text(
            color  = INK,
            size   = 12,
            face   = "bold",
            margin = margin(b = 4)
        ),
        plot.subtitle    = element_text(
            color  = INK_SOFT,
            size   = 9,
            margin = margin(b = 8)
        ),
        plot.margin      = margin(t = 12, r = 8, b = 8, l = 8),
        strip.text       = element_text(color = INK, size = 9, face = "bold"),
        strip.background = element_rect(
            fill      = ELEVATED_BG,
            color     = INK_SOFT,
            linewidth = 0.3
        ),
        strip.placement  = "outside"
    )

ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 8,
    height   = 4.5,
    units    = "in",
    dpi      = 400
)
