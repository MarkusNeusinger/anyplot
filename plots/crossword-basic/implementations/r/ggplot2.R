#' anyplot.ai
#' crossword-basic: Crossword Puzzle Grid
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 89/100 | Created: 2026-05-20

library(ggplot2)
library(ragg)

# Theme tokens
THEME   <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK     <- if (THEME == "light") "#1A1A17" else "#F0EFE8"

# 13x13 crossword grid (1 = black cell, 0 = entry cell)
# Traditional 180-degree rotational symmetry
n <- 13
grid_data <- matrix(c(
  0,0,0,1,1,0,0,0,1,1,0,0,0,
  0,0,0,0,0,0,1,0,0,0,0,0,0,
  1,0,0,0,0,0,0,0,0,0,0,0,1,
  0,0,0,0,1,0,0,0,1,0,0,0,0,
  0,1,0,0,0,0,0,0,0,0,0,1,0,
  0,0,0,1,0,0,0,0,0,1,0,0,0,
  0,0,1,0,1,0,0,0,1,0,1,0,0,
  0,0,0,1,0,0,0,0,0,1,0,0,0,
  0,1,0,0,0,0,0,0,0,0,0,1,0,
  0,0,0,0,1,0,0,0,1,0,0,0,0,
  1,0,0,0,0,0,0,0,0,0,0,0,1,
  0,0,0,0,0,0,1,0,0,0,0,0,0,
  0,0,0,1,1,0,0,0,1,1,0,0,0
), nrow = n, ncol = n, byrow = TRUE)

# Cell data frame — row 1 at top, so plot y = n + 1 - row
rows_idx <- rep(1:n, each = n)
cols_idx <- rep(1:n, times = n)

df <- data.frame(
  col        = cols_idx,
  y          = n + 1 - rows_idx,
  fill_color = ifelse(
    as.logical(grid_data[cbind(rows_idx, cols_idx)]),
    "black", "white"
  )
)

# Assign clue numbers in reading order (top-left to bottom-right)
starts_across <- function(r, c) {
  grid_data[r, c] == 0 &&
    (c == 1 || grid_data[r, c - 1] == 1) &&
    c < n && grid_data[r, c + 1] == 0
}

starts_down <- function(r, c) {
  grid_data[r, c] == 0 &&
    (r == 1 || grid_data[r - 1, c] == 1) &&
    r < n && grid_data[r + 1, c] == 0
}

num_list <- list()
clue_n   <- 1
for (r in 1:n) {
  for (c in 1:n) {
    if (starts_across(r, c) || starts_down(r, c)) {
      num_list[[length(num_list) + 1]] <- data.frame(
        col   = c,
        y     = n + 1 - r,
        label = as.character(clue_n)
      )
      clue_n <- clue_n + 1
    }
  }
}
num_df <- do.call(rbind, num_list)

# Plot
p <- ggplot(df, aes(x = col, y = y)) +
  geom_tile(aes(fill = fill_color), color = "#333333", linewidth = 0.3) +
  scale_fill_identity() +
  geom_text(
    data  = num_df,
    aes(x = col - 0.40, y = y + 0.38, label = label),
    size  = 2.0,
    color = "black",
    hjust = 0,
    vjust = 1
  ) +
  annotate(
    "rect",
    xmin = 0.5, xmax = n + 0.5,
    ymin = 0.5, ymax = n + 0.5,
    fill      = NA,
    color     = "black",
    linewidth = 0.7
  ) +
  coord_fixed(ratio = 1, clip = "off") +
  scale_x_continuous(expand = expansion(add = 0.25)) +
  scale_y_continuous(expand = expansion(add = 0.25)) +
  labs(title = "crossword-basic · r · ggplot2 · anyplot.ai") +
  theme_void() +
  theme(
    plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG),
    plot.title = element_text(
      color  = INK,
      size   = 12,
      hjust  = 0.5,
      margin = margin(t = 8, b = 12)
    ),
    plot.margin = margin(12, 15, 12, 15)
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
