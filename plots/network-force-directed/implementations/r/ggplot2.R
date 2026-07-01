#' anyplot.ai
#' network-force-directed: Force-Directed Graph
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-07-01

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens (Imprint palette)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette positions 1-5 for the five research areas
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030")
GROUP_LABELS    <- c("Genomics", "Neuroscience", "Immunology", "Bioinformatics", "Pharmacology")

# Network: scientific collaboration across 5 research areas, 8 researchers each
N_GROUPS        <- 5L
NODES_PER_GROUP <- 8L
N_NODES         <- N_GROUPS * NODES_PER_GROUP

nodes_df <- data.frame(
  id         = seq_len(N_NODES),
  group      = rep(seq_len(N_GROUPS), each = NODES_PER_GROUP),
  group_name = rep(GROUP_LABELS,      each = NODES_PER_GROUP),
  stringsAsFactors = FALSE
)

# Build edge list
edges_raw  <- vector("list", 400L)
edge_count <- 0L

# Within-group edges (dense intra-community connectivity)
for (g in seq_len(N_GROUPS)) {
  grp <- which(nodes_df$group == g)
  for (i in grp) {
    n_conn  <- sample(2L:4L, 1L)
    others  <- grp[grp != i]
    targets <- sample(others, min(n_conn, length(others)))
    for (j in targets) {
      if (i < j) {
        edge_count <- edge_count + 1L
        edges_raw[[edge_count]] <- c(i, j)
      }
    }
  }
}

# Cross-group bridges (sparse inter-community collaboration)
cross_pairs <- list(c(1L, 4L), c(2L, 4L), c(3L, 5L), c(1L, 2L), c(4L, 5L), c(2L, 3L))
for (pair in cross_pairs) {
  g1  <- which(nodes_df$group == pair[1L])
  g2  <- which(nodes_df$group == pair[2L])
  frm <- sample(g1, 2L)
  too <- sample(g2, 2L)
  for (i in 1L:2L) {
    edge_count <- edge_count + 1L
    edges_raw[[edge_count]] <- c(frm[i], too[i])
  }
}

edges_mat <- do.call(rbind, edges_raw[seq_len(edge_count)])
edges_df  <- unique(data.frame(from = edges_mat[, 1L], to = edges_mat[, 2L]))

# Degree per node
deg_tbl         <- table(c(edges_df$from, edges_df$to))
nodes_df$degree <- as.integer(deg_tbl[as.character(nodes_df$id)])
nodes_df$degree[is.na(nodes_df$degree)] <- 1L

# Fruchterman-Reingold force-directed layout (pure R, no external graph packages)
fr_layout <- function(n, group_vec, n_grp, edges, iterations = 200L) {
  # Warm start: arrange groups on a circle, nodes on smaller sub-circles
  ang_g <- seq(0, 2 * pi, length.out = n_grp + 1L)[seq_len(n_grp)]
  pos_x <- numeric(n)
  pos_y <- numeric(n)
  for (g in seq_len(n_grp)) {
    idx   <- which(group_vec == g)
    ng    <- length(idx)
    ang_i <- seq(0, 2 * pi, length.out = ng + 1L)[seq_len(ng)]
    cx    <- 0.5 + 0.34 * cos(ang_g[g])
    cy    <- 0.5 + 0.34 * sin(ang_g[g])
    pos_x[idx] <- cx + 0.09 * cos(ang_i) + runif(ng, -0.01, 0.01)
    pos_y[idx] <- cy + 0.09 * sin(ang_i) + runif(ng, -0.01, 0.01)
  }

  k    <- sqrt(1.0 / n) * 1.6
  temp <- 0.10
  cool <- temp / iterations

  for (iter in seq_len(iterations)) {
    disp_x <- numeric(n)
    disp_y <- numeric(n)

    # Repulsive forces: vectorized over all other nodes for each v
    for (v in seq_len(n)) {
      dx    <- pos_x[v] - pos_x
      dy    <- pos_y[v] - pos_y
      d2    <- dx^2 + dy^2
      d2[v] <- Inf
      d     <- sqrt(pmax(d2, 1e-8))
      fr    <- k^2 / d
      disp_x[v] <- sum(dx / d * fr)
      disp_y[v] <- sum(dy / d * fr)
    }

    # Attractive forces along each edge
    for (e in seq_len(nrow(edges))) {
      v  <- edges$from[e]
      u  <- edges$to[e]
      dx <- pos_x[v] - pos_x[u]
      dy <- pos_y[v] - pos_y[u]
      d  <- sqrt(dx^2 + dy^2)
      if (d < 1e-8) next
      fa         <- d / k
      disp_x[v]  <- disp_x[v] - dx / d * fa
      disp_y[v]  <- disp_y[v] - dy / d * fa
      disp_x[u]  <- disp_x[u] + dx / d * fa
      disp_y[u]  <- disp_y[u] + dy / d * fa
    }

    # Apply temperature-clamped displacements
    dm    <- sqrt(disp_x^2 + disp_y^2)
    dm    <- pmax(dm, 1e-10)
    sc    <- pmin(dm, temp) / dm
    pos_x <- pmax(0.04, pmin(0.96, pos_x + disp_x * sc))
    pos_y <- pmax(0.04, pmin(0.96, pos_y + disp_y * sc))
    temp  <- temp - cool
  }

  data.frame(x = pos_x, y = pos_y)
}

layout     <- fr_layout(N_NODES, nodes_df$group, N_GROUPS, edges_df)
nodes_df$x <- layout$x
nodes_df$y <- layout$y

# Edge segment endpoints
edges_plot <- data.frame(
  x    = nodes_df$x[edges_df$from],
  y    = nodes_df$y[edges_df$from],
  xend = nodes_df$x[edges_df$to],
  yend = nodes_df$y[edges_df$to]
)

# Node size scaled by degree (hub nodes appear larger)
nodes_df$pt_size <- 1.6 + 3.4 * (nodes_df$degree / max(nodes_df$degree))

# Title (standard format; square canvas is narrower so keep fontsize modest)
plot_title     <- "network-force-directed · r · ggplot2 · anyplot.ai"
title_fontsize <- 11L
edge_alpha     <- if (THEME == "light") 0.28 else 0.18

# Plot
p <- ggplot() +
  geom_segment(
    data      = edges_plot,
    aes(x = x, y = y, xend = xend, yend = yend),
    color     = INK_SOFT,
    alpha     = edge_alpha,
    linewidth = 0.25
  ) +
  geom_point(
    data  = nodes_df,
    aes(x = x, y = y, color = group_name, size = pt_size),
    alpha = 0.88,
    shape = 16L
  ) +
  scale_color_manual(
    values = setNames(IMPRINT_PALETTE, GROUP_LABELS),
    name   = "Research Area"
  ) +
  scale_size_identity(guide = "none") +
  coord_fixed(ratio = 1) +
  labs(title = plot_title, x = NULL, y = NULL) +
  theme_void(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    plot.title          = element_text(
      color  = INK,
      size   = title_fontsize,
      hjust  = 0.5,
      margin = margin(t = 8, b = 12)
    ),
    plot.title.position = "plot",
    plot.margin       = margin(14, 24, 14, 24),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.4),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    legend.margin     = margin(8, 10, 8, 10),
    legend.position   = "right"
  ) +
  guides(
    color = guide_legend(
      override.aes   = list(size = 4, alpha = 1),
      title.position = "top"
    )
  )

# Save (square canvas: 2400 x 2400 px)
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
