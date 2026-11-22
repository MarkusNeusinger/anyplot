#' anyplot.ai
#' voronoi-basic: Voronoi Diagram for Spatial Partitioning
#' Library: ggplot2 | R
#' Quality: 90/100 | Updated: 2026-11-22

library(ggplot2)
library(dplyr)
library(ragg)

# Theme tokens
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
X_COORD <- "x"  # role: x
Y_COORD <- "y"  # role: y

# Data: replace this block with your own table of seed points, for example df <- read.csv("seeds.csv")
set.seed(42)
n_points <- 25
df <- tibble::tibble(
  !!X_COORD := runif(n_points, 0, 100),
  !!Y_COORD := runif(n_points, 0, 100)
)

# Voronoi cells: assign every pixel of a fine grid to its nearest seed,
# clipped to the bounding box of the data range
x_lim <- range(0, 100)
y_lim <- range(0, 100)
res <- 700
gx <- seq(x_lim[1], x_lim[2], length.out = res)
gy <- seq(y_lim[1], y_lim[2], length.out = res)
grid_df <- expand.grid(x = gx, y = gy)

dist_mat <- sapply(seq_len(nrow(df)), function(i) {
  (grid_df$x - df[[X_COORD]][i])^2 + (grid_df$y - df[[Y_COORD]][i])^2
})
grid_df$cell <- max.col(-dist_mat, ties.method = "first")

# Cells that share an edge: neighbouring pixels with different owners
owner <- matrix(grid_df$cell, nrow = res)
pairs <- rbind(
  cbind(as.vector(owner[-res, ]), as.vector(owner[-1, ])),
  cbind(as.vector(owner[, -res]), as.vector(owner[, -1]))
)
pairs <- unique(pairs[pairs[, 1] != pairs[, 2], , drop = FALSE])

# Greedy colouring: each cell takes the first palette colour unused by its neighbours
cell_color <- integer(nrow(df))
for (i in seq_len(nrow(df))) {
  nb <- c(pairs[pairs[, 1] == i, 2], pairs[pairs[, 2] == i, 1])
  free <- setdiff(seq_along(IMPRINT_PALETTE), cell_color[nb])
  cell_color[i] <- free[1]
}
grid_df$fill <- IMPRINT_PALETTE[cell_color[grid_df$cell]]

# Plot
p <- ggplot(grid_df, aes(x = x, y = y, fill = fill)) +
  geom_raster() +
  geom_point(
    data = df,
    aes(x = .data[[X_COORD]], y = .data[[Y_COORD]]),
    inherit.aes = FALSE,
    shape = 21, size = 3, stroke = 0.9,
    color = INK, fill = PAGE_BG
  ) +
  scale_fill_identity() +
  scale_x_continuous(expand = c(0, 0)) +
  scale_y_continuous(expand = c(0, 0)) +
  coord_fixed() +
  labs(
    title = "voronoi-basic · r · ggplot2 · anyplot.ai",
    x = X_COORD,
    y = Y_COORD
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid       = element_blank(),
    panel.border     = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.4),
    axis.title       = element_text(color = INK, size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    plot.title       = element_text(color = INK, size = 12, face = "bold"),
    legend.position  = "none"
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
