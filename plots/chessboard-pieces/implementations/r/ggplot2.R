#' anyplot.ai
#' chessboard-pieces: Chess Board with Pieces for Position Diagrams
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-05-17

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT   <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                 "#AE3030", "#2ABCCD", "#954477")

# --- Data: Chess board setup ------------------------------------------------

# Create board squares (8x8 grid)
board <- expand.grid(
  col = 0:7,
  row = 0:7
) %>%
  mutate(
    square_color = if_else((col + row) %% 2 == 0, "light", "dark"),
    piece = NA_character_,
    piece_color = NA_character_
  )

# Define piece positions for a sample opening position
# Using algebraic notation: 'a1' = bottom-left, 'h8' = top-right
positions <- data.frame(
  square = c(
    # White pieces
    "a1", "h1", "b1", "g1", "c1", "f1", "d1", "e1",  # back rank
    "a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2",  # pawns
    # Black pieces
    "a8", "h8", "b8", "g8", "c8", "f8", "d8", "e8",  # back rank
    "a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"   # pawns
  ),
  piece = c(
    # White
    "R", "R", "N", "N", "B", "B", "Q", "K",
    "P", "P", "P", "P", "P", "P", "P", "P",
    # Black
    "r", "r", "n", "n", "b", "b", "q", "k",
    "p", "p", "p", "p", "p", "p", "p", "p"
  )
)

# Convert algebraic notation to grid coordinates
notation_to_grid <- function(notation) {
  col <- match(substr(notation, 1, 1), letters[1:8]) - 1
  row <- as.numeric(substr(notation, 2, 2)) - 1
  data.frame(col = col, row = row)
}

# Add pieces to board
for (i in seq_len(nrow(positions))) {
  coords <- notation_to_grid(positions$square[i])
  piece_char <- positions$piece[i]
  board$piece[board$col == coords$col & board$row == coords$row] <- piece_char
  board$piece_color[board$col == coords$col & board$row == coords$row] <-
    if (piece_char %in% c("K", "Q", "R", "B", "N", "P")) "white" else "black"
}

# --- Plot: Chess board visualization ----------------------------------------

# Board square colors (chess standard: light squares, dark squares)
light_square <- "#F5E6D3"
dark_square  <- "#8B7355"

# Piece text color (contrasts with board)
piece_text_color <- "#2C2C2C"

p <- ggplot(board, aes(x = col, y = row)) +
  # Draw board squares
  geom_tile(aes(fill = square_color), color = NA) +
  scale_fill_manual(values = c("light" = light_square, "dark" = dark_square),
                    guide = "none") +

  # Draw pieces as text annotations
  geom_text(aes(label = piece, color = piece_color),
            size = 18,
            vjust = 0.5, hjust = 0.5,
            family = "DejaVu Sans") +
  scale_color_manual(
    values = c("white" = "#F5F5F5", "black" = "#1A1A1A"),
    na.value = NA,
    guide = "none"
  ) +

  # Labels and title
  labs(
    title = "chessboard-pieces · ggplot2 · anyplot.ai",
    x = "",
    y = ""
  ) +

  # Coordinate settings
  scale_x_continuous(
    breaks = 0:7,
    labels = c("a", "b", "c", "d", "e", "f", "g", "h"),
    expand = c(0, 0)
  ) +
  scale_y_continuous(
    breaks = 0:7,
    labels = c("1", "2", "3", "4", "5", "6", "7", "8"),
    expand = c(0, 0)
  ) +
  coord_fixed(ratio = 1) +

  # Theme styling
  theme_minimal(base_size = 14) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    axis.title        = element_text(color = INK, size = 20),
    axis.text         = element_text(color = INK_SOFT, size = 16),
    plot.title        = element_text(color = INK, size = 24, face = "bold"),
    axis.ticks        = element_blank(),
    plot.margin       = unit(c(1, 1, 1, 1), "cm")
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
