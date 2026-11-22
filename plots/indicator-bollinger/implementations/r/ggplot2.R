#' anyplot.ai
#' indicator-bollinger: Bollinger Bands Indicator Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 90/100 | Created: 2026-05-17

library(ggplot2)
library(ragg)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Columns ----------------------------------------------------------------
DATE  <- "Date"            # role: x
CLOSE <- "Close ($)"       # role: price
SMA   <- "20-day SMA ($)"  # role: middle band
UPPER <- "Upper band ($)"  # role: upper band
LOWER <- "Lower band ($)"  # role: lower band

# --- Data -------------------------------------------------------------------
set.seed(42)
n_periods  <- 150
sma_period <- 20
band_width <- 2
price <- 100 + cumsum(rnorm(n_periods, mean = 0.15, sd = 1.2))
window_start <- pmax(seq_len(n_periods) - sma_period + 1, 1)
sma <- vapply(seq_len(n_periods), function(i) mean(price[window_start[i]:i]), numeric(1))
std_dev <- vapply(seq_len(n_periods), function(i) sd(price[window_start[i]:i]), numeric(1))

df <- tibble::tibble(
  !!DATE  := seq.Date(from = as.Date("2024-01-01"), by = "1 day", length.out = n_periods),
  !!CLOSE := price,
  !!SMA   := sma,
  !!UPPER := sma + band_width * std_dev,
  !!LOWER := sma - band_width * std_dev
)

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = .data[[DATE]])) +
  geom_ribbon(aes(ymin = .data[[LOWER]], ymax = .data[[UPPER]]),
              fill = IMPRINT_PALETTE[1], alpha = 0.15) +
  geom_line(aes(y = .data[[UPPER]]), color = IMPRINT_PALETTE[1], linewidth = 0.4, alpha = 0.6) +
  geom_line(aes(y = .data[[LOWER]]), color = IMPRINT_PALETTE[1], linewidth = 0.4, alpha = 0.6) +
  geom_line(aes(y = .data[[SMA]]), color = IMPRINT_PALETTE[1], linewidth = 0.6,
            linetype = "dashed", alpha = 0.8) +
  geom_line(aes(y = .data[[CLOSE]]), color = IMPRINT_PALETTE[1], linewidth = 0.9) +
  scale_x_date(date_labels = "%b") +
  labs(
    title = "indicator-bollinger · r · ggplot2 · anyplot.ai",
    x = DATE,
    y = "Price ($)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK_SOFT, linewidth = 0.2),
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.title       = element_text(color = INK, size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    plot.title       = element_text(color = INK, size = 12, face = "plain"),
    plot.margin      = unit(c(6, 6, 6, 6), "mm")
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
