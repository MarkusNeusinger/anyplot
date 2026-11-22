#' anyplot.ai
#' renko-basic: Basic Renko Chart
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 80/100 | Updated: 2026-11-22

library(ggplot2)
library(dplyr)
library(ragg)

# --- Theme tokens -----------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette: position 1 for bullish, position 5 (semantic red) for bearish
BULL <- "#009E73"
BEAR <- "#AE3030"

# --- Columns ----------------------------------------------------------------
DATE  <- "Date"          # role: time
CLOSE <- "Close ($)"     # role: value
BRICK <- "Brick index"   # role: x
LOW   <- "Brick low ($)"   # role: ymin
HIGH  <- "Brick high ($)"  # role: ymax
MOVE  <- "Direction"     # role: group

BRICK_SIZE <- 1.0

# --- Data -------------------------------------------------------------------
set.seed(42)
n <- 250
prices <- tibble::tibble(
  !!DATE  := seq.Date(as.Date("2024-01-01"), length.out = n, by = "day"),
  !!CLOSE := 100 + cumsum(rnorm(n, 0, 0.8))
)

# Renko construction: a brick is added only when the close moves one full brick
# beyond the top (up) or bottom (down) of the last brick.
build_renko <- function(close, brick_size) {
  top <- bottom <- floor(close[1] / brick_size) * brick_size
  lows <- highs <- numeric(0)
  dirs <- character(0)
  for (p in close) {
    while (p >= top + brick_size) {
      lows <- c(lows, top)
      highs <- c(highs, top + brick_size)
      dirs <- c(dirs, "Bullish")
      top <- top + brick_size
      bottom <- top - brick_size
    }
    while (p <= bottom - brick_size) {
      lows <- c(lows, bottom - brick_size)
      highs <- c(highs, bottom)
      dirs <- c(dirs, "Bearish")
      bottom <- bottom - brick_size
      top <- bottom + brick_size
    }
  }
  tibble::tibble(
    !!BRICK := seq_along(lows),
    !!LOW   := lows,
    !!HIGH  := highs,
    !!MOVE  := dirs
  )
}

df <- build_renko(prices[[CLOSE]], BRICK_SIZE)

# --- Plot -------------------------------------------------------------------
p <- ggplot(df) +
  geom_rect(
    aes(
      xmin = .data[[BRICK]] - 0.42, xmax = .data[[BRICK]] + 0.42,
      ymin = .data[[LOW]] + 0.03, ymax = .data[[HIGH]] - 0.03,
      fill = .data[[MOVE]]
    )
  ) +
  scale_fill_manual(values = c("Bullish" = BULL, "Bearish" = BEAR), guide = "none") +
  scale_x_continuous(breaks = scales::breaks_pretty(n = 8)) +
  labs(
    title = "renko-basic · r · ggplot2 · anyplot.ai",
    x = BRICK,
    y = "Price ($)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK, linewidth = 0.1),
    panel.grid.minor = element_blank(),
    axis.title       = element_text(color = INK, size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    plot.title       = element_text(color = INK, size = 12),
    legend.position  = "none"
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
