#' anyplot.ai
#' qrcode-basic: Basic QR Code Generator
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 90/100 | Created: 2026-06-24

library(ggplot2)
library(ragg)
library(qrcode)

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# QR module colors — high contrast ink/paper tones for reliable scanning
MODULE_DARK  <- INK      # encodes data bits
MODULE_LIGHT <- PAGE_BG  # background (quiet) modules

# Content to encode
encode_url <- "https://anyplot.ai"

# Generate QR code (error correction level M = 15%)
# Returns a logical matrix: TRUE = dark module, FALSE = light module
# The package includes a 3-module quiet zone border in the matrix
qr     <- qr_code(encode_url, ecl = "M")
qr_mat <- as.matrix(qr)
n      <- nrow(qr_mat)

# Build tidy data frame for geom_tile
# as.vector(t(m)) = row-major order: m[1,1], m[1,2], ..., m[n,n]
# y is flipped so matrix row 1 appears at the top of the plot
qr_df <- data.frame(
  x    = rep(seq_len(n), times = n),
  y    = rep(seq(n, 1L),  each  = n),
  dark = as.character(as.vector(t(qr_mat)))
)

# Title fontsize: baseline 12pt for ~67-char title; scale down if longer
plot_title <- "qrcode-basic · r · ggplot2 · anyplot.ai"
title_n    <- nchar(plot_title)
title_size <- if (title_n > 67) max(round(12L * 67L / title_n), 8L) else 12L

# Build plot — square canvas suits the symmetric QR grid
p <- ggplot(qr_df, aes(x = x, y = y, fill = dark)) +
  geom_tile(color = NA, linewidth = 0) +
  scale_fill_manual(
    values = c("TRUE" = MODULE_DARK, "FALSE" = MODULE_LIGHT),
    guide  = "none"
  ) +
  coord_fixed() +
  labs(
    title    = plot_title,
    subtitle = encode_url,
    x        = NULL,
    y        = NULL
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.border     = element_blank(),
    axis.text        = element_blank(),
    axis.ticks       = element_blank(),
    axis.title       = element_blank(),
    plot.title       = element_text(
      color  = INK,
      size   = title_size,
      hjust  = 0.5,
      face   = "bold"
    ),
    plot.subtitle    = element_text(
      color  = INK_SOFT,
      size   = 9,
      hjust  = 0.5
    ),
    plot.margin      = margin(20, 20, 20, 20)
  )

# Save — square PNG (2400 × 2400 px at dpi = 400)
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
