#' anyplot.ai
#' chessboard-pieces: Chess Board with Pieces for Position Diagrams
#' Library: ggplot2 4.0.1 | R 4.4.1
#' Quality: 86/100 | Updated: 2026-11-17

library(ggplot2)
library(dplyr)
library(ragg)

# Theme tokens
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Board and piece colors are data colors: identical in both themes
LIGHT_SQUARE <- "#F0D9B5"
DARK_SQUARE  <- "#A8794F"
WHITE_PIECE  <- "#FFFFFF"
BLACK_PIECE  <- "#1A1A17"

# Columns: set these to your table's column names
SQUARE <- "square"  # role: category (algebraic notation, e.g. e4)
PIECE  <- "piece"   # role: category (K/Q/R/B/N/P white, k/q/r/b/n/p black)

# Data: replace this block with your own position, e.g. Scholar's Mate or a puzzle
set.seed(42)
pieces <- c(
  a1 = "R", b1 = "N", c1 = "B", d1 = "Q", e1 = "K", f1 = "B", g1 = "N", h1 = "R",
  a2 = "P", b2 = "P", c2 = "P", d2 = "P", e2 = "P", f2 = "P", g2 = "P", h2 = "P",
  a7 = "p", b7 = "p", c7 = "p", d7 = "p", e7 = "p", f7 = "p", g7 = "p", h7 = "p",
  a8 = "r", b8 = "n", c8 = "b", d8 = "q", e8 = "k", f8 = "b", g8 = "n", h8 = "r"
)
df <- tibble::tibble(
  !!SQUARE := names(pieces),
  !!PIECE  := unname(pieces)
)

# Plot: reads only df and the constants above
files <- letters[1:8]
board <- expand.grid(col = 1:8, row = 1:8) |>
  mutate(light = (col + row) %% 2 == 1)  # h1 (col 8, row 1) is a light square

# Solid glyphs (U+265A-265F) carry the piece color; outline glyphs (U+2654-2659)
# drawn on top give white pieces a dark contour on light squares
solid_glyph   <- c(k = "♚", q = "♛", r = "♜", b = "♝", n = "♞", p = "♟")
outline_glyph <- c(k = "♔", q = "♕", r = "♖", b = "♗", n = "♘", p = "♙")

placed <- df |>
  mutate(
    col   = match(substr(.data[[SQUARE]], 1, 1), files),
    row   = as.integer(substr(.data[[SQUARE]], 2, 2)),
    kind  = tolower(.data[[PIECE]]),
    white = .data[[PIECE]] != kind,
    solid = solid_glyph[kind],
    ink   = ifelse(white, WHITE_PIECE, BLACK_PIECE)
  )

PIECE_SIZE <- 11  # geom_text size in mm: about 70% of a square

p <- ggplot() +
  geom_tile(data = board, aes(x = col, y = row, fill = light), color = NA) +
  scale_fill_manual(values = c(`TRUE` = LIGHT_SQUARE, `FALSE` = DARK_SQUARE), guide = "none") +
  geom_text(data = placed, aes(x = col, y = row, label = solid, color = ink),
            size = PIECE_SIZE, family = "DejaVu Sans") +
  geom_text(data = filter(placed, white), aes(x = col, y = row, label = outline_glyph[kind]),
            size = PIECE_SIZE, family = "DejaVu Sans", color = BLACK_PIECE) +
  scale_color_identity() +
  scale_x_continuous(breaks = 1:8, labels = files, expand = c(0, 0)) +
  scale_y_continuous(breaks = 1:8, labels = as.character(1:8), expand = c(0, 0)) +
  coord_fixed(xlim = c(0.5, 8.5), ylim = c(0.5, 8.5)) +
  labs(title = "chessboard-pieces · r · ggplot2 · anyplot.ai", x = NULL, y = NULL) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid       = element_blank(),
    axis.text        = element_text(color = INK_SOFT, size = 12),
    axis.ticks       = element_blank(),
    plot.title       = element_text(color = INK, size = 13, face = "bold", hjust = 0.5),
    plot.margin      = margin(12, 12, 12, 12)
  )

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
