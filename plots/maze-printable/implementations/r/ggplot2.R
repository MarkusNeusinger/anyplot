#' anyplot.ai
#' maze-printable: Printable Maze Puzzle
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 90/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME     <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG   <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK       <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_MUTED <- if (THEME == "light") "#6B6A63" else "#A8A79F"
IMPRINT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# --- Maze generation (randomized depth-first backtracker) ---------------
# A spanning tree over the cell grid guarantees exactly one path between
# any two cells, so start and goal have a single unique solution route.
maze_width  <- 22
maze_height <- 22

east_open  <- matrix(FALSE, nrow = maze_width, ncol = maze_height)
south_open <- matrix(FALSE, nrow = maze_width, ncol = maze_height)
visited    <- matrix(FALSE, nrow = maze_width, ncol = maze_height)

visited[1, 1] <- TRUE
stack <- list(list(x = 0, y = 0))

while (length(stack) > 0) {
  cur <- stack[[length(stack)]]
  cx  <- cur$x
  cy  <- cur$y

  neighbors <- list()
  if (cx > 0 && !visited[cx, cy + 1]) {
    neighbors[[length(neighbors) + 1]] <- list(x = cx - 1, y = cy, dir = "W")
  }
  if (cx < maze_width - 1 && !visited[cx + 2, cy + 1]) {
    neighbors[[length(neighbors) + 1]] <- list(x = cx + 1, y = cy, dir = "E")
  }
  if (cy > 0 && !visited[cx + 1, cy]) {
    neighbors[[length(neighbors) + 1]] <- list(x = cx, y = cy - 1, dir = "N")
  }
  if (cy < maze_height - 1 && !visited[cx + 1, cy + 2]) {
    neighbors[[length(neighbors) + 1]] <- list(x = cx, y = cy + 1, dir = "S")
  }

  if (length(neighbors) > 0) {
    pick <- neighbors[[sample.int(length(neighbors), 1)]]
    nx <- pick$x
    ny <- pick$y

    if (pick$dir == "E") east_open[cx + 1, cy + 1] <- TRUE
    if (pick$dir == "W") east_open[nx + 1, ny + 1] <- TRUE
    if (pick$dir == "S") south_open[cx + 1, cy + 1] <- TRUE
    if (pick$dir == "N") south_open[nx + 1, ny + 1] <- TRUE

    visited[nx + 1, ny + 1] <- TRUE
    stack[[length(stack) + 1]] <- list(x = nx, y = ny)
  } else {
    stack[[length(stack)]] <- NULL
  }
}

# --- Wall segments --------------------------------------------------------
# Row 0 sits at the top of the print, so its y-coordinate is the tallest.
vertical_walls <- expand.grid(col = 0:(maze_width - 2), row = 0:(maze_height - 1)) |>
  filter(!east_open[cbind(col + 1, row + 1)]) |>
  transmute(x = col + 1, xend = col + 1, y = maze_height - row - 1, yend = maze_height - row)

horizontal_walls <- expand.grid(col = 0:(maze_width - 1), row = 0:(maze_height - 2)) |>
  filter(!south_open[cbind(col + 1, row + 1)]) |>
  transmute(x = col, xend = col + 1, y = maze_height - row - 1, yend = maze_height - row - 1)

# Outer border, with a one-cell gap for the entrance (top-left) and exit
# (bottom-right) so the puzzle can be entered and exited with a pen.
border_walls <- tibble::tibble(
  x    = c(1,           0,               0,           maze_width),
  xend = c(maze_width,  maze_width - 1,  0,           maze_width),
  y    = c(maze_height, 0,               0,           0),
  yend = c(maze_height, 0,               maze_height, maze_height)
)

walls <- bind_rows(vertical_walls, horizontal_walls, border_walls)

# --- Start / goal markers --------------------------------------------------
markers <- tibble::tibble(
  label = c("S", "G"),
  x     = c(0.5, maze_width - 0.5),
  y     = c(maze_height - 0.5, 0.5),
  color = c(IMPRINT_PALETTE[1], IMPRINT_PALETTE[2])
)

# --- Plot --------------------------------------------------------------
title_text <- "maze-printable · r · ggplot2 · anyplot.ai"
subtitle_text <- sprintf(
  "%d × %d grid · exactly one path from start to goal",
  maze_width, maze_height
)

p <- ggplot() +
  geom_segment(
    data = walls, aes(x = x, xend = xend, y = y, yend = yend),
    color = INK, linewidth = 1.3, lineend = "square", linejoin = "mitre"
  ) +
  geom_point(
    data = markers, aes(x = x, y = y, color = color),
    size = 9, show.legend = FALSE
  ) +
  geom_text(
    data = markers, aes(x = x, y = y, label = label),
    color = PAGE_BG, size = 4.2, fontface = "bold"
  ) +
  scale_color_identity() +
  coord_fixed(
    xlim = c(-0.5, maze_width + 0.5),
    ylim = c(-0.5, maze_height + 0.5),
    expand = FALSE
  ) +
  labs(title = title_text, subtitle = subtitle_text) +
  theme_void(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    plot.title       = element_text(color = INK, size = 12, hjust = 0.5, margin = margin(b = 6)),
    plot.subtitle    = element_text(color = INK_MUTED, size = 8, hjust = 0.5, margin = margin(b = 10)),
    plot.margin      = margin(t = 20, r = 20, b = 20, l = 20)
  )

# --- Save --------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
