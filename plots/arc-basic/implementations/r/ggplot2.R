#' anyplot.ai
#' arc-basic: Basic Arc Diagram
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 83/100 | Created: 2026-05-30

library(ggplot2)
library(dplyr)
library(tibble)
library(tidyr)
library(ragg)

set.seed(42)

# Theme tokens (Imprint palette)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Nodes: Hamlet characters ordered by narrative prominence
node_names <- c("Hamlet", "Horatio", "Claudius", "Gertrude", "Ophelia",
                "Polonius", "Laertes", "Marcellus", "Rosencrantz", "Guildenstern")
node_df <- tibble(name = node_names, x = seq_along(node_names))

# Edges with relationship type
edges_df <- tribble(
  ~from,         ~to,            ~type,
  "Hamlet",      "Horatio",      "Friendship",
  "Hamlet",      "Claudius",     "Political",
  "Hamlet",      "Gertrude",     "Family",
  "Hamlet",      "Ophelia",      "Romantic",
  "Hamlet",      "Polonius",     "Political",
  "Hamlet",      "Laertes",      "Political",
  "Hamlet",      "Marcellus",    "Friendship",
  "Hamlet",      "Rosencrantz",  "Friendship",
  "Hamlet",      "Guildenstern", "Friendship",
  "Claudius",    "Gertrude",     "Romantic",
  "Claudius",    "Polonius",     "Political",
  "Claudius",    "Rosencrantz",  "Political",
  "Claudius",    "Guildenstern", "Political",
  "Ophelia",     "Polonius",     "Family",
  "Ophelia",     "Laertes",      "Family",
  "Polonius",    "Laertes",      "Family",
  "Horatio",     "Marcellus",    "Friendship"
) %>%
  left_join(node_df, by = c("from" = "name")) %>%
  rename(x1 = x) %>%
  left_join(node_df, by = c("to" = "name")) %>%
  rename(x2 = x) %>%
  mutate(edge_id = row_number())

# Semi-ellipse arcs: height proportional to span distance, inlined per-row
arc_data <- edges_df %>%
  rowwise() %>%
  mutate(pts = list({
    cx <- (x1 + x2) / 2
    r  <- abs(x2 - x1) / 2
    t  <- seq(pi, 0, length.out = 80)
    tibble(arc_x = cx + r * cos(t), arc_y = 0.55 * r * sin(t))
  })) %>%
  ungroup() %>%
  unnest(cols = c(pts))

# Title: 36 chars < 67 baseline, so full default size
plot_title <- "arc-basic · r · ggplot2 · anyplot.ai"
n_chars    <- nchar(plot_title)
title_size <- max(8L, round(12 * min(1.0, 67 / n_chars)))

# Relationship colors — Imprint palette positions 1–4
rel_colors <- c(
  "Family"     = IMPRINT_PALETTE[1],  # #009E73 brand green
  "Friendship" = IMPRINT_PALETTE[2],  # #C475FD lavender
  "Political"  = IMPRINT_PALETTE[3],  # #4467A3 blue
  "Romantic"   = IMPRINT_PALETTE[4]   # #BD8233 ochre
)

p <- ggplot() +
  # Arcs above the baseline
  geom_path(
    data = arc_data,
    aes(x = arc_x, y = arc_y, group = edge_id, color = type),
    linewidth = 0.85, alpha = 0.60
  ) +
  # Horizontal baseline
  geom_hline(yintercept = 0, color = INK_SOFT, linewidth = 0.35) +
  # Nodes as filled circles on the baseline
  geom_point(
    data = node_df, aes(x = x, y = 0),
    shape = 21, size = 3.0, fill = INK, color = PAGE_BG, stroke = 0.8
  ) +
  # Node labels rotated below baseline
  geom_text(
    data = node_df, aes(x = x, y = -0.15, label = name),
    color = INK_SOFT, size = 3.0, angle = 40, hjust = 1, vjust = 1
  ) +
  scale_color_manual(values = rel_colors, name = "Relationship") +
  scale_x_continuous(expand = expansion(mult = c(0.04, 0.12))) +
  coord_cartesian(ylim = c(-0.8, 2.8), clip = "off") +
  labs(title = plot_title) +
  theme_void() +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    plot.title        = element_text(color = INK, size = title_size,
                                      hjust = 0.5, face = "bold",
                                      margin = margin(t = 10, b = 6)),
    legend.position   = "bottom",
    legend.direction  = "horizontal",
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 9, face = "bold"),
    legend.background = element_rect(fill = ELEVATED_BG, color = NA),
    legend.key        = element_rect(fill = NA, color = NA),
    legend.margin     = margin(2, 8, 4, 8),
    plot.margin       = margin(20, 20, 10, 20)
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
