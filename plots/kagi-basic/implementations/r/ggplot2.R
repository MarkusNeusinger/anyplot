#' anyplot.ai
#' kagi-basic: Basic Kagi Chart
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 82/100 | Updated: 2026-11-22

library(ggplot2)
library(dplyr)
library(tibble)
library(ragg)

# --- Theme tokens (Imprint palette) -------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")
COLOR_YANG <- IMPRINT_PALETTE[1]  # thick, rising above the previous shoulder
COLOR_YIN  <- IMPRINT_PALETTE[5]  # thin, falling below the previous waist

# Constants
REVERSAL_PCT <- 0.04   # direction changes after a 4% move against the line
WIDTH_YANG   <- 2.4    # line width in mm
WIDTH_YIN    <- 0.8

# Columns: set these to your table's column names
DATE  <- "date"   # role: time
CLOSE <- "close"  # role: value

# Data: replace this block with your own table, for example df <- read.csv("prices.csv")
set.seed(42)
n_days <- 150
df <- tibble::tibble(
  !!DATE  := seq(as.Date("2025-10-01"), by = "day", length.out = n_days),
  !!CLOSE := 100 * exp(cumsum(rnorm(n_days, mean = 0.003, sd = 0.02)))
)

# --- Kagi construction ----------------------------------------------------------
# One vertical line per column: it extends while price keeps going the same way and
# a new column starts once price reverses by REVERSAL_PCT of the line's end.
prices <- df[[CLOSE]]
cols <- list()
dir <- NA_character_
start <- prices[1]
end <- prices[1]
for (p_i in prices[-1]) {
  if (is.na(dir)) {
    if (p_i >= start * (1 + REVERSAL_PCT)) { dir <- "up"; end <- p_i }
    else if (p_i <= start * (1 - REVERSAL_PCT)) { dir <- "down"; end <- p_i }
  } else if (dir == "up") {
    if (p_i > end) {
      end <- p_i
    } else if (p_i <= end * (1 - REVERSAL_PCT)) {
      cols[[length(cols) + 1]] <- list(dir = dir, from = start, to = end)
      start <- end; end <- p_i; dir <- "down"
    }
  } else {
    if (p_i < end) {
      end <- p_i
    } else if (p_i >= end * (1 + REVERSAL_PCT)) {
      cols[[length(cols) + 1]] <- list(dir = dir, from = start, to = end)
      start <- end; end <- p_i; dir <- "up"
    }
  }
}
cols[[length(cols) + 1]] <- list(dir = dir, from = start, to = end)  # open last line

# Split every column where it breaks the previous shoulder (turns yang) or waist
# (turns yin), then join consecutive columns with horizontal connectors.
state <- if (cols[[1]]$dir == "up") "yang" else "yin"
pieces <- list()
for (k in seq_along(cols)) {
  cl <- cols[[k]]
  if (k > 1) {
    prev_level <- cols[[k - 1]]$from  # previous shoulder (going up) or waist (going down)
    if (cl$dir == "up" && cl$to > prev_level) {
      lo <- max(cl$from, min(prev_level, cl$to))
      pieces[[length(pieces) + 1]] <- tibble(x = k, y = cl$from, yend = lo, state = state)
      pieces[[length(pieces) + 1]] <- tibble(x = k, y = lo, yend = cl$to, state = "yang")
      state <- "yang"
    } else if (cl$dir == "down" && cl$to < prev_level) {
      hi <- min(cl$from, max(prev_level, cl$to))
      pieces[[length(pieces) + 1]] <- tibble(x = k, y = cl$from, yend = hi, state = state)
      pieces[[length(pieces) + 1]] <- tibble(x = k, y = hi, yend = cl$to, state = "yin")
      state <- "yin"
    } else {
      pieces[[length(pieces) + 1]] <- tibble(x = k, y = cl$from, yend = cl$to, state = state)
    }
  } else {
    pieces[[length(pieces) + 1]] <- tibble(x = k, y = cl$from, yend = cl$to, state = state)
  }
  if (k < length(cols)) {
    pieces[[length(pieces) + 1]] <- tibble(x = k, y = cl$to, yend = cl$to, state = state, xend = k + 1)
  }
}
kagi <- bind_rows(pieces) |>
  mutate(xend = coalesce(xend, x), state = factor(state, levels = c("yang", "yin")))

# --- Plot -----------------------------------------------------------------------
p <- ggplot(kagi) +
  geom_segment(
    aes(x = x, xend = xend, y = y, yend = yend, color = state, linewidth = state),
    lineend = "square", show.legend = FALSE
  ) +
  scale_color_manual(values = c(yang = COLOR_YANG, yin = COLOR_YIN)) +
  scale_linewidth_manual(values = c(yang = WIDTH_YANG, yin = WIDTH_YIN)) +
  scale_x_continuous(breaks = scales::breaks_pretty(n = 8), expand = expansion(add = 0.6)) +
  labs(
    title = "kagi-basic · r · ggplot2 · anyplot.ai",
    x = "Line index (4% reversal)",
    y = "Closing price (USD)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK_SOFT, linewidth = 0.1),
    panel.grid.minor = element_blank(),
    axis.title       = element_text(color = INK, size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    plot.title       = element_text(color = INK, size = 12)
  )

# --- Save -----------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot = p,
  device = ragg::agg_png,
  width = 8,
  height = 4.5,
  units = "in",
  dpi = 400
)
