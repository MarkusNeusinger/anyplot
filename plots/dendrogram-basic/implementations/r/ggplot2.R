#' anyplot.ai
#' dendrogram-basic: Basic Dendrogram
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-06-18

library(ggplot2)
library(dplyr)
library(ragg)
library(gapminder)

# Theme tokens (Imprint palette)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# Data: first 20 European countries (2007) clustered by development indicators
europe_2007 <- gapminder |>
  filter(continent == "Europe", year == 2007) |>
  arrange(country) |>
  slice(1:20) |>
  as.data.frame()

feat_mat <- scale(as.matrix(europe_2007[, c("lifeExp", "gdpPercap", "pop")]))
rownames(feat_mat) <- as.character(europe_2007$country)

# Hierarchical clustering with Ward's linkage
hc       <- hclust(dist(feat_mat), method = "ward.D2")
n_leaves <- nrow(feat_mat)
n_merges <- n_leaves - 1

# Leaf x positions in dendrogram display order
x_pos <- integer(n_leaves)
for (pos in seq_along(hc$order)) {
  x_pos[hc$order[pos]] <- pos
}

# Internal node x (midpoint of children) and y (merge height)
node_x <- numeric(n_merges)
node_y <- hc$height

for (k in seq_len(n_merges)) {
  lft <- hc$merge[k, 1]
  rgt <- hc$merge[k, 2]
  xl  <- if (lft < 0) x_pos[-lft] else node_x[lft]
  xr  <- if (rgt < 0) x_pos[-rgt] else node_x[rgt]
  node_x[k] <- (xl + xr) / 2
}

# Build segment data frame: 3 segments per merge (left vert, horiz, right vert)
n_segs   <- 3L * n_merges
seg_x    <- numeric(n_segs)
seg_xend <- numeric(n_segs)
seg_y    <- numeric(n_segs)
seg_yend <- numeric(n_segs)

for (k in seq_len(n_merges)) {
  lft <- hc$merge[k, 1]
  rgt <- hc$merge[k, 2]
  xl  <- if (lft < 0) x_pos[-lft] else node_x[lft]
  yl  <- if (lft < 0) 0            else node_y[lft]
  xr  <- if (rgt < 0) x_pos[-rgt] else node_x[rgt]
  yr  <- if (rgt < 0) 0            else node_y[rgt]
  i   <- (k - 1L) * 3L + 1L
  seg_x[i]       <- xl; seg_xend[i]       <- xl; seg_y[i]       <- yl;         seg_yend[i]       <- node_y[k]
  seg_x[i + 1L]  <- xl; seg_xend[i + 1L]  <- xr; seg_y[i + 1L]  <- node_y[k]; seg_yend[i + 1L]  <- node_y[k]
  seg_x[i + 2L]  <- xr; seg_xend[i + 2L]  <- xr; seg_y[i + 2L]  <- yr;        seg_yend[i + 2L]  <- node_y[k]
}

seg_df <- data.frame(x = seg_x, xend = seg_xend, y = seg_y, yend = seg_yend)

# Cut tree into 3 clusters; assign Imprint palette colors to leaves
clust_assign <- cutree(hc, k = 3)
leaf_clust   <- clust_assign[hc$order]
max_h        <- max(node_y)
label_y      <- -max_h * 0.02

label_df <- data.frame(
  x       = seq_len(n_leaves),
  y       = label_y,
  label   = hc$labels[hc$order],
  cluster = factor(leaf_clust)
)

plot_title <- "dendrogram-basic · r · ggplot2 · anyplot.ai"

# Plot — horizontal dendrogram via coord_flip; leaves on the right, root on the left
p <- ggplot() +
  geom_segment(
    data = seg_df,
    aes(x = x, xend = xend, y = y, yend = yend),
    color = INK_SOFT, linewidth = 0.55
  ) +
  geom_text(
    data  = label_df,
    aes(x = x, y = y, label = label, color = cluster),
    hjust = 1, size = 2.8
  ) +
  scale_color_manual(
    values = setNames(IMPRINT_PALETTE[1:3], c("1", "2", "3")),
    name   = "Cluster"
  ) +
  guides(color = guide_legend(override.aes = list(label = "■", size = 4))) +
  scale_x_continuous(breaks = NULL, expand = c(0.03, 0.03)) +
  scale_y_continuous(
    limits = c(-max_h * 0.55, max_h * 1.05),
    breaks = pretty(c(0, max_h), n = 5)
  ) +
  coord_flip() +
  labs(
    title = plot_title,
    x     = NULL,
    y     = "Ward's Distance"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major   = element_blank(),
    panel.grid.minor   = element_blank(),
    axis.text.x        = element_text(color = INK_SOFT, size = 8),
    axis.text.y        = element_blank(),
    axis.ticks.y       = element_blank(),
    axis.title.x       = element_text(color = INK, size = 10),
    axis.title.y       = element_blank(),
    plot.title         = element_text(color = INK, size = 12, face = "bold"),
    legend.background  = element_rect(fill = ELEVATED_BG, color = INK_SOFT,
                                      linewidth = 0.3),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_text(color = INK, size = 10),
    legend.position    = "top",
    plot.margin        = margin(20, 20, 20, 20)
  )

ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
