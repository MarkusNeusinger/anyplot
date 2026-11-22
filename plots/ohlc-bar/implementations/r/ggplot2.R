#' anyplot.ai
#' ohlc-bar: OHLC Bar Chart
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 83/100 | Updated: 2026-11-22

library(ggplot2)
library(dplyr)
library(ragg)

# Theme tokens
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID_COL <- if (THEME == "light") "#E8E6DC" else "#2A2824"

# Imprint palette: up bars take position 1, down bars the matte red (loss anchor)
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
DATE  <- "Date"         # role: x
OPEN  <- "Open ($)"     # role: open price
HIGH  <- "High ($)"     # role: high price
LOW   <- "Low ($)"      # role: low price
CLOSE <- "Close ($)"    # role: close price

# Data: replace this block with your own table, for example df <- read.csv("prices.csv", check.names = FALSE)
set.seed(42)
days <- seq(as.Date("2024-01-01"), by = "1 day", length.out = 70)
trading_days <- days[!weekdays(days) %in% c("Saturday", "Sunday")][1:45]
n <- length(trading_days)
close_prices <- 150 * cumprod(1 + rnorm(n, mean = 0.001, sd = 0.015))
open_prices <- close_prices + rnorm(n, mean = -0.5, sd = 0.8)
high_prices <- pmax(close_prices, close_prices + abs(rnorm(n, mean = 1.5, sd = 0.6)))
low_prices <- pmin(close_prices, close_prices - abs(rnorm(n, mean = 1.5, sd = 0.6)))
df <- tibble::tibble(
  !!DATE  := trading_days,
  !!OPEN  := open_prices,
  !!HIGH  := high_prices,
  !!LOW   := low_prices,
  !!CLOSE := close_prices
)

# Plot: reads only df and the constants above
bars <- df |>
  mutate(direction = ifelse(.data[[CLOSE]] >= .data[[OPEN]], "up", "down"))
tick <- 0.4  # half a day: long enough to read, short enough to keep neighbours apart
label_dates <- bars[[DATE]][seq(1, nrow(bars), by = 5)]

p <- ggplot(bars, aes(color = direction)) +
  geom_segment(aes(x = .data[[DATE]], xend = .data[[DATE]],
                   y = .data[[LOW]], yend = .data[[HIGH]]),
               linewidth = 0.55, lineend = "butt") +
  geom_segment(aes(x = .data[[DATE]] - tick, xend = .data[[DATE]],
                   y = .data[[OPEN]], yend = .data[[OPEN]]),
               linewidth = 0.55, lineend = "butt") +
  geom_segment(aes(x = .data[[DATE]], xend = .data[[DATE]] + tick,
                   y = .data[[CLOSE]], yend = .data[[CLOSE]]),
               linewidth = 0.55, lineend = "butt") +
  scale_color_manual(values = c(up = IMPRINT_PALETTE[1], down = IMPRINT_PALETTE[5]),
                     guide = "none") +
  scale_x_date(breaks = label_dates, date_labels = "%b %d",
               expand = expansion(add = 1.5)) +
  labs(title = "ohlc-bar · r · ggplot2 · anyplot.ai",
       x = DATE, y = "Price ($)") +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = GRID_COL, linewidth = 0.3),
    panel.grid.major.x = element_blank(),
    panel.grid.minor  = element_blank(),
    axis.ticks        = element_line(color = INK_SOFT, linewidth = 0.3),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.text.x       = element_text(angle = 45, hjust = 1, vjust = 1),
    plot.title        = element_text(color = INK, size = 12, face = "bold",
                                     margin = margin(b = 8)),
    plot.margin       = margin(12, 16, 8, 8)
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
