#' anyplot.ai
#' indicator-sma: Simple Moving Average (SMA) Indicator Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-05-19

library(ggplot2)
library(tidyr)
library(scales)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants
SMA_PERIODS <- c(20L, 50L, 200L)  # standard short, medium and long windows for daily data

# Columns: set these to your table's column names
DATE   <- "Date"          # role: date
CLOSE  <- "Price"         # role: close
SMA_S  <- "SMA 20"        # role: sma_short
SMA_M  <- "SMA 50"        # role: sma_medium
SMA_L  <- "SMA 200"       # role: sma_long

# Data: replace this block with your own table, for example df <- read.csv("prices.csv", check.names = FALSE)
set.seed(42)
all_dates <- seq(as.Date("2022-01-03"), by = "day", length.out = 700L)
trading_dates <- all_dates[!weekdays(all_dates) %in% c("Saturday", "Sunday")][seq_len(500L)]
close_price <- 148.0 * cumprod(1 + rnorm(500L, mean = 0.0004, sd = 0.016))

# Trailing mean over a full window; the first k - 1 values stay NA
trailing_mean <- function(x, k) as.numeric(stats::filter(x, rep(1 / k, k), sides = 1))

df <- tibble::tibble(
  !!DATE  := trading_dates,
  !!CLOSE := close_price,
  !!SMA_S := trailing_mean(close_price, SMA_PERIODS[1]),
  !!SMA_M := trailing_mean(close_price, SMA_PERIODS[2]),
  !!SMA_L := trailing_mean(close_price, SMA_PERIODS[3])
)

# Plot: reads only df and the constants above
series <- c(CLOSE, SMA_S, SMA_M, SMA_L)
df_long <- tidyr::pivot_longer(df, cols = all_of(series), names_to = "series", values_to = "value")
df_long$series <- factor(df_long$series, levels = series)

series_colors <- setNames(IMPRINT_PALETTE[seq_along(series)], series)
series_widths <- setNames(c(1.1, rep(0.7, length(series) - 1L)), series)

p <- ggplot(df_long, aes(x = .data[[DATE]], y = value, color = series, linewidth = series)) +
  geom_line(na.rm = TRUE) +
  scale_color_manual(values = series_colors) +
  scale_linewidth_manual(values = series_widths) +
  scale_x_date(date_breaks = "3 months", date_labels = "%b %Y") +
  scale_y_continuous(labels = scales::dollar_format(prefix = "$", accuracy = 1)) +
  guides(linewidth = "none") +
  labs(
    title = "Daily Close Price · indicator-sma · r · ggplot2 · anyplot.ai",
    x     = DATE,
    y     = "Price (USD)",
    color = NULL
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK_SOFT, linewidth = 0.15),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    axis.title         = element_text(color = INK,      size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.text.x        = element_text(angle = 30, hjust = 1, vjust = 1),
    axis.line.x        = element_line(color = INK_SOFT, linewidth = 0.25),
    axis.line.y        = element_line(color = INK_SOFT, linewidth = 0.25),
    plot.title         = element_text(color = INK,      size = 12, face = "bold"),
    legend.background  = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.25),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.key         = element_rect(fill = NA),
    legend.position    = "top",
    legend.direction   = "horizontal"
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
