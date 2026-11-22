#' anyplot.ai
#' network-weighted: Weighted Network Graph with Edge Thickness
#' Library: ggplot2 | R
#' Quality: pending | Updated: 2026-11-22

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
SOURCE <- "Exporter"                  # role: source
TARGET <- "Importer"                  # role: target
WEIGHT <- "Trade volume (bn USD)"     # role: weight

# Data: replace this block with your own edge table, for example df <- read.csv("trade.csv", check.names = FALSE)
set.seed(42)
countries <- c("USA", "China", "India", "Japan", "Germany",
               "UK", "France", "Brazil", "Canada", "Mexico",
               "South Korea", "Italy", "Spain", "Netherlands", "Australia")
src <- c(1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 4, 5, 5, 6, 6, 7, 8, 9, 10, 11, 12, 13, 14)
dst <- c(2, 3, 4, 3, 5, 6, 4, 5, 5, 11, 12, 6, 7, 7, 14, 8, 9, 10, 9, 2, 13, 14, 1)
df <- tibble::tibble(
  !!SOURCE := countries[src],
  !!TARGET := countries[dst],
  !!WEIGHT := c(640, 380, 285, 620, 290, 240, 185, 165, 310, 85, 150, 520,
                380, 275, 220, 185, 95, 120, 85, 330, 95, 80, 65)
)

# Plot: reads only df and the constants above
# Spring layout (Fruchterman-Reingold): heavier edges pull their nodes closer
node_ids <- unique(c(df[[SOURCE]], df[[TARGET]]))
n <- length(node_ids)
ia <- match(df[[SOURCE]], node_ids)
ib <- match(df[[TARGET]], node_ids)
w  <- df[[WEIGHT]] / max(df[[WEIGHT]])
pos <- cbind(cos(2 * pi * (1:n) / n), sin(2 * pi * (1:n) / n)) + matrix(rnorm(2 * n, sd = 0.1), n, 2)
k <- 1
temp <- 0.3
for (iter in 1:400) {
  disp <- matrix(0, n, 2)
  for (i in 1:n) {
    d <- matrix(pos[i, ], n, 2, byrow = TRUE) - pos
    dist <- pmax(sqrt(rowSums(d^2)), 1e-6)
    disp[i, ] <- colSums(d / dist * (8 * k^2 / dist) * (seq_len(n) != i))
  }
  for (e in seq_along(ia)) {
    d <- pos[ia[e], ] - pos[ib[e], ]
    dist <- max(sqrt(sum(d^2)), 1e-6)
    f <- (dist^2 / k) * (0.02 + 0.06 * w[e]) * d / dist
    disp[ia[e], ] <- disp[ia[e], ] - f
    disp[ib[e], ] <- disp[ib[e], ] + f
  }
  len <- pmax(sqrt(rowSums(disp^2)), 1e-6)
  pos <- pos + disp / len * pmin(len, temp)
  temp <- temp * 0.985
}
nodes <- tibble::tibble(node = node_ids, x = pos[, 1], y = pos[, 2])

edges <- df |>
  mutate(
    x    = nodes$x[ia], y    = nodes$y[ia],
    xend = nodes$x[ib], yend = nodes$y[ib]
  )

p <- ggplot() +
  geom_segment(
    data = edges,
    aes(x = x, y = y, xend = xend, yend = yend, linewidth = .data[[WEIGHT]]),
    color = IMPRINT_PALETTE[1], alpha = 0.55, lineend = "round"
  ) +
  geom_point(data = nodes, aes(x = x, y = y), color = IMPRINT_PALETTE[1], size = 10) +
  geom_text(
    data = nodes, aes(x = x, y = y, label = substr(node, 1, 3)),
    color = PAGE_BG, size = 3.2, fontface = "bold"
  ) +
  scale_linewidth_continuous(
    range = c(0.5, 3.5), breaks = c(100, 300, 600), name = WEIGHT,
    guide = guide_legend(override.aes = list(alpha = 0.55, colour = IMPRINT_PALETTE[1]))
  ) +
  coord_equal(expand = TRUE) +
  scale_x_continuous(expand = expansion(mult = 0.08)) +
  scale_y_continuous(expand = expansion(mult = 0.08)) +
  labs(title = "network-weighted · r · ggplot2 · anyplot.ai") +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    axis.title        = element_blank(),
    axis.text         = element_blank(),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12, face = "bold"),
    legend.background = element_rect(fill = PAGE_BG, color = NA, linewidth = 0),
    legend.key        = element_rect(fill = PAGE_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 9),
    legend.title      = element_text(color = INK, size = 10),
    legend.key.width  = unit(1.2, "cm"),
    plot.margin       = margin(10, 10, 10, 10, "pt")
  )

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
