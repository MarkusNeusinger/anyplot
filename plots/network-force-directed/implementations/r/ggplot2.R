#' anyplot.ai
#' network-force-directed: Force-Directed Graph
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-08-24
library(ggplot2)
library(dplyr)
library(tidyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data: microservice dependency graph, grouped by architectural layer ---
layers <- list(
  Frontend = c("web", "mobile", "admin", "embed", "portal", "kiosk", "docs", "sdk", "cli"),
  Backend  = c("auth", "users", "orders", "payments", "notify", "search", "catalog", "pricing", "shipping"),
  Data     = c("db-primary", "db-replica", "cache", "queue", "warehouse", "lake", "etl", "backup", "index"),
  Infra    = c("gateway", "lb", "cdn", "dns", "monitor", "logging", "secrets", "ci", "registry")
)

nodes <- tibble(
  id      = unlist(layers, use.names = FALSE),
  cluster = rep(names(layers), times = lengths(layers))
)

# Within-layer edges: a ring plus a handful of random chords per layer
intra_edges <- bind_rows(lapply(layers, function(ids) {
  n <- length(ids)
  ring <- tibble(from = ids, to = ids[c(2:n, 1)])
  chord_i <- sample.int(n, size = round(n * 0.55))
  chords <- tibble(
    from = ids[chord_i],
    to   = ids[sapply(chord_i, function(i) sample(setdiff(seq_len(n), i), 1))]
  )
  bind_rows(ring, chords)
}))

# Cross-layer edges: calls that cross architectural boundaries
bridge_edges <- tibble(
  from = c("web", "mobile", "admin", "gateway", "gateway", "gateway", "auth",
           "orders", "payments", "catalog", "search", "notify", "orders",
           "etl", "warehouse", "ci", "monitor", "secrets", "cdn", "lb"),
  to   = c("gateway", "gateway", "gateway", "auth", "users", "orders", "cache",
           "db-primary", "db-primary", "index", "index", "queue", "queue",
           "warehouse", "lake", "registry", "logging", "auth", "web", "gateway")
)

edges <- bind_rows(intra_edges, bridge_edges) %>%
  mutate(pair_key = ifelse(from < to, paste(from, to), paste(to, from))) %>%
  distinct(pair_key, .keep_all = TRUE) %>%
  filter(from != to) %>%
  select(from, to) %>%
  mutate(weight = sample(1:5, n(), replace = TRUE))

degree <- bind_rows(
  edges %>% count(id = from),
  edges %>% count(id = to)
) %>%
  group_by(id) %>%
  summarise(degree = sum(n), .groups = "drop")

nodes <- nodes %>%
  left_join(degree, by = "id") %>%
  mutate(degree = coalesce(degree, 0))

# --- Force-directed layout (Fruchterman-Reingold) ---------------------------
n_nodes  <- nrow(nodes)
area     <- 4
k_ideal  <- sqrt(area / n_nodes)
pos      <- matrix(runif(n_nodes * 2, -1, 1), ncol = 2)
from_idx <- match(edges$from, nodes$id)
to_idx   <- match(edges$to, nodes$id)
n_iter   <- 400
temp     <- 0.15

for (iter in seq_len(n_iter)) {
  dx   <- outer(pos[, 1], pos[, 1], "-")
  dy   <- outer(pos[, 2], pos[, 2], "-")
  dist <- sqrt(dx^2 + dy^2)
  diag(dist) <- Inf
  repulse <- (k_ideal^2) / dist
  disp    <- cbind(rowSums(repulse * dx / dist), rowSums(repulse * dy / dist))

  edge_dx   <- pos[from_idx, 1] - pos[to_idx, 1]
  edge_dy   <- pos[from_idx, 2] - pos[to_idx, 2]
  edge_dist <- pmax(sqrt(edge_dx^2 + edge_dy^2), 1e-6)
  attract   <- (edge_dist^2) / k_ideal
  attract_x <- (edge_dx / edge_dist) * attract
  attract_y <- (edge_dy / edge_dist) * attract

  for (e in seq_along(from_idx)) {
    disp[from_idx[e], 1] <- disp[from_idx[e], 1] - attract_x[e]
    disp[from_idx[e], 2] <- disp[from_idx[e], 2] - attract_y[e]
    disp[to_idx[e], 1]   <- disp[to_idx[e], 1] + attract_x[e]
    disp[to_idx[e], 2]   <- disp[to_idx[e], 2] + attract_y[e]
  }

  disp_len <- pmax(sqrt(rowSums(disp^2)), 1e-6)
  step     <- pmin(disp_len, temp)
  pos      <- pos + (disp / disp_len) * step
  temp     <- temp * 0.99
}

nodes$x <- pos[, 1]
nodes$y <- pos[, 2]

edge_positions <- edges %>%
  left_join(nodes %>% select(id, x, y), by = c("from" = "id")) %>%
  left_join(nodes %>% select(id, xend = x, yend = y), by = c("to" = "id"))

hub_nodes <- nodes %>% slice_max(degree, n = 5, with_ties = FALSE)
nodes$cluster <- factor(nodes$cluster, levels = names(layers))

# --- Plot ---------------------------------------------------------------
p <- ggplot() +
  geom_segment(
    data = edge_positions,
    aes(x = x, y = y, xend = xend, yend = yend, linewidth = weight),
    color = INK_MUTED, alpha = 0.35, lineend = "round"
  ) +
  geom_point(
    data = nodes,
    aes(x = x, y = y, color = cluster, size = degree)
  ) +
  geom_text(
    data = hub_nodes,
    aes(x = x, y = y, label = id),
    color = INK, size = 3.2, fontface = "bold", nudge_y = 0.22
  ) +
  scale_color_manual(values = IMPRINT_PALETTE[1:4], name = "Layer") +
  scale_size_continuous(range = c(3, 9), guide = "none") +
  scale_linewidth_continuous(range = c(0.3, 1.4), guide = "none") +
  scale_x_continuous(expand = expansion(mult = 0.1)) +
  scale_y_continuous(expand = expansion(mult = 0.1)) +
  coord_equal() +
  labs(title = "network-force-directed · r · ggplot2 · anyplot.ai") +
  theme_void(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    plot.title        = element_text(color = INK, size = 12, hjust = 0.5, margin = margin(b = 12)),
    legend.position   = "bottom",
    legend.title      = element_text(color = INK, size = 10),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.key        = element_rect(fill = PAGE_BG, color = NA),
    plot.margin       = margin(15, 15, 15, 15)
  )

# --- Save ---------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
