#' anyplot.ai
#' datamatrix-basic: Basic Data Matrix 2D Barcode
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 90/100 | Created: 2026-05-20

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# Theme tokens
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Barcode module colors (data colors — constant across themes)
CELL_DARK  <- "#1A1A17"
CELL_LIGHT <- "#FAF8F1"

# Data Matrix parameters
N  <- 16L   # 16x16 symbol (ECC 200)
QZ <- 2L    # quiet zone width in cells

# Build barcode matrix (row 1 = top, col 1 = left)
mat <- matrix(0L, nrow = N, ncol = N)

# Interior: pseudo-encoded data cells
mat[2:(N - 1), 2:(N - 1)] <- matrix(
  sample(0:1, (N - 2L)^2, replace = TRUE),
  nrow = N - 2L
)

# Finder pattern (L-shape): left column and bottom row — all dark
mat[, 1L] <- 1L
mat[N, ]  <- 1L

# Timing patterns: top row (col 1 = dark) and right column (row N = dark)
mat[1L, ] <- as.integer(seq_len(N) %% 2L == 1L)
mat[, N]  <- as.integer(seq_len(N) %% 2L == N %% 2L)

# Embed barcode in quiet zone
N_total    <- N + 2L * QZ
padded_mat <- matrix(0L, nrow = N_total, ncol = N_total)
padded_mat[(QZ + 1L):(QZ + N), (QZ + 1L):(QZ + N)] <- mat

# Tidy data frame (flip y so matrix row 1 appears at the top of the plot)
df <- expand.grid(col = seq_len(N_total), row = seq_len(N_total)) %>%
  mutate(
    value = padded_mat[cbind(row, col)],
    x     = col,
    y     = N_total + 1L - row
  )

# Plot
p <- ggplot(df, aes(x = x, y = y, fill = factor(value))) +
  geom_tile(color = NA) +
  scale_fill_manual(
    values = c("0" = CELL_LIGHT, "1" = CELL_DARK),
    guide  = "none"
  ) +
  coord_fixed(ratio = 1) +
  labs(
    title    = "datamatrix-basic · r · ggplot2 · anyplot.ai",
    subtitle = 'Content: "MED-DEVICE:SN-2024-08751"  |  16x16  |  ECC 200'
  ) +
  theme_void() +
  theme(
    plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG),
    plot.title      = element_text(
      color  = INK,      size   = 12, face = "bold",
      hjust  = 0.5,      margin = margin(b = 4)
    ),
    plot.subtitle   = element_text(
      color  = INK_SOFT, size   = 9,
      hjust  = 0.5,      margin = margin(b = 16)
    ),
    plot.margin     = margin(24, 24, 24, 24)
  )

# Save (square canvas: 6 in x 6 in x 400 dpi = 2400x2400 px)
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
