#' anyplot.ai
#' indicator-bollinger: Bollinger Bands Indicator Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 90/100 | Created: 2026-05-17

library(ggplot2)
library(dplyr)
library(tidyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT   <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                 "#AE3030", "#2ABCCD", "#954477")

# --- Data -------------------------------------------------------------------
n_periods <- 150
dates <- seq.Date(from = as.Date("2024-01-01"), by = "1 day", length.out = n_periods)

price <- 100 + cumsum(rnorm(n_periods, mean = 0.15, sd = 1.2))

sma_period <- 20
sma <- numeric(n_periods)
for (i in 1:n_periods) {
  if (i < sma_period) {
    sma[i] <- mean(price[1:i])
  } else {
    sma[i] <- mean(price[(i - sma_period + 1):i])
  }
}

std_dev <- numeric(n_periods)
for (i in 1:n_periods) {
  if (i < sma_period) {
    std_dev[i] <- sd(price[1:i])
  } else {
    std_dev[i] <- sd(price[(i - sma_period + 1):i])
  }
}

upper_band <- sma + 2 * std_dev
lower_band <- sma - 2 * std_dev

df <- data.frame(
  date = dates,
  close = price,
  sma = sma,
  upper_band = upper_band,
  lower_band = lower_band
)

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = date)) +
  geom_ribbon(aes(ymin = lower_band, ymax = upper_band),
              fill = IMPRINT[1], alpha = 0.15) +
  geom_line(aes(y = upper_band), color = IMPRINT[1], linewidth = 0.6,
            linetype = "solid", alpha = 0.6) +
  geom_line(aes(y = lower_band), color = IMPRINT[1], linewidth = 0.6,
            linetype = "solid", alpha = 0.6) +
  geom_line(aes(y = sma), color = IMPRINT[1], linewidth = 0.8,
            linetype = "dashed", alpha = 0.7) +
  geom_line(aes(y = close), color = IMPRINT[1], linewidth = 1.2) +
  labs(
    title = "indicator-bollinger · ggplot2 · anyplot.ai",
    x = "Date",
    y = "Price ($)"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK_SOFT, linewidth = 0.3),
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.title       = element_text(color = INK, size = 20),
    axis.text        = element_text(color = INK_SOFT, size = 16),
    plot.title       = element_text(color = INK, size = 24, face = "plain"),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.text      = element_text(color = INK_SOFT, size = 16),
    plot.margin      = unit(c(12, 12, 12, 12), "mm")
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
