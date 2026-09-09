#' anyplot.ai
#' tree-phylogenetic: Phylogenetic Tree Diagram
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 92/100 | Created: 2026-09-09

library(ggplot2)
library(dplyr)
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
BRAND       <- IMPRINT_PALETTE[1]

# --- Data ---------------------------------------------------------------
# Primate phylogeny with divergence times (millions of years ago, mtDNA-based
# estimates). Ultrametric time tree: every tip sits at the present (age 0);
# internal-node x is its divergence age. Plotted as x = -age so tips align at
# x = 0 and the tree grows leftward into the past, with species labels
# readable to the right of the tips.
tips <- tibble::tibble(
  label = c("Human", "Chimpanzee", "Gorilla", "Orangutan",
            "Gibbon", "Rhesus Macaque", "Common Marmoset"),
  y     = c(7, 6, 5, 4, 3, 2, 1),
  clade = c("Great apes (Hominidae)", "Great apes (Hominidae)",
            "Great apes (Hominidae)", "Great apes (Hominidae)",
            "Other primates", "Other primates", "Other primates")
) %>%
  mutate(x = 0)

# Internal nodes: age = divergence time (Mya), y = midpoint of children
nodes <- tibble::tibble(
  node  = c("human_chimp", "homini", "hominid", "hominoid", "catarrhini"),
  age   = c(6, 8, 15, 18, 29),
  y     = c((7 + 6) / 2, ((7 + 6) / 2 + 5) / 2,
            (((7 + 6) / 2 + 5) / 2 + 4) / 2,
            ((((7 + 6) / 2 + 5) / 2 + 4) / 2 + 3) / 2,
            (((((7 + 6) / 2 + 5) / 2 + 4) / 2 + 3) / 2 + 2) / 2)
) %>%
  mutate(x = -age)
root_age <- 43
root_y   <- (nodes$y[nodes$node == "catarrhini"] + 1) / 2

# Horizontal branches: x = ancestor age, xend = descendant age, at descendant y
branches <- tibble::tibble(
  x     = c(nodes$x[nodes$node == "human_chimp"],
            nodes$x[nodes$node == "human_chimp"],
            nodes$x[nodes$node == "homini"],
            nodes$x[nodes$node == "homini"],
            nodes$x[nodes$node == "hominid"],
            nodes$x[nodes$node == "hominid"],
            nodes$x[nodes$node == "hominoid"],
            nodes$x[nodes$node == "hominoid"],
            nodes$x[nodes$node == "catarrhini"],
            nodes$x[nodes$node == "catarrhini"],
            -root_age,
            -root_age),
  xend  = c(0, 0,
            nodes$x[nodes$node == "human_chimp"],
            0,
            nodes$x[nodes$node == "homini"],
            0,
            nodes$x[nodes$node == "hominid"],
            0,
            nodes$x[nodes$node == "hominoid"],
            0,
            nodes$x[nodes$node == "catarrhini"],
            0),
  y     = c(7, 6,
            nodes$y[nodes$node == "human_chimp"],
            5,
            nodes$y[nodes$node == "homini"],
            4,
            nodes$y[nodes$node == "hominid"],
            3,
            nodes$y[nodes$node == "hominoid"],
            2,
            nodes$y[nodes$node == "catarrhini"],
            1),
  clade = c("Great apes (Hominidae)", "Great apes (Hominidae)",
            "Great apes (Hominidae)",
            "Great apes (Hominidae)",
            "Great apes (Hominidae)",
            "Great apes (Hominidae)",
            "Great apes (Hominidae)",
            "Other primates",
            "Other primates",
            "Other primates",
            "Other primates",
            "Other primates")
) %>%
  mutate(yend = y)

# Vertical connectors at each internal node, spanning its two children
connectors <- tibble::tibble(
  x     = c(nodes$x[nodes$node == "human_chimp"],
            nodes$x[nodes$node == "homini"],
            nodes$x[nodes$node == "hominid"],
            nodes$x[nodes$node == "hominoid"],
            nodes$x[nodes$node == "catarrhini"],
            -root_age),
  y     = c(6, 5, 4, 3, 2, 1),
  yend  = c(7,
            nodes$y[nodes$node == "human_chimp"],
            nodes$y[nodes$node == "homini"],
            nodes$y[nodes$node == "hominid"],
            nodes$y[nodes$node == "hominoid"],
            nodes$y[nodes$node == "catarrhini"]),
  clade = c("Great apes (Hominidae)", "Great apes (Hominidae)",
            "Great apes (Hominidae)", "Other primates", "Other primates",
            "Other primates")
) %>%
  mutate(xend = x)

branch_lines <- bind_rows(branches, connectors)

# --- Plot -----------------------------------------------------------------
p <- ggplot() +
  geom_segment(
    data = branch_lines,
    aes(x = x, xend = xend, y = y, yend = yend, color = clade),
    linewidth = 1.4, lineend = "round"
  ) +
  geom_point(data = tips, aes(x = x, y = y, color = clade), size = 3.4) +
  geom_text(
    data = tips, aes(x = x, y = y, label = label, color = clade),
    hjust = 0, nudge_x = 1, size = 3.5, fontface = "italic",
    show.legend = FALSE
  ) +
  scale_color_manual(values = c("Great apes (Hominidae)" = BRAND,
                                 "Other primates" = INK_MUTED)) +
  scale_x_continuous(
    breaks = seq(-40, 0, by = 10),
    labels = abs(seq(-40, 0, by = 10)),
    limits = c(-root_age - 2, 14)
  ) +
  scale_y_continuous(limits = c(0.3, 7.7)) +
  labs(
    title = "Primate Phylogeny · tree-phylogenetic · r · ggplot2 · anyplot.ai",
    x = "Divergence time (millions of years ago)",
    color = "Clade"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x  = element_line(color = INK, linewidth = 0.25),
    panel.grid.minor.x  = element_blank(),
    panel.grid.major.y  = element_blank(),
    panel.grid.minor.y  = element_blank(),
    axis.title.x        = element_text(color = INK, size = 10),
    axis.title.y        = element_blank(),
    axis.text.x         = element_text(color = INK_SOFT, size = 8),
    axis.text.y         = element_blank(),
    axis.ticks          = element_blank(),
    plot.title          = element_text(color = INK, size = 12),
    legend.position     = "bottom",
    legend.title        = element_text(color = INK, size = 10),
    legend.text         = element_text(color = INK_SOFT, size = 8),
    legend.background   = element_rect(fill = PAGE_BG, color = NA),
    legend.key          = element_rect(fill = PAGE_BG, color = NA),
    plot.margin         = margin(t = 10, r = 20, b = 5, l = 5)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
