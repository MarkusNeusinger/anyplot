#' anyplot.ai
#' barcode-ean13: EAN-13 Barcode
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 84/100 | Created: 2026-05-21

library(ggplot2)
library(ragg)

THEME   <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK     <- if (THEME == "light") "#1A1A17" else "#F0EFE8"

# EAN-13 encoding tables
L_CODES <- list(
  "0" = c(0,0,0,1,1,0,1), "1" = c(0,0,1,1,0,0,1),
  "2" = c(0,0,1,0,0,1,1), "3" = c(0,1,1,1,1,0,1),
  "4" = c(0,1,0,0,0,1,1), "5" = c(0,1,1,0,0,0,1),
  "6" = c(0,1,0,1,1,1,1), "7" = c(0,1,1,1,0,1,1),
  "8" = c(0,1,1,0,1,1,1), "9" = c(0,0,0,1,0,1,1)
)

G_CODES <- list(
  "0" = c(0,1,0,0,1,1,1), "1" = c(0,1,1,0,0,1,1),
  "2" = c(0,0,1,1,0,1,1), "3" = c(0,1,0,0,0,0,1),
  "4" = c(0,0,1,1,1,0,1), "5" = c(0,1,1,1,0,0,1),
  "6" = c(0,0,0,0,1,0,1), "7" = c(0,0,1,0,0,0,1),
  "8" = c(0,0,0,1,0,0,1), "9" = c(0,0,1,0,1,1,1)
)

R_CODES <- list(
  "0" = c(1,1,1,0,0,1,0), "1" = c(1,1,0,0,1,1,0),
  "2" = c(1,1,0,1,1,0,0), "3" = c(1,0,0,0,0,1,0),
  "4" = c(1,0,1,1,1,0,0), "5" = c(1,0,0,1,1,1,0),
  "6" = c(1,0,1,0,0,0,0), "7" = c(1,0,0,0,1,0,0),
  "8" = c(1,0,0,1,0,0,0), "9" = c(1,1,1,0,1,0,0)
)

# Parity for left-side digits based on first digit (0 = L-code, 1 = G-code)
PARITY <- list(
  "0" = c(0,0,0,0,0,0), "1" = c(0,0,1,0,1,1),
  "2" = c(0,0,1,1,0,1), "3" = c(0,0,1,1,1,0),
  "4" = c(0,1,0,0,1,1), "5" = c(0,1,1,0,0,1),
  "6" = c(0,1,1,1,0,0), "7" = c(0,1,0,1,0,1),
  "8" = c(0,1,0,1,1,0), "9" = c(0,1,1,0,1,0)
)

ean13_check <- function(d) {
  s <- sum(d[c(1,3,5,7,9,11)]) + 3L * sum(d[c(2,4,6,8,10,12)])
  (10L - s %% 10L) %% 10L
}

build_ean13 <- function(code) {
  d <- as.integer(strsplit(code, "")[[1]])
  if (length(d) == 12L) d <- c(d, ean13_check(d))
  par  <- PARITY[[as.character(d[1])]]
  bits <- c(1L, 0L, 1L)
  for (i in seq_len(6L)) {
    ch   <- as.character(d[i + 1L])
    bits <- c(bits, if (par[i] == 0L) L_CODES[[ch]] else G_CODES[[ch]])
  }
  bits <- c(bits, 0L, 1L, 0L, 1L, 0L)
  for (i in seq_len(6L)) {
    ch   <- as.character(d[i + 7L])
    bits <- c(bits, R_CODES[[ch]])
  }
  list(bits = c(bits, 1L, 0L, 1L), digits = d)
}

# --- Data ---
result <- build_ean13("4006381333931")  # German product
bits   <- result$bits    # 95 modules
digits <- result$digits  # 13 digits

quiet     <- 9L   # quiet-zone modules on each side
bar_h     <- 40   # standard bar height
guard_ext <- 3    # guards descend this many units below y = 0

# Guard module positions (0-indexed within the 95-bit array)
guard_idx <- c(0L:2L, 45L:49L, 92L:94L)
bar_pos   <- which(bits == 1L) - 1L  # 0-indexed bar positions
is_guard  <- bar_pos %in% guard_idx

bar_df <- data.frame(
  xmin = quiet + bar_pos,
  xmax = quiet + bar_pos + 1L,
  ymin = ifelse(is_guard, -guard_ext, 0),
  ymax = bar_h
)

total_w <- quiet + 95L + quiet  # 113 modules

# Human-readable digit positions
# First digit sits in the left quiet zone
x_first <- quiet / 2
# Left  6 digits: one 7-module cell each, starting after start guard (module 12)
x_left  <- quiet + 3L + (0L:5L) * 7L + 3.5
# Right 6 digits: one 7-module cell each, starting after center guard (module 59)
x_right <- quiet + 3L + 42L + 5L + (0L:5L) * 7L + 3.5

digit_df <- data.frame(
  x     = c(x_first, x_left, x_right),
  y     = rep(-guard_ext - 2.8, 13L),
  label = as.character(digits)
)

# --- Plot ---
p <- ggplot() +
  geom_rect(
    data = bar_df,
    aes(xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax),
    fill = INK, color = NA
  ) +
  geom_text(
    data = digit_df,
    aes(x = x, y = y, label = label),
    color = INK, size = 3.5, vjust = 1, family = "sans"
  ) +
  scale_x_continuous(limits = c(0, total_w), expand = expansion(add = c(1, 1))) +
  scale_y_continuous(limits = c(-guard_ext - 13, bar_h + 5), expand = c(0, 0)) +
  labs(title = "barcode-ean13 · r · ggplot2 · anyplot.ai") +
  theme_void() +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    plot.title       = element_text(
      color = INK, size = 12, hjust = 0.5,
      margin = margin(t = 15, b = 15)
    ),
    plot.margin = margin(10, 60, 10, 60)
  )

# --- Save ---
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
