#' anyplot.ai
#' scatter-embedding: t-SNE and UMAP Embedding Visualization
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-08-11

library(ggplot2)
library(dplyr)
library(tibble)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD")

# --- Data: UMAP projection of PBMC single-cell RNA-seq profiles -------------
# Cluster geometry (center, spread, rotation) mimics the elongated, irregular
# blobs a real non-linear embedding produces, rather than circular Gaussians.
cell_types <- c("CD4+ T cells", "CD8+ T cells", "B cells", "NK cells", "Monocytes", "Dendritic cells")
cluster_n  <- c(700, 550, 450, 350, 400, 250)
center_x   <- c(-6.0, -3.5, 5.5, -7.0, 6.5, 1.5)
center_y   <- c(2.0, -3.0, 2.5, -1.5, -2.0, 4.5)
spread_x   <- c(1.3, 1.0, 1.1, 0.9, 1.2, 0.8)
spread_y   <- c(0.55, 0.5, 0.6, 0.45, 0.5, 0.4)
angle_deg  <- c(20, -30, 10, 60, -15, 45)

n_total    <- sum(cluster_n)
cluster_id <- factor(rep(seq_along(cluster_n), cluster_n), labels = cell_types)
cx_vec     <- rep(center_x, cluster_n)
cy_vec     <- rep(center_y, cluster_n)
sx_vec     <- rep(spread_x, cluster_n)
sy_vec     <- rep(spread_y, cluster_n)
angle_vec  <- rep(angle_deg, cluster_n) * pi / 180

raw_x <- rnorm(n_total, mean = 0, sd = sx_vec)
raw_y <- rnorm(n_total, mean = 0, sd = sy_vec)

embedding <- tibble::tibble(
  x         = raw_x * cos(angle_vec) - raw_y * sin(angle_vec) + cx_vec,
  y         = raw_x * sin(angle_vec) + raw_y * cos(angle_vec) + cy_vec,
  cell_type = cluster_id
)

# --- Title (scales fontsize to length; mandated title is well under the
# 67-char baseline here, so this resolves to the library default of 12pt) ---
title_text  <- "scatter-embedding · r · ggplot2 · anyplot.ai"
title_ratio <- if (nchar(title_text) > 67) 67 / nchar(title_text) else 1.0
title_size  <- max(8, round(12 * title_ratio))

# --- Plot ---------------------------------------------------------------
p <- ggplot(embedding, aes(x = x, y = y, color = cell_type, shape = cell_type)) +
  geom_point(size = 1.8, alpha = 0.55, stroke = 0.4) +
  scale_color_manual(values = IMPRINT_PALETTE, name = "Cell type") +
  scale_shape_manual(values = c(16, 17, 15, 18, 3, 8), name = "Cell type") +
  labs(
    title    = title_text,
    subtitle = "UMAP projection (n_neighbors = 15) of PBMC single-cell RNA-seq profiles",
    x        = "UMAP 1",
    y        = "UMAP 2"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    axis.text         = element_blank(),
    axis.ticks        = element_blank(),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.title        = element_text(color = INK, size = 10),
    plot.title        = element_text(color = INK, size = title_size, face = "bold"),
    plot.subtitle     = element_text(color = INK_SOFT, size = 9),
    legend.position    = "right",
    legend.background = element_rect(fill = ELEVATED_BG, color = NA),
    legend.key         = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_text(color = INK, size = 9)
  )

# --- Save --------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
