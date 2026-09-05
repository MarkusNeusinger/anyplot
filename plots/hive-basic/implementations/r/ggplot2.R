#' anyplot.ai
#' hive-basic: Basic Hive Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(tibble)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data: software module dependency network -------------------------------
module_types <- c("core", "utility", "interface")
n_per_type   <- c(core = 12, utility = 10, interface = 8)

nodes <- bind_rows(lapply(module_types, function(m) {
  tibble(id = paste0(m, "_", seq_len(n_per_type[[m]])), type = m)
}))

sample_edges <- function(from_type, to_type, n) {
  from_ids <- nodes$id[nodes$type == from_type]
  to_ids   <- nodes$id[nodes$type == to_type]
  tibble(
    from   = sample(from_ids, n, replace = TRUE),
    to     = sample(to_ids, n, replace = TRUE),
    weight = sample(1:5, n, replace = TRUE)
  )
}

# Layered dependency edges: core -> utility -> interface, plus core -> interface
edges <- bind_rows(
  sample_edges("core", "utility", 22),
  sample_edges("utility", "interface", 18),
  sample_edges("core", "interface", 10)
) %>%
  filter(from != to) %>%
  distinct(from, to, .keep_all = TRUE) %>%
  mutate(edge_id = row_number())

# Node position along its axis is degree-based: higher-degree modules sit
# farther from the hive center, surfacing the busiest dependency hubs.
degree_tbl <- tibble(id = c(edges$from, edges$to)) %>% count(id, name = "degree")

nodes <- nodes %>%
  left_join(degree_tbl, by = "id") %>%
  mutate(degree = ifelse(is.na(degree), 0, degree)) %>%
  group_by(type) %>%
  mutate(radius = 0.18 + 0.78 * (rank(degree, ties.method = "first") - 1) / (n() - 1)) %>%
  ungroup()

# --- Axis geometry: 3 radial axes, 120 degrees apart ------------------------
axis_angle <- c(core = pi / 2, utility = pi / 2 + 2 * pi / 3, interface = pi / 2 + 4 * pi / 3)
max_radius <- 1.0

nodes <- nodes %>%
  mutate(angle = axis_angle[type], x = radius * cos(angle), y = radius * sin(angle))

axis_lines <- tibble(
  type = module_types,
  angle = axis_angle[module_types],
  x0 = 0, y0 = 0,
  x1 = max_radius * cos(axis_angle[module_types]),
  y1 = max_radius * sin(axis_angle[module_types])
)

axis_labels <- axis_lines %>%
  mutate(
    x = 1.14 * cos(angle),
    y = 1.14 * sin(angle),
    label = tools::toTitleCase(type)
  )

# --- Edge curves: quadratic Bezier bent toward the hive center --------------
# Bundling curves through a shared interior control point (rather than
# straight chords) is the classic hive-plot device for keeping dense
# cross-axis connections legible.
bezier_points <- function(x0, y0, x1, y1, n = 30) {
  cx <- (x0 + x1) / 2.5
  cy <- (y0 + y1) / 2.5
  t <- seq(0, 1, length.out = n)
  tibble(
    x = (1 - t)^2 * x0 + 2 * (1 - t) * t * cx + t^2 * x1,
    y = (1 - t)^2 * y0 + 2 * (1 - t) * t * cy + t^2 * y1
  )
}

edge_coords <- edges %>%
  left_join(nodes %>% select(id, x, y), by = c("from" = "id")) %>%
  rename(x0 = x, y0 = y) %>%
  left_join(nodes %>% select(id, x, y), by = c("to" = "id")) %>%
  rename(x1 = x, y1 = y)

edge_curves <- bind_rows(lapply(seq_len(nrow(edge_coords)), function(i) {
  row <- edge_coords[i, ]
  bind_cols(bezier_points(row$x0, row$y0, row$x1, row$y1),
            edge_id = row$edge_id, weight = row$weight)
}))

# --- Plot --------------------------------------------------------------------
p <- ggplot() +
  geom_segment(
    data = axis_lines,
    aes(x = x0, y = y0, xend = x1, yend = y1),
    color = INK_SOFT, linewidth = 0.6
  ) +
  geom_path(
    data = edge_curves,
    aes(x = x, y = y, group = edge_id, alpha = weight),
    color = INK_MUTED, linewidth = 0.5
  ) +
  scale_alpha_continuous(range = c(0.12, 0.55), guide = "none") +
  annotate(
    "point", x = 0, y = 0, shape = 21,
    size = 3.4, stroke = 0.7, color = INK_SOFT, fill = PAGE_BG
  ) +
  geom_point(
    data = nodes,
    aes(x = x, y = y, color = type),
    size = 2.8
  ) +
  scale_color_manual(
    values = setNames(IMPRINT_PALETTE[1:3], module_types),
    labels = setNames(tools::toTitleCase(module_types), module_types),
    name   = "Module type"
  ) +
  geom_text(
    data = axis_labels,
    aes(x = x, y = y, label = label),
    color = INK, size = 3.5, fontface = "bold"
  ) +
  labs(title = "hive-basic · r · ggplot2 · anyplot.ai") +
  coord_equal(xlim = c(-1.05, 1.05), ylim = c(-0.62, 1.18), clip = "off") +
  theme_void(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    plot.title         = element_text(color = INK, size = 12, hjust = 0.5, margin = margin(b = 14)),
    legend.position    = "bottom",
    legend.background  = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_text(color = INK, size = 10),
    plot.margin        = margin(20, 30, 20, 30)
  )

# --- Save --------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
