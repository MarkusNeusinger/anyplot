#' anyplot.ai
#' depth-order-book: Order Book Depth Chart
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-06-15

library(ggplot2)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens
THEME     <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG   <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK       <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT  <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# Imprint palette — semantic: green = bids (buy), red = asks (sell)
BID_COLOR <- "#009E73"  # Imprint position 1 (brand green) — first series
ASK_COLOR <- "#AE3030"  # Imprint position 5 (semantic anchor — sell/loss)
GRID_COL  <- adjustcolor(INK, alpha.f = 0.12)

# Market parameters: BTC/USD snapshot near $60,000
mid_price   <- 60000
half_spread <- 5        # $10 total spread
n_levels    <- 50
tick_size   <- 5        # $5 between price levels

# Price grids — index 1 = best (closest to mid), index 50 = worst
bid_prices <- mid_price - half_spread - (seq_len(n_levels) - 1) * tick_size
ask_prices <- mid_price + half_spread + (seq_len(n_levels) - 1) * tick_size

# Individual order sizes with mild trend (deeper levels accumulate more liquidity)
qty_trend <- 1 + (seq_len(n_levels) - 1) * 0.04
bid_qtys  <- rlnorm(n_levels, meanlog = 1.5, sdlog = 0.5) * qty_trend
ask_qtys  <- rlnorm(n_levels, meanlog = 1.5, sdlog = 0.5) * qty_trend

# Insert liquidity walls — large resting orders that act as support/resistance
bid_qtys[12] <- bid_qtys[12] * 7
ask_qtys[18] <- ask_qtys[18] * 5

# Cumulative volume from mid price outward
bid_cum <- cumsum(bid_qtys)
ask_cum <- cumsum(ask_qtys)

# Build a closed step polygon for geom_polygon (fill)
make_step_poly <- function(prices, cums) {
  n  <- length(prices)
  xs <- prices[1]
  ys <- 0
  for (i in seq_len(n)) {
    xs <- c(xs, prices[i])
    ys <- c(ys, cums[i])
    if (i < n) {
      xs <- c(xs, prices[i + 1])
      ys <- c(ys, cums[i])
    }
  }
  xs <- c(xs, prices[n], prices[1])
  ys <- c(ys, 0, 0)
  data.frame(x = xs, y = ys)
}

# Build an open step path for geom_path (outline)
make_step_path <- function(prices, cums) {
  n  <- length(prices)
  xs <- prices[1]
  ys <- 0
  for (i in seq_len(n)) {
    xs <- c(xs, prices[i])
    ys <- c(ys, cums[i])
    if (i < n) {
      xs <- c(xs, prices[i + 1])
      ys <- c(ys, cums[i])
    }
  }
  data.frame(x = xs, y = ys)
}

bid_poly <- make_step_poly(bid_prices, bid_cum)
ask_poly <- make_step_poly(ask_prices, ask_cum)
bid_path <- make_step_path(bid_prices, bid_cum)
ask_path <- make_step_path(ask_prices, ask_cum)

# Annotation
max_cum    <- max(max(bid_cum), max(ask_cum))
label_text <- sprintf("Mid: $%s\nSpread: $%d",
                      format(mid_price, big.mark = ",", scientific = FALSE),
                      half_spread * 2)

# Title — count chars to compute size (baseline 67 chars = 12 pt)
plot_title <- "BTC/USD Order Book · depth-order-book · r · ggplot2 · anyplot.ai"
title_size <- max(8, round(12 * 67 / max(nchar(plot_title), 67)))

# Plot
p <- ggplot() +
  geom_polygon(data = bid_poly, aes(x = x, y = y),
               fill = BID_COLOR, color = NA, alpha = 0.22) +
  geom_polygon(data = ask_poly, aes(x = x, y = y),
               fill = ASK_COLOR, color = NA, alpha = 0.22) +
  geom_path(data = bid_path, aes(x = x, y = y),
            color = BID_COLOR, linewidth = 0.85) +
  geom_path(data = ask_path, aes(x = x, y = y),
            color = ASK_COLOR, linewidth = 0.85) +
  geom_vline(xintercept = mid_price,
             linetype = "dashed", color = INK_SOFT, linewidth = 0.5) +
  annotate("text", x = mid_price, y = max_cum * 0.90,
           label = label_text, color = INK_MUTED, size = 2.8,
           hjust = 0.5, lineheight = 1.3) +
  scale_x_continuous(
    labels = label_dollar(accuracy = 1),
    breaks = seq(59750, 60250, by = 100),
    expand = expansion(mult = 0.01)
  ) +
  scale_y_continuous(
    labels = label_comma(accuracy = 1),
    limits = c(0, max_cum * 1.12),
    expand = expansion(mult = c(0, 0))
  ) +
  labs(
    title = plot_title,
    x     = "Price (USD)",
    y     = "Cumulative Volume (BTC)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = GRID_COL, linewidth = 0.3),
    panel.grid.minor = element_blank(),
    panel.border     = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.4),
    axis.title       = element_text(color = INK,     size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    axis.text.x      = element_text(color = INK_SOFT, size = 8,
                                    angle = 30, hjust = 1),
    plot.title       = element_text(color = INK, size = title_size,
                                    face = "bold", margin = margin(b = 8)),
    plot.margin      = margin(t = 12, r = 16, b = 8, l = 8)
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
