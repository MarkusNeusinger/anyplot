#' anyplot.ai
#' network-weighted: Weighted Network Graph with Edge Thickness
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-05-17

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT   <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                 "#AE3030", "#2ABCCD", "#954477")

# Data: Trade network between countries (weighted by annual trade volume)
set.seed(42)
nodes <- data.frame(
  id = 1:15,
  country = c("USA", "China", "India", "Japan", "Germany",
              "UK", "France", "Brazil", "Canada", "Mexico",
              "South Korea", "Italy", "Spain", "Netherlands", "Australia"),
  region = c("Americas", "Asia", "Asia", "Asia", "Europe",
             "Europe", "Europe", "Americas", "Americas", "Americas",
             "Asia", "Europe", "Europe", "Europe", "Oceania")
)

# Edges: trade relationships with weights (annual volume in billions USD)
edges <- data.frame(
  source = c(1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 4, 5, 5, 6, 6, 7, 8, 9, 10, 11, 12, 13, 14),
  target = c(2, 3, 4, 3, 5, 6, 4, 5, 5, 11, 12, 6, 7, 7, 14, 8, 9, 10, 9, 2, 13, 14, 1),
  weight = c(640, 380, 285, 620, 290, 240, 185, 165, 310, 85, 150, 520, 380, 275, 220, 185, 95, 120, 85, 330, 95, 80, 65)
)

# Simple spring-like layout: place nodes on a circle with slight random jitter
n_nodes <- nrow(nodes)
angles <- seq(0, 2 * pi, length.out = n_nodes + 1)[1:n_nodes]
nodes$x <- 2 * cos(angles) + rnorm(n_nodes, 0, 0.3)
nodes$y <- 2 * sin(angles) + rnorm(n_nodes, 0, 0.3)

# Create edge data frame with node positions
edges_positioned <- edges %>%
  left_join(nodes %>% select(id, x, y), by = c("source" = "id")) %>%
  rename(x_start = x, y_start = y) %>%
  left_join(nodes %>% select(id, x, y), by = c("target" = "id")) %>%
  rename(x_end = x, y_end = y)

# Normalize edge weights for linewidth (1 to 4)
weight_min <- min(edges_positioned$weight)
weight_max <- max(edges_positioned$weight)
edges_positioned$linewidth <- 1 + 3 * (edges_positioned$weight - weight_min) / (weight_max - weight_min)

# Create base theme
anyplot_theme <- theme_minimal(base_size = 14) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    axis.title        = element_blank(),
    axis.text         = element_blank(),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 24, face = "bold"),
    plot.margin       = margin(20, 20, 20, 20, "pt")
  )

# Create plot
p <- ggplot() +
  # Draw edges first (so they appear behind nodes)
  geom_segment(
    data = edges_positioned,
    aes(x = x_start, y = y_start, xend = x_end, yend = y_end, linewidth = linewidth),
    color = IMPRINT[1],
    alpha = 0.5,
    lineend = "round"
  ) +
  # Draw nodes
  geom_point(
    data = nodes,
    aes(x = x, y = y),
    color = IMPRINT[1],
    size = 8,
    alpha = 0.9
  ) +
  # Node labels
  geom_text(
    data = nodes,
    aes(x = x, y = y, label = substr(country, 1, 3)),
    color = PAGE_BG,
    size = 3.5,
    fontface = "bold"
  ) +
  scale_linewidth(range = c(1, 4), guide = "none") +
  coord_equal() +
  labs(title = "network-weighted · ggplot2 · anyplot.ai") +
  anyplot_theme

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 16,
  height   = 9,
  units    = "in",
  dpi      = 300
)
