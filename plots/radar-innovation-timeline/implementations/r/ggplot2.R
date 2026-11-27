#' anyplot.ai
#' radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 79/100 | Updated: 2026-11-27

library(ggplot2)
library(ragg)

# Theme tokens — Imprint palette
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green → AI & ML
  "#C475FD",  # 2 — lavender    → Cloud & Infra
  "#4467A3",  # 3 — blue        → Security
  "#BD8233"   # 4 — ochre       → Dev Tools
)

sector_names  <- c("AI & ML", "Cloud & Infra", "Security", "Dev Tools")
ring_labels_v <- c("Now", "Near-term", "Mid-term", "Future")
color_map     <- setNames(IMPRINT_PALETTE, sector_names)
sector_starts <- setNames(c(0, 67.5, 135, 202.5), sector_names)

# Ring geometry: four equal-width horizons around a small open centre
ring_edges  <- c(0.2, 1.45, 2.45, 3.4, 4.3)
ring_mid    <- (ring_edges[1:4] + ring_edges[2:5]) / 2
ring_mid[1] <- 0.6  # the innermost band is narrow in pixels, so its markers sit closer to the centre
SWEEP       <- 270  # three-quarter layout, the last quadrant stays open

# 16 technology items: one per (sector x ring) cell, short names so each fits its cell
items <- tibble::tibble(
  name = c(
    "LLM\nServing", "Agentic AI", "Foundation\nModels", "Spiking\nChips",
    "GitOps", "FinOps", "Edge ML", "Quantum\nCloud",
    "Zero\nTrust", "AI-Powered\nSIEM", "Homomorphic\nEncryption", "Post-Quantum\nCrypto",
    "Copilot", "Platform\nEng.", "Wasm", "Auto\nTesting"
  ),
  sector = rep(sector_names, each = 4),
  ring_r = rep(1:4, times = 4),
  # Angle inside the 67.5-degree sector and the side the label runs to, chosen so each label stays in its cell
  angle_offset = c(30, 4, 26, 4,  50, 62, 62, 62,  45, 26, 34, 34,  60, 4, 56, 4),
  right_side   = c(TRUE, TRUE, FALSE, TRUE,  TRUE, TRUE, TRUE, TRUE,  TRUE, FALSE, FALSE, FALSE,  FALSE, FALSE, TRUE, FALSE)
)

items$angle <- sector_starts[items$sector] + items$angle_offset
items$y     <- ring_mid[items$ring_r]
items$label <- ifelse(
  items$right_side,
  gsub("(^|\n)", "\\1   ", items$name),
  gsub("($|\n)", "   \\1", items$name)
)
# Larger points for more-immediate rings to convey urgency/immediacy
items$point_size <- c(6.5, 5.5, 4.5, 3.5)[items$ring_r]

RING_FILL <- if (THEME == "light") "#E6E3DB" else "#232320"
edge_df   <- tibble::tibble(y = ring_edges)
band_df   <- tibble::tibble(ymin = ring_edges[c(1, 3)], ymax = ring_edges[c(2, 4)])
spoke_df  <- tibble::tibble(angle = c(sector_starts, SWEEP))

# Ring names sit in the open quadrant, one per band
ring_ann_df <- tibble::tibble(angle = 350, y = ring_mid, label = ring_labels_v)

# Sector headers outside the outermost ring boundary
sector_hdr_df <- tibble::tibble(
  angle = sector_starts + 33.75,
  y     = ring_edges[5] + 0.22,
  label = sector_names
)

title_str <- "radar-innovation-timeline · r · ggplot2 · anyplot.ai"
title_sz  <- max(8L, round(12 * 67 / nchar(title_str)))

p <- ggplot() +
  # Alternating ring fills (rings 1 and 3)
  geom_rect(
    data = band_df,
    aes(xmin = 0, xmax = SWEEP, ymin = ymin, ymax = ymax),
    fill = RING_FILL, color = NA, alpha = 0.75
  ) +
  # Ring boundary arcs
  geom_segment(
    data = edge_df,
    aes(x = 0, xend = SWEEP, y = y, yend = y),
    color = INK_SOFT, linewidth = 0.25, alpha = 0.5
  ) +
  # Sector divider spokes
  geom_segment(
    data = spoke_df,
    aes(x = angle, xend = angle, y = ring_edges[1], yend = ring_edges[5]),
    color = INK_SOFT, linewidth = 0.45, alpha = 0.6
  ) +
  # Sector header labels
  geom_text(
    data = sector_hdr_df,
    aes(x = angle, y = y, label = label),
    size = 3.6, fontface = "bold", color = INK, hjust = 0.5
  ) +
  # Ring names in the open quadrant
  geom_text(
    data = ring_ann_df,
    aes(x = angle, y = y, label = label),
    size = 3.4, color = INK_SOFT, fontface = "bold", hjust = 1
  ) +
  # Technology item points, larger for more-immediate rings
  geom_point(
    data = items,
    aes(x = angle, y = y, color = sector, size = point_size),
    alpha = 0.95
  ) +
  scale_size_identity(guide = "none") +
  # Technology item labels beside each marker
  geom_text(
    data = items,
    aes(x = angle, y = y, label = label, hjust = ifelse(right_side, 0, 1), color = sector),
    size = 2.7, vjust = 0.5, lineheight = 0.85, show.legend = FALSE
  ) +
  coord_polar(theta = "x", start = 0) +
  scale_x_continuous(limits = c(0, 360), breaks = NULL, expand = c(0, 0)) +
  scale_y_continuous(limits = c(0, 4.7), breaks = NULL) +
  scale_color_manual(values = color_map, guide = guide_legend(override.aes = list(size = 5))) +
  labs(title = title_str, color = "Sector") +
  theme_void(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    plot.title = element_text(
      color = INK, size = title_sz, hjust = 0.5,
      margin = margin(b = 4)
    ),
    legend.position   = "inside",
    legend.position.inside = c(0.02, 0.9),
    legend.justification = c(0, 1),
    legend.direction  = "vertical",
    legend.background = element_rect(
      fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3
    ),
    legend.text     = element_text(color = INK_SOFT, size = 10),
    legend.title    = element_text(color = INK, size = 11),
    legend.key       = element_blank(),
    legend.margin    = margin(8, 10, 8, 8),
    legend.key.size = unit(0.55, "cm"),
    plot.margin     = margin(10, 10, 10, 10)
  )

ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
