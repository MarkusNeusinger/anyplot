#' anyplot.ai
#' chessboard-basic: Chess Board Grid Visualization
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-05-17

library(ggplot2)
library(dplyr)
library(ragg)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# --- Data -------------------------------------------------------------------
# Create 8x8 chessboard with algebraic notation
# Columns: a-h (1-8), Rows: 1-8
# Light square at h1 and a8 (standard chess convention)

board <- expand.grid(
  col = 1:8,
  row = 1:8
) %>%
  mutate(
    # Alternate colors: (col + row) %% 2 determines light/dark
    # h1 (col=8, row=1) should be light: (8+1)%%2 = 1 (light)
    is_light = (col + row) %% 2 == 1,
    square_color = if_else(is_light, "#E8D5B7", "#8B7355")
  )

# --- Plot -------------------------------------------------------------------
p <- ggplot(board, aes(x = col, y = row)) +
  geom_tile(aes(fill = square_color), color = NA, width = 1, height = 1) +
  scale_fill_identity() +
  scale_x_continuous(
    breaks = 1:8,
    labels = c("a", "b", "c", "d", "e", "f", "g", "h"),
    limits = c(0.5, 8.5),
    expand = c(0, 0)
  ) +
  scale_y_continuous(
    breaks = 1:8,
    labels = as.character(1:8),
    limits = c(0.5, 8.5),
    expand = c(0, 0)
  ) +
  coord_fixed(ratio = 1) +
  labs(
    title = "chessboard-basic · ggplot2 · anyplot.ai",
    x = NULL,
    y = NULL
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    panel.border      = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.5),
    axis.title        = element_blank(),
    axis.text.x       = element_text(color = INK, size = 20),
    axis.text.y       = element_text(color = INK, size = 20),
    plot.title        = element_text(color = INK, size = 24, hjust = 0.5),
    plot.margin       = unit(c(20, 20, 20, 20), "pt")
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 9,
  height   = 9,
  units    = "in",
  dpi      = 300
)
