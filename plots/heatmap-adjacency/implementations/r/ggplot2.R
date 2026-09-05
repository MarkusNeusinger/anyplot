#' anyplot.ai
#' heatmap-adjacency: Network Adjacency Matrix Heatmap
#' Library: ggplot2 3.5.1 | R 4.4
#' Quality: pending | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(tidyr)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# --- Data: coworker collaboration network ------------------------------------
# 30 employees across 3 departments; node labels carry the department prefix
# so group boundaries are visible directly in the axis ticks (per spec note
# on large networks). Within-department pairs collaborate more often and more
# intensely than cross-department pairs, producing block-diagonal structure.
departments <- c("Engineering", "Marketing", "Sales")
dept_short  <- c(Engineering = "ENG", Marketing = "MKT", Sales = "SLS")
n_per_dept  <- 10

nodes <- tibble::tibble(department = rep(departments, each = n_per_dept)) %>%
  group_by(department) %>%
  mutate(idx = row_number()) %>%
  ungroup() %>%
  mutate(node = sprintf("%s-%02d", dept_short[department], idx))

n_nodes <- nrow(nodes)

weight_mat <- matrix(NA_real_, n_nodes, n_nodes)
for (i in seq_len(n_nodes)) {
  for (j in seq_len(n_nodes)) {
    if (j <= i) next
    same_dept <- nodes$department[i] == nodes$department[j]
    edge_prob <- if (same_dept) 0.75 else 0.12
    if (runif(1) < edge_prob) {
      weight <- if (same_dept) runif(1, 4, 10) else runif(1, 1, 4)
      weight_mat[i, j] <- weight
      weight_mat[j, i] <- weight # undirected graph: fill both triangles
    }
  }
}
rownames(weight_mat) <- nodes$node
colnames(weight_mat) <- nodes$node

adjacency_df <- as.data.frame(weight_mat) %>%
  tibble::rownames_to_column("source") %>%
  pivot_longer(-source, names_to = "target", values_to = "weight") %>%
  mutate(
    source = factor(source, levels = nodes$node),
    target = factor(target, levels = nodes$node)
  )

# --- Plot ---------------------------------------------------------------
p <- ggplot(adjacency_df, aes(x = target, y = source, fill = weight)) +
  geom_tile(color = PAGE_BG, linewidth = 0.15) +
  scale_fill_gradient(
    low      = "#009E73",
    high     = "#4467A3",
    na.value = ELEVATED_BG, # absent edges (incl. diagonal): near-bg, distinct from data
    name     = "Meetings\nper month",
    guide    = guide_colorbar(barheight = unit(9, "cm"), barwidth = unit(0.4, "cm"))
  ) +
  scale_x_discrete(expand = c(0, 0)) +
  scale_y_discrete(expand = c(0, 0), limits = rev(nodes$node)) +
  coord_fixed(ratio = 1) +
  labs(
    title = "heatmap-adjacency · r · ggplot2 · anyplot.ai",
    x = NULL, y = NULL
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid         = element_blank(),
    axis.text.x        = element_text(color = INK_SOFT, size = 8, angle = 90, hjust = 1, vjust = 0.5),
    axis.text.y        = element_text(color = INK_SOFT, size = 8),
    plot.title         = element_text(color = INK, size = 12),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_text(color = INK, size = 10),
    legend.background  = element_rect(fill = ELEVATED_BG, color = NA),
    plot.margin        = margin(10, 10, 10, 10)
  )

# --- Save ---------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
